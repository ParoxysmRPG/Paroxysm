// Built by run_combat_map_tests.py, with whole production functions inserted.
#include "merc.h"
#include "combat_map.h"
#include "local_map.h"
#include "text_format.h"
#include <array>
#include <cassert>
#include <cstdarg>
#include <cmath>
#include <cstring>
#include <deque>
#include <memory>
#include <set>
#include <sstream>
#include <tuple>
#include <unordered_map>

CharList char_list;
const char *dir_name[][2] = {
    {"north", "N"}, {"east", "E"}, {"south", "S"}, {"west", "W"},
    {"up", "U"}, {"down", "D"}, {"northeast", "NE"}, {"northwest", "NW"},
    {"southeast", "SE"}, {"southwest", "SW"}
};
int map_translation[50];
static std::string output;
static std::set<CHAR_DATA *> hidden, gms, ghosts, possessing;
static std::set<std::pair<CHAR_DATA *, CHAR_DATA *>> aggression;
static std::set<ROOM_INDEX_DATA *> unreachable, darkness, public_rooms, unseen;
static std::map<CHAR_DATA *, std::set<int>> affects;
static std::map<CHAR_DATA *, int> sight_calls, map_sight_calls, name_calls, roster_name_calls;
static std::map<ROOM_INDEX_DATA *, int> path_calls, light_calls, room_sight_calls;
static std::map<std::tuple<int, int, int>, ROOM_INDEX_DATA *> coordinates;
static std::vector<OperationPoiPosition> objectives;
static int poi_snapshots = 0, poi_rosters = 0, room_lookups = 0, clairvoyance = 0;
static bool cone_visible = true;
static bool real_path_helpers = false, fixture_flying = false;

extern "C" {
bool fixture_can_map_see(CHAR_DATA *, CHAR_DATA *);
static bool fixture_can_get_to_for_map(CHAR_DATA *, ROOM_INDEX_DATA *);
bool is_gm(CHAR_DATA *ch) { return gms.count(ch) != 0; }
bool in_fight(CHAR_DATA *ch) { return ch && ch->fighting; }
bool same_fight(CHAR_DATA *a, CHAR_DATA *b) { return in_fight(a) && in_fight(b); }
bool can_see(CHAR_DATA *, CHAR_DATA *ch) { return hidden.count(ch) == 0; }
bool can_see_char_distance(CHAR_DATA *, CHAR_DATA *ch, int range) {
    assert(range == DISTANCE_MEDIUM);
    ++sight_calls[ch];
    return hidden.count(ch) == 0;
}
bool can_map_see(CHAR_DATA *viewer, CHAR_DATA *ch) {
    ++map_sight_calls[ch];
    return fixture_can_map_see(viewer, ch);
}
bool has_caff(CHAR_DATA *ch, int flag) { return affects[ch].count(flag) != 0; }
bool is_ghost(CHAR_DATA *ch) { return ghosts.count(ch) != 0; }
bool is_possessing(CHAR_DATA *ch) { return possessing.count(ch) != 0; }
int get_skill(CHAR_DATA *, int skill) { return skill == SKILL_CLAIRVOYANCE ? clairvoyance : 0; }
int get_dist(int x1, int y1, int x2, int y2) {
    return static_cast<int>(std::hypot(x1 - x2, y1 - y2));
}
int combat_distance(CHAR_DATA *a, CHAR_DATA *b, bool) {
    return get_dist(0, 0, relative_x(a, b->in_room, b->x), relative_y(a, b->in_room, b->y));
}
char *PERS(CHAR_DATA *ch, CHAR_DATA *) { ++name_calls[ch]; return ch->name; }
char *PERS_2(CHAR_DATA *ch, CHAR_DATA *) { return ch->name; }
char *PERS_3(CHAR_DATA *ch, CHAR_DATA *) { ++roster_name_calls[ch]; return ch->name; }
int get_agg(CHAR_DATA *from, CHAR_DATA *to) {
    return aggression.count(std::make_pair(from, to)) ? 10 : 0;
}
bool battleground(ROOM_INDEX_DATA *) { return false; }
void send_to_char(const char *text, CHAR_DATA *) { output += text; }
void printf_to_char(CHAR_DATA *, char *format, ...) {
    va_list args;
    va_start(args, format);
    va_list copy;
    va_copy(copy, args);
    const int length = vsnprintf(nullptr, 0, format, copy);
    va_end(copy);
    assert(length >= 0);
    std::vector<char> buf(length + 1);
    vsnprintf(buf.data(), buf.size(), format, args);
    va_end(args);
    output += buf.data();
}
bool can_get_to(CHAR_DATA *, ROOM_INDEX_DATA *room) {
    ++path_calls[room]; return unreachable.count(room) == 0;
}
static bool can_get_to_for_map(CHAR_DATA *viewer, ROOM_INDEX_DATA *room) {
    if (real_path_helpers) {
        ++path_calls[room]; return fixture_can_get_to_for_map(viewer, room);
    }
    return can_get_to(viewer, room);
}
bool water_breathe(CHAR_DATA *) { return false; }
bool is_combat_flyer(CHAR_DATA *) { return fixture_flying; }
bool is_combat_jumper(CHAR_DATA *) { return false; }
bool is_animal(CHAR_DATA *) { return false; }
int animal_size(int) { return 0; }
int get_animal_weight(CHAR_DATA *, int) { return 0; }
bool guestmonster(CHAR_DATA *) { return false; }
bool in_lodge(ROOM_INDEX_DATA *) { return false; }
PROP_TYPE *prop_from_room(ROOM_INDEX_DATA *) { return nullptr; }
bool no_deep_access(ROOM_INDEX_DATA *, ROOM_INDEX_DATA *) { return false; }
int fight_path(ROOM_INDEX_DATA *from, ROOM_INDEX_DATA *to) {
    for (int direction = 0; direction < MAX_DIR; ++direction)
        if (from->exit[direction] && from->exit[direction]->u1.to_room == to) return direction;
    return -1;
}
bool is_dark(ROOM_INDEX_DATA *room) { ++light_calls[room]; return darkness.count(room) != 0; }
bool public_room(ROOM_INDEX_DATA *room) { return public_rooms.count(room) != 0; }
bool can_see_room(CHAR_DATA *, ROOM_INDEX_DATA *room) {
    ++room_sight_calls[room]; return unseen.count(room) == 0;
}
int get_trust(CHAR_DATA *ch) { return ch->level; }
bool invisioncone_coordinates(CHAR_DATA *, int, int) { return cone_visible; }
ROOM_INDEX_DATA *sourced_room_by_coordinates(ROOM_INDEX_DATA *, int x, int y, int z, bool) {
    ++room_lookups;
    const auto found = coordinates.find(std::make_tuple(x, y, z));
    return found == coordinates.end() ? nullptr : found->second;
}
int operation_poi_positions(CHAR_DATA *, OperationPoiPosition *points) {
    ++poi_snapshots;
    assert(objectives.size() <= 10);
    std::copy(objectives.begin(), objectives.end(), points);
    return static_cast<int>(objectives.size());
}
void displaypois(CHAR_DATA *) { ++poi_rosters; }
}

// PRODUCTION_FUNCTIONS

static std::string plain(const std::string &text) {
    std::string result;
    for (size_t i = 0; i < text.size(); ++i) {
        if (text[i] == '<') {
            size_t end = i + 1;
            if (end < text.size() && text[end] == '/') ++end;
            if (end + 1 < text.size() &&
                std::string("bBiIuU").find(text[end]) != std::string::npos &&
                text[end + 1] == '>') {
                i = end + 1;
                continue;
            }
        }
        if (text[i] == '`' && i + 1 < text.size()) {
            if (text[++i] == '`') result += '`';
        } else if (text[i] != '\r') result += text[i];
    }
    return result;
}

static int occurrences(const std::string &text, const std::string &needle) {
    int count = 0;
    for (size_t pos = 0; (pos = text.find(needle, pos)) != std::string::npos; pos += needle.size()) ++count;
    return count;
}

static void clear_counts() {
    sight_calls.clear(); map_sight_calls.clear(); name_calls.clear(); roster_name_calls.clear();
    path_calls.clear(); light_calls.clear(); room_sight_calls.clear();
    poi_snapshots = poi_rosters = room_lookups = 0;
    output.clear();
}

struct Fixture {
    AREA_DATA area = {};
    std::unique_ptr<CHAR_DATA> viewer{new CHAR_DATA{}};
    std::unique_ptr<PC_DATA> pc{new PC_DATA{}};
    DESCRIPTOR_DATA descriptor = {};
    std::vector<std::unique_ptr<CHAR_DATA>> people;
    std::vector<std::unique_ptr<MOB_INDEX_DATA>> indices;
    std::vector<std::unique_ptr<ROOM_INDEX_DATA>> rooms;
    std::vector<std::unique_ptr<CharList>> room_people;
    std::vector<std::unique_ptr<EXIT_DATA>> exits;
    std::deque<std::string> names;

    Fixture() {
        char_list.clear(); hidden.clear(); gms.clear(); ghosts.clear(); possessing.clear();
        unreachable.clear(); darkness.clear(); public_rooms.clear(); unseen.clear();
        coordinates.clear(); objectives.clear(); affects.clear(); aggression.clear();
        clairvoyance = 0; cone_visible = true;
        real_path_helpers = fixture_flying = false;
        clear_counts();
        area.vnum = 1; area.world = WORLD_EARTH;
        viewer->pcdata = pc.get(); viewer->fighting = true; viewer->desc = &descriptor;
        viewer->name = const_cast<char *>("You");
        viewer->facing = DIR_NORTH; viewer->linewidth = 80;
        viewer->in_room = room();
    }
    ~Fixture() { char_list.clear(); }
    ROOM_INDEX_DATA *room(int x = 0, int y = 0, int z = 0) {
        rooms.emplace_back(new ROOM_INDEX_DATA{});
        room_people.emplace_back(new CharList{});
        auto r = rooms.back().get();
        r->x = x; r->y = y; r->z = z; r->size = 50;
        r->vnum = static_cast<int>(rooms.size()) + 1000;
        r->area = &area; r->sector_type = SECT_STREET;
        r->people = room_people.back().get();
        coordinates[std::make_tuple(x, y, z)] = r;
        return r;
    }
    CHAR_DATA *person(const std::string &name = "a guard", int x = 0, int y = 0,
                      ROOM_INDEX_DATA *where = nullptr) {
        people.emplace_back(new CHAR_DATA{});
        auto ch = people.back().get();
        ch->in_room = where ? where : viewer->in_room;
        ch->x = x; ch->y = y; ch->fighting = true;
        names.push_back(name); ch->name = &names.back()[0];
        char_list.push_back(ch); ch->in_room->people->push_back(ch);
        return ch;
    }
    CHAR_DATA *object(int vnum, int x, int y) {
        auto ch = person("a combat object", x, y);
        indices.emplace_back(new MOB_INDEX_DATA{});
        ch->pIndexData = indices.back().get(); ch->pIndexData->vnum = vnum;
        SET_FLAG(ch->act, ACT_IS_NPC); SET_FLAG(ch->act, ACT_COMBATOBJ);
        return ch;
    }
    CHAR_DATA *cover(const std::string &name = "a barricade", int x = 0, int y = 0,
                     ROOM_INDEX_DATA *where = nullptr) {
        auto ch = person(name, x, y, where);
        indices.emplace_back(new MOB_INDEX_DATA{});
        ch->pIndexData = indices.back().get(); ch->pIndexData->vnum = 110;
        SET_FLAG(ch->act, ACT_IS_NPC); SET_FLAG(ch->act, ACT_COVER);
        return ch;
    }
    EXIT_DATA *link(ROOM_INDEX_DATA *from, int direction, ROOM_INDEX_DATA *to) {
        exits.emplace_back(new EXIT_DATA{});
        auto e = exits.back().get(); e->u1.to_room = to;
        e->orig_door = direction; from->exit[direction] = e;
        return e;
    }
};

static int entry_index(const haven::CombatMapSnapshot &snapshot, CHAR_DATA *ch) {
    for (size_t i = 0; i < snapshot.entries.size(); ++i)
        if (snapshot.entries[i].character == ch) return static_cast<int>(i);
    return -1;
}

static const haven::CombatMapEntry &entry_for(
        const haven::CombatMapSnapshot &snapshot, CHAR_DATA *ch) {
    const int index = entry_index(snapshot, ch);
    assert(index >= 0);
    return snapshot.entries[index];
}

static std::string roster_line(CHAR_DATA *ch) {
    std::istringstream lines(plain(output));
    std::string line;
    while (std::getline(lines, line))
        if (!line.empty() && line.front() == '(' &&
            line.find(") " + std::string(ch->name)) == 3) return line;
    assert(false && "Expected actor in combat roster");
    return "";
}

static void check_cover_proximity_and_roles() {
    Fixture f;
    auto cover = f.cover();
    char_list.push_back(f.viewer.get());
    std::vector<CHAR_DATA *> adjacent, outside;
    for (int x = -1; x <= 1; ++x) for (int y = -1; y <= 1; ++y)
        adjacent.push_back(f.person("a nearby actor", x, y));
    for (auto pos : {std::make_pair(-2, 0), std::make_pair(2, 0),
                    std::make_pair(0, -2), std::make_pair(0, 2),
                    std::make_pair(2, 2)})
        outside.push_back(f.person("a distant actor", pos.first, pos.second));
    auto other_room = f.person("an actor in another room", 0, 0, f.room());
    auto above = f.person("an actor above", 0, 0, f.room(0, 0, 1));
    auto turret = f.cover("a turret", 10);
    REMOVE_FLAG(turret->act, ACT_COVER); SET_FLAG(turret->act, ACT_TURRET);
    auto beside_turret = f.person("beside turret", 10);
    auto covered_turret = f.cover("a bunker turret", 20);
    SET_FLAG(covered_turret->act, ACT_TURRET);
    auto beside_bunker = f.person("beside bunker", 20);
    auto false_cover = f.person("a player with coincident flags", 30);
    SET_FLAG(false_cover->act, ACT_COVER);
    auto beside_player = f.person("beside player", 30);

    auto snapshot = haven::combat_map_snapshot(f.viewer.get());
    for (auto actor : adjacent) {
        assert(is_in_cover(actor)); // Whole production predicate, not a copied rule.
        assert(entry_for(snapshot, actor).cover_entry == entry_index(snapshot, cover));
        assert(entry_for(snapshot, actor).label.find("<u>") != std::string::npos);
    }
    for (auto actor : outside) {
        assert(!is_in_cover(actor));
        assert(entry_for(snapshot, actor).cover_entry == -1);
        assert(entry_for(snapshot, actor).label.find("<u>") == std::string::npos);
    }
    for (auto actor : {cover, turret, covered_turret, other_room, above,
                       beside_turret, false_cover, beside_player}) {
        assert(!is_in_cover(actor));
        assert(entry_for(snapshot, actor).cover_entry == -1);
    }
    assert(entry_for(snapshot, f.viewer.get()).label == "`W<u>Me</u>`x");
    assert(entry_for(snapshot, cover).is_cover && !entry_for(snapshot, cover).is_turret);
    assert(entry_for(snapshot, cover).label == "`Cba`x");
    assert(!entry_for(snapshot, false_cover).is_cover);
    assert(entry_for(snapshot, turret).label == "`C{}`x");
    assert(!entry_for(snapshot, turret).is_cover && entry_for(snapshot, turret).is_turret);
    assert(entry_for(snapshot, covered_turret).label == "`C{}`x");
    assert(entry_for(snapshot, covered_turret).is_cover);
    assert(is_in_cover(beside_bunker));
    assert(entry_for(snapshot, beside_bunker).cover_entry == entry_index(snapshot, covered_turret));
    assert(entry_for(snapshot, other_room).x == entry_for(snapshot, cover).x);
    assert(entry_for(snapshot, other_room).y == entry_for(snapshot, cover).y);

    output.clear(); haven::show_combat_map_roster(f.viewer.get(), snapshot);
    assert(roster_line(cover).find("[Cover]") != std::string::npos);
    assert(roster_line(turret).find("[Turret]") != std::string::npos);
    assert(roster_line(covered_turret).find("[Turret; Cover]") != std::string::npos);
    assert(roster_line(beside_bunker).find("[In cover: a bunker turret]") != std::string::npos);
    puts("PASS: cover display matches production same-room, one-unit axis/diagonal rules; other floors, two-unit gaps, PC flags and bare turrets do not grant cover.");
}

static void check_cover_visibility_and_freshness() {
    {
        Fixture f;
        auto cover = f.cover("a hidden barricade");
        auto actor = f.person("a visible ally", 1);
        auto snapshot = haven::combat_map_snapshot(f.viewer.get());
        assert(entry_for(snapshot, actor).cover_entry >= 0);
        actor->x = 2;
        snapshot = haven::combat_map_snapshot(f.viewer.get());
        assert(entry_for(snapshot, actor).cover_entry == -1);
        assert(entry_for(snapshot, actor).label.find("<u>") == std::string::npos);
        cover->x = 3;
        snapshot = haven::combat_map_snapshot(f.viewer.get());
        assert(entry_for(snapshot, actor).cover_entry == entry_index(snapshot, cover));
        hidden.insert(cover);
        clear_counts(); snapshot = haven::combat_map_snapshot(f.viewer.get());
        assert(is_in_cover(actor)); // Real protection must not reveal a hidden object.
        assert(entry_index(snapshot, cover) == -1 && entry_for(snapshot, actor).cover_entry == -1);
        assert(entry_for(snapshot, actor).label.find("<u>") == std::string::npos);
        haven::show_combat_map_roster(f.viewer.get(), snapshot);
        assert(output.find("barricade") == std::string::npos);
        assert(output.find("In cover") == std::string::npos);
        assert(sight_calls[cover] == 1 && map_sight_calls.count(cover) == 0);
        assert(sight_calls[actor] == 1 && map_sight_calls[actor] == 1);
        hidden.clear(); snapshot = haven::combat_map_snapshot(f.viewer.get());
        assert(entry_for(snapshot, actor).cover_entry >= 0);
    }
    {
        Fixture f;
        auto cover = f.cover("a smoke-obscured barricade", 11);
        auto actor = f.person("a nearby visible ally", 10);
        f.object(COBJ_SMOKE, 20, 0);
        const auto snapshot = haven::combat_map_snapshot(f.viewer.get());
        assert(is_in_cover(actor));
        assert(entry_index(snapshot, cover) == -1);
        assert(entry_for(snapshot, actor).cover_entry == -1);
        assert(entry_for(snapshot, actor).label.find("<u>") == std::string::npos);
        haven::show_combat_map_roster(f.viewer.get(), snapshot);
        assert(output.find("barricade") == std::string::npos && output.find("In cover") == std::string::npos);
    }
    puts("PASS: actor/cover movement refreshes protection; hidden and production smoke-obscured cover never leaks through actor labels or roster annotations.");
}

static void check_cover_priority_cells_and_colors() {
    Fixture f;
    auto cover = f.cover("a low wall"); // Deliberately precedes the actor.
    auto second_cover = f.cover("a second wall");
    auto actor = f.person("a foreground actor", 2);
    auto snapshot = haven::combat_map_snapshot(f.viewer.get());
    auto cells = haven::combat_map_cells(f.viewer.get(), snapshot, 11);
    assert(cells[5 * 11 + 5].entry == entry_index(snapshot, actor));
    assert(cells[5 * 11 + 5].count == 3 && cells[5 * 11 + 5].cover_count == 2);
    assert(entry_for(snapshot, actor).cover_entry == -1); // Same coarse cell is not actual cover.
    draw_map(f.viewer.get(), 11);
    assert(roster_line(actor).find("[Cover in cell: 2]") != std::string::npos);
    assert(roster_line(actor).find("In cover:") == std::string::npos);
    assert(roster_line(cover).find("[Cover]") != std::string::npos);
    assert(roster_line(second_cover).find("[Cover]") != std::string::npos);

    f.viewer->cfighting = cover;
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    cells = haven::combat_map_cells(f.viewer.get(), snapshot, 11);
    assert(cells[5 * 11 + 5].entry == entry_index(snapshot, cover));
    assert(entry_for(snapshot, cover).label == "`Mlo`x");
    f.viewer->cfighting = nullptr;
    aggression.insert(std::make_pair(cover, f.viewer.get()));
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    assert(entry_for(snapshot, cover).label == "`Rlo`x");
    aggression.clear();
    actor->x = 1;
    f.viewer->cfighting = actor;
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    assert(entry_for(snapshot, actor).label == "`M<u>fo</u>`x");
    output.clear(); draw_map(f.viewer.get(), 11);
    assert(roster_line(actor).find("In cover: a low wall") != std::string::npos);
    assert(roster_line(actor).find("Cover in cell") == std::string::npos);
    f.viewer->cfighting = nullptr;
    aggression.insert(std::make_pair(f.viewer.get(), actor));
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    assert(entry_for(snapshot, actor).label == "`R<u>fo</u>`x");
    aggression.clear();
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    assert(entry_for(snapshot, actor).label == "`G<u>fo</u>`x");
    char_list.push_back(f.viewer.get());
    f.viewer->cfighting = cover;
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    cells = haven::combat_map_cells(f.viewer.get(), snapshot, 11);
    assert(cells[5 * 11 + 5].entry == entry_index(snapshot, f.viewer.get()));
    assert(entry_for(snapshot, f.viewer.get()).label == "`W<u>Me</u>`x");
    const auto before_sight = sight_calls, before_map_sight = map_sight_calls;
    const auto before_names = roster_name_calls;
    output.clear(); haven::show_combat_map_roster(f.viewer.get(), snapshot);
    assert(roster_line(actor).find("[In cover: a low wall]") != std::string::npos);
    assert(sight_calls == before_sight && map_sight_calls == before_map_sight);
    assert(roster_name_calls == before_names);
    hidden.insert(f.viewer.get()); hidden.insert(actor);
    f.viewer->cfighting = nullptr;
    auto turret = f.cover("an active turret"); SET_FLAG(turret->act, ACT_TURRET);
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    cells = haven::combat_map_cells(f.viewer.get(), snapshot, 11);
    assert(cells[5 * 11 + 5].entry == entry_index(snapshot, turret));
    assert(cells[5 * 11 + 5].cover_count == 3);
    assert(entry_for(snapshot, turret).cover_entry == -1);
    f.viewer->cfighting = turret;
    assert(entry_for(haven::combat_map_snapshot(f.viewer.get()), turret).label == "`M{}`x");
    f.viewer->cfighting = nullptr;
    aggression.insert(std::make_pair(turret, f.viewer.get()));
    assert(entry_for(haven::combat_map_snapshot(f.viewer.get()), turret).label == "`R{}`x");
    puts("PASS: self/target/actor/cover priority, visible cover retained in shared cells, and protected markers preserve target/hostile/friendly/self colors without extra visibility or name scans.");
}

static void check_reserved_cover_glyphs() {
    Fixture f;
    auto actor = f.person("a duplicate");
    // Reuse one fixture actor to exercise the entire two-character fallback ID
    // space without allocating thousands of heavyweight CHAR_DATA structures.
    for (int i = 1; i < 12000; ++i) char_list.push_back(actor);
    const auto snapshot = haven::combat_map_snapshot(f.viewer.get());
    for (const auto &entry : snapshot.entries) {
        const auto label = plain(entry.label);
        assert(label.size() == 2 && label != "[]" && label != "{}");
    }
    puts("PASS: cover/turret glyphs remain reserved through the full ordinary-actor fallback label namespace.");
}

static void check_roster_boundaries_and_reuse() {
    for (int count : {0, 99, 100, 101, 350}) {
        Fixture f;
        char_list.push_back(nullptr);
        for (int i = 0; i < count; ++i)
            f.person("a guard", (i * 7) % 49, (i * 11) % 49);
        auto snapshot = haven::combat_map_snapshot(f.viewer.get());
        assert(snapshot.entries.size() == static_cast<size_t>(count));
        std::set<std::string> labels;
        for (const auto &entry : snapshot.entries) {
            const auto label = plain(entry.label);
            assert(label.size() == 2);
            assert(labels.insert(label).second);
        }
        auto sight_before = sight_calls, map_before = map_sight_calls;
        auto names_before = name_calls, roster_names_before = roster_name_calls;
        for (int size : {11, 21, 31}) {
            auto cells = haven::combat_map_cells(f.viewer.get(), snapshot, size);
            assert(cells.size() == static_cast<size_t>(size * size));
            output.clear(); haven::show_combat_map_roster(f.viewer.get(), snapshot);
            assert(occurrences(output, "(X:") == count);
        }
        assert(sight_calls == sight_before && map_sight_calls == map_before);
        assert(name_calls == names_before && roster_name_calls == roster_names_before);
        for (const auto &ch : f.people) {
            assert(sight_calls[ch.get()] == 1 && map_sight_calls[ch.get()] == 1);
            assert(name_calls[ch.get()] == 1 && roster_name_calls[ch.get()] == 1);
        }
        // Integrated draw must reuse its one snapshot for both placement and list.
        clear_counts(); draw_map(f.viewer.get(), 31);
        assert(occurrences(output, "(X:") == count);
        for (const auto &ch : f.people)
            assert(sight_calls[ch.get()] == 1 && map_sight_calls[ch.get()] == 1);
    }
    puts("PASS: 0/99/100/101/350 visible actors; two-column unique labels and one visibility/name snapshot reused by grid and roster.");
}

static void check_priorities_and_fresh_counts() {
    Fixture f;
    auto ordinary = f.person("a guard");
    auto target = f.person("a target");
    char_list.push_back(f.viewer.get()); // Viewer deliberately appears last.
    f.viewer->cfighting = target;
    auto snapshot = haven::combat_map_snapshot(f.viewer.get());
    auto cells = haven::combat_map_cells(f.viewer.get(), snapshot, 11);
    assert(snapshot.entries[cells[5 * 11 + 5].entry].character == f.viewer.get());
    assert(cells[5 * 11 + 5].count == 3);
    target->x = ordinary->x = map_expand(1);
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    cells = haven::combat_map_cells(f.viewer.get(), snapshot, 11);
    assert(snapshot.entries[cells[5 * 11 + 6].entry].character == target);
    assert(cells[5 * 11 + 6].count == 2);
    f.viewer->cfighting = nullptr; f.viewer->chattacking = target;
    snapshot = haven::combat_map_snapshot(f.viewer.get());
    cells = haven::combat_map_cells(f.viewer.get(), snapshot, 11);
    assert(snapshot.entries[cells[5 * 11 + 6].entry].character == target);
    f.viewer->cfighting = target;
    target->mapcount = ordinary->mapcount = f.viewer->mapcount = 999;
    output.clear(); draw_map(f.viewer.get(), 11);
    assert(output.find("and 1 other (") != std::string::npos);
    assert(output.find("998 others") == std::string::npos);
    ordinary->x = map_expand(-1);
    output.clear(); draw_map(f.viewer.get(), 11);
    assert(output.find("others") == std::string::npos);
    snapshot = haven::combat_map_snapshot(target);
    for (const auto &entry : snapshot.entries) assert(entry.overlap_count == 1);
    target->desc = &f.descriptor;
    output.clear(); scan_fight(target, true);
    assert(occurrences(output, "(X:") == 3 && output.find("other (") == std::string::npos);
    puts("PASS: self/selected-target/pending-target priorities and no stale overlap after movement, viewer changes or scan.");
}

static void check_visibility_rules() {
    Fixture f;
    auto visible = f.person("a visible bystander", 5); visible->fighting = false;
    auto hidden_ch = f.person("a hidden actor", 5); hidden.insert(hidden_ch);
    auto gm = f.person("a gamemaster", 5); gms.insert(gm);
    auto no_room = f.person("a disconnected actor", 5); no_room->in_room = nullptr;
    auto distant_mine = f.object(COBJ_LANDMINE, 30, 0);
    auto near_mine = f.object(COBJ_LANDMINE, 5, 0);
    auto smoke = f.object(COBJ_SMOKE, 30, 0);
    auto obscured = f.person("a smoke obscured actor", 30, 0);
    auto ghost = f.person("a ghost", 5, 0); ghosts.insert(ghost);
    auto invisible = f.person("an invisible actor", 5, 0);
    invisible->invis_level = 10; SET_FLAG(invisible->act, PLR_ROOMINVIS);
    auto cloaked = f.person("a cloaked actor", 5, 0);
    affects[f.viewer.get()].insert(CAFF_CLOAKBLIND); f.viewer->cloaked = cloaked;
    const auto snapshot = haven::combat_map_snapshot(f.viewer.get());
    for (auto ch : {visible, near_mine, smoke}) assert(entry_index(snapshot, ch) >= 0);
    for (auto ch : {hidden_ch, gm, no_room, distant_mine, obscured, ghost, invisible, cloaked})
        assert(entry_index(snapshot, ch) == -1);
    assert(sight_calls.count(gm) == 0 && sight_calls.count(no_room) == 0);
    assert(map_sight_calls.count(hidden_ch) == 0);
    // Clairvoyance restores an ordinary ghost, but never a possessing one.
    clairvoyance = 2;
    assert(entry_index(haven::combat_map_snapshot(f.viewer.get()), ghost) >= 0);
    possessing.insert(ghost);
    assert(entry_index(haven::combat_map_snapshot(f.viewer.get()), ghost) == -1);
    affects[f.viewer.get()].insert(CAFF_STASIS);
    f.viewer->fight_fast = true; f.viewer->attack_timer = f.viewer->move_timer = 1;
    assert(haven::combat_map_snapshot(f.viewer.get()).entries.empty());
    puts("PASS: production smoke/landmine, cloakblind, invisibility, ghost/possession and stasis rules; visible bystanders/combat objects retained.");
}

static void check_frame_and_objectives() {
    for (int size : {11, 21, 31}) for (int heading : {
            DIR_NORTH, DIR_NORTHEAST, DIR_EAST, DIR_SOUTHEAST,
            DIR_SOUTH, DIR_SOUTHWEST, DIR_WEST, DIR_NORTHWEST}) {
        Fixture f;
        f.viewer->facing = heading;
        for (int i = 0; i < 180; ++i)
            f.person("a guard", map_expand((i % 17) - 8), map_expand((i / 17) - 5));
        f.cover("a capture barricade", 0);
        f.cover("an extraction barricade", map_expand(1));
        auto target = f.person("a protected opponent", map_expand(1));
        f.viewer->cfighting = target;
        char_list.push_back(f.viewer.get());
        objectives.push_back({0, 0, POI_CAPTURE});
        objectives.push_back({map_expand(1), 0, POI_EXTRACT});
        draw_map(f.viewer.get(), size);
        std::istringstream lines(plain(output));
        std::string line;
        size_t width = 0, border_width = 0; int rows = 0;
        while (std::getline(lines, line)) {
            if (!line.empty() && line.front() == '+') {
                if (border_width == 0) border_width = line.size();
                assert(line.size() == border_width);
            }
            if (line.empty() || line.front() != '|') continue;
            assert(line.back() == '|');
            if (width == 0) width = line.size();
            assert(line.size() == width);
            ++rows;
        }
        assert(rows > 0 && width == border_width && width <= 80);
        assert(output.find("`YC") != std::string::npos);
        assert(output.find("`YE") != std::string::npos);
        assert(poi_snapshots == 1 && poi_rosters == 1);
        assert(output.find("`W<u>Me</u>`x") != std::string::npos);
        assert(roster_line(f.viewer.get()).find("[In cover: a capture barricade]") != std::string::npos);
        assert(roster_line(f.viewer.get()).find("[Capture point]") != std::string::npos);
        assert(roster_line(target).find("[In cover: an extraction barricade]") != std::string::npos);
        assert(roster_line(target).find("[Extraction point]") != std::string::npos);
    }
    puts("PASS: aligned styled cover/actor maps for 11/21/31 sizes and eight headings; cover protection coexists with capture/extraction objectives.");
}

static void check_boundary_cells_and_names() {
    Fixture f;
    f.viewer->in_room->size = 5000;
    auto actor = f.person("a guard");
    for (int edge = -15; edge <= 16; ++edge) for (int delta : {-1, 0, 1}) {
        actor->x = map_expand(edge) + delta;
        actor->y = map_expand(-edge) + delta;
        auto snapshot = haven::combat_map_snapshot(f.viewer.get());
        auto cells = haven::combat_map_cells(f.viewer.get(), snapshot, 31);
        for (int y = 0; y < 31; ++y) for (int x = 0; x < 31; ++x) {
            const bool inside = actor->x >= map_expand(x - 15) &&
                actor->x < map_expand(x - 14) && actor->y >= map_expand(y - 15) &&
                actor->y < map_expand(y - 14);
            assert(cells[y * 31 + x].count == static_cast<int>(inside));
            assert((cells[y * 31 + x].entry >= 0) == inside);
        }
    }
    assert(haven::combat_map_cells(f.viewer.get(), {}, 0).empty());
    assert(haven::combat_map_cells(f.viewer.get(), {}, 32).empty());
    for (const std::string &name : std::vector<std::string>{
            "", "A", "an ", "`", "`R", "`123a guard", "`#FF00FFa guard",
            "<b>an agent</b>", "\033[31ma guard", "\033]0;title\007a guard",
            "\n\t", "a \303\251lan", "Me", "CC", "EE", "[]", "{}", std::string(15000, 'G')})
        f.person(name);
    const auto snapshot = haven::combat_map_snapshot(f.viewer.get());
    std::set<std::string> labels;
    for (const auto &entry : snapshot.entries) {
        const auto label = plain(entry.label);
        assert(label.size() == 2 && labels.insert(label).second);
        assert(label != "Me" && label != "CC" && label != "EE");
        assert(label != "[]" && label != "{}");
        for (unsigned char c : label) assert(c >= 32 && c <= 126);
    }
    output.clear(); haven::show_combat_map_roster(f.viewer.get(), snapshot);
    assert(output.find(std::string(15000, 'G')) != std::string::npos);
    puts("PASS: half-open positive/negative cell boundaries; empty/short/color/control/long names stay two columns and long roster text is untruncated.");
}

static void check_terrain_stairs_and_visibility() {
    Fixture f;
    auto origin = f.viewer->in_room;
    auto upper = f.room(0, 0, 1), lower = f.room(0, 0, -1);
    auto up = f.link(origin, DIR_UP, upper), down = f.link(origin, DIR_DOWN, lower);
    unreachable.insert(origin);
    auto glyph = [&]() { CombatMapTerrain renderer(f.viewer.get()); return plain(renderer.fill(origin)); };
    assert(glyph() == "*");
    origin->exit[DIR_DOWN] = nullptr;
    assert(glyph() == "^");
    for (int EXIT_DATA::*field : {&EXIT_DATA::jump, &EXIT_DATA::climb, &EXIT_DATA::fall}) {
        up->*field = 1; assert(glyph() == "#"); up->*field = 0;
    }
    for (int sector : {SECT_AIR, SECT_ATMOSPHERE, SECT_WATER, SECT_UNDERWATER, SECT_SHALLOW}) {
        upper->sector_type = sector; assert(glyph() == "#"); upper->sector_type = SECT_STREET;
        origin->sector_type = sector; assert(glyph() == "#"); origin->sector_type = SECT_STREET;
    }
    upper->sector_type = origin->sector_type = SECT_FOREST;
    assert(glyph() == "#");
    upper->room_flags |= ROOM_INDOORS; assert(glyph() == "^");
    upper->room_flags = 0; upper->sector_type = origin->sector_type = SECT_STREET;
    for (int flag : {EX_CLOSED, EX_HIDDEN}) {
        up->exit_info = flag; assert(glyph() == "#"); up->exit_info = 0;
    }
    SET_FLAG(up->affected_by, AFF_XHIDE); assert(glyph() == "#");
    up->affected_by[AFF_XHIDE / UL_BITS] = 0;
    unseen.insert(upper); assert(glyph() == "#"); unseen.clear();
    upper->room_flags |= ROOM_INVISIBLE; assert(glyph() == "#"); upper->room_flags = 0;
    AREA_DATA other = {}; other.world = WORLD_OTHER;
    upper->area = &other; assert(glyph() == "#"); upper->area = &f.area;
    unreachable.insert(upper); assert(glyph() == "#"); unreachable.erase(upper);
    origin->exit[DIR_UP] = nullptr; origin->exit[DIR_DOWN] = down;
    assert(glyph() == "v");
    for (int EXIT_DATA::*field : {&EXIT_DATA::jump, &EXIT_DATA::climb, &EXIT_DATA::fall}) {
        down->*field = 1; assert(glyph() == "#"); down->*field = 0;
    }
    // Denied terrain never spends path/light work or leaks its sector.
    clear_counts(); unseen.insert(upper);
    CombatMapTerrain renderer(f.viewer.get());
    assert(plain(renderer.fill(upper)) == "#");
    assert(path_calls.empty() && light_calls.empty());
    assert(plain(renderer.fill(upper)) == "#" && room_sight_calls[upper] == 1);
    puts("PASS: genuine up/down/both stairs; excludes jump/climb/fall, air/water/canopy, closed/hidden/unseen/cross-world routes and unreachable destinations.");
}

static void check_narrow_frames_and_roster_order() {
    Fixture f;
    auto near = f.person("Near", 2);
    auto first = f.person("First", 6);
    auto second = f.person("Second", 6);
    auto far = f.person("Far", 9);
    f.cover("a nearby barrier", 2);
    auto different_floor = f.person("Above", 7, 0, f.room(0, 0, 1));
    (void)near; (void)first; (void)second; (void)far;
    auto snapshot = haven::combat_map_snapshot(f.viewer.get());
    haven::show_combat_map_roster(f.viewer.get(), snapshot);
    assert(output.find("Near") < output.find("First"));
    assert(output.find("First") < output.find("Second"));
    assert(output.find("Second") < output.find("Far"));
    assert(output.find("D:7(25)") != std::string::npos);
    different_floor->in_room = f.viewer->in_room;
    for (int linewidth : {10, 11, 20, 40, 80}) {
        f.viewer->linewidth = linewidth;
        output.clear(); draw_map(f.viewer.get(), 31);
        std::istringstream lines(plain(output));
        std::string line;
        while (std::getline(lines, line))
            if (!line.empty() && (line.front() == '|' || line.front() == '+'))
                assert(line.size() <= static_cast<size_t>(linewidth));
    }
    puts("PASS: stable distance-sorted roster, vertical distances, and aligned frames fitting 10/11/20/40/80-column clients.");
}

static void check_terrain_cache() {
    Fixture f;
    for (int x = -8; x <= 8; ++x) for (int y = -8; y <= 8; ++y) {
        if (x || y) f.room(x, y);
    }
    draw_map(f.viewer.get(), 31);
    assert(path_calls.size() > 1);
    for (const auto &count : path_calls) assert(count.second == 1);
    for (const auto &count : light_calls) assert(count.second == 1);
    int terrain_columns = 0;
    std::istringstream rows(plain(output));
    std::string row;
    while (std::getline(rows, row))
        if (!row.empty() && row.front() == '|') terrain_columns += static_cast<int>(row.size()) - 4;
    assert(terrain_columns > static_cast<int>(path_calls.size()) * 5);
    assert(occurrences(output, "`W=") < static_cast<int>(path_calls.size()));
    printf("MEASURE: 31-cell outdoor map has %d terrain columns; reachability/light checks %zu/%zu (legacy per-column reachability %d).\n",
           terrain_columns, path_calls.size(), light_calls.size(), terrain_columns);
    const auto once_paths = path_calls;
    draw_map(f.viewer.get(), 31);
    for (const auto &count : once_paths) assert(path_calls[count.first] == 2);
    clear_counts(); cone_visible = false;
    draw_map(f.viewer.get(), 31);
    assert(path_calls.empty() && light_calls.empty());
    puts("PASS: path/lighting work scales with distinct rendered rooms, refreshes next draw, and skips out-of-cone terrain.");
}

static void check_covered_objectives_and_battleflags() {
    Fixture f;
    auto ordinary = f.person("A bystander", 0);
    auto target = f.person("A selected target", map_expand(1));
    f.viewer->cfighting = target;
    char_list.push_back(f.viewer.get());
    objectives.push_back({0, 0, POI_CAPTURE});
    objectives.push_back({map_expand(1), 0, POI_EXTRACT});
    draw_map(f.viewer.get(), 11);
    assert(output.find("`WMe`x") != std::string::npos);
    assert(output.find("Capture point") != std::string::npos);
    assert(output.find("Extraction point") != std::string::npos);
    assert(output.find("`YCC") == std::string::npos && output.find("`YEE") == std::string::npos);
    assert(ordinary->mapcount == 0); // A draw never writes global per-actor counts.
    // Exercise the actual battleflags function's static buffer under sanitizers.
    f.names.emplace_back(MSL * 2, 'Q'); target->name = &f.names.back()[0];
    target->x = 2;
    for (int i = 0; i < 2000; ++i) {
        const char *flags = battleflags(f.viewer.get(), f.viewer.get());
        assert(strlen(flags) == MSL - 1);
        assert(strncmp(flags, " fighting ", 10) == 0);
    }
    target->x = 20;
    assert(strncmp(battleflags(f.viewer.get(), f.viewer.get()), " shooting at ", 13) == 0);
    puts("PASS: self/selected-target markers preserve covered objective details in roster; repeated battleflags with oversized opponent names are bounded and leak-free.");
}

static void check_quiet_path_reporting() {
    Fixture f;
    auto destination = f.room(1);
    f.link(f.viewer->in_room, DIR_EAST, destination);
    real_path_helpers = true; fixture_flying = true;
    assert(can_get_to_for_map(f.viewer.get(), destination));
    assert(fixture_can_get_to(f.viewer.get(), destination));
    destination->sector_type = SECT_AIR; f.viewer->debuff = 75;
    output.clear();
    assert(!can_get_to_for_map(f.viewer.get(), destination) && output.empty());
    CombatMapTerrain renderer(f.viewer.get());
    assert(plain(renderer.fill(destination)) == "#" && output.empty());
    assert(!fixture_can_get_to(f.viewer.get(), destination));
    assert(output == "You are too disoriented to fly.\n\r");
    puts("PASS: production map path checks preserve reachability and suppress drawing warnings; ordinary movement retains its warning.");
}

int main() {
    setup_translation();
    check_cover_proximity_and_roles();
    check_cover_visibility_and_freshness();
    check_cover_priority_cells_and_colors();
    check_reserved_cover_glyphs();
    check_roster_boundaries_and_reuse();
    check_priorities_and_fresh_counts();
    check_visibility_rules();
    check_frame_and_objectives();
    check_boundary_cells_and_names();
    check_terrain_stairs_and_visibility();
    check_narrow_frames_and_roster_order();
    check_terrain_cache();
    check_covered_objectives_and_battleflags();
    check_quiet_path_reporting();
    return 0;
}
