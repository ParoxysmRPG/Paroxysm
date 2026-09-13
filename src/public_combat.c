#include "merc.h"
#include "global.h"

extern "C" {

bool public_target_excluded(CHAR_DATA *ch, CHAR_DATA *victim) {
  // Preserve the existing ROOM_PUBLIC target exclusion and breach/enforcer
  // handling, with exceptions for dissenting crowds, full-moon packs and
  // the two participants in a sin encounter.
  if (state_of_emergency() || !ch || !victim || cortex_breach_monster(ch) || cortex_breach_monster(victim)
      || dissent_crowd(ch) || dissent_crowd(victim)
      || full_moon_pack(ch) || full_moon_pack(victim)) return FALSE;
  if (sin_vigilante_target(ch, victim) || sin_vigilante_target(victim, ch)) return FALSE;
  return (victim->in_room && IS_SET(victim->in_room->room_flags, ROOM_PUBLIC)
          && !IS_FLAG(victim->act, PLR_SHROUD))
      || (ch->in_room && IS_SET(ch->in_room->room_flags, ROOM_PUBLIC)
          && !IS_FLAG(ch->act, PLR_SHROUD));
}

bool cortex_public_enforcer(CHAR_DATA *ch) {
  return cortex_enforcer(ch) && IS_FLAG(ch->act, ACT_CORTEX_PUBLIC);
}

void cortex_public_response(CHAR_DATA *attacker, CHAR_DATA *defender) {
  if (sin_vigilante_target(defender, attacker)) return;
  if (state_of_emergency() || !attacker || !defender || attacker == defender || IS_NPC(attacker)
      || !attacker->pcdata || !attacker->in_room || !defender->in_room
      || IS_FLAG(attacker->act, PLR_SHROUD) || IS_FLAG(attacker->act, PLR_DEEPSHROUD)
      || IS_FLAG(defender->act, PLR_SHROUD) || IS_FLAG(defender->act, PLR_DEEPSHROUD)
      || dissent_in_room(attacker->in_room) || dissent_in_room(defender->in_room)) return;
  for (CHAR_DATA *mob : char_list)
    if (cortex_public_enforcer(mob) && mob->ttl > 0
        && !str_cmp(mob->aggression, attacker->name)) return;

  MOB_INDEX_DATA *index = get_mob_index(CORTEX_SOLDIER);
  if (!index) return;
  act("Cortex enforcers arrive to defend $N and subdue you for starting a public fight!", attacker, NULL, defender, TO_CHAR);
  act("Cortex enforcers arrive to defend you and subdue $n!", attacker, NULL, defender, TO_VICT);
  act("Cortex enforcers arrive to defend $N and subdue $n!", attacker, NULL, defender, TO_NOTVICT);
  const int difficulty = number_range(1, 10);
  const int count = cortex_encounter_count(attacker);
  for (int n = 0; n < count; ++n) {
    CHAR_DATA *mob = create_mobile(index);
    SET_FLAG(mob->act, ACT_CORTEX_ENFORCER);
    SET_FLAG(mob->act, ACT_CORTEX_PUBLIC);
    REMOVE_FLAG(mob->act, ACT_SENTINEL); // Sentinels cannot stay in combat.
    mob->faction = FACTION_CORTEX;
    mob->ttl = 12;
    free_string(mob->name);
    mob->name = str_dup("cortex enforcer armored soldier");
    free_string(mob->short_descr);
    mob->short_descr = str_dup("an armored Cortex enforcer");
    free_string(mob->long_descr);
    mob->long_descr = str_dup("An armored Cortex enforcer moves to subdue the public aggressor.\n\r");
    free_string(mob->description);
    mob->description = str_dup("This armored Cortex enforcer has come to defend the victim of a public attack and knock out the aggressor.\n\r");
    free_string(mob->aggression);
    mob->aggression = str_dup(attacker->name);
    free_string(mob->protecting);
    mob->protecting = str_dup(defender->name);
    cortex_scale_enforcer(mob, attacker, difficulty);
    char_to_room(mob, defender->in_room);
    mob->x = defender->x;
    mob->y = defender->y;
    mob->hit = max_hp(mob);
    start_fight(mob, attacker);
  }
}

void cortex_public_update(void) {
  for (CHAR_DATA *mob : char_list) {
    if (!cortex_public_enforcer(mob) || mob->ttl <= 0) continue;
    CHAR_DATA *attacker = get_char_world_pc(mob->aggression);
    if (!state_of_emergency() && attacker && attacker->in_room && !is_helpless(attacker)
        && attacker->wounds < 3 && !IS_FLAG(attacker->act, PLR_SHROUD)
        && !IS_FLAG(attacker->act, PLR_DEEPSHROUD)
        && !dissent_in_room(attacker->in_room) && !dissent_in_room(mob->in_room)) continue;
    // The attacker is already subdued, has left, or is in the nightmare.
    // Do not let the squad switch to the defender or unrelated bystanders.
    act("The Cortex enforcer withdraws.", mob, NULL, NULL, TO_ROOM);
    free_string(mob->aggression);
    mob->aggression = str_dup("");
    mob->ttl = 0;
    set_combat_state(mob, FALSE);
  }
}

} // extern "C"
