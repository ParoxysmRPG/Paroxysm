#ifndef HAVEN_COMBAT_MAP_H
#define HAVEN_COMBAT_MAP_H

#include <string>
#include <vector>
#include "merc.h"

namespace haven {

struct CombatMapEntry {
  CHAR_DATA *character = NULL;
  int x = 0;
  int y = 0;
  int z = 0;
  int distance = 0;
  std::string label;
  std::string display_name;
  int overlap_count = 1;
  int map_objective = -1;
  bool is_cover = false;
  bool is_turret = false;
  // Visible shelter within one local coordinate, indexed in this snapshot.
  int cover_entry = -1;
  // Coarse map-cell overlap is distinct from actual cover protection.
  int cell_cover_count = 0;
};

// Owned by one draw/scan, so visibility and overlap never leak between viewers.
struct CombatMapSnapshot {
  std::vector<CombatMapEntry> entries;
};

struct CombatMapCell {
  int entry = -1;
  int count = 0;
  int cover_count = 0;
};

CombatMapSnapshot combat_map_snapshot(CHAR_DATA *viewer);
std::vector<CombatMapCell> combat_map_cells(
    CHAR_DATA *viewer, const CombatMapSnapshot &snapshot, int size);
void show_combat_map_roster(CHAR_DATA *viewer,
                            const CombatMapSnapshot &snapshot);

}

#endif
