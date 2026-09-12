#!/usr/bin/env python3
"""Instrument production NPC searches and action guards (Linux/WSL, g++)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
fight = (ROOT / 'src/fight.c').read_text()


def section(start, end):
    offset = fight.index(start)
    return fight[offset:fight.index(end, offset)]


stubs = r'''
#include <algorithm>
#include <cassert>
#include <cstring>
#include <cstdio>
#include <list>
#include <map>
#include <vector>
#define TRUE true
#define FALSE false
#define UMAX(a,b) std::max(a,b)
#define IS_NPC(c) ((c)->npc)
#define IS_IMMORTAL(c) ((c)->immortal)
#define IS_FLAG(flags,flag) (((flags)&(flag))!=0)
enum { PLR_SHROUD=1, PLR_DEEPSHROUD=2, ACT_COVER=4, ACT_TURRET=8,
       ACT_COMBATOBJ=16, PLR_GUEST=32, ACT_SENTINEL=64 };
enum { MONSTER_TEMPLATE=10, CORTEX_SOLDIER=20, ALLY_TEMPLATE=30,
       MINION_TEMPLATE=40, RACE_HUMAN=1, RACE_ANIMAL=2, RACE_CIVILIAN=3,
       RACE_DEMON=4, BORDER_ATTACK=1, INNER_NORTH_FOREST=1,
       INNER_SOUTH_FOREST=2, INNER_WEST_FOREST=3, HAVEN_TOWN_VNUM=4,
       DISTANCE_MEDIUM=1, FIGHT_WAIT=5 };
struct AREA_DATA { int vnum=0; };
struct ROOM_INDEX_DATA { AREA_DATA *area; int x=0; bool battle=false; };
struct MOB_INDEX_DATA { int vnum=115; };
struct CHAR_DATA {
  ROOM_INDEX_DATA *in_room=nullptr;
  MOB_INDEX_DATA *pIndexData=nullptr;
  CHAR_DATA *target=nullptr, *target_2=nullptr, *target_3=nullptr,
            *controled_by=nullptr, *cfighting=nullptr, *fight_current=nullptr,
            *cover=nullptr;
  bool npc=true, immortal=false, gm=false, ghost=false, helpless=false,
       ranged=true, reachable=true, in_fight=true, enemy=false;
  int wounds=0, act=0, faction=1, factiontwo=0, target_dam=0,
      target_dam_2=0, target_dam_3=0, race=5, order=0, bagcarrier=0,
      ttl=10, x=0, y=0, attack_timer=0, move_timer=0, attacking=1;
  const char *protecting="", *aggression="all", *ordertarget="", *name="unit";
};
struct FACTION_TYPE { const char *name="faction", *battle_target=""; int battle_order=0; };
struct Discipline { int vnum; };
Discipline discipline_table[]={{1},{2}};
int discipline_table_count=2;
using CharList=std::list<CHAR_DATA*>;
CharList char_list;
int preferences=0, paths=0, rounds=0, enemy_checks=0, fight_problem=0;
int str_cmp(const char *a,const char *b) { return strcmp(a,b); }
int safe_strlen(const char *s) { return strlen(s); }
bool is_gm(CHAR_DATA *c) { return c->gm; }
bool is_ghost(CHAR_DATA *c) { return c->ghost; }
bool is_helpless(CHAR_DATA *c) { return c->helpless; }
bool in_fight(CHAR_DATA *c) { return !fight_problem && c->in_fight; }
bool battleground(ROOM_INDEX_DATA *r) { return r && r->battle; }
bool can_get_to(CHAR_DATA *, ROOM_INDEX_DATA *) { ++paths; return true; }
const char *get_fac(CHAR_DATA *) { return "faction"; }
FACTION_TYPE *clan_lookup(int) { return nullptr; }
bool same_player(CHAR_DATA *, CHAR_DATA *) { return false; }
bool is_ranged(CHAR_DATA *c) { ++preferences; return c->ranged; }
int default_ranged(CHAR_DATA *) { return 1; }
int disc_range(CHAR_DATA *,int) { return 100; }
int combat_distance(CHAR_DATA *a,CHAR_DATA *b,bool) {
  return std::max(1,abs(a->x-b->x)+abs(a->in_room->x-b->in_room->x));
}
int damage_mod(int distance,int range) { return std::max(10,range-distance); }
bool is_in_cover(CHAR_DATA *c) { return c->cover; }
CHAR_DATA *get_cover(CHAR_DATA *c) { return c->cover; }
bool full_moon_pack(CHAR_DATA *) { return false; }
CHAR_DATA *full_moon_pack_prey(CHAR_DATA *) { return nullptr; }
bool dissent_crowd(CHAR_DATA *) { return false; }
bool cortex_public_enforcer(CHAR_DATA *) { return false; }
bool cortex_breach_monster(CHAR_DATA *) { return false; }
bool in_public(CHAR_DATA *,CHAR_DATA *) { return false; }
bool forest_monster(CHAR_DATA *) { return false; }
bool is_invader(CHAR_DATA *) { return false; }
int mist_level(ROOM_INDEX_DATA *) { return 3; }
bool will_agg(CHAR_DATA *a,CHAR_DATA *b) { return a->in_room && b->in_room && b->reachable; }
bool same_fight(CHAR_DATA *a,CHAR_DATA *b) { return in_fight(a) && in_fight(b); }
bool is_cover(CHAR_DATA *c) { return IS_FLAG(c->act,ACT_COVER); }
std::vector<CHAR_DATA*> combatants;
CHAR_DATA *next_combat_character(unsigned long long *cursor) {
  return *cursor<combatants.size() ? combatants[(*cursor)++] : nullptr;
}
void round_process(CHAR_DATA *) { ++rounds; }
int fight_speed(CHAR_DATA *) { return 2; }
bool has_enemy(CHAR_DATA *c) { ++enemy_checks; return c->enemy; }
bool can_see_char_distance(CHAR_DATA *,CHAR_DATA *,int) { return true; }
void log_string(const char *) {}
'''

production = section('  // Lazily initialized and reused', '  int process_npc_special(')
production += section('  CHAR_DATA *get_close_cover(', '  void npc_combat_move(')
# Exercise the actual guards, stopping before movement/damage callbacks.
production += section('  void npc_combat_attack(', '    CHAR_DATA *original = victim;') + '}\n'
move = section('  void npc_combat_move(', '    if (IS_NPC(ch) && (ch->pIndexData->vnum == ALLY_TEMPLATE')
production += move + '}\n'
production += section('  bool check_fight(', '  CHAR_DATA *next_fight_member(')

tests = r'''
int main() {
  AREA_DATA area;
  ROOM_INDEX_DATA room{&area}, remote{&area}; remote.x=500;
  MOB_INDEX_DATA mob;
  CHAR_DATA hunter; hunter.in_room=&room; hunter.pIndexData=&mob;
  std::vector<CHAR_DATA> candidates(80);
  for(size_t i=0;i<candidates.size();++i) {
    auto &c=candidates[i]; c.in_room=i%2 ? &remote : &room;
    c.pIndexData=&mob; c.npc=false; c.faction=2; c.race=RACE_HUMAN;
    c.x=i; c.target=&hunter; c.target_dam=i;
    char_list.push_back(&c);
  }
  // Reference selects by public, uncached scores in the original list order.
  for(int trial=0;trial<20;++trial) {
    hunter.ranged=trial%2; hunter.x=trial*3;
    CHAR_DATA *expected=nullptr; int best=0;
    for(auto c:char_list) {
      int score=get_agg(&hunter,c);
      if(score>best) { best=score; expected=c; }
    }
    preferences=paths=0;
    assert(get_npc_target(&hunter)==expected);
    assert(preferences==1 && paths==40);
  }
  char_list={&candidates[0],&candidates[2]};
  candidates[0].x=candidates[2].x=5;
  candidates[0].target_dam=candidates[2].target_dam=10;
  assert(get_npc_target(&hunter)==&candidates[0]); // first wins a tie
  candidates[0].immortal=true;
  assert(get_npc_target(&hunter)==&candidates[2]);
  candidates[0].immortal=false; candidates[0].act=PLR_SHROUD;
  assert(get_npc_target(&hunter)==&candidates[2]);
  candidates[0].act=0; candidates[0].reachable=false;
  assert(get_npc_target(&hunter)==&candidates[2]);
  candidates[0].reachable=true;
  char_list={&candidates[0]};
  candidates[0].cover=&candidates[3];
  assert(get_npc_target(&hunter)==&candidates[3]);
  candidates[0].cover=nullptr;
  puts("PASS: target equivalence, ties, exclusions, cover and fresh preferences; one profile per search.");

  for(int flag:{ACT_COVER,ACT_COMBATOBJ,ACT_TURRET}) {
    hunter.act=flag; hunter.move_timer=0; preferences=0;
    int before=rounds; npc_combat_move(&hunter);
    assert(rounds==before+1 && hunter.move_timer==10 && preferences==0);
    if(flag!=ACT_TURRET) {
      hunter.cfighting=&candidates[0]; npc_combat_attack(&hunter);
      assert(!hunter.cfighting && preferences==0);
    }
  }
  hunter.act=0; hunter.attack_timer=hunter.move_timer=3; preferences=0;
  npc_combat_move(&hunter); npc_combat_attack(&hunter);
  assert(preferences==0 && hunter.move_timer==3 && hunter.attack_timer==3);
  hunter.attack_timer=hunter.move_timer=0; hunter.wounds=3;
  npc_combat_move(&hunter); npc_combat_attack(&hunter);
  assert(preferences==0 && hunter.move_timer==0);
  hunter.wounds=0; char_list.clear(); hunter.attacking=1;
  npc_combat_attack(&hunter); assert(hunter.attacking==0);
  puts("PASS: inactive NPCs skip targeting; round processing, move cooldowns and targetless attacks.");

  hunter.x=0;
  for(auto &c:candidates) { c.in_room=&room; c.x=10; c.npc=true; c.act=ACT_COVER; }
  combatants={&candidates[2],&candidates[0]};
  assert(get_close_cover(&hunter)==&candidates[2]);
  assert(get_close_ally(&hunter)==&candidates[2]);
  candidates[2].in_fight=false;
  assert(get_close_cover(&hunter)==&candidates[0]);
  candidates[0].bagcarrier=1;
  assert(get_bag_carrier()==&candidates[0]);
  combatants.clear(); assert(!get_close_cover(&hunter) && !get_bag_carrier());
  puts("PASS: combat-index helper ordering, inactive filtering and empty populations.");

  hunter.npc=false; hunter.enemy=false;
  for(auto &c:candidates) { c.in_room=&remote; c.act=0; char_list.push_back(&c); }
  enemy_checks=0; assert(!check_fight(&hunter)); assert(enemy_checks==1);
  candidates[0].in_room=&room; candidates[0].enemy=true;
  candidates[0].fight_current=&candidates[1];
  enemy_checks=0; assert(check_fight(&hunter)); assert(enemy_checks==2);
  assert(hunter.fight_current==&candidates[1]);
  puts("PASS: distant bystanders skip nested enemy scans; nearby combat joins preserve turn state.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-npc-test-') as directory:
    cpp = Path(directory) / 'npc.cpp'
    binary = Path(directory) / 'npc-test'
    cpp.write_text(stubs + production + tests)
    subprocess.run(['g++', '-std=c++17', '-O1', '-g', '-Wall',
                    '-Wno-unused-variable', '-Wno-unused-parameter',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
