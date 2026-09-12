#ifndef HAVEN_SPY_CAMERA_H
#define HAVEN_SPY_CAMERA_H

#include "merc.h"
#include "olc.h"
#include <cerrno>
#include <cctype>
#include <climits>
#include <cstdlib>
#include <sstream>
#include <string>

namespace haven {

// Permanent location restrictions apply both when planting and recording.
inline bool camera_room_supported(ROOM_INDEX_DATA *room) {
  return room && room->area && room->area->vnum != 1 && room->area->vnum != 12
      && in_haven(room) && !public_room(room) && !room_in_school(room->vnum);
}

inline int camera_lifetime_hours(int hacking) {
  return 7 * 24 * UMAX(1, UMIN(5, hacking));
}

inline bool camera_decimal(const std::string &text, long long &value) {
  if (text.empty() || text.find_first_not_of("0123456789") != std::string::npos) return false;
  errno = 0;
  value = std::strtoll(text.c_str(), NULL, 10);
  return errno != ERANGE;
}

// Persist number:expiry:planter (Unix seconds) in the existing !bugs field.
inline bool camera_token(const std::string &token, int &number, long long &expiry, std::string &owner) {
  const size_t colon = token.find(':');
  const size_t owner_colon = colon == std::string::npos ? colon : token.find(':', colon + 1);
  long long parsed;
  if (!camera_decimal(token.substr(0, colon), parsed) || parsed < 100 || parsed > INT_MAX) return false;
  number = static_cast<int>(parsed);
  expiry = 0;
  owner = owner_colon == std::string::npos ? "" : token.substr(owner_colon + 1);
  if (owner_colon != std::string::npos && (owner.empty() || owner.size() >= MAX_INPUT_LENGTH
      || owner.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") != std::string::npos)) return false;
  return colon == std::string::npos || (camera_decimal(token.substr(colon + 1,
      owner_colon == std::string::npos ? owner_colon : owner_colon - colon - 1), expiry) && expiry > 0);
}

inline EXTRA_DESCR_DATA *camera_links(ROOM_INDEX_DATA *room, bool destroy = false) {
  if (!room) return NULL;
  for (EXTRA_DESCR_DATA *ed = room->extra_descr; ed; ed = ed->next) {
    if (!is_name("!bugs", ed->keyword)) continue;
    std::istringstream input(ed->description ? ed->description : "");
    std::string token, live;
    struct Notice { int number; std::string owner; bool expired; };
    std::vector<Notice> notices;
    while (input >> token) {
      int number;
      long long expiry;
      std::string owner;
      if (!camera_token(token, number, expiry, owner)) continue;
      // Old installations have no planter skill. Give them a baseline lifetime
      // on first access and save it, so subsequent restarts cannot reset it.
      if (!expiry) expiry = static_cast<long long>(current_time) + camera_lifetime_hours(0) * 3600;
      if (expiry <= static_cast<long long>(current_time) || destroy) {
        notices.push_back({number, owner, expiry <= static_cast<long long>(current_time)});
        continue;
      }
      if (!live.empty()) live += ' ';
      live += std::to_string(number) + ":" + std::to_string(expiry);
      if (!owner.empty()) live += ":" + owner;
    }
    if (!ed->description || live != ed->description) {
      free_string(ed->description);
      ed->description = str_dup(live.c_str());
      if (room->area) SET_BIT(room->area->area_flags, AREA_CHANGED);
    }
    // Commit removal first: a second sweep or tick must not repeat a notice.
    for (const auto &notice : notices)
      camera_notify(room, notice.number, notice.owner.c_str(), notice.expired);
    return ed;
  }
  return NULL;
}

// is_name accepts prefixes: phone 123 must never receive phone 1234's feed.
inline bool camera_linked(EXTRA_DESCR_DATA *ed, int number) {
  if (!ed || !ed->description || number < 100) return false;
  std::istringstream input(ed->description);
  std::string token;
  while (input >> token) {
    int linked_number;
    long long expiry;
    std::string owner;
    if (camera_token(token, linked_number, expiry, owner) && linked_number == number
        && expiry > static_cast<long long>(current_time)) return true;
  }
  return false;
}

} // namespace haven
#endif
