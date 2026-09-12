#ifndef HAVEN_AI_PROTOCOL_H
#define HAVEN_AI_PROTOCOL_H
#include <climits>
#include <string>
#include <vector>

namespace haven {
inline bool ai_integer(const std::string &value, int low, int high) {
    if (value.empty()) return false;
    long long number = 0;
    for (char ch : value) {
        if (ch < '0' || ch > '9') return false;
        number = number * 10 + ch - '0';
        if (number > high) return false;
    }
    return number >= low;
}
inline bool ai_name(const std::string &value) {
    if (value.empty() || value.size() > 64) return false;
    for (char ch : value)
        if (!((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z'))) return false;
    return true;
}
inline bool valid_ai_fields(const std::vector<std::string> &v, int expected = 0) {
    if (v.empty() || !ai_integer(v[0], 1, 6)) return false;
    const int type = std::stoi(v[0]);
    const size_t sizes[] = {0, 3, 6, 4, 6, 4, 11};
    if ((expected && type != expected) ||
        (v.size() != sizes[type] && !(type == 2 && v.size() == 9))) return false;
    for (const auto &field : v)
        if (field.size() > 16000 || field.find('\0') != std::string::npos ||
            field.find('~') != std::string::npos) return false;
    switch (type) {
    case 1: return ai_integer(v[1], 1, INT_MAX) && !v[2].empty();
    case 2: return !v[1].empty() && !v[2].empty() && !v[3].empty() && !v[4].empty() &&
        v[5].size() >= 10 && (v.size() == 6 || (ai_integer(v[6], 0, INT_MAX) &&
        ai_integer(v[7], 1, INT_MAX) && ai_integer(v[8], 0, INT_MAX)));
    case 3: return ai_name(v[1]) && ai_integer(v[2], 0, 36500) && !v[3].empty();
    case 4: return ai_name(v[1]) && ai_name(v[3]) && ai_integer(v[2], 0, 100) && ai_integer(v[4], 0, 100);
    case 5: return !v[1].empty() && !v[3].empty();
    case 6: return ai_name(v[1]) && ai_name(v[2]) && !v[3].empty() && !v[4].empty() &&
        !v[5].empty() && ai_integer(v[8], 1, 10) && ai_integer(v[9], 0, 11);
    }
    return false;
}
bool parse_ai_record(const std::string &input, std::vector<std::string> &fields);

}
#endif
