#!/usr/bin/env python3
"""Exercise production combat movement and aliases under ASan/UBSan (Linux/WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
fight = (ROOT / 'src/fight.c').read_text()


def section(start, end):
    offset = fight.index(start)
    return fight[offset:fight.index(end, offset)]


source = r'''
#include "merc.h"
#include <cassert>
#include <climits>
#include <cstring>
#include <cstdlib>
#include <cstdarg>
#include <cmath>
CHAR_DATA actor = {}, target = {}, monster = {}, protected_person = {};
PC_DATA pc = {};
ROOM_INDEX_DATA room = {}, destination = {};
std::string output, forwarded;
bool fighting = true, gm = false, fistfighting = false, capture_forwarding = false;
int moves = 0, toward_x = 0, toward_y = 0, speed = 0, speed_calls = 0;
int fatigue_during_move = 0;
CHAR_DATA *protection_during_move = nullptr;
int reports = 0;
DO_FUN *forwarded_function = nullptr;
bool has_exit(ROOM_INDEX_DATA *, int);
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool is_number(char *s) {
  if (*s == '+' || *s == '-') ++s;
  if (!*s) return false;
  for (; *s; ++s) if (*s < '0' || *s > '9') return false;
  return true;
}
char *one_argument_nouncap(char *s, char *word) {
  while (*s == ' ') ++s;
  while (*s && *s != ' ') *word++ = *s++;
  *word = '\0'; while (*s == ' ') ++s; return s;
}
char *str_dup(const char *s) { return strdup(s); }
void free_string(char *s) { free(s); }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void printf_to_char(CHAR_DATA *, const char *format, ...) {
  char buffer[MSL]; va_list args; va_start(args, format);
  vsnprintf(buffer, sizeof(buffer), format, args); va_end(args); output += buffer;
}
void act_new(const char *, CHAR_DATA *, const void *, const void *, int, int) {}
bool is_gm(CHAR_DATA *) { return gm; }
bool in_fight(CHAR_DATA *) { return fighting; }
bool in_fistfight(CHAR_DATA *) { return fistfighting; }
bool is_helpless(CHAR_DATA *) { return false; }
bool is_attacking(CHAR_DATA *) { return false; }
bool is_animal(CHAR_DATA *) { return false; }
bool guestmonster(CHAR_DATA *) { return false; }
int animal_size(int) { return ANIMAL_SMALL; }
int get_animal_weight(CHAR_DATA *, int) { return 10; }
bool wearing_armor(CHAR_DATA *) { return false; }
bool has_shield(CHAR_DATA *) { return false; }
bool deep_water(CHAR_DATA *) { return false; }
bool airborne(CHAR_DATA *) { return false; }
bool has_caff(CHAR_DATA *ch, int aff) {
  for (int i = 0; i < 30; ++i) if (ch->caff[i] == aff && ch->caff_duration[i] > 0) return true;
  return false;
}
void remove_caff(CHAR_DATA *, int) {}
void apply_caff(CHAR_DATA *, int, int) {}
int get_skill(CHAR_DATA *ch, int skill) { return ch->skills[skill]; }
int get_speed(CHAR_DATA *) { ++speed_calls; return 10; }
OBJ_DATA *get_eqr_char(CHAR_DATA *, int) { return nullptr; }
CHAR_DATA *get_char_fight(CHAR_DATA *, char *name) { return !str_cmp(name, "Target") ? &target : nullptr; }
int relative_x(CHAR_DATA *ch, ROOM_INDEX_DATA *, int x) { return x - ch->x; }
int relative_y(CHAR_DATA *ch, ROOM_INDEX_DATA *, int y) { return y - ch->y; }
int get_dist(int x, int y, int a, int b) { return static_cast<int>(std::hypot(x-a, y-b)); }
int combat_distance(CHAR_DATA *, CHAR_DATA *, bool) { return 10; }
bool same_fight(CHAR_DATA *, CHAR_DATA *) { return true; }
void move_towards(CHAR_DATA *ch, int x, int y, int dist, int, bool) {
  ++moves; toward_x = x; toward_y = y; speed = dist;
  if (!IS_NPC(ch) && ch->pcdata) {
    fatigue_during_move = ch->pcdata->fatigue;
    protection_during_move = ch->pcdata->protecting;
  }
}
void move_away(CHAR_DATA *ch, int x, int y, int dist, int z, bool voluntary) {
  move_towards(ch, -x, -y, dist, z, voluntary);
}
void move_message(CHAR_DATA *, int, int, int, ROOM_INDEX_DATA *) {}
bool will_fight_show(CHAR_DATA *, bool) { return false; }
bool open_sound(ROOM_INDEX_DATA *, int) { return true; }
bool can_get_to(CHAR_DATA *, ROOM_INDEX_DATA *) { return true; }
void char_from_room(CHAR_DATA *ch) { ch->in_room = nullptr; }
void char_to_room(CHAR_DATA *ch, ROOM_INDEX_DATA *room) { ch->in_room = room; }
bool battleground(ROOM_INDEX_DATA *) { return false; }
bool get_poi_target(CHAR_DATA *, int, int *, int *) { return false; }
void op_report(char *s, CHAR_DATA *) { ++reports; free(s); }
void useattack(CHAR_DATA *) {}
void fleeroom(CHAR_DATA *) {}
bool fight_over(ROOM_INDEX_DATA *) { return false; }
void end_fight(ROOM_INDEX_DATA *) {}
void next_attacker(CHAR_DATA *, bool) {}
void do_look(CHAR_DATA *, char *) {}
void do_hangup(CHAR_DATA *, char *) {}
void do_knock(CHAR_DATA *, char *) {}
void do_attack(CHAR_DATA *, char *) {}
void do_function(CHAR_DATA *ch, DO_FUN *function, char *argument) {
  if (capture_forwarding) { forwarded = argument; forwarded_function = function; }
  else function(ch, argument);
}
'''
source += next(line for line in fight.splitlines() if line.startswith('#define MOVE_FATIGUE')) + '\n'
source += section('  int get_exit_x(', '  char *special_name(')
source += section('  _DOFUN(do_knockout)', '  int GET_NPC_SPECIAL(')
source += r'''
void reset() {
  free(actor.qmove); free(monster.qmove);
  actor = {}; target = {}; monster = {}; protected_person = {}; pc = {};
  room = {}; destination = {};
  actor.pcdata = &pc; actor.name = (char *)"Actor";
  actor.in_room = target.in_room = monster.in_room = &room;
  actor.fight_current = &actor; actor.fight_fast = true;
  actor.x = 5; actor.y = 7; target.x = 45; target.y = 82;
  room.size = destination.size = 100;
  pc.protecting = &protected_person; pc.fatigue = 50;
  fighting = true; gm = fistfighting = capture_forwarding = false;
  moves = speed_calls = reports = 0; output.clear(); forwarded.clear();
}
void command(DO_FUN *function, const char *input) {
  std::string argument = input; function(&actor, argument.data());
}
void assert_rejected(const char *input) {
  reset(); command(do_move, input);
  assert(moves == 0 && pc.fatigue == 50 && pc.protecting == &protected_person);
  assert(!output.empty());
}
int main() {
  // Approach must use both target coordinates, including when x != y.
  reset(); command(do_move, "Target 6");
  assert(moves == 1 && toward_x == 40 && toward_y == 75 && speed == 6);
  assert(pc.fatigue == 50 + MOVE_FATIGUE && pc.protecting == nullptr);
  assert(fatigue_during_move == pc.fatigue && protection_during_move == nullptr);
  reset(); pc.fatigue = 1000 - MOVE_FATIGUE; command(do_move, "Target 6");
  assert(fatigue_during_move == 1000 && protection_during_move == nullptr);
  reset(); command(do_move, "-10 20");
  assert(moves == 1 && toward_x == -10 && toward_y == 20);
  for (const char *input : {"", "bogus", "10", "10 bogus", "bogus 10", "Target bogus",
       "Target 0", "Target -1", "up", "down", "capture", "extract", "Target path",
       "2147483648 0", "0 -2147483649", "999999999999999999999999 1",
       "Target 2147483648", "Target retreat -1", "Target retreat 0",
       "Target retreat 3oops", "Target retreat 99999999999999999999999"})
    assert_rejected(input);
  reset(); command(do_move, "2147483647 -2147483648");
  assert(moves == 1 && toward_x == INT_MAX && toward_y == INT_MIN);
  reset(); command(do_move, "Target retreat 3");
  assert(moves == 1 && speed == 3);
  reset(); actor.facing = DIR_UP; command(do_move, "sprint");
  assert(moves == 0 && pc.fatigue == 50 && pc.protecting == &protected_person);
  reset(); command(do_move, "Target protect");
  assert(moves == 1 && pc.protecting == &target && pc.fatigue == 50 + MOVE_FATIGUE);
  assert(fatigue_during_move == pc.fatigue && protection_during_move == nullptr);
  reset(); command(do_move, "Target jump"); // Untrained jump falls back to charge.
  assert(moves == 1 && pc.fatigue == 50 + MOVE_FATIGUE && pc.protecting == nullptr);
  assert(fatigue_during_move == pc.fatigue && protection_during_move == nullptr);
  reset(); actor.skills[SKILL_SUPERJUMP] = 1; command(do_move, "Target jump");
  assert(moves == 1 && pc.fatigue == 50 + MOVE_FATIGUE);
  reset(); actor.fight_fast = false; command(do_move, "Target 3");
  assert(moves == 1 && actor.moving && actor.actiontimer == 120);
  command(do_move, "Target 3");
  assert(moves == 1 && pc.fatigue == 50 + MOVE_FATIGUE);
  reset(); actor.move_timer = 5; command(do_move, "Target protect");
  assert(moves == 0 && std::string(actor.qmove) == "Target protect");
  assert(pc.protecting == &protected_person && pc.fatigue == 50);
  reset(); fighting = false; command(do_move, "12 -7");
  assert(moves == 1 && pc.fatigue == 50 && pc.protecting == &protected_person);
  // GM movement must reject a coordinate pair with either component missing.
  for (const char *input : {"10", "10 bogus", "bogus 10", "2147483648 0", "0 -2147483649",
       "Target 0", "Target -1", "Target 2147483648"}) {
    reset(); gm = true; actor.fight_current = &monster; monster.controled_by = &actor;
    command(do_gmmove, input); assert(moves == 0 && !monster.moving);
  }
  reset(); gm = true; actor.fight_current = &monster; monster.controled_by = &actor;
  command(do_gmmove, "10 -20"); assert(moves == 1 && toward_y == -20);
  for (const char *input : {"2147483648 0", "0 -2147483649", "99999999999999999999999 1"}) {
    reset(); fighting = false; command(do_move, input);
    assert(moves == 0 && actor.wait == 0 && pc.fatigue == 50);
  }
  // Every physical exit, especially direction 9 (southeast), is considered.
  for (int direction = 0; direction < MAX_DIR; ++direction) {
    reset(); EXIT_DATA exit = {}; exit.u1.to_room = &destination;
    room.exit[direction] = &exit;
    actor.x = get_exit_x(direction, &room); actor.y = get_exit_y(direction, &room);
    assert(on_roomexit(&actor) && get_flee_direction(&actor) == direction);
    assert(closest_exit_x(&actor, &room) == actor.x);
    assert(closest_exit_y(&actor, &room) == actor.y);
  }
  reset(); EXIT_DATA exit = {}; exit.u1.to_room = &room;
  destination.exit[DIR_NORTHEAST] = &exit;
  assert(closest_exit_x(&actor, &destination) == 100);
  assert(closest_exit_y(&actor, &destination) == 100);
  assert(!on_roomexit(&actor) && get_flee_direction(&actor) == -1);
  // Reuse the same base speed without changing unencumbered movement values.
  const int kinds[] = {MOVE_MOVE, MOVE_FLEE, MOVE_CHARGE, MOVE_JUMP, MOVE_PROTECT};
  const int expected[] = {10, 41, 22, 34, 25};
  for (int i = 0; i < 5; ++i) {
    reset(); assert(combat_move_speed(&actor, kinds[i]) == expected[i]);
    assert(speed_calls == 1);
  }
  // Legal input can be far longer than the aliases' former 200-byte buffers.
  DO_FUN *aliases[] = {do_charge, do_protect, do_jump, do_retreat, do_knockout};
  const char *suffixes[] = {" charge", " protect", " jump", " retreat", " knockout"};
  for (size_t length : {size_t(0), size_t(12), size_t(195), size_t(MAX_INPUT_LENGTH - 1)}) {
    for (int i = 0; i < 5; ++i) {
      reset(); capture_forwarding = true; std::string input(length, 'a');
      command(aliases[i], input.c_str());
      assert(forwarded == input + suffixes[i]);
      assert(forwarded_function == (i == 4 ? do_attack : do_move));
    }
  }
  reset(); fighting = false; capture_forwarding = true; command(do_knockout, "door");
  assert(forwarded == "door" && forwarded_function == do_knock);
  reset(); fighting = false; fistfighting = true; command(do_retreat, "");
  assert(actor.fistattack == FIST_RETREAT && actor.fisttimer == 15);
  reset();
  puts("PASS: combat coordinates, rejected moves, fatigue, protection, aliases, exits and speed reuse");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-combat-commands-') as temporary:
    path = Path(temporary)
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
