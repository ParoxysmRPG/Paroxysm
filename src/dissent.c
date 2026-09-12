#include "merc.h"
#include "global.h"
#include <algorithm>
#include <cstdio>

extern "C" {

static const int DISSENT_DURATION = 30 * 60;
static const int DISSENT_COOLDOWN = 7 * 24 * 60 * 60;
static const int DISSENT_SOCIETY_REWARD = 1000;
static const int DISSENT_CORTEX_REWARD = 10000;
static time_t dissent_until = 0;

bool dissent_crowd(CHAR_DATA *ch) {
  return ch && IS_NPC(ch) && IS_FLAG(ch->act, ACT_DISSENT_CROWD);
}

static bool dissent_society(FACTION_TYPE *fac) {
  return fac && fac->valid && fac->vnum > 0 && fac->type == FACTION_SOCIETY;
}

bool dissent_participant(CHAR_DATA *ch) {
  return ch && !IS_NPC(ch) && ch->pcdata
      && !IS_FLAG(ch->act, PLR_SHROUD) && !IS_FLAG(ch->act, PLR_DEEPSHROUD)
      && (ch->fcore == FACTION_CORTEX
          || dissent_society(clan_lookup(ch->fsociety))
          || dissent_society(clan_lookup(ch->legacy_society)));
}

static CHAR_DATA *dissent_mob() {
  for (CHAR_DATA *mob : char_list)
    if (dissent_crowd(mob) && mob->wounds < 4) return mob;
  return NULL;
}

bool dissent_in_room(ROOM_INDEX_DATA *room) {
  if (!dissent_until || !room) return FALSE;
  CHAR_DATA *mob = dissent_mob();
  return mob && mob->in_room == room && !IS_FLAG(mob->act, PLR_SHROUD)
      && !IS_FLAG(mob->act, PLR_DEEPSHROUD);
}

static void dissent_broadcast(const char *message) {
  for (DESCRIPTOR_DATA *d : descriptor_list)
    if (d->connected == CON_PLAYING && dissent_participant(d->character))
      send_to_char(message, d->character);
}

static void dissent_finish(CHAR_DATA *mob, bool success) {
  if (!dissent_until) return;
  dissent_until = 0; // Settle exactly once, even if multiple attacks land together.
  char buf[MSL];
  if (success) {
    for (FACTION_TYPE *fac : FacVect) {
      if (!dissent_society(fac)) continue;
      fac->resource += DISSENT_SOCIETY_REWARD;
      snprintf(buf, sizeof(buf), "Dissent succeeded: the dissenting mob held out. Reward: $%d.",
          DISSENT_SOCIETY_REWARD * 10);
      send_log(fac->vnum, buf);
    }
    snprintf(buf, sizeof(buf), "Dissent successful! The dissenting mob has held out for thirty minutes and disperses. Every player society receives $%d in resources.\n\r",
        DISSENT_SOCIETY_REWARD * 10);
  } else {
    FACTION_TYPE *cortex = clan_lookup(FACTION_CORTEX);
    if (cortex) {
      cortex->resource += DISSENT_CORTEX_REWARD;
      snprintf(buf, sizeof(buf), "Dissent suppressed: the dissenting mob was knocked out. Reward: $%d.",
          DISSENT_CORTEX_REWARD * 10);
      send_log(cortex->vnum, buf);
    }
    snprintf(buf, sizeof(buf), "Dissent unsuccessful! The dissenting mob has been knocked out and the protest suppressed. Cortex receives $%d in resources.\n\r",
        DISSENT_CORTEX_REWARD * 10);
  }
  dissent_broadcast(buf);
  save_clans(FALSE);
  if (mob) {
    act(success ? "The dissenting mob cheers its defiance of Cortex and disperses."
                : "The dissenting mob collapses, its protest silenced.", mob, NULL, NULL, TO_ROOM);
    // Combat callers still reference the NPC after damage. Retire it just as
    // other patrol NPCs retire, and let mobile_update safely extract it.
    mob->hit = 0;
    mob->wounds = 4;
    set_combat_state(mob, FALSE);
    mob->attacking = 0;
    mob->ttl = 1;
    char_from_room(mob);
    char_to_room(mob, get_room_index(ROOM_VNUM_LIMBO));
  }
}

void dissent_defeated(CHAR_DATA *mob) {
  if (dissent_crowd(mob)) dissent_finish(mob, FALSE);
}

void dissent_update(void) {
  if (!dissent_until) return;
  CHAR_DATA *mob = dissent_mob();
  if (!mob || !mob->in_room) {
    // A purge or other administrative removal is not a Cortex victory.
    dissent_until = 0;
    dissent_broadcast("Dissent cancelled: the dissenting mob is no longer present. No rewards were awarded.\n\r");
  } else if (mob->hit <= 0 || mob->wounds >= 2) {
    dissent_finish(mob, FALSE);
  } else if (current_time >= dissent_until) {
    dissent_finish(mob, TRUE);
  }
}

static bool dissent_room(ROOM_INDEX_DATA *room) {
  if (!room || !room->area || room->area->vnum != HAVEN_TOWN_VNUM
      || room->sector_type != SECT_STREET || room->z != 0
      || IS_SET(room->room_flags, ROOM_INDOORS | ROOM_PRIVATE | ROOM_SAFE | ROOM_INVISIBLE))
    return FALSE;
  for (int door = 0; door < 10; ++door) {
    EXIT_DATA *exit = room->exit[door];
    if (exit && exit->u1.to_room && !IS_SET(exit->exit_info, EX_CLOSED)
        && (exit->wall == WALL_NONE || exit->wallcondition == WALLCOND_HOLE)) return TRUE;
  }
  return FALSE;
}

bool dissent_launch(CHAR_DATA *ch) {
  FACTION_TYPE *cortex = clan_lookup(FACTION_CORTEX);
  if (!cortex || !dissent_participant(ch) || !ch->in_room || !free_to_act(ch)
      || is_gm(ch) || higher_power(ch) || IS_FLAG(ch->act, PLR_STASIS)
      || event_cleanse || dissent_until
      || (cortex->last_dissent > 0 && current_time < (time_t)cortex->last_dissent + DISSENT_COOLDOWN))
    return FALSE;
  bool attackers = FALSE, defenders = FALSE;
  for (DESCRIPTOR_DATA *d : descriptor_list) {
    CHAR_DATA *to = d->character;
    if (d->connected != CON_PLAYING || !dissent_participant(to) || !to->in_room
        || !free_to_act(to) || is_gm(to) || higher_power(to)
        || IS_FLAG(to->comm, COMM_AFK) || IS_FLAG(to->act, PLR_STASIS)) continue;
    if (to->fcore == FACTION_CORTEX) attackers = TRUE;
    else defenders = TRUE;
  }
  if (!attackers || !defenders) return FALSE;

  MOB_INDEX_DATA *index = get_mob_index(115); // Combat-capable adversary template.
  if (!index) return FALSE;
  ROOM_INDEX_DATA *room = NULL;
  int count = 0;
  for (int hash = 0; hash < MAX_KEY_HASH; ++hash)
    for (ROOM_INDEX_DATA *candidate = room_index_hash[hash]; candidate; candidate = candidate->next)
      if (dissent_room(candidate) && number_range(1, ++count) == 1) room = candidate;
  if (!room) return FALSE;

  const int previous_start = cortex->last_dissent;
  cortex->last_dissent = current_time;
  if (!save_clans(FALSE)) {
    cortex->last_dissent = previous_start;
    return FALSE; // Never launch without a durable weekly cooldown.
  }
  CHAR_DATA *mob = create_mobile(index);
  SET_FLAG(mob->act, ACT_DISSENT_CROWD);
  // ACT_SENTINEL NPCs are excluded by the combat engine. Movement is instead
  // suppressed in mobile_update, so this stationary crowd remains attackable.
  REMOVE_FLAG(mob->act, ACT_SENTINEL);
  REMOVE_FLAG(mob->act, ACT_AGGRESSIVE);
  mob->faction = 0;
  mob->ttl = 12 * 35; // Positive TTL is required for combat; wall clock ends dissent.
  free_string(mob->name);
  mob->name = str_dup("crowd dissent dissenting mob protesters");
  free_string(mob->short_descr);
  mob->short_descr = str_dup("a crowd");
  free_string(mob->long_descr);
  mob->long_descr = str_dup("A crowd forms a dissenting mob, chanting defiance against Cortex.\n\r");
  free_string(mob->description);
  mob->description = str_dup("This dissenting mob is a crowd of townspeople protesting Cortex's rule. Raised placards and angry chants demand freedom from Cortex. They stand together, determined to keep their dissent alive.\n\r");
  std::fill(mob->disciplines, mob->disciplines + MAX_DIS, 0);
  mob->disciplines[DIS_TOUGHNESS] = 100;
  char_to_room(mob, room);
  mob->x = room->size / 2;
  mob->y = room->size / 2;
  mob->hit = max_hp(mob);
  dissent_until = current_time + DISSENT_DURATION;
  act("A crowd gathers into a dissenting mob, raising placards and chanting against Cortex!", mob, NULL, NULL, TO_ROOM);
  char buf[MSL];
  snprintf(buf, sizeof(buf), "Dissent patrol: a dissenting mob is protesting Cortex at %s in %s (map %d, %d). Cortex must knock out the crowd; player societies must keep it alive for thirty minutes. Use 'attack crowd' to start combat, or 'patrol dissent' for its current location and remaining time.\n\r",
      roomtitle(mob->in_room, FALSE), mob->in_room->area->name, mob->in_room->x, mob->in_room->y);
  dissent_broadcast(buf);
  return TRUE;
}

void dissent_status(CHAR_DATA *ch) {
  if (!dissent_participant(ch)) {
    send_to_char("Dissent patrols involve only Cortex and player societies.\n\r", ch);
    return;
  }
  dissent_update();
  CHAR_DATA *mob = dissent_until ? dissent_mob() : NULL;
  if (!mob || !mob->in_room) {
    send_to_char("There is no active dissent patrol. Dissents can begin at most once every seven days.\n\r", ch);
    return;
  }
  printf_to_char(ch, "Dissent: a dissenting mob is protesting Cortex at %s in %s (map %d, %d). %d minute(s) remain. %s\n\r",
      roomtitle(mob->in_room, FALSE), mob->in_room->area->name, mob->in_room->x, mob->in_room->y,
      (int)((dissent_until - current_time + 59) / 60),
      ch->fcore == FACTION_CORTEX ? "Knock out the crowd to suppress the dissent (attack crowd)."
          : "Keep the crowd alive until the dissent ends to reward every player society.");
}

} // extern "C"
