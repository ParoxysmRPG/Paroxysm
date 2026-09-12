#include "merc.h"
#include "recycle.h"
#include "global.h"
#include "olc.h"
#include "runtime_io.h"
#include "text_format.h"
#include <cassert>
#include <cstring>
#include <fstream>
#include <iterator>

extern "C" {
char *operation_location(OPERATION_TYPE *);
void show_operation_to_char(CHAR_DATA *, OPERATION_TYPE *);
char *newtimeline(char *, char *);
void do_decree(CHAR_DATA *, char *);
}

static void assign_text(char *&field, const char *text) {
    free_string(field);
    field = str_dup(text);
}

static void clear_output(CHAR_DATA *ch) {
    ch->desc->outtop = 0;
    ch->desc->outbuf[0] = '\0';
}

void test_build_safety(CHAR_DATA *ch) {
    for (int vnum : {294, 295, 296}) {
        assert(get_obj_index(vnum));
        assert(get_obj_index(vnum)->item_type == ITEM_TRASH);
    }
    const int editor = ch->desc->editor;
    ch->desc->editor = ED_SUBRACE;
    assert(!strcmp(olc_ed_name(ch), "SubraceEdit"));
    ch->desc->editor = editor;

    const std::string large(MSL + 100, 'z');
    assert(haven::format_text("%s/%s/%s", large.c_str(), large.c_str(), large.c_str())
           == large + "/" + large + "/" + large);
    assert(haven::format_text("[%08d] %-6s", 12, "ok") == "[00000012] ok    ");
    char *timeline = newtimeline(const_cast<char *>(large.c_str()), (char *)"last entry");
    assert(std::string(timeline).find(large) == 0);
    assert(std::string(timeline).find("last entry") != std::string::npos);
    free_string(timeline);
    char *boxed = text_complete_box((char *)"abc", (char *)"|", 8, false);
    assert(!strcmp(boxed, "||||||||\n|abc   |\n||||||||\n\r"));
    free_string(boxed);
    boxed = text_complete_box(const_cast<char *>(large.c_str()), (char *)"|", 80, true);
    assert(strstr(boxed, large.c_str()));
    free_string(boxed);

    clear_output(ch);
    printf_to_char(ch, "Prefix %s suffix", large.c_str());
    assert(strstr(ch->desc->outbuf, ("Prefix " + large + " suffix").c_str()));
    clear_output(ch);
    act_new(large.c_str(), ch, nullptr, nullptr, TO_CHAR, POS_DEAD);
    assert(strstr(ch->desc->outbuf, ("Z" + large.substr(1)).c_str()));
    clear_output(ch);
    act_new("literal$", ch, nullptr, nullptr, TO_CHAR, POS_DEAD);
    assert(strstr(ch->desc->outbuf, "Literal$"));

    std::string words;
    for (int i = 0; i < 8000; ++i) words += "word ";
    words += "end";
    const std::string wrapped = wrap_string(words.data(), 80);
    assert(wrapped.find("end") != std::string::npos);
    assert(words.back() == 'd'); // Wrapping must not alter its caller's string.
    assert(!strcmp(wrap_string((char *)"", 80), "\n\r"));
    assert(!strcmp(wrap_string((char *)"x", 80), "x\n\r"));
    puts("PASS: editor label, complete long formatted output, action expansion and wrapping.");

    const std::string compressed = "../data/" + std::string(120, 'x') + ";$() ' player.gz";
    assert(haven::decompress_player_file(compressed));
    const std::string plain = compressed.substr(0, compressed.size() - 3);
    std::ifstream file(plain);
    const std::string bytes((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    assert(bytes == "complete player data\n");
    assert(!haven::decompress_player_file("../data/invalid-player.gz"));
    assert(!haven::decompress_player_file("../data/missing-player.gz"));
    assert(haven::remove_optional_file(plain));
    assert(haven::remove_optional_file(plain));
    puts("PASS: gzip handles long literal filenames, corrupt/missing inputs and optional file deletion.");

    OPERATION_TYPE *op = new_operation();
    op->territoryvnum = 999999;
    op->faction = 999999;
    op->goal = GOAL_PSYCHIC;
    assert(!strcmp(operation_location(nullptr), "Somewhere"));
    assert(!strcmp(operation_location(op), "Somewhere"));
    assert(!strcmp(territory_name(-1), "Somewhere"));
    assert(!territory_leader(ch, nullptr));
    clear_output(ch);
    show_operation_to_char(ch, op);
    assert(strstr(ch->desc->outbuf, "Unknown faction"));
    op->goal = GOAL_CONTROL;
    clear_output(ch);
    show_operation_to_char(ch, op);
    assert(strstr(ch->desc->outbuf, "Territory: Somewhere"));
    assert(!strstr(ch->desc->outbuf, "Local time will be"));

    const auto old_decrees = DecreeVect;
    DECREE_TYPE *decree = new_decree();
    decree->territory_vnum = 999999;
    decree->btype = 1;
    DecreeVect = {decree};
    clear_output(ch);
    do_decree(ch, (char *)"list");
    assert(strstr(ch->desc->outbuf, "Lockdown in Somewhere"));
    clear_output(ch);
    do_decree(ch, (char *)"info 1");
    assert(strstr(ch->desc->outbuf, "Lockdown decree in Somewhere"));
    for (const char *command : {"info unknown", "withdraw unknown", "support unknown"}) {
        clear_output(ch);
        do_decree(ch, const_cast<char *>(command));
        assert(strstr(ch->desc->outbuf, "No such decree"));
    }
    decree->btype = 999;
    clear_output(ch);
    do_decree(ch, (char *)"list");
    assert(strstr(ch->desc->outbuf, "Unknown in Somewhere"));
    DecreeVect = old_decrees;

    const auto old_factions = FacVect;
    OPERATION_TYPE *old_operation = activeoperation;
    FACTION_TYPE *faction = new_faction();
    faction->vnum = 999998;
    faction->stasis = faction->antagonist = faction->outcast = 0;
    faction->attributes[FACTION_SCOUTS] = 1;
    assign_text(faction->name, "Audit faction");
    FacVect = {faction};
    activeoperation = op;
    op->faction = faction->vnum;
    op->goal = GOAL_PSYCHIC;
    op->speed = 5;
    op_report(const_cast<char *>(large.c_str()), nullptr);
    assert(strstr(faction->reportone_text, "Somewhere"));
    assert(strstr(faction->reportone_text, large.c_str()));
    op_report((char *)"last report line", nullptr);
    assert(strstr(faction->report_overflow[0][0], "last report line"));
    op->faction = 999999;
    op_report((char *)"missing faction", nullptr);
    activeoperation = old_operation;
    FacVect = old_factions;
    puts("PASS: stale territory/faction lookups, decree display and long operation report rollover.");
}
