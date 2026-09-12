#ifndef HAVEN_EQUIPMENT_SNAPSHOT_H
#define HAVEN_EQUIPMENT_SNAPSHOT_H

#include "merc.h"

namespace haven {
// Operation-local: never retain across inventory mutations or callbacks.
class EquipmentSnapshot {
    OBJ_DATA *slots_[MAX_WEAR] = {};
public:
    explicit EquipmentSnapshot(CHAR_DATA *ch) {
        int count = 0;
        for (OBJ_DATA *obj = ch ? ch->carrying : nullptr;
             obj && count < 200; obj = obj->next_content, ++count) {
            const int slot = obj->wear_loc;
            if (slot >= 0 && slot < MAX_WEAR && !slots_[slot])
                slots_[slot] = obj;
        }
    }
    OBJ_DATA *get(int slot) const {
        if (slot < 0 || slot >= MAX_WEAR) return nullptr;
        if (slot == WEAR_HOLD && !slots_[slot]) return slots_[WEAR_HOLD_2];
        return slots_[slot];
    }
};
}
// Explicit snapshots never survive an inventory mutation or gameplay callback.
extern "C" bool can_see_wear_equipped(CHAR_DATA *ch, int slot,
                                     const haven::EquipmentSnapshot &equipment);
extern "C" bool is_covered_equipped(CHAR_DATA *ch, int cover,
                                   const haven::EquipmentSnapshot &equipment);
#endif
