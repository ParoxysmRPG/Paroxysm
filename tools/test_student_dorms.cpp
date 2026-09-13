// Linked with the real engine; run only in a disposable copy of the world.
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <queue>
#include <set>
#include "merc.h"
#include "recycle.h"

extern "C" {
extern char str_boot_time[];
extern char *enclave_room[2 * MAX_DORMROOMS];
void boot_db();
void load_dorms();
void save_dorms();
void dorms_update();
bool door_locked(EXIT_DATA *, ROOM_INDEX_DATA *, CHAR_DATA *);
}

static void clear_output(CHAR_DATA *ch) {
  ch->desc->outtop = 0;
  ch->desc->outbuf[0] = '\0';
}

static void command(CHAR_DATA *ch, void (*fn)(CHAR_DATA *, char *), const char *arg) {
  clear_output(ch);
  char text[MSL];
  strcpy(text, arg);
  fn(ch, text);
}

static void run(CHAR_DATA *ch, const char *input) {
  command(ch, interpret, input);
}

static void output_contains(CHAR_DATA *ch, const char *expected) {
  if (!strstr(ch->desc->outbuf, expected))
    fprintf(stderr, "Expected output [%s], got [%s]\n", expected, ch->desc->outbuf);
  assert(strstr(ch->desc->outbuf, expected));
}

static void place(CHAR_DATA *ch, int vnum) {
  if (ch->in_room) char_from_room(ch);
  char_to_room(ch, get_room_index(vnum));
}

static CHAR_DATA *student(const char *name, bool enrolled = true) {
  CHAR_DATA *ch = new_char();
  if (!ch->pcdata) ch->pcdata = new_pcdata();
  ch->level = 1;
  ch->trust = 0;
  ch->name = str_dup(name);
  ch->desc = new_descriptor();
  ch->desc->character = ch;
  ch->desc->connected = CON_PLAYING;
  ch->position = POS_STANDING;
  ch->hit = 1000;
  char_list.push_front(ch);
  register_live_character(ch);
  if (enrolled) {
    INSTITUTE_TYPE *ins = new_institute();
    ins->name = str_dup(name);
    ins->college_prestige = 1;
    InVect.push_back(ins);
  }
  place(ch, 16156);
  return ch;
}

static void locked(EXIT_DATA *a, EXIT_DATA *b) {
  SET_BIT(a->exit_info, EX_CLOSED | EX_LOCKED);
  SET_BIT(b->exit_info, EX_CLOSED | EX_LOCKED);
}

static void roster(CHAR_DATA *viewer, int hall, const char *house, int room,
                   const char *resident, const char *roommate = NULL) {
  place(viewer, hall);
  run(viewer, "look roster");
  char expected[160];
  snprintf(expected, sizeof(expected), "House %s Roster", house);
  output_contains(viewer, expected);
  if (roommate)
    snprintf(expected, sizeof(expected), "Room %d: %s | Roommate: %s", room, resident, roommate);
  else
    snprintf(expected, sizeof(expected), "Room %d: %s", room, resident);
  output_contains(viewer, expected);
}

static INSTITUTE_TYPE *enrollment(CHAR_DATA *ch) {
  for (INSTITUTE_TYPE *ins : InVect)
    if (!str_cmp(ins->name, ch->name)) return ins;
  assert(false);
  return NULL;
}

static WEEKLY_TYPE *activity(CHAR_DATA *ch, int days) {
  WEEKLY_TYPE *weekly = new_weekly();
  free_string(weekly->charname);
  weekly->charname = str_dup(ch->name);
  weekly->logon = current_time - days * 24 * 3600;
  WeeklyVect.push_back(weekly);
  return weekly;
}

static void offline(CHAR_DATA *ch) {
  save_char_obj(ch, FALSE, FALSE);
  char_list.remove(ch);
  unregister_live_character(ch);
  ch->desc->connected = CON_GET_NAME;
}

int main() {
  current_time = time(NULL);
  strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  for (int i = 0; i < 2 * MAX_DORMROOMS; ++i) {
    free_string(enclave_room[i]);
    enclave_room[i] = str_dup("");
  }
  const int halls[] = {3881, 8996, 3894, 9032};
  const int landings[] = {9023, 9431, 3963, 9465};
  const int bathrooms[] = {9026, 9000, 9053, 9047};
  const int bedrooms[][5] = {
    {3341, 9017, 9016, 9003, 9004},
    {8997, 9005, 9001, 9006, 9014},
    {9049, 9050, 5951, 9037, 9038},
    {9035, 9034, 9033, 9036, 9042}
  };
  const char *names[] = {"Bishop", "Rook", "Queenson", "Kingson"};
  // Walkable common paths from the covered campus walkway, without flying,
  // swimming, crossing walls, or passing through somebody else's bedroom.
  std::queue<int> pending;
  std::set<int> reachable;
  pending.push(15641);
  while (!pending.empty()) {
    int vnum = pending.front(); pending.pop();
    if (!reachable.insert(vnum).second) continue;
    ROOM_INDEX_DATA *r = get_room_index(vnum);
    assert(r && r->sector_type != SECT_AIR && r->sector_type != SECT_WATER);
    for (int d = 0; d < MAX_DIR; ++d) {
      EXIT_DATA *e = r->exit[d];
      if (!e || !e->u1.to_room || !student_dormitory(e->u1.to_room)) continue;
      if (e->wall != WALL_NONE || e->jump || e->climb || e->fall) continue;
      if (IS_SET(e->exit_info, EX_LOCKED)) continue;
      EXIT_DATA *back = e->u1.to_room->exit[rev_dir[d]];
      assert(back && back->u1.to_room == r && back->wall == WALL_NONE);
      pending.push(e->u1.to_room->vnum);
    }
  }
  for (int n : {16156, 3347, 3477, 3883, 3881, 8996, 3894, 9032,
                9023, 9431, 3963, 9465, 9026, 9000, 9053, 9047})
    assert(reachable.count(n));

  CHAR_DATA *owner = student("DormAuditOwner");
  CHAR_DATA *roomie = student("DormAuditRoommate");
  CHAR_DATA *outsider = student("DormAuditOutsider", false);
  assert(college_student(owner, FALSE) && !IS_IMMORTAL(owner));
  place(owner, 15641);
  move_char(owner, DIR_WEST, FALSE, FALSE);
  assert(owner->in_room->vnum == 16156);
  move_char(owner, DIR_UP, FALSE, FALSE);
  assert(owner->in_room->vnum == 3347);
  assert(!student_dormitory(get_room_index(COLLEGE_ROOM_FOR_THREE)));
  for (int h = 0; h < 4; ++h) {
    for (int i = 0; i < 5; ++i) {
      const int slot = h * 5 + i;
      ROOM_INDEX_DATA *room = get_room_index(bedrooms[h][i]);
      assert(room && student_dormitory(room));
      char expected[80]; snprintf(expected, sizeof(expected), "%s %d", names[h], i + 1);
      assert(!strcmp(room->name, expected));
      assert(room->sector_type == SECT_HOUSE && IS_SET(room->room_flags, ROOM_INDOORS));
      assert(IS_SET(room->room_flags, ROOM_BEDROOM));
      assert(room->description_decorated && room->places);
      int door = -1, open_routes = 0;
      ROOM_INDEX_DATA *hall = NULL;
      EXIT_DATA *entrance = NULL, *back = NULL;
      for (int d = 0; d < MAX_DIR; ++d) {
        EXIT_DATA *e = room->exit[d];
        if (!e || e->wall != WALL_NONE) continue;
        ++open_routes;
        hall = e->u1.to_room;
        assert(hall && (hall->vnum == halls[h] || hall->vnum == landings[h]));
        door = rev_dir[d]; back = e; entrance = hall->exit[door];
        assert(entrance && entrance->u1.to_room == room);
      }
      assert(open_routes == 1 && reachable.count(hall->vnum));
      for (EXIT_DATA *e : {entrance, back}) {
        assert(e->wall == WALL_NONE && !e->jump && !e->climb && !e->fall);
        assert(IS_SET(e->exit_info, EX_ISDOOR));
        assert(IS_SET(e->exit_info, EX_CLOSED) && IS_SET(e->exit_info, EX_LOCKED));
        assert(is_name("door", e->keyword));
      }
      char number[8]; snprintf(number, sizeof(number), "%d", i + 1);
      char rent_command[24]; snprintf(rent_command, sizeof(rent_command), "rent %s", number);
      char roomie_command[24]; snprintf(roomie_command, sizeof(roomie_command), "roomie %s", number);
      place(outsider, halls[h]); run(outsider, rent_command);
      assert(!*enclave_room[slot]);
      place(owner, halls[h]); run(owner, rent_command);
      assert(!str_cmp(enclave_room[slot], owner->name) && owner->money == 0);
      // The command itself must persist the rental, without an autosave tick.
      load_dorms();
      assert(!str_cmp(enclave_room[slot], owner->name));
      roster(outsider, halls[h], names[h], i + 1, owner->name);
      place(owner, hall->vnum); place(outsider, hall->vnum);
      assert(!bblocked(room, owner) && bblocked(room, outsider));
      assert(!door_locked(entrance, room, owner) && door_locked(entrance, room, outsider));
      command(outsider, do_open, dir_name[door][0]);
      assert(IS_SET(entrance->exit_info, EX_CLOSED));
      command(owner, do_open, dir_name[door][0]);
      assert(!IS_SET(entrance->exit_info, EX_CLOSED) && !IS_SET(back->exit_info, EX_CLOSED));
      move_char(owner, door, FALSE, FALSE);
      assert(owner->in_room == room);
      // Closing behind the resident must not trap them inside.
      place(owner, room->vnum); locked(entrance, back);
      assert(!door_locked(back, hall, owner));
      command(owner, do_open, dir_name[rev_dir[door]][0]);
      assert(!IS_SET(back->exit_info, EX_CLOSED));
      move_char(owner, rev_dir[door], FALSE, FALSE);
      assert(owner->in_room == hall);
      // Roommate keys survive the same persistence path as resident keys.
      place(roomie, halls[h]); run(roomie, roomie_command);
      assert(!str_cmp(enclave_room[slot + MAX_DORMROOMS], roomie->name));
      load_dorms();
      assert(!str_cmp(enclave_room[slot], owner->name));
      assert(!str_cmp(enclave_room[slot + MAX_DORMROOMS], roomie->name));
      roster(outsider, halls[h], names[h], i + 1, owner->name, roomie->name);
      place(roomie, hall->vnum); locked(entrance, back);
      assert(!door_locked(entrance, room, roomie));
      command(roomie, do_open, dir_name[door][0]);
      assert(!IS_SET(entrance->exit_info, EX_CLOSED));
      run(roomie, "roomie stop");
      load_dorms();
      assert(!*enclave_room[slot + MAX_DORMROOMS]);
      roster(outsider, halls[h], names[h], i + 1, owner->name, "Vacant");
      run(owner, "rent stop");
      load_dorms();
      assert(!*enclave_room[slot] && !*enclave_room[slot + MAX_DORMROOMS]);
      roster(outsider, halls[h], names[h], i + 1, "Vacant");
      assert(!strstr(outsider->desc->outbuf, owner->name));
      assert(!strstr(outsider->desc->outbuf, roomie->name));
      assert(bblocked(room, owner) && bblocked(room, roomie));
      printf("PASS: %s rental, doors, roommate, persistence, exit\n", expected);
    }
  }
  CHAR_DATA *third = student("DormAuditThird");
  for (int h = 0; h < 4; ++h) {
    const int slot = h * 5;
    // All common house locations and bedrooms must route to the same rooms.
    place(owner, landings[h]); run(owner, "rent 1");
    load_dorms();
    assert(!str_cmp(enclave_room[slot], owner->name));
    place(outsider, bathrooms[h]); run(outsider, "roomie 1");
    assert(!*enclave_room[slot + MAX_DORMROOMS]);
    place(roomie, bathrooms[h]); run(roomie, "roomie 1");
    load_dorms();
    assert(!str_cmp(enclave_room[slot + MAX_DORMROOMS], roomie->name));

    place(third, halls[h]); run(third, "rent 1");
    assert(!str_cmp(enclave_room[slot], owner->name));
    run(third, "roomie 1");
    assert(!str_cmp(enclave_room[slot + MAX_DORMROOMS], roomie->name));
    for (const char *invalid : {"rent 0", "rent 6", "roomie 0", "roomie 6", "roomie 8"}) {
      run(third, invalid);
      for (int i = 0; i < 2 * MAX_DORMROOMS; ++i)
        assert(str_cmp(enclave_room[i], third->name));
    }

    // One character cannot accumulate additional primary or roommate leases.
    const int other = ((h + 1) % 4) * 5;
    place(owner, halls[(h + 1) % 4]); run(owner, "rent 2");
    assert(!*enclave_room[other + 1]);
    place(roomie, halls[(h + 1) % 4]); run(roomie, "rent 2");
    assert(!*enclave_room[other + 1]);
    place(third, halls[(h + 1) % 4]); run(third, "rent 2");
    assert(!str_cmp(enclave_room[other + 1], third->name));
    run(owner, "roomie 2"); run(roomie, "roomie 2");
    assert(!*enclave_room[other + 1 + MAX_DORMROOMS]);
    run(third, "rent stop");

    // Leaving the primary lease immediately transfers the remaining resident's key.
    place(owner, bedrooms[h][0]); run(owner, "rent stop");
    load_dorms();
    assert(!str_cmp(enclave_room[slot], roomie->name));
    assert(!*enclave_room[slot + MAX_DORMROOMS]);
    assert(bblocked(get_room_index(bedrooms[h][0]), owner));
    assert(!bblocked(get_room_index(bedrooms[h][0]), roomie));
    roster(outsider, halls[h], names[h], 1, roomie->name);

    run(outsider, "look");
    char heading[80]; snprintf(heading, sizeof(heading), "House %s Roster", names[h]);
    output_contains(outsider, heading);
    output_contains(outsider, roomie->name);
    for (const char *alias : {"look board", "look noticeboard"}) {
      run(outsider, alias);
      output_contains(outsider, heading);
      output_contains(outsider, roomie->name);
    }
    place(roomie, bathrooms[h]); run(roomie, "rent stop");
    load_dorms();
    assert(!*enclave_room[slot]);
  }
  for (int entrance : {16156, 3347}) {
    place(outsider, entrance);
    for (const char *look : {"look", "look roster"}) {
      run(outsider, look);
      for (const char *house : names) {
        char heading[80]; snprintf(heading, sizeof(heading), "House %s Roster", house);
        output_contains(outsider, heading);
      }
    }
  }
  puts("PASS: house-wide commands, rent constraints, promotion and entrance rosters");

  // Exercise real cleanup with a mix of online and saved offline residents.
  place(owner, halls[0]); run(owner, "rent 1");
  place(roomie, halls[0]); run(roomie, "roomie 1");
  WEEKLY_TYPE *owner_activity = activity(owner, 8);
  activity(roomie, 8);
  enrollment(owner)->inactivity = 501;
  enrollment(roomie)->inactivity = 501;
  dorms_update();
  assert(!str_cmp(enclave_room[0], owner->name));
  assert(!str_cmp(enclave_room[MAX_DORMROOMS], roomie->name));
  // Once offline, crossing the campus inactivity threshold releases the lease
  // even when the saved last login is recent; the online roommate stays.
  owner_activity->logon = current_time;
  offline(owner);

  CHAR_DATA *keeper = student("DormAuditBoundary");
  CHAR_DATA *idle_roomie = student("DormAuditIdleRoomie");
  CHAR_DATA *idle_owner = student("DormAuditIdleOwner");
  CHAR_DATA *deleted = student("DormAuditDeleted");
  CHAR_DATA *withdrawn = student("DormAuditWithdrawn");
  place(keeper, halls[0]); run(keeper, "rent 2");
  place(idle_roomie, halls[0]); run(idle_roomie, "roomie 2");
  place(idle_owner, halls[0]); run(idle_owner, "rent 3");
  place(deleted, halls[0]); run(deleted, "rent 4");
  place(withdrawn, halls[0]); run(withdrawn, "rent 5");
  assert(!str_cmp(enclave_room[1], keeper->name));
  assert(!str_cmp(enclave_room[1 + MAX_DORMROOMS], idle_roomie->name));
  assert(!str_cmp(enclave_room[2], idle_owner->name));
  assert(!str_cmp(enclave_room[3], deleted->name));
  assert(!str_cmp(enclave_room[4], withdrawn->name));
  WEEKLY_TYPE *keeper_activity = activity(keeper, 7);
  activity(idle_roomie, 8);
  activity(deleted, 0);
  activity(withdrawn, 0);
  enrollment(keeper)->inactivity = 500;
  enrollment(withdrawn)->college_prestige = 0;
  // No weekly record for this resident: cleanup must read the saved activity.
  idle_owner->activeat = current_time - 8 * 24 * 3600;
  for (CHAR_DATA *ch : {keeper, idle_roomie, idle_owner, deleted, withdrawn}) offline(ch);
  char deleted_path[MIL];
  snprintf(deleted_path, sizeof(deleted_path), "%s%s", PLAYER_DIR, capitalize(deleted->name));
  assert(std::remove(deleted_path) == 0);

  dorms_update();
  // Verify automatic persistence as well as removal of roommate access.
  load_dorms();
  assert(!str_cmp(enclave_room[0], roomie->name));
  assert(!*enclave_room[MAX_DORMROOMS]);
  assert(!str_cmp(enclave_room[1], keeper->name));
  assert(!*enclave_room[1 + MAX_DORMROOMS]);
  for (int i = 2; i < 5; ++i) assert(!*enclave_room[i]);
  assert(bblocked(get_room_index(bedrooms[0][0]), owner));
  assert(!bblocked(get_room_index(bedrooms[0][0]), roomie));
  assert(bblocked(get_room_index(bedrooms[0][1]), idle_roomie));
  roster(outsider, halls[0], names[0], 1, roomie->name);
  output_contains(outsider, keeper->name);
  for (CHAR_DATA *ch : {owner, idle_roomie, idle_owner, deleted, withdrawn})
    assert(!strstr(outsider->desc->outbuf, ch->name));

  keeper_activity->logon = current_time - 8 * 24 * 3600;
  dorms_update();
  load_dorms();
  assert(!*enclave_room[1]);
  roster(outsider, halls[0], names[0], 2, "Vacant");
  assert(!strstr(outsider->desc->outbuf, keeper->name));
  place(third, halls[0]); run(third, "rent 3");
  load_dorms();
  assert(!str_cmp(enclave_room[2], third->name));
  roster(outsider, halls[0], names[0], 3, third->name);
  assert(!bblocked(get_room_index(bedrooms[0][2]), third));
  assert(bblocked(get_room_index(bedrooms[0][2]), idle_owner));
  CHAR_DATA *departing = student("DormAuditDeparting");
  CHAR_DATA *absent = student("DormAuditAbsent");
  place(departing, halls[0]); run(departing, "rent 4");
  place(absent, halls[0]); run(absent, "roomie 4");
  assert(!str_cmp(enclave_room[3 + MAX_DORMROOMS], absent->name));
  activity(absent, 8);
  offline(absent);
  run(departing, "rent stop");
  load_dorms();
  assert(!*enclave_room[3] && !*enclave_room[3 + MAX_DORMROOMS]);
  roster(outsider, halls[0], names[0], 4, "Vacant");
  assert(!strstr(outsider->desc->outbuf, absent->name));
  assert(bblocked(get_room_index(bedrooms[0][3]), absent));
  puts("PASS: inactivity boundaries, saved activity fallback, deleted and unenrolled residents");
  puts("PASS: inactive roommates released, active roommates promoted, cleanup saved and roster updated");
  puts("PASS: all 20 student dorms and common campus access");
}
