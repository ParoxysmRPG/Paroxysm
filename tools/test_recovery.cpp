#include "merc.h"
#include "recycle.h"
#include "runtime_io.h"
#include <cassert>
#include <cstring>
#include <ctime>
#include <fstream>
#include <sstream>
#include <iterator>
#include <sys/socket.h>
#include <unistd.h>
#include <dlfcn.h>

extern "C" {
extern char str_boot_time[];
void resurrection(OBJ_DATA *);
bool can_deploy(CHAR_DATA *, OPERATION_TYPE *, int);
void append_messages(CHAR_DATA *, char *);
void replace_focused(CHAR_DATA *, int, char *);
void append_focused(CHAR_DATA *, int, char *);
bool read_from_ident(int, char *, size_t);
bool read_from_descriptor(DESCRIPTOR_DATA *);
void pc_update(CHAR_DATA *, int);
bool payday(CHAR_DATA *);
void faction_daily(FACTION_TYPE *);
void do_faction(CHAR_DATA *, char *);
int faction_secrecy(FACTION_TYPE *, CHAR_DATA *);
int focus_point_per_tier(CHAR_DATA *);
bool faction_hardelligible(CHAR_DATA *, FACTION_TYPE *, bool, CHAR_DATA *);
void process_order(CHAR_DATA *, int);
bool can_raise(int, CHAR_DATA *);
int train_skill_cost(CHAR_DATA *, int, int);
void do_train(CHAR_DATA *, char *);
}
static void assign(char *&field, const char *value) {
  free_string(field); field = str_dup(value);
}
static bool at_trolly_stop(CHAR_DATA *ch) {
  for (int i = 0; i < trolly_stop_count; ++i)
    if (ch->in_room->vnum == trolly_stops[i]) return true;
  return false;
}
static CHAR_DATA *player(const char *name) {
  CHAR_DATA *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->position = POS_STANDING;
  ch->race = RACE_HUMAN; ch->id = 12345;
  char_to_room(ch, get_room_index(16068));
  char_list.push_front(ch);
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->desc->connected = CON_PLAYING;
  return ch;
}
static FACTION_TYPE *organization(int id, int type = FACTION_SOCIETY) {
  auto *fac = new_faction(); fac->vnum = id; fac->type = type;
  assign(fac->name, "RecoveryTest"); fac->resource = 70000;
  fac->lifeearned = 1000; fac->attributes[FACTION_UNDERSTANDING] = 1;
  FacVect.push_back(fac); return fac;
}
static void coverage(CHAR_DATA *ch, int source) {
  affect_strip(ch, AFF_UNDERSTANDING); // Explicitly remove by bit below.
  for (AFFECT_DATA *a = ch->affected, *next; a; a = next) {
    next = a->next; if (a->bitvector == AFF_UNDERSTANDING) affect_remove(ch, a);
  }
  assign(ch->pcdata->understanding, source == RECOVERY_NONE ? "None" : "All");
  if (source == RECOVERY_RITUAL) {
    AFFECT_DATA af = {}; af.where = TO_AFFECTS; af.duration = 36000;
    af.bitvector = AFF_UNDERSTANDING; affect_to_char(ch, &af);
  }
  if (source == RECOVERY_SANCTUARY) assert(under_understanding(ch, ch));
}
static OBJ_DATA *item(CHAR_DATA *ch, const char *name, int type, int wear = WEAR_NONE) {
  auto *obj = create_object(get_obj_index(OBJ_VNUM_DUMMY), 0);
  assign(obj->name, name); obj->extra_flags = 0; obj->item_type = type;
  obj_to_char(obj, ch); obj->wear_loc = wear; return obj;
}
static CHAR_DATA *reload(CHAR_DATA *ch) {
  std::string name = ch->name;
  char_list.remove(ch); char_from_room(ch); free_char(ch);
  auto *d = new_descriptor(); assert(load_char_obj(d, const_cast<char *>(name.c_str())));
  ch = d->character; char_list.push_front(ch);
  return ch;
}
static void next_day() { current_time = next_sanctuary_recovery(); }
static std::string bytes(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  return std::string(std::istreambuf_iterator<char>(f), {});
}
static void second_class_recovery(FACTION_TYPE *fac, CHAR_DATA *forest, CHAR_DATA *civilian) {
  auto *ch = player("Secondclass");
  ch->newrpexp = 100000;
  ch->pcdata->rpexp_cap = 1000000;
  assert(skilltype(SKILL_SECONDCLASS) == STYPE_SOCIAL);
  assert(skillpoint(-2) == -2 && skillpoint(-1) == -1);
  assert(has_requirements(ch, SKILL_SECONDCLASS, -2, false)); // Creation.
  assert(!can_raise(SKILL_SECONDCLASS, ch));
  for (int level : {0, -1, -2}) {
    ch->skills[SKILL_SECONDCLASS] = level;
    const int before = available_rpexp(ch);
    ch->desc->outtop = 0; ch->desc->outbuf[0] = '\0';
    do_negtrain(ch, (char *)"Second Class Citizen");
    assert(ch->skills[SKILL_SECONDCLASS] == level);
    assert(available_rpexp(ch) == before);
    assert(strstr(ch->desc->outbuf, "Second Class Citizen cannot be negtrained."));
  }
  for (int expected : {-1, 0}) {
    assert(can_raise(SKILL_SECONDCLASS, ch));
    assert(train_skill_cost(ch, SKILL_SECONDCLASS, TRAINED_NATURAL) == BASE_STAT_COST);
    int before = available_rpexp(ch);
    do_train(ch, (char *)"Second Class Citizen");
    assert(ch->skills[SKILL_SECONDCLASS] == expected);
    assert(available_rpexp(ch) == before - BASE_STAT_COST);
  }
  do_train(ch, (char *)"Second Class Citizen");
  assert(ch->skills[SKILL_SECONDCLASS] == 0);
  auto *observer = player("Auraviewer");
  SET_FLAG(observer->act, PLR_GM);
  // An established supernatural needs an independent sanctuary source.
  auto *uncovered = player("Secondclasseligibility");
  uncovered->race = RACE_NEWVAMPIRE;
  uncovered->played = 126 * 3600;
  assert(is_super(uncovered) && seems_super(uncovered));
  for (int level : {0, -1, -2}) {
    uncovered->skills[SKILL_SECONDCLASS] = level;
    for (int source : {RECOVERY_NONE, RECOVERY_SANCTUARY, RECOVERY_NONE,
                       RECOVERY_RITUAL, RECOVERY_NONE}) {
      coverage(uncovered, RECOVERY_NONE); // Remove previous ritual coverage.
      assign(uncovered->pcdata->understanding, "All");
      uncovered->fsociety = source == RECOVERY_SANCTUARY ? fac->vnum : 0;
      if (source == RECOVERY_RITUAL) coverage(uncovered, RECOVERY_RITUAL);
      const bool covered = source != RECOVERY_NONE;
      assert(under_understanding(uncovered, uncovered) == (covered && level == 0));
      assert(under_limited(uncovered, uncovered) == (covered && level == -1));
      assert(under_black(uncovered, uncovered) == (covered && level == -2));
      assert(under_sanctuary(uncovered, uncovered) == (covered && level != -2));
      assert(full_sanctuary_protection(uncovered, uncovered) == (covered && level == 0));
      assert(seems_under_understanding(uncovered, observer) == (covered && level == 0));
      assert(seems_under_limited(uncovered, observer) == (covered && level == -1));
      assert(seems_under_black(uncovered, observer) == (covered && level == -2));
      record_death_recovery(uncovered, civilian, false, false);
      assert(uncovered->pcdata->recovery->death.source == source);
      record_critical_injury(uncovered, civilian, false);
      assert(uncovered->pcdata->recovery->critical.source == source);
    }
  }
  puts("PASS: second-class coverage and aura require an existing sanctuary source and disappear when it is lost.");
  for (int level : {0, -1, -2}) {
    ch->skills[SKILL_SECONDCLASS] = level;
    assert(get_skill(ch, SKILL_SECONDCLASS) == level);
    assert(under_understanding(ch, ch) == (level == 0));
    assert(under_limited(ch, ch) == (level == -1));
    assert(under_black(ch, ch) == (level == -2));
    assert(under_sanctuary(ch, ch) == (level != -2));
    assert(full_sanctuary_protection(ch, ch) == (level == 0));
    assert(seems_under_understanding(ch, observer) == (level == 0));
    assert(seems_under_limited(ch, observer) == (level == -1));
    assert(seems_under_black(ch, observer) == (level == -2));
    if (level < 0) {
      observer->desc->outtop = 0; observer->desc->outbuf[0] = '\0';
      show_char_to_char_1(ch, observer, 0, false);
      if (!strstr(observer->desc->outbuf, level == -2 ? "black" : "orange"))
        fprintf(stderr, "Aura output at %d: %s\n", level, observer->desc->outbuf);
      assert(strstr(observer->desc->outbuf, level == -2 ? "black" : "orange"));
    }
    record_death_recovery(ch, civilian, false, false);
    assert(ch->pcdata->recovery->death.source == RECOVERY_SANCTUARY);
    record_death_recovery(ch, forest, false, false);
    assert(ch->pcdata->recovery->death.source == RECOVERY_NONE);
  }
  // Full sanctuary from a society or ritual cannot upgrade either drawback.
  ch->fsociety = fac->vnum;
  for (int level : {-1, -2}) {
    ch->skills[SKILL_SECONDCLASS] = level;
    assert(!under_understanding(ch, ch));
    AFFECT_DATA af = {}; af.where = TO_AFFECTS; af.duration = 100;
    af.bitvector = AFF_UNDERSTANDING; affect_to_char(ch, &af);
    assert(!full_sanctuary_protection(ch, ch));
    coverage(ch, RECOVERY_NONE); // Also removes ritual affect.
    assert(!under_limited(ch, ch) && !under_black(ch, ch));
    assign(ch->pcdata->understanding, "All");
    restore_sanctuary_population(true);
    assert(!under_limited(ch, ch) && !under_black(ch, ch));
    restore_sanctuary_population(false);
  }
  ch->skills[SKILL_SECONDCLASS] = 0;
  assign(ch->pcdata->understanding, "Limited");
  assert(under_sanctuary(ch, ch) && !full_sanctuary_protection(ch, ch));
  assert(!strcmp(ch->pcdata->understanding, "Limited"));
  assign(ch->pcdata->understanding, "All");
  // All tiers, mixed orange/black maims, critical provenance and persistent fees.
  const int old_stance = fac->axes[AXES_CORRUPT];
  fac->axes[AXES_CORRUPT] = AXES_DEMONIC;
  for (int tier = 1; tier <= 6; ++tier) {
    ch->pcdata->tier_raised += tier - get_tier(ch);
    ch->skills[SKILL_SECONDCLASS] = -1;
    record_maim(ch, "orange injury", ch, false);
    ch->skills[SKILL_SECONDCLASS] = -2;
    record_maim(ch, "black injury", ch, false);
    record_critical_injury(ch, ch, false);
    ch->skills[SKILL_SECONDCLASS] = 0;
    record_death_recovery(ch, ch, true, false);
    assert(ch->pcdata->recovery->death.cost_percent == 20);
    SET_FLAG(ch->act, PLR_DEAD);
    save_char_obj(ch, false, false); ch = reload(ch);
    const RecoveryState stale = *ch->pcdata->recovery;
    const int before = fac->resource;
    next_day(); assert(process_character_recovery(ch));
    const int multiplier = UMIN(5, tier);
    assert(fac->resource == before - multiplier * (SANCTUARY_DEATH_COST / 5
        + SANCTUARY_MAIM_COST + SANCTUARY_MAIM_COST / 5));
    assert(!IS_FLAG(ch->act, PLR_DEAD) && !*ch->pcdata->maim);
    assert(!process_character_recovery(ch));
    const int charged_balance = fac->resource;
    *ch->pcdata->recovery = stale;
    SET_FLAG(ch->act, PLR_DEAD);
    assign(ch->pcdata->maim, "orange injury and black injury");
    assert(process_character_recovery(ch));
    assert(fac->resource == charged_balance);
  }
  fac->axes[AXES_CORRUPT] = old_stance;
  ch->fsociety = 0;
  ch->pcdata->tier_raised = 0;
  ch->skills[SKILL_SECONDCLASS] = -2;
  ch->pcdata->total_money = 0;
  record_death_recovery(ch, ch, false, false);
  SET_FLAG(ch->act, PLR_DEAD);
  save_char_obj(ch, false, false); ch = reload(ch);
  assert(ch->skills[SKILL_SECONDCLASS] == -2);
  next_day(); assert(process_character_recovery(ch));
  assert(ch->pcdata->total_money == -PERSONAL_SANCTUARY_DEATH_COST / 5);
  assert(!process_character_recovery(ch));
  ch->pcdata->total_money = -PERSONAL_SANCTUARY_DEBT_LIMIT;
  assert(!under_black(ch, ch));
  ch->pcdata->total_money = 0;
  save_char_obj(ch, false, false);
  // Older incident formats retain the original full fee.
  for (const char *version : {"RecoveryIncident", "RecoveryIncidentV2"}) {
    FILE *fp = tmpfile(); assert(fp);
    fprintf(fp, "0 1 0 0 1 123 old~ %s", !strcmp(version, "RecoveryIncidentV2") ? "receipt~" : "");
    rewind(fp); assert(read_recovery(fp, ch, version)); fclose(fp);
    assert(ch->pcdata->recovery->death.cost_percent == 100);
  }
  ch->pcdata->recovery->death = RecoveryIncident();
  puts("PASS: second-class stat training, orange/black aura display, protection matrix, exclusions, tiered discounted fees, mixed incidents, critical provenance and old/new saves.");
}
static void personal_recovery(FACTION_TYPE *fac) {
  auto *ch = player("Personalrecovery"); coverage(ch, RECOVERY_SANCTUARY);
  ch->pcdata->total_money = 0;
  assert(personal_sanctuary(ch) && !indentured_servant(ch));
  maim_char(ch, (char *)"personal injury", ch);
  next_day(); assert(process_character_recovery(ch));
  assert(ch->pcdata->total_money == 0); // No personal maim charge.
  record_death_recovery(ch, ch, false, false);
  assert(ch->pcdata->recovery->death.payer == RECOVERY_PERSONAL_PAYER);
  SET_FLAG(ch->act, PLR_DEAD);
  save_char_obj(ch, false, false); ch = reload(ch);
  next_day(); assert(process_character_recovery(ch));
  assert(ch->pcdata->total_money == -PERSONAL_SANCTUARY_DEATH_COST);
  assert(indentured_servant(ch) && get_lifeforce(ch, false, nullptr) <= 30);
  assert(!process_character_recovery(ch));
  ch = reload(ch);
  assert(ch->pcdata->total_money == -PERSONAL_SANCTUARY_DEATH_COST);
  assert(!process_character_recovery(ch)); // Reload cannot bill twice.
  ch->pcdata->lfcount = 1; ch->pcdata->lftotal = 30;
  assert(estimated_pay(ch) == 400); // Full-time double wage, unaffected by low LF.
  SET_FLAG(ch->act, PLR_NOPAY);
  assert(estimated_pay(ch) == 0 && IS_FLAG(ch->act, PLR_NOPAY));
  REMOVE_FLAG(ch->act, PLR_NOPAY);
  ch->pcdata->account = new_account();
  assign(ch->pcdata->account->name, "Personalrecovery");
  ch->pcdata->lastnotalone = current_time;
  ch->pcdata->emotes[EMOTE_PAY] = 5;
  const int expenses = estimated_expenses(ch) + garage_charge(ch);
  assert(payday(ch));
  assert(ch->pcdata->total_money == -PERSONAL_SANCTUARY_DEATH_COST + (400 - expenses) * 100);
  assert(!indentured_servant(ch) && get_lifeforce(ch, false, nullptr) > 30);
  ch->pcdata->total_money = -PERSONAL_SANCTUARY_DEBT_LIMIT + 1;
  assert(!debt_blocks_sanctuary(ch));
  ch->pcdata->total_money = -PERSONAL_SANCTUARY_DEBT_LIMIT;
  assert(debt_blocks_sanctuary(ch));
  assert(!under_understanding(ch, ch) && !seems_under_understanding(ch, ch));
  assign(ch->pcdata->understanding, "Limited");
  assert(!under_limited(ch, ch) && !seems_under_limited(ch, ch));
  record_death_recovery(ch, ch, false, false);
  assert(ch->pcdata->recovery->death.source == RECOVERY_NONE);
  ch->vassal = fac->vnum; coverage(ch, RECOVERY_SANCTUARY);
  assert(!debt_blocks_sanctuary(ch));
  record_death_recovery(ch, ch, false, false);
  assert(ch->pcdata->recovery->death.payer == fac->vnum);
  const int treasury = fac->resource;
  SET_FLAG(ch->act, PLR_DEAD); ch->vassal = 0;
  next_day(); assert(process_character_recovery(ch));
  assert(fac->resource == treasury - SANCTUARY_DEATH_COST);
  assert(ch->pcdata->total_money == -PERSONAL_SANCTUARY_DEBT_LIMIT);
  ch->pcdata->total_money = 0;
  assert(!indentured_servant(ch) && !debt_blocks_sanctuary(ch));
  puts("PASS: per-death personal fees, free maims, reload billing, debt cutoff, indentured LF/pay and captured vassal treasury.");
}
static void deaths(FACTION_TYPE *fac, CHAR_DATA *monster, CHAR_DATA *civilian) {
  const char *names[] = {"Uninsured", "Ordinary", "Ritual", "Forestordinary", "Forestritual", "Civilian"};
  for (int i = 0; i < 6; ++i) {
    auto *ch = player(names[i]); ch->fsociety = fac->vnum;
    int source = i == 0 ? RECOVERY_NONE : i == 2 || i == 4 ? RECOVERY_RITUAL : RECOVERY_SANCTUARY;
    coverage(ch, source);
    OBJ_DATA *coat = item(ch, "originalcoat", ITEM_CLOTHING, WEAR_BODY_1);
    OBJ_DATA *held = item(ch, "originalweapon", ITEM_WEAPON, WEAR_HOLD);
    OBJ_DATA *bag = item(ch, "originalbag", ITEM_CONTAINER);
    OBJ_DATA *nested = item(ch, "originalnested", ITEM_KEY);
    obj_from_char(nested); obj_to_obj(nested, bag);
    ROOM_INDEX_DATA *scene = ch->in_room;
    real_kill(ch, i == 3 || i == 4 ? monster : i == 5 ? civilian : ch);
    assert(IS_FLAG(ch->act, PLR_DEAD));
    assert(!ch->carrying && coat->in_obj && coat->in_obj->in_room == scene);
    assert(held->in_obj == coat->in_obj && bag->in_obj == coat->in_obj && nested->in_obj == bag);
    OBJ_DATA *corpse = coat->in_obj;
    const bool insured = i == 1 || i == 2 || i == 5;
    assert(ch->pcdata->recovery->death.source == (insured ? source : RECOVERY_NONE));
    auto saved = bytes(std::string(PLAYER_DIR) + capitalize(ch->name));
    assert(saved.find("originalcoat") == std::string::npos);
    ch = reload(ch);
    int balance = fac->resource;
    assert(!process_character_recovery(ch));
    coverage(ch, insured ? RECOVERY_NONE : RECOVERY_RITUAL);
    ch->fsociety = 0; // Captured payer remains responsible.
    next_day(); process_character_recovery(ch);
    assert(bool(IS_FLAG(ch->act, PLR_DEAD)) == !insured);
    if (insured) assert(at_trolly_stop(ch));
    assert(!ch->carrying && coat->in_obj == corpse && nested->in_obj == bag);
    assert(fac->resource == balance - (insured && source == RECOVERY_SANCTUARY ? SANCTUARY_DEATH_COST : 0));
    balance = fac->resource;
    process_character_recovery(ch); assert(fac->resource == balance);
    if (insured) {
      // Simulate stale player state after the durable treasury write.
      std::ofstream(std::string(PLAYER_DIR) + capitalize(ch->name), std::ios::binary) << saved;
      ch = reload(ch); process_character_recovery(ch); assert(fac->resource == balance);
      assert(!IS_FLAG(ch->act, PLR_DEAD) && !ch->carrying);
    }
  }
  puts("PASS: death coverage matrix, normal NPC versus forest source, original worn/held/nested inventory, relog, payer capture, and stale-save billing.");
}
static void maim_provenance(FACTION_TYPE *fac) {
  const char *names[] = {"Maimordinary", "Maimlimited", "Maimblack", "Maimritual"};
  const char *same = "left arm and hand injury";
  for (int i = 0; i < 4; ++i) {
    auto *ch = player(names[i]); ch->fsociety = fac->vnum;
    coverage(ch, RECOVERY_NONE); record_maim(ch, same, ch, false);
    const int source = i == 3 ? RECOVERY_RITUAL : RECOVERY_SANCTUARY;
    coverage(ch, source);
    ch->skills[SKILL_SECONDCLASS] = i == 1 ? -1 : i == 2 ? -2 : 0;
    record_maim(ch, same, ch, false); // Identical text is a separate injury.
    assert(ch->pcdata->recovery->maims.back().source == source);
    coverage(ch, RECOVERY_NONE);
    record_maim(ch, "injury during interruption", ch, false);
    const int drawback = ch->skills[SKILL_SECONDCLASS];
    ch->skills[SKILL_SECONDCLASS] = 0; coverage(ch, source);
    ch->skills[SKILL_SECONDCLASS] = drawback;
    save_char_obj(ch, false, false); ch = reload(ch);
    const int balance = fac->resource;
    next_day(); assert(process_character_recovery(ch));
    assert(!strcmp(ch->pcdata->maim, "left arm and hand injury and injury during interruption"));
    assert(ch->pcdata->recovery->maims.size() == 2);
    for (const auto &maim : ch->pcdata->recovery->maims)
      assert(maim.source == RECOVERY_NONE && maim.due == 0);
    const int cost = i == 3 ? 0 : i == 2 ? SANCTUARY_MAIM_COST / 5 : SANCTUARY_MAIM_COST;
    assert(fac->resource == balance - cost);
    ch = reload(ch); next_day(); assert(!process_character_recovery(ch));
    assert(!strcmp(ch->pcdata->maim, "left arm and hand injury and injury during interruption"));
  }
  // Legacy text has no provenance; neither a new maim nor protected death insures it.
  auto *legacy = player("Legacymaimcovered");
  assign(legacy->pcdata->maim, "old arm and leg injury");
  assert(legacy->pcdata->recovery->maims.empty());
  coverage(legacy, RECOVERY_RITUAL);
  record_maim(legacy, "new injury", legacy, false);
  real_kill(legacy, legacy);
  save_char_obj(legacy, false, false); legacy = reload(legacy);
  next_day(); assert(process_character_recovery(legacy));
  assert(!IS_FLAG(legacy->act, PLR_DEAD));
  assert(!strcmp(legacy->pcdata->maim, "old arm and leg injury"));

  // Explicit administrative replacement cannot reuse matching covered metadata.
  auto *edited = player("Maimedited"); coverage(edited, RECOVERY_RITUAL);
  auto *admin = player("Maimeditor"); admin->level = MAX_LEVEL;
  for (bool clear_first : {false, true}) {
    assign(edited->pcdata->maim, ""); edited->pcdata->recovery->maims.clear();
    record_maim(edited, "matching injury", edited, false);
    if (clear_first) {
      char command[] = "char Maimedited maim clear";
      do_string(admin, command); assert(!*edited->pcdata->maim);
    }
    char command[] = "char Maimedited maim matching injury";
    do_string(admin, command);
    assert(!strcmp(edited->pcdata->maim, "matching injury"));
    assert(edited->pcdata->recovery->maims.empty());
    save_char_obj(edited, false, false); edited = reload(edited);
    next_day(); assert(!process_character_recovery(edited));
    assert(!strcmp(edited->pcdata->maim, "matching injury"));
  }
  puts("PASS: full, limited, black and ritual recovery preserve old, duplicate and interrupted-coverage maims across reload; protected death and admin replacement cannot insure old injuries.");
}
static void suspended_ritual_recovery() {
  auto *ch = player("Ritualsuspended");
  auto *event = new_event(); event->type = EVENT_UNDERSTANDINGMINUS;
  event->valid = false; assign(event->author, "Someoneelse"); EventVect.push_back(event);
  for (int level : {0, -1, -2}) {
    ch->skills[SKILL_SECONDCLASS] = level;
    for (int reason = 0; reason < 6; ++reason) {
      coverage(ch, RECOVERY_RITUAL);
      record_maim(ch, "covered before suspension", ch, false);
      assert(ch->pcdata->recovery->maims.back().source == RECOVERY_RITUAL);
      AFFECT_DATA *revoked = nullptr;
      if (reason == 0) {
        AFFECT_DATA af = {}; af.where = TO_AFFECTS; af.duration = 36000;
        af.bitvector = AFF_NOUNDERSTANDING; affect_to_char(ch, &af);
        revoked = ch->affected;
      } else if (reason == 1) assign(ch->pcdata->understanding, "None");
      else if (reason == 2) ch->pcdata->total_money = -PERSONAL_SANCTUARY_DEBT_LIMIT;
      else if (reason == 3) {
        ch->pcdata->tier_raised = 3 - get_tier(ch);
        ch->pcdata->last_feeding = current_time - feeding_interval(ch) - 21 * 86400;
        assert(feeding_blocks_sanctuary(ch));
      } else if (reason == 4) restore_sanctuary_population(true);
      else {
        event->valid = true; event->active_time = current_time - 1;
        event->deactive_time = current_time + 2 * 86400;
      }
      assert(IS_AFFECTED(ch, AFF_UNDERSTANDING));
      assert(!under_sanctuary(ch, ch) && !under_black(ch, ch));
      record_maim(ch, "injury while suspended", ch, false);
      record_critical_injury(ch, ch, false);
      assert(ch->pcdata->recovery->critical.source == RECOVERY_NONE);
      record_death_recovery(ch, ch, false, false);
      assert(ch->pcdata->recovery->death.source == RECOVERY_NONE);
      assert(ch->pcdata->recovery->death.due == 0);
      assert(ch->pcdata->recovery->maims.back().source == RECOVERY_NONE);
      assert(ch->pcdata->recovery->maims.back().due == 0);
      next_day(); assert(process_character_recovery(ch));
      assert(!strcmp(ch->pcdata->maim, "injury while suspended"));
      if (revoked) affect_remove(ch, revoked);
      ch->pcdata->total_money = 0; ch->pcdata->tier_raised = 0;
      ch->pcdata->last_feeding = 0; event->valid = false;
      restore_sanctuary_population(false); coverage(ch, RECOVERY_RITUAL);
      next_day(); assert(!process_character_recovery(ch));
      assert(!strcmp(ch->pcdata->maim, "injury while suspended"));
      assign(ch->pcdata->maim, ""); ch->pcdata->recovery->maims.clear();
    }
  }
  puts("PASS: ritual full/limited/black coverage honors revocation, opt-out, debt, starvation, population and event suspension while preserving earlier covered maims.");
}
static void injuries(FACTION_TYPE *fac, CHAR_DATA *monster) {
  auto *ch = player("Mixedmaims"); ch->fsociety = fac->vnum;
  coverage(ch, RECOVERY_NONE); maim_char(ch, (char *)"Maim A", ch);
  coverage(ch, RECOVERY_SANCTUARY); maim_char(ch, (char *)"Maim B", ch);
  coverage(ch, RECOVERY_RITUAL); maim_char(ch, (char *)"Maim C", ch);
  maim_char(ch, (char *)"Maim D", monster);
  assert(ch->pcdata->recovery->maims.size() == 4);
  save_char_obj(ch, false, false); ch = reload(ch);
  int balance = fac->resource;
  next_day(); process_character_recovery(ch);
  assert(!strcmp(ch->pcdata->maim, "Maim A and Maim D"));
  assert(fac->resource == balance - SANCTUARY_MAIM_COST);
  ch = reload(ch); next_day(); process_character_recovery(ch);
  assert(!strcmp(ch->pcdata->maim, "Maim A and Maim D"));
  assert(fac->resource == balance - SANCTUARY_MAIM_COST);
  puts("PASS: independent maim provenance survives save/reload; only ordinary maim charges.");
  const char *names[] = {"Criticalnone", "Criticalordinary", "Criticalritual", "Criticalforest"};
  for (int i = 0; i < 4; ++i) {
    ch = player(names[i]); ch->fsociety = fac->vnum;
    coverage(ch, i == 3 ? RECOVERY_RITUAL : i);
    wound_char_absolute(ch, 3, i == 3 ? monster : ch);
    assert(ch->wounds == 3);
    save_char_obj(ch, false, false); ch = reload(ch);
    coverage(ch, i == 0 ? RECOVERY_SANCTUARY : RECOVERY_NONE);
    current_time += 7200;
    ch->death_timer = 1;
    pc_update(ch, -1);
    assert(IS_FLAG(ch->act, PLR_DEAD));
    balance = fac->resource;
    next_day(); process_character_recovery(ch);
    assert(bool(IS_FLAG(ch->act, PLR_DEAD)) == (i == 0 || i == 3));
    assert(fac->resource == balance - (i == 1 ? SANCTUARY_DEATH_COST : 0));
  }
  puts("PASS: critical bleed death inherits original ordinary/ritual/uninsured/forest coverage after coverage changes and reload.");
}
static void society_service_costs() {
  auto *fac = organization(990004);
  auto *ch = player("Serviceleader"); ch->fsociety = fac->vnum;
  assign(fac->leader, ch->name);
  const char *commands[] = {"develop sanctuary", "develop disposal", "develop scouts", "develop scanner", "develop comms"};
  const int attributes[] = {FACTION_UNDERSTANDING, FACTION_CORPSE, FACTION_SCOUTS, FACTION_911, FACTION_COMMS};
  const int setup[] = {100, 100, 25, 25, 30};
  for (int members : {0, 1, 3, 100}) {
    for (int i = 0; i < 100; ++i) assign(fac->member_names[i], i < members ? "Member" : "");
    const int billed = members ? members : 1;
    for (int i = 0; i < 5; ++i) {
      const int price = setup[i] * billed;
      fac->attributes[attributes[i]] = 0;
      fac->resource = price - 1;
      do_society(ch, const_cast<char *>(commands[i]));
      assert(!fac->attributes[attributes[i]] && fac->resource == price - 1);
      // Societies need only the actual setup price, with no protected reserve.
      fac->resource = price;
      do_society(ch, const_cast<char *>(commands[i]));
      assert(fac->attributes[attributes[i]] == 1 && fac->resource == 0);
      do_society(ch, const_cast<char *>(commands[i]));
      assert(!fac->attributes[attributes[i]] && fac->resource == 0);
      fac->resource = price;
      do_society(ch, const_cast<char *>(commands[i]));
      assert(fac->attributes[attributes[i]] == 1 && fac->resource == 0);
    }
    fac->resource = 1000000;
    fac->update = 0;
    faction_daily(fac);
    char expected[100];
    snprintf(expected, sizeof(expected), "Someone spends $%d resources on ongoing costs.", 3400 * billed);
    bool found = false;
    for (int i = 0; i < 20; ++i) if (strstr(fac->log[i], expected)) found = true;
    assert(found);
  }
  fac->secret_days = 100000;
  ch->pcdata->tier_raised = 4;
  assert(faction_secrecy(fac, ch) == 1000 && char_secrecy(ch, ch) == 1000);
  int balance = fac->resource;
  use_resources(123, fac->vnum, ch, (char *)"secrecy removal test");
  assert(fac->resource == balance - 123);
  // Faction setup retains its base rate even with a full roster.
  fac->type = FACTION_CORE; ch->fcore = fac->vnum;
  fac->attributes[FACTION_SCOUTS] = 0;
  balance = fac->resource;
  do_faction(ch, (char *)"develop scouts");
  assert(fac->attributes[FACTION_SCOUTS] && fac->resource == balance - 25);
  fac->attributes[FACTION_UNDERSTANDING] = 0;
  fac->resource = 2499;
  do_faction(ch, (char *)"develop sanctuary");
  assert(!fac->attributes[FACTION_UNDERSTANDING] && fac->resource == 2499);
  fac->resource = 2500;
  do_faction(ch, (char *)"develop sanctuary");
  assert(fac->attributes[FACTION_UNDERSTANDING] && fac->resource == 2400);
  puts("PASS: society service exact-price activation, insufficient funds, cancellation and upkeep scale with roster size; core setup rates and reserves stay fixed; secrecy is neutral.");
}
static void tiered_recovery_costs(FACTION_TYPE *fac) {
  const int old_stance = fac->axes[AXES_CORRUPT];
  fac->axes[AXES_CORRUPT] = AXES_DEMONIC;
  const char *names[] = {"Tierone", "Tiertwo", "Tierthree", "Tierfour", "Tierfive", "Tiersix"};
  const int death_costs[] = {5000, 10000, 15000, 20000, 25000, 25000};
  const int maim_costs[] = {1250, 2500, 3750, 5000, 6250, 6250};
  for (int i = 0; i < 6; ++i) {
    auto *ch = player(names[i]); ch->fsociety = fac->vnum;
    coverage(ch, RECOVERY_SANCTUARY);
    record_maim(ch, "tiered injury", ch, false);
    record_death_recovery(ch, ch, false, false);
    SET_FLAG(ch->act, PLR_DEAD);
    ch->pcdata->tier_raised += i + 1 - get_tier(ch);
    assert(get_tier(ch) == i + 1);
    save_char_obj(ch, false, false); ch = reload(ch);
    const int balance = fac->resource;
    next_day(); assert(process_character_recovery(ch));
    assert(!IS_FLAG(ch->act, PLR_DEAD) && !*ch->pcdata->maim);
    assert(fac->resource == balance - death_costs[i] - maim_costs[i]);
    assert(!process_character_recovery(ch));
    assert(fac->resource == balance - death_costs[i] - maim_costs[i]);
    ch->fsociety = 0;
    save_char_obj(ch, false, false);
  }
  fac->axes[AXES_CORRUPT] = old_stance;
  puts("PASS: revive and maim costs scale by recovery tier through T5, cap T6, survive reload, and bill once.");
}
static void clinic_recovery(FACTION_TYPE *fac) {
  auto *patient = player("Clinicrespawn");
  auto *sponsor = player("Clinicsponsor");
  auto *stranger = player("Clinicstranger");
  assign(patient->last_ip, "clinic-patient");
  assign(sponsor->last_ip, "clinic-sponsor");
  assign(stranger->last_ip, "clinic-stranger");
  auto *ins = new_institute();
  assign(ins->name, patient->name); assign(ins->asylum_owner, sponsor->name);
  ins->asylum_prestige = 100; ins->asylum_inactive = 0;
  ins->asylum_status = ASYLUM_REMOTECOMMIT; InVect.push_back(ins);
  ROOM_INDEX_DATA clinic = {}; clinic.subarea = (char *)"clinic";
  auto *original_room = patient->in_room;
  patient->in_room = &clinic;
  assert(clinic_patient(patient));
  assert(clinic_execution_allowed(sponsor, patient));
  assert(!clinic_execution_allowed(stranger, patient));
  assert(!clinic_execution_allowed(patient, patient));
  assign(ins->asylum_owner, fac->name); sponsor->faction = fac->vnum;
  assert(clinic_execution_allowed(sponsor, patient));
  sponsor->faction = 0; sponsor->factiontwo = fac->vnum;
  assert(clinic_execution_allowed(sponsor, patient));
  ins->asylum_status = ASYLUM_SELFCOMMIT;
  assert(!clinic_execution_allowed(sponsor, patient));
  ins->asylum_status = ASYLUM_REMOTECOMMIT;
  patient->in_room = original_room;
  assert(clinic_execution_allowed(stranger, patient));
  coverage(patient, RECOVERY_RITUAL);
  real_kill(patient, stranger);
  assert(IS_FLAG(patient->act, PLR_DEAD) && clinic_patient(patient));
  SET_FLAG(patient->act, PLR_BOUND); SET_FLAG(patient->act, PLR_BOUNDFEET);
  next_day(); assert(process_character_recovery(patient));
  assert(!clinic_patient(patient) && ins->asylum_inactive == 1 && ins->asylum_status == 0);
  assert(!IS_FLAG(patient->act, PLR_BOUND) && !IS_FLAG(patient->act, PLR_BOUNDFEET));
  assert(at_trolly_stop(patient));
  // Breakouts must also be discharged, so their timer cannot re-admit them.
  ins->asylum_inactive = 0; ins->asylum_status = ASYLUM_REMOTECOMMIT;
  ins->clinic_breakout = 100;
  release_clinic_after_respawn(patient);
  assert(ins->asylum_inactive == 1 && ins->clinic_breakout == 0);
  puts("PASS: clinic execution requires sponsorship and respawn discharges and unbinds patients, including breakouts.");
}

static void regeneration_and_operations(FACTION_TYPE *fac) {
  auto *ch = player("Regenerator"); ch->fsociety = fac->vnum;
  auto *ins = new_institute(); assign(ins->name, ch->name);
  ins->asylum_prestige = 100; ins->asylum_inactive = 0;
  ins->asylum_status = ASYLUM_REMOTECOMMIT; InVect.push_back(ins);
  coverage(ch, RECOVERY_SANCTUARY); ch->skills[SKILL_HYPERREGEN] = 3;
  auto *obj = item(ch, "regenitem", ITEM_KEY);
  real_kill(ch, ch); assert(IS_FLAG(ch->act, PLR_DEAD));
  auto *corpse = obj->in_obj; assert(corpse->timer == 20);
  int balance = fac->resource;
  resurrection(corpse);
  assert(!clinic_patient(ch) && ins->asylum_inactive == 1);
  assert(!IS_FLAG(ch->act, PLR_DEAD) && !ch->carrying && obj->in_obj == corpse);
  next_day(); process_character_recovery(ch); assert(fac->resource == balance);
  puts("PASS: Hyper Regeneration retains its corpse timer, recovers for free, and leaves original items behind.");
  ch->fsociety = 0;
  ch = player("Deadoperative"); coverage(ch, RECOVERY_NONE); real_kill(ch, ch);
  ch->faction = fac->vnum;
  auto *op = new_operation(); assign(op->sign_up[0], ch->name);
  assert(can_deploy(ch, op, 0));
  operation_recovery_wake(ch); assert(!IS_FLAG(ch->act, PLR_DEAD));
  assert(ch->pcdata->recovery->operation_dead);
  to_spectre(ch, true); assert(ch->pcdata->spectre == 1 && ch->pcdata->ghost_room == 98);
  char_from_room(ch); char_to_room(ch, get_room_index(16068));
  save_char_obj(ch, false, false); ch = reload(ch);
  wake_char(ch); assert(IS_FLAG(ch->act, PLR_DEAD) && ch->in_room->vnum == 98);
  next_day(); process_character_recovery(ch); assert(IS_FLAG(ch->act, PLR_DEAD));
  puts("PASS: operation wake and return preserve persistent death across save/reload.");
}
static void containment_recovery_costs() {
  auto *fac = organization(990005);
  assign(fac->name, "ContainmentTest");
  auto *patient = player("Prioritypatient"); patient->fsociety = fac->vnum;
  assign(fac->leader, patient->name);
  auto *high = player("Priorityhigh"); high->fsociety = fac->vnum;
  high->pcdata->tier_raised = 4 - get_tier(high);
  auto *legend = player("Prioritylegend"); legend->legacy_society = fac->vnum;
  legend->skills[SKILL_HYPERREGEN] = 1;
  assign(fac->member_names[0], high->name);
  assign(fac->member_names[1], legend->name);
  assign(fac->member_names[2], legend->name); // Corrupt duplicate rosters count once.
  assert(containment_priority_count(fac, patient) == 2);
  // Neutralizer implants clear the status globally, including independent societies.
  high->pcdata->neutralized = 1;
  legend->pcdata->neutralized = 1;
  assert(!is_containment_priority(high) && !is_containment_priority(legend));
  assert(containment_priority_count(fac, patient) == 0);
  high->pcdata->neutralized = 0;
  legend->pcdata->neutralized = 0;
  assert(is_containment_priority(high) && is_containment_priority(legend));
  assert(containment_priority_count(fac, patient) == 2);
  save_char_obj(legend, false, false);
  const std::string offline_path = std::string(PLAYER_DIR) + capitalize(legend->name);
  const std::string saved = bytes(offline_path);
  char_list.remove(legend); char_from_room(legend); free_char(legend);
  assert(containment_priority_count(fac, patient) == 2);
  assert(bytes(offline_path) == saved); // Read-only offline inspection.
  auto *implanted = player("Priorityimplanted");
  implanted->fsociety = fac->vnum;
  implanted->skills[SKILL_HYPERREGEN] = 1;
  implanted->pcdata->neutralized = 1;
  assign(fac->member_names[3], implanted->name);
  save_char_obj(implanted, false, false);
  char_list.remove(implanted); char_from_room(implanted); free_char(implanted);
  assert(containment_priority_count(fac, patient) == 2);

  coverage(patient, RECOVERY_SANCTUARY);
  record_maim(patient, "priority injury", patient, false);
  record_death_recovery(patient, patient, false, false);
  SET_FLAG(patient->act, PLR_DEAD);
  const RecoveryState stale = *patient->pcdata->recovery;
  int balance = fac->resource;
  next_day(); assert(process_character_recovery(patient));
  assert(fac->resource == balance - 7500 - 1875);
  *patient->pcdata->recovery = stale;
  SET_FLAG(patient->act, PLR_DEAD); assign(patient->pcdata->maim, "priority injury");
  assert(process_character_recovery(patient));
  assert(fac->resource == balance - 7500 - 1875);
  high->fsociety = 0; // A stale roster entry does not count as membership.
  assert(containment_priority_count(fac, patient) == 1);
  record_maim(patient, "rounded injury", patient, false);
  balance = fac->resource;
  next_day(); assert(process_character_recovery(patient));
  assert(fac->resource == balance - 1563);
  patient->skills[SKILL_SECONDCLASS] = -2;
  record_maim(patient, "discounted rounded injury", patient, false);
  record_death_recovery(patient, patient, false, false);
  SET_FLAG(patient->act, PLR_DEAD);
  balance = fac->resource;
  next_day(); assert(process_character_recovery(patient));
  assert(fac->resource == balance - 1250 - 313);
  patient->skills[SKILL_SECONDCLASS] = 0;
  do_society(patient, (char *)"position corrupt demonic");
  assert(fac->axes[AXES_CORRUPT] == AXES_DEMONIC);
  do_society(patient, (char *)"info ContainmentTest");
  assert(strstr(patient->desc->outbuf, "demonic"));
  assert(containment_priority_count(fac, patient) == 0);
  record_maim(patient, "demonic injury", patient, false);
  balance = fac->resource;
  next_day(); assert(process_character_recovery(patient));
  assert(fac->resource == balance - 1250);
  assert(faction_secrecy(fac, patient) == 1000 && char_secrecy(patient, patient) == 1000);

  auto *cortex = clan_lookup(FACTION_CORTEX);
  high->fcore = FACTION_CORTEX;
  high->race = RACE_PILLAR;
  high->pcdata->tier_raised = 0;
  high->skills[SKILL_HYPERREGEN] = 1;
  const int without_chip = containment_priority_count(cortex, high);
  assert(without_chip >= 1 && !cortex_loyalty_chip(high));
  high->pcdata->implant_frequency = 123;
  assert(cortex_loyalty_chip(high));
  assert(containment_priority_count(cortex, high) == without_chip - 1);
  high->pcdata->implant_frequency = 0;
  high->race = RACE_NEWVAMPIRE;
  assert(cortex_loyalty_chip(high));
  assert(containment_priority_count(cortex, high) == without_chip - 1);
  assert(is_containment_priority(high)); // Exempt characters keep the marker.
  assign(patient->pcdata->order_target, high->name);
  high->pcdata->birth_month = 1;
  high->shape = SHAPE_HUMAN;
  patient->pcdata->order_type = 20; // Hired investigation, no faction rank required.
  process_order(patient, 20);
  assert(strstr(patient->desc->outbuf, "CONTAINMENT PRIORITY"));
  assert(strstr(patient->desc->outbuf, "brainwashed"));

  auto *pact = player("Pactbonus");
  const int focus = focus_point_per_tier(pact), lf = lifeforce_mod(pact, nullptr);
  SET_FLAG(pact->act, PLR_DEMONPACT);
  assert(focus_point_per_tier(pact) == focus + 1);
  assert(lifeforce_mod(pact, nullptr) == lf + 5);
  fac->axes[AXES_CORRUPT] = AXES_NEUTRAL; fac->soft_restrict = 1;
  pact->in_fight = true;
  assert(!faction_hardelligible(pact, fac, false, nullptr));
  fac->axes[AXES_CORRUPT] = AXES_FARLEFT;
  assert(faction_hardelligible(pact, fac, false, nullptr));
  do_society(patient, (char *)"position demonic");
  assert(fac->axes[AXES_CORRUPT] == AXES_DEMONIC);
  save_clans(false);
  puts("PASS: containment costs count live/offline/legacy members once, round up, preserve receipts, exempt demonic societies and chipped Cortex members, and leave secrecy disabled; pact bonuses and hard bans apply.");
}


int main(int argc, char **) {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  if (argc > 1) {
    assert(clan_lookup(990005)->axes[AXES_CORRUPT] == AXES_DEMONIC);
    for (const char *name : {"originalcoat", "originalweapon", "originalbag", "originalnested"}) {
      int count = 0;
      for (auto *obj : object_list) if (!strcmp(obj->name, name)) {
        ++count; assert(!obj->carried_by && obj->in_obj);
      }
      assert(count == 6);
    }
    for (const char *name : {"Uninsured", "Forestordinary", "Forestritual", "Criticalnone", "Criticalforest"}) {
      auto *d = new_descriptor(); assert(load_char_obj(d, const_cast<char *>(name)));
      assert(IS_FLAG(d->character->act, PLR_DEAD) && !d->character->carrying);
      free_char(d->character);
    }
    assert(clan_lookup(990002)->resource == 123);
    assert(clan_lookup(990003)->resource == 90001);
    assert(faction_alliance(clan_lookup(990003)) == ALLIANCE_SIDERIGHT);
    auto *d = new_descriptor(); assert(load_char_obj(d, (char *)"Stalereceipt"));
    const int balance = clan_lookup(990001)->resource;
    current_time = d->character->pcdata->recovery->death.due + 1;
    assert(process_character_recovery(d->character));
    assert(clan_lookup(990001)->resource == balance);
    puts("PASS: reloaded treasury receipts prevent charging a stale player save again after reboot.");
    puts("PASS: fresh boot preserves corpse contents exactly once, uninsured deaths, small/large treasuries and faction alliance state.");
    return 0;
  }
  auto *fac = organization(990001);
  auto *monster = create_mobile(get_mob_index(10)); assert(forest_monster(monster));
  CHAR_DATA *civilian = nullptr;
  for (int id = 1; id < 10000 && !civilian; ++id) {
    auto *index = get_mob_index(id); if (!index) continue;
    auto *mob = create_mobile(index);
    if (!forest_monster(mob)) civilian = mob;
  }
  assert(civilian);
  char_to_room(monster, get_room_index(16068)); char_to_room(civilian, get_room_index(16068));
  // Locate exact boundary using the authoritative server clock.
  while (get_hour(nullptr) != 5) current_time += 3600;
  current_time -= current_time % 3600; current_time += 59 * 60;
  assert(next_sanctuary_recovery() == current_time + 60);
  current_time += 60; assert(next_sanctuary_recovery() == current_time + 86400);
  current_time += 60; assert(next_sanctuary_recovery() == current_time + 86340);
  puts("PASS: next 06:00 uses server time at 05:59, 06:00 and 06:01.");
  second_class_recovery(fac, monster, civilian);
  personal_recovery(fac);
  maim_provenance(fac);
  suspended_ritual_recovery();
  deaths(fac, monster, civilian); injuries(fac, monster); regeneration_and_operations(fac);
  clinic_recovery(fac);
  tiered_recovery_costs(fac);
  society_service_costs();
  containment_recovery_costs();
  auto *offline = player("Offlineinsured"); offline->fsociety = fac->vnum;
  coverage(offline, RECOVERY_NONE); record_maim(offline, "old offline injury", offline, false);
  coverage(offline, RECOVERY_SANCTUARY); record_maim(offline, "covered offline injury", offline, false);
  real_kill(offline, offline);
  char_list.remove(offline); char_from_room(offline); free_char(offline);
  int balance = fac->resource;
  current_time += 3 * 86400; process_daily_recoveries();
  auto *d = new_descriptor(); assert(load_char_obj(d, (char *)"Offlineinsured"));
  assert(!IS_FLAG(d->character->act, PLR_DEAD)); assert(at_trolly_stop(d->character));
  assert(!strcmp(d->character->pcdata->maim, "old offline injury"));
  assert(fac->resource == balance - SANCTUARY_DEATH_COST - SANCTUARY_MAIM_COST);
  process_daily_recoveries(); assert(fac->resource == balance - SANCTUARY_DEATH_COST - SANCTUARY_MAIM_COST);
  puts("PASS: offline overdue scan recovers once without requiring login and preserves preexisting maims.");
  // Replay a prepared transaction after the player half was replaced.
  const std::string path = std::string(PLAYER_DIR) + "Journalplayer";
  const std::string journal = std::string(PLAYER_DIR) + ".death-recovery-journal";
  const std::string ground_path = std::string(PLAYER_DIR) + "GroundObjects";
  std::string ground = bytes(ground_path), saved = bytes(std::string(PLAYER_DIR) + "Offlineinsured");
  std::ofstream(path) << "stale inventory";
  std::ofstream(journal, std::ios::binary) << path << '\n' << saved.size() << ' ' << ground.size() << '\n' << saved << ground;
  assert(haven::replay_death_snapshots());
  assert(bytes(path) == saved && bytes(ground_path) == ground);
  assert(haven::replay_death_snapshots());
  puts("PASS: interrupted death-save transaction replays both files idempotently.");
  auto *stale = player("Stalereceipt"); stale->fsociety = fac->vnum;
  coverage(stale, RECOVERY_SANCTUARY); real_kill(stale, stale);
  const std::string stale_path = std::string(PLAYER_DIR) + "Stalereceipt";
  std::string before_charge = bytes(stale_path);
  next_day(); assert(process_character_recovery(stale));
  std::ofstream(stale_path, std::ios::binary) << before_charge;
  auto *small = organization(990002); small->resource = 123;
  auto *large = organization(990003, FACTION_CORE); large->resource = 90001;
  large->strategic_alliance = ALLIANCE_SIDERIGHT;
  normalize_alliance_data(); assert(small->resource == 123 && large->resource == 90001);
  assert(save_clans(false));
  auto *ch = player("Safetycases");
  for (const char *text : {"", "   ", "42", "42 Body.\n\r"}) {
    assign(ch->description, text);
    replace_focused(ch, -1, (char *)"Replacement.");
    assert(strstr(ch->description, "Replacement."));
    append_focused(ch, -1, (char *)"Addition.");
    assert(strstr(ch->description, "Replacement. Addition."));
  }
  std::string long_message(MSL * 2, 'm');
  append_messages(ch, const_cast<char *>(long_message.c_str()));
  assert(strlen(ch->pcdata->messages) >= long_message.size());
  auto *other = player("Protectedsex"); coverage(ch, RECOVERY_NONE); coverage(other, RECOVERY_SANCTUARY);
  const int before_sex = other->pcdata->last_sex;
  other->wounds = 4;
  do_rape(ch, (char *)"Protectedsex coital");
  assert(other->pcdata->last_sex == before_sex);
  assert(strstr(ch->desc->outbuf, "Sanctuary prevents"));
  puts("PASS: empty/whitespace/digit focused edits, long messages, and sexual Sanctuary protection.");
  auto *legacy = player("Legacydead");
  SET_FLAG(legacy->act, PLR_DEAD); assign(legacy->pcdata->maim, "old injury");
  save_char_obj(legacy, false, false);
  const std::string legacy_path = std::string(PLAYER_DIR) + "Legacydead";
  std::istringstream legacy_input(bytes(legacy_path));
  std::string line, old_format;
  while (std::getline(legacy_input, line))
    if (line.compare(0, 8, "Recovery")) old_format += line + "\n";
  std::ofstream(legacy_path) << old_format;
  legacy = reload(legacy); coverage(legacy, RECOVERY_RITUAL);
  next_day(); assert(!process_character_recovery(legacy));
  assert(IS_FLAG(legacy->act, PLR_DEAD) && !strcmp(legacy->pcdata->maim, "old injury"));
  auto *payer = player("Payercase"); coverage(payer, RECOVERY_SANCTUARY);
  payer->fsociety = fac->vnum; payer->legacy_society = small->vnum;
  payer->vassal = large->vnum; payer->fcore = fac->vnum; payer->faction = small->vnum;
  for (int expected : {fac->vnum, small->vnum, large->vnum, fac->vnum, RECOVERY_PERSONAL_PAYER}) {
    maim_char(payer, (char *)"covered injury", payer);
    assert(payer->pcdata->recovery->maims.back().payer == expected);
    if (payer->fsociety) payer->fsociety = 0;
    else if (payer->legacy_society) payer->legacy_society = 0;
    else if (payer->vassal) payer->vassal = 0;
    else payer->fcore = 0;
  }
  puts("PASS: pre-metadata dead/maimed saves remain uninsured; payer priority covers society, legacy, vassal and faction fallbacks.");
  int sockets[2]; assert(socketpair(AF_UNIX, SOCK_STREAM, 0, sockets) == 0);
  assert(write(sockets[0], "toolongforbuffer\n\r", 18) == 18);
  char small_buffer[8]; assert(!read_from_ident(sockets[1], small_buffer, sizeof(small_buffer)));
  close(sockets[0]); close(sockets[1]);
  for (int n = 0; n < 15; ++n) {
    assert(socketpair(AF_UNIX, SOCK_STREAM, 0, sockets) == 0);
    close(sockets[0]);
    auto *connection = new_descriptor(); connection->descriptor = sockets[1];
    assert(!read_from_descriptor(connection));
    close(sockets[1]); free_descriptor(connection);
  }
  puts("PASS: oversized ident replies and repeated ordinary socket EOFs cannot overflow or crash the server.");
  const char *suffixes[] = {"location", "specialroleone", "specialroletwo", "conclusion"};
  const char *arguments[] = {"Here", "Branding", "Helpless", "yes"};
  for (int scene = 1; scene <= 18; ++scene) {
    for (int field = 0; field < 4; ++field) {
      std::string tokens[4] = {std::string(10000, 'a'), std::string(10000, 'b'),
                               std::string(10000, 'c'), std::string(10000, 'd')};
      std::string original = tokens[0] + " " + tokens[1] + " " + tokens[2] + " " + tokens[3];
      assign(ch->pcdata->ci_excludes[scene - 1], original.c_str());
      ch->pcdata->ci_editing = 16;
      char handler_name[80]; snprintf(handler_name, sizeof(handler_name), "do_scene%02d%s", scene, suffixes[field]);
      auto handler = reinterpret_cast<void (*)(CHAR_DATA *, char *)>(dlsym(RTLD_DEFAULT, handler_name));
      assert(handler);
      handler(ch, const_cast<char *>(arguments[field]));
      tokens[field] = std::to_string(field == 0 ? ch->in_room->vnum : field == 1 ? DEST_FEAT_BRAND : field == 2 ? DEST_FEAT_HELPLESS : 1);
      assert(tokens[0] + " " + tokens[1] + " " + tokens[2] + " " + tokens[3] == ch->pcdata->ci_excludes[scene - 1]);
    }
  }
  puts("PASS: all 72 scene field editors preserve other fields with output larger than MSL.");
}
