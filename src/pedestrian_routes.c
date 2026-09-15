#include "merc.h"
#include "global.h"
#include <map>
#include <vector>

namespace {
// One bounded street graph is shared by the whole population. Paths contain
// room numbers, never retained room pointers, so OLC changes cannot leave a
// stale pointer behind. There is no world search in an individual NPC's step.
const size_t MAX_STREET_ROOMS = 4096;
const size_t MAX_STOPS = 32;
const unsigned short UNREACHABLE = 65535;
const time_t CACHE_LIFETIME = 300;
const time_t BLOCKED_RETRY = 60;

struct StreetNode {
  int vnum;
  std::vector<int> incoming;
};

std::vector<StreetNode> streets;
std::map<int, int> street_index;
std::vector<int> stops;
std::vector<std::vector<unsigned short> > distances;
std::vector<int> spawn_stops;
std::map<CHAR_DATA *, int> destinations;
time_t next_rebuild = 0;
time_t last_rebuild = 0;
bool cache_built = false;

bool street_room(ROOM_INDEX_DATA *room) {
  if (!room || !room->area || room->area->world != WORLD_EARTH
      || room->sector_type != SECT_STREET
      || IS_SET(room->room_flags, ROOM_INDOORS | ROOM_PRIVATE | ROOM_NO_MOB | ROOM_INVISIBLE))
    return false;
  // public_room() also considers current darkness/mist. Cache the permanent
  // public street designation instead of rebuilding paths with the weather.
  return room->area->vnum == 13 || IS_SET(room->room_flags, ROOM_PUBLIC);
}

bool open_exit(EXIT_DATA *exit) {
  return exit && exit->u1.to_room
      && !IS_SET(exit->exit_info, EX_CLOSED | EX_LOCKED | EX_HELLGATE | EX_HIDDEN)
      && (exit->wall == WALL_NONE || exit->wallcondition == WALLCOND_HOLE)
      && exit->jump <= 0 && exit->climb <= 0 && exit->fall <= 0;
}

int add_street(ROOM_INDEX_DATA *room) {
  std::map<int, int>::const_iterator found = street_index.find(room->vnum);
  if (found != street_index.end()) return found->second;
  if (streets.size() >= MAX_STREET_ROOMS) return -1;
  const int index = static_cast<int>(streets.size());
  StreetNode node;
  node.vnum = room->vnum;
  streets.push_back(node);
  street_index[room->vnum] = index;
  return index;
}

void build_routes() {
  cache_built = true;
  last_rebuild = current_time;
  next_rebuild = current_time + CACHE_LIFETIME;
  streets.clear();
  street_index.clear();
  stops.clear();
  distances.clear();
  spawn_stops.clear();

  for (int n = 0; n < trolly_stop_count && stops.size() < MAX_STOPS; ++n) {
    ROOM_INDEX_DATA *room = get_room_index(trolly_stops[n]);
    if (!street_room(room) || street_index.count(room->vnum)) continue;
    stops.push_back(add_street(room));
  }

  // Multi-source BFS visits at most MAX_STREET_ROOMS and ten exits per room.
  for (size_t head = 0; head < streets.size(); ++head) {
    ROOM_INDEX_DATA *room = get_room_index(streets[head].vnum);
    if (!street_room(room)) continue;
    for (int door = 0; door < 10; ++door) {
      EXIT_DATA *exit = room->exit[door];
      if (!open_exit(exit) || !street_room(exit->u1.to_room)) continue;
      const int target = add_street(exit->u1.to_room);
      if (target >= 0) streets[target].incoming.push_back(static_cast<int>(head));
    }
  }

  // Reverse distances to each trolley stop let every pedestrian reuse the
  // same shortest routes, including correctly handling one-way streets.
  for (size_t goal = 0; goal < stops.size(); ++goal) {
    std::vector<unsigned short> distance(streets.size(), UNREACHABLE);
    std::vector<int> pending(1, stops[goal]);
    distance[stops[goal]] = 0;
    for (size_t head = 0; head < pending.size(); ++head) {
      const int at = pending[head];
      for (int from : streets[at].incoming) {
        if (distance[from] != UNREACHABLE) continue;
        distance[from] = distance[at] + 1;
        pending.push_back(from);
      }
    }
    distances.push_back(distance);
  }

  // Only spawn/use destinations with a return route to another stop. An
  // isolated or one-way dead-end trolley stop must not strand new people.
  for (size_t a = 0; a < stops.size(); ++a) {
    for (size_t b = 0; b < stops.size(); ++b) {
      if (a != b && distances[a][stops[b]] != UNREACHABLE
          && distances[b][stops[a]] != UNREACHABLE) {
        spawn_stops.push_back(static_cast<int>(a));
        break;
      }
    }
  }
}

void ensure_routes() {
  if (!cache_built || current_time >= next_rebuild || current_time < last_rebuild)
    build_routes();
}

void retry_routes() {
  // A closed door can shorten the shared refresh interval, but thirty
  // blocked people still cause at most one rebuild per minute.
  const time_t retry = last_rebuild + BLOCKED_RETRY;
  if (retry < next_rebuild) next_rebuild = retry;
}

CHAR_DATA *carrier_in(CHAR_DATA *mob, ROOM_INDEX_DATA *room) {
  if (!room->people) return NULL;
  for (CHAR_DATA *actor : *room->people) {
    if (actor && actor != mob && actor->in_room == room
        && (actor->dragging == mob || actor->lifting == mob)
        && !is_helpless(actor) && !in_fight(actor)
        && !IS_FLAG(actor->act, PLR_SHROUD) && !IS_FLAG(actor->act, PLR_DEEPSHROUD))
      return actor;
  }
  return NULL;
}
} // namespace

extern "C" {

bool pedestrian_route_ready(void) {
  ensure_routes();
  return !spawn_stops.empty();
}

ROOM_INDEX_DATA *pedestrian_spawn_room(int slot) {
  ensure_routes();
  if (spawn_stops.empty()) return NULL;
  const size_t start = static_cast<unsigned int>(slot) % spawn_stops.size();
  for (size_t n = 0; n < spawn_stops.size(); ++n) {
    const int goal = spawn_stops[(start + n) % spawn_stops.size()];
    ROOM_INDEX_DATA *room = get_room_index(streets[stops[goal]].vnum);
    if (street_room(room) && !room_hostile(room)) return room;
  }
  retry_routes();
  return NULL;
}

void pedestrian_forget_route(CHAR_DATA *mob) {
  destinations.erase(mob);
}

bool pedestrian_move(CHAR_DATA *mob, int door, bool follow) {
  if (!pedestrian(mob) || !mob->in_room || !mob->in_room->area || door < 0 || door >= 10
      || mob->in_room->area->world != WORLD_EARTH || in_fight(mob)
      || mob->fistfighting || mob->fighting
      || IS_FLAG(mob->act, PLR_DEAD) || IS_FLAG(mob->act, PLR_SHROUD)
      || IS_FLAG(mob->act, PLR_DEEPSHROUD)) return false;
  ROOM_INDEX_DATA *from = mob->in_room;
  EXIT_DATA *exit = from->exit[door];
  if (!open_exit(exit)) return false;
  ROOM_INDEX_DATA *to = exit->u1.to_room;
  if (to == from || !to->area || to->area->world != WORLD_EARTH
      || IS_SET(to->room_flags, ROOM_NO_MOB)
      || to->sector_type == SECT_AIR || to->sector_type == SECT_ATMOSPHERE
      || to->sector_type == SECT_WATER || to->sector_type == SECT_UNDERWATER
      || to->sector_type == SECT_HELLGATE) return false;

  CHAR_DATA *carrier = follow ? carrier_in(mob, to) : NULL;
  if (!carrier && (is_helpless(mob) || mob->position <= POS_SITTING
      || IS_FLAG(mob->act, PLR_BOUND) || IS_FLAG(mob->act, PLR_BOUNDFEET))) return false;
  if (follow && !carrier && (!mob->master || mob->master->in_room != to
      || IS_FLAG(mob->master->act, PLR_SHROUD)
      || IS_FLAG(mob->master->act, PLR_DEEPSHROUD))) return false;
  if (!follow && (mob->master || !street_room(from) || !street_room(to))) return false;
  if (!carrier && (room_hostile(from) || room_hostile(to))) return false;

  mob->facing = door;
  mob->recent_moved = 10;
  mob->on = NULL;
  if (!carrier) act("$n walks $T.", mob, NULL, dir_name[door][0], TO_ROOM);
  char_from_room(mob);
  char_to_room(mob, to);
  mob->x = carrier ? carrier->x : get_exit_x(rev_dir[door], to);
  mob->y = carrier ? carrier->y : get_exit_y(rev_dir[door], to);
  if (!carrier) act("$n walks in.", mob, NULL, NULL, TO_ROOM);
  if (follow) pedestrian_forget_route(mob);
  return true;
}

bool pedestrian_walk_step(CHAR_DATA *mob) {
  if (!pedestrian(mob) || !mob->in_room || mob->master || is_helpless(mob)
      || in_fight(mob) || mob->fighting || mob->fistfighting
      || mob->position <= POS_SITTING || !street_room(mob->in_room)) return false;
  ensure_routes();
  std::map<int, int>::const_iterator here = street_index.find(mob->in_room->vnum);
  if (here == street_index.end() || spawn_stops.empty()) {
    retry_routes();
    return false;
  }
  const int at = here->second;
  int goal = -1;
  std::map<CHAR_DATA *, int>::const_iterator previous = destinations.find(mob);
  if (previous != destinations.end()) {
    for (int candidate : spawn_stops) {
      if (streets[stops[candidate]].vnum == previous->second
          && distances[candidate][at] != UNREACHABLE && distances[candidate][at] > 0) {
        goal = candidate;
        break;
      }
    }
  }
  if (goal < 0) {
    int candidates[MAX_STOPS];
    int count = 0;
    for (int candidate : spawn_stops)
      if (distances[candidate][at] != UNREACHABLE && distances[candidate][at] > 0)
        candidates[count++] = candidate;
    if (!count) return false;
    goal = candidates[number_range(0, count - 1)];
    destinations[mob] = streets[stops[goal]].vnum;
  }
  for (int door = 0; door < 10; ++door) {
    EXIT_DATA *exit = mob->in_room->exit[door];
    if (!open_exit(exit) || !street_room(exit->u1.to_room)) continue;
    std::map<int, int>::const_iterator next = street_index.find(exit->u1.to_room->vnum);
    if (next == street_index.end() || distances[goal][next->second] >= distances[goal][at]) continue;
    if (pedestrian_move(mob, door, false)) return true;
  }
  retry_routes();
  return false;
}

} // extern "C"
