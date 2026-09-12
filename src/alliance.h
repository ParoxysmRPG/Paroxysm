#ifndef HAVEN_ALLIANCE_H
#define HAVEN_ALLIANCE_H

// IDs are persisted in faction files and territory support slots. Keep the
// surviving IDs stable; the retired slot is handled only when loading data.
enum Alliance { ALLIANCE_NONE = 0, ALLIANCE_SIDELEFT = 1, ALLIANCE_SIDERIGHT = 3 };
constexpr int ALLIANCE_COUNT = 2;
constexpr int alliance_sides[ALLIANCE_COUNT] = {ALLIANCE_SIDELEFT, ALLIANCE_SIDERIGHT};
constexpr int TERRITORY_SUPPORT_SLOTS = 20; // Shared, persisted faction storage.

inline bool is_alliance(int side) {
  return side == ALLIANCE_SIDELEFT || side == ALLIANCE_SIDERIGHT;
}

inline int opposing_alliance(int side) {
  return side == ALLIANCE_SIDELEFT ? ALLIANCE_SIDERIGHT
       : side == ALLIANCE_SIDERIGHT ? ALLIANCE_SIDELEFT : ALLIANCE_NONE;
}

#endif
