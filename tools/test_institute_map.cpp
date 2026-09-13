#include <cassert>
#include <cstdio>
#include <cstring>
#include <ctime>
#include "merc.h"
#include "recycle.h"

extern "C" {
extern char str_boot_time[];
void boot_db();
bool door_locked(EXIT_DATA *, ROOM_INDEX_DATA *, CHAR_DATA *);
bool can_decorate_p(CHAR_DATA *, ROOM_INDEX_DATA *);
}

static void command(CHAR_DATA *ch, void (*fn)(CHAR_DATA *, char *), const char *arg) {
  char text[MSL]; strcpy(text, arg); fn(ch, text);
}

static void place(CHAR_DATA *ch, int vnum) {
  if (ch->in_room) char_from_room(ch);
  char_to_room(ch, get_room_index(vnum));
}

static CHAR_DATA *student(const char *name) {
  CHAR_DATA *ch = new_char();
  if (!ch->pcdata) ch->pcdata = new_pcdata();
  ch->name = str_dup(name); ch->level = 1; ch->trust = 0;
  ch->position = POS_STANDING; ch->hit = 1000;
  ch->desc = new_descriptor(); ch->desc->character = ch;
  return ch;
}

static void walk(CHAR_DATA *ch, int direction, int destination) {
  EXIT_DATA *e = ch->in_room->exit[direction];
  assert(e && e->u1.to_room && e->u1.to_room->vnum == destination);
  assert(e->wall == WALL_NONE && !e->jump && !e->climb && !e->fall);
  if (IS_SET(e->exit_info, EX_CLOSED)) command(ch, do_open, dir_name[direction][0]);
  move_char(ch, direction, FALSE, FALSE);
  if (ch->in_room->vnum != destination)
    fprintf(stderr, "Failed to walk %s to %d:\n%s", dir_name[direction][0], destination, ch->desc->outbuf);
  assert(ch->in_room->vnum == destination);
}

int main() {
  current_time = time(NULL); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  CHAR_DATA *owner = student("InstituteMapOwner");
  CHAR_DATA *other = student("InstituteMapOther");
  INSTITUTE_TYPE *ins = new_institute();
  ins->name = str_dup(owner->name); ins->college_prestige = 1; InVect.push_back(ins);
  INSTITUTE_TYPE *outsider = new_institute();
  outsider->name = str_dup(other->name); outsider->college_prestige = 1; InVect.push_back(outsider);
  const int ids[][6] = {
    {3864, 3865, 3870, 3882, 3892, 4310},
    {3230, 3804, 3798, 3809, 3800, 3818},
    {4385, 4386, 4393, 4396, 4716, 4719},
    {4790, 4795, 4798, 4804, 4823, 4831}
  };
  const int houses[] = {HOUSE_REPENT, HOUSE_PURITY, HOUSE_FORBEAR, HOUSE_CHARITY};
  const char *names[] = {"Repentance", "Purity", "Forbearance", "Charity"};
  for (int h = 0; h < 4; ++h) {
    ins->college_house = outsider->college_house = houses[h];
    for (int i = 0; i < 6; ++i) {
      ROOM_INDEX_DATA *bedroom = get_room_index(ids[h][i]);
      char expected[80]; snprintf(expected, sizeof(expected), "%s %d", names[h], i + 1);
      assert(bedroom && !strcmp(bedroom->name, expected));
      assert(bedroom->sector_type == SECT_HOUSE && IS_SET(bedroom->room_flags, ROOM_BEDROOM));
      ins->dorm_room = bedroom->vnum;
      bool tested = false;
      for (int d = 0; d < MAX_DIR; ++d) {
        EXIT_DATA *back = bedroom->exit[d];
        if (!back || back->wall != WALL_NONE || !IS_SET(back->exit_info, EX_ISDOOR)) continue;
        ROOM_INDEX_DATA *hall = back->u1.to_room;
        EXIT_DATA *entrance = hall->exit[rev_dir[d]];
        assert(entrance && entrance->u1.to_room == bedroom && entrance->wall == WALL_NONE);
        SET_BIT(entrance->exit_info, EX_LOCKED | EX_CLOSED);
        SET_BIT(back->exit_info, EX_LOCKED | EX_CLOSED);
        place(owner, hall->vnum); place(other, hall->vnum);
        assert(college_student(owner, FALSE) && dorm_room(owner) == bedroom->vnum);
        assert(!bblocked(bedroom, owner) && bblocked(bedroom, other));
        assert(!door_locked(entrance, bedroom, owner) && door_locked(entrance, bedroom, other));
        command(other, do_open, dir_name[rev_dir[d]][0]);
        assert(IS_SET(entrance->exit_info, EX_CLOSED));
        walk(owner, rev_dir[d], bedroom->vnum);
        assert(can_decorate_p(owner, bedroom));
        SET_BIT(entrance->exit_info, EX_LOCKED | EX_CLOSED);
        SET_BIT(back->exit_info, EX_LOCKED | EX_CLOSED);
        walk(owner, d, hall->vnum);
        tested = true;
      }
      assert(tested);
    }
    printf("PASS: %s six assigned bedrooms, resident keys, privacy and exit\n", names[h]);
  }
  // No resident can walk from the lawn straight through their bedroom floor.
  for (int n : {9355, 9356, 9912, 9913, 9914, 9915, 16157, 16160}) {
    EXIT_DATA *e = get_room_index(n)->exit[DIR_UP];
    assert(e && e->wall == WALL_BRICK);
  }
  place(owner, 15641); walk(owner, DIR_WEST, 16156);
  ROOM_INDEX_DATA *entry = owner->in_room;
  assert(entry->sector_type == SECT_HOUSE && IS_SET(entry->room_flags, ROOM_INDOORS));
  assert(entry->z == 0 && strstr(entry->name, "Entrance"));
  for (int d = 0; d < MAX_DIR; ++d) {
    if (d != DIR_EAST && d != DIR_UP && entry->exit[d]) assert(entry->exit[d]->wall == WALL_BRICK);
  }
  walk(owner, DIR_UP, 3347);
  assert(owner->in_room->z == 1 && owner->in_room->sector_type == SECT_HOUSE);
  walk(owner, DIR_SOUTHWEST, 8996); walk(owner, DIR_UP, 9431); walk(owner, DIR_UP, 9378);
  assert(owner->in_room->sector_type == SECT_ROOFTOP);
  walk(owner, DIR_DOWN, 9431);
  place(owner, 1597); walk(owner, DIR_NORTH, 9664); walk(owner, DIR_SOUTH, 1597);
  place(owner, 9769); walk(owner, DIR_UP, 1998); walk(owner, DIR_WEST, 9782);
  assert(owner->in_room->sector_type != SECT_AIR);
  place(owner, 3900); walk(owner, DIR_EAST, 1490); walk(owner, DIR_WEST, 3900);
  const int restored[][3] = {{1494,2,9384}, {1494,0,2387}, {9597,2,9391},
    {3871,3,9592}, {9610,3,9609}, {9612,3,9611}, {2399,1,16164}, {16299,1,16298},
    {9757,2,9796}};
  for (auto &route : restored) {
    place(owner, route[0]); walk(owner, route[1], route[2]); walk(owner, rev_dir[route[1]], route[0]);
  }
  // Enclosed air above the biodome and actual swimming water are preserved.
  assert(get_room_index(3419)->sector_type == SECT_AIR);
  assert(IS_SET(get_room_index(3419)->room_flags, ROOM_INDOORS));
  assert(get_room_index(4921)->sector_type == SECT_SHALLOW);
  assert(get_room_index(4934)->sector_type == SECT_WATER);
  assert(get_room_index(4948)->sector_type == SECT_UNDERWATER);
  puts("PASS: bounded nexus entrance, Rook rooftop hatch, biodome entrance, play platforms, office and nine restored interiors");
}
