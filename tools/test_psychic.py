#!/usr/bin/env python3
"""Run isolated production psychic ability branches and confusion targeting (WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
skills = (ROOT / 'src/skills.c').read_text()
fight = (ROOT / 'src/fight.c').read_text()

def section(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a)]

source = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
#include <set>
enum { SKILL_PSYCHIC, CAFF_CONFUSE, CAFF_BEWILDER, CAFF_WEAKEN,
       CAFF_SEMIWEAKEN, CAFF_STASIS, CAFF_FEAR, FIGHT_NOATTACK=64,
       ACT_COMBATOBJ=128, TO_CHAR, TO_VICT, TO_NOTVICT, FIGHT_WAIT=10 };
const bool TRUE=true, FALSE=false;
#define IS_FLAG(flags, flag) ((flags) & (flag))
#define IS_NPC(ch) ((ch)->npc)
struct CHAR_DATA {
  int rank=2, fightflag=0, attackdam=0, ability_timer=0, act=0;
  int attacks=0, moves=0, in_room=1, distance=1;
  bool fight_fast=false, ward=false, npc=false, gm=false, fighting=true, enemy=true;
  CHAR_DATA *afraid_of=nullptr;
  std::set<int> effects, cooldowns;
};
using CharList=std::vector<CHAR_DATA *>;
CharList char_list;
CHAR_DATA *target;
int get_skill(CHAR_DATA *ch, int) { return ch->rank; }
int str_cmp(const char *a, const char *b) { return strcmp(a,b); }
void send_to_char(const char *, CHAR_DATA *) {}
CHAR_DATA *get_char_fight(CHAR_DATA *, const char *) { return target; }
bool abilcool(CHAR_DATA *ch, int, int id) { return ch->cooldowns.count(id); }
void useabil(CHAR_DATA *ch, int, int id) { ch->cooldowns.insert(id); }
bool mindwarded(CHAR_DATA *ch) { return ch->ward; }
void act(const char *, CHAR_DATA *, void *, CHAR_DATA *, int) {}
void apply_caff(CHAR_DATA *ch, int id, int) { ch->effects.insert(id); }
bool has_caff(CHAR_DATA *ch, int id) { return ch->effects.count(id); }
void remove_caff(CHAR_DATA *ch, int id) { ch->effects.erase(id); }
int fight_speed(CHAR_DATA *) { return 1; }
int ability_cooldown(CHAR_DATA *, int) { return 2; }
void useattack(CHAR_DATA *ch) { ++ch->attacks; }
void usemove(CHAR_DATA *ch) { ++ch->moves; }
void noattack(CHAR_DATA *ch) { ++ch->attacks; }
void nomove(CHAR_DATA *ch) { ++ch->moves; }
bool battleground(int) { return false; }
const char *logact(const char *s, CHAR_DATA *, CHAR_DATA *) { return s; }
void op_report(const char *, CHAR_DATA *) {}
bool is_gm(CHAR_DATA *ch) { return ch->gm; }
bool in_fight(CHAR_DATA *ch) { assert(ch); return ch->fighting; }
bool same_fight(CHAR_DATA *a, CHAR_DATA *b) { return a->fighting && b->fighting; }
bool is_enemy(CHAR_DATA *, CHAR_DATA *b) { return b->enemy; }
int combat_distance(CHAR_DATA *a, CHAR_DATA *, bool) { return a->distance; }
int rolls=0;
int number_range(int, int) { ++rolls; return 1; }
'''
source += section(fight, '  static CHAR_DATA *confused_target(', '  // Retreat vectors are extended')
branches = section(skills, '    else if (!str_cmp(arg1, "bewilder"))',
                   '    else if (!str_cmp(arg1, "distract"))')
source += 'void ability(CHAR_DATA *ch, const char *arg1) {\nconst char *arg2="target"; CHAR_DATA *victim;\nif (false) {}\n' + branches + '\n}\n'
source += r'''
int main() {
  const char *names[]={"bewilder","confuse","doubt","stasis","fear"};
  int effects[]={CAFF_BEWILDER,CAFF_CONFUSE,CAFF_WEAKEN,CAFF_STASIS,CAFF_FEAR};
  for (int i=0;i<5;++i) for (bool fast : {false,true}) {
    CHAR_DATA caster, victim;
    caster.fight_fast=fast; target=&victim;
    ability(&caster,names[i]);
    assert(victim.effects.count(effects[i]));
    assert(caster.ability_timer==20);
    assert(caster.attacks==(i==1 || i>=3));
    assert(caster.moves==(i>=3));
    if(i==3) assert(victim.moves==1 && victim.attacks==1);
    if(i==4) assert(victim.afraid_of==&caster);
    caster={}; victim={}; victim.ward=true;
    ability(&caster,names[i]);
    assert(victim.effects.empty() && !victim.afraid_of);
    assert(victim.attacks==0 && victim.moves==0);
    caster={}; victim={}; caster.rank=i>=3 ? 1 : 0;
    ability(&caster,names[i]);
    assert(victim.effects.empty() && caster.cooldowns.empty());
    caster={}; target=nullptr;
    ability(&caster,names[i]);
    assert(caster.cooldowns.empty());
    if(i>0) {
      caster={}; target=&victim; caster.cooldowns.insert(i+1);
      ability(&caster,names[i]);
      assert(victim.effects.empty() && caster.ability_timer==0);
    }
  }
  CHAR_DATA caster, original, near, far, ally, gm, outside;
  original.distance=10; near.distance=1; far.distance=9;
  ally.enemy=false; gm.gm=true; outside.fighting=false;
  char_list={nullptr,&caster,&original,&near,&far,&ally,&gm,&outside};
  caster.effects.insert(CAFF_CONFUSE);
  assert(confused_target(&caster,&original,false)==&far);
  assert(rolls==2); // The near candidate must not shrink the original range.
  assert(!has_caff(&caster,CAFF_CONFUSE));
  assert(confused_target(&caster,&original,true)==&original && rolls==2);
  caster.effects.insert(CAFF_CONFUSE); char_list={&caster};
  assert(confused_target(&caster,&original,true)==&original);
  assert(!has_caff(&caster,CAFF_CONFUSE));
  puts("PASS: psychic ranks, wards, costs, cooldowns, and single-use confusion targeting.");
}
'''
# Queue storage must retain the command before either argument is consumed.
queue = section(skills, '  _DOFUN(do_ability)', '    if (!in_fight(ch)) {')
assert queue.index('snprintf(queued_argument') < queue.index('one_argument_nouncap')
assert queue.count('str_dup(queued_argument)') == 2
assert 'ch->abilmove = str_dup(argument)' not in queue
assert fight.count('same_fight(ch, ch->afraid_of)') == 1  # Shared approach/retreat handler.
with tempfile.TemporaryDirectory(prefix='haven-psychic-') as tmp:
    cpp = Path(tmp) / 'psychic.cpp'
    binary = Path(tmp) / 'psychic'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=c++17', '-fsanitize=address,undefined', '-g',
                    str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
