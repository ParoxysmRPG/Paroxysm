#ifndef HAVEN_PERFORMANCE_H
#define HAVEN_PERFORMANCE_H

#include <chrono>

namespace haven {
using SteadyClock = std::chrono::steady_clock;
void record_duration(const char *name, double milliseconds);
void report_performance();

class ScopedTimer {
    const char *name_;
    SteadyClock::time_point start_;
public:
    explicit ScopedTimer(const char *name) : name_(name), start_(SteadyClock::now()) {}
    ~ScopedTimer() {
        record_duration(name_, std::chrono::duration<double, std::milli>(
            SteadyClock::now() - start_).count());
    }
    ScopedTimer(const ScopedTimer &) = delete;
    ScopedTimer &operator=(const ScopedTimer &) = delete;
};
}
#endif
