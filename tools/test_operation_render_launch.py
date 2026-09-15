#!/usr/bin/env python3
"""Exercise real signup/assignment rules under ASan/UBSan without world writes."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
clans = (ROOT / "src/clans.c").read_text()
def section(start, end):
    a = clans.index(start)
    return clans[a:clans.index(end, a)]
source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <random>
#include <set>
#include <memory>
using std::vector;
vector<FACTION_TYPE *> FacVect;
std::map<std::string, CHAR_DATA *> online;
vector<char *> allocations;
int battle_factions[6] = {};
LOCATION_TYPE location = {};
char *str_dup(const char *s) { char *p = strdup(s ? s : ""); allocations.push_back(p); return p; }
void free_string(char *) {}
bool str_cmp(const char *a, const char *b) { return strcasecmp(a ? a : "", b ? b : "") != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void log_string(const char *) {}
CHAR_DATA *get_char_world_pc(char *name) {
  auto it = online.find(name); return it == online.end() ? nullptr : it->second;
}
FACTION_TYPE *clan_lookup(int id) {
  for (auto f : FacVect) if (id > 0 && f->vnum == id) return f;
  return nullptr;
}
bool same_alliance(FACTION_TYPE *a, FACTION_TYPE *b) {
  return a && b && a->type == b->type && (a == b || (a->alliance > 0 && a->alliance == b->alliance));
}
LOCATION_TYPE *territory_by_number(int) { return &location; }
bool has_base(FACTION_TYPE *f, LOCATION_TYPE *l) { return f->vnum == l->base_society; }
int society_deployment(CHAR_DATA *c, int f) {
  return f == c->fsociety ? c->deploy_society : f == c->legacy_society ? c->deploy_legacy_society : 0;
}
bool can_deploy(CHAR_DATA *ch, OPERATION_TYPE *, int) { return ch && ch->wounds < 2; }
bool join_to_operation(int, OPERATION_TYPE *);
'''
source += section("  struct OperationSignupFactions", "  int border_count(")
source += section("  bool join_to_operation(int facvnum,", "  void battle_faction(")
source += r'''
int main() {
  auto host = std::make_unique<FACTION_TYPE>();
  auto ally = std::make_unique<FACTION_TYPE>();
  auto foe = std::make_unique<FACTION_TYPE>();
  auto core = std::make_unique<FACTION_TYPE>();
  auto player = std::make_unique<CHAR_DATA>();
  auto pc = std::make_unique<PC_DATA>();
  DESCRIPTOR_DATA descriptor = {}; descriptor.connected = CON_PLAYING;
  player->desc = &descriptor;
  player->pcdata = pc.get(); player->name = str_dup("Al");
  int id = 100;
  for (auto f : {host.get(), ally.get(), foe.get(), core.get()}) {
    f->vnum = id++; f->type = FACTION_SOCIETY; f->name = str_dup("Society");
    f->battle_leader = str_dup(""); f->alliance = 1;
  }
  foe->alliance = 2; core->type = FACTION_CORE;
  FacVect = {ally.get(), foe.get(), core.get(), host.get()};
  const auto original = FacVect;
  OPERATION_TYPE op = {}; op.hour = 12; op.faction = host->vnum;
  op.competition = COMPETE_OPEN; op.sign_up[0] = player->name;
  online[player->name] = player.get();
  player->fsociety = ally->vnum; player->legacy_society = foe->vnum;
  player->fcore = core->vnum; player->faction = ally->vnum;
  player->deploy_society = 2; player->deploy_legacy_society = 1; player->deploy_core = 1;
  auto signups = operation_signup_factions(&op);
  assert(signups.members.count(ally->vnum) && !signups.members.count(foe->vnum));
  assert(fac_signed_up(ally->vnum, &op) && !nomembers(ally->vnum, &op));
  assign_operation_factions(&op, FACTION_SOCIETY, signups);
  assert(battle_factions[0] == host->vnum); // Host has NO personal signups.
  assert(battle_factions[1] == 0 && FacVect == original);
  assert(player->faction == ally->vnum);
  puts("PASS: allied-only signups supply the host team; short names and positive deployment settings agree.");
  player->faction = foe->vnum;
  signups = operation_signup_factions(&op);
  assert(signups.members.count(foe->vnum) && !signups.members.count(ally->vnum));
  std::fill(battle_factions, battle_factions + 6, 0);
  assign_operation_factions(&op, FACTION_SOCIETY, signups);
  assert(battle_factions[0] == foe->vnum && battle_factions[1] == 0);
  assert(FacVect == original && player->faction == foe->vnum);
  assert(core->deployed_power == 0 && host->last_defeated == 0);
  puts("PASS: selected society wins over primary membership; no duplicate/wrong-category teams or global shuffle.");
  player->deploy_legacy_society = 0;
  assert(operation_deployment_faction(player.get(), FACTION_SOCIETY) == ally->vnum);
  player->deploy_society = 0;
  assert(operation_deployment_faction(player.get(), FACTION_SOCIETY) == 0);
  record_operation_deployment(&op, player.get(), ally->vnum, host->vnum);
  assert(operation_member_faction(&op, player.get()) == ally->vnum);
  player->faction = foe->vnum;
  assert(operation_member_faction(&op, player.get()) == ally->vnum);
  CHAR_DATA npc = {}; SET_FLAG(npc.act, ACT_IS_NPC);
  assert(operation_member_faction(&op, &npc) == 0);
  player->deploy_society = 1; player->wounds = 2;
  assert(operation_signup_factions(&op).members.empty());
  player->wounds = 0; descriptor.connected = CON_QUITTING;
  assert(operation_signup_factions(&op).members.empty());
  online.clear(); signups = operation_signup_factions(&op);
  assert(signups.members.empty());
  puts("PASS: disabled membership fallback and recorded credit survive identity changes; NPC/absent signups are safe.");
  for (auto p : allocations) free(p);
}
'''
with tempfile.TemporaryDirectory(prefix="operation-launch-") as temp:
    cpp, binary = Path(temp) / "test.cpp", Path(temp) / "test"
    cpp.write_text(source)
    subprocess.run(["g++", "-std=gnu++17", "-g", "-O1", "-Wno-deprecated", "-Wno-write-strings",
                    "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-no-pie",
                    "-I" + str(ROOT / "src"), str(cpp), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
