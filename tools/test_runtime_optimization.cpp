#include "merc.h"
#include "recycle.h"
#include "runtime_io.h"
#include "equipment_snapshot.h"
#include <cassert>
#include <cstring>
#include <cmath>
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/wait.h>

extern "C" {
extern char str_boot_time[];
void fight_update(void);
bool can_get_wet(CHAR_DATA *, int);
void wetify(CHAR_DATA *);
void dry(CHAR_DATA *);
void snowify(CHAR_DATA *);
void fread_grouptext(FILE *);
void do_grouptext(CHAR_DATA *, char *);
void fread_texthistory(FILE *);
void fread_profile(FILE *);
void string_append(CHAR_DATA *, char **);
void string_add(CHAR_DATA *, char *);
float fashion_score(CHAR_DATA *);
float phys_score(CHAR_DATA *);
int get_jewelry_cost(CHAR_DATA *);
int get_clothes_cost(CHAR_DATA *);
int get_obj_cover_amount(OBJ_DATA *, CHAR_DATA *, int);
bool has_shapewear_body(CHAR_DATA *);
bool has_shapewear_height(CHAR_DATA *);
bool is_obj_reset(OBJ_DATA *, ROOM_INDEX_DATA *);
void fwrite_obj_2(OBJ_DATA *, FILE *, int);
void ai_operation_job(void);
FILE *__real_open_snapshot_file(const char *);
int __real_close_snapshot_file(FILE *);
OBJ_DATA *__real_get_eq_char(CHAR_DATA *, int);
FACTION_TYPE *__real_clan_lookup(int);
char *__real_str_dup(const char *);
}
static int group_serializations = 0;
static bool fail_group_save = false;
static std::map<std::string, int> serializations;
static std::string fail_open;
static bool fail_close = false;
static int equipment_lookups = 0, faction_lookups = 0, string_copies = 0;
extern "C" OBJ_DATA *__wrap_get_eq_char(CHAR_DATA *ch, int slot) {
    ++equipment_lookups; return __real_get_eq_char(ch, slot);
}
extern "C" FACTION_TYPE *__wrap_clan_lookup(int vnum) {
    ++faction_lookups; return __real_clan_lookup(vnum);
}
extern "C" char *__wrap_str_dup(const char *value) {
    ++string_copies; return __real_str_dup(value);
}
extern "C" int __wrap_close_snapshot_file(FILE *stream) {
    const int result = __real_close_snapshot_file(stream);
    return fail_close ? EOF : result;
}
extern "C" FILE *__wrap_open_snapshot_file(const char *path) {
    ++serializations[path];
    if (fail_open == path) return nullptr;
    if (!strcmp(path, GROUPTEXT_FILE)) {
        ++group_serializations;
        if (fail_group_save) return nullptr;
    }
    return __real_open_snapshot_file(path);
}
static void write_file(const std::string &path, const std::string &s, bool append = false) {
    FILE *f = fopen(path.c_str(), append ? "ab" : "wb"); assert(f);
    assert(fwrite(s.data(), 1, s.size(), f) == s.size()); assert(fclose(f) == 0);
}
static std::string read_file(const std::string &path) {
    std::ifstream f(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(f), {});
}
static struct stat file_stat(const std::string &path) {
    struct stat s; assert(stat(path.c_str(), &s) == 0); return s;
}
static void restart_pop(const char *binary, const char *path, const char *expected) {
    pid_t pid = fork(); assert(pid >= 0);
    if (!pid) { execl(binary, binary, "pop", path, expected, nullptr); _exit(127); }
    int status; assert(waitpid(pid, &status, 0) == pid);
    assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
}
static void queue_tests(const char *binary) {
    const char *path = "queue-test.csv";
    write_file(path, "one\r\ntwo\npartial");
    const auto original = file_stat(path);
    assert(haven::pop_file_line(path) == "one");
    auto after = file_stat(path);
    assert(after.st_ino == original.st_ino && after.st_size == original.st_size);
    restart_pop(binary, path, "two");
    assert(haven::pop_file_line(path).empty());
    write_file(path, "-end\n\nlast\n", true);
    assert(haven::pop_file_line(path) == "partial-end");
    assert(haven::pop_file_line(path).empty()); // Blank records advance.
    const int lock = open("queue-test.csv.lock", O_RDWR); assert(lock >= 0);
    assert(flock(lock, LOCK_EX | LOCK_NB) == 0);
    assert(haven::pop_file_line(path).empty());
    close(lock);
    restart_pop(binary, path, "last");
    assert(haven::pop_file_line(path).empty());
    write_file("replacement.csv", "replacement\n");
    assert(rename("replacement.csv", path) == 0);
    assert(haven::pop_file_line(path) == "replacement");
    // Truncation resets a cursor beyond EOF.
    write_file(path, "x\n");
    assert(haven::pop_file_line(path) == "x");
    write_file("compact.csv", std::string(1024 * 1024, 'a') + "\nnext\npartial");
    auto before_compact = file_stat("compact.csv");
    assert(haven::pop_file_line("compact.csv").size() == 1024 * 1024);
    assert(file_stat("compact.csv").st_ino != before_compact.st_ino);
    assert(read_file("compact.csv") == "next\npartial");
    restart_pop(binary, "compact.csv", "next");
    write_file("compact.csv", "-done\n", true);
    restart_pop(binary, "compact.csv", "partial-done");
    // An unreadable/uncommittable cursor must not acknowledge the record.
    write_file("failed.csv", "retry\n");
    assert(mkdir("failed.csv.cursor", 0700) == 0);
    assert(haven::pop_file_line("failed.csv").empty());
    assert(rmdir("failed.csv.cursor") == 0);
    assert(haven::pop_file_line("failed.csv") == "retry");
    puts("PASS: queue cursor, restart, lock contention, partial records, replacement and compaction");
}
static void equipment_tests() {
    CHAR_DATA ch = {};
    std::vector<OBJ_DATA> items(205);
    for (size_t i = 0; i < items.size(); ++i) {
        items[i].next_content = i + 1 < items.size() ? &items[i+1] : nullptr;
        items[i].wear_loc = WEAR_NONE;
    }
    ch.carrying = items.data();
    items[2].wear_loc = WEAR_HOLD_2;
    items[199].wear_loc = WEAR_BODY_1;
    items[200].wear_loc = WEAR_BODY_2; // Historical 200-item limit.
    for (int pass = 0; pass < 3; ++pass) {
        haven::EquipmentSnapshot eq(&ch);
        for (int slot = 0; slot < MAX_WEAR; ++slot)
            assert(eq.get(slot) == get_eq_char(&ch, slot));
        if (!pass) items[3].wear_loc = WEAR_HOLD;
        else items[0].wear_loc = WEAR_HOLD; // First duplicate wins.
    }
    assert(haven::EquipmentSnapshot(nullptr).get(WEAR_BODY_1) == nullptr);
    puts("PASS: equipment snapshot matches legacy lookup, limits, duplicates and hand fallback");
}
static void combat_tests() {
    CHAR_DATA older = {}, middle = {}, newer = {}, spawned = {}, offline = {};
    register_live_character(&older); register_live_character(&middle); register_live_character(&newer);
    set_combat_state(&newer, true); set_combat_state(&older, true);
    unsigned long long cursor = 0;
    assert(next_combat_character(&cursor) == &newer);
    unregister_live_character(&newer); // Removing current/next must not invalidate iteration.
    set_combat_state(&middle, true);
    register_live_character(&spawned); set_combat_state(&spawned, true);
    assert(next_combat_character(&cursor) == &middle);
    unregister_live_character(&older);
    assert(next_combat_character(&cursor) == nullptr);
    cursor = 0; assert(next_combat_character(&cursor) == &spawned);
    set_combat_state(&middle, false);
    assert(next_combat_character(&cursor) == nullptr);
    unregister_live_character(&middle); unregister_live_character(&spawned);
    set_combat_state(&offline, true);
    cursor = 0; assert(next_combat_character(&cursor) == nullptr);
    register_live_character(&offline);
    assert(next_combat_character(&cursor) == &offline);
    unregister_live_character(&offline);
    // Reusing a character address must create a new position.
    register_live_character(&older); set_combat_state(&older, true);
    cursor = 0; assert(next_combat_character(&cursor) == &older);
    unregister_live_character(&older);
    puts("PASS: combat ordering, activation during iteration, removal, spawn and address reuse");
}
static void faction_tests() {
    auto saved = FacVect;
    FACTION_TYPE a = {}, b = {}, duplicate = {};
    a.vnum = 901; b.vnum = 902; duplicate.vnum = 901;
    FacVect = {&a, &b, &duplicate}; invalidate_faction_index();
    assert(clan_lookup(901) == &a && clan_lookup(902) == &b && !clan_lookup(999));
    a.vnum = 903; invalidate_faction_index();
    assert(clan_lookup(901) == &duplicate && clan_lookup(903) == &a);
    duplicate.vnum = 903; std::reverse(FacVect.begin(), FacVect.end()); invalidate_faction_index();
    assert(clan_lookup(903) == &duplicate);
    FacVect.clear(); assert(!clan_lookup(903));
    FacVect = saved; invalidate_faction_index();
    puts("PASS: faction index preserves misses, first match, renumbering and ordering");
}
static void operation_job_tests() {
    const auto saved_ops = OpVect;
    const auto saved_factions = FacVect;
    const auto saved_locations = locationVect;
    const auto saved_queue = read_file(AI_IN_FILE);
    ai_operation_job(); // Exercise the operations loaded from the current world, too.
    FACTION_TYPE faction = {};
    faction.vnum = 901; faction.name = (char *)"Antagonist"; faction.antagonist = 1;
    LOCATION_TYPE territory = {};
    territory.name = (char *)"Test territory"; territory.continent = 1; territory.valid = TRUE;
    FacVect = {&faction}; invalidate_faction_index();
    locationVect = {&territory};
    OPERATION_TYPE valid = {};
    valid.valid = TRUE; valid.description = (char *)"";
    valid.faction = faction.vnum; valid.territoryvnum = 1;
    auto missing_faction = valid; missing_faction.faction = 999;
    auto missing_territory = valid; missing_territory.territoryvnum = 999;
    auto zero_territory = valid; zero_territory.territoryvnum = 0;
    auto no_description = valid; no_description.description = nullptr;
    auto completed = valid; completed.description = (char *)"0123456789";
    auto removed = valid; removed.valid = FALSE;
    OpVect = {nullptr, &missing_faction, &missing_territory, &zero_territory, &no_description,
              &completed, &removed, &valid};
    write_file(AI_IN_FILE, "existing\n");
    ai_operation_job();
    assert(read_file(AI_IN_FILE) == "existing\n2,0,Antagonist,\"Test territory\",,,\n");

    OpVect = {&valid};
    write_file(AI_IN_FILE, "");
    faction.antagonist = 0; ai_operation_job();
    faction.antagonist = 1; faction.name = nullptr; ai_operation_job();
    faction.name = (char *)"Antagonist"; territory.name = nullptr; ai_operation_job();
    assert(read_file(AI_IN_FILE).empty());

    std::string long_name(MSL * 2, 'x');
    faction.name = const_cast<char *>(long_name.c_str()); territory.name = (char *)"Test territory";
    valid.description = (char *)"123456789";
    ai_operation_job();
    assert(read_file(AI_IN_FILE) == "2,0," + long_name + ",\"Test territory\",,,\n");
    OpVect = saved_ops; FacVect = saved_factions; locationVect = saved_locations;
    invalidate_faction_index(); write_file(AI_IN_FILE, saved_queue);

    for (int vnum : {294, 295, 296}) {
        auto *object = get_obj_index(vnum);
        assert(object && object->item_type == ITEM_TRASH);
    }
    puts("PASS: operation AI skips invalid records, preserves eligible jobs and handles long names; limbo object types load");
}
static void group_save_tests() {
    auto saved = GTextVect; GTextVect.clear(); mark_grouptexts_dirty();
    current_time = 2000000000;
    FILE *input = tmpfile(); assert(input);
    fprintf(input, "TName runtime-test~\nLastMsg %ld\nNumber 0 42\nHistory original~\nEnd\n",
            static_cast<long>(current_time - 3600 * 24 * 90));
    rewind(input); fread_grouptext(input); fclose(input);
    const int start = group_serializations;
    save_grouptexts(); assert(group_serializations == start + 1);
    assert(read_file(GROUPTEXT_FILE).find("runtime-test") != std::string::npos);
    save_grouptexts(); assert(group_serializations == start + 1);
    ++current_time; save_grouptexts(); assert(group_serializations == start + 2);
    assert(read_file(GROUPTEXT_FILE).find("runtime-test") == std::string::npos);
    save_grouptexts(); assert(group_serializations == start + 2);
    --current_time; save_grouptexts(); // Clock rewind restores eligible records.
    assert(group_serializations == start + 3);
    assert(read_file(GROUPTEXT_FILE).find("runtime-test") != std::string::npos);
    mark_grouptexts_dirty(); fail_group_save = true; save_grouptexts();
    fail_group_save = false; save_grouptexts(); assert(group_serializations == start + 5);
    save_grouptexts(); assert(group_serializations == start + 5);
    assert(unlink(GROUPTEXT_FILE) == 0); save_grouptexts(); assert(group_serializations == start + 6);
    GTextVect = saved; mark_grouptexts_dirty();
    puts("PASS: clean saves skip serialization; expiry, clock rewind, failed saves and missing files retry");
}
static void assign(char *&field, const char *value) {
    free_string(field); field = str_dup(value);
}
static CHAR_DATA *test_player(const char *name) {
    auto *ch = new_char(); ch->pcdata = new_pcdata();
    assign(ch->name, name); ch->race = RACE_HUMAN; ch->level = 2;
    ch->position = POS_STANDING; ch->shape = SHAPE_HUMAN;
    ch->desc = new_descriptor(); ch->desc->character = ch;
    ch->desc->connected = CON_PLAYING;
    char_to_room(ch, get_room_index(16068));
    char_list.push_front(ch); register_live_character(ch);
    return ch;
}
static OBJ_DATA *test_item(CHAR_DATA *ch, int type, const char *name, int slot) {
    auto *obj = create_object(get_obj_index(OBJ_VNUM_PHONE), 0);
    obj->item_type = type; assign(obj->name, name);
    REMOVE_BIT(obj->extra_flags, ITEM_OFF);
    REMOVE_BIT(obj->extra_flags, ITEM_WATERPROOF);
    obj_to_char(obj, ch); obj->wear_loc = slot;
    return obj;
}
static void gameplay_tests() {
    auto *ch = test_player("RuntimeWeather");
    assert(!in_water(ch));
    auto *coat = test_item(ch, ITEM_CLOTHING, "cotton shirt", WEAR_BODY_1);
    coat->value[4] = 0;
    assert(can_get_wet(ch, WEAR_BODY_1));
    wetify(ch); assert(coat->value[4] == 3);
    dry(ch); assert(coat->value[4] == 2);
    snowify(ch); assert(coat->value[4] == 3);
    auto *umbrella = test_item(ch, ITEM_UMBRELLA, "umbrella", WEAR_HOLD_2);
    assert(!can_get_wet(ch, WEAR_BODY_1));
    wetify(ch); snowify(ch); assert(coat->value[4] == 3);
    SET_BIT(umbrella->extra_flags, ITEM_OFF);
    assert(can_get_wet(ch, WEAR_BODY_1));
    wetify(ch); assert(coat->value[4] == 6);
    SET_BIT(coat->extra_flags, ITEM_WATERPROOF);
    assert(!can_get_wet(ch, WEAR_BODY_1));
    assert(!can_get_wet(ch, WEAR_BODY_2)); // Empty slot is safe.
    puts("PASS: real weather preserves wetting, drying, snow, umbrellas and waterproof clothing");

    auto *idle = test_player("RuntimeIdle");
    ch->caff[0] = idle->caff[0] = 0;
    ch->caff_duration[0] = idle->caff_duration[0] = 5;
    ch->fight_fast = idle->fight_fast = TRUE;
    set_combat_state(ch, true);
    fight_update();
    assert(ch->caff_duration[0] == 4 && idle->caff_duration[0] == 5);
    set_combat_state(ch, false); fight_update();
    assert(ch->caff_duration[0] == 4);
    puts("PASS: real combat tick updates active characters and leaves idle characters untouched");

    auto *phone = test_item(ch, ITEM_PHONE, "phone", WEAR_HOLD);
    phone->value[0] = 990011;
    save_grouptexts();
    auto command = [&](const char *value) {
        char input[MSL]; snprintf(input, sizeof(input), "%s", value);
        do_grouptext(ch, input);
    };
    int calls = group_serializations;
    command("create runtime-group"); save_grouptexts();
    assert(group_serializations == ++calls);
    assert(read_file(GROUPTEXT_FILE).find("runtime-group") != std::string::npos);
    command("list"); save_grouptexts(); assert(group_serializations == calls);
    command("addnumber runtime-group 990012"); save_grouptexts();
    assert(group_serializations == ++calls);
    assert(read_file(GROUPTEXT_FILE).find("Number 1 990012") != std::string::npos);
    command("leave runtime-group"); save_grouptexts();
    assert(group_serializations == ++calls);
    assert(read_file(GROUPTEXT_FILE).find("Number 0 990011") == std::string::npos);
    puts("PASS: real group create/add/leave commands invalidate saves; listing does not");
}
static void phonebook_tests() {
    const auto saved = PhoneVect;
    PhoneVect.clear(); invalidate_phonebook_index();
    update_phonebook(1234, (char *)"First");
    auto *first = PhoneVect.front();
    auto *duplicate = new_phonebook(); duplicate->number = 1234;
    assign(duplicate->owner, "Duplicate"); PhoneVect.push_back(duplicate);
    auto *appended = new_phonebook(); appended->number = 5678;
    PhoneVect.push_back(appended);
    update_phonebook(5678, (char *)"Append");
    const int copies = string_copies;
    for (int i = 0; i < 1000; ++i) {
        first->inactivity = 99;
        update_phonebook(1234, first->owner);
        assert(first->inactivity == 0);
    }
    assert(string_copies == copies);
    update_phonebook(1234, (char *)"FIRST");
    assert(!strcmp(first->owner, "FIRST") && !strcmp(duplicate->owner, "Duplicate"));
    std::reverse(PhoneVect.begin(), PhoneVect.end()); invalidate_phonebook_index();
    update_phonebook(1234, (char *)"NowFirst");
    assert(!strcmp(duplicate->owner, "NowFirst"));
    appended->number = 9999; invalidate_phonebook_index();
    update_phonebook(9999, (char *)"Renumbered");
    assert(PhoneVect.size() == 3 && !strcmp(appended->owner, "Renumbered"));
    PhoneVect = saved; invalidate_phonebook_index();
    puts("PASS: phone index handles append, duplicates, reorder and renumber; 1000 unchanged updates copy no strings");
}

static void social_save_tests() {
    const auto histories = HTextVect;
    const auto profiles = ProfileVect;
    HTextVect.clear(); ProfileVect.clear();
    mark_texthistories_dirty(); mark_profiles_dirty();
    current_time = 2000000000;
    for (bool profile : {false, true}) {
        const char *path = profile ? PROFILE_FILE : TEXTHISTORY_FILE;
        auto save = profile ? save_profiles : save_texthistories;
        auto dirty = profile ? mark_profiles_dirty : mark_texthistories_dirty;
        FILE *input = tmpfile(); assert(input);
        if (profile)
            fprintf(input, "Name runtime-profile~\nHandle runtime~\nLastActive %ld\nEnd\n",
                    static_cast<long>(current_time - 3600 * 24 * 90));
        else
            fprintf(input, "NameOne runtime-history~\nNameTwo second~\nHistory original~\nLastMsg %ld\nEnd\n",
                    static_cast<long>(current_time - 3600 * 24 * 90));
        rewind(input);
        if (profile) fread_profile(input); else fread_texthistory(input);
        fclose(input);
        int calls = serializations[path];
        save(); assert(serializations[path] == ++calls);
        assert(read_file(path).find("runtime-") != std::string::npos);
        save(); assert(serializations[path] == calls);
        ++current_time; save(); assert(serializations[path] == ++calls);
        assert(read_file(path) == "#END\n");
        save(); assert(serializations[path] == calls);
        --current_time; save(); assert(serializations[path] == ++calls);
        assert(read_file(path).find("runtime-") != std::string::npos);
        dirty(); fail_open = path; save(); assert(serializations[path] == ++calls);
        fail_open.clear(); save(); assert(serializations[path] == ++calls);
        save(); assert(serializations[path] == calls);
        dirty(); fail_close = true; save(); assert(serializations[path] == ++calls);
        fail_close = false; save(); assert(serializations[path] == ++calls);
        save(); assert(serializations[path] == calls);
        assert(unlink(path) == 0);
        fail_close = true; save(); assert(serializations[path] == ++calls);
        fail_close = false; save(); assert(serializations[path] == ++calls);
        save(); assert(serializations[path] == calls);
    }
    auto *profile = ProfileVect.front();
    auto *ch = test_player("RuntimeEditor");
    string_append(ch, &profile->profile);
    save_profiles();
    int calls = serializations[PROFILE_FILE];
    char first[] = "First edit"; string_add(ch, first); save_profiles();
    assert(serializations[PROFILE_FILE] == ++calls);
    char second[] = "Second edit"; string_add(ch, second); save_profiles();
    assert(serializations[PROFILE_FILE] == ++calls);
    assert(read_file(PROFILE_FILE).find("Second edit") != std::string::npos);
    ch->desc->pString = nullptr;
    edit_profile(profile)->rating = 42; save_profiles();
    assert(serializations[PROFILE_FILE] == ++calls);
    assert(read_file(PROFILE_FILE).find("Rating 42\n") != std::string::npos);
    profile_lookup(profile->name); save_profiles();
    assert(serializations[PROFILE_FILE] == calls);
    HTextVect = histories; ProfileVect = profiles;
    mark_texthistories_dirty(); mark_profiles_dirty();
    puts("PASS: history/profile dirty saves, expiry, rewind, open/close failure, missing files and editor sessions");
}

static void snapshot_backup_tests() {
    assert(haven::ensure_backup_directories());
    const auto saved_objects = object_list;
    object_list.clear();
    auto *object = create_object(get_obj_index(OBJ_VNUM_PHONE), 0);
    assign(object->name, "runtime-ground");
    obj_to_room(object, get_room_index(16068));
    char *bytes = nullptr; size_t size = 0;
    FILE *reference = open_memstream(&bytes, &size); assert(reference);
    if (!is_obj_reset(object, object->in_room)) fwrite_obj_2(object, reference, 0);
    fprintf(reference, "#END\n"); assert(fclose(reference) == 0);
    const std::string expected(bytes, size); free(bytes);
    assert(expected.find("runtime-ground") != std::string::npos);
    const char *roots[] = {BACK1_DIR, BACK2_DIR, BACK3_DIR, BACK4_DIR, BACK5_DIR, BACK6_DIR, BACK7_DIR};
    const int saved_day = time_info.day;
    for (int day = 1; day <= 7; ++day) {
        time_info.day = day;
        const std::string backup = std::string(roots[7 - day]) + "GroundObjects";
        const int calls = serializations[std::string(PLAYER_DIR) + "GroundObjects"];
        const int backup_calls = serializations[backup];
        save_ground_objects();
        assert(serializations[std::string(PLAYER_DIR) + "GroundObjects"] == calls + 1);
        assert(serializations[backup] == backup_calls); // No second serialization buffer.
        assert(read_file(std::string(PLAYER_DIR) + "GroundObjects") == expected);
        assert(read_file(backup) == expected);
    }
    time_info.day = saved_day;
    obj_from_room(object); object_list = saved_objects;
    FILE *stream = open_snapshot_file("missing-primary/snapshot"); assert(stream);
    fputs("backup survives\n", stream);
    assert(close_snapshot_file_with_backup(stream, "snapshot-backup") == EOF);
    assert(read_file("snapshot-backup") == "backup survives\n");
    stream = open_snapshot_file("snapshot-primary"); assert(stream);
    fputs("primary survives\n", stream);
    assert(close_snapshot_file_with_backup(stream, "missing-backup/snapshot") == EOF);
    assert(read_file("snapshot-primary") == "primary survives\n");
    puts("PASS: ground bytes match legacy serialization in all seven backups; destinations fail independently");
}

static void appearance_tests() {
    auto *ch = test_player("RuntimeAppearance");
    for (int pass = 0; pass < 5; ++pass) {
        if (pass == 1) {
            auto *clothing = test_item(ch, ITEM_CLOTHING, "corset", WEAR_BODY_1);
            clothing->cost = 31000; clothing->value[2] = 40;
        }
        if (pass == 2) {
            auto *jewel = test_item(ch, ITEM_JEWELRY, "ring", WEAR_HOLD_2);
            jewel->cost = 5900;
        }
        if (pass == 3) {
            auto *clothing = test_item(ch, ITEM_CLOTHING, "heels", WEAR_BODY_2);
            clothing->value[2] = 10;
            SET_FLAG(ch->comm, COMM_BLINDFOLD);
            ch->pcdata->exposed[0] = 111;
        }
        if (pass == 4) {
            // Push worn items past the historical 200-item search boundary.
            for (int i = 0; i < 201; ++i) test_item(ch, ITEM_TRASH, "filler", WEAR_NONE);
        }
        int clothes = 0, jewelry = 0, coverage = 0, exposed = 0;
        bool body = false, height = false;
        for (int slot = 0; slot < MAX_WEAR; ++slot) {
            OBJ_DATA *obj = get_eq_char(ch, slot);
            if (!obj) continue;
            const int cost = can_see_wear(ch, slot) ? obj->cost : obj->cost / 3;
            if (obj->item_type == ITEM_JEWELRY) jewelry += cost;
            if (obj->item_type == ITEM_CLOTHING) {
                clothes += cost;
                body |= obj->value[2] > 30 || is_name("corset", obj->name)
                    || is_name("shapewear", obj->name) || is_name("girdle", obj->name);
                height |= obj->value[2] > 1 && obj->value[2] < 20;
            }
            coverage += get_obj_cover_amount(obj, ch, slot);
        }
        for (int cover = 0; cover < MAX_COVERS; ++cover) {
            bool covered = IS_FLAG(ch->comm, COMM_BLINDFOLD) && cover == COVERS_EYES;
            bool explicitly_exposed = false;
            for (int i = 0; i < MAX_COVERS; ++i)
                if (cover_table[i] == cover && ch->pcdata->exposed[i] == 111) explicitly_exposed = true;
            if (!covered && !explicitly_exposed)
                for (int slot = 0; slot < MAX_WEAR; ++slot) {
                    auto *obj = get_eq_char(ch, slot);
                    if (obj && does_cover(obj, cover)) covered = true;
                }
            if (!covered) ++exposed;
        }
        equipment_lookups = 0;
        assert(get_jewelry_cost(ch) == jewelry / 100);
        assert(get_clothes_cost(ch) == clothes / 100);
        const float expected = sqrt(static_cast<float>(jewelry / 100)) / 4
                             + sqrt(static_cast<float>(clothes / 100)) / 2;
        assert(fashion_score(ch) == expected);
        assert(phys_score(ch) == exposed * exposed - coverage);
        assert(has_shapewear_body(ch) == body && has_shapewear_height(ch) == height);
        assert(equipment_lookups == 0);
    }
    puts("PASS: appearance scores preserve clothing, jewelry, shapewear, blindfold, exposure and inventory limits without repeated equipment lookups");
}

static void territory_lookup_tests() {
    const auto factions = FacVect; const auto locations = locationVect;
    FACTION_TYPE faction = {}; faction.vnum = 901; faction.valid = TRUE;
    FacVect = {&faction}; invalidate_faction_index();
    std::vector<LOCATION_TYPE> territories(100);
    locationVect.clear();
    for (auto &loc : territories) {
        loc.valid = TRUE; loc.name = (char *)"test";
        loc.territory_bonus = TERRITORY_BEACH_BOD;
        locationVect.push_back(&loc);
    }
    auto *ch = test_player("RuntimeTerritory"); ch->fcore = 901;
    faction_lookups = 0;
    assert(!has_territory_bonus(ch, TERRITORY_BEACH_BOD));
    assert(faction_lookups <= 3);
    territories.back().base_faction_core = 901;
    assert(has_territory_bonus(ch, TERRITORY_BEACH_BOD));
    faction.antagonist = 1;
    assert(!has_territory_bonus(ch, TERRITORY_BEACH_BOD));
    faction.antagonist = 0; territories.back().base_faction_core = 0;
    assert(!has_territory_bonus(ch, TERRITORY_BEACH_BOD));
    FacVect = factions; locationVect = locations; invalidate_faction_index();
    puts("PASS: territory queries resolve at most three factions and immediately reflect control/eligibility changes");
}

int main(int argc, char **argv) {
    if (argc == 4 && !strcmp(argv[1], "pop")) {
        assert(haven::pop_file_line(argv[2]) == argv[3]); return 0;
    }
    setvbuf(stdout, nullptr, _IONBF, 0);
    queue_tests(argv[0]); equipment_tests(); combat_tests();
    current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time)); boot_db();
    faction_tests(); operation_job_tests(); group_save_tests(); gameplay_tests();
    phonebook_tests(); social_save_tests(); snapshot_backup_tests(); appearance_tests(); territory_lookup_tests();
    return 0;
}
