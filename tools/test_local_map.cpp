// Synthetic rooms exercise the real renderer without loading any world files.
#include "merc.h"
#include "local_map.h"
#include <cassert>
#include <chrono>
#include <climits>
#include <cstdio>
#include <memory>
#include <set>
#include <sstream>

static std::set<ROOM_INDEX_DATA *> invisible;
static int visibility_calls = 0;

extern "C" {
bool can_see_room(CHAR_DATA *, ROOM_INDEX_DATA *room) {
    ++visibility_calls;
    return invisible.count(room) == 0;
}
int get_trust(CHAR_DATA *viewer) { return viewer->level; }
}

struct Fixture {
    AREA_DATA area = {};
    AREA_DATA other_area = {};
    std::unique_ptr<CHAR_DATA> viewer{new CHAR_DATA{}};
    std::unique_ptr<PC_DATA> pc{new PC_DATA{}};
    std::vector<std::unique_ptr<ROOM_INDEX_DATA>> rooms;
    std::vector<std::unique_ptr<EXIT_DATA>> exits;

    Fixture() {
        area.vnum = 1;
        area.world = WORLD_EARTH;
        other_area.vnum = 2;
        other_area.world = WORLD_OTHER;
        viewer->pcdata = pc.get();
        viewer->linewidth = 80;
        invisible.clear();
        visibility_calls = 0;
    }
    ROOM_INDEX_DATA *room(int x = 0, int y = 0, int sector = SECT_STREET,
                          int z = 0) {
        rooms.emplace_back(new ROOM_INDEX_DATA{});
        ROOM_INDEX_DATA *r = rooms.back().get();
        r->vnum = static_cast<int>(rooms.size()) + 1000;
        r->area = &area;
        r->sector_type = sector;
        r->x = x;
        r->y = y;
        r->z = z;
        r->name = const_cast<char *>("Synthetic map fixture");
        if (!viewer->in_room) viewer->in_room = r;
        return r;
    }
    EXIT_DATA *link(ROOM_INDEX_DATA *from, int direction, ROOM_INDEX_DATA *to) {
        exits.emplace_back(new EXIT_DATA{});
        EXIT_DATA *e = exits.back().get();
        e->u1.to_room = to;
        e->orig_door = direction;
        from->exit[direction] = e;
        return e;
    }
    std::string render(bool compact = true, haven::LocalMapStats *stats = nullptr) {
        return haven::render_local_map(viewer.get(), viewer->in_room, compact, stats);
    }
};

static std::string plain(const std::string &colored) {
    std::string result;
    for (size_t i = 0; i < colored.size(); ++i) {
        if (colored[i] == '`' && i + 1 < colored.size()) {
            ++i;
            if (colored[i] == '`') result += '`';
        } else if (colored[i] != '\r') result += colored[i];
    }
    return result;
}

static std::vector<std::string> lines(const std::string &colored) {
    std::istringstream input(plain(colored));
    std::vector<std::string> result;
    std::string line;
    while (std::getline(input, line)) result.push_back(line);
    return result;
}

// Relative positions are part of the public display: four columns and two rows
// between room centers. Locating @ avoids depending on frame/header wording.
static char offset(const std::string &colored, int dx, int dy = 0) {
    const auto rows = lines(colored);
    for (size_t y = 0; y < rows.size(); ++y) {
        const size_t x = rows[y].find('@');
        if (x == std::string::npos) continue;
        const int xx = static_cast<int>(x) + dx;
        const int yy = static_cast<int>(y) + dy;
        if (xx < 0 || yy < 0 || yy >= static_cast<int>(rows.size()) ||
            xx >= static_cast<int>(rows[yy].size())) return '\0';
        return rows[yy][xx];
    }
    assert(!"Player marker missing");
    return '\0';
}

static void check_stairs() {
    Fixture f;
    auto origin = f.room();
    auto upstairs = f.room(0, 0, SECT_HOUSE, 1);
    auto downstairs = f.room(0, 0, SECT_HOUSE, -1);
    auto up = f.link(origin, DIR_UP, upstairs);
    assert(offset(f.render(), 1) == '^');
    auto down = f.link(origin, DIR_DOWN, downstairs);
    assert(offset(f.render(), 1) == '*');
    origin->exit[DIR_UP] = nullptr;
    assert(offset(f.render(), 1) == 'v');
    origin->exit[DIR_UP] = up;
    origin->exit[DIR_DOWN] = nullptr;

    for (int EXIT_DATA::*field : {&EXIT_DATA::jump, &EXIT_DATA::climb, &EXIT_DATA::fall}) {
        up->*field = 1;
        assert(offset(f.render(), 1) != '^');
        up->*field = 0;
        origin->exit[DIR_UP] = nullptr;
        origin->exit[DIR_DOWN] = down;
        down->*field = 1;
        assert(offset(f.render(), 1) != 'v');
        down->*field = 0;
        origin->exit[DIR_UP] = up;
        origin->exit[DIR_DOWN] = nullptr;
    }
    for (int sector : {SECT_AIR, SECT_ATMOSPHERE, SECT_WATER,
                       SECT_UNDERWATER, SECT_SHALLOW}) {
        upstairs->sector_type = sector;
        assert(offset(f.render(), 1) != '^');
        upstairs->sector_type = SECT_HOUSE;
        origin->sector_type = sector;
        assert(offset(f.render(), 1) != '^');
        origin->sector_type = SECT_STREET;
    }
    up->exit_info = EX_HIDDEN;
    assert(offset(f.render(), 1) != '^');
    up->exit_info = 0;
    up->affected_by[AFF_XHIDE / UL_BITS] |= 1UL << (AFF_XHIDE % UL_BITS);
    assert(offset(f.render(), 1) != '^');
    up->affected_by[AFF_XHIDE / UL_BITS] = 0;
    invisible.insert(upstairs);
    assert(offset(f.render(), 1) != '^');
    invisible.clear();
    upstairs->area = &f.other_area;
    assert(offset(f.render(), 1) != '^');
    puts("PASS: genuine stairs, both directions; no jump/climb/fall, aerial, aquatic, hidden, unseen or cross-realm stairs.");
}

static void check_visibility_and_doors() {
    Fixture f;
    auto origin = f.room();
    auto interior = f.room(1, 0, SECT_HOUSE);
    auto deeper = f.room(1, 1, SECT_SHOP);
    interior->room_flags = ROOM_INDOORS;
    deeper->room_flags = ROOM_INDOORS;
    auto east = f.link(origin, DIR_EAST, interior);
    f.link(interior, DIR_NORTH, deeper);
    assert(offset(f.render(), 4) == 'H');
    assert(offset(f.render(), 4, -2) == '$');

    east->exit_info = EX_HIDDEN;
    assert(offset(f.render(), 4) == ' ');
    assert(offset(f.render(), 4, -2) == ' ');
    east->exit_info = 0;
    east->affected_by[AFF_XHIDE / UL_BITS] |= 1UL << (AFF_XHIDE % UL_BITS);
    assert(offset(f.render(), 4) == ' ');
    east->affected_by[AFF_XHIDE / UL_BITS] = 0;

    east->wall = WALL_BRICK;
    assert(offset(f.render(), 4) == ' ');
    east->wallcondition = WALLCOND_HOLE;
    assert(offset(f.render(), 4) == 'H');
    east->wallcondition = WALLCOND_NORMAL;
    east->wall = WALL_GLASS;
    assert(offset(f.render(), 2) == 'W');
    assert(offset(f.render(), 4) == ' ');
    east->wall = WALL_NONE;

    invisible.insert(interior);
    assert(offset(f.render(), 4) == ' ');
    assert(offset(f.render(), 4, -2) == ' ');
    invisible.clear();

    east->exit_info = EX_ISDOOR | EX_CLOSED;
    auto closed = f.render();
    assert(offset(closed, 2) == '+');
    assert(offset(closed, 4) == ' ');
    assert(offset(closed, 4, -2) == ' ');
    east->exit_info |= EX_LOCKED;
    assert(offset(f.render(), 2) == 'X');
    east->exit_info = EX_ISDOOR;
    auto opened = f.render();
    assert(offset(opened, 2) == 'o');
    assert(offset(opened, 4, -2) == '$');
    east->exit_info = EX_ISDOOR | EX_CLOSED;
    assert(f.render() == closed);
    east->exit_info |= EX_SEETHRU;
    assert(offset(f.render(), 4) == 'H');
    assert(offset(f.render(), 4, -2) == '$');
    east->exit_info |= EX_CURTAINS;
    assert(offset(f.render(), 4) == ' ');
    assert(offset(f.render(), 4, -2) == ' ');
    east->exit_info = 0;
    assert(offset(f.render(), 2) == '=');
    puts("PASS: hidden and magical hidden exits, walls/holes/glass, visibility, entrances, live open/closed/locked doors and interior traversal limits.");
}

static void check_legacy_canopy() {
    // Persisted forest-to-treetop exits can have no movement metadata at all
    // (for example 1904->8178). They must not look like staircases.
    Fixture f;
    auto ground = f.room(0, 0, SECT_FOREST, 0);
    auto canopy = f.room(0, 0, SECT_FOREST, 1);
    f.link(ground, DIR_UP, canopy);
    f.link(canopy, DIR_DOWN, ground);
    assert(offset(f.render(), 1) == ' ');
    f.viewer->in_room = canopy;
    assert(offset(f.render(), 1) == ' ');

    // Custom interiors sometimes retain the stock forest sector. Indoor
    // physical stairs still need to be represented in both directions.
    ground->room_flags = ROOM_INDOORS;
    canopy->room_flags = ROOM_INDOORS;
    f.viewer->in_room = ground;
    assert(offset(f.render(), 1) == '^');
    f.viewer->in_room = canopy;
    assert(offset(f.render(), 1) == 'v');
    ground->room_flags = 0;
    f.viewer->in_room = ground;
    assert(offset(f.render(), 1) == '^');
    f.viewer->in_room = canopy;
    assert(offset(f.render(), 1) == 'v');
    puts("PASS: unannotated outdoor forest/canopy links are not stairs; indoor forest-sector stairs remain visible.");
}

static void check_geometry() {
    Fixture f;
    auto origin = f.room();
    auto ne = f.room(1, 1, SECT_FOREST);
    f.link(origin, DIR_NORTHEAST, ne);
    assert(offset(f.render(), 4, -2) == 'T');
    assert(offset(f.render(), 2, -1) == '/');

    auto north = f.room(0, 1, SECT_PARK);
    auto collision = f.room(1, 1, SECT_WATER);
    f.link(origin, DIR_NORTH, north);
    f.link(north, DIR_EAST, collision);
    const auto collision_map = plain(f.render());
    assert(collision_map.find('!') != std::string::npos);
    assert(offset(f.render(), 0) == '@');

    auto remote = f.room(INT_MAX, INT_MIN, SECT_HOSPITAL);
    auto east = f.link(origin, DIR_EAST, remote);
    const auto remote_map = f.render();
    assert(offset(remote_map, 2) == '!');
    assert(offset(remote_map, 4) == ' ');
    remote->x = 1;
    remote->y = 0;
    remote->area = &f.other_area;
    assert(offset(f.render(), 2) == ' ');
    assert(offset(f.render(), 4) == ' ');
    remote->area = &f.area;
    remote->z = 1;
    assert(offset(f.render(), 2) == '!');
    assert(offset(f.render(), 4) == ' ');
    east->u1.to_room = nullptr;
    assert(offset(f.render(), 2) == ' ');
    puts("PASS: diagonal geometry, overlapping room coordinates, remote exits, realm/floor boundaries and missing destinations.");
}

static void check_colors_and_width() {
    Fixture f;
    auto origin = f.room();
    f.link(origin, DIR_NORTH, f.room(0, 1, SECT_FOREST));
    f.link(origin, DIR_EAST, f.room(1, 0, SECT_WATER));
    f.link(origin, DIR_SOUTH, f.room(0, -1, SECT_SHOP));
    f.link(origin, DIR_WEST, f.room(-1, 0, SECT_HOSPITAL));
    const auto map = f.render();
    std::set<char> colors;
    for (size_t i = 0; i + 1 < map.size(); ++i)
        if (map[i] == '`') colors.insert(map[++i]);
    assert(colors.size() >= 5);
    const auto visible = plain(map);
    assert(std::count(visible.begin(), visible.end(), '@') == 1);
    assert(visible.find("Synthetic map fixture") == std::string::npos);
    assert(visible.find("Legend") == std::string::npos);
    assert(visible.find("Nearby") == std::string::npos);
    assert(visible.find("help map") == std::string::npos);
    const auto compact_lines = lines(map);
    assert(compact_lines.size() == 7);
    assert(compact_lines.front() == "+-----------+");
    assert(compact_lines.back() == compact_lines.front());
    for (const auto &line : compact_lines) assert(line.size() == 13);
    assert(map.compare(0, 3, "`g+") == 0);
    assert(f.render(false).compare(0, 3, "`g+") == 0);
    for (int width : {10, 12, 13, 20, 40, 60, 80, 120}) {
        f.viewer->linewidth = width;
        for (bool compact : {true, false})
            for (const auto &line : lines(f.render(compact)))
                assert(line.size() <= static_cast<size_t>(width));
    }
    f.viewer->linewidth = 80;
    assert(f.render(false).size() > f.render(true).size());
    assert(haven::render_local_map(nullptr, origin, true).empty());
    assert(haven::render_local_map(f.viewer.get(), nullptr, true).empty());
    puts("PASS: distinct terrain colors, one player, separate help legend, compact/full views, terminal widths and null inputs.");
}

static ROOM_INDEX_DATA *grid(Fixture &f, int radius) {
    const int side = 2 * radius + 1;
    std::vector<ROOM_INDEX_DATA *> cells;
    for (int y = -radius; y <= radius; ++y)
        for (int x = -radius; x <= radius; ++x) cells.push_back(f.room(x, y));
    for (int y = 0; y < side; ++y) {
        for (int x = 0; x < side; ++x) {
            auto r = cells[y * side + x];
            if (y + 1 < side) f.link(r, DIR_NORTH, cells[(y + 1) * side + x]);
            if (x + 1 < side) f.link(r, DIR_EAST, cells[y * side + x + 1]);
            if (y > 0) f.link(r, DIR_SOUTH, cells[(y - 1) * side + x]);
            if (x > 0) f.link(r, DIR_WEST, cells[y * side + x - 1]);
        }
    }
    f.viewer->in_room = cells[radius * side + radius];
    return f.viewer->in_room;
}

static void check_bounded_work() {
    Fixture small;
    grid(small, 8);
    haven::LocalMapStats compact_stats, large_stats;
    const auto compact_map = small.render(true, &compact_stats);
    const auto large_map = small.render(false, &large_stats);
    // An ordinary road continuing past the crop is still an ordinary road.
    assert(plain(compact_map).find('!') == std::string::npos);
    assert(plain(large_map).find('!') == std::string::npos);
    assert(compact_stats.rooms == 9);
    assert(large_stats.rooms == 165);
    assert(compact_stats.exits_examined <= 10 * compact_stats.rooms);
    assert(large_stats.exits_examined <= 10 * large_stats.rooms);
    assert(compact_stats.visibility_checks <= compact_stats.exits_examined);
    assert(large_stats.visibility_checks <= large_stats.exits_examined);

    Fixture large;
    grid(large, 24);
    for (bool compact : {true, false}) {
        haven::LocalMapStats stats;
        visibility_calls = 0;
        const auto actual = large.render(compact, &stats);
        const auto &baseline = compact ? compact_stats : large_stats;
        assert(actual == (compact ? compact_map : large_map));
        assert(stats.rooms == baseline.rooms);
        assert(stats.exits_examined == baseline.exits_examined);
        assert(stats.visibility_checks == baseline.visibility_checks);
        assert(visibility_calls == stats.visibility_checks);
    }
    const int iterations = 2000;
    size_t bytes = 0;
    auto start = std::chrono::steady_clock::now();
    for (int i = 0; i < iterations; ++i) bytes += large.render(true).size();
    auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now() - start).count();
    assert(bytes > 0);
    printf("PASS: cyclic grids (289 vs 2401 rooms) have identical output/work; compact %d rooms/%d exits, full %d/%d.\n",
           compact_stats.rooms, compact_stats.exits_examined,
           large_stats.rooms, large_stats.exits_examined);
    printf("BENCHMARK: %d minimaps in %.2f ms (%.2f us each; synthetic visibility helpers).\n",
           iterations, elapsed / 1000.0, elapsed / static_cast<double>(iterations));
}

int main() {
    check_stairs();
    check_visibility_and_doors();
    check_legacy_canopy();
    check_geometry();
    check_colors_and_width();
    check_bounded_work();
    puts("All local-map renderer tests passed.");
}
