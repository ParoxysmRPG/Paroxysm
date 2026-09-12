#include "merc.h"
#include "performance.h"
#include <algorithm>
#include <cstdlib>
#include <map>
#include <string>

namespace haven {
struct Timing {
    unsigned long calls = 0;
    double total = 0;
    double maximum = 0;
};
static std::map<std::string, Timing> timings;

void record_duration(const char *name, double milliseconds) {
    Timing &t = timings[name];
    ++t.calls;
    t.total += milliseconds;
    t.maximum = std::max(t.maximum, milliseconds);
}

void report_performance() {
    static auto last_report = SteadyClock::now();
    const auto now = SteadyClock::now();
    if (now - last_report < std::chrono::seconds(60))
        return;
    const char *setting = std::getenv("HAVEN_PROFILE");
    const bool enabled = setting && setting[0] == '1';
    for (const auto &entry : timings) {
        const Timing &t = entry.second;
        // Always report stalls; detailed statistics are opt-in.
        if (t.calls && (enabled || t.maximum >= 250.0)) {
            char message[256];
            snprintf(message, sizeof(message),
                "PERF %s: calls=%lu total_ms=%.3f mean_ms=%.3f max_ms=%.3f",
                entry.first.c_str(), t.calls, t.total, t.total / t.calls, t.maximum);
            log_string(message);
        }
    }
    timings.clear();
    last_report = now;
}
}
