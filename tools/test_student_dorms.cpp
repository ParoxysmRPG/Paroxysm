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
bool door_locked(EXIT_DATA *, ROOM_INDEX_DATA *, CHAR_DATA *);
}

static void command(CHAR_DATA *ch, void (*fn)(CHAR_DATA *, char *), const char *arg) {
  char text[MSL];
  strcpy(text, arg);
  fn(ch, text);
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
  ch->position = POS_STANDING;
  ch->hit = 1000;
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
      place(outsider, halls[h]); command(outsider, do_rent, number);
      assert(!*enclave_room[slot]);
      place(owner, halls[h]); command(owner, do_rent, number);
      assert(!str_cmp(enclave_room[slot], owner->name) && owner->money == 0);
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
      place(roomie, halls[h]); command(roomie, do_roomie, number);
      assert(!str_cmp(enclave_room[slot + MAX_DORMROOMS], roomie->name));
      save_dorms(); load_dorms();
      assert(!str_cmp(enclave_room[slot], owner->name));
      assert(!str_cmp(enclave_room[slot + MAX_DORMROOMS], roomie->name));
      place(roomie, hall->vnum); locked(entrance, back);
      assert(!door_locked(entrance, room, roomie));
      command(roomie, do_open, dir_name[door][0]);
      assert(!IS_SET(entrance->exit_info, EX_CLOSED));
      command(roomie, do_roomie, "stop"); command(owner, do_rent, "stop");
      assert(bblocked(room, owner) && bblocked(room, roomie));
      printf("PASS: %s rental, doors, roommate, persistence, exit\n", expected);
    }
  }
  puts("PASS: all 20 student dorms and common campus access");
}
