#!/usr/bin/env python3
"""Exercise warfare patrols against the full engine in a disposable world.

Run under Linux/WSL after make -C src. No live world or player files are changed.
--diagnose-staging demonstrates the legacy distance failure without asserting
the repaired behavior, and is useful when comparing an older engine build.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "src/.build-local/release-sanitize0"
SOURCE = r'''
#include "merc.h"
#include "recycle.h"
#include "olc.h"
#include <cassert>
#include <cstring>
#include <ctime>

extern "C" {
extern char str_boot_time[];
ROOM_INDEX_DATA *patrol_attack_room(CHAR_DATA *);
void do_patrol(CHAR_DATA *, char *);
void patrol_update(CHAR_DATA *);
bool check_fight(CHAR_DATA *);
bool is_enemy(CHAR_DATA *, CHAR_DATA *);
int init_combat_distance(CHAR_DATA *, CHAR_DATA *, bool);
bool free_to_act(CHAR_DATA *);
bool arcane_attackable(CHAR_DATA *);
bool patrol_attackable(CHAR_DATA *);
}

static void assign(char *&field, const char *value) {
  free_string(field); field = str_dup(value);
}
static ROOM_INDEX_DATA *room(int x, int size = 100) {
  static int next_vnum = 990700;
  auto *r = new_room_index();
  r->vnum = next_vnum++;
  r->area = get_room_index(4331)->area;
  r->x = x; r->y = 1000; r->z = 0; r->size = size;
  r->sector_type = SECT_STREET;
  assign(r->name, "Warfare regression street");
  const int hash = r->vnum % MAX_KEY_HASH;
  r->next = room_index_hash[hash]; room_index_hash[hash] = r;
  return r;
}
static void connect(ROOM_INDEX_DATA *a, ROOM_INDEX_DATA *b) {
  auto *forward = new_exit(); auto *back = new_exit();
  forward->u1.to_room = b; back->u1.to_room = a;
  forward->wall = back->wall = WALL_NONE;
  forward->exit_info = back->exit_info = 0;
  a->exit[DIR_EAST] = forward; b->exit[DIR_WEST] = back;
}
static CHAR_DATA *player(const char *name, ROOM_INDEX_DATA *r) {
  static int id = 890000;
  auto *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->race = RACE_HUMAN; ch->position = POS_STANDING;
  ch->id = ++id; ch->x = ch->y = 50;
  ch->pcdata->account = new_account();
  assign(ch->pcdata->account->name, name);
  ch->pcdata->spectre = 1; ch->pcdata->ghost_room = r->vnum;
  ch->pcdata->sleeping = 0;
  SET_FLAG(ch->act, PLR_SHROUD); SET_FLAG(ch->act, PLR_DEEPSHROUD);
  char_to_room(ch, r); char_list.push_front(ch); register_live_character(ch);
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->desc->connected = CON_PLAYING;
  descriptor_list.push_front(ch->desc);
  assert(!IS_NPC(ch) && !is_gm(ch) && !is_helpless(ch));
  return ch;
}
struct Encounter { CHAR_DATA *attacker, *defender; ROOM_INDEX_DATA *staging; };
static Encounter encounter() {
  static int offset = 1000;
  offset += 100;
  auto *home = room(offset);
  auto *previous = home;
  for (int i = 1; i <= 3; ++i) {
    auto *next = room(offset + i); connect(previous, next); previous = next;
  }
  auto *defender = player("Warfaredefender", home);
  auto *staging = patrol_attack_room(defender);
  auto *attacker = player("Warfareattacker", staging);
  attacker->pcdata->patrol_status = PATROL_ATTACKSEARCHING;
  defender->pcdata->patrol_status = PATROL_DEFENDHIDING;
  attacker->pcdata->patrol_timer = defender->pcdata->patrol_timer = 10;
  attacker->pcdata->patrol_target = defender;
  defender->pcdata->patrol_target = attacker;
  attacker->pcdata->patrol_room = staging;
  defender->pcdata->patrol_room = home;
  return {attacker, defender, staging};
}
static void command(CHAR_DATA *ch, const char *argument) {
  char text[MSL]; strcpy(text, argument); do_patrol(ch, text);
}
static void sustained_combat(const Encounter &e) {
  for (int tick = 0; tick < 3; ++tick) {
    assert(in_fight(e.attacker) && in_fight(e.defender));
    if (!check_fight(e.attacker) || !check_fight(e.defender))
      printf("DIAGNOSTIC: failed combat persistence distance=%d, enemy=%d/%d, attacking=%d/%d, positions=%d,%d/%d,%d, helpless=%d/%d, fight_problem=%d\n",
          init_combat_distance(e.attacker, e.defender, true),
          is_enemy(e.attacker, e.defender), is_enemy(e.defender, e.attacker),
          e.attacker->attacking, e.defender->attacking,
          e.attacker->x, e.attacker->y, e.defender->x, e.defender->y,
          is_helpless(e.attacker), is_helpless(e.defender), fight_problem);
    assert(check_fight(e.attacker) && check_fight(e.defender));
    set_combat_state(e.attacker, check_fight(e.attacker));
    set_combat_state(e.defender, check_fight(e.defender));
    patrol_update(e.attacker); patrol_update(e.defender);
    assert(e.attacker->pcdata->patrol_status == PATROL_WAGINGWAR);
    assert(e.defender->pcdata->patrol_status == PATROL_WAGINGWAR);
    assert(e.attacker->pcdata->spectre == 1 && e.defender->pcdata->spectre == 1);
  }
}
int main(int argc, char **argv) {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  if (argc > 1 && !strcmp(argv[1], "--diagnose-staging")) {
    auto e = encounter();
    e.attacker->pcdata->patrol_status = e.defender->pcdata->patrol_status = PATROL_WAGINGWAR;
    start_fight(e.attacker, e.defender);
    printf("DIAGNOSTIC: staging room offset=%d, combat distance=%d, initial combat=%d/%d, survives check_fight=%d/%d\n",
        e.attacker->in_room->x - e.defender->in_room->x,
        init_combat_distance(e.attacker, e.defender, true),
        in_fight(e.attacker), in_fight(e.defender), check_fight(e.attacker), check_fight(e.defender));
    return 0;
  }
  {
    auto e = encounter();
    // Teleports used to retain positions from a much larger origin room.
    e.attacker->x = e.attacker->y = 900;
    command(e.defender, "attack");
    sustained_combat(e);
    puts("PASS: defender attack remains in real combat despite stale attacker coordinates.");
  }
  for (int remaining : {1, 0}) {
    auto e = encounter();
    e.attacker->pcdata->patrol_timer = remaining;
    patrol_update(e.attacker);
    sustained_combat(e);
  }
  puts("PASS: both normal and already-expired search timers start sustained combat.");
  {
    auto e = encounter();
    // Existing encounters may still use the old, distant staging room.
    auto *distant = e.defender->in_room->exit[DIR_EAST]->u1.to_room
        ->exit[DIR_EAST]->u1.to_room->exit[DIR_EAST]->u1.to_room;
    char_from_room(e.attacker); char_to_room(e.attacker, distant);
    e.attacker->pcdata->patrol_room = distant;
    e.attacker->pcdata->patrol_timer = 1;
    assert(init_combat_distance(e.attacker, e.defender, true) >= 250);
    patrol_update(e.attacker);
    sustained_combat(e);
    puts("PASS: an encounter staged under the old room layout can still begin combat.");
  }
  {
    auto e = encounter();
    e.attacker->pcdata->patrol_timer = 1;
    e.defender->pcdata->sleeping = 5; // Real start_fight refuses this target.
    patrol_update(e.attacker);
    assert(!in_fight(e.attacker) && !in_fight(e.defender));
    assert(e.attacker->pcdata->patrol_status == PATROL_ATTACKSEARCHING);
    assert(e.defender->pcdata->patrol_status == PATROL_DEFENDHIDING);
    assert(e.attacker->pcdata->patrol_timer >= 1);
    e.defender->pcdata->sleeping = 0;
    patrol_update(e.attacker);
    sustained_combat(e);
    puts("PASS: a refused combat start preserves preparation and succeeds on retry.");
  }
  {
    auto e = encounter();
    command(e.defender, "attack");
    fight_problem = 1;
    patrol_update(e.attacker); patrol_update(e.defender);
    assert(e.attacker->pcdata->patrol_status == PATROL_WAGINGWAR);
    assert(e.defender->pcdata->patrol_status == PATROL_WAGINGWAR);
    fight_problem = 0;
    sustained_combat(e);
    puts("PASS: a temporary combat-engine suspension does not cancel warfare patrols.");
  }
  {
    auto e = encounter();
    command(e.attacker, "wait");
    for (int tick = 0; tick < 15; ++tick) {
      patrol_update(e.attacker); patrol_update(e.defender);
    }
    assert(e.attacker->pcdata->patrol_status == PATROL_ATTACKWAITING);
    assert(e.defender->pcdata->patrol_status == PATROL_DEFENDHIDING);
    assert(!in_fight(e.attacker) && !in_fight(e.defender));
    command(e.attacker, "search");
    e.attacker->pcdata->patrol_timer = 1;
    patrol_update(e.attacker);
    sustained_combat(e);
    puts("PASS: waiting pauses the encounter until searching resumes.");
  }
  {
    auto e = encounter();
    auto *assistant = player("Warfareassistant", e.staging);
    assistant->pcdata->patrol_status = PATROL_ATTACKASSISTING;
    assistant->pcdata->patrol_target = e.defender;
    assistant->pcdata->patrol_room = e.staging;
    assistant->x = assistant->y = 800;
    command(e.defender, "attack");
    assert(in_fight(assistant));
    assert(assistant->pcdata->patrol_status == PATROL_WAGINGWAR);
    sustained_combat(e);
    assert(check_fight(assistant));
    set_combat_state(assistant, check_fight(assistant));
    patrol_update(assistant);
    assert(assistant->pcdata->patrol_status == PATROL_WAGINGWAR);
    assert(is_enemy(assistant, e.defender));
    REMOVE_FLAG(e.attacker->act, PLR_SHROUD);
    REMOVE_FLAG(e.attacker->act, PLR_DEEPSHROUD);
    set_combat_state(e.attacker, FALSE);
    assert(check_fight(assistant) && check_fight(e.defender));
    puts("PASS: assistants with stale coordinates join and remain in the actual fight.");
  }
  for (int side : {PATROL_WARMOVINGATTACK, PATROL_WARMOVINGDEFEND}) {
    auto e = encounter();
    auto *opponent = side == PATROL_WARMOVINGATTACK ? e.defender : e.attacker;
    auto *origin = get_room_index(4331);
    auto *joiner = player("Warfarejoiner", origin);
    auto *follower = player("Warfarefollower", origin);
    follower->master = joiner;
    joiner->pcdata->patrol_status = side;
    joiner->pcdata->patrol_timer = 3;
    joiner->pcdata->patrol_target = opponent;
    joiner->pcdata->patrol_room = opponent->in_room;
    assert(free_to_act(joiner) && can_shroud(joiner));
    command(joiner, "engage");
    const int assisting = side == PATROL_WARMOVINGATTACK
        ? PATROL_ATTACKASSISTING : PATROL_DEFENDASSISTING;
    for (auto *participant : {joiner, follower}) {
      assert(participant->pcdata->patrol_status == assisting);
      assert(participant->pcdata->patrol_target == opponent);
      assert(participant->in_room == opponent->in_room);
      command(participant, "");
      assert(participant->pcdata->patrol_status == assisting);
    }
    command(e.defender, "attack");
    sustained_combat(e);
    for (auto *participant : {joiner, follower}) {
      assert(in_fight(participant) && check_fight(participant));
      assert(participant->pcdata->patrol_status == PATROL_WAGINGWAR);
    }
  }
  puts("PASS: both sides can engage with followers, preserving opponent links and immediate combat protection.");
  for (int side : {PATROL_WARMOVINGATTACK, PATROL_WARMOVINGDEFEND}) {
    auto e = encounter();
    command(e.defender, "attack");
    auto *joiner = player("Warfarelatejoiner", get_room_index(4331));
    auto *opponent = side == PATROL_WARMOVINGATTACK ? e.defender : e.attacker;
    joiner->pcdata->patrol_status = side;
    joiner->pcdata->patrol_timer = 3;
    joiner->pcdata->patrol_target = opponent;
    joiner->pcdata->patrol_room = opponent->in_room;
    command(joiner, "engage");
    assert(in_fight(joiner) && check_fight(joiner));
    assert(joiner->pcdata->patrol_status == PATROL_WAGINGWAR);
    sustained_combat(e);
  }
  puts("PASS: late reinforcements immediately join combat on either side.");
  for (bool expired : {false, true}) {
    auto e = encounter();
    auto *origin = get_room_index(4331);
    auto *joiner = player("Warfareexpiredjoiner", origin);
    joiner->pcdata->patrol_status = PATROL_WARMOVINGATTACK;
    joiner->pcdata->patrol_timer = expired ? 0 : 3;
    joiner->pcdata->patrol_target = expired ? e.defender : nullptr;
    joiner->pcdata->patrol_room = e.defender->in_room;
    command(joiner, "engage");
    assert(joiner->in_room == origin && !in_fight(joiner));
    assert(joiner->pcdata->patrol_status == 0);
    assert(joiner->pcdata->patrol_target == nullptr && joiner->pcdata->patrol_room == nullptr);
  }
  puts("PASS: expired and invalid invitations cancel without teleporting the player.");
  {
    auto e = encounter();
    auto *assistant = player("Warfareorphanassistant", e.staging);
    assistant->pcdata->patrol_status = PATROL_ATTACKASSISTING;
    assistant->pcdata->patrol_target = e.defender;
    assistant->pcdata->patrol_room = e.staging;
    e.defender->pcdata->patrol_target = nullptr;
    patrol_update(assistant);
    assert(assistant->pcdata->patrol_status == 0);
    assert(assistant->pcdata->patrol_target == nullptr && assistant->pcdata->patrol_room == nullptr);
    puts("PASS: preparing assistants cancel when the paired encounter disappears.");
  }
  {
    auto *street = room(5); street->y = 5;
    auto *exit = room(6); exit->y = 5; connect(street, exit);
    auto *candidate = player("Warfarecandidate", street);
    candidate->pcdata->spectre = 0;
    candidate->pcdata->availability = AVAIL_HIGH;
    REMOVE_FLAG(candidate->act, PLR_SHROUD); REMOVE_FLAG(candidate->act, PLR_DEEPSHROUD);
    auto *clothes = create_object(get_obj_index(OBJ_VNUM_DUMMY), 0);
    clothes->item_type = ITEM_CLOTHING; clothes->extra_flags = 0;
    clothes->value[0] = COVERS_GROIN; clothes->value[4] = 0;
    obj_to_char(clothes, candidate); clothes->wear_loc = WEAR_BODY_1;
    if (!arcane_attackable(candidate) || !patrol_attackable(candidate))
      printf("DIAGNOSTIC: eligible candidate arcane=%d warfare=%d free=%d covered=%d haven=%d institute=%d availability=%d\n",
          arcane_attackable(candidate), patrol_attackable(candidate), free_to_act(candidate),
          is_covered(candidate, COVERS_GROIN), in_haven(street), institute_room(street), candidate->pcdata->availability);
    assert(arcane_attackable(candidate) && patrol_attackable(candidate));
    candidate->pcdata->patrol_status = PATROL_DEFENDHIDING;
    assert(!arcane_attackable(candidate) && !patrol_attackable(candidate));
    candidate->pcdata->patrol_status = 0; candidate->pcdata->spectre = 1;
    assert(!arcane_attackable(candidate) && !patrol_attackable(candidate));
    puts("PASS: an otherwise eligible target is excluded while in a patrol or projected as a spectre.");
  }
  {
    auto e = encounter();
    e.attacker->pcdata->patrol_timer = 0;
    e.attacker->pcdata->patrol_target = nullptr;
    patrol_update(e.attacker);
    assert(e.attacker->pcdata->patrol_status == 0);
    assert(e.attacker->pcdata->patrol_timer == 0);
    assert(e.attacker->pcdata->patrol_target == nullptr);
    command(e.defender, "attack");
    assert(e.defender->pcdata->patrol_status == 0);
    assert(e.defender->pcdata->patrol_target == nullptr);
    puts("PASS: missing and no-longer-participating opponents cancel cleanly.");
  }
  {
    auto e = encounter();
    command(e.defender, "attack");
    e.attacker->pcdata->patrol_timer = 0;
    command(e.attacker, "");
    assert(e.attacker->pcdata->patrol_status == PATROL_WAGINGWAR);
    sustained_combat(e);
    puts("PASS: the patrol toggle cannot clear a live warfare encounter.");
  }
}
'''

with tempfile.TemporaryDirectory(prefix="warfare-patrol-") as temporary:
    scratch = Path(temporary)
    for name in ("area", "data", "accounts", "gods"):
        shutil.copytree(ROOT / name, scratch / name,
                        ignore=shutil.ignore_patterns("back[1-7]"))
    (scratch / "log").mkdir()
    (scratch / "player").mkdir()
    comm = scratch / "comm-test.o"
    shutil.copy2(BUILD / "comm.o", comm)
    subprocess.run(["objcopy", "--redefine-sym", "main=warfare_game_main", str(comm)], check=True)
    makefile = (ROOT / "src/Makefile").read_text()
    objects_text = re.search(r"^O_FILES\s*=\s*(.*?)(?=\n\n)", makefile, re.M | re.S)[1]
    objects = [str(BUILD / name) for name in re.findall(r"[\w-]+\.o\b", objects_text)
               if name != "comm.o"]
    cpp, binary = scratch / "test.cpp", scratch / "test"
    cpp.write_text(SOURCE)
    subprocess.run(["g++", "-g", "-Wno-deprecated", "-Wno-write-strings",
                    "-I" + str(ROOT / "src"), str(cpp), str(comm), *objects,
                    "-rdynamic", "-ldl", "-lcrypt", "-lcurl", "-o", str(binary)], check=True)
    result = subprocess.run([str(binary), *sys.argv[1:]], cwd=scratch / "area",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors="replace", timeout=120)
    (BUILD.parent / "warfare-patrol-test.log").write_text(result.stdout)
    lines = result.stdout.splitlines()
    print("\n".join(lines[-60:] if result.returncode else
                    [line for line in lines if "PASS:" in line or "DIAGNOSTIC:" in line]))
    raise SystemExit(result.returncode)
