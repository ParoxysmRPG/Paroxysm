#ifndef HAVEN_TEXT_FORMAT_H
#define HAVEN_TEXT_FORMAT_H

#include <cstdarg>
#include <cstdio>
#include <stdexcept>
#include <string>

namespace haven {
// Size formatted text before writing it, preserving complete messages and names.
inline std::string format_text(const char *format, ...)
    __attribute__((format(printf, 1, 2)));

inline std::string vformat_text(const char *format, va_list args) {
    va_list measure;
    va_copy(measure, args);
    const int size = std::vsnprintf(nullptr, 0, format, measure);
    va_end(measure);
    if (size < 0) {
        throw std::runtime_error("Cannot format game text");
    }
    std::string text(static_cast<std::size_t>(size), '\0');
    const int written = std::vsnprintf(text.data(), text.size() + 1, format, args);
    if (written != size)
        throw std::runtime_error("Cannot format game text");
    return text;
}

inline std::string format_text(const char *format, ...) {
    va_list args;
    va_start(args, format);
    try {
        std::string text = vformat_text(format, args);
        va_end(args);
        return text;
    } catch (...) {
        va_end(args);
        throw;
    }
}
}

#endif
