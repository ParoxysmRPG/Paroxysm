#ifndef HAVEN_SOCIAL_LOOKUP_H
#define HAVEN_SOCIAL_LOOKUP_H

#include <string>
#include <unordered_map>

namespace haven {
// Scoped to one social update: names/vector order cannot change during its
// eligibility checks. emplace retains the original first-match semantics.
class SocialLookup {
    std::unordered_map<std::string, PROFILE_TYPE *> profiles_;
    std::unordered_map<std::string, MATCH_TYPE *> matches_;
    static std::string name_key(const char *name) {
        std::string key(name ? name : "");
        for (char &ch : key) if (ch >= 'A' && ch <= 'Z') ch += 'a' - 'A';
        return key;
    }
    static std::string pair_key(const char *one, const char *two) {
        std::string a = name_key(one), b = name_key(two);
        if (b < a) a.swap(b);
        return a + '\n' + b;
    }
public:
    SocialLookup(const std::vector<PROFILE_TYPE *> &profiles,
                 const std::vector<MATCH_TYPE *> &matches) {
        profiles_.reserve(profiles.size());
        matches_.reserve(matches.size());
        for (auto *p : profiles) if (p) profiles_.emplace(name_key(p->name), p);
        for (auto *m : matches) if (m) matches_.emplace(pair_key(m->nameone, m->nametwo), m);
    }
    PROFILE_TYPE *profile(const char *name) const {
        auto it = profiles_.find(name_key(name));
        return it == profiles_.end() ? nullptr : it->second;
    }
    MATCH_TYPE *match(const char *one, const char *two) const {
        auto it = matches_.find(pair_key(one, two));
        return it == matches_.end() ? nullptr : it->second;
    }
};
}
#endif
