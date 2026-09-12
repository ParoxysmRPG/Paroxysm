#!/usr/bin/env python3
"""Compare production map rendering and launch indexing against legacy searches.

Run in Linux/WSL with python3 tools/test_operation_render_launch.py.
Compiles an isolated ASan/UBSan executable; never loads or modifies game data.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
fight = (ROOT / 'src/fight.c').read_text()
clans = (ROOT / 'src/clans.c').read_text()


def section(text, start, end):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


stubs = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <list>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <vector>
using std::vector;
#define TRUE true
#define FALSE false
#define MSL 4096
#define DISTANCE_MEDIUM 1
enum { DIR_NORTH, DIR_NORTHEAST, DIR_EAST, DIR_SOUTHEAST,
       DIR_SOUTH, DIR_SOUTHWEST, DIR_WEST, DIR_NORTHWEST,
       POI_EXTRACT, POI_CAPTURE };
struct ROOM_INDEX_DATA { int x=0, y=0, z=0, size=50; };
struct CHAR_DATA {
  ROOM_INDEX_DATA *in_room=nullptr;
  int x=0, y=0, mapcount=0, facing=DIR_NORTH;
  int fcore=0, legacy_society=0, fsociety=0, deploy_core=0, deploy_legacy_society=0, deploy_society=0;
  bool gm=false, visible=true, mapvisible=true, hostile=false;
  std::string name="a guard", alternate="a guard";
};
typedef std::list<CHAR_DATA*> CharList;
CharList char_list;
long visibility_calls=0, lookup_calls=0;
bool is_gm(CHAR_DATA *ch) { return ch->gm; }
bool can_see_char_distance(CHAR_DATA *, CHAR_DATA *ch, int) {
  ++visibility_calls; return ch->visible && ch->in_room;
}
bool can_map_see(CHAR_DATA *, CHAR_DATA *ch) { return ch->mapvisible; }
const char *PERS(CHAR_DATA *ch, CHAR_DATA *) { return ch->name.c_str(); }
const char *PERS_2(CHAR_DATA *ch, CHAR_DATA *) { return ch->alternate.c_str(); }
void remove_color(char *buf, const char *s) { strcpy(buf,s); }
int get_agg(CHAR_DATA *a, CHAR_DATA *b) { return a->hostile || b->hostile; }
int map_translation[50];
std::string output;
void send_to_char(const char *s, CHAR_DATA *) { output+=s; }
void scan_fight(CHAR_DATA *, bool) {}
bool invisioncone_coordinates(CHAR_DATA *, int, int) { return true; }
ROOM_INDEX_DATA terrain;
ROOM_INDEX_DATA *sourced_room_by_coordinates(ROOM_INDEX_DATA *, int x, int y, int z, bool) {
  terrain.x=x; terrain.y=y; terrain.z=z; return &terrain;
}
const char *mapfill(CHAR_DATA *, ROOM_INDEX_DATA *) { return "`g+"; }
struct OperationPoiPosition { int x,y,type; };
bool show_objectives=true;
int operation_poi_positions(CHAR_DATA *, OperationPoiPosition *) { return show_objectives ? 1 : 0; }
int operation_poi_type(const OperationPoiPosition *, int count, int size, int y, int x) {
  return count && y==size/2 && x/2==size/2 ? POI_CAPTURE : -1;
}
struct OPERATION_TYPE { char *sign_up[100] = {}; };
struct FACTION_TYPE { int vnum; };
vector<FACTION_TYPE *> FacVect;
std::map<std::string, CHAR_DATA *> online;
int safe_strlen(const char *s) { return s ? strlen(s) : 0; }
CHAR_DATA *get_char_world_pc(char *s) {
  ++lookup_calls;
  auto it=online.find(s);
  return it==online.end() ? nullptr : it->second;
}
typedef std::tuple<int,int,bool> Assignment;
vector<Assignment> assignments;
void operation_assign_one(FACTION_TYPE *f, OPERATION_TYPE *, int, bool members) {
  assignments.emplace_back(1,f->vnum,members);
}
void operation_assign_two(FACTION_TYPE *f, OPERATION_TYPE *, int) {
  assignments.emplace_back(2,f->vnum,false);
}
void operation_assign_three(FACTION_TYPE *f, OPERATION_TYPE *, int) {
  assignments.emplace_back(3,f->vnum,false);
}
'''

draw = section(fight, '  void draw_map(CHAR_DATA *ch, int size)', '  void init_map(')
# Keep rendering and formatting identical; restore the previous occupant lookup
# and count calls to compare every byte and per-character mapcount side effect.
reference = draw.replace('void draw_map(', 'void reference_draw_map(')
reference = reference.replace('    const std::vector<CombatMapCell> map_cells = combat_map_cells(ch, size);\n', '')
reference = reference.replace('          const CombatMapCell &cell = map_cells[i * size + j / 2];\n          rch = cell.character;',
                              '          rch = get_mapch(ch, size, i, j);')
reference = reference.replace('rch->mapcount = cell.count;', 'rch->mapcount = mapch_count(ch, size, i, j);')
assert 'map_cells' not in reference and 'cell.' not in reference

production = (
    section(fight, '  int relative_x(CHAR_DATA *ch,', '  int relative_z(CHAR_DATA *ch,')
    + section(fight, '  int setup_expand(int number)', '  int map_contract(int number)')
    + section(fight, '  struct CombatMapCell', '  bool can_map_see(')
    + section(fight, '  int maptox(int size,', '  char *mapfill(')
    + draw + reference
    + section(clans, '  struct OperationSignupFactions', '  bool defender(')
    + section(clans, '  bool nomembers(int vnum,', '  void operation_assign_one(')
    + section(clans, '  static void assign_operation_factions(', '  int border_count(')
)

tests = r'''
int main() {
  setup_translation();
  ROOM_INDEX_DATA room, other; other.x=2; other.y=-1;
  CHAR_DATA viewer; viewer.in_room=&room; viewer.name=viewer.alternate="You";
  vector<CHAR_DATA> people(300);
  char_list.push_back(nullptr); char_list.push_back(&viewer);
  for (int i=0; i<300; ++i) {
    auto &c=people[i]; c.in_room=i%4 ? &room : &other;
    c.x=(i*17)%290-120; c.y=(i*23)%290-120;
    c.gm=i%17==0; c.visible=i%7!=0; c.mapvisible=i%11!=0; c.hostile=i%2;
    c.name=i%3 ? "a guard" : "an agent";
    c.alternate=i%5 ? c.name : "Someone";
    char_list.push_back(&c);
  }
  // Shared cells preserve list order and counts, even when one occupant hides.
  people[1].x=people[2].x=people[3].x=0;
  people[1].y=people[2].y=people[3].y=0;
  long old_calls=0,new_calls=0;
  for (int size : {11,21,31}) for (int heading=0; heading<8; ++heading) {
    viewer.facing=heading; viewer.x=heading*3; viewer.y=heading*2;
    people[2].visible=heading%2;
    people[3].in_room=heading%2 ? &room : &other;
    output.clear(); visibility_calls=0;
    for (auto c:char_list) if(c) c->mapcount=-1;
    reference_draw_map(&viewer,size);
    const std::string expected=output;
    vector<int> counts;
    for (auto c:char_list) if(c) counts.push_back(c->mapcount);
    old_calls+=visibility_calls;
    output.clear(); visibility_calls=0;
    for (auto c:char_list) if(c) c->mapcount=-1;
    draw_map(&viewer,size);
    new_calls+=visibility_calls;
    assert(output==expected);
    int n=0; for (auto c:char_list) if(c) assert(c->mapcount==counts[n++]);
  }
  printf("PASS: identical map output/counts for 24 draws, all headings; visibility checks %ld -> %ld.\n",old_calls,new_calls);
  assert(new_calls<old_calls/5);
  // Verify every cell, including exact positive/negative interval boundaries.
  for (int edge=-15; edge<=15; ++edge) {
    people[1].x=map_expand(edge); people[1].y=map_expand(-edge);
    auto cells=combat_map_cells(&viewer,31);
    for(int y=0;y<31;++y) for(int x=0;x<62;++x) {
      assert(cells[y*31+x/2].character==get_mapch(&viewer,31,y,x));
      assert(cells[y*31+x/2].count==mapch_count(&viewer,31,y,x));
    }
  }
  // Colour-heavy maps can exceed the old 4096-byte destination buffer.
  char_list.clear(); show_objectives=false; viewer.facing=DIR_NORTH;
  output.clear(); draw_map(&viewer,31); assert(output.size()>4096);
  puts("PASS: exact map boundaries, refreshed visibility/rooms, and map output larger than 4096 bytes.");

  OPERATION_TYPE op;
  vector<std::string> names(100);
  for(int i=0;i<100;++i) {
    names[i]="Player"+std::to_string(i); op.sign_up[i]=&names[i][0];
    auto &c=people[i]; c.fcore=i%23; c.legacy_society=i%13; c.fsociety=i%7;
    c.deploy_core=i%4-1; c.deploy_legacy_society=i%3; c.deploy_society=i%5;
    if(i%9) online[names[i]]=&c;
  }
  op.sign_up[0]=nullptr; op.sign_up[1]=const_cast<char*>("Al");
  op.sign_up[2]=op.sign_up[3]; // Duplicate names must not duplicate factions.
  vector<FACTION_TYPE> factions(200);
  for(int i=0;i<200;++i) { factions[i].vnum=(i*37)%200; FacVect.push_back(&factions[i]); }
  lookup_calls=0;
  for(auto f:FacVect) if(fac_signed_up(f->vnum,&op))
    operation_assign_one(f,&op,1,!nomembers(f->vnum,&op));
  for(auto f:FacVect) if(fac_signed_up(f->vnum,&op)) operation_assign_two(f,&op,1);
  for(auto f:FacVect) if(fac_signed_up(f->vnum,&op)) operation_assign_three(f,&op,1);
  auto expected=assignments;
  long legacy_lookups=lookup_calls;
  assignments.clear(); lookup_calls=0;
  auto signups=operation_signup_factions(&op);
  assert(lookup_calls==98);
  assign_operation_factions(&op,1,signups);
  assert(assignments==expected && lookup_calls==98);
  printf("PASS: identical faction assignment order and eligibility; player lookups %ld -> %ld.\n",legacy_lookups,lookup_calls);
  for(int i=0;i<200;++i) {
    assert((signups.deployed.count(i)!=0)==fac_signed_up(i,&op));
    assert((signups.members.count(i)!=0)==!nomembers(i,&op));
  }
  online.clear(); auto empty=operation_signup_factions(&op);
  assignments.clear(); assign_operation_factions(&op,1,empty);
  assert(assignments.empty() && empty.members.empty());
  puts("PASS: all deployment states, absent/duplicate/short names, and fresh launch after disconnects.");
}
'''

with tempfile.TemporaryDirectory(prefix='haven-render-launch-') as directory:
    cpp = Path(directory) / 'test.cpp'
    binary = Path(directory) / 'test'
    cpp.write_text(stubs + production + tests)
    subprocess.run(['g++', '-std=c++11', '-O1', '-g', '-Wall', '-Wextra',
                    '-Wno-unused-parameter', '-Wno-write-strings',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
