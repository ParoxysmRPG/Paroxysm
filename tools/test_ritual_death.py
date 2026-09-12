#!/usr/bin/env python3
"""Exercise production ritual death cleanup with engine stubs (Linux/WSL, g++)."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
skills = (root / "src/skills.c").read_text()
start = skills.index("  void end_maintained_ritual_on_death(")
function = skills[start:skills.index("  _DOFUN(do_ritual)", start)]
source = r'''
#include <cassert>
#include <cstdlib>
#include <cstring>
#include <strings.h>
#define FALSE false
#define IS_NPC(ch) ((ch)->npc)
struct PC_DATA {
  char *maintained_target = strdup("");
  char *ritual_maintainer = strdup("");
  int maintained_ritual = 0, maintain_cost = 0;
  ~PC_DATA() { free(maintained_target); free(ritual_maintainer); }
};
struct CHAR_DATA { const char *name; PC_DATA *pcdata; bool npc = false; };
struct DESCRIPTOR_DATA { CHAR_DATA *character = nullptr; };
CHAR_DATA *online = nullptr, *offline = nullptr;
int loads = 0, frees = 0, saves = 0;
bool loaded = true;
int safe_strlen(const char *s) { return s ? strlen(s) : 0; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
void free_string(char *s) { free(s); }
char *str_dup(const char *s) { return strdup(s); }
CHAR_DATA *get_char_world_pc(char *) { return online; }
bool load_char_obj(DESCRIPTOR_DATA *d, char *) { ++loads; d->character = offline; return loaded; }
void free_char(CHAR_DATA *) { ++frees; }
void save_char_obj(CHAR_DATA *, bool, bool) { ++saves; }
void set(char *&s, const char *value) { free(s); s = strdup(value); }
'''
source += function
source += r'''
int main() {
  PC_DATA caster_pc, target_pc;
  CHAR_DATA caster{"Caster", &caster_pc}, target{"Target", &target_pc};
  auto prepare = [&]() {
    set(caster_pc.maintained_target, "Target"); caster_pc.maintain_cost = 10;
    set(target_pc.ritual_maintainer, "Caster"); target_pc.maintained_ritual = 7;
  };
  end_maintained_ritual_on_death(nullptr);
  prepare(); caster.npc = true; end_maintained_ritual_on_death(&caster);
  assert(caster_pc.maintain_cost == 10); caster.npc = false;
  online = &target;
  end_maintained_ritual_on_death(&caster);
  assert(!*caster_pc.maintained_target && caster_pc.maintain_cost == 0);
  assert(!*target_pc.ritual_maintainer && target_pc.maintained_ritual == 0);
  assert(saves == 1 && loads == 0);
  end_maintained_ritual_on_death(&caster); assert(saves == 1);
  prepare(); online = nullptr; offline = &target;
  end_maintained_ritual_on_death(&caster);
  assert(target_pc.maintained_ritual == 0 && saves == 2 && frees == 1);
  prepare(); set(target_pc.ritual_maintainer, "SomeoneElse");
  end_maintained_ritual_on_death(&caster);
  assert(target_pc.maintained_ritual == 7 && saves == 2);
  prepare(); loaded = false;
  end_maintained_ritual_on_death(&caster);
  assert(!*caster_pc.maintained_target && saves == 2 && frees == 3);
  int previous_loads = loads;
  set(caster_pc.maintained_target, "casting"); caster_pc.maintain_cost = 10;
  end_maintained_ritual_on_death(&caster);
  assert(!*caster_pc.maintained_target && caster_pc.maintain_cost == 0);
  assert(loads == previous_loads);
  prepare(); online = &caster;
  set(caster_pc.maintained_target, "Caster");
  set(caster_pc.ritual_maintainer, "Caster"); caster_pc.maintained_ritual = 7;
  end_maintained_ritual_on_death(&caster);
  assert(caster_pc.maintained_ritual == 0 && saves == 2);
}
'''
with tempfile.TemporaryDirectory(prefix="haven-ritual-death-") as directory:
    cpp = Path(directory) / "ritual_death.cpp"
    binary = Path(directory) / "ritual_death"
    cpp.write_text(source)
    subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra",
                    "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                    "-no-pie", str(cpp), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("Ritual death cleanup checks passed.")
