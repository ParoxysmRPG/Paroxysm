#include "combat_map.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <unordered_map>
#include <unordered_set>
#include <utility>

// The combat subsystem's aggression helper is local to fight.c's declarations.
extern "C" int get_agg(CHAR_DATA *viewer, CHAR_DATA *actor);

namespace haven {
namespace {

CHAR_DATA *selected_target(CHAR_DATA *viewer) {
  // target/target_2/target_3 track damage history, not the selected opponent.
  return viewer->cfighting != NULL ? viewer->cfighting : viewer->chattacking;
}

bool ascii_digit(unsigned char c) { return c >= '0' && c <= '9'; }
bool ascii_alpha(unsigned char c) {
  return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
}

// Only the short visible prefix is needed. Do not run remove_color: it copies
// whole descriptions through legacy fixed buffers and allocates engine strings.
std::string name_prefix(const char *name) {
  std::string prefix;
  if (name == NULL)
    return prefix;
  const unsigned char *p = reinterpret_cast<const unsigned char *>(name);
  while (*p != 0 && prefix.size() < 5) {
    if (*p == '`') {
      ++p;
      if (*p == 0)
        break;
      if (*p == '#') {
        ++p;
        for (int i = 0; i < 6 && *p != 0 && *p != ' '; ++i)
          ++p;
      } else if (ascii_digit(p[0]) && p[1] != 0 && ascii_digit(p[1]) &&
                 p[2] != 0 && ascii_digit(p[2])) {
        p += 3;
      } else {
        ++p;
      }
      continue;
    }
    // The game's text renderer recognizes these inline emphasis tags.
    if (*p == '<') {
      const unsigned char *tag = p + 1;
      if (*tag == '/')
        ++tag;
      if ((*tag == 'b' || *tag == 'B' || *tag == 'i' || *tag == 'I' ||
           *tag == 'u' || *tag == 'U') && tag[1] == '>') {
        p = tag + 2;
        continue;
      }
    }
    // Never pass terminal control bytes into the two-column map label.
    if (*p == 27) {
      ++p;
      if (*p == '[') {
        ++p;
        while (*p != 0 && !(*p >= 0x40 && *p <= 0x7e))
          ++p;
        if (*p != 0)
          ++p;
      } else if (*p == ']') {
        ++p;
        while (*p != 0 && *p != 7 && !(*p == 27 && p[1] == '\\'))
          ++p;
        if (*p == 7)
          ++p;
        else if (*p == 27)
          p += 2;
      }
      continue;
    }
    const unsigned char c = *p++;
    if (c < 32 || c == 127 || (prefix.empty() && c == ' '))
      continue;
    // ASCII tokens keep cell widths predictable on all MUD clients.
    prefix += c < 127 ? static_cast<char>(c) : '?';
  }
  return prefix;
}

std::string preferred_label(const char *name) {
  const std::string prefix = name_prefix(name);
  size_t offset = 0;
  if (prefix.size() >= 2 && (prefix[0] == 'a' || prefix[0] == 'A')) {
    if (prefix[1] == ' ')
      offset = 2;
    else if (prefix.size() >= 3 && (prefix[1] == 'n' || prefix[1] == 'N') &&
             prefix[2] == ' ')
      offset = 3;
  }
  std::string label(2, '?');
  for (size_t i = 0; i < 2 && offset + i < prefix.size(); ++i) {
    const unsigned char c = prefix[offset + i];
    if (ascii_alpha(c) || ascii_digit(c))
      label[i] = static_cast<char>(c);
  }
  return label;
}

struct CoverPosition {
  ROOM_INDEX_DATA *room;
  std::int64_t x;
  std::int64_t y;

  bool operator==(const CoverPosition &other) const {
    return room == other.room && x == other.x && y == other.y;
  }
};

struct CoverPositionHash {
  size_t operator()(const CoverPosition &position) const {
    size_t hash = std::hash<ROOM_INDEX_DATA *>()(position.room);
    hash ^= std::hash<std::int64_t>()(position.x) + 0x9e3779b9U +
            (hash << 6) + (hash >> 2);
    hash ^= std::hash<std::int64_t>()(position.y) + 0x9e3779b9U +
            (hash << 6) + (hash >> 2);
    return hash;
  }
};

void associate_cover(CombatMapSnapshot &snapshot) {
  size_t cover_count = 0;
  for (const CombatMapEntry &entry : snapshot.entries)
    if (entry.is_cover)
      ++cover_count;
  if (cover_count == 0)
    return;

  // Index the nine local positions each visible cover protects. Including the
  // room avoids false associations across room boundaries; using local units
  // avoids mistaking a compressed map cell for actual cover proximity.
  std::unordered_map<CoverPosition, int, CoverPositionHash> protection;
  protection.reserve(cover_count * 9);
  for (size_t i = 0; i < snapshot.entries.size(); ++i) {
    const CombatMapEntry &entry = snapshot.entries[i];
    if (!entry.is_cover)
      continue;
    const CHAR_DATA *cover = entry.character;
    for (int dy = -1; dy <= 1; ++dy)
      for (int dx = -1; dx <= 1; ++dx)
        protection.emplace(CoverPosition{cover->in_room,
            static_cast<std::int64_t>(cover->x) + dx,
            static_cast<std::int64_t>(cover->y) + dy}, static_cast<int>(i));
  }
  for (CombatMapEntry &entry : snapshot.entries) {
    if (entry.is_cover || entry.is_turret)
      continue;
    const CHAR_DATA *actor = entry.character;
    const auto found = protection.find(
        CoverPosition{actor->in_room, actor->x, actor->y});
    if (found != protection.end())
      entry.cover_entry = found->second;
  }
}

std::string styled_label(const char *color, const std::string &token,
                         bool protected_by_cover) {
  return std::string(color) + (protected_by_cover ? "<u>" : "") + token +
         (protected_by_cover ? "</u>" : "") + "`x";
}

void assign_labels(CHAR_DATA *viewer, CombatMapSnapshot &snapshot) {
  std::unordered_set<std::string> reserved;
  reserved.reserve(snapshot.entries.size() + 1);
  reserved.insert("Me");
  reserved.insert("CC");
  reserved.insert("EE");
  reserved.insert("[]");
  reserved.insert("{}");
  for (const CombatMapEntry &entry : snapshot.entries)
    reserved.insert(entry.label);

  std::unordered_set<std::string> assigned;
  assigned.reserve(snapshot.entries.size() + 1);
  assigned.insert("Me");
  assigned.insert("CC");
  assigned.insert("EE");
  assigned.insert("[]");
  assigned.insert("{}");
  // Names retain their initials when possible. Collisions get a two-character
  // ID, with a monotonic cursor so even very crowded groups remain linear.
  const char alphabet[] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                          "!#$%()*+,-./:;=?@[]^_{|}~";
  const size_t radix = sizeof(alphabet) - 1;
  const size_t alphanumeric_radix = 62;
  const size_t alphanumeric_count = alphanumeric_radix * alphanumeric_radix;
  size_t next_id = 0;
  CHAR_DATA *target = selected_target(viewer);
  for (CombatMapEntry &entry : snapshot.entries) {
    if (entry.character == viewer) {
      entry.label = styled_label("`W", "Me", entry.cover_entry >= 0);
      continue;
    }
    std::string token = entry.label;
    if (!entry.is_cover && !entry.is_turret && !assigned.insert(token).second) {
      token = "??";
      while (next_id < alphanumeric_count + radix * radix) {
        const bool alphanumeric = next_id < alphanumeric_count;
        const size_t candidate_id = alphanumeric ? next_id : next_id - alphanumeric_count;
        const size_t candidate_radix = alphanumeric ? alphanumeric_radix : radix;
        std::string candidate;
        candidate += alphabet[candidate_id / candidate_radix];
        candidate += alphabet[candidate_id % candidate_radix];
        ++next_id;
        if (reserved.find(candidate) == reserved.end() &&
            assigned.insert(candidate).second) {
          token = candidate;
          break;
        }
      }
      // Beyond the finite two-ASCII-column namespace, keep every roster entry
      // and use a neutral overflow marker rather than widening/corrupting cells.
    }
    const char *color = entry.character == target ? "`M" :
        (get_agg(viewer, entry.character) > 0 || get_agg(entry.character, viewer) > 0)
            ? "`R" : (entry.is_cover || entry.is_turret) ? "`C" : "`G";
    entry.label = styled_label(color, token, entry.cover_entry >= 0);
  }
}

int map_axis(int coordinate, const std::array<int, 32> &edges, int size) {
  // upper_bound gives the original half-open cells, including negative edges.
  const auto end = edges.begin() + size + 1;
  const auto edge = std::upper_bound(edges.begin(), end, coordinate);
  if (edge == edges.begin() || edge == end)
    return -1;
  return static_cast<int>(edge - edges.begin()) - 1;
}

int actor_priority(const CombatMapEntry &entry, CHAR_DATA *viewer,
                   CHAR_DATA *target) {
  return entry.character == viewer ? 3 : entry.character == target ? 2 :
         entry.is_cover && !entry.is_turret ? 0 : 1;
}

}

CombatMapSnapshot combat_map_snapshot(CHAR_DATA *viewer) {
  CombatMapSnapshot snapshot;
  if (viewer == NULL || viewer->in_room == NULL)
    return snapshot;
  snapshot.entries.reserve(32);
  for (CHAR_DATA *actor : char_list) {
    if (actor == NULL || actor->in_room == NULL || is_gm(actor))
      continue;
    if (!can_see_char_distance(viewer, actor, DISTANCE_MEDIUM) ||
        !can_map_see(viewer, actor))
      continue;
    CombatMapEntry entry;
    entry.character = actor;
    entry.x = relative_x(viewer, actor->in_room, actor->x);
    entry.y = relative_y(viewer, actor->in_room, actor->y);
    entry.z = relative_z(viewer, actor->in_room);
    entry.distance = combat_distance(viewer, actor, FALSE);
    entry.is_cover = IS_NPC(actor) && IS_FLAG(actor->act, ACT_COVER);
    entry.is_turret = IS_NPC(actor) && IS_FLAG(actor->act, ACT_TURRET);
    entry.label = actor == viewer ? "Me" : entry.is_turret ? "{}" :
                  preferred_label(PERS(actor, viewer));
    const char *name = PERS_3(actor, viewer);
    entry.display_name = name == NULL ? "" : name;
    snapshot.entries.push_back(std::move(entry));
  }
  associate_cover(snapshot);
  assign_labels(viewer, snapshot);
  return snapshot;
}

std::vector<CombatMapCell> combat_map_cells(
    CHAR_DATA *viewer, const CombatMapSnapshot &snapshot, int size) {
  if (viewer == NULL || size <= 0 || size > 31)
    return std::vector<CombatMapCell>();
  std::vector<CombatMapCell> cells(size * size);
  std::array<int, 32> edges;
  const int offset = (size - 1) / 2;
  for (int i = 0; i <= size; ++i)
    edges[i] = map_expand(i - offset);
  CHAR_DATA *target = selected_target(viewer);
  for (size_t i = 0; i < snapshot.entries.size(); ++i) {
    const CombatMapEntry &entry = snapshot.entries[i];
    const int x = map_axis(entry.x, edges, size);
    const int y = map_axis(entry.y, edges, size);
    if (x < 0 || y < 0)
      continue;
    CombatMapCell &cell = cells[y * size + x];
    if (cell.entry < 0 ||
        actor_priority(entry, viewer, target) >
        actor_priority(snapshot.entries[cell.entry], viewer, target))
      cell.entry = static_cast<int>(i);
    ++cell.count;
    if (entry.is_cover)
      ++cell.cover_count;
  }
  return cells;
}

void show_combat_map_roster(CHAR_DATA *viewer,
                            const CombatMapSnapshot &snapshot) {
  if (viewer == NULL || viewer->in_room == NULL)
    return;
  displaypois(viewer);
  std::vector<const CombatMapEntry *> ordered;
  ordered.reserve(snapshot.entries.size());
  for (const CombatMapEntry &entry : snapshot.entries) {
    if (entry.distance < 1000)
      ordered.push_back(&entry);
  }
  std::stable_sort(ordered.begin(), ordered.end(),
      [](const CombatMapEntry *a, const CombatMapEntry *b) {
        return a->distance < b->distance;
      });
  for (const CombatMapEntry *entry : ordered) {
    std::string line = "(" + entry->label + ") " + entry->display_name;
    const char *flags = battleflags(entry->character, viewer);
    if (flags != NULL)
      line += flags;
    if (entry->is_turret)
      line += entry->is_cover ? " [`CTurret; Cover`x]" : " [`CTurret`x]";
    else if (entry->is_cover)
      line += " [`CCover`x]";
    if (entry->cover_entry >= 0 &&
        static_cast<size_t>(entry->cover_entry) < snapshot.entries.size())
      line += " [`CIn cover: `x" +
              snapshot.entries[entry->cover_entry].display_name + "`x]";
    if (entry->cell_cover_count > 0 && !entry->is_cover && entry->cover_entry < 0) {
      line += " [`CCover in cell";
      if (entry->cell_cover_count > 1)
        line += ": " + std::to_string(entry->cell_cover_count);
      line += "`x]";
    }
    if (entry->map_objective == POI_CAPTURE)
      line += " [`YCapture point`x]";
    else if (entry->map_objective == POI_EXTRACT)
      line += " [`YExtraction point`x]";
    if (entry->overlap_count > 1)
      line += " and " + std::to_string(entry->overlap_count - 1) +
              (entry->overlap_count == 2 ? " other" : " others");
    line += " (X:" + std::to_string(entry->x) + " Y:" + std::to_string(entry->y) +
            " D:" + std::to_string(entry->distance);
    if (entry->z != 0)
      line += "(" + std::to_string(entry->z) + ")";
    line += ")\n\r";
    send_to_char(line.c_str(), viewer);
  }
}

}
