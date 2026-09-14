#ifndef HAVEN_LOCAL_MAP_H
#define HAVEN_LOCAL_MAP_H

#include <string>
#include "merc.h"

namespace haven {

// Physical metadata shared by exploration and combat-map vertical markers.
// Visibility and reachability are checked by each renderer for its viewer.
bool ordinary_map_vertical_route(const ROOM_INDEX_DATA *room, const EXIT_DATA *exit);

// Optional per-call instrumentation; the renderer never changes game state.
struct LocalMapStats {
  int rooms;
  int exits_examined;
  int visibility_checks;
};

// A bounded schematic of visible, connected rooms on the origin's floor.
// Compact maps visit at most 9 rooms and fit a 13-column, 7-line frame;
// full maps visit at most 165. Both narrow for small terminal widths.
std::string render_local_map(CHAR_DATA *viewer, ROOM_INDEX_DATA *origin,
                             bool compact, LocalMapStats *stats = NULL);

}

#endif
