#include "merc.h"
#include <functional>
#include <unordered_map>

namespace {
using Order = unsigned long long;
struct CombatIndex {
    Order sequence = 0;
    std::unordered_map<CHAR_DATA *, Order> live;
    std::map<Order, CHAR_DATA *, std::greater<Order>> active;
};
CombatIndex &combat_index() {
    static CombatIndex index;
    return index;
}
}

extern "C" void register_live_character(CHAR_DATA *ch) {
    auto &index = combat_index();
    auto old = index.live.find(ch);
    if (old != index.live.end()) index.active.erase(old->second);
    const Order order = ++index.sequence;
    index.live[ch] = order;
    if (ch->in_fight) index.active[order] = ch;
}

extern "C" void unregister_live_character(CHAR_DATA *ch) {
    auto &index = combat_index();
    auto found = index.live.find(ch);
    if (found == index.live.end()) return;
    index.active.erase(found->second);
    index.live.erase(found);
}

extern "C" void set_combat_state(CHAR_DATA *ch, bool fighting) {
    ch->in_fight = fighting;
    auto &index = combat_index();
    auto found = index.live.find(ch);
    // Offline characters enter the index when added to char_list.
    if (found == index.live.end()) return;
    if (fighting) index.active[found->second] = ch;
    else index.active.erase(found->second);
}

extern "C" CHAR_DATA *next_combat_character(unsigned long long *cursor) {
    auto &active = combat_index().active;
    // No iterator survives a gameplay callback. Newly activated older characters
    // retain their place in char_list; newly spawned push_front entries wait.
    auto found = *cursor ? active.upper_bound(*cursor) : active.begin();
    if (found == active.end()) return nullptr;
    *cursor = found->first;
    return found->second;
}
