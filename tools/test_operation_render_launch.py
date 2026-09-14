#!/usr/bin/env python3
"""Compare operation launch indexing against the legacy faction searches.

Run in Linux/WSL with python3 tools/test_operation_render_launch.py.
Compiles an isolated ASan/UBSan executable; never loads or modifies game data.
Combat rendering is now covered by run_combat_map_tests.py: improved labels and
collision priorities intentionally no longer match the old rendering bytes.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
clans = (ROOT / 'src/clans.c').read_text()


def section(text, start, end):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


stubs = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <vector>
using std::vector;
#define TRUE true
#define FALSE false
struct CHAR_DATA {
  int fcore=0, legacy_society=0, fsociety=0, deploy_core=0, deploy_legacy_society=0, deploy_society=0;
};
long lookup_calls=0;
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

production = (
    section(clans, '  struct OperationSignupFactions', '  bool defender(')
    + section(clans, '  bool nomembers(int vnum,', '  void operation_assign_one(')
    + section(clans, '  static void assign_operation_factions(', '  int border_count(')
)

tests = r'''
int main() {
  vector<CHAR_DATA> people(300);
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
