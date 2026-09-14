#ifndef HAVEN_GAME_TIME_H
#define HAVEN_GAME_TIME_H

#include <ctime>
#include <string>

namespace haven {
// The scheduler uses a fixed UTC-5 clock. Never apply the host's timezone or
// daylight saving rules to game time; jetlag and location offsets are relative
// to this clock.
inline std::tm game_time_fields(std::time_t timestamp, int offset_hours = 0) {
  timestamp += (static_cast<std::time_t>(offset_hours) - 5) * 3600;
  return *std::gmtime(&timestamp);
}

inline std::string format_game_time(std::time_t timestamp, int offset_hours = 0) {
  std::tm fields = game_time_fields(timestamp, offset_hours);
  return std::asctime(&fields);
}

inline std::time_t operation_departure_time(std::time_t now, int hour, int day) {
  const std::tm fields = game_time_fields(now);
  // day counts future occurrences of the departure hour, not midnights.
  return now - fields.tm_sec - fields.tm_min * 60 - fields.tm_hour * 3600
      + hour * 3600 + (static_cast<std::time_t>(day) + (fields.tm_hour >= hour)) * 86400;
}
}

#endif
