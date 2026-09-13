#!/usr/bin/env python3
"""WSL/Linux: sanitizer checks for production lookup, aliases and edit distance."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
interp = (ROOT / "src/interp.c").read_text()


def section(start, end):
    offset = interp.index(start)
    return interp[offset:interp.index(end, offset)]


source = r'''
#include "merc.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <random>
CMD_TYPE *command_hash[MAX_COMMAND_HASH] = {};
std::vector<char *> allocations;
std::string output, dispatched;
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
bool str_cmp(const char *a, const char *b) { return strcasecmp(a, b) != 0; }
bool str_prefix(const char *a, const char *b) { return strncasecmp(a, b, strlen(a)) != 0; }
char *str_dup(const char *s) { char *p = strdup(s); allocations.push_back(p); return p; }
void free_string(char *) {} // Release the test arena at the end.
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void smash_tilde(char *s) { for (; *s; ++s) if (*s == '~') *s = '-'; }
char *one_argument(char *s, char *word) {
  while (*s == ' ') ++s;
  while (*s && *s != ' ') { *word++ = LOWER(*s); ++s; }
  *word = '\0'; while (*s == ' ') ++s; return s;
}
void interpret(CHAR_DATA *, char *s) { dispatched = s; }
void probe(CHAR_DATA *, char *) {}
int minimum(int a, int b, int c) { return std::min(a, std::min(b, c)); }
'''
source += section("  static CMD_TYPE *lookup_command(", "#define MAX_ABIL_NAMES")
source += section("  CMD_TYPE *find_command(", "  /**************************************************************************")
source += section("  int levenshtein_distance(char *s, char *t)", "  int minimum(int a,")
source += (ROOT / "src/alias.c").read_text()
source += r'''
int reference(const std::string &a, const std::string &b) {
  if (a.empty() || b.empty()) return -1;
  std::vector<std::vector<int>> d(a.size() + 1, std::vector<int>(b.size() + 1));
  for (size_t i = 0; i <= a.size(); ++i) d[i][0] = i;
  for (size_t j = 0; j <= b.size(); ++j) d[0][j] = j;
  for (size_t i = 1; i <= a.size(); ++i)
    for (size_t j = 1; j <= b.size(); ++j)
      d[i][j] = minimum(d[i-1][j] + 1, d[i][j-1] + 1,
                        d[i-1][j-1] + (a[i-1] != b[j-1]));
  return d[a.size()][b.size()];
}
int main() {
  std::mt19937 rng(713);
  for (int trial = 0; trial < 3000; ++trial) {
    std::string a(rng() % 50, 'a'), b(rng() % 50, 'a');
    for (char &c : a) c += rng() % 5;
    for (char &c : b) c += rng() % 5;
    assert(levenshtein_distance(a.data(), b.data()) == reference(a, b));
    assert(levenshtein_distance(b.data(), a.data()) == reference(a, b));
  }
  std::string long_input(5999, 'x'), short_input = "attack";
  assert(levenshtein_distance(long_input.data(), short_input.data()) == 5999);
  assert(levenshtein_distance(nullptr, short_input.data()) == -1);
  for (int byte = 128; byte <= 255; ++byte) {
    char input[] = {static_cast<char>(byte), '\0'};
    assert(!lookup_command(input, MAX_LEVEL));
    assert(!find_command(input));
  }
  CMD_TYPE prefix = {}, exact = {}, unavailable = {};
  prefix.name = (char *)"society"; prefix.do_fun = probe;
  exact.name = (char *)"s"; exact.do_fun = probe;
  unavailable.name = (char *)"southmissing";
  prefix.next = &unavailable; unavailable.next = &exact;
  command_hash['s' % MAX_COMMAND_HASH] = &prefix;
  assert(lookup_command("s", 1) == &exact);
  assert(lookup_command("so", 1) == &prefix);
  assert(lookup_command("southmissing", 1) == &unavailable);
  assert(!lookup_command("southm", 1));
  exact.level = MAX_LEVEL;
  assert(lookup_command("s", 1) == &prefix);

  CHAR_DATA ch = {}; PC_DATA pc = {}; DESCRIPTOR_DATA descriptor = {};
  ch.pcdata = &pc; ch.desc = &descriptor; descriptor.character = &ch;
  ch.prefix = (char *)""; ch.trust = ch.level = 1;
  char trigger[] = "jemhack86";
  do_alias(&ch, trigger);
  assert(ch.trust == 1 && ch.level == 1);
  char definition[] = "hit attack target";
  do_alias(&ch, definition);
  char invocation[] = "hit knockout";
  substitute_alias(&descriptor, invocation);
  assert(dispatched == "attack target knockout");
  char removal[] = "hit";
  do_unalias(&ch, removal);
  assert(!pc.alias[0] && !pc.alias_sub[0]);
  for (char *p : allocations) free(p);
  puts("PASS: aliases cannot grant privileges; command hash accepts all input bytes; 6,000 edit-distance comparisons match reference.");
}
'''
with tempfile.TemporaryDirectory(prefix="command-safety-") as temporary:
    cpp, binary = Path(temporary) / "test.cpp", Path(temporary) / "test"
    cpp.write_text(source)
    subprocess.run(["g++", "-std=gnu++17", "-g", "-Wno-deprecated", "-Wno-write-strings",
                    "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-no-pie",
                    "-I" + str(ROOT / "src"), str(cpp), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
