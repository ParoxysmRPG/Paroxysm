#include "merc.h"
#include "global.h"

extern "C" bool proximate_fight(ROOM_INDEX_DATA *room);

// An unused, already-saved habit slot keeps old character files compatible.
// Zero retains the existing Murderer portrayal until the player chooses another sin.
int sin_habit(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata) return SIN_MURDERER;
  int sin = ch->pcdata->habit[HABIT_SIN];
  return sin >= SIN_MURDERER && sin <= SIN_CORRUPT ? sin : SIN_MURDERER;
}

static const char *scammer_texts[] = {
  "You said it was safe. I told you it was the deposit for a place with a second bedroom. My son still asks when he can unpack his things. Just send back enough for the deposit. Please.",
  "Stop blocking me. My dad worked thirty-one years for that money. Now he puts his uniform on at five in the morning again and tells Mum he missed having something to do. You knew he believed you.",
  "The bank says I authorised it, so it isn't their problem. You say it isn't yours. The landlord wants us out on Friday. Whose problem is my daughter supposed to be?",
  "I sold her sewing machine today. She used to make all our curtains on it. I told her we needed the space because I couldn't tell her I'd given you the emergency fund. Please answer me. I can't keep inventing reasons things are missing.",
  "You can keep whatever you made off me. I need 86 for the electricity. I have been charging this phone at the library so the school can still reach me. I am begging you for 86 of my own money.",
  "I recommended you to my sister. She won't speak to me now. I keep opening our messages because she used to send pictures of the baby every morning. You took more than our savings. I need you to know that.",
  "ARE YOU READING THESE? We closed the shop. Twelve years and I had to tell the woman who worked beside me that there was no last paycheck. She hugged me because she thought I was the one who needed comforting. I hate you for that.",
  "The kids think sleeping in the car is an adventure. I let them pick which side is their bedroom. When they fell asleep I went through our messages again. You called me sensible for putting something aside for them.",
  "I don't want an explanation anymore. I want to stop checking my balance before I buy bread. I want my husband to look at me without remembering that I trusted you. Is there really nothing left you can send back?",
  "This is a borrowed phone. Mine is gone. So is the ring. I know you can ignore a number you don't recognise, but I was a person when you needed my signature. Please be there for one minute."
};

static const char *vigilante_accounts[] = {
  "'My sister reported him. You made the complaint disappear. She still checks the lock three times before she goes to bed.' The stranger unfolds a photograph, then carefully puts it away. 'You don't even know her name, do you?'",
  "'You were paid to say that building was safe. We carried my mother down six flights when the ceiling came in. She keeps asking when we can go home.' The stranger's hands are shaking. 'There isn't a home. I haven't told her yet.'",
  "'You buried the evidence. My brother is still inside. His little girl sends him drawings of a bedroom she's never been able to show him.' The stranger swallows. 'She leaves a space for him at the table. Every night.'",
  "'You gave them the names of everyone who complained. My dad was the first one they fired. He apologised to us for telling the truth.' The stranger raises two unsteady fists. 'Somebody has to stand up to you. He can't afford to anymore.'",
  "'You took their money and signed away our water. My wife washes the baby with bottles we buy at the petrol station.' The stranger blinks hard. 'We did everything they told us. Forms. Meetings. Petitions. You never even opened them.'"
};

static int next_story(int previous, int count) {
  // Sample without immediately repeating the previous vignette.
  if (previous < 0 || previous >= count) return number_range(0, count - 1);
  int choice = number_range(0, count - 2);
  return choice >= previous ? choice + 1 : choice;
}

static bool sin_player(CHAR_DATA *ch) {
  return ch && !IS_NPC(ch) && ch->pcdata && get_tier(ch) >= 3
      && !is_gm(ch) && !IS_IMMORTAL(ch) && !IS_FLAG(ch->act, PLR_GUEST)
      && !IS_FLAG(ch->act, PLR_DEAD) && !is_ghost(ch);
}

static bool sin_present(CHAR_DATA *ch) {
  return sin_player(ch) && ch->in_room && ch->desc
      && ch->desc->connected == CON_PLAYING && !IS_FLAG(ch->comm, COMM_AFK)
      && ch->position >= POS_RESTING && !is_helpless(ch) && !is_dreaming(ch)
      && !IS_FLAG(ch->act, PLR_SHROUD) && !IS_FLAG(ch->act, PLR_DEEPSHROUD);
}

bool sin_vigilante(CHAR_DATA *ch) {
  return ch && IS_NPC(ch) && IS_FLAG(ch->act, ACT_SIN_VIGILANTE);
}

static bool sin_public_street(ROOM_INDEX_DATA *room) {
  return room && room->area && room->area->world == WORLD_EARTH
      && room->sector_type == SECT_STREET
      && !IS_SET(room->room_flags, ROOM_INDOORS | ROOM_PRIVATE | ROOM_SAFE | ROOM_NO_MOB)
      && public_room(room);
}

bool sin_vigilante_target(CHAR_DATA *mob, CHAR_DATA *victim) {
  return sin_vigilante(mob) && mob->ttl > 0 && mob->wounds < 2 && mob->hit > 0
      && sin_public_street(mob->in_room)
      && sin_present(victim) && victim->in_room == mob->in_room
      && victim->wounds < 3 && !str_cmp(mob->aggression, victim->name);
}

CHAR_DATA *sin_vigilante_prey(CHAR_DATA *mob) {
  if (!sin_vigilante(mob) || !mob->in_room || mob->ttl <= 0) return NULL;
  for (CHAR_DATA *victim : *mob->in_room->people)
    if (sin_vigilante_target(mob, victim)) return victim;
  return NULL;
}

static void retire_sin_npc(CHAR_DATA *mob) {
  mob->ttl = 0;
  free_string(mob->aggression);
  mob->aggression = str_dup("");
  free_string(mob->protecting);
  mob->protecting = str_dup("");
  set_combat_state(mob, FALSE);
}

void sin_vigilante_update(CHAR_DATA *mob) {
  if (!sin_vigilante(mob)) return;
  // Stay with this encounter; never roam, pursue a fleeing player, or retarget.
  if (mob->ttl <= 0 || !sin_vigilante_prey(mob) || !in_fight(mob)) {
    if (mob->ttl > 0)
      act("$n lowers trembling hands and leaves, still clutching a photograph.", mob, NULL, NULL, TO_ROOM);
    retire_sin_npc(mob);
  }
}

void sin_vigilante_defeat(CHAR_DATA *mob, CHAR_DATA *victim) {
  if (!sin_vigilante_target(mob, victim)) return;
  retire_sin_npc(mob);
  set_combat_state(victim, FALSE);
  victim->hit = 0;
  victim->pcdata->sleeping = UMAX(victim->pcdata->sleeping, 240);
  send_to_char("As you fall, the stranger kneels to check that you are breathing. 'I just wanted you to listen.' They leave you unconscious where you fell.\n\r", victim);
  act("The stranger checks $n is breathing, then leaves $m unconscious where $e fell.", victim, NULL, NULL, TO_ROOM);
  // No wounds, death, capture, auction, recovery transfer, or inventory changes.
  save_char_obj(victim, FALSE, FALSE);
}

bool sin_cortex_guard(CHAR_DATA *ch) {
  return ch && IS_NPC(ch) && IS_FLAG(ch->act, ACT_CORTEX_SIN_GUARD);
}

bool sin_cortex_guard_target(CHAR_DATA *guard, CHAR_DATA *victim) {
  return sin_cortex_guard(guard) && guard->ttl > 0 && guard->wounds < 2
      && sin_public_street(guard->in_room)
      && guard->hit > 0 && sin_vigilante(victim) && victim->ttl > 0
      && victim->hit > 0 && victim->in_room == guard->in_room
      && !str_cmp(guard->protecting, victim->aggression);
}

CHAR_DATA *sin_cortex_guard_prey(CHAR_DATA *guard) {
  if (!sin_cortex_guard(guard) || !guard->in_room || guard->ttl <= 0) return NULL;
  for (CHAR_DATA *victim : *guard->in_room->people)
    if (sin_cortex_guard_target(guard, victim)) return victim;
  return NULL;
}

void sin_cortex_guard_update(CHAR_DATA *guard) {
  if (!sin_cortex_guard(guard)) return;
  if (!sin_cortex_guard_prey(guard) || !in_fight(guard)) {
    if (guard->ttl > 0)
      act("$n withdraws now that the virtuous vigilante's challenge is over.", guard, NULL, NULL, TO_ROOM);
    retire_sin_npc(guard);
  }
}

static void send_cortex_guards(CHAR_DATA *ch, CHAR_DATA *vigilante) {
  if (!ch || !sin_public_street(ch->in_room) || vigilante->in_room != ch->in_room) return;
  MOB_INDEX_DATA *index = get_mob_index(CORTEX_SOLDIER);
  if (!index || !in_fight(vigilante)) return;
  send_to_char("Two armored Cortex enforcers move to protect you from the virtuous vigilante. 'Stand down. This citizen is under Cortex protection.'\n\r", ch);
  act("Two armored Cortex enforcers move to protect $n and attack the virtuous vigilante.", ch, NULL, NULL, TO_ROOM);
  act("The virtuous vigilante stares at the uniforms. 'I brought you the evidence. You sent it back to the people I was reporting.'", vigilante, NULL, NULL, TO_ROOM);
  for (int n = 0; n < 2; ++n) {
    CHAR_DATA *guard = create_mobile(index);
    SET_FLAG(guard->act, ACT_CORTEX_ENFORCER);
    SET_FLAG(guard->act, ACT_CORTEX_SIN_GUARD);
    REMOVE_FLAG(guard->act, ACT_SENTINEL);
    guard->ttl = 1;
    guard->faction = FACTION_CORTEX;
    free_string(guard->name);
    guard->name = str_dup("cortex enforcer guard armored soldier");
    free_string(guard->short_descr);
    guard->short_descr = str_dup("an armored Cortex enforcer");
    free_string(guard->long_descr);
    guard->long_descr = str_dup("An armored Cortex enforcer shields a corrupt citizen from a virtuous vigilante.\n\r");
    free_string(guard->description);
    guard->description = str_dup("The Cortex uniform is immaculate, the armor expensive. This enforcer has come to protect the powerful person being confronted, not the people whose suffering brought a virtuous vigilante here.\n\r");
    free_string(guard->protecting);
    guard->protecting = str_dup(ch->name);
    char_to_room(guard, ch->in_room);
    guard->x = ch->x;
    guard->y = ch->y;
    guard->hit = max_hp(guard);
    start_fight(guard, vigilante);
  }
}

static bool vigilante_scene(CHAR_DATA *ch) {
  ROOM_INDEX_DATA *room = ch->in_room;
  if (!sin_present(ch) || in_fight(ch) || ch->wounds > 0 || ch->hit < max_hp(ch)
      || ch->position != POS_STANDING || is_prisoner(ch) || ch->pcdata->travel_to > 0
      || !sin_public_street(room) || room->vnum <= 300
      || battleground(room) || institute_room(room)
      || IS_FLAG(ch->act, PLR_HIDE) || proximate_fight(room) || dissent_in_room(room)) return false;
  for (CHAR_DATA *mob : char_list)
    if (sin_vigilante(mob) && mob->ttl > 0 && !str_cmp(mob->aggression, ch->name)) return false;
  return true;
}

static bool send_vigilante(CHAR_DATA *ch, int story) {
  if (!vigilante_scene(ch)) return false;
  MOB_INDEX_DATA *index = get_mob_index(MINION_TEMPLATE);
  if (!index) return false;
  CHAR_DATA *mob = create_mobile(index);
  SET_FLAG(mob->act, ACT_SIN_VIGILANTE);
  REMOVE_FLAG(mob->act, ACT_SENTINEL);
  mob->ttl = 1; // This module owns lifetime; the ordinary minion AI is bypassed.
  mob->faction = 0;
  mob->level = 1;
  mob->race = RACE_HUMAN;
  for (int i = 0; i < MAX_DIS; ++i) mob->disciplines[i] = 0;
  mob->disciplines[DIS_STRIKING] = 5;
  mob->disciplines[DIS_TOUGHNESS] = 5;
  free_string(mob->name);
  mob->name = str_dup("stranger virtuous vigilante");
  free_string(mob->short_descr);
  mob->short_descr = str_dup("a virtuous vigilante");
  free_string(mob->long_descr);
  mob->long_descr = str_dup("A virtuous vigilante stands here, an ordinary person with tired eyes and unsteady fists.\n\r");
  free_string(mob->description);
  mob->description = str_dup("This is a virtuous person seeking justice for innocent people hurt by corruption. There is no armor, no practiced stance, no supernatural strength here. They want the harm to stop, not money or power for themselves. A photograph has been folded and unfolded until its creases are white.\n\r");
  free_string(mob->aggression);
  mob->aggression = str_dup(ch->name);
  char_to_room(mob, ch->in_room);
  mob->x = ch->x;
  mob->y = ch->y;
  mob->hit = max_hp(mob);
  act("A virtuous vigilante steps into $n's path, seeking justice for the people $e hurt.", ch, NULL, NULL, TO_ROOM);
  send_to_char("A virtuous vigilante steps into your path. This ordinary person has come to stand up for the innocent people your corruption hurt.\n\r", ch);
  act(vigilante_accounts[story], mob, NULL, NULL, TO_ROOM);
  start_fight(mob, ch);
  if (!in_fight(mob)) retire_sin_npc(mob);
  else send_cortex_guards(ch, mob);
  // Even an interrupted encounter consumes its interval; never repeat the speech.
  return true;
}

void sin_update(CHAR_DATA *ch) {
  if (!sin_player(ch)) return;
  int sin = sin_habit(ch);
  if (sin == SIN_MURDERER) return;
  if (ch->pcdata->next_sin_event <= 0) {
    ch->pcdata->next_sin_event = current_time
        + (sin == SIN_SCAMMER ? number_range(14, 18) : number_range(28, 42)) * 86400;
    save_char_obj(ch, FALSE, FALSE);
    return;
  }
  if (current_time < ch->pcdata->next_sin_event || !sin_present(ch) || in_fight(ch)) return;
  int count = sin == SIN_SCAMMER ? sizeof(scammer_texts) / sizeof(*scammer_texts)
                               : sizeof(vigilante_accounts) / sizeof(*vigilante_accounts);
  int story = next_story(ch->pcdata->last_sin_story, count);
  bool delivered = sin == SIN_SCAMMER ? deliver_sin_text(ch, scammer_texts[story])
                                      : send_vigilante(ch, story);
  if (!delivered) return;
  ch->pcdata->last_sin_story = story;
  // Schedule from delivery, with no catch-up queue after an absence.
  ch->pcdata->next_sin_event = current_time
      + (sin == SIN_SCAMMER ? number_range(14, 18) : number_range(28, 42)) * 86400;
  save_char_obj(ch, FALSE, FALSE);
}
