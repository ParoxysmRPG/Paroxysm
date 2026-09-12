#ifndef HAVEN_REWARD_COLORS_H
#define HAVEN_REWARD_COLORS_H

#include <cstdio>
#include <cstring>
#include <string>

namespace haven {
// Zero means default; 1..256 represent xterm colors 0..255.
inline bool parse_reward_color(const char *text, int &stored) {
  if (!std::strcmp(text, "default")) {
    stored = 0;
    return true;
  }
  size_t length = std::strlen(text);
  if (length < 1 || length > 3)
    return false;
  int value = 0;
  for (size_t i = 0; i < length; ++i) {
    if (text[i] < '0' || text[i] > '9')
      return false;
    value = value * 10 + text[i] - '0';
  }
  if (value > 255)
    return false;
  stored = value + 1;
  return true;
}

inline std::string reward_color(int stored, const char *fallback) {
  if (stored < 1 || stored > 256)
    return fallback;
  char code[5];
  std::snprintf(code, sizeof(code), "`%03d", stored - 1);
  return code;
}

inline std::string emote_quote_colors(const char *text, int stored) {
  std::string result;
  bool quoted = false;
  for (; *text; ++text) {
    if (*text == '"') {
      if (quoted)
        result += "`x\"";
      else
        result += "\"" + reward_color(stored, "`o");
      quoted = !quoted;
    }
    else
      result += *text;
  }
  if (quoted)
    result += "`x\"";
  return result;
}
}
#endif
