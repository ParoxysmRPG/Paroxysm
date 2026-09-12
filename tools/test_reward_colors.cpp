#include "reward_colors.h"
#include <cassert>

int main() {
  int color = 99;
  for (const char *bad : {"", "-1", "+1", "256", "999999999999", "1x", "12 34", "`123"}) {
    assert(!haven::parse_reward_color(bad, color));
    assert(color == 99);
  }
  assert(haven::parse_reward_color("0", color) && color == 1);
  assert(haven::reward_color(color, "`x") == "`000");
  assert(haven::parse_reward_color("9", color) && color == 10);
  assert(haven::reward_color(color, "`x") == "`009");
  assert(haven::parse_reward_color("255", color) && color == 256);
  assert(haven::reward_color(color, "`x") == "`255");
  assert(haven::parse_reward_color("default", color) && color == 0);
  assert(haven::reward_color(color, "`o") == "`o");
  assert(haven::reward_color(1000, "`o") == "`o");
  assert(haven::emote_quote_colors("waves.", 10) == "waves.");
  assert(haven::emote_quote_colors("says \"Hello\" and \"bye\".", 10)
         == "says \"`009Hello`x\" and \"`009bye`x\".");
  assert(haven::emote_quote_colors("says \"Hello", 10) == "says \"`009Hello`x\"");
  assert(haven::emote_quote_colors("says \"Hello\".", 0) == "says \"`oHello`x\".");
}
