#include "local_map.h"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace haven {
namespace {

const int kMaxColumns = 15;
const int kMaxRows = 11;
const int kMaxRooms = kMaxColumns * kMaxRows;
const int kCanvasWidth = 4 * kMaxColumns + 1;
const int kCanvasHeight = 2 * kMaxRows + 1;
// At most ten distinct destinations per visited room, plus the origin.
// This fixed cache also remembers denied rooms, avoiding repeated visibility
// checks (which may inspect the viewer's inventory for special areas).
const int kRoomCacheSize = 2048;
static_assert(kRoomCacheSize > 10 * kMaxRooms + 1, "map cache too small");

struct Direction {
  int door;
  int dx;
  int dy;
  char line;
};

const Direction kDirections[] = {
  {DIR_NORTH, 0, -1, '|'}, {DIR_EAST, 1, 0, '-'},
  {DIR_SOUTH, 0, 1, '|'}, {DIR_WEST, -1, 0, '-'},
  {DIR_NORTHEAST, 1, -1, '/'}, {DIR_NORTHWEST, -1, -1, '\\'},
  {DIR_SOUTHEAST, 1, 1, '\\'}, {DIR_SOUTHWEST, -1, 1, '/'}
};

struct Pixel {
  char glyph;
  char color;
  unsigned char priority;
};

struct Node {
  ROOM_INDEX_DATA *room;
  int x;
  int y;
  char stairs;
  char stair_color;
};

struct RoomRecord {
  ROOM_INDEX_DATA *room;
  int node;
  bool visible;
};

bool aerial_or_water(const ROOM_INDEX_DATA *room) {
  switch (room->sector_type) {
    case SECT_AIR: case SECT_ATMOSPHERE: case SECT_WATER:
    case SECT_UNDERWATER: case SECT_SHALLOW: return true;
    default: return false;
  }
}

bool indoors(const ROOM_INDEX_DATA *room) {
  return IS_SET(room->room_flags, ROOM_INDOORS) != 0;
}

Pixel terrain(const ROOM_INDEX_DATA *room) {
  // Room flags take precedence over outdoor stock terrain on custom interiors.
  if (indoors(room)) {
    switch (room->sector_type) {
      case SECT_SHOP: case SECT_BANK: case SECT_COMMERCIAL:
        return {'$', 'Y', 100};
      case SECT_CLUB: case SECT_RESTERAUNT: case SECT_TAVERN: case SECT_CAFE:
        return {'C', 'M', 100};
      case SECT_HOSPITAL: return {'M', 'R', 100};
      case SECT_TUNNELS: case SECT_BASEMENT: return {'U', 'c', 100};
      default: return {'H', 'C', 100};
    }
  }
  switch (room->sector_type) {
    case SECT_HOUSE: case SECT_WAREHOUSE: case SECT_CAR:
      return {'H', 'C', 100};
    case SECT_SHOP: case SECT_BANK: case SECT_COMMERCIAL:
      return {'$', 'Y', 100};
    case SECT_CLUB: case SECT_RESTERAUNT: case SECT_TAVERN: case SECT_CAFE:
      return {'C', 'M', 100};
    case SECT_HOSPITAL: return {'M', 'R', 100};
    case SECT_STREET:
      return IS_SET(room->room_flags, ROOM_DIRTROAD)
          ? Pixel{'%', 'y', 100} : Pixel{'#', 'W', 100};
    case SECT_SIDEWALK: return {'.', 'w', 100};
    case SECT_ALLEY: return {':', 'w', 100};
    case SECT_DIRT: return {'%', 'y', 100};
    case SECT_PARKING: return {'P', 'w', 100};
    case SECT_PARK: return {'"', 'G', 100};
    case SECT_FOREST: return {'T', 'g', 100};
    case SECT_WATER: case SECT_UNDERWATER: case SECT_SHALLOW:
      return {'~', 'B', 100};
    case SECT_SWAMP: return {';', 'g', 100};
    case SECT_BEACH: return {',', 'Y', 100};
    case SECT_ROCKY: return {'A', 'y', 100};
    case SECT_CAVE: return {'O', 'y', 100};
    case SECT_TUNNELS: case SECT_BASEMENT: return {'U', 'c', 100};
    case SECT_ROOFTOP: return {'_', 'C', 100};
    case SECT_CEMETARY: return {'t', 'w', 100};
    case SECT_AIR: case SECT_ATMOSPHERE: return {'a', 'B', 100};
    case SECT_HELLGATE: return {'!', 'M', 100};
    default: return {'?', 'w', 100};
  }
}

class MapRenderer {
public:
  MapRenderer(CHAR_DATA *viewer, ROOM_INDEX_DATA *origin, bool compact,
              LocalMapStats &stats)
      : viewer_(viewer), origin_(origin), stats_(stats),
        administrator_(IS_ADMIN(viewer)), compact_(compact), count_(0) {
    const int linewidth = viewer->linewidth >= 10 && viewer->linewidth <= 1000
        ? viewer->linewidth : 80;
    columns_ = std::min(compact ? 3 : kMaxColumns,
                        std::max(1, (linewidth - (compact ? 1 : 5)) / 4));
    if (columns_ % 2 == 0)
      --columns_;
    rows_ = compact ? 3 : kMaxRows;
    width_ = 4 * columns_ + 1;
    height_ = 2 * rows_ + 1;
    for (int &cell : occupied_)
      cell = -1;
    for (Pixel &pixel : canvas_)
      pixel = {' ', 'x', 0};
  }

  std::string render() {
    RoomRecord &start = record(origin_);
    // The current room is already visible to the caller (look/map visibility
    // gates live at the command boundary). Do not run room light calculations.
    start.visible = true;
    add_node(start, columns_ / 2, rows_ / 2);

    // The queue cannot exceed the grid. Each queued room examines ten exits
    // exactly once. No recursion, world lookup, pathfinding, or mutable cache.
    for (int index = 0; index < count_; ++index) {
      Node &node = nodes_[index];
      add_stairs(node);
      for (const Direction &direction : kDirections)
        add_connection(node, direction, index == 0);
    }
    stats_.rooms = count_;

    for (int index = 0; index < count_; ++index) {
      const Node &node = nodes_[index];
      const int x = 2 + 4 * node.x;
      const int y = 1 + 2 * node.y;
      paint(x, y, index == 0 ? Pixel{'@', 'W', 110} : terrain(node.room));
      if (node.stairs != ' ')
        paint(x + 1, y, {node.stairs, node.stair_color, 110});
    }

    std::string result;
    // Reserve the fixed worst-case color/glyph budget once, including frames.
    result.reserve((3 * width_ + 16) * (height_ + 2));
    if (compact_) {
      append_compact_border(result);
    } else {
      char title[64];
      std::snprintf(title, sizeof(title), "Local map | N | z %d", origin_->z);
      if (std::strlen(title) > static_cast<size_t>(width_ + 2))
        std::snprintf(title, sizeof(title), "N z%d", origin_->z);
      append_border(result, title);
    }
    // The title-side minimap omits the empty outer canvas margin. Its three
    // room rows occupy an 11-by-5 interior inside a quiet 13-by-7 frame.
    const int inset = compact_ ? 1 : 0;
    for (int y = inset; y < height_ - inset; ++y) {
      result += compact_ ? "`g|`x" : "`g| `x";
      char color = 'x';
      for (int x = inset; x < width_ - inset; ++x) {
        const Pixel &pixel = canvas_[y * kCanvasWidth + x];
        // Spaces need no color change; emit only transitions between glyphs.
        if (pixel.glyph != ' ' && color != pixel.color) {
          result += '`';
          result += pixel.color;
          color = pixel.color;
        }
        result += pixel.glyph;
      }
      result += compact_ ? "`g|`x\n\r" : "`g |`x\n\r";
    }
    if (compact_)
      append_compact_border(result);
    else
      append_border(result, width_ + 2 >= 10 ? "help map" : "map");
    return result;
  }

private:
  CHAR_DATA *viewer_;
  ROOM_INDEX_DATA *origin_;
  LocalMapStats &stats_;
  bool administrator_;
  bool compact_;
  int columns_;
  int rows_;
  int width_;
  int height_;
  int count_;
  std::array<Node, kMaxRooms> nodes_{};
  std::array<int, kMaxRooms> occupied_{};
  std::array<Pixel, kCanvasWidth * kCanvasHeight> canvas_{};
  std::array<RoomRecord, kRoomCacheSize> cache_{};

  RoomRecord &record(ROOM_INDEX_DATA *room) {
    std::uintptr_t hash = reinterpret_cast<std::uintptr_t>(room);
    hash ^= hash >> 17;
    hash *= static_cast<std::uintptr_t>(0xed5ad4bbU);
    hash ^= hash >> 11;
    int slot = static_cast<int>(hash & (kRoomCacheSize - 1));
    while (cache_[slot].room != NULL && cache_[slot].room != room)
      slot = (slot + 1) & (kRoomCacheSize - 1);
    RoomRecord &entry = cache_[slot];
    if (entry.room == NULL) {
      entry.room = room;
      entry.node = -1;
      entry.visible = false;
      if (room == origin_) {
        entry.visible = true;
      } else if (room->area != NULL &&
                 room->area->world == origin_->area->world &&
                 (administrator_ || !IS_SET(room->room_flags, ROOM_INVISIBLE))) {
        ++stats_.visibility_checks;
        entry.visible = can_see_room(viewer_, room);
      }
    }
    return entry;
  }

  EXIT_DATA *visible_exit(ROOM_INDEX_DATA *room, int door) {
    ++stats_.exits_examined;
    EXIT_DATA *exit = room->exit[door];
    if (exit == NULL || exit->u1.to_room == NULL)
      return NULL;
    if (!administrator_ && (IS_SET(exit->exit_info, EX_HIDDEN) ||
                            IS_AFFECTED(exit, AFF_XHIDE)))
      return NULL;
    if (exit->wall > WALL_GLASS && exit->wallcondition != WALLCOND_HOLE)
      return NULL;
    ROOM_INDEX_DATA *destination = exit->u1.to_room;
    // Cross-world visibility can run property scans. Such portals have no
    // truthful location on this floor map and are left to the normal exits UI.
    if (destination->area == NULL ||
        destination->area->world != origin_->area->world)
      return NULL;
    return record(destination).visible ? exit : NULL;
  }

  void add_node(RoomRecord &entry, int x, int y) {
    entry.node = count_;
    nodes_[count_++] = {entry.room, x, y, ' ', 'Y'};
    occupied_[y * kMaxColumns + x] = entry.node;
  }

  bool is_stair(ROOM_INDEX_DATA *room, EXIT_DATA *exit) const {
    return ordinary_map_vertical_route(room, exit);
  }

  void add_stairs(Node &node) {
    EXIT_DATA *up = visible_exit(node.room, DIR_UP);
    EXIT_DATA *down = visible_exit(node.room, DIR_DOWN);
    const bool has_up = is_stair(node.room, up);
    const bool has_down = is_stair(node.room, down);
    node.stairs = has_up ? (has_down ? '*' : '^') : (has_down ? 'v' : ' ');
    node.stair_color = has_up ? (has_down ? 'M' : 'C') : 'c';
    if ((has_up && IS_SET(up->exit_info, EX_CLOSED)) ||
        (has_down && IS_SET(down->exit_info, EX_CLOSED)))
      node.stair_color = 'Y';
    if ((has_up && IS_SET(up->exit_info, EX_LOCKED) &&
                   IS_SET(up->exit_info, EX_CLOSED)) ||
        (has_down && IS_SET(down->exit_info, EX_LOCKED) &&
                     IS_SET(down->exit_info, EX_CLOSED)))
      node.stair_color = 'R';
  }

  bool local_coordinates(const ROOM_INDEX_DATA *from,
                          const ROOM_INDEX_DATA *to,
                          const Direction &direction) const {
    if (to->z != origin_->z)
      return false;
    // Legacy interiors sometimes share placeholder coordinates. Lay them out
    // from their exits within the same area, still detecting graph collisions.
    if (from->area == to->area && from->x == to->x && from->y == to->y)
      return true;
    // Widen before subtraction: builders can supply arbitrary integer coords.
    return static_cast<long long>(to->x) - from->x == direction.dx &&
           static_cast<long long>(to->y) - from->y == -direction.dy;
  }

  void add_connection(const Node &node, const Direction &direction,
                        bool from_origin) {
    EXIT_DATA *exit = visible_exit(node.room, direction.door);
    if (exit == NULL)
      return;
    ROOM_INDEX_DATA *destination = exit->u1.to_room;
    Pixel link = {direction.line, 'w', 1};
    bool traversable = true;
    const bool doorway = IS_SET(exit->exit_info, EX_ISDOOR) ||
                          IS_SET(exit->exit_info, EX_CLOSED);
    if (IS_SET(exit->exit_info, EX_CLOSED)) {
      link = IS_SET(exit->exit_info, EX_LOCKED)
          ? Pixel{'X', 'R', 8} : Pixel{'+', 'Y', 7};
      traversable = IS_SET(exit->exit_info, EX_SEETHRU) &&
                    !IS_SET(exit->exit_info, EX_CURTAINS);
    } else if (doorway) {
      link = {'o', 'G', 6};
    } else if (indoors(node.room) != indoors(destination)) {
      link = {'=', 'C', 5};
    }
    if (exit->wall == WALL_GLASS && exit->wallcondition != WALLCOND_HOLE) {
      if (!IS_SET(exit->exit_info, EX_CLOSED))
        link = {'W', 'C', 4};
      traversable = false;
    }
    if (!doorway && exit->wall == WALL_NONE) {
      if (exit->jump != 0)
        link = {'j', 'Y', 3};
      else if (exit->climb != 0)
        link = {'c', 'Y', 3};
      else if (exit->fall != 0)
        link = {'f', 'Y', 3};
    }

    if (traversable) {
      const int x = node.x + direction.dx;
      const int y = node.y + direction.dy;
      RoomRecord &entry = record(destination);
      const bool outside = x < 0 || y < 0 || x >= columns_ || y >= rows_;
      if (!local_coordinates(node.room, destination, direction) ||
          (entry.node >= 0 &&
           (nodes_[entry.node].x != x || nodes_[entry.node].y != y)) ||
          (!outside && occupied_[y * kMaxColumns + x] >= 0 &&
           occupied_[y * kMaxColumns + x] != entry.node)) {
        link = {'!', 'M', 9};
      } else if (!outside && entry.node < 0) {
        add_node(entry, x, y);
      }
      // Normal routes at the viewport edge retain their line/door glyph; an
      // edge is a crop of the neighborhood, not a nonlocal or malformed exit.
    }

    // One connector per edge; current-room door state wins if reverse exits
    // disagree. Crossing diagonal links remain a crossing, not a room.
    if (from_origin)
      link.priority += 32;
    paint(2 + 4 * node.x + 2 * direction.dx,
          1 + 2 * node.y + direction.dy, link);
  }

  void paint(int x, int y, Pixel pixel) {
    if (x < 0 || y < 0 || x >= width_ || y >= height_)
      return;
    Pixel &current = canvas_[y * kCanvasWidth + x];
    if ((current.glyph == '/' && pixel.glyph == '\\') ||
        (current.glyph == '\\' && pixel.glyph == '/')) {
      current = {'x', 'w', std::max(current.priority, pixel.priority)};
    } else if (pixel.priority >= current.priority) {
      current = pixel;
    }
  }

  void append_border(std::string &result, const char *caption) const {
    const int inner = width_ + 2;
    const int text_length = std::min(static_cast<int>(std::strlen(caption)),
                                      inner - 2);
    const int remaining = inner - text_length - 2;
    result += "`g+";
    result.append(remaining / 2, '-');
    result += " `C";
    result.append(caption, text_length);
    result += "`g ";
    result.append(remaining - remaining / 2, '-');
    result += "+`x\n\r";
  }

  void append_compact_border(std::string &result) const {
    result += "`g+";
    result.append(width_ - 2, '-');
    result += "+`x\n\r";
  }
};

} // namespace

bool ordinary_map_vertical_route(const ROOM_INDEX_DATA *room, const EXIT_DATA *exit) {
  if (room == NULL || exit == NULL || exit->u1.to_room == NULL)
    return false;
  const ROOM_INDEX_DATA *destination = exit->u1.to_room;
  // Legacy canopy rooms retain forest terrain and zero movement requirements.
  // Omit ambiguous outdoor links while retaining custom indoor stairways.
  if (room->sector_type == SECT_FOREST && destination->sector_type == SECT_FOREST &&
      !indoors(room) && !indoors(destination))
    return false;
  return (exit->wall == WALL_NONE || exit->wallcondition == WALLCOND_HOLE) &&
      exit->jump == 0 && exit->climb == 0 && exit->fall == 0 &&
      !aerial_or_water(room) && !aerial_or_water(destination);
}

std::string render_local_map(CHAR_DATA *viewer, ROOM_INDEX_DATA *origin,
                             bool compact, LocalMapStats *stats) {
  LocalMapStats local_stats = {0, 0, 0};
  LocalMapStats &measurement = stats != NULL ? *stats : local_stats;
  measurement = {0, 0, 0};
  if (viewer == NULL || origin == NULL || origin->area == NULL ||
      viewer->in_room == NULL || viewer->in_room->area == NULL ||
      viewer->in_room->area->world != origin->area->world)
    return std::string();
  return MapRenderer(viewer, origin, compact, measurement).render();
}

} // namespace haven
