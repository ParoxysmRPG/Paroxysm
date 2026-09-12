#!/usr/bin/env python3
"""Exercise production toxin application, cooldowns and round effects (WSL)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
skills = (ROOT / "src/skills.c").read_text()
fight = (ROOT / "src/fight.c").read_text()

def section(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a)]

source = r'''
#include <cassert>
#include <cstring>
#include <cstdio>
#include <initializer_list>
#define _DOFUN(name) void name(CHAR_DATA *ch, char *argument)
#define IS_SET(value, flag) ((value) & (flag))
#define IS_NPC(ch) ((ch)->npc)
const bool TRUE=true, FALSE=false;
enum { MSL=1024, SKILL_PARALYTIC=1, SKILL_POISONTOXIN, ITEM_WEAPON,
       ITEM_RANGED, ITEM_WARDROBE=16, ITEM_ARMORED=32, AMMO_PARALYTIC,
       AMMO_POISON, CAFF_PARALYTICTOXIN, CAFF_POISONTOXIN, CAFF_STUNNED,
       CAFF_ROOT, DIS_RADIATION, FIGHT_WAIT=10 };
struct OBJ_DATA {
  OBJ_DATA *next_content=nullptr;
  int extra_flags=0, item_type=ITEM_WEAPON, buff=0, value[5]={};
  const char *name="knife", *description="a knife";
};
struct CHAR_DATA {
  OBJ_DATA *carrying=nullptr;
  CHAR_DATA *fight_current=this;
  bool fight_fast=false, doneabil=false, fighting=false, gm=false, npc=false, undead=false;
  int skills[3]={0,1,1}, ability_timer=0, debuff=0, damage=0, speed=2;
  int attack_timer=0, move_timer=0, caff[30]={}, caff_duration[30]={};
};
char *one_argument_nouncap(char *input, char *out) {
  while (*input && *input!=' ') *out++=*input++;
  *out=0; while (*input==' ') ++input; return input;
}
int get_skill(CHAR_DATA *ch, int id) { return ch->skills[id]; }
bool is_name(const char *a, const char *b) { return !strcmp(a,b); }
int str_cmp(const char *a, const char *b) { return strcmp(a,b); }
void send_to_char(const char *, CHAR_DATA *) {}
void printf_to_char(CHAR_DATA *, const char *, ...) {}
bool in_fight(CHAR_DATA *ch) { return ch->fighting; }
bool is_gm(CHAR_DATA *ch) { return ch->gm; }
bool is_undead(CHAR_DATA *ch) { return ch->undead; }
int fight_speed(CHAR_DATA *ch) { return ch->speed; }
int ability_cooldown(CHAR_DATA *, int) { return 2; }
int max_hp(CHAR_DATA *) { return 1000; }
void combat_damage(CHAR_DATA *, CHAR_DATA *ch, int damage, int) { ch->damage+=damage; }
'''
source += section(skills, "  _DOFUN(do_toxin)", "  _DOFUN(do_trace)")
source += section(fight, "  void apply_caff(", "  _DOFUN(do_caff)")
source += "void toxin_round(CHAR_DATA *ch) {\n" + section(
    fight, "    if (has_caff(ch, CAFF_PARALYTICTOXIN))", "    if (IS_FLAG(ch->fightflag, FIGHT_MINIONS1))") + "}\n"
source += r'''
void apply(CHAR_DATA *ch, const char *kind) {
  char command[80]; snprintf(command,sizeof(command),"knife %s",kind); do_toxin(ch,command);
}
int main() {
  for (const char *kind : {"paralytic", "poison"}) for (bool fast : {false,true}) {
    CHAR_DATA ch; OBJ_DATA weapon; ch.carrying=&weapon; ch.fight_fast=fast;
    apply(&ch,kind); assert(weapon.buff==1 && ch.ability_timer==0 && ch.debuff==0);
    weapon.buff=0; ch.fighting=true; ch.ability_timer=1;
    apply(&ch,kind); assert(weapon.buff==0 && ch.ability_timer==1);
    ch.ability_timer=0;
    if (!fast) {
      ch.fight_current=nullptr; apply(&ch,kind); assert(weapon.buff==0);
      ch.fight_current=&ch; ch.doneabil=true; apply(&ch,kind); assert(weapon.buff==0);
      ch.doneabil=false;
    }
    apply(&ch,kind);
    assert(weapon.buff==1 && ch.ability_timer==(fast?40:20) && ch.doneabil);
    weapon.buff=0; apply(&ch,kind); assert(weapon.buff==0);
    ch.ability_timer=0; ch.doneabil=false; apply(&ch,kind); assert(weapon.buff==1);
    weapon.buff=0; ch.ability_timer=0; ch.doneabil=false; ch.skills[1]=ch.skills[2]=0;
    apply(&ch,kind); assert(weapon.buff==0 && ch.ability_timer==0);
  }
  for (bool undead : {false,true}) for (int effect : {CAFF_PARALYTICTOXIN,CAFF_POISONTOXIN}) {
    CHAR_DATA ch; ch.undead=undead;
    apply_caff(&ch,effect,1); toxin_round(&ch);
    assert(ch.debuff==(effect==CAFF_PARALYTICTOXIN?(undead?10:30):0));
    assert(ch.damage==(effect==CAFF_POISONTOXIN&&!undead?50:0));
    lower_caff(&ch,effect); assert(!has_caff(&ch,effect));
    int damage=ch.damage, debuff=ch.debuff; toxin_round(&ch);
    assert(ch.damage==damage && ch.debuff==debuff);
  }
  puts("PASS: free toxin reapplication, shared cooldown, turn checks, one-round effects and undead behavior.");
}
'''
assert "apply_caff(ch, CAFF_PARALYTICTOXIN, 1);" in fight
assert "apply_caff(ch, CAFF_POISONTOXIN, 1);" in fight
with tempfile.TemporaryDirectory(prefix="haven-toxin-") as tmp:
    cpp = Path(tmp) / "toxin.cpp"
    binary = Path(tmp) / "toxin"
    cpp.write_text(source)
    subprocess.run(["g++", "-std=c++17", "-fsanitize=address,undefined", "-g",
                    str(cpp), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
