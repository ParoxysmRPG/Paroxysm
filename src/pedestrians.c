#include "merc.h"
#include "global.h"
#include "performance.h"
#include <unordered_map>

namespace {
const unsigned POPULATION = 30;
const int WALK_SECONDS = 15;
const int BOUND_SECONDS = 6 * 3600;
const int SICK_SECONDS = 30 * 60;
const int KO_SECONDS = 10 * 60;
const int FOLLOW_SECONDS = 30 * 60;
const int STUCK_SECONDS = 5 * 60;
const int LF_REWARD = 100; // One displayed LF; never hunger/feeding credit.
const int HYPNOSIS_ALARM_PERCENT = 20;

struct PedestrianState {
  time_t bound_since = 0;
  time_t sick_since = 0;
  time_t unconscious_until = 0;
  time_t following_until = 0;
  time_t next_move = 0;
  time_t stuck_since = 0;
  std::string intro;
};
std::unordered_map<CHAR_DATA *, PedestrianState> pedestrians;
time_t next_spawn = 0;
unsigned spawn_sequence = 0;

bool bound(CHAR_DATA *mob) {
  return IS_FLAG(mob->act, PLR_BOUND) || IS_FLAG(mob->act, PLR_BOUNDFEET);
}

void replace_text(char *&field, const std::string &value) {
  free_string(field);
  field = str_dup(value.c_str());
}

void outfit(CHAR_DATA *mob, int vnum, int slot, const char *name, const char *intro) {
  OBJ_INDEX_DATA *index = get_obj_index(vnum);
  if (!index || index->item_type != ITEM_CLOTHING) return;
  OBJ_DATA *obj = create_object(index, 0);
  if (!obj) return;
  replace_text(obj->name, name);
  replace_text(obj->short_descr, intro);
  replace_text(obj->description, std::string(intro) + " lies here.");
  obj->cost = 100; // Cheap, ordinary clothes, not a lucrative spawn source.
  obj_to_char(obj, mob);
  equip_char_silent(mob, obj, slot);
}

void spawn_pedestrian() {
  if (pedestrians.size() >= POPULATION || !pedestrian_route_ready()) return;
  ROOM_INDEX_DATA *room = pedestrian_spawn_room(spawn_sequence);
  MOB_INDEX_DATA *index = get_mob_index(115);
  if (!room || !index || index->pShop) return;
  CHAR_DATA *mob = create_mobile(index);
  SET_INIT(mob->act);
  SET_INIT(mob->affected_by);
  SET_FLAG(mob->act, ACT_IS_NPC);
  SET_FLAG(mob->act, ACT_PEDESTRIAN);
  mob->race = RACE_HUMAN;
  mob->level = 1;
  mob->ttl = -1; // This subsystem owns lifetime, not generic prey/TTL logic.
  mob->faction = mob->factiontwo = mob->factiontrue = 0;
  mob->fcore = mob->fsociety = mob->legacy_society = 0;
  mob->sex = number_range(SEX_MALE, SEX_FEMALE);
  mob->position = mob->start_pos = mob->default_pos = POS_STANDING;
  mob->money = number_range(200, 1000); // $2-$10, in cents.
  mob->lifeforce = LF_REWARD;
  std::fill(mob->skills, mob->skills + SKILL_MAX, 0);
  std::fill(mob->wilds_skills, mob->wilds_skills + SKILL_MAX, 0);
  std::fill(mob->other_skills, mob->other_skills + SKILL_MAX, 0);
  std::fill(mob->godrealm_skills, mob->godrealm_skills + SKILL_MAX, 0);
  std::fill(mob->hell_skills, mob->hell_skills + SKILL_MAX, 0);
  std::fill(mob->disciplines, mob->disciplines + MAX_DIS, 0);
  replace_text(mob->aggression, "");
  replace_text(mob->protecting, "");
  static const char *looks[] = {
    "a brown-haired", "a dark-haired", "a fair-haired", "a grey-haired",
    "a short-haired", "a curly-haired", "a stocky", "a slender"
  };
  const char *gender = mob->sex == SEX_FEMALE ? "woman" : "man";
  PedestrianState &state = pedestrians[mob];
  state.intro = std::string(looks[number_range(0, 7)]) + " " + gender;
  state.next_move = current_time + WALK_SECONDS;
  replace_text(mob->name, std::string("pedestrian passerby commuter human ") + gender + " " + state.intro);
  replace_text(mob->short_descr, state.intro);
  replace_text(mob->long_descr, state.intro);
  replace_text(mob->description, "An ordinary adult townsperson, dressed for an unremarkable day of errands and trolley journeys.\n\r");
  const bool dark = number_percent() <= 50;
  outfit(mob, OBJ_VNUM_SHIRT, WEAR_BODY_1,
      dark ? "grey cotton shirt" : "blue cotton shirt",
      dark ? "a plain grey cotton shirt" : "a plain blue cotton shirt");
  outfit(mob, OBJ_VNUM_JEANS, WEAR_BODY_2, "dark trousers pants", "a pair of plain dark trousers");
  outfit(mob, OBJ_VNUM_SHOES, WEAR_BODY_3, "worn shoes", "a pair of worn everyday shoes");
  char_to_room(mob, room);
  mob->x = mob->y = UMAX(0, room->size / 2);
  mob->hit = max_hp(mob);
  ++spawn_sequence;
  act("$n joins the foot traffic.", mob, NULL, NULL, TO_ROOM);
}
} // namespace

extern "C" {
bool pedestrian(CHAR_DATA *mob) {
  return mob && IS_NPC(mob) && IS_FLAG(mob->act, ACT_PEDESTRIAN)
      && (!mob->pIndexData || !mob->pIndexData->pShop);
}

bool pedestrian_helpless(CHAR_DATA *mob) {
  return pedestrian(mob) && (bound(mob) || mob->position <= POS_SLEEPING);
}

void pedestrian_forget(CHAR_DATA *mob) {
  if (pedestrians.erase(mob)) pedestrian_forget_route(mob);
}

void pedestrian_bound(CHAR_DATA *mob) {
  if (!pedestrian(mob)) return;
  PedestrianState &state = pedestrians[mob];
  if (bound(mob)) {
    if (!state.bound_since) state.bound_since = current_time;
    state.stuck_since = 0;
  } else {
    state.bound_since = 0;
  }
}

void pedestrian_knockout(CHAR_DATA *mob) {
  if (!pedestrian(mob) || mob->position <= POS_SLEEPING) return;
  PedestrianState &state = pedestrians[mob];
  state.unconscious_until = current_time + KO_SECONDS;
  state.following_until = state.stuck_since = 0;
  mob->master = NULL;
  mob->hit = 0;
  mob->wounds = 0;
  mob->position = POS_SLEEPING;
  mob->fighting = FALSE;
  if (mob->fistfighting && mob->fistfighting->fistfighting == mob)
    mob->fistfighting->fistfighting = NULL;
  mob->fistfighting = NULL;
  mob->fistattack = mob->fisttimer = 0;
  mob->attacking = 0;
  mob->cfighting = mob->target = mob->target_2 = mob->target_3 = NULL;
  set_combat_state(mob, FALSE);
  act("$n collapses, unconscious.", mob, NULL, NULL, TO_ROOM);
}

bool pedestrian_drain(CHAR_DATA *actor, CHAR_DATA *mob) {
  if (!pedestrian(mob) || !actor || IS_NPC(actor) || !actor->pcdata
      || !actor->in_room || actor->in_room != mob->in_room) return FALSE;
  PedestrianState &state = pedestrians[mob];
  if (state.sick_since) {
    send_to_char("They're drained dry.\n\r", actor);
    return FALSE;
  }
  if (!pedestrian_helpless(mob)) {
    send_to_char("Maybe you should tie them up first.\n\r", actor);
    return FALSE;
  }
  state.sick_since = current_time;
  if (state.intro.empty()) state.intro = mob->short_descr;
  std::string intro = state.intro;
  if (intro.compare(0, 2, "a ") == 0) intro.insert(2, "sickly ");
  else intro = "a sickly " + intro;
  replace_text(mob->short_descr, intro);
  replace_text(mob->long_descr, intro);
  replace_text(mob->description, "This ordinary adult townsperson looks sickly, pale and drained after losing what little life force they had to spare.\n\r");
  replace_text(mob->name, std::string(mob->name) + " sickly drained");
  mob->lifeforce = 0;
  give_lifeforce_nouse(actor, LF_REWARD, (char *)"pedestrian drain");
  send_to_char("You gain 1 LF from their meagre reserves. This does not satisfy your feeding requirement.\n\r", actor);
  if (in_public(actor, mob)) cortex_public_response(actor, mob);
  return TRUE;
}

bool pedestrian_hypnotise(CHAR_DATA *actor, CHAR_DATA *mob, const char *argument) {
  if (!pedestrian(mob) || !actor || IS_NPC(actor) || !actor->pcdata
      || !actor->in_room || actor->in_room != mob->in_room) return FALSE;
  if (!argument || (str_cmp(argument, "follow") && str_cmp(argument, "release"))) {
    send_to_char("Syntax: hypnotize <pedestrian> follow/release\n\r", actor);
    return FALSE;
  }
  if (!str_cmp(argument, "release")) {
    if (mob->master != actor) {
      send_to_char("They aren't following you.\n\r", actor);
      return FALSE;
    }
    stop_follower(mob);
    pedestrians[mob].following_until = 0;
    return TRUE;
  }
  if (get_skill(actor, SKILL_HYPNOTISM) < 1) {
    send_to_char("You don't have that skill.\n\r", actor);
    return FALSE;
  }
  if (is_helpless(actor) || is_pinned(actor) || is_ghost(actor) || is_dreaming(actor)
      || in_fight(actor) || in_fight(mob) || pedestrian_helpless(mob)
      || is_mute(actor) || IS_FLAG(actor->comm, COMM_GAG) || is_deaf(mob)
      || IS_FLAG(actor->act, PLR_SHROUD) || IS_FLAG(actor->act, PLR_DEEPSHROUD)) {
    send_to_char("You can't get them to follow you like this.\n\r", actor);
    return FALSE;
  }
  if (mob->master) {
    send_to_char(mob->master == actor ? "They're already following you.\n\r"
        : "They're already following someone.\n\r", actor);
    return FALSE;
  }
  act("You catch $N's eye and quietly compel $M to follow you.", actor, NULL, mob, TO_CHAR);
  act("$n catches $N's eye and murmurs a quiet instruction.", actor, NULL, mob, TO_NOTVICT);
  add_follower(mob, actor);
  PedestrianState &state = pedestrians[mob];
  state.following_until = current_time + FOLLOW_SECONDS;
  state.stuck_since = 0;
  WAIT_STATE(actor, PULSE_PER_SECOND * 2);
  if (public_room(actor->in_room) && number_percent() <= HYPNOSIS_ALARM_PERCENT) {
    act("Someone nearby shouts, 'HELP! MONSTER!'", actor, NULL, NULL, TO_CHAR);
    act("Someone nearby shouts, 'HELP! MONSTER!'", actor, NULL, NULL, TO_ROOM);
    if (cortex_send_enforcers(actor)) {
      act("Cortex enforcers rush in at the cry and ambush you!", actor, NULL, NULL, TO_CHAR);
      act("Cortex enforcers rush in at the cry and ambush $n!", actor, NULL, NULL, TO_ROOM);
    }
  }
  return TRUE;
}

void pedestrian_mobile_update(CHAR_DATA *mob) {
  if (!pedestrian(mob)) return;
  // Extraction requires a room; handle orphaned NPCs before timed emotes/expiry.
  if (!mob->in_room) {
    char_to_room(mob, get_room_index(ROOM_VNUM_LIMBO));
    extract_char(mob, TRUE);
    return;
  }
  PedestrianState &state = pedestrians[mob];
  pedestrian_bound(mob);
  if (state.bound_since && current_time - state.bound_since >= BOUND_SECONDS) {
    act("Sanctuary attendants arrive and take $n away to safety.", mob, NULL, NULL, TO_ROOM);
    extract_char(mob, TRUE); // Flavor only: no Sanctuary service, payer or recovery record.
    return;
  }
  if (state.unconscious_until && current_time >= state.unconscious_until) {
    state.unconscious_until = 0;
    mob->position = POS_STANDING;
    mob->hit = max_hp(mob);
    act("$n stirs and regains consciousness.", mob, NULL, NULL, TO_ROOM);
  }
  if (mob->master && state.following_until && current_time >= state.following_until) {
    stop_follower(mob);
    state.following_until = 0;
  }
  const bool occupied = pedestrian_helpless(mob) || mob->master || in_fight(mob);
  if (occupied) state.stuck_since = 0;
  if (!occupied && ((state.sick_since && current_time - state.sick_since >= SICK_SECONDS)
      || (state.stuck_since && current_time - state.stuck_since >= STUCK_SECONDS))) {
    act("$n heads away and disappears from view.", mob, NULL, NULL, TO_ROOM);
    extract_char(mob, TRUE);
    return;
  }
  if (mob->ttl == 0 || mob->wounds >= 4) {
    extract_char(mob, TRUE);
  }
}

void pedestrian_update(void) {
  haven::ScopedTimer timer("pedestrian_update");
  // Spawn one at a time, including replacements, without a world-character scan.
  if (current_time >= next_spawn) {
    next_spawn = current_time + 2;
    spawn_pedestrian();
  }
  for (auto &entry : pedestrians) {
    CHAR_DATA *mob = entry.first;
    PedestrianState &state = entry.second;
    if (pedestrian_helpless(mob) || mob->master || in_fight(mob)) {
      state.stuck_since = 0;
      continue;
    }
    if (current_time < state.next_move) continue;
    state.next_move = current_time + WALK_SECONDS;
    if (pedestrian_walk_step(mob)) state.stuck_since = 0;
    else if (!state.stuck_since) state.stuck_since = current_time;
  }
}
} // extern "C"
