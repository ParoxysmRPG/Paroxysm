#!/usr/bin/env python3
"""Exercise the real command and trust function in a disposable Linux harness."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
handler = (ROOT / "src/handler.c").read_text()
start = handler.index("int get_trust(CHAR_DATA *ch) {")
trust = handler[start:handler.index("\n}", start) + 2]

HARNESS = r'''
#include "merc.h"
#include <cassert>
#include <cctype>
#include <cstring>
#include <sys/stat.h>
#include "game_update.cc"

static std::string output;
void send_to_char(const char *text, CHAR_DATA *) { output += text; }
void printf_to_char(CHAR_DATA *, char *, ...) { assert(false); }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
char *one_argument(char *argument, char *word) {
    while (*argument && isspace(*argument)) ++argument;
    while (*argument && !isspace(*argument)) *word++ = *argument++;
    *word = '\0';
    while (*argument && isspace(*argument)) ++argument;
    return argument;
}

TRUST_FUNCTION

static void invoke(CHAR_DATA &ch, const char *action) {
    char argument[128];
    strcpy(argument, action);
    output.clear();
    do_gameupdate(&ch, argument); // Direct calls bypass the command table.
}
static void denied(CHAR_DATA &ch) {
    for (const char *action : {"", "build", "install", "rollback", "status", "log"}) {
        invoke(ch, action);
        assert(output == "Only admins may use gameupdate.\n\r");
    }
}
int main() {
    CHAR_DATA ch = {};
    ch.name = const_cast<char *>("PermissionTest");
    for (int level = 0; level < LEVEL_ADMIN; ++level) {
        ch.level = level;
        denied(ch);
    }
    ch.level = MAX_LEVEL;
    ch.trust = LEVEL_ADMIN - 1; // Explicit lower trust overrides character level.
    denied(ch);
    ch.trust = -1;
    denied(ch);
    ch.trust = MAX_LEVEL;
    SET_FLAG(ch.act, ACT_IS_NPC);
    denied(ch);
    REMOVE_FLAG(ch.act, ACT_IS_NPC);
    struct stat st;
    assert(stat("../.updates", &st) != 0); // Denied calls have no updater side effects.
    ch.trust = 0;
    for (int level = LEVEL_ADMIN; level <= MAX_LEVEL; ++level) {
        ch.level = level;
        invoke(ch, "");
        assert(output.find("Gameupdate build") != std::string::npos);
    }
    ch.level = 1;
    ch.trust = LEVEL_ADMIN; // Explicitly delegated admin trust is supported.
    invoke(ch, "status");
    assert(output.find("Updater idle.") != std::string::npos);
    invoke(ch, "log");
    assert(output.find("Updater idle.") != std::string::npos);
    puts("Gameupdate permissions passed: admin boundary, trust overrides, NPCs, all actions.");
}
'''

with tempfile.TemporaryDirectory(prefix="haven-update-permissions-") as directory:
    root = Path(directory)
    (root / "area").mkdir()
    source = root / "permissions.cc"
    source.write_text(HARNESS.replace("TRUST_FUNCTION", trust))
    executable = root / "permissions"
    subprocess.run(["g++", "-std=c++11", "-Wno-deprecated", "-Wno-write-strings",
                    "-I" + str(ROOT / "src"), str(source), "-o", str(executable)], check=True)
    subprocess.run([str(executable)], cwd=root / "area", check=True)
