#!/usr/bin/env python3
"""Exercise production emotion commands and eligibility without loading world files."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
skills = (root / 'src/skills.c').read_text()
clans = (root / 'src/clans.c').read_text()

def section(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a)]

source = r'''
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#define TRUE true
#define FALSE false
#define MSL 4096
#define IS_NPC(ch) ((ch)->npc)
#define IS_AFFECTED(ch, flag) ((ch)->affected)
#define NAME(ch) ((ch)->name)
#define _DOFUN(name) void name(CHAR_DATA *ch, char *argument)
enum { RACE_FREEANGEL=1, AFF_SUFFER, TO_CHAR, STYPE_ABOMINATION,
       SKILL_MINDREADING, SKILL_TOUCHED };
struct CHAR_DATA;
using CharList = std::vector<CHAR_DATA *>;
struct ROOM { CharList *people; };
struct PC { int neutralized=0, bonus_origin=0, dexp=0; };
struct CHAR_DATA {
  bool npc=false, angel=false, demon=false, ward=false, affected=false, super=false;
  int race=0, tier=1, legendary=0, society=0, skills[20]={};
  PC data; PC *pcdata=&data;
  ROOM *in_room=nullptr;
  const char *name="someone";
  std::string output;
};
bool is_angelborn(CHAR_DATA *ch) { return ch->angel; }
bool is_demonborn(CHAR_DATA *ch) { return ch->demon; }
bool seems_demonborn(CHAR_DATA *ch) { return ch->demon; }
bool is_suggestible(CHAR_DATA *ch) { return ch->angel && !ch->ward; }
bool is_sufferingsensitive(CHAR_DATA *ch) { return ch->demon; }
bool is_super(CHAR_DATA *ch) { return ch->super; }
bool cortex_loyalty_brainwashed(CHAR_DATA *) { return false; }
int get_tier(CHAR_DATA *ch) { return ch->tier; }
int skillbase_count(CHAR_DATA *ch, int) { return ch->legendary; }
int safe_strlen(const char *s) { return strlen(s); }
int str_cmp(const char *a, const char *b) { return strcmp(a,b); }
char *one_argument_nouncap(char *s, char *out) {
  while (*s==' ') ++s;
  while (*s && *s!=' ') *out++=*s++;
  *out=0;
  while (*s==' ') ++s;
  return s;
}
CHAR_DATA *get_char_room(CHAR_DATA *ch, void *, const char *name) {
  for (auto *to : *ch->in_room->people) if (!strcmp(to->name,name)) return to;
  return nullptr;
}
void send_to_char(const char *text, CHAR_DATA *to) { to->output += text; }
void printf_to_char(CHAR_DATA *to, const char *format, ...) {
  char buf[MSL]; va_list args; va_start(args,format);
  vsnprintf(buf,sizeof(buf),format,args); va_end(args); to->output += buf;
}
void act(const char *text, CHAR_DATA *to, void *, CHAR_DATA *, int) { to->output += text; }
void spyshow(CHAR_DATA *, const char *) {}
void char_rplog(CHAR_DATA *, const char *) {}
'''
source += section(clans, '  bool is_containment_priority(', '  bool cortex_loyalty_chip(')
source += section(skills, '  _DOFUN(do_suffer)', '  bool seems_suggestible(')
source += 'bool learn(CHAR_DATA *ch, int skill, bool show) {\n'
source += section(skills, '    if (skill == SKILL_MINDREADING) {', '    if (skill == SKILL_SILVERVULN')
source += 'return true; }\n'
source += r'''
int main() {
  CHAR_DATA speaker, angel, demon, ordinary;
  angel.name="angel"; angel.angel=true;
  demon.name="demon"; demon.demon=true;
  CharList people={&speaker,&angel,&demon,&ordinary}; ROOM room{&people};
  for (auto *ch : people) ch->in_room=&room;
  for (const char *strength : {"mild","moderate","strong"}) {
    char command[MSL];
    auto clear=[&]() { for (auto *ch : people) ch->output.clear(); };
    clear(); snprintf(command,sizeof(command),"%s win the race",strength);
    do_desire(&speaker,command);
    assert(demon.output.find("sinfully sabotage $N's desire to win the race")!=std::string::npos);
    assert(angel.output.find("want to help")!=std::string::npos);
    assert(ordinary.output.empty());
    clear(); snprintf(command,sizeof(command),"demon %s win the race",strength);
    do_desire(&speaker,command);
    assert(demon.output.find("sinfully sabotage")!=std::string::npos && angel.output.empty());
    clear(); snprintf(command,sizeof(command),"%s losing the race",strength);
    do_dread(&speaker,command);
    assert(angel.output.find("soothe $N's dread of losing the race")!=std::string::npos);
    assert(demon.output.find("want to manifest")!=std::string::npos);
    assert(ordinary.output.empty());
    clear(); snprintf(command,sizeof(command),"angel %s losing the race",strength);
    do_dread(&speaker,command);
    assert(angel.output.find("soothe")!=std::string::npos && demon.output.empty());
    clear(); snprintf(command,sizeof(command),"%s lose the race",strength);
    do_suffer(&speaker,command);
    assert(angel.output.find("pang of guilt from $N's suffering")!=std::string::npos);
    assert(demon.output.find("mood")!=std::string::npos && ordinary.output.empty());
    clear(); angel.ward=true;
    do_suffer(&speaker,command); assert(angel.output.empty());
    do_dread(&speaker,command); assert(angel.output.empty());
    angel.ward=false;
  }
  assert(!learn(&speaker,SKILL_MINDREADING,false));
  speaker.skills[SKILL_TOUCHED]=1; assert(learn(&speaker,SKILL_MINDREADING,false));
  speaker.skills[SKILL_TOUCHED]=0; speaker.super=true;
  assert(learn(&speaker,SKILL_MINDREADING,false));
  assert(!is_containment_priority(nullptr));
  for (int society : {0,5,990005}) for (bool legendary : {false,true}) {
    speaker.society=society; speaker.tier=legendary ? 1 : 4;
    speaker.legendary=legendary;
    assert(is_containment_priority(&speaker));
    speaker.pcdata->neutralized=1; assert(!is_containment_priority(&speaker));
    speaker.pcdata->neutralized=0; assert(is_containment_priority(&speaker));
  }
  speaker.tier=3; speaker.legendary=0; assert(!is_containment_priority(&speaker));
  puts("PASS: neutralizer priority exemption/restoration, zero-dream-XP mindreading eligibility, and all emotion strengths/targets with ordinary-recipient and angel ward exclusions.");
}
'''
with tempfile.TemporaryDirectory(prefix='haven-sensitivity-') as temp:
    cpp = Path(temp) / 'test.cpp'
    binary = Path(temp) / 'test'
    cpp.write_text(source)
    subprocess.run(['g++', '-std=c++17', '-Wall', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
