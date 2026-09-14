#!/usr/bin/env python3
"""Exercise production combat maps with real engine structures and fixture rooms.

Run in Linux/WSL: python3 tools/run_combat_map_tests.py [--sanitize]
The snapshot module is compiled directly. Whole coordinate, map visibility,
terrain/draw, scan and POI-cell functions are extracted from their production
files, so this suite cannot silently keep testing a copied implementation.
External world/path/lighting helpers are instrumented fixtures. No game data is
loaded, no server is started, and no world/player/account files are changed.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def section(text, start, end):
    offset = text.index(start)
    return text[offset:text.index(end, offset)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    fight = (ROOT / 'src/fight.c').read_text()
    clans = (ROOT / 'src/clans.c').read_text()
    # Count calls without replacing the actual smoke/concealment predicates.
    visibility = section(fight, '  bool can_map_see(', '  int maptox(')
    visibility = visibility.replace('bool can_map_see(', 'bool fixture_can_map_see(', 1)
    path_helpers = section(fight, '  static bool get_to_path_impl(', '  void fall_character(')
    path_helpers = path_helpers.replace('bool can_get_to(', 'bool fixture_can_get_to(', 1)
    path_helpers = path_helpers.replace('bool can_get_to_for_map(', 'bool fixture_can_get_to_for_map(', 1)
    production = (
        section(fight, '  int relative_x(CHAR_DATA *ch,', '  int init_combat_distance(')
        + section(fight, '  int setup_expand(int number)', '  int default_mapsize(')
        + section(fight, '  bool is_in_cover(', '  void explode_grenade(')
        + visibility
        + section(fight, '  int maptox(', '  void init_map(')
        + section(fight, '  void scan_fight(CHAR_DATA *ch, bool', '  int dam_type_mod(')
        + section(fight, '  char *battleflags(CHAR_DATA *ch,', '  _DOFUN(do_diminish)')
        + path_helpers
        + section(clans, '  static int operation_poi_index(', '  int poidistance(')
    )
    fixture = (ROOT / 'tools/test_combat_map.cpp').read_text()
    assert fixture.count('// PRODUCTION_FUNCTIONS') == 1
    fixture = fixture.replace('// PRODUCTION_FUNCTIONS', 'extern "C" {\n' + production + '\n}')
    flags = (['-O1', '-g', '-fsanitize=address,undefined',
              '-fno-omit-frame-pointer'] if args.sanitize else ['-O2', '-g'])
    with tempfile.TemporaryDirectory(prefix='paroxysm-combat-map-') as directory:
        source = Path(directory) / 'combat-map-fixture.cpp'
        binary = Path(directory) / 'combat-map-test'
        source.write_text(fixture)
        subprocess.run([
            'g++', '-std=gnu++17', '-Wall', '-Wextra', '-Wno-deprecated',
            '-Wno-write-strings', '-Wno-unused-parameter', *flags,
            '-I' + str(ROOT / 'src'), str(source),
            str(ROOT / 'src/combat_map.cc'), str(ROOT / 'src/local_map.cc'),
            '-o', str(binary),
        ], check=True)
        environment = dict(os.environ)
        if args.sanitize:
            environment.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',
                               UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        subprocess.run([str(binary)], cwd=directory, env=environment,
                       check=True, timeout=45)


if __name__ == '__main__':
    main()
