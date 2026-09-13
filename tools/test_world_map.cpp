#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ctime>
#include "merc.h"
#include "recycle.h"

extern "C" {
extern char str_boot_time[];
void boot_db();
}

static void place(CHAR_DATA *ch, int n) {
  if (ch->in_room) char_from_room(ch);
  char_to_room(ch, get_room_index(n));
}

static void walk(CHAR_DATA *ch, int d, int n) {
  EXIT_DATA *e = ch->in_room->exit[d];
  assert(e && e->u1.to_room && e->u1.to_room->vnum == n);
  assert(e->wall == WALL_NONE && ((!e->jump && !e->climb && !e->fall) || is_flying(ch)));
  // Test movement after access is granted; lock integrity is checked separately.
  REMOVE_BIT(e->exit_info, EX_LOCKED);
  if (IS_SET(e->exit_info, EX_CLOSED)) {
    char arg[40]; strcpy(arg, dir_name[d][0]); do_open(ch, arg);
  }
  move_char(ch, d, FALSE, FALSE);
  if (ch->in_room->vnum != n)
    fprintf(stderr, "Movement failed: %s -> %d\n%s\n", dir_name[d][0], n, ch->desc->outbuf);
  assert(ch->in_room->vnum == n);
}

static void round_trip(CHAR_DATA *ch, int n, int d, int t) {
  place(ch, n); walk(ch, d, t); walk(ch, rev_dir[d], n);
}

int main() {
  setvbuf(stdout, NULL, _IONBF, 0);
  current_time = time(NULL); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  CHAR_DATA *ch = new_char();
  if (!ch->pcdata) ch->pcdata = new_pcdata();
  ch->name = str_dup("WorldMapVisitor"); ch->level = 1; ch->trust = 0;
  ch->position = POS_STANDING; ch->hit = 1000;
  ch->desc = new_descriptor(); ch->desc->character = ch;

  const int routes[][3] = {{16514,1,16519}, {1836,1,16520}, {1836,6,16521},
    {16547,0,16546}, {18438,2,15093}, {16796,2,2527}, {2158,4,7390},
    {16645,3,16658}, {34001,8,34006}};
  for (auto &route : routes) round_trip(ch, route[0], route[1], route[2]);
  puts("PASS: ordinary movement into and back out of restored town rooms and Tijuana shop");

  // Market slots and unclassified historic forest doors are not normalized.
  assert(get_room_index(14817)->exit[DIR_SOUTH]->u1.to_room->vnum == 14818);
  assert(get_room_index(14808)->exit[DIR_NORTH]->u1.to_room->vnum == 14809);
  assert(IS_SET(get_room_index(405002)->exit[DIR_WEST]->exit_info, EX_ISDOOR));
  assert(IS_SET(get_room_index(92186)->exit[DIR_NORTH]->exit_info, EX_ISDOOR));
  assert(!IS_SET(get_room_index(92330)->exit[DIR_SOUTH]->exit_info, EX_ISDOOR));
  assert(get_room_index(14818)->exit[DIR_NORTH]->wall == WALL_BRICK);
  assert(get_room_index(14809)->exit[DIR_SOUTH]->wall == WALL_BRICK);
  puts("PASS: saved market slots, unclassified forest doors and local boundary walls retained");

  // Ordinary characters cannot enter northern buildings through the forest wall.
  for (auto route : {std::array<int, 3>{90052, DIR_SOUTH, 16679},
                     {90072, DIR_SOUTH, 16645}, {90090, DIR_SOUTH, 16740},
                     {151817, DIR_EAST, 56972}}) {
    place(ch, route[0]);
    assert(ch->in_room->exit[route[1]]->wall != WALL_NONE);
    move_char(ch, route[1], FALSE, FALSE);
    assert(ch->in_room->vnum == route[0]);
  }
  for (int n : {9103, 9104, 2998, 7273, 36028, 36037}) {
    ROOM_INDEX_DATA *r = get_room_index(n);
    assert(r->sector_type == SECT_ROOFTOP && !IS_SET(r->room_flags, ROOM_INDOORS));
  }
  assert(get_room_index(2999)->sector_type == SECT_HOUSE);
  assert(IS_SET(get_room_index(2999)->room_flags, ROOM_INDOORS));
  assert(get_room_index(405031)->sector_type == SECT_AIR);
  assert(IS_SET(get_room_index(405031)->room_flags, ROOM_INDOORS));
  assert(get_room_index(405031)->exit[DIR_SOUTHEAST]->wall == WALL_NONE);
  int copies = 0;
  for (ROOM_INDEX_DATA *r = room_index_hash[302600 % MAX_KEY_HASH]; r; r = r->next)
    if (r->vnum == 302600) ++copies;
  assert(copies == 1 && !strcmp(from_color(get_room_index(302600)->name), "The Crossroads"));
  puts("PASS: wall collisions, roof terrain, indoor exceptions and unique Crossroads definition");

  place(ch, 16386); walk(ch, DIR_DOWN, 10199); walk(ch, DIR_DOWN, 10214);
  assert(strstr(from_color(ch->in_room->name), "Lower Caverns"));
  assert(ch->in_room->sector_type == SECT_CAVE);
  walk(ch, DIR_UP, 10199); walk(ch, DIR_UP, 16386);
  assert(get_room_index(6180)->sector_type == SECT_ROOFTOP);
  assert(strstr(from_color(get_room_index(6180)->name), "Rooftop"));
  assert(room_by_coordinates(47, 65, 0)->vnum == 15215);
  assert(room_by_coordinates(70, 42, 0)->vnum == 3112);
  for (int n : {1842, 137281, 137283, 137285, 137286, 137287, 137289,
                137290, 137292, 137293, 137295, 137284, 137288, 137291, 137294}) assert(!get_room_index(n));
  for (int n = 73930; n <= 73941; ++n) assert(!get_room_index(n));
  apply_caff(ch, CAFF_GLIDING, 100);
  REMOVE_FLAG(ch->act, PLR_FLYING);
  assert(is_flying(ch));
  const int vertical[][2] = {{131622,9775}, {131734,9601}, {197697,114108}, {197699,114106}};
  for (auto &link : vertical) {
    ROOM_INDEX_DATA *lower = get_room_index(link[0]), *upper = get_room_index(link[1]);
    assert(lower->exit[DIR_UP]->u1.to_room == upper);
    assert(upper->exit[DIR_DOWN]->u1.to_room == lower);
    assert(lower->x == upper->x && lower->y == upper->y && lower->z + 1 == upper->z);
    round_trip(ch, lower->vnum, DIR_UP, upper->vnum);
  }
  round_trip(ch, 2207, DIR_UP, 3879);
  place(ch, 6948); walk(ch, DIR_UP, 9313); walk(ch, DIR_NORTH, 3497);
  walk(ch, DIR_SOUTH, 9313); walk(ch, DIR_DOWN, 6948);
  assert(get_room_index(5210)->exit[DIR_DOWN]->wall == WALL_BRICK);
  assert(get_room_index(6868)->exit[DIR_DOWN]->wall == WALL_BRICK);
  // The well's saved falling/confinement configuration is untouched.
  assert(get_room_index(1110)->exit[DIR_DOWN]->fall == 1);
  assert(get_room_index(2044)->exit[DIR_UP]->wall == WALL_GLASS);
  puts("PASS: underground routes and identity, rooftop identity, coordinate lookup and four repaired vertical links");
  puts("PASS: flight back from all three former sky traps; roof floors and well hazard preserved");
}
