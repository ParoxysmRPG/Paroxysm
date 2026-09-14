#!/usr/bin/env python3
"""Compile and test the production local mapper against instrumented visibility.

Run on Linux/WSL: python3 tools/run_local_map_integration.py [--sanitize]
The actual engine structures and renderer are used. No world is booted, and no
world, player, or account files are read or changed. The two visibility/trust
helpers are controlled fixtures so hidden rooms and traversal cost are testable.
"""
from pathlib import Path
import argparse
import os
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


COMMAND_STUBS = r'''
#include "merc.h"
#include "local_map.h"
#include <cassert>
#include <cstring>
#include <memory>
#include <strings.h>

static bool fighting = false, dreaming = false, sleeping = false;
static bool blind = false, dark = false, nightvision = false;
static int maps = 0, tactics = 0, helps = 0;
static std::string output;
namespace haven {
std::string render_local_map(CHAR_DATA *, ROOM_INDEX_DATA *, bool compact,
                             LocalMapStats *) {
    assert(!compact);
    ++maps;
    return "LOCAL MAP";
}
}
extern "C" {
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
char *one_argument(char *input, char *word) {
    while (*input == ' ') ++input;
    while (*input && *input != ' ') *word++ = *input++;
    *word = '\0';
    while (*input == ' ') ++input;
    return input;
}
bool in_fight(CHAR_DATA *) { return fighting; }
bool is_dreaming(CHAR_DATA *) { return dreaming; }
bool is_asleep(CHAR_DATA *) { return sleeping; }
bool check_blind(CHAR_DATA *) { return !blind; }
bool is_dark(ROOM_INDEX_DATA *) { return dark; }
bool can_see_dark(CHAR_DATA *) { return nightvision; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void do_help(CHAR_DATA *, char *argument) {
    assert(!strcmp(argument, fighting ? "combat map" : "map")); ++helps;
}
void do_function(CHAR_DATA *ch, DO_FUN *function, char *argument) {
    function(ch, argument);
}
int default_mapsize(CHAR_DATA *) { return 33; }
void draw_map(CHAR_DATA *, int size) { assert(size == 33); ++tactics; }
}
'''

COMMAND_TESTS = r'''
int main() {
    std::unique_ptr<CHAR_DATA> ch(new CHAR_DATA{});
    std::unique_ptr<PC_DATA> pc(new PC_DATA{});
    ROOM_INDEX_DATA room = {};
    DESCRIPTOR_DATA descriptor = {};
    ch->pcdata = pc.get();
    ch->in_room = &room;
    ch->desc = &descriptor;
    room.size = 5;
    auto command = [&](const char *text) {
        maps = tactics = helps = 0; output.clear(); ch->wait = 0;
        char argument[MAX_INPUT_LENGTH];
        strcpy(argument, text);
        do_map(ch.get(), argument);
    };
    command("");
    assert(maps == 1 && tactics == 0 && ch->wait == 0 && output == "LOCAL MAP");
    command("local"); assert(maps == 1 && ch->wait == 0);
    command("combat"); assert(maps == 0 && tactics == 0 && !output.empty());
    for (const char *help : {"help", "key", "legend"}) {
        command(help); assert(helps == 1 && maps == 0 && tactics == 0);
    }
    command("invalid"); assert(maps == 0 && output.find("Syntax") != std::string::npos);
    command("local extra"); assert(maps == 0 && output.find("Syntax") != std::string::npos);
    assert(!IS_FLAG(ch->comm, COMM_NOMINIMAP));
    command("off");
    assert(IS_FLAG(ch->comm, COMM_NOMINIMAP));
    assert(maps == 0 && tactics == 0 && ch->wait == 0 && !output.empty());
    command("off"); assert(IS_FLAG(ch->comm, COMM_NOMINIMAP));
    for (const char *malformed : {"on extra", "off extra", "toggle extra"}) {
        command(malformed);
        assert(IS_FLAG(ch->comm, COMM_NOMINIMAP));
        assert(maps == 0 && tactics == 0 && ch->wait == 0);
        assert(output.find("Syntax") != std::string::npos);
    }
    command(""); assert(maps == 1 && ch->wait == 0);
    command("local"); assert(maps == 1 && ch->wait == 0);
    command("toggle"); assert(!IS_FLAG(ch->comm, COMM_NOMINIMAP));
    command("toggle"); assert(IS_FLAG(ch->comm, COMM_NOMINIMAP));
    command("on"); assert(!IS_FLAG(ch->comm, COMM_NOMINIMAP));
    command("on"); assert(!IS_FLAG(ch->comm, COMM_NOMINIMAP));
    fighting = true;
    command("off");
    assert(IS_FLAG(ch->comm, COMM_NOMINIMAP));
    assert(maps == 0 && tactics == 0 && ch->wait == 0);
    for (const char *help : {"help", "key", "legend"}) {
        command(help); assert(helps == 1 && maps == 0 && tactics == 0 && ch->wait == 0);
    }
    command(""); assert(tactics == 1 && maps == 0 && ch->wait == PULSE_PER_SECOND * 3);
    command("combat"); assert(tactics == 1 && maps == 0);
    command("local"); assert(tactics == 0 && maps == 1 && ch->wait == 0);
    command("toggle");
    assert(!IS_FLAG(ch->comm, COMM_NOMINIMAP));
    assert(maps == 0 && tactics == 0 && ch->wait == 0);
    fighting = false;
    for (bool *blocked : {&dreaming, &sleeping, &blind, &dark}) {
        *blocked = true;
        command(""); assert(maps == 0 && tactics == 0);
        *blocked = false;
    }
    dark = nightvision = true;
    command(""); assert(maps == 1);
    dark = nightvision = false;
    ch->act[PLR_DEEPSHROUD / UL_BITS] |= 1UL << (PLR_DEEPSHROUD % UL_BITS);
    command(""); assert(maps == 0);
    ch->act[PLR_DEEPSHROUD / UL_BITS] &= ~(1UL << (PLR_DEEPSHROUD % UL_BITS));
    ch->act[ACT_IS_NPC / UL_BITS] |= 1UL << (ACT_IS_NPC % UL_BITS);
    command(""); assert(maps == 0);
    ch->act[ACT_IS_NPC / UL_BITS] &= ~(1UL << (ACT_IS_NPC % UL_BITS));
    ch->desc = nullptr;
    command(""); assert(maps == 0);
    ch->desc = &descriptor;
    ch->in_room = nullptr;
    command(""); assert(maps == 0);
    puts("PASS: map routes/help, look-only on/off/toggle, unchanged combat delay, malformed options and sight/state guards.");
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    flags = (['-O1', '-g', '-fsanitize=address,undefined',
              '-fno-omit-frame-pointer'] if args.sanitize else ['-O2', '-g'])
    with tempfile.TemporaryDirectory(prefix='paroxysm-local-map-') as directory:
        binary = Path(directory) / 'local-map-test'
        subprocess.run([
            'g++', '-std=gnu++11', '-Wall', '-Wextra', '-Wno-deprecated',
            '-Wno-write-strings', *flags, '-I' + str(ROOT / 'src'),
            str(ROOT / 'tools' / 'test_local_map.cpp'),
            str(ROOT / 'src' / 'local_map.cc'), '-o', str(binary),
        ], check=True)
        environment = dict(os.environ)
        if args.sanitize:
            environment.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',
                               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        subprocess.run([str(binary)], cwd=directory, env=environment,
                       check=True, timeout=45)
        # Extract the whole production command, not a copied implementation.
        fight = (ROOT / 'src' / 'fight.c').read_text()
        start = fight.index('  _DOFUN(do_map) {')
        end = fight.index('  _DOFUN(do_knockout)', start)
        command_source = Path(directory) / 'map-command.cpp'
        command_source.write_text(COMMAND_STUBS + '\n' + fight[start:end] +
                                  '\n' + COMMAND_TESTS)
        command_binary = Path(directory) / 'map-command-test'
        subprocess.run([
            'g++', '-std=gnu++11', '-Wall', '-Wextra', '-Wno-deprecated',
            '-Wno-write-strings', *flags, '-I' + str(ROOT / 'src'),
            str(command_source), '-o', str(command_binary),
        ], check=True)
        subprocess.run([str(command_binary)], cwd=directory, env=environment,
                       check=True, timeout=10)


if __name__ == '__main__':
    main()
