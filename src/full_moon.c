#include "merc.h"
#include "global.h"
#include <vector>

extern "C" {
void wound_check(CHAR_DATA *ch, CHAR_DATA *victim, int wounds);

bool full_moon_pack(CHAR_DATA *ch) {
  return ch && IS_NPC(ch) && IS_FLAG(ch->act, ACT_FULL_MOON_PACK);
}

bool full_moon_night() {
  const int phase = sunphase(NULL);
  return full_moon() && (phase < 2 || phase == 7);
}

bool full_moon_pack_target(CHAR_DATA *mob, CHAR_DATA *victim) {
  return full_moon_pack(mob) && mob->ttl != 0 && mob->wounds < 2
      && victim && !IS_NPC(victim) && victim->pcdata
      && victim->in_room == mob->in_room && victim->wounds < 3
      && !is_werewolf(victim) && !is_helpless(victim)
      && !is_gm(victim) && !IS_IMMORTAL(victim) && !is_ghost(victim)
      && victim->desc && !IS_FLAG(victim->comm, COMM_AFK)
      && !IS_FLAG(victim->act, PLR_SHROUD)
      && !IS_FLAG(victim->act, PLR_DEEPSHROUD)
      && can_see(mob, victim);
}

CHAR_DATA *full_moon_pack_prey(CHAR_DATA *mob) {
  if (!mob || !mob->in_room) return NULL;
  for (CHAR_DATA *victim : *mob->in_room->people)
    if (full_moon_pack_target(mob, victim)) return victim;
  return NULL;
}

void full_moon_pack_defeat(CHAR_DATA *mob, CHAR_DATA *victim) {
  if (!full_moon_pack_target(mob, victim)) return;
  record_critical_injury(victim, mob, TRUE);
  invalidate_wound_treatment(victim);
  victim->wounds = 3;
  victim->heal_timer = 4300;
  victim->death_timer = 720;
  victim->hit = 0;
  SET_FLAG(victim->act, PLR_WOLFBIT);
  wound_check(mob, victim, 3);
  miscarriage(victim, FALSE);
  set_combat_state(victim, FALSE);
  send_to_char("`RThe pack leaves you critically wounded with an infected bite!`x\n\r"
               "Cauterize your bite with 'cauterize <your name>'. This costs no karma, "
               "but caps your lifeforce at 10 for fourteen days.\n\r", victim);
  act("`RThe pack savages $n, leaving a critical wound and an infected bite.`x",
      victim, NULL, NULL, TO_ROOM);
}

static bool pack_room(ROOM_INDEX_DATA *room) {
  return room && room->area && room->vnum > 300
      && room->area->world == WORLD_EARTH && in_haven(room)
      && !battleground(room) && !institute_room(room)
      && !IS_SET(room->room_flags, ROOM_INDOORS | ROOM_NO_MOB | ROOM_PRIVATE | ROOM_SAFE)
      && (room->sector_type == SECT_STREET || room->sector_type == SECT_FOREST);
}

void full_moon_pack_update() {
  static bool spawned = false;
  if (!full_moon_night()) {
    spawned = false;
    // Extraction belongs to mobile_update, outside combat/list iteration.
    for (CHAR_DATA *mob : char_list) {
      if (!full_moon_pack(mob)) continue;
      mob->ttl = 0;
      set_combat_state(mob, FALSE);
    }
    return;
  }
  if (!spawned) {
    MOB_INDEX_DATA *index = get_mob_index(40); // Existing dire-wolf combat template.
    if (!index) return;
    std::vector<ROOM_INDEX_DATA *> rooms;
    for (int bucket = 0; bucket < MAX_KEY_HASH; ++bucket)
      for (ROOM_INDEX_DATA *room = room_index_hash[bucket]; room; room = room->next)
        if (pack_room(room)) rooms.push_back(room);
    for (int pack = 0; pack < 3 && !rooms.empty(); ++pack) {
      const int chosen = number_range(0, static_cast<int>(rooms.size()) - 1);
      ROOM_INDEX_DATA *room = rooms[chosen];
      rooms.erase(rooms.begin() + chosen);
      for (int member = 0; member < 2; ++member) {
        CHAR_DATA *mob = create_mobile(index);
        SET_FLAG(mob->act, ACT_FULL_MOON_PACK);
        SET_FLAG(mob->act, ACT_SENTINEL);
        mob->ttl = -1; // The lunar event owns lifetime, not the generic TTL.
        free_string(mob->name);
        mob->name = str_dup("full moon werewolf wolf pack");
        free_string(mob->short_descr);
        mob->short_descr = str_dup("a moon-maddened werewolf");
        free_string(mob->long_descr);
        mob->long_descr = str_dup("`RA moon-maddened werewolf prowls with its pack here.`x\n\r");
        char_to_room(mob, room);
        mob->x = number_range(0, room->size);
        mob->y = number_range(0, room->size);
        mob->hit = max_hp(mob);
      }
    }
    spawned = true;
  }
  for (CHAR_DATA *mob : char_list) {
    if (!full_moon_pack(mob) || mob->ttl == 0 || in_fight(mob)) continue;
    CHAR_DATA *prey = full_moon_pack_prey(mob);
    if (prey) start_fight(mob, prey);
  }
}

}
