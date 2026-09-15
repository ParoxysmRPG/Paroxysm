#!/usr/bin/env python3
"""Test real operation resolution in a disposable world after make -C src.

The full engine is linked so command-test stubs cannot hide completion bugs.
Run under Linux/WSL; live world and player files are never changed.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "src/.build-local/release-sanitize0"
SOURCE = r'''
#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>
extern "C" {
extern char str_boot_time[];
extern bool isactiveoperation;
void win_operation(int, OPERATION_TYPE *);
void do_operation(CHAR_DATA *, char *);
void launch_operation(OPERATION_TYPE *);
void pc_update(CHAR_DATA *, int);
bool can_deploy(CHAR_DATA *, OPERATION_TYPE *, int);
bool try_deploy(CHAR_DATA *, OPERATION_TYPE *, int, STORYLINE_TYPE *, int, int, int, int, int, int);
CHAR_DATA *get_patroller(CHAR_DATA *);
ROOM_INDEX_DATA *first_battleroom(int);
void prp_rplog(CHAR_DATA *, char *);
extern int battle_factions[6];
}
static OPERATION_TYPE *operation(FACTION_TYPE *host) {
  auto *op = new_operation();
  op->faction = host->vnum; op->territoryvnum = 1;
  op->hour = 12; op->day = 2; op->goal = GOAL_CONTROL;
  op->competition = COMPETE_OPEN; op->max_pcs = 5; op->speed = 3;
  return op;
}
int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  auto *host = new_faction();
  host->vnum = 990121; host->type = FACTION_SOCIETY;
  host->alliance = ALLIANCE_SIDELEFT; host->resource = 100000;
  host->manpower = 20;
  free_string(host->name); host->name = str_dup("Operationtesters");
  FacVect.push_back(host);
  auto *actor = new_char(); actor->pcdata = new_pcdata();
  free_string(actor->name); actor->name = str_dup("Operationtester");
  actor->level = MAX_LEVEL; actor->faction = host->vnum;
  auto *op = operation(host); op->home_soldiers = 4;
  OpVect.clear(); OpVect.push_back(op);
  activeoperation = nullptr; isactiveoperation = false;
  char bribe[] = "bribe 1";
  do_operation(actor, bribe);
  assert(op->hour == 0 && host->manpower == 24 && host->operation_wins == 1);
  const auto resources = host->resource;
  assert(resources < 100000);
  char repeat[] = "bribe 1";
  do_operation(actor, repeat);
  assert(host->resource == resources && host->manpower == 24 && host->operation_wins == 1);
  puts("PASS: a bribed operation retires; repeated commands cannot charge or refund it again.");

  auto *unrelated = operation(host); unrelated->hour = 15;
  activeoperation = unrelated; isactiveoperation = false;
  auto *pending = operation(host);
  win_operation(host->vnum, pending);
  assert(pending->hour == 0 && unrelated->hour == 15);
  assert(activeoperation == unrelated && !isactiveoperation);
  isactiveoperation = true;
  pending = operation(host);
  win_operation(host->vnum, pending);
  assert(pending->hour == 0 && unrelated->hour == 15 && isactiveoperation);
  puts("PASS: explicit operation resolution retires its argument without altering another operation.");

  activeoperation = operation(host); isactiveoperation = true;
  win_operation(host->vnum, nullptr);
  assert(activeoperation->hour == 0 && !isactiveoperation);
  puts("PASS: battlefield victory still retires the active operation and clears battle state.");

  activeoperation = operation(host); activeoperation->goal = GOAL_PSYCHIC;
  isactiveoperation = true;
  win_operation(200000, nullptr);
  assert(activeoperation->hour == 0 && !isactiveoperation);
  puts("PASS: psychic defense victory retires its operation and clears battle state.");

  activeoperation = operation(host); activeoperation->goal = GOAL_PSYCHIC;
  free_string(activeoperation->target);
  activeoperation->target = str_dup("Absentpsychictarget");
  isactiveoperation = true;
  win_operation(300000, nullptr);
  assert(activeoperation->hour == 0 && !isactiveoperation);
  puts("PASS: psychic attack victory retires even if the offline target no longer exists.");

  auto assign = [](char *&field, const char *value) {
    free_string(field); field = str_dup(value);
  };
  auto player = [&](const char *name) {
    auto *ch = new_char(); ch->pcdata = new_pcdata();
    assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
    ch->level = 2; ch->race = RACE_HUMAN; ch->position = POS_STANDING;
    ch->faction = ch->fsociety = host->vnum; ch->deploy_society = 1;
    ch->factiontrue = -1;
    char_to_room(ch, get_room_index(16068)); char_list.push_front(ch);
    ch->desc = new_descriptor(); ch->desc->character = ch;
    ch->desc->connected = CON_PLAYING; descriptor_list.push_back(ch->desc);
    return ch;
  };
  auto *member = player("Deploymenttester");
  auto *opponent = player("Deploymentopponent");
  auto *ally = new_faction(); ally->vnum = 990122; ally->type = FACTION_SOCIETY;
  ally->alliance = host->alliance; assign(ally->name, "Allytesters"); FacVect.push_back(ally);
  assign(host->member_names[0], member->name); assign(ally->member_names[0], member->name);
  member->legacy_society = ally->vnum; member->deploy_legacy_society = 1;
  member->faction = ally->vnum;
  auto *testop = operation(host); testop->terrain = BATTLE_FIELD;
  testop->type = OPERATION_CAPTURE; testop->max_pcs = 1;
  assign(testop->sign_up[0], member->name); assign(testop->sign_up[1], opponent->name);
  member->wounds = 2; assert(!can_deploy(member, testop, 0));
  SET_FLAG(member->act, PLR_DEAD); assert(!can_deploy(member, testop, 0));
  REMOVE_FLAG(member->act, PLR_DEAD);
  member->wounds = 1; member->heal_timer = 23456;
  opponent->wounds = 3;
  activeoperation = nullptr; isactiveoperation = false;
  const auto faction_order = FacVect;
  launch_operation(testop);
  assert(isactiveoperation && activeoperation == testop && battleground(member->in_room));
  assert(!battleground(opponent->in_room) && opponent->wounds == 3);
  assert(member->faction == host->vnum && member->factiontrue == ally->vnum);
  assert(testop->deployed_faction[0] == ally->vnum && testop->deployed_team[0] == host->vnum);
  assert(member->wounds == 1 && member->heal_timer == 23456 && !can_heal(member));
  assert(FacVect == faction_order);
  puts("PASS: real launch honors selected allied society, blocks severe/dead-severe wounds, and preserves a preexisting mild wound.");

  opponent->wounds = 0;
  assign(testop->sign_up[1], opponent->name);
  // An exhausted team slot must not change an unsuccessful player's identity.
  host->deployed_super = 1; host->deployed_nosuper = 1;
  const int before_faction = opponent->faction;
  assert(!try_deploy(opponent, testop, host->vnum, nullptr, 3, 0, 2, 250, testop->battleground_number, -1));
  assert(opponent->faction == before_faction && opponent->factiontrue == -1);
  assert(!opponent->pcdata->recovery->operation_active);

  CHAR_DATA *mob = nullptr;
  for (CHAR_DATA *candidate : char_list) {
    if (IS_NPC(candidate) && battleground(candidate->in_room) && !is_cover(candidate)) { mob = candidate; break; }
  }
  assert(mob && !mob->pcdata);
  char_from_room(mob); char_to_room(mob, member->in_room);
  mob->x = member->x; mob->y = member->y; mob->hit = 1000;
  set_combat_state(member, true); member->fighting = true; member->attacking = 1;
  member->cfighting = mob; mob->cfighting = member;
  (void)get_patroller(mob); char_rplog(mob, "NPC log probe"); prp_rplog(mob, "NPC log probe");
  assert(get_patroller(nullptr) == nullptr); char_rplog(nullptr, "probe"); prp_rplog(nullptr, "probe");
  member->hit = 1;
  damage(member, mob, 1);
  assert(!battleground(member->in_room) && member->in_room->vnum == 16068);
  assert(!in_fight(member) && !member->fighting && member->attacking == 0);
  assert(member->cfighting == nullptr && mob->cfighting == nullptr);
  assert(member->faction == ally->vnum && member->factiontrue == -1);
  assert(member->wounds == 2 && member->heal_timer == 2300 && can_heal(member));
  assert(member->pcdata->recovery->operation_wound);
  // Persist the pending fast recovery before letting the actual update finish it.
  FILE *recovery_file = tmpfile(); assert(recovery_file);
  write_recovery(recovery_file, member); rewind(recovery_file);
  auto *loaded_recovery = new_char(); loaded_recovery->pcdata = new_pcdata();
  while (!feof(recovery_file)) {
    char *word = fread_word(recovery_file);
    if (!word || !*word) break;
    assert(read_recovery(recovery_file, loaded_recovery, word));
  }
  fclose(recovery_file);
  assert(loaded_recovery->pcdata->recovery->operation_wound);
  assert(loaded_recovery->pcdata->recovery->operation_saved_wounds == 1);
  assert(loaded_recovery->pcdata->recovery->operation_saved_heal_timer == 23456);
  *loaded_recovery->pcdata->recovery = RecoveryState();
  loaded_recovery->pcdata->recovery->operation_dead = true;
  loaded_recovery->wounds = 2; loaded_recovery->heal_timer = 9876;
  operation_recovery_return(loaded_recovery);
  assert(loaded_recovery->wounds == 2 && loaded_recovery->heal_timer == 9876);
  member->heal_timer = 1;
  pc_update(member, -1);
  assert(member->wounds == 1 && member->heal_timer == 23456 && !member->pcdata->recovery->operation_wound);
  puts("PASS: real NPC-to-PC 0 DF exits combat safely; only the new wound heals quickly, then the original timer resumes.");

  // Exercise the opposite direction using a new deployment with no old wound.
  member->wounds = 0; member->heal_timer = 0;
  host->deployed_super = host->deployed_nosuper = 0;
  assert(try_deploy(member, testop, ally->vnum, nullptr, 1, 0, 2, 250, testop->battleground_number, -1));
  char_from_room(mob); char_to_room(mob, member->in_room);
  mob->x = member->x; mob->y = member->y; mob->hit = 1;
  mob->wounds = 0; mob->cfighting = member; member->cfighting = mob;
  damage(mob, member, 1);
  assert(mob->in_room->vnum == 2 && mob->wounds == 4 && mob->ttl == 1);
  assert(!in_fight(mob) && member->cfighting == nullptr);
  puts("PASS: real PC-to-NPC 0 DF retires the NPC without player-only cleanup or dangling combat targets.");

  assign(ally->eidilon, member->name);
  save_char_obj(member, false, false);
  const int ally_resources = ally->resource;
  const int old_host_power = host->member_power[0], old_ally_power = ally->member_power[0];
  const int host_wins = host->operation_wins, ally_wins = ally->operation_wins;
  member->pcdata->op_emotes = 5;
  win_operation(host->vnum, nullptr);
  assert(host->operation_wins == host_wins + 1 && ally->operation_wins == ally_wins);
  assert(ally->resource > ally_resources);
  assert(host->member_power[0] == old_host_power && ally->member_power[0] > old_ally_power);
  assert(member->faction == host->vnum); // Rewards never rewrite live combat identity.
  end_battle();
  assert(!battleground(member->in_room) && !in_fight(member));
  assert(member->faction == ally->vnum && member->wounds == 0);
  win_operation(host->vnum, testop); assert(host->operation_wins == host_wins + 1);
  puts("PASS: winner is the battlefield team; membership awards go only to the recorded society, and resolution cannot repeat.");

  // A survivor with no new wound gets neither a reset nor an accelerated timer.
  member->wounds = 1; member->heal_timer = 19876;
  operation_recovery_wake(member);
  char_from_room(member); char_to_room(member, first_battleroom(testop->battleground_number));
  end_battle();
  assert(member->wounds == 1 && member->heal_timer == 19876);
  assert(!member->pcdata->recovery->operation_active && !member->pcdata->recovery->operation_wound);
  puts("PASS: finishing an operation without a new injury preserves a preexisting wound exactly.");

  FACTION_TYPE *core = clan_lookup(FACTION_CORTEX); assert(core);
  member->fcore = core->vnum;
  member->pcdata->intel = member->pcdata->pending_resources = 0;
  assign(host->eidilon, member->name);
  for (FACTION_TYPE *fac : {host, ally, core}) {
    fac->weekly_resources = 0; fac->last_high_intel = 0; fac->last_intel = current_time;
  }
  const int core_before = core->resource, host_before = host->resource, ally_before = ally->resource;
  gain_resources(100, host->vnum, member, "testing society contribution shares");
  assert(host->resource == host_before + 100);
  assert(core->resource == core_before + 40 && ally->resource == ally_before + 40);
  puts("PASS: primary-society resource sharing pays each secondary membership once, without duplicating the core share.");


}
'''

with tempfile.TemporaryDirectory(prefix="operation-lifecycle-") as temporary:
    scratch = Path(temporary)
    for name in ("area", "data", "accounts", "gods"):
        shutil.copytree(ROOT / name, scratch / name,
                        ignore=shutil.ignore_patterns("back[1-7]"))
    wilds = scratch / "area/wildfor.are"
    if not wilds.read_bytes().rstrip().endswith(b"#$"):
        shutil.copy2(ROOT / "area/back7/wildfor.are", wilds)
    (scratch / "log").mkdir()
    (scratch / "prp").mkdir()
    (scratch / "player").mkdir()
    comm = scratch / "comm-test.o"
    shutil.copy2(BUILD / "comm.o", comm)
    subprocess.run(["objcopy", "--redefine-sym", "main=operation_game_main", str(comm)], check=True)
    makefile = (ROOT / "src/Makefile").read_text()
    objects_text = re.search(r"^O_FILES\s*=\s*(.*?)(?=\n\n)", makefile, re.M | re.S)[1]
    objects = [str(BUILD / name) for name in re.findall(r"[\w-]+\.o\b", objects_text)
               if name != "comm.o"]
    cpp, binary = scratch / "test.cpp", scratch / "test"
    cpp.write_text(SOURCE)
    subprocess.run(["g++", "-g", "-Wno-deprecated", "-Wno-write-strings",
                    "-I" + str(ROOT / "src"), str(cpp), str(comm), *objects,
                    "-rdynamic", "-ldl", "-lcrypt", "-lcurl", "-o", str(binary)], check=True)
    result = subprocess.run([str(binary)], cwd=scratch / "area", stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace", timeout=120)
    (BUILD.parent / "operation-lifecycle-test.log").write_text(result.stdout)
    lines = result.stdout.splitlines()
    print("\n".join(lines[-50:] if result.returncode else
                    [line for line in lines if "PASS:" in line]))
    raise SystemExit(result.returncode)
