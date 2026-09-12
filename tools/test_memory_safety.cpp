#include "merc.h"
#include "recycle.h"
#include "olc.h"
#include "global.h"
#include <cassert>
#include <cstring>
#include <ctime>
#include <cstddef>
#include <cstdint>

void test_build_safety(CHAR_DATA *ch);

extern "C" {
extern char str_boot_time[];
extern char *enclave_room[2 * MAX_DORMROOMS];
extern const int cover_table[MAX_COVERS];
void save_dorms();
void load_dorms();
void fread_dorms(FILE *);
void save_object(FILE *, OBJ_INDEX_DATA *);
void load_objects(FILE *);
void fwrite_obj_2(OBJ_DATA *, FILE *, int);
void fread_gobj(FILE *);
CLAN_TYPE *new_clan();
void free_clan(CLAN_TYPE *);
extern int town_blackout;
char *static_text(CHAR_DATA *, CHAR_DATA *, char *);
char *format_column(int, char *, char *, int);
void show_location(CHAR_DATA *, CHAR_DATA *, int);
void show_multilocation(CHAR_DATA *, CHAR_DATA *, int);
float skin_face_score(CHAR_DATA *);
}

static void assign(char *&field, const char *value) {
    free_string(field);
    field = str_dup(value);
}

static void expect(char *actual, const char *expected) {
    if (strcmp(actual, expected))
        fprintf(stderr, "Expected <%s>, got <%s>\n", expected, actual);
    assert(!strcmp(actual, expected));
    free_string(actual);
}

static void test_descriptions(CHAR_DATA *ch) {
    assign(ch->description, "Overall.\n\r");
    assign(ch->pcdata->focused_descs[0], "Hands.\n\r");
    assign(ch->pcdata->focused_descs[17], "Eyes.\n\r");
    assign(ch->pcdata->focused_descs[COVERS_SMELL], "Pine smell.\n\r");
    ch->pcdata->focused_order[COVERS_ALL] = 1;
    ch->pcdata->focused_order[0] = 2;
    ch->pcdata->focused_order[COVERS_SMELL] = 3;
    ch->pcdata->focused_order[17] = 4;
    expect(get_focused(ch, ch, false), "Overall.Hands.Pine smell.Eyes.");
    expect(get_default_dreamdesc(ch), "Overall.Hands.Eyes.");

    CHAR_DATA *viewer = new_char();
    viewer->pcdata = new_pcdata();
    viewer->in_room = ch->in_room;
    // An ordinary observer cannot smell the focused description.
    expect(get_focused(viewer, ch, false), "Overall.Hands.Eyes.");
    viewer->skills[SKILL_ACUTESMELL] = 1;
    expect(get_focused(viewer, ch, false), "Overall.Hands.Pine smell.Eyes.");
    viewer->in_room = nullptr;
    expect(get_focused(viewer, ch, false), "Overall.Hands.Eyes.");

    OBJ_DATA *gloves = create_object(get_obj_index(OBJ_VNUM_DUMMY), 0);
    gloves->item_type = ITEM_CLOTHING;
    gloves->value[0] = COVERS_HANDS;
    obj_to_char(gloves, ch);
    gloves->wear_loc = WEAR_BODY_1;
    assert(is_covered(ch, COVERS_HANDS));
    expect(get_focused(ch, ch, false), "Overall.Pine smell.Eyes.");
    expect(get_focused(ch, ch, true), "Overall.Hands.Pine smell.Eyes.");
    expect(get_default_dreamdesc(ch), "Overall.Eyes.");
    gloves->wear_loc = WEAR_NONE;

    ch->shape = SHAPE_MERMAID;
    assign(ch->pcdata->focused_descs[3], "Feet.");
    ch->pcdata->focused_order[3] = 2;
    expect(get_focused(ch, ch, false), "Overall.Hands.Pine smell.Eyes.");
    ch->shape = 0;
    assign(ch->pcdata->focused_descs[3], "");
    assign(ch->description, "X");
    assign(ch->pcdata->focused_descs[0], "Y");
    expect(get_focused(ch, ch, false), "XYPine smell.Eyes.");
    expect(get_default_dreamdesc(ch), "XYEyes.");
    assign(ch->pcdata->scent, "Fresh scent.");
    expect(get_focused(ch, ch, false), "XYPine smell.Eyes. Fresh scent.\n");
    do_look(ch, (char *)"me");
    assert(strstr(ch->desc->outbuf, "Pine smell."));
    show_location(ch, ch, COVERS_SMELL);
    show_multilocation(ch, ch, 4); // Includes body and smell descriptions.
    puts("PASS: look me, focused ordering, smell/scent, clothing, xray, mermaid and short descriptions.");
}

static void test_allocators() {
    auto *fantasy = new_fantasy();
    for (int i = 0; i < 100; ++i)
        assert(fantasy->rooms[i] == 0 && fantasy->safe_room[i] == 0);
    for (int i = 0; i < 200; ++i) {
        assert(!strcmp(fantasy->participants[i], ""));
        assert(!strcmp(fantasy->exit_name[i], ""));
        assert(!strcmp(fantasy->exit_alias[i], ""));
        assert(fantasy->exits[i] == 0 && fantasy->entrances[i] == 0);
        assert(fantasy->participant_stats[i][29] == 0);
    }
    free_fantasy(fantasy);
    auto *group = new_grouptext();
    for (int number : group->pnumber) assert(number == 0);
    assert(group->valid);
    auto *clan = new_clan();
    for (auto *leader : clan->division_leaders) assert(!strcmp(leader, ""));
    assert(clan->oak == 0 && clan->stone == 0);
    free_clan(clan);
    puts("PASS: fantasy, group text and clan initialization and cleanup.");
}

static void test_objects(CHAR_DATA *ch) {
    static_assert(sizeof(((OBJ_DATA *)0)->value) == sizeof(((OBJ_INDEX_DATA *)0)->value),
                  "Prototype and instance value counts differ");
    const int types[] = {ITEM_CLOTHING, ITEM_JEWELRY, ITEM_KEY, ITEM_RANGED,
                         ITEM_POTION, ITEM_CONTAINER};
    FILE *area = tmpfile();
    assert(area);
    int vnum = 990000;
    for (int type : types) {
        auto *prototype = new_obj_index();
        prototype->vnum = ++vnum;
        assert(!get_obj_index(vnum));
        prototype->item_type = type;
        for (int value : prototype->value) assert(value == 0);
        for (int i = 0; i < MAX_OBJ_VALUES; ++i) prototype->value[i] = 10 + i;
        save_object(area, prototype);
    }
    fputs("#0\n", area);
    rewind(area);
    load_objects(area);
    fclose(area);
    vnum = 990000;
    for (int type : types) {
        auto *prototype = get_obj_index(++vnum);
        assert(prototype && prototype->item_type == type);
        // The historical container area record has five values; the sixth defaults to zero.
        for (int i = 0; i < MAX_OBJ_VALUES; ++i)
            assert(prototype->value[i] == (type == ITEM_CONTAINER && i == 5 ? 0 : 10 + i));
        auto *obj = create_object(prototype, 0);
        for (int i = 0; i < MAX_OBJ_VALUES; ++i) assert(obj->value[i] == prototype->value[i]);
        auto *clone = new_obj();
        clone_object(obj, clone);
        for (int i = 0; i < MAX_OBJ_VALUES; ++i) assert(clone->value[i] == obj->value[i]);
        obj->value[5] = 123456;
        obj->rot_timer = 789;
        // Exercise each player/world writer with its corresponding loader.
        for (auto writer : {fwrite_obj, fwrite_obj_2}) {
            FILE *file = tmpfile();
            assert(file);
            if (writer == fwrite_obj_2) obj_to_room(obj, ch->in_room);
            writer(obj, file, 0);
            rewind(file);
            assert(!strcmp(fread_word(file), "#O"));
            THING holder = {};
            holder.thing_type = THING_CH;
            holder.thing.ch = ch;
            if (writer == fwrite_obj_2) fread_gobj(file);
            else fread_obj(holder, file);
            fclose(file);
            auto *loaded = writer == fwrite_obj_2 ? ch->in_room->contents : ch->carrying;
            for (int i = 0; i < MAX_OBJ_VALUES; ++i) assert(loaded->value[i] == obj->value[i]);
            assert(loaded->rot_timer == 789);
        }
    }
    puts("PASS: object prototypes, five/six-value area records, creation, cloning and both save writers round-trip.");
}

static void test_dorms(CHAR_DATA *ch) {
    assign(enclave_room[19], "LastResident");
    assign(enclave_room[39], "LastRoommate");
    save_dorms();
    assign(enclave_room[19], "");
    assign(enclave_room[39], "");
    load_dorms();
    assert(!strcmp(enclave_room[19], "LastResident"));
    assert(!strcmp(enclave_room[39], "LastRoommate"));
    FILE *file = tmpfile();
    fputs("DormRoom -1 invalid~\nDormRoom 40 invalid~\nDormRoom 39 ValidRoommate~\nEnd\n", file);
    rewind(file);
    fread_dorms(file);
    fclose(file);
    assert(!strcmp(enclave_room[39], "ValidRoommate"));
    assign(enclave_room[39], ch->name);
    do_roomie(ch, (char *)"stop");
    assert(!strcmp(enclave_room[39], ""));
    puts("PASS: all 40 dorm slots persist, last roommate can leave, invalid file indexes are rejected.");
}

static void test_appends(CHAR_DATA *ch) {
    expect(draw_horizontal_line(0), "");
    expect(draw_horizontal_line(5), "_____");
    expect(draw_horizontal_line(320), std::string(320, '_').c_str());
    expect(format_column(40, (char *)"H:", (char *)"abcdefghijklmnop", 1), "H:abcdefghi");
    expect(format_column(0, (char *)"H:", (char *)"text", 1), "H:");
    int blackout = town_blackout;
    town_blackout = 1;
    ch->pcdata->garbled = 100;
    char input[] = "one two three";
    expect(static_text(ch, ch, input), " <static> <static>");
    std::string long_input;
    for (int i = 0; i < 5000; ++i) long_input += "x ";
    char *output = static_text(ch, ch, &long_input[0]);
    std::string expected;
    for (int i = 1; i < 5000; ++i) expected += " <static>";
    assert(expected == output);
    free_string(output);
    town_blackout = blackout;
    puts("PASS: append spacing, complete expanded text and column truncation.");
}

static void test_file_bytes() {
    FILE *file = tmpfile();
    assert(file);
    const char text[] = "A\xae\xffZ";
    fwrite(text, 1, sizeof(text) - 1, file);
    fputc('\n', file);
    rewind(file);
    expect(fread_string_eol(file), text);
    fclose(file);
    file = tmpfile();
    assert(file);
    fwrite(text, 1, sizeof(text) - 1, file);
    fputc('~', file);
    rewind(file);
    expect(fread_string(file), text);
    fclose(file);
    puts("PASS: file strings preserve high bytes and distinguish 0xff from EOF.");
}

static std::string who_output(CHAR_DATA *ch, const char *argument) {
    ch->desc->outtop = 0;
    ch->desc->outbuf[0] = '\0';
    do_who(ch, const_cast<char *>(argument));
    return ch->desc->outbuf;
}

static void test_who(CHAR_DATA *ch) {
    auto saved_descriptors = descriptor_list;
    descriptor_list.clear();
    ch->lines = 0;
    for (int width : {80, 100, 320}) {
        ch->linewidth = width;
        std::string output = who_output(ch, "list");
        assert(output == who_output(ch, ""));
        for (const char *category : {"Immortals", "Entities", "Players"}) {
            std::string section = std::string(category) + ":\n\r," +
                std::string(width - 2, '_') + ",\n\r|" +
                std::string(width - 2, '_') + "|\n\r";
            assert(output.find(section) != std::string::npos);
        }
        assert(output.find("Characters Online: 0") != std::string::npos);
        assert(output.find("Characters Visible: 0") != std::string::npos);
        size_t footer = output.find(" Characters Online:");
        assert(output.find('\n', footer) - footer == size_t(width - 4));
        assert(output.find("SRs Online: 0 | SRs Working: 0") != std::string::npos);
        assert(output.find("Immortals Online: 0 | Immortals Hidden: 0") != std::string::npos);
    }
    ch->linewidth = 80;
    ch->pcdata->account = new_account();
    assign(ch->pcdata->account->name, "WhoAudit");
    ch->desc->connected = CON_PLAYING;
    descriptor_list.push_back(ch->desc);
    assign(ch->pcdata->whotitle, " `Rhas a colored status`x");
    std::string output = who_output(ch, "list");
    assert(output == who_output(ch, ""));
    assert(output.find("Characters Online: 1") != std::string::npos);
    assert(output.find("Immortals Online: 1 | Immortals Hidden: 0") != std::string::npos);
    size_t name = output.find("MemoryAudit");
    assert(name != std::string::npos);
    size_t start = output.rfind('|', name);
    size_t end = output.find('|', name);
    assert(end - start + 1 == 80);
    assert(name - start == 14);
    assert(output.find("has a colored status") != std::string::npos);
    assign(ch->pcdata->crank, "`226LongColoredRank");
    assign(ch->pcdata->whotitle, (" `R" + std::string(200, 'z') + "`x").c_str());
    output = who_output(ch, "list");
    name = output.find("MemoryAudit");
    start = output.rfind('|', name);
    end = output.find('|', name);
    assert(end - start + 1 == 80 && name - start == 14);
    assert(output.find("LongColoredR") != std::string::npos);
    assert(output.find(std::string(52, 'z')) != std::string::npos);
    const int level = ch->level, trust = ch->trust;
    ch->level = ch->trust = 2;
    SET_FLAG(ch->act, PLR_GM);
    SET_FLAG(ch->comm, COMM_STORY);
    output = who_output(ch, "list");
    assert(output.find("SRs Online: 1 | SRs Working: 1") != std::string::npos);
    REMOVE_FLAG(ch->act, PLR_GM);
    REMOVE_FLAG(ch->comm, COMM_STORY);
    output = who_output(ch, "list");
    assert(output.find("MemoryAudit") > output.find("Players:"));
    for (int i = 1; i < 30; ++i)
        descriptor_list.push_back(ch->desc);
    output = who_output(ch, "list");
    assert(output.find("Characters Online: 30") != std::string::npos);
    size_t rows = 0, position = 0;
    while ((position = output.find("MemoryAudit", position)) != std::string::npos) {
        ++rows;
        ++position;
    }
    assert(rows == 30);
    descriptor_list.clear();
    descriptor_list.push_back(ch->desc);
    SET_FLAG(ch->comm, COMM_AFK);
    SET_FLAG(ch->comm, COMM_QUIET);
    output = who_output(ch, "list");
    assert(output.find("[AFK] [QUIET] MemoryAudit") != std::string::npos);
    REMOVE_FLAG(ch->comm, COMM_AFK);
    REMOVE_FLAG(ch->comm, COMM_QUIET);
    ch->level = level;
    ch->trust = trust;
    SET_FLAG(ch->act, PLR_SPYSHIELD);
    output = who_output(ch, "list");
    assert(output.find("Characters Visible: 0") != std::string::npos);
    assert(output.find("Immortals Online: 1 | Immortals Hidden: 1") != std::string::npos);
    REMOVE_FLAG(ch->act, PLR_SPYSHIELD);
    SET_FLAG(ch->act, PLR_COLOR);
    output = who_output(ch, "list");
    assert(output.find("\033[") != std::string::npos);
    REMOVE_FLAG(ch->act, PLR_COLOR);
    descriptor_list = saved_descriptors;
    puts("PASS: who/list equivalence, full-width empty sections at 80/100/320, aligned colored row and population footer.");
}

int main() {
    setvbuf(stdout, nullptr, _IONBF, 0);
    for (size_t size : {1, 3, 4, 7, 16, 31, 64}) {
        assert(reinterpret_cast<uintptr_t>(alloc_perm(size)) % alignof(std::max_align_t) == 0);
        void *block = alloc_mem(size);
        assert(reinterpret_cast<uintptr_t>(block) % alignof(std::max_align_t) == 0);
        memset(block, 0x5a, size);
        free_mem(block, size);
        block = alloc_mem(size);
        assert(reinterpret_cast<uintptr_t>(block) % alignof(std::max_align_t) == 0);
        free_mem(block, size);
    }
    puts("PASS: permanent and recycled allocation alignment.");
    current_time = time(nullptr);
    strcpy(str_boot_time, ctime(&current_time));
    boot_db();
    auto *ch = new_char();
    ch->pcdata = new_pcdata();
    assign(ch->name, "MemoryAudit");
    ch->level = ch->trust = MAX_LEVEL;
    ch->position = POS_STANDING;
    char_to_room(ch, get_room_index(16068));
    ch->desc = new_descriptor();
    ch->desc->character = ch;
    assert(discipline_table_count > 0 && skill_table_count > 0);
    bool found_speargun = false, found_hotspec = false;
    for (int i = 0; i < discipline_table_count; ++i) {
        const auto &entry = discipline_table[i];
        assert(entry.vnum > 0 && static_cast<size_t>(entry.vnum) < sizeof(ch->disciplines) / sizeof(ch->disciplines[0]));
        assert(entry.name && *entry.name);
        found_speargun |= entry.vnum == DIS_SPEARGUN;
    }
    bool known_skills[SKILL_MAX] = {};
    for (int i = 0; i < skill_table_count; ++i) {
        const auto &entry = skill_table[i];
        assert(entry.vnum > 0 && entry.vnum < SKILL_MAX);
        assert(static_cast<size_t>(entry.vnum) < sizeof(ch->skills) / sizeof(ch->skills[0]));
        assert(entry.name && *entry.name);
        assert(!strcmp(skill_name(entry.vnum), entry.name));
        known_skills[entry.vnum] = true;
        found_hotspec |= entry.vnum == SKILL_HOTSPEC;
    }
    assert(found_speargun && found_hotspec);
    const auto &last_skill = skill_table[skill_table_count - 1];
    assert(!strcmp(skill_name(last_skill.vnum), last_skill.name));
    assert(!strcmp(skill_name(SKILL_HOTSPEC), "Hot Specialization"));
    int unknown_skill = SKILL_MAX - 1;
    while (unknown_skill > 0 && known_skills[unknown_skill]) --unknown_skill;
    assert(!strcmp(skill_name(unknown_skill), ""));
    assert(shield_total(ch) == 0);
    puts("PASS: table iteration includes final IDs and safely handles an unknown skill.");
    test_allocators();
    ch->pcdata->last_shower = current_time;
    assert(skin_face_score(ch) == 100.0f);
    ch->pcdata->last_shower = current_time - 60 * 8;
    assert(skin_face_score(ch) == 96.0f);
    ch->pcdata->last_shower = 0;
    assert(skin_face_score(ch) == 0.0f);
    puts("PASS: skin score handles recent and long-absent showers without integer overflow.");
    test_descriptions(ch);
    test_objects(ch);
    test_dorms(ch);
    test_appends(ch);
    test_file_bytes();
    test_who(ch);
    test_build_safety(ch);
    ch->pcdata->storycon[9][0] = 1;
    ch->pcdata->storycon[9][2] = 2;
    scon_update(ch);
    assert(ch->pcdata->storycon[9][2] == 1);
    puts("PASS: story condition final slot updates.");
}
