// Linked against the actual engine. Run via test_command_dispatch.py in WSL.
#include "merc.h"
#include "recycle.h"
#include "runtime_io.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <dlfcn.h>
#include <sys/stat.h>

extern "C" {
extern CMD_TYPE *command_hash[MAX_COMMAND_HASH];
extern char str_boot_time[];
extern DisabledList disabled_list;
}

static int south_calls, society_calls, prefix_calls;
static void south_probe(CHAR_DATA *, char *) { ++south_calls; }
static void society_probe(CHAR_DATA *, char *) { ++society_calls; }
static void prefix_probe(CHAR_DATA *, char *) { ++prefix_calls; }

static CMD_TYPE *named(const char *name) {
    for (auto *cmd = command_hash[LOWER(name[0]) % MAX_COMMAND_HASH]; cmd; cmd = cmd->next)
        if (!strcmp(cmd->name, name)) return cmd;
    return nullptr;
}

static void run(CHAR_DATA *ch, const char *input) {
    char buffer[MAX_INPUT_LENGTH];
    snprintf(buffer, sizeof(buffer), "%s", input);
    substitute_alias(ch->desc, buffer);
}

static void test_backups() {
    assert(haven::ensure_backup_directories());
    assert(haven::ensure_backup_directories()); // Existing directories are fine.
    for (const char *root : {"../data/", ACCOUNT_DIR, PLAYER_DIR}) {
        for (int slot = 1; slot <= 7; ++slot) {
            std::string path = std::string(root) + "back" + std::to_string(slot);
            struct stat info;
            assert(stat(path.c_str(), &info) == 0 && S_ISDIR(info.st_mode));
        }
    }
    const char *path = "../data/back2/command-test.txt";
    FILE *file = open_snapshot_file(path);
    assert(file);
    fputs("saved backup\n", file);
    assert(close_snapshot_file(file) == 0);
    file = fopen(path, "r");
    assert(file);
    char text[64];
    assert(fgets(text, sizeof(text), file) && !strcmp(text, "saved backup\n"));
    fclose(file);
    // A file occupying a directory name must be reported, never overwritten.
    assert(rmdir("../accounts/back3") == 0);
    file = fopen("../accounts/back3", "w");
    assert(file);
    fputs("keep", file);
    fclose(file);
    assert(!haven::ensure_backup_directories());
    file = fopen("../accounts/back3", "r");
    assert(file && fgets(text, sizeof(text), file) && !strcmp(text, "keep"));
    fclose(file);
    assert(unlink("../accounts/back3") == 0);
    assert(haven::ensure_backup_directories());
}

int main() {
    current_time = time(nullptr);
    strcpy(str_boot_time, ctime(&current_time));
    boot_db();
    test_backups();

    int commands = 0;
    for (int bucket = 0; bucket < MAX_COMMAND_HASH; ++bucket)
        for (auto *cmd = command_hash[bucket]; cmd; cmd = cmd->next) {
            if (!cmd->do_fun) fprintf(stderr, "Missing handler: %s (%s)\n", cmd->name, cmd->lookup_name);
            assert(cmd->do_fun);
            ++commands;
        }
    assert(commands > 500);
    assert(named("affect") && named("affects"));
    assert(named("affect")->do_fun == do_affect);
    assert(named("affects")->do_fun == do_affect);
    assert(find_command((char *)"affect") == named("affect"));
    assert(find_command((char *)"affects") == named("affects"));
    assert(named("society")->do_fun == do_society);
    assert(named("newalliance")->do_fun == do_newalliance);
    assert(named("s")->do_fun == do_south);
    assert(find_command((char *)"s") == named("s"));
    assert(find_command((char *)"society") == named("society"));
    assert(!find_command((char *)"") && !find_command(nullptr));

    CHAR_DATA *ch = new_char();
    if (!ch->pcdata) ch->pcdata = new_pcdata();
    ch->name = str_dup("CommandAudit");
    ch->level = ch->trust = MAX_LEVEL;
    ch->position = POS_STANDING;
    ch->in_room = get_room_index(16068);
    assert(ch->in_room);
    ch->desc = new_descriptor();
    ch->desc->character = ch;

    auto *south = named("s");
    auto *society = named("society");
    DO_FUN *real_south = south->do_fun;
    DO_FUN *real_society = society->do_fun;
    south->do_fun = south_probe;
    society->do_fun = society_probe;
    run(ch, "s");
    run(ch, "S");
    assert(south_calls == 2 && society_calls == 0);
    run(ch, "society");
    assert(society_calls == 1);
    society->do_fun = nullptr;
    run(ch, "s"); // The reported crash: broken society must not steal south.
    run(ch, "society"); // Explicit missing handler must not crash or fall through.
    assert(south_calls == 3 && society_calls == 1);
    assert(strstr(ch->desc->outbuf, "This command is unavailable"));

    // Runtime/editor-created commands can also have missing or empty Code.
    void *handle = dlopen(nullptr, RTLD_LAZY);
    assert(handle);
    auto *missing = new_command();
    missing->name = str_dup("zzmissing");
    missing->lookup_name = str_dup("do_missing_test_handler");
    missing->do_fun = prefix_probe; // Failed lookup must clear a stale pointer.
    add_command(missing, handle);
    assert(!missing->do_fun);
    auto *working = new_command();
    working->name = str_dup("zzworking");
    working->lookup_name = str_dup("do_south");
    add_command(working, handle);
    assert(working->do_fun == do_south);
    working->do_fun = prefix_probe;
    run(ch, "zz");
    assert(prefix_calls == 1);
    run(ch, "zzmissing");
    assert(prefix_calls == 1);
    auto *empty = new_command();
    empty->name = str_dup("zzempty");
    add_command(empty, handle);
    assert(!empty->do_fun);
    run(ch, "zzempty");
    do_function(ch, nullptr, (char *)"");

    // Exact lookup still respects trust and disabled-handler aliases.
    working->level = MAX_LEVEL;
    ch->trust = ch->level = 1;
    run(ch, "zzworking");
    assert(prefix_calls == 1);
    run(ch, "s");
    assert(south_calls == 4);
    DISABLED_DATA disabled = {};
    disabled.command = south;
    named("south")->do_fun = south_probe;
    disabled_list.push_front(&disabled);
    run(ch, "s");
    run(ch, "south");
    assert(south_calls == 4);
    disabled_list.remove(&disabled);
    named("south")->do_fun = real_south;
    society->do_fun = real_society;
    south->do_fun = real_south;
    run(ch, "society select nonexistent-test-society");
    assert(strstr(ch->desc->outbuf, "Select a society you already belong to"));
    do_function(ch, do_newalliance, (char *)"");
    assert(strstr(ch->desc->outbuf, "You do not have permission to change alliances"));
    ch->trust = ch->level = MAX_LEVEL;
    run(ch, "newalliance invalid");
    assert(strstr(ch->desc->outbuf, "Syntax: newalliance"));
    run(ch, "newalliance");
    assert(strstr(ch->desc->outbuf, "Faction and society alliances recalculated"));
    run(ch, "south"); // Exercise the real movement handler too.
    printf("PASS: %d command handlers resolved; dispatch, permissions, missing handlers and backups verified.\n", commands);
}
