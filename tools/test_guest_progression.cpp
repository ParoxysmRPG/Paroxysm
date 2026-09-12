#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>
#include <fstream>

extern "C" {
extern char str_boot_time[];
extern bool isactiveoperation;
extern int battle_factions[6];
void do_guest(CHAR_DATA *, char *);
void do_credits(CHAR_DATA *, char *);
void do_goal(CHAR_DATA *, char *);
void do_done(CHAR_DATA *, char *);
void launch_operation(OPERATION_TYPE *);
void win_operation(int, OPERATION_TYPE *);
void do_operation(CHAR_DATA *, char *);
void do_target(CHAR_DATA *, char *);
bool targeted_operation_power(CHAR_DATA *, OPERATION_TYPE *);
bool can_deploy(CHAR_DATA *, OPERATION_TYPE *, int);
bool deploy_operation_power(CHAR_DATA *, OPERATION_TYPE *, STORYLINE_TYPE *, int, int, int);
}

static void assign(char *&field, const char *text) { free_string(field); field = str_dup(text); }
static int sanctuary_news_count() {
  int count = 0;
  for (NEWS_TYPE *news : NewsVect)
    if (news->valid && !strcmp(news->author, "Sanctuary Watch")) ++count;
  return count;
}
static CHAR_DATA *player(const char *name, const char *account_name) {
  auto *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->race = RACE_HUMAN; ch->position = POS_STANDING;
  ch->id = get_pc_id(); ch->logon = current_time; ch->played = 100 * 3600;
  auto *account = new_account(); assign(account->name, account_name);
  account->maxhours = 100; ch->pcdata->account = account;
  assign(ch->pcdata->account_name, account_name);
  ch->desc = new_descriptor(); ch->desc->character = ch; ch->desc->account = account;
  ch->desc->connected = CON_PLAYING;
  char_to_room(ch, get_room_index(16068)); char_list.push_front(ch);
  return ch;
}
static void command(CHAR_DATA *ch, void (*handler)(CHAR_DATA *, char *), const std::string &input) {
  std::string copy = input; handler(ch, &copy[0]);
}
static OPERATION_TYPE *operation(int faction, int territory, int goal, const char *target) {
  auto *op = new_operation(); op->faction = faction; op->territoryvnum = territory;
  op->goal = goal; op->hour = 12; op->competition = COMPETE_OPEN;
  assign(op->target, target); OpVect.push_back(op); activeoperation = op;
  return op;
}

int main(int argc, char **) {
  setvbuf(stdout, NULL, _IONBF, 0);
  current_time = time(NULL); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  if (argc > 1) {
    assert(sanctuary_population_blocked());
    assert(sanctuary_news_count() == 3);
    update_sanctuary_population();
    assert(!sanctuary_population_blocked() && sanctuary_news_count() == 4);
    update_sanctuary_population();
    assert(sanctuary_news_count() == 4);
    puts("PASS: persisted overwhelmed state survives restart and posts recovery once when the population stabilizes.");
    auto *dom = power_domain("Testpower");
    assert(dom && dom->guest_retired && dom->successful_worships == 0 && dom->claimed_territory > 0);
    auto *fac = clan_lookup(990101);
    assert(fac && power_relation(fac, "Testpower") == SOCIETY_PATRON_WORSHIP);
    assert(power_relation(fac, "Secondpower") == SOCIETY_PATRON_OPPOSE);
    auto *d = new_descriptor(); assert(load_char_obj(d, (char *)"Earnedhero"));
    assert(d->character->pcdata->earned_guest_tier == 5 && !IS_FLAG(d->character->act, PLR_GUEST));
    assert(load_char_obj(new_descriptor(), (char *)"Testpower"));
    puts("PASS: guest retirement, claims, relations and permanent remake survive restart.");
    return 0;
  }

  auto *source = player("Testsource", "Guesttest");
  command(source, do_guest, "");
  assert(strstr(source->desc->outbuf, "Choose a guest type"));
  command(source, do_guest, "higherpower");
  assert(strstr(source->desc->outbuf, "Choose a higher power"));
  assert(!IS_FLAG(source->act, PLR_REROLL));
  source->wounds = 1;
  command(source, do_credits, "bandaid");
  assert(source->wounds == 1);
  command(source, do_credits, "rename Removedrename");
  assert(!strcmp(source->pcdata->account->name, "Guesttest"));
  source->wounds = 0;
  auto *god = player("Godsource", "Godtest");
  command(god, do_guest, "higherpower god Testgod");
  command(god, do_guest, "higherpower god Testgod");
  assert(god->race == RACE_SPIRIT_DIVINE);
  assert(IS_FLAG(god->act, PLR_GUEST));
  assert(god->pcdata->guest_type == GUEST_HIGHERPOWER);
  assert(!readychar(god));
  puts("PASS: guest choices prompt, God creates a higher-power guest, and removed credit commands have no effect.");
  command(source, do_guest, "higherpower fae Testpower");
  assert(!strcmp(source->name, "Testsource"));
  command(source, do_guest, "higherpower fae Testpower");
  assert(!strcmp(source->name, "Testpower"));
  assert(!readychar(source));
  command(source, do_done, "");
  assert(source->in_room->vnum == ROOM_INDEX_GENESIS);
  assert(strstr(source->desc->outbuf, "You must choose a territory"));
  command(source, do_change, "territory");
  command(source, do_guest, "claim");
  assert(!power_domain(source->name));
  command(source, do_change, "territory nonexistent-territory");
  assert(!power_domain(source->name));
  LOCATION_TYPE *loc = territory_by_number(1); assert(loc);
  command(source, do_change, "territory " + std::string(loc->name));
  auto *power = source;
  assert(!strcmp(power->name, "Testpower"));
  assert(higher_power(power) && IS_FLAG(power->act, PLR_GUEST));
  auto *dom = power_domain(power->name); assert(dom && power_available(dom));
  assert(!claim_power_territory(power, territory_by_number(2)));
  assert(charcost(power) == 0 && guest_remake_tier(power) == 0);
  puts("PASS: higher-power guest creation requires and persists a permanent territory claim without karma.");

  auto *fac = new_faction(); fac->vnum = 990101; fac->type = FACTION_SOCIETY;
  fac->alliance = ALLIANCE_SIDELEFT; assign(fac->name, "Guesttesters"); FacVect.push_back(fac);
  auto *cortex = clan_lookup(FACTION_CORTEX); assert(cortex);
  show_power_relations(source, cortex);
  assert(strstr(source->desc->outbuf, "every higher power (permanent)"));
  assert(!set_power_relation(cortex, power->name, SOCIETY_PATRON_WORSHIP));
  assert(power_relation(cortex, "Anyfuturepower") == SOCIETY_PATRON_OPPOSE);
  assert(set_power_relation(fac, power->name, SOCIETY_PATRON_WORSHIP));
  assert(set_power_relation(fac, "Secondpower", SOCIETY_PATRON_OPPOSE));
  assert(power_relation(fac, power->name) == SOCIETY_PATRON_WORSHIP);
  assert(power_operation_error(fac->vnum, 1, GOAL_WORSHIP, power->name));
  loc->base_society = fac->vnum;
  assert(!power_operation_error(fac->vnum, 1, GOAL_WORSHIP, power->name));
  assert(power_operation_error(fac->vnum, 1, GOAL_ATTACK_POWER, power->name));
  assert(power_operation_error(fac->vnum, 2, GOAL_WORSHIP, power->name));
  assert(power_operation_error(fac->vnum, 1, GOAL_WORSHIP, "Nobody"));
  assert(power_operation_error(fac->vnum, 1, GOAL_WORSHIP, ""));
  assert(power_operation_error(fac->vnum, 1, GOAL_ATTACK_POWER, ""));
  {
    auto saved_operations = OpVect;
    OpVect.clear();
    auto *op = operation(fac->vnum, 1, GOAL_WORSHIP, power->name);
    activeoperation = NULL;
    char_from_room(power); char_to_room(power, get_room_index(16068));
    const int original_faction = power->faction;
    power->faction = 0;
    command(power, do_operation, "signup 1");
    assert(!strcmp(op->sign_up[0], power->name));
    assert(can_deploy(power, op, 0));
    command(power, do_operation, "signup 1");
    assert(!*op->sign_up[0] && !can_deploy(power, op, 0));
    assign(op->target, "Someoneelse");
    command(power, do_operation, "signup 1");
    assert(!*op->sign_up[0]);
    assign(op->target, power->name);
    op->goal = GOAL_INCITE;
    command(power, do_operation, "signup 1");
    assert(!*op->sign_up[0]);
    for (int goal : {GOAL_WORSHIP, GOAL_ATTACK_POWER}) {
      op->goal = goal;
      command(power, do_operation, "signup 1");
      assert(!strcmp(op->sign_up[0], power->name));
      assert(targeted_operation_power(power, op));
      dom->banished_until = current_time + 60;
      assert(!can_deploy(power, op, 0));
      dom->banished_until = 0;
      for (int i = 0; i < 6; ++i) battle_factions[i] = 0;
      battle_factions[0] = fac->vnum;
      assert(deploy_operation_power(power, op, NULL, 2, 250, 0));
      assert(battleground(power->in_room));
      assert(power->faction == (goal == GOAL_WORSHIP ? fac->vnum : 200000));
      assert(power->factiontrue == 0 && power->pcdata->deploy_from == 16068);
      assert(!deploy_operation_power(power, op, NULL, 2, 250, 0));
      if (goal == GOAL_ATTACK_POWER) {
        activeoperation = op; isactiveoperation = TRUE;
        win_operation(200000, NULL);
        assert(op->hour == 0 && !isactiveoperation && dom->banished_until == 0);
        assert(power->in_room->vnum == 16068 && power->faction == 0 && power->factiontrue == -1);
      } else {
        char_from_room(power); char_to_room(power, get_room_index(16068));
        power->faction = 0; power->factiontrue = -1;
        command(power, do_operation, "signup 1");
      }
    }
    power->faction = original_faction;
    op->hour = 0;
    OpVect = saved_operations;
    puts("PASS: only targeted powers sign up and deploy without society membership; correct sides and safe defense victory/return.");
  }
  assert(!resolve_power_operation(fac->vnum + 1, operation(fac->vnum, 1, GOAL_WORSHIP, power->name)));
  assert(dom->successful_worships == 0);
  for (int i = 1; i <= 5; ++i) {
    auto *op = operation(fac->vnum, 1, GOAL_WORSHIP, power->name);
    if (i == 1) { isactiveoperation = TRUE; win_operation(fac->vnum, NULL); }
    else assert(resolve_power_operation(fac->vnum, op));
    assert(!resolve_power_operation(fac->vnum, op));
    assert(dom->successful_worships == i);
    assert(guest_remake_tier(power) == (i >= 5 ? 5 : i >= 3 ? 4 : 0));
  }
  puts("PASS: foothold, territory, target, stance and winner checks; three/five worship thresholds; no duplicate rewards.");

  auto *editor = player("Testeditor", "Editortest"); editor->faction = fac->vnum;
  editor->pcdata->ci_editing = 12; assign(editor->pcdata->ci_short, loc->name);
  command(editor, do_goal, "worship Testpower");
  assert(editor->pcdata->ci_discipline2 == GOAL_WORSHIP);
  assert(!strcmp(editor->pcdata->ci_message, "Testpower"));
  command(editor, do_goal, "worship");
  assert(editor->pcdata->ci_discipline2 == GOAL_WORSHIP && !*editor->pcdata->ci_message);
  size_t incomplete_count = OpVect.size();
  command(editor, do_done, "");
  assert(OpVect.size() == incomplete_count);
  command(editor, do_target, "Nobody");
  assert(!*editor->pcdata->ci_message);
  command(editor, do_target, "Testpower");
  assert(!strcmp(editor->pcdata->ci_message, "Testpower"));
  editor->pcdata->ci_discipline = COMPETE_CLOSED;
  size_t count = OpVect.size(); command(editor, do_done, ""); assert(OpVect.size() == count);
  auto *stale = operation(fac->vnum, 1, GOAL_WORSHIP, power->name);
  set_power_relation(fac, power->name, SOCIETY_PATRON_OPPOSE);
  launch_operation(stale); assert(stale->hour == 0 && !stale->valid);
  // Attack an offline power, then check the exact 30-day boundary.
  char_list.remove(power);
  auto *attack = operation(fac->vnum, 1, GOAL_ATTACK_POWER, power->name);
  assert(resolve_power_operation(fac->vnum, attack));
  assert(dom->successful_worships == 0 && dom->banished_until == current_time + POWER_BANISH_SECONDS);
  assert(!power_available(dom) && guest_remake_tier(power) == 0 && guest_out_of_play(power));
  set_power_relation(fac, power->name, SOCIETY_PATRON_WORSHIP);
  assert(power_operation_error(fac->vnum, 1, GOAL_WORSHIP, power->name));
  current_time = dom->banished_until - 1; assert(!power_available(dom));
  ++current_time; assert(power_available(dom)); char_list.push_front(power);
  puts("PASS: editor validation, stale launch cancellation, offline attack reset and exact month-long worship/remake lockout.");

  auto *monster = player("Testmonster", "Monstertest");
  SET_FLAG(monster->act, PLR_GUEST); monster->pcdata->guest_type = GUEST_MONSTER;
  monster->race = RACE_LANDMONSTER; monster->pcdata->monster_reward_hours = 30;
  for (int hours : {30, 31, 60, 61}) {
    monster->played = hours * 3600;
    assert(guest_remake_tier(monster) == (hours > 60 ? 5 : hours > 30 ? 4 : 0));
  }
  SET_FLAG(monster->act, PLR_DEAD); assert(guest_remake_tier(monster) == 0);
  REMOVE_FLAG(monster->act, PLR_DEAD);
  monster->pcdata->guest_reward_used = 1; assert(guest_remake_tier(monster) == 0);
  puts("PASS: monster survival reward boundaries and dead/consumed guest exclusion.");
  auto *live = player("Banishlive", "Banishtest"); live->race = RACE_SPIRIT_DIVINE;
  assert(claim_power_territory(live, loc));
  set_power_relation(fac, live->name, SOCIETY_PATRON_OPPOSE);
  auto *live_dom = power_domain(live->name);
  assert(resolve_power_operation(fac->vnum, operation(fac->vnum, 1, GOAL_ATTACK_POWER, live->name)));
  assert(!get_char_world_pc((char *)"Banishlive") && !power_available(live_dom));
  puts("PASS: successful attacks immediately disconnect and remove online higher powers.");

  dom->successful_worships = 5;
  // Leave genesis after constructing the test guest, as a finished character would.
  char_from_room(power); char_to_room(power, get_room_index(GMHOME));
  command(power, do_guest, "remake t5 Earnedhero"); command(power, do_guest, "remake t5 Earnedhero");
  assert(!strcmp(power->name, "Earnedhero") && power->pcdata->earned_guest_tier == 5);
  assert(!IS_FLAG(power->act, PLR_GUEST) && dom->guest_retired && dom->successful_worships == 0);
  for (int i = 0; i < MAX_PC_RACE; ++i) if (race_table[i].tier == 5 && race_table[i].pc_race) { power->race = i; break; }
  assert(get_tier(power) == 5 && charcost(power) == 0);
  power->pcdata->earned_guest_tier = 4; assert(!readychar(power));
  power->pcdata->earned_guest_tier = 0; power->pcdata->account->karma = 1000000;
  assert(!readychar(power)); power->pcdata->earned_guest_tier = 5;
  save_char_obj(power, FALSE, FALSE); save_domains(FALSE); save_clans(FALSE);
  puts("PASS: actual guest remake command consumes the guest and creates a permanent, free T5 character.");

  ++current_time; // The original source save is now outside the 30-day window.
  // Isolate the census from copied fixtures and prior guest tests.
  for (CHAR_DATA *ch : char_list) SET_FLAG(ch->act, PLR_STASIS);
  for (const char *name : {"TestGuest", "Admin"}) unlink((std::string(PLAYER_DIR) + name).c_str());
  CHAR_DATA *people[10];
  for (int i = 0; i < 10; ++i) {
    std::string name = "Census" + std::string(1, 'a' + i);
    people[i] = player(name.c_str(), name.c_str());
  }
  int high_race = power->race;
  people[0]->race = high_race; people[1]->race = high_race;
  update_sanctuary_population(); assert(!sanctuary_population_blocked());
  assert(sanctuary_news_count() == 0);
  auto *alt = player("Censusalt", "Censusa"); alt->race = high_race;
  update_sanctuary_population(); assert(!sanctuary_population_blocked());
  people[2]->race = high_race; update_sanctuary_population(); assert(sanctuary_population_blocked());
  assert(sanctuary_news_count() == 1);
  assert(strstr(NewsVect.back()->message, "Sanctuary Overwhelmed"));
  assert(NewsVect.back()->stats[0] == 0 && NewsVect.back()->timer > 0);
  update_sanctuary_population(); assert(sanctuary_news_count() == 1);
  auto *ordinary = people[9]; assign(ordinary->pcdata->understanding, "All");
  SET_FLAG(ordinary->affected_by, AFF_UNDERSTANDING);
  assert(!under_understanding(ordinary, ordinary) && !under_limited(ordinary, ordinary));
  assert(!seems_under_understanding(ordinary, ordinary) && !seems_under_limited(ordinary, ordinary));
  record_critical_injury(ordinary, ordinary, false);
  assert(ordinary->pcdata->recovery->critical.source == RECOVERY_NONE);
  SET_FLAG(people[2]->act, PLR_DEAD); update_sanctuary_population();
  // 2 of 9 remains above 20%; removing one more high-tier account restores it.
  assert(sanctuary_population_blocked());
  people[1]->race = RACE_HUMAN; update_sanctuary_population(); assert(!sanctuary_population_blocked());
  assert(sanctuary_news_count() == 2);
  assert(strstr(NewsVect.back()->message, "Sanctuary Stabilized"));
  assert(NewsVect.back()->stats[0] == 0);
  update_sanctuary_population(); assert(sanctuary_news_count() == 2);
  puts("PASS: account deduplication, exact 20% boundary, global full/limited/ritual suppression and automatic restoration.");
  // Leave an overwhelmed state on disk, with no saved active census characters.
  // The next process must report its recovery, not repeat the failure notice.
  people[1]->race = high_race; update_sanctuary_population();
  assert(sanctuary_population_blocked() && sanctuary_news_count() == 3);
  puts("PASS: public overwhelmed/stabilized news posts occur once per threshold crossing, including repeated cycles.");
}
