// Full-engine integration tests, run in a disposable world by test_phone_delivery.py.
#include "merc.h"
#include "recycle.h"
#include "spy_camera.h"
#include <cassert>
#include <cstring>
#include <ctime>

extern "C" {
extern char str_boot_time[];
void do_text(CHAR_DATA *, char *);
void do_teletext(CHAR_DATA *, char *);
void do_telesay(CHAR_DATA *, char *);
void do_drive(CHAR_DATA *, char *);
void do_phone(CHAR_DATA *, char *);
void second_update();
void pc_update(CHAR_DATA *, int);
OBJ_DATA *find_phone(CHAR_DATA *, int);
void save_rooms(FILE *, AREA_DATA *);
}

static void assign(char *&field, const char *value) { free_string(field); field = str_dup(value); }
static CHAR_DATA *player(const char *name, int number) {
  auto *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->race = RACE_HUMAN; ch->position = POS_STANDING; ch->hit = 100;
  ch->id = get_pc_id(); ch->logon = current_time; ch->played = 100 * 3600;
  auto *account = new_account(); assign(account->name, name);
  account->maxhours = 100; ch->pcdata->account = account;
  assign(ch->pcdata->account_name, name);
  ch->desc = new_descriptor(); ch->desc->character = ch; ch->desc->account = account;
  ch->desc->connected = CON_PLAYING; descriptor_list.push_back(ch->desc);
  char_to_room(ch, get_room_index(16068)); char_list.push_front(ch);
  auto *phone = create_object(get_obj_index(OBJ_VNUM_PHONE), 0);
  phone->item_type = ITEM_PHONE; phone->value[0] = number;
  REMOVE_BIT(phone->extra_flags, ITEM_OFF); assign(phone->name, "phone"); assign(phone->material, "");
  obj_to_char(phone, ch); equip_char(ch, phone, WEAR_HOLD);
  assert(get_phone(ch) == phone && cell_signal(ch));
  return ch;
}
static void command(CHAR_DATA *ch, DO_FUN *handler, const char *value) {
  char input[MAX_INPUT_LENGTH]; snprintf(input, sizeof(input), "%s", value); handler(ch, input);
}
static bool has(CHAR_DATA *ch, const char *text) { return strstr(get_phone(ch)->material, text); }
static void clear(CHAR_DATA *ch) { assign(get_phone(ch)->material, ""); }

static void loudspeakers(CHAR_DATA *sender, CHAR_DATA *target, CHAR_DATA *third, CHAR_DATA *fourth) {
  ROOM_INDEX_DATA *origin = sender->in_room;
  ROOM_INDEX_DATA *remote = get_room_index(taxi_table[0].vnum);
  assert(remote && remote != origin);
  command(sender, do_call, "990002");
  command(target, do_pickup, "");
  assert(target->pcdata->connection_stage == CONNECT_TALKING);
  for (auto *ch : {sender, fourth}) { char_from_room(ch); char_to_room(ch, remote); }
  auto reset = [&]() {
    for (auto *ch : {sender, target, third, fourth}) {
      ch->desc->outtop = 0; ch->desc->outbuf[0] = '\0';
    }
  };
  auto broadcast = [](CHAR_DATA *ch) { return strstr(ch->desc->outbuf, "A phone on loudspeaker says"); };
  auto say = [&](const char *words) { do_function(sender, do_say, (char *)words); };
  reset(); say("private call");
  assert(strstr(target->desc->outbuf, "Your phone says"));
  assert(!broadcast(third));

  command(target, do_phone, "loudspeaker on");
  command(target, do_phone, "loudspeaker on"); // Explicit on is idempotent.
  reset(); say("loudspeaker normal speech");
  assert(broadcast(third) && strstr(third->desc->outbuf, "loudspeaker normal speech"));
  assert(!broadcast(target) && !broadcast(sender) && !broadcast(fourth));
  assert(!strstr(broadcast(third) + 1, "A phone on loudspeaker says"));

  reset(); say("to phone directed speech");
  assert(broadcast(third) && strstr(third->desc->outbuf, "directed speech"));
  assert(!broadcast(target) && !broadcast(fourth));

  third->pcdata->sleeping = 10;
  reset(); say("sleeping listener"); assert(!broadcast(third));
  third->pcdata->sleeping = 0;
  SET_FLAG(third->affected_by, AFF_DEAF);
  reset(); say("deaf listener"); assert(!broadcast(third));
  REMOVE_FLAG(third->affected_by, AFF_DEAF);

  command(target, do_phone, "silent");
  reset(); say("silent ringer still audible"); assert(broadcast(third));
  command(target, do_phone, "silent");
  command(target, do_phone, "loudspeaker off");
  reset(); say("private again"); assert(!broadcast(third));
  command(target, do_phone, "loudspeaker off");
  reset(); say("still private"); assert(!broadcast(third));

  // Each end independently controls who hears incoming speech.
  command(sender, do_phone, "loudspeaker");
  reset(); do_function(target, do_say, (char *)"reverse call speech");
  assert(broadcast(fourth) && !broadcast(sender) && !broadcast(third));
  command(sender, do_phone, "loudspeaker");
  command(target, do_phone, "loudspeaker on");
  sender->skills[SKILL_ELECTROPATHIC] = 2;
  assert(get_skill(sender, SKILL_ELECTROPATHIC) >= 1);
  reset(); do_function(sender, do_telesay, (char *)"electropathic call speech");
  assert(broadcast(third) && strstr(third->desc->outbuf, "electropathic call speech"));
  sender->skills[SKILL_ELECTROPATHIC] = 0;
  command(target, do_phone, "loudspeaker off");
  command(sender, do_hangup, "");
  reset(); say("after hangup"); assert(!broadcast(third));
  for (auto *ch : {sender, fourth}) { char_from_room(ch); char_to_room(ch, origin); }
  puts("PASS: loudspeaker toggles, normal/directed/electropathic speech, room scope, hearing and independent call ends");
}

static void electropathic_controls(CHAR_DATA *sender, CHAR_DATA *target,
    CHAR_DATA *third, CHAR_DATA *fourth) {
  OBJ_DATA *phone = get_phone(target);
  OBJ_DATA *own_phone = get_phone(third);
  auto loudspeaker = [&]() { return get_extra_descr("+loudspeaker", phone->extra_descr) != nullptr; };
  auto control = [&](const char *value) { command(third, do_phone, value); };
  command(sender, do_call, "990002");
  third->skills[SKILL_ELECTROPATHIC] = 2;
  control("PhoneTarget loudspeaker on"); assert(!loudspeaker()); // Ringing is not an answered call.
  command(target, do_pickup, "");
  third->skills[SKILL_ELECTROPATHIC] = 0;
  control("PhoneTarget loudspeaker on"); assert(!loudspeaker());
  third->skills[SKILL_ELECTROPATHIC] = 2;
  assert(get_skill(third, SKILL_ELECTROPATHIC) > 0);
  SET_FLAG(third->affected_by, AFF_BLIND);
  control("PhoneTarget loudspeaker on"); assert(!loudspeaker());
  REMOVE_FLAG(third->affected_by, AFF_BLIND);
  SET_FLAG(third->affected_by, AFF_SILENCED);
  control("PhoneTarget loudspeaker on"); assert(!loudspeaker());
  REMOVE_FLAG(third->affected_by, AFF_SILENCED);
  SET_FLAG(target->affected_by, AFF_SILENCED);
  control("PhoneTarget loudspeaker on"); assert(!loudspeaker());
  REMOVE_FLAG(target->affected_by, AFF_SILENCED);
  ROOM_INDEX_DATA *origin = target->in_room;
  char_from_room(target); char_to_room(target, get_room_index(taxi_table[0].vnum));
  control("PhoneTarget loudspeaker on"); assert(!loudspeaker());
  char_from_room(target); char_to_room(target, origin);
  sender->pcdata->connected_to = fourth;
  control("PhoneTarget loudspeaker on"); assert(!loudspeaker());
  sender->pcdata->connected_to = target;

  // Electropaths need no phone, and control the phone used by the target's call.
  obj_from_char(own_phone);
  control("PhoneTarget loudspeaker on"); assert(loudspeaker());
  assert(!get_phone(third) && !get_extra_descr("+loudspeaker", own_phone->extra_descr));
  third->desc->outtop = 0; third->desc->outbuf[0] = '\0';
  do_function(sender, do_say, (char *)"electropath overhears caller");
  assert(strstr(third->desc->outbuf, "A phone on loudspeaker says"));
  control("PhoneTarget loudspeaker off"); assert(!loudspeaker());
  control("PhoneTarget silent"); assert(IS_SET(phone->extra_flags, ITEM_SILENT));
  control("PhoneTarget silent"); assert(!IS_SET(phone->extra_flags, ITEM_SILENT));
  control("PhoneTarget ringtone a psychic ringtone");
  assert(!str_cmp(get_extra_descr("+ringtone", phone->extra_descr), "a psychic ringtone"));
  control("PhoneTarget on"); assert(!IS_SET(phone->extra_flags, ITEM_OFF));
  control("PhoneTarget loudspeaker invalid"); assert(!loudspeaker());
  phone->value[4] = 990004;
  control("PhoneTarget clean"); assert(phone->value[4] == 990004);
  phone->value[4] = 0;

  // Switching off somebody else's phone must not disconnect the electropath.
  obj_to_char(own_phone, third); equip_char(third, own_phone, WEAR_HOLD);
  command(third, do_call, "990004"); command(fourth, do_pickup, "");
  assert(third->pcdata->connected_to == fourth);
  third->pcdata->cam_spy_char = sender;
  target->pcdata->cam_spy_char = fourth;
  auto *spare = create_object(get_obj_index(OBJ_VNUM_PHONE), 0);
  assign(spare->name, "phone"); spare->item_type = ITEM_PHONE;
  REMOVE_BIT(spare->extra_flags, ITEM_OFF); obj_to_char(spare, target);
  control("PhoneTarget off");
  assert(IS_SET(phone->extra_flags, ITEM_OFF) && get_phone(target) == spare);
  assert(!target->pcdata->connected_to && !sender->pcdata->connected_to);
  assert(target->pcdata->connection_stage == CONNECT_NONE && sender->pcdata->connection_stage == CONNECT_NONE);
  assert(third->pcdata->connected_to == fourth && fourth->pcdata->connected_to == third);
  assert(!target->pcdata->cam_spy_char && third->pcdata->cam_spy_char == sender);
  assert(!IS_SET(own_phone->extra_flags, ITEM_OFF));
  control("PhoneTarget loudspeaker on");
  assert(!get_extra_descr("+loudspeaker", spare->extra_descr));
  extract_obj(spare);
  command(target, do_phone, "on");
  command(third, do_hangup, "");
  third->pcdata->cam_spy_char = nullptr; third->skills[SKILL_ELECTROPATHIC] = 0;
  puts("PASS: nearby electropathic phone controls, active-call/skill/sight/signal checks and target-only power-off");
}

static void calls(CHAR_DATA *sender, CHAR_DATA *target, CHAR_DATA *third, CHAR_DATA *fourth) {
  command(sender, do_call, "990001");
  assert(!sender->pcdata->connected_to && sender->pcdata->connection_stage == CONNECT_NONE);
  command(sender, do_call, "9999999");
  assert(!sender->pcdata->connected_to);
  assert(strstr(sender->desc->outbuf, "not available"));

  command(sender, do_call, "990002");
  assert(sender->pcdata->connected_to == target && target->pcdata->connected_to == sender);
  OBJ_DATA *phone = get_phone(target);
  SET_BIT(phone->extra_flags, ITEM_OFF);
  command(target, do_pickup, "");
  assert(target->pcdata->connection_stage == CONNECT_RINGING);
  REMOVE_BIT(phone->extra_flags, ITEM_OFF);
  command(target, do_pickup, "");
  assert(sender->pcdata->connection_stage == CONNECT_TALKING && target->pcdata->connection_stage == CONNECT_TALKING);
  command(target, do_hangup, "");
  assert(!sender->pcdata->connected_to && !target->pcdata->connected_to);
  assert(sender->pcdata->connection_stage == CONNECT_NONE && target->pcdata->connection_stage == CONNECT_NONE);

  command(sender, do_call, "990002");
  command(target, do_phone, "off");
  assert(!sender->pcdata->connected_to && !target->pcdata->connected_to);
  command(target, do_phone, "on");

  // An obsolete one-sided connection must not alter someone else's current call.
  command(third, do_call, "990004");
  sender->pcdata->connected_to = third; sender->pcdata->connection_stage = CONNECT_RINGING;
  command(sender, do_pickup, "");
  assert(!sender->pcdata->connected_to && third->pcdata->connected_to == fourth);
  sender->pcdata->connected_to = third; sender->pcdata->connection_stage = CONNECT_NONE;
  command(sender, do_hangup, "");
  assert(!sender->pcdata->connected_to && third->pcdata->connected_to == fourth);
  command(third, do_hangup, "");

  third->race = fourth->race = RACE_CIVIL_SERVANT;
  third->desc->outtop = fourth->desc->outtop = 0;
  third->desc->outbuf[0] = fourth->desc->outbuf[0] = '\0';
  command(sender, do_call, "911");
  assert(sender->pcdata->connected_to == third || sender->pcdata->connected_to == fourth);
  assert((strstr(third->desc->outbuf, "Dispatch connects") != nullptr)
      != (strstr(fourth->desc->outbuf, "Dispatch connects") != nullptr));
  command(sender, do_hangup, "");
  third->race = fourth->race = RACE_HUMAN;
  for (auto *ch : {sender, target, third, fourth}) clear(ch);
  puts("PASS: self/unavailable calls, pickup, two-sided hangup, stale connections and single emergency responder");
}

static void driving() {
  auto *driver = player("DriveTester", 990010);
  auto *one = player("PassengerOne", 990011);
  auto *two = player("PassengerTwo", 990012);
  ROOM_INDEX_DATA *origin = get_room_index(taxi_table[0].vnum);
  assert(origin);
  for (auto *ch : {driver, one, two}) { char_from_room(ch); char_to_room(ch, origin); }
  driver->pcdata->garage_cost[0] = 20000;
  driver->pcdata->garage_status[0] = GARAGE_ACTIVE;
  driver->pcdata->garage_typeone[0] = 6; // CAR_SPORTSBIKE (travel.c).
  driver->pcdata->garage_typetwo[0] = -1;
  assign(driver->pcdata->garage_name[0], "test motorcycle");
  one->master = two->master = driver;
  assert(has_active_vehicle(driver));

  command(driver, do_drive, "slow");
  assert(IS_FLAG(driver->comm, COMM_SLOW) && !IS_FLAG(one->comm, COMM_SLOW));
  command(driver, do_drive, "slow");
  command(driver, do_drive, "");
  assert(driver->in_room == origin);
  assign(driver->pcdata->drivenames[0], "missing");
  driver->pcdata->driveloc[0] = -999;
  driver->pcdata->garage_location[0] = -999;
  command(driver, do_drive, "missing");
  assert(driver->in_room == origin && driver->pcdata->garage_location[0] == 0);

  // Fill every cab: failure must preserve the parked vehicle and pending action.
  std::vector<CHAR_DATA *> occupants;
  for (int vnum = INIT_CABS; vnum < END_CABS; ++vnum) {
    auto *room = get_room_index(vnum);
    if (!room) continue;
    auto *occupant = new_char(); SET_FLAG(occupant->act, ACT_IS_NPC);
    char_to_room(occupant, room); char_list.push_front(occupant); occupants.push_back(occupant);
  }
  driver->pcdata->process_timer = 20;
  assign(origin->vehicle_lplates[0], vehicle_lplate(driver));
  origin->vehicle_cost[0] = 20000;
  command(driver, do_drive, "2 PassengerOne PassengerTwo");
  assert(driver->in_room == origin && one->in_room == origin && two->in_room == origin);
  assert(driver->pcdata->process_timer == 20 && origin->vehicle_cost[0] == 20000);
  assert(strstr(driver->desc->outbuf, "no room to begin"));
  for (auto *occupant : occupants) {
    char_from_room(occupant); char_list.remove(occupant); free_char(occupant);
  }

  // Luring must resolve once for the whole vehicle, using the actual origin.
  EXIT_DATA *saved_exits[10];
  for (int dir = 0; dir < 10; ++dir) {
    saved_exits[dir] = origin->exit[dir]; origin->exit[dir] = nullptr;
  }
  SET_FLAG(driver->affected_by, AFF_LURED);
  driver->pcdata->lured_room = taxi_table[2].vnum;
  assert(path_dir(origin, get_room_index(taxi_table[2].vnum), -1, driver) == -1);
  command(driver, do_drive, "2 PassengerOne PassengerTwo");
  assert(driver->in_room != origin);
  assert(driver->pcdata->travel_time == 2);
  assert(driver->pcdata->travel_to == taxi_table[2].vnum);
  assert((one->in_room == driver->in_room) != (two->in_room == driver->in_room));
  CHAR_DATA *passenger = one->in_room == driver->in_room ? one : two;
  assert(passenger->pcdata->travel_to == driver->pcdata->travel_to);
  assert(passenger->pcdata->travel_time == driver->pcdata->travel_time);
  assert(passenger->pcdata->travel_from == origin->vnum && driver->pcdata->travel_from == origin->vnum);
  command(driver, do_drive, "slow");
  assert(IS_FLAG(passenger->comm, COMM_SLOW));
  passenger->pcdata->travel_type = TRAVEL_HPASSENGER;
  command(passenger, do_drive, "slow");
  assert(IS_FLAG(passenger->comm, COMM_SLOW));
  passenger->pcdata->travel_type = TRAVEL_BPASSENGER;
  command(driver, do_drive, "slow");
  DescList saved_descriptors = descriptor_list;
  descriptor_list.clear();
  descriptor_list.push_back(driver->desc); descriptor_list.push_back(passenger->desc);
  for (int tick = 0; tick < 3; ++tick) second_update();
  descriptor_list = saved_descriptors;
  assert(driver->in_room == get_room_index(taxi_table[2].vnum));
  assert(passenger->in_room == driver->in_room && driver->pcdata->travel_time == -1);
  for (int dir = 0; dir < 10; ++dir) origin->exit[dir] = saved_exits[dir];
  puts("PASS: drive capacity, full cabins, empty destination, lured route consistency and passenger speed controls");
  puts("PASS: driving without a path still delivers the driver and passenger to their destination");
}

static void walking() {
  auto *walker = player("WalkTester", 990020);
  ROOM_INDEX_DATA *origin = walker->in_room;
  time_t start = current_time;
  command(walker, do_walk, "2");
  assert(walker->walking == 1 && walker->walk_started_at == start);
  ROOM_INDEX_DATA *destination = walker->destination;
  assert(destination && destination != origin);
  current_time = start + 600;
  assert(!finish_overdue_walk(walker) && walker->in_room == origin);
  walker->wait = 100; // Movement delays must not postpone the fallback.
  current_time = start + 601;
  pc_update(walker, 0);
  assert(walker->in_room == destination);
  assert(walker->walking == 0 && !walker->destination && walker->walk_started_at == 0);
  command(walker, do_walk, "1");
  assert(walker->walk_started_at == current_time);
  command(walker, do_walk, "stop");
  current_time += 601;
  assert(!finish_overdue_walk(walker) && walker->in_room == destination);
  command(walker, do_walk, "0");
  command(walker, do_walk, "not-a-destination");
  assert(walker->walking == 0 && !walker->destination);
  assign(walker->pcdata->drivenames[0], "testhome");
  walker->pcdata->driveloc[0] = origin->vnum;
  command(walker, do_walk, "testhome");
  assert(walker->destination == origin && walker->walk_started_at == current_time);
  current_time += 30;
  command(walker, do_walk, "1");
  assert(walker->walk_started_at == current_time);
  command(walker, do_walk, "stop");
  current_time = start;
  puts("PASS: ten-minute walking boundary, delayed movement, destination arrival, cancellation and fresh journey timers");
}

static void assert_history_saved(const char *message) {
  save_texthistories();
  std::ifstream saved(TEXTHISTORY_FILE);
  std::string contents(std::istreambuf_iterator<char>(saved), {});
  assert(contents.find(message) != std::string::npos);
}

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  bool found_help = false;
  for (HELP_DATA *help = help_first; help; help = help->next)
    if (!str_cmp(help->keyword, "compromised")) {
      found_help = strstr(help->text, "30,000") && strstr(help->text, "48 hours");
    }
  assert(found_help);
  auto *sender = player("PhoneSender", 990001);
  auto *target = player("PhoneTarget", 990002);
  auto *third = player("PhoneThird", 990003);
  auto *fourth = player("PhoneFourth", 990004);
  calls(sender, target, third, fourth);
  loudspeakers(sender, target, third, fourth);
  electropathic_controls(sender, target, third, fourth);
  auto *event = new_event(); event->valid = true; event->type = EVENT_COMPROMISED;
  assign(event->target, sender->name); event->active_time = current_time - 1;
  event->deactive_time = current_time + 3600; EventVect.push_back(event);

  save_texthistories();
  command(sender, do_text, "990002 direct-message");
  assert_history_saved("direct-message");
  assert(has(target, "direct-message"));
  assert(has(third, "copied text") != has(fourth, "copied text"));
  assert(!has(sender, "copied text") && !has(target, "copied text"));
  clear(third); clear(fourth);
  command(sender, do_text, "990002"); // Empty text must not trigger a copy.
  assert(!has(third, "copied text") && !has(fourth, "copied text"));
  assign(get_phone(target)->material, std::string(16000, 'x').c_str());
  command(sender, do_text, "990002 full-inbox");
  assert(!has(third, "copied text") && !has(fourth, "copied text"));
  clear(target);

  auto *group = new_grouptext(); group->valid = true; assign(group->tname, "phone-audit");
  group->pnumber[0] = 990001; group->pnumber[1] = 990002; group->pnumber[2] = 990003;
  GTextVect.push_back(group);
  mark_grouptexts_dirty(); save_grouptexts();
  command(sender, do_text, "phone-audit group-message");
  save_grouptexts();
  {
    std::ifstream saved(GROUPTEXT_FILE);
    std::string contents(std::istreambuf_iterator<char>(saved), {});
    assert(contents.find("group-message") != std::string::npos);
  }
  assert(has(target, "group-message") && has(third, "group-message"));
  assert(!has(target, "copied text") && !has(third, "copied text"));
  assert(has(fourth, "copied text") && has(fourth, "group-message"));
  assert(strstr(group->history, "group-message"));
  SET_BIT(get_phone(third)->extra_flags, ITEM_OFF);
  OBJ_DATA *third_phone = find_phone(third, 990003);
  assert(third_phone == nullptr);
  command(sender, do_text, "phone-audit off-phone-message");
  for (OBJ_DATA *item = third->carrying; item; item = item->next_content)
    if (item->item_type == ITEM_PHONE) REMOVE_BIT(item->extra_flags, ITEM_OFF);
  assert(!has(third, "off-phone-message"));
  command(sender, do_text, "phone-audit reenabled-phone-message");
  assert(has(third, "reenabled-phone-message"));
  command(fourth, do_text, "history phone-audit");
  assert(strstr(fourth->desc->outbuf, "You are not a member"));

  clear(third); clear(fourth);
  event->deactive_time = current_time;
  command(sender, do_text, "990002 expired-scheme");
  assert_history_saved("expired-scheme");
  assert(has(target, "expired-scheme"));
  assert(!has(third, "copied text") && !has(fourth, "copied text"));
  event->deactive_time = current_time + 3600;
  sender->skills[SKILL_ELECTROPATHIC] = 2;
  command(sender, do_teletext, "990002 anonymous-message");
  assert(has(target, "anonymous-message"));
  assert(has(third, "copied text") != has(fourth, "copied text"));
  clear(third); clear(fourth);
  auto *from_profile = new_profile(); assign(from_profile->name, sender->name);
  assign(from_profile->handle, "@phone-sender"); ProfileVect.push_back(from_profile);
  auto *to_profile = new_profile(); assign(to_profile->name, target->name);
  assign(to_profile->handle, "@phone-target"); ProfileVect.push_back(to_profile);
  assert(!dm_to_person(sender, target->name, (char *)"unmatched", FALSE));
  auto *match = new_match(); assign(match->nameone, sender->name); assign(match->nametwo, target->name);
  match->status_one = match->status_two = 1; MatchVect.push_back(match);
  command(sender, do_text, "@phone-target dm-message");
  assert_history_saved("dm-message");
  assert(has(target, "dm-message"));
  assert(has(third, "copied text") != has(fourth, "copied text"));
  clear(third); clear(fourth);
  auto *book = new PHONEBOOK_TYPE{}; book->number = 990002; book->owner = str_dup(target->name);
  PhoneVect.push_back(book);
  save_char_obj(target, FALSE, FALSE);
  command(sender, do_call, "990002");
  assert(sender->pcdata->connected_to == target);
  descriptor_list.remove(target->desc); target->desc->character = nullptr; target->desc = nullptr;
  extract_char(target, TRUE);
  assert(!sender->pcdata->connected_to && sender->pcdata->connection_stage == CONNECT_NONE);
  assert(!get_char_world_pc(book->owner));
  command(sender, do_text, "phone-audit offline-group-message");
  assert(has(third, "offline-group-message") && has(fourth, "copied text"));
  clear(third); clear(fourth);
  command(sender, do_text, "990002 offline-message");
  assert_history_saved("offline-message");
  assert(has(third, "copied text") != has(fourth, "copied text"));
  assert(dm_to_person(sender, book->owner, (char *)"phone", TRUE));
  DESCRIPTOR_DATA loaded = {};
  assert(load_char_obj(&loaded, book->owner));
  OBJ_DATA *stored = find_phone(loaded.character, 990002);
  assert(stored && strstr(stored->material, "offline-message") && strstr(stored->material, "offline-group-message") && strstr(stored->material, "A photo message"));
  free_char(loaded.character);
  // Camera lifecycle notices use the real online/offline saved-message path.
  ROOM_INDEX_DATA *camera_room = sender->in_room;
  camera_notify(camera_room, 990001, sender->name, false);
  assert(strstr(sender->pcdata->messages, "found and destroyed in a bugsweep"));
  assert(strstr(sender->desc->outbuf, "found and destroyed in a bugsweep"));
  camera_notify(camera_room, 990002, book->owner, true);
  DESCRIPTOR_DATA camera_loaded = {};
  assert(load_char_obj(&camera_loaded, book->owner));
  assert(strstr(camera_loaded.character->pcdata->messages, "has expired"));
  free_char(camera_loaded.character);

  // Saving must preserve timer/planter metadata beyond 20 ordinary descriptions.
  EXTRA_DESCR_DATA *original_ed = camera_room->extra_descr;
  auto *camera_ed = new_extra_descr(); assign(camera_ed->keyword, "!bugs");
  const std::string camera_record = "990001:" + std::to_string(current_time + 604800) + ":" + sender->name;
  assign(camera_ed->description, camera_record.c_str()); camera_ed->next = original_ed;
  camera_room->extra_descr = camera_ed;
  for (int i = 0; i < 22; ++i) {
    auto *extra = new_extra_descr(); assign(extra->keyword, "camera-test-padding");
    extra->next = camera_room->extra_descr; camera_room->extra_descr = extra;
  }
  AREA_DATA isolated_area = {}; isolated_area.vnum = 2;
  AREA_DATA *original_area = camera_room->area; camera_room->area = &isolated_area;
  FILE *camera_save = tmpfile(); assert(camera_save);
  save_rooms(camera_save, &isolated_area); rewind(camera_save);
  std::string serialized; char saved_line[MSL];
  while (fgets(saved_line, sizeof(saved_line), camera_save)) serialized += saved_line;
  fclose(camera_save); camera_room->area = original_area;
  assert(serialized.find(camera_record) != std::string::npos);
  while (camera_room->extra_descr != original_ed) {
    auto *extra = camera_room->extra_descr; camera_room->extra_descr = extra->next;
    free_extra_descr(extra);
  }
  puts("PASS: camera online/offline notices and timer/planter area persistence beyond description limit");
  puts("PASS: real direct/group/DM/teletext and offline delivery, single scheme copies, rejection paths and group-history access");
  command(sender, do_society, "list");
  assert(!strstr(sender->desc->outbuf, "Unaffiliated"));
  driving();
  walking();
}
