#include "merc.h"
#include "global.h"
#include "recycle.h"
#include <cassert>
#include <chrono>
#include <cstring>

extern "C" {
extern char str_boot_time[];
void do_bind(CHAR_DATA *, char *);
void do_untie(CHAR_DATA *, char *);
void do_bite(CHAR_DATA *, char *);
void do_victimize(CHAR_DATA *, char *);
void do_hypnotise(CHAR_DATA *, char *);
void do_look(CHAR_DATA *, char *);
void do_drag(CHAR_DATA *, char *);
int __real_number_percent(void);
}
static int percent = 0;
extern "C" int __wrap_number_percent(void) {
  return percent ? percent : __real_number_percent();
}
static bool live(CHAR_DATA *mob) {
  return std::find(char_list.begin(), char_list.end(), mob) != char_list.end();
}
static std::vector<CHAR_DATA *> population() {
  std::vector<CHAR_DATA *> result;
  for (CHAR_DATA *mob : char_list) if (pedestrian(mob)) result.push_back(mob);
  return result;
}
static int enforcers() {
  int count = 0;
  for (CHAR_DATA *mob : char_list) if (cortex_enforcer(mob)) ++count;
  return count;
}
static void relocate(CHAR_DATA *ch, ROOM_INDEX_DATA *room) {
  if (ch->in_room) char_from_room(ch);
  char_to_room(ch, room);
  ch->x = ch->y = room->size / 2;
}
static void clear_fight(CHAR_DATA *ch) {
  cortex_retire_enforcers(ch);
  cortex_public_update();
  set_combat_state(ch, FALSE);
  ch->fighting = false;
  ch->pcdata->sleeping = 0;
}
static void output_clear(CHAR_DATA *ch) {
  ch->desc->outtop = 0;
  ch->desc->outbuf[0] = '\0';
}

int main() {
  setvbuf(stdout, NULL, _IONBF, 0);
  current_time = time(NULL);
  strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  assert(pedestrian_route_ready());
  for (int n = 0; n < 40; ++n) {
    current_time += 2;
    pedestrian_update();
  }
  auto people = population();
  assert(people.size() == 30);
  for (CHAR_DATA *mob : people) {
    assert(mob->race == RACE_HUMAN && !mob->pcdata && mob->hit > 0);
    assert(mob->money >= 200 && mob->money <= 1000);
    for (int n = 0; n < SKILL_MAX; ++n) assert(mob->skills[n] == 0);
    for (int n = 0; n < MAX_DIS; ++n) assert(mob->disciplines[n] == 0);
    assert(get_skill(mob, SKILL_STRENGTH) == 0);
    int clothes = 0;
    for (OBJ_DATA *obj = mob->carrying; obj; obj = obj->next_content)
      if (obj->item_type == ITEM_CLOTHING && obj->wear_loc != WEAR_NONE) ++clothes;
    assert(clothes == 3);
  }
  CHAR_DATA *ordinary = create_mobile(get_mob_index(115));
  relocate(ordinary, people[0]->in_room);
  assert(!pedestrian(ordinary));
  const int ordinary_hit = ordinary->hit;
  pedestrian_knockout(ordinary);
  pedestrian_mobile_update(ordinary);
  assert(live(ordinary) && ordinary->hit == ordinary_hit);
  MOB_INDEX_DATA shop_index = {};
  SHOP_DATA shop = {};
  shop_index.pShop = &shop;
  CHAR_DATA shopkeeper = {};
  shopkeeper.pIndexData = &shop_index;
  SET_FLAG(shopkeeper.act, ACT_IS_NPC);
  SET_FLAG(shopkeeper.act, ACT_PEDESTRIAN);
  assert(!pedestrian(&shopkeeper));
  puts("PASS: population capped at 30; humans have cash, three clothes, zero skills, no PC allocation; existing NPCs/shopkeepers excluded.");

  CHAR_DATA *actor = new_char();
  actor->pcdata = new_pcdata();
  actor->pcdata->account = new_account();
  actor->pcdata->account->maxhours = 200;
  actor->played = 200 * 3600;
  free_string(actor->name); actor->name = str_dup("Walkertest");
  actor->race = RACE_HUMAN; actor->level = 2;
  actor->position = POS_STANDING; actor->shape = SHAPE_HUMAN;
  actor->desc = new_descriptor(); actor->desc->character = actor;
  actor->desc->connected = CON_PLAYING;
  descriptor_list.push_back(actor->desc);
  char_list.push_front(actor); register_live_character(actor);
  CHAR_DATA *mob = people[0];
  relocate(actor, mob->in_room);
  assert(get_char_room(actor, NULL, (char *)"pedestrian") != NULL);
  do_look(actor, (char *)"pedestrian");
  // Removing/re-equipping NPC clothes must not access PC descriptions.
  OBJ_DATA *shirt = mob->carrying;
  const int slot = shirt->wear_loc;
  obj_from_char(shirt); obj_to_char(shirt, mob); equip_char(mob, shirt, slot);
  const int before = mob->in_room->vnum;
  assert(pedestrian_walk_step(mob) && mob->in_room->vnum != before);
  relocate(actor, mob->in_room);
  start_fight(actor, mob);
  assert(in_fight(actor) && in_fight(mob));
  assert(enforcers() >= 1 && enforcers() <= 6);
  damage(mob, actor, 100000);
  assert(pedestrian_helpless(mob) && mob->position == POS_SLEEPING && mob->wounds == 0);
  clear_fight(actor);
  do_bind(actor, (char *)"pedestrian");
  if (!IS_FLAG(mob->act, PLR_BOUND)) printf("BIND OUTPUT: %s\n", actor->desc->outbuf);
  assert(IS_FLAG(mob->act, PLR_BOUND) && IS_FLAG(mob->act, PLR_BOUNDFEET));
  assert(!pedestrian_walk_step(mob));
  puts("PASS: real public attack summons Cortex; depleted pedestrian HP causes KO; bind stops walking without NPC PC-data access.");

  const time_t fed = current_time - 1000;
  actor->pcdata->last_feeding = actor->pcdata->feeding_reminder = fed;
  const int taken = actor->lf_taken;
  assert(pedestrian_drain(actor, mob));
  assert(actor->lf_taken == taken - 100);
  assert(actor->pcdata->last_feeding == fed && actor->pcdata->feeding_reminder == fed);
  assert(strstr(mob->short_descr, "sickly") && strstr(mob->long_descr, "sickly"));
  assert(!pedestrian_drain(actor, mob) && actor->lf_taken == taken - 100);
  clear_fight(actor);
  output_clear(actor);
  do_victimize(actor, (char *)"pedestrian");
  assert(strstr(actor->desc->outbuf, "drained dry"));
  actor->race = RACE_WIGHT;
  output_clear(actor);
  do_bite(actor, (char *)"pedestrian mild");
  assert(strstr(actor->desc->outbuf, "drained dry"));
  actor->race = RACE_HUMAN;
  const time_t bound_at = current_time;
  current_time += 1801;
  pedestrian_mobile_update(mob);
  assert(live(mob)); // The sick timer cannot take a bound prisoner away early.
  assert(population().size() == 30);
  current_time = bound_at + 6 * 3600 - 1;
  pedestrian_mobile_update(mob); assert(live(mob));
  current_time += 1;
  pedestrian_mobile_update(mob); assert(!live(mob));
  assert(population().size() == 29 && actor->pcdata->last_feeding == fed);
  current_time += 2; pedestrian_update();
  assert(population().size() == 30);
  puts("PASS: bite/victimize share one 1-LF reward and sickly intro, never reset feeding; bound sick NPC survives until six hours then is replaced.");

  mob = population()[0];
  relocate(actor, mob->in_room);
  SET_FLAG(mob->act, PLR_BOUND); pedestrian_bound(mob);
  assert(pedestrian_drain(actor, mob)); clear_fight(actor);
  REMOVE_FLAG(mob->act, PLR_BOUND); pedestrian_bound(mob);
  current_time += 1800;
  pedestrian_mobile_update(mob); assert(!live(mob));
  current_time += 2; pedestrian_update();
  assert(population().size() == 30);
  puts("PASS: a drained pedestrian released from captivity retires after 30 minutes and is replaced by a healthy one.");

  mob = population()[0];
  ROOM_INDEX_DATA *offroute = get_room_index(ROOM_VNUM_LIMBO);
  relocate(mob, offroute);
  current_time += 15; pedestrian_update();
  const time_t stuck_at = current_time;
  current_time += 299; pedestrian_mobile_update(mob); assert(live(mob));
  current_time = stuck_at + 300;
  pedestrian_mobile_update(mob); assert(!live(mob));
  current_time += 2; pedestrian_update();
  mob = population()[0];
  relocate(mob, offroute);
  pedestrian_knockout(mob);
  current_time += 400; pedestrian_update(); pedestrian_mobile_update(mob);
  assert(live(mob)); // Unconscious time is not stalled time.
  mob->master = actor;
  current_time += 400; pedestrian_update(); pedestrian_mobile_update(mob);
  assert(live(mob)); // Following time is not stalled time either.
  mob->master = NULL;
  relocate(mob, pedestrian_spawn_room(0));
  puts("PASS: five-minute blocked-route replacement excludes unconscious and following pedestrians.");

  relocate(actor, mob->in_room);
  actor->skills[SKILL_HYPNOTISM] = 1;
  percent = 100;
  do_hypnotise(actor, (char *)"pedestrian follow");
  assert(mob->master == actor && enforcers() == 0);
  ROOM_INDEX_DATA *from = mob->in_room;
  int door = -1;
  for (int d = 0; d < 10; ++d) {
    if (from->exit[d] && from->exit[d]->u1.to_room
        && !IS_SET(from->exit[d]->exit_info, EX_CLOSED | EX_LOCKED)
        && from->exit[d]->wall == WALL_NONE
        && from->exit[d]->u1.to_room->sector_type == SECT_STREET) { door = d; break; }
  }
  assert(door >= 0);
  relocate(actor, from->exit[door]->u1.to_room);
  move_char(mob, door, TRUE, FALSE);
  assert(mob->in_room == actor->in_room);
  do_hypnotise(actor, (char *)"pedestrian release");
  assert(!mob->master);
  percent = 1;
  output_clear(actor);
  const int before_alarm_population = population().size();
  do_hypnotise(actor, (char *)"pedestrian follow");
  assert(mob->master == actor);
  assert(strstr(actor->desc->outbuf, "HELP! MONSTER!"));
  assert(enforcers() >= 1 && enforcers() <= 6);
  assert(population().size() == static_cast<unsigned>(before_alarm_population));
  clear_fight(actor);
  mob->master = NULL;
  percent = 0;
  puts("PASS: hypnosis follow/release uses actual exits; public alarm is an emote and summons Cortex without a witness NPC.");

  // A missing room must not bypass cleanup when another expiry is also due.
  SET_FLAG(mob->act, PLR_BOUND); pedestrian_bound(mob);
  char_from_room(mob);
  current_time += 6 * 3600;
  pedestrian_mobile_update(mob);
  assert(!live(mob) && population().size() == 29);
  current_time += 2; pedestrian_update();
  assert(population().size() == 30);
  puts("PASS: an orphaned pedestrian is removed and replaced even when its bound timeout is due.");

  const auto start = std::chrono::steady_clock::now();
  for (int i = 0; i < 1000; ++i) pedestrian_update();
  const auto ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
  printf("PASS: 1000 idle pedestrian scheduler calls with 30 loaded pedestrians: %.3f ms (local fixture, not production latency).\n", ms);
}
