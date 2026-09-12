#!/usr/bin/env python3
"""Exercise production Wakebound application, pull checks, and shroud capability."""
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
def section(file, start, end):
    s = (ROOT / file).read_text()
    a = s.index(start)
    return s[a:s.index(end, a)]
source = r'''
#include <cassert>
#include <cstring>
enum { AFF_WAKEBOUND=124, PLR_SHROUD=1, RITUAL_WAKEBOUND=56,
       SKILL_RITUALPROOF, TO_AFFECTS, APPLY_NONE, TO_CHAR, TO_ROOM, SHAPE_HUMAN };
const bool TRUE=true, FALSE=false;
struct PC { int process_subtype=RITUAL_WAKEBOUND, nightmare_shifted=0, prep_action=0; };
struct CHAR_DATA { PC *pcdata; bool ward=false, npc=false, proof=false, manip=true; int act=0, shape=SHAPE_HUMAN; CHAR_DATA *your_car=nullptr; };
struct AFFECT_DATA { int where,type,level,duration,location,modifier,bitvector; void *caster; bool weave; };
#define IS_AFFECTED(ch, f) ((ch)->ward)
#define IS_FLAG(a, f) ((a)&(f))
#define IS_NPC(ch) ((ch)->npc)
int event_cleanse=0, duration=0, power_value=100, saves=0, frees=0;
int ritual_buff_power(CHAR_DATA *) { return power_value; }
int get_skill(CHAR_DATA *ch, int) { return ch->proof; }
void act(const char *, CHAR_DATA *, void *, void *, int) {}
void send_to_char(const char *, CHAR_DATA *) {}
void affect_to_char(CHAR_DATA *ch, AFFECT_DATA *af) { assert(af->bitvector==AFF_WAKEBOUND); ch->ward=true; duration=af->duration; }
void save_char_obj(CHAR_DATA *, bool, bool) { ++saves; }
void free_char(CHAR_DATA *) { ++frees; }
bool has_shroudmanip(CHAR_DATA *ch) { return ch->manip; }
bool is_gm(CHAR_DATA *) { return false; }
bool str_cmp(const char *a,const char *b) { return strcmp(a,b)!=0; }
'''
source += section('src/lookup.c', '  bool can_shroud(', '  bool can_blood(')
source += 'void complete(CHAR_DATA *ch, CHAR_DATA *victim, bool online) { int power;\n'
source += section('src/process_actions.c', '      if (ch->pcdata->process_subtype == RITUAL_WAKEBOUND)', '      if (ch->pcdata->process_subtype == RITUAL_MINDWARD)') + '}\n'
source += 'bool allowed; void entry(CHAR_DATA *ch, const char *arg1) { allowed=false;\n'
source += section('src/skills.c', '    if (IS_AFFECTED(ch, AFF_WAKEBOUND) &&', '    if (battleground(ch->in_room)') + 'allowed=true; }\n'
source += 'void pull(CHAR_DATA *ch, CHAR_DATA *victim) { allowed=false;\n'
source += section('src/skills.c', '      CHAR_DATA *pull_target =', '      if (in_lodge(victim->in_room))') + 'allowed=true; }\n'
source += r'''
int main() {
 PC pc; CHAR_DATA caster{&pc}, target{&pc}, car{&pc}; car.npc=true; car.your_car=&target;
 complete(&caster,&target,true); assert(target.ward && duration==4320 && saves==1);
 // Operation eligibility must retain the normal shroud capability.
 assert(can_shroud(&target));
 entry(&target, ""); assert(!allowed);
 entry(&target, "pull"); assert(!allowed);
 target.act=PLR_SHROUD; entry(&target, ""); assert(allowed); // Can leave.
 entry(&target, "pull"); assert(!allowed);
 pull(&caster,&target); assert(!allowed);
 pull(&caster,&car); assert(!allowed);
 target.ward=false; target.act=0; entry(&target, ""); assert(allowed);
 pull(&caster,&target); assert(allowed); pull(&caster,&car); assert(allowed);
 target.proof=true; complete(&caster,&target,true); assert(!target.ward);
 target.proof=false; power_value=150; complete(&caster,&target,false);
 assert(target.ward && duration==6480 && frees==1);
}
'''
with tempfile.TemporaryDirectory(prefix='wakebound-') as temp:
    cpp=Path(temp)/'test.cpp'; exe=Path(temp)/'test'
    cpp.write_text(source)
    subprocess.run(['g++','-std=c++17',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('Wakebound regression checks passed')
