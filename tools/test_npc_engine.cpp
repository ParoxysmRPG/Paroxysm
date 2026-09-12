#include "merc.h"
#include "recycle.h"
#include "global.h"
#include "report_text.h"
#include <cassert>
#include <cstring>

extern "C" {
extern char *string_space, *top_string;
CHAR_DATA *get_bag_carrier();
}

static void assign_text(char *&field, const std::string &text) {
    free_string(field);
    field = str_dup(text.c_str());
}

int main() {
    // Real allocator and engine functions, without loading world files.
    char pool[] = "shared room name";
    string_space = pool;
    top_string = pool + sizeof(pool);
    char *text = str_dup("");
    std::string expected;
    int reallocations = 0;
    for (int i = 0; i < 1000; ++i) {
        char *previous = text;
        append_report_text(text, "report line", true);
        expected += "\nreport line";
        assert(expected == text);
        if (text != previous) ++reallocations;
    }
    assert(reallocations < 15);
    append_report_text(text, text + 10, true);
    expected += "\n" + expected.substr(10);
    assert(expected == text);
    free_string(text);
    text = str_dup(pool);
    assert(text == pool);
    append_report_text(text, " appended");
    assert(!strcmp(pool, "shared room name"));
    assert(!strcmp(text, "shared room name appended") && text != pool);
    free_string(text);
    text = str_dup("abc");
    char *same = text;
    append_report_text(text, text, true);
    assert(text == same && !strcmp(text, "abc\nabc"));
    free_string(text);
    // Repeatedly cross allocator buckets and then recycle each allocation.
    for (int length : {1, 15, 16, 31, 48, 112, 240, 1008, 2032, 4080,
                       8176, 16368, 32688, 65520}) {
        text = str_dup(std::string(length, 'a').c_str());
        append_report_text(text, "12345678901234567");
        assert(strlen(text) == static_cast<size_t>(length + 17));
        free_string(text);
    }
    printf("PASS: real report allocator: 1000 appends, %d allocations; shared strings, aliases and bucket boundaries.\n", reallocations);

    current_time = time(nullptr);
    FACTION_TYPE *fac = new_faction();
    fac->vnum = 100;
    fac->stasis = fac->antagonist = fac->outcast = 0;
    fac->attributes[FACTION_SCOUTS] = 1;
    assign_text(fac->name, "Audit faction");
    FacVect = {fac};
    invalidate_faction_index();
    activeoperation = new_operation();
    activeoperation->faction = fac->vnum;
    activeoperation->territoryvnum = 999999;
    activeoperation->goal = GOAL_PSYCHIC;
    activeoperation->competition = COMPETE_OPEN;
    activeoperation->speed = 5;
    char **titles[] = {&fac->reportone_title, &fac->reporttwo_title, &fac->reportthree_title};
    char **texts[] = {&fac->reportone_text, &fac->reporttwo_text, &fac->reportthree_text};
    int *times[] = {&fac->reportone_time, &fac->reporttwo_time, &fac->reportthree_time};
    for (int slot = 0; slot < 3; ++slot) {
        for (auto title : titles) assign_text(*title, "");
        assign_text(*titles[slot], "Audit faction's operation in Somewhere");
        *times[slot] = current_time;
        assign_text(*texts[slot], std::string(25000, 'a'));
        op_report((char *)"boundary", nullptr);
        assert(std::string(*texts[slot]) == std::string(25000, 'a') + "\nboundary");
        op_report((char *)"overflow", nullptr);
        assert(!strcmp(fac->report_overflow[slot][0], "\noverflow"));
        const std::string marker = "\n\n`WSee society report battle " + std::to_string(slot + 1) + " 2 to continue.`x\n\r";
        assert(std::string(*texts[slot]) == std::string(25000, 'a') + "\nboundary" + marker);
        assign_text(fac->report_overflow[slot][0], std::string(24999, 'b'));
        op_report((char *)"x", nullptr);
        assert(std::string(fac->report_overflow[slot][0]) == std::string(24999, 'b') + "\nx\n\n`WSee society report battle " + std::to_string(slot+1) + " 3 to continue.`x\n\r");
        op_report((char *)"next page", nullptr);
        assert(!strcmp(fac->report_overflow[slot][1], "\nnext page"));
    }
    puts("PASS: real operation reports preserve all three slots, exact rollover boundaries and continuation markers.");

    CHAR_DATA older = {}, newer = {};
    SET_FLAG(older.act, ACT_IS_NPC); SET_FLAG(newer.act, ACT_IS_NPC);
    older.bagcarrier = newer.bagcarrier = 1;
    register_live_character(&older); register_live_character(&newer);
    set_combat_state(&older, true); set_combat_state(&newer, true);
    assert(get_bag_carrier() == &newer);
    unregister_live_character(&newer);
    assert(get_bag_carrier() == &older);
    set_combat_state(&older, false);
    assert(get_bag_carrier() == nullptr);
    unregister_live_character(&older);
    puts("PASS: real carrier lookup preserves combat-index ordering, removal and deactivation.");
}
