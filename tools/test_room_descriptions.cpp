// Integration test linked against the actual engine, including its area loader,
// allocator, colour parser, place matcher, and procedural room functions.
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <set>
#include <string>
#include "merc.h"
#include "recycle.h"
#include "olc.h"

extern "C" {
extern ROOM_INDEX_DATA *room_index_hash[MAX_KEY_HASH];
extern char str_boot_time[];
void boot_db();
void room_to_default(ROOM_INDEX_DATA *room);
void load_rooms(FILE *fp);
void do_decorate(CHAR_DATA *ch, char *argument);
void do_join(CHAR_DATA *ch, char *argument);
void string_add(CHAR_DATA *ch, char *argument);
void walktosubway(CHAR_DATA *ch);
void subwaytowalk(CHAR_DATA *ch);
}

static void command(CHAR_DATA *ch, void (*fn)(CHAR_DATA *, char *), const char *argument) {
  char text[MSL];
  strcpy(text, argument);
  fn(ch, text);
}

static void check_room(ROOM_INDEX_DATA *room) {
  assert(room != NULL);
  assert(!unfinished_room_description(room->description));
  assert(strlen(room->description) > 40);
  const char *last = strrchr(room->description, '`');
  assert(last && last[1] == 'x');
  for (EXTRA_DESCR_DATA *p = room->places; p; p = p->next) {
    assert(*p->keyword && *p->description);
    assert(is_name(p->keyword, p->keyword));
    assert(get_extra_descr(p->keyword, room->places) != NULL);
    last = strrchr(p->description, '`');
    assert(last && last[1] == 'x');
  }
  char plain[MSL];
  remove_color(plain, room->description);
  assert(strchr(plain, '`') == NULL && strlen(plain) > 40);
}

int main() {
  current_time = time(NULL);
  strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  unsigned rooms = 0, places = 0, stock = 0;
  for (int i = 0; i < MAX_KEY_HASH; ++i) {
    for (ROOM_INDEX_DATA *r = room_index_hash[i]; r; r = r->next) {
      check_room(r);
      ++rooms;
      if (room_uses_stock_description(r)) ++stock;
      for (EXTRA_DESCR_DATA *p = r->places; p; p = p->next) ++places;
    }
  }
  assert(rooms > 90000 && places > 1500 && stock > 80000);
  // Individual interiors survive loading and ordinary procedural resets.
  const int interiors[] = {6184, 6185, 41168, 390139, 38025};
  for (int vnum : interiors) {
    ROOM_INDEX_DATA *interior = get_room_index(vnum);
    assert(interior && interior->description_decorated);
    std::string saved = interior->description;
    room_to_default(interior);
    ensure_room_description(interior);
    assert(saved == interior->description);
  }
  assert(strcmp(get_room_index(6184)->description, get_room_index(6185)->description));
  assert(get_extra_descr("bed", get_room_index(41168)->places));
  assert(get_extra_descr("stone", get_room_index(41168)->places) == NULL);
  const int shower_rooms[] = {39030, 39031, 39032, 2467, 3015, 10842, 10863};
  for (int vnum : shower_rooms) {
    ROOM_INDEX_DATA *bathroom = get_room_index(vnum);
    assert(IS_SET(bathroom->room_flags, ROOM_BATHROOM));
    assert(get_extra_descr("shower", bathroom->places));
    assert(get_extra_descr("sofa", bathroom->places) == NULL);
  }
  // Saved taxis retain distinct prose when the loader applies defaults.
  std::set<std::string> loaded_cabs;
  for (int vnum = 19000; vnum <= 19099; ++vnum) {
    ROOM_INDEX_DATA *cab = get_room_index(vnum);
    if (str_cmp(cab->name, "Taxi")) continue;
    assert(room_uses_stock_description(cab));
    assert(loaded_cabs.insert(cab->description).second);
  }
  assert(loaded_cabs.size() == 90);
  ROOM_INDEX_DATA *saved_cab = get_room_index(19099);
  free_string(saved_cab->name);
  saved_cab->name = str_dup("A sidewalk");
  saved_cab->sector_type = SECT_SIDEWALK;
  ensure_room_description(saved_cab);
  assert(saved_cab->places == NULL);
  assert(!strcmp(saved_cab->description, default_room_description(saved_cab)));
  // The real taxi setup uses this helper before setting ROOM_INDOORS. Legacy
  // shells may have a non-car sector; each still needs the right seats and text.
  ROOM_INDEX_DATA *cab = new_room_index();
  std::set<std::string> generated_cabs;
  for (int vnum = 19000; vnum <= 19099; ++vnum) {
    cab->vnum = vnum;
    cab->sector_type = SECT_FOREST;
    cab->room_flags = 0;
    free_string(cab->name);
    cab->name = str_dup("The back of a Taxi");
    set_generated_room_description(cab, default_room_description(cab));
    check_room(cab);
    assert(room_uses_stock_description(cab));
    assert(generated_cabs.insert(cab->description).second);
    assert(get_extra_descr("seats", cab->places));
    free_string(cab->name);
    cab->name = str_dup("A sidewalk");
    cab->sector_type = SECT_SIDEWALK;
    ensure_room_description(cab);
    assert(cab->places == NULL);
    assert(!strcmp(cab->description, default_room_description(cab)));
  }
  free_string(cab->name);
  cab->name = str_dup("A Taxidermist's Shop");
  cab->sector_type = SECT_SHOP;
  ensure_room_description(cab);
  assert(get_extra_descr("counter", cab->places));
  assert(get_extra_descr("seats", cab->places) == NULL);
  // Empty floor is not a separate social destination. Removing the last
  // catalogue place must not undo decoration ownership or recreate filler.
  const int empty_rooms[] = {45000, 1133};
  for (int vnum : empty_rooms) {
    ROOM_INDEX_DATA *empty = get_room_index(vnum);
    assert(empty && empty->description_decorated && empty->places == NULL);
    ensure_room_description(empty);
    assert(empty->places == NULL);
  }
  ROOM_INDEX_DATA *r = new_room_index();
  for (int sector = 0; sector < SECT_MAX; ++sector) {
    // A saved-and-loaded stock description must remain regenerable, even
    // after its sector changes. Each test starts with a fresh place list.
    while (r->places) {
      EXTRA_DESCR_DATA *p = r->places;
      r->places = p->next;
      free_extra_descr(p);
    }
    r->sector_type = sector;
    ensure_room_description(r);
    check_room(r);
    assert(room_uses_stock_description(r));
    assert(!strcmp(r->description, default_room_description(r)));
    const char *before = r->description;
    EXTRA_DESCR_DATA *before_places = r->places;
    ensure_room_description(r);
    assert(before == r->description && before_places == r->places);
  }
  free_string(r->description);
  r->description = str_dup(" \n\r\t");
  ensure_room_description(r);
  check_room(r);
  free_string(r->description);
  r->description = str_dup("An authored room has its own carefully finished surroundings.`x\n\r");
  const char *authored = r->description;
  ensure_room_description(r);
  assert(authored == r->description);
  r->sector_type = SECT_FOREST;
  room_to_default(r);
  ensure_room_description(r);
  check_room(r);
  assert(room_uses_stock_description(r));
  for (const char *code = "wgcybrx"; *code; ++code) {
    char ansi[64] = {0};
    assert(color(*code, NULL, ansi) > 0);
    assert(strchr(ansi, '\033') != NULL);
  }
  // Use the real Decorate command and string editor, including the case where
  // a player deliberately chooses text identical to an automatic default.
  r->area = get_room_index(10128)->area;
  r->vnum = 987654320;
  r->sector_type = SECT_CAFE;
  ensure_room_description(r);
  CHAR_DATA *ch = new_char();
  if (ch->pcdata == NULL) ch->pcdata = new_pcdata();
  ch->trust = MAX_LEVEL;
  ch->level = MAX_LEVEL;
  ch->in_room = r;
  ch->desc = new_descriptor();
  ch->desc->character = ch;
  ch->name = str_dup("RoomAudit");
  // Exercise useful furnishings through the real keyword matcher and join.
  struct Furnishing { int vnum; const char *keyword; const char *place; };
  const Furnishing furnishings[] = {
    {38025, "bed", "bed"}, {33006, "sofa", "sofa"},
    {10128, "booths", "booths"}, {390139, "front", "front desk"},
    {390139, "rear", "rear desks"}
  };
  for (const Furnishing &fixture : furnishings) {
    ch->in_room = get_room_index(fixture.vnum);
    assert(ch->in_room && get_extra_descr(fixture.keyword, ch->in_room->places));
    command(ch, do_join, fixture.keyword);
    assert(!str_cmp(ch->pcdata->place, fixture.place));
  }
  ch->in_room = r;
  command(ch, do_decorate, "description");
  assert(r->description_decorated && ch->desc->pString == &r->description);
  command(ch, string_add, ".c");
  command(ch, string_add, "A warm brick alcove surrounds a small table and two chairs.`x");
  command(ch, string_add, "@");
  authored = r->description;
  ensure_room_description(r);
  room_to_default(r);
  set_generated_room_description(r, "An automatic replacement must not overwrite the player's room.`x\n\r");
  assert(r->description == authored && r->sector_type == SECT_CAFE);
  command(ch, do_decorate, "place alcove");
  assert(ch->desc->pString != NULL);
  command(ch, string_add, "Two chairs face a small table within the brick alcove.`x");
  command(ch, string_add, "@");
  command(ch, do_join, "alcove");
  assert(!str_cmp(ch->pcdata->place, "alcove"));
  command(ch, do_decorate, "placedelete alcove");
  command(ch, do_decorate, "placedelete tables");
  command(ch, do_decorate, "placedelete counter");
  ensure_room_description(r);
  assert(r->places == NULL);
  free_string(r->description);
  r->description = str_dup(default_room_description(r));
  ensure_room_description(r);
  assert(!room_uses_stock_description(r) && r->places == NULL);
  // The B marker survives the real area loader, even for stock-looking prose.
  FILE *saved = tmpfile();
  fprintf(saved, "#987654321\nA decorated cafe~\n%s~\n0 0 12\nB 1\nS\n#0\n", r->description);
  rewind(saved);
  load_rooms(saved);
  fclose(saved);
  ROOM_INDEX_DATA *loaded = get_room_index(987654321);
  assert(loaded->description_decorated && loaded->places == NULL);
  assert(!room_uses_stock_description(loaded));
  // Place lists are deep-copied and reset without following recycled links.
  ROOM_INDEX_DATA *copy = new_room_index();
  ROOM_INDEX_DATA *source = get_room_index(10128);
  assert(source->places != NULL);
  copy_room_places(copy, source);
  assert(copy->places != source->places);
  assert(!strcmp(copy->places->keyword, source->places->keyword));
  clear_room_places(copy);
  assert(copy->places == NULL && source->places != NULL);
  check_room(source);
  // Automatically supplied seats disappear when transit becomes sidewalk.
  r->description_decorated = FALSE;
  r->sector_type = SECT_CAR;
  ensure_room_description(r);
  assert(r->places != NULL);
  r->sector_type = SECT_SIDEWALK;
  ensure_room_description(r);
  assert(r->places == NULL);
  walktosubway(ch);
  assert(strstr(r->description, "subway carriage") && r->places != NULL);
  subwaytowalk(ch);
  assert(strstr(r->description, "sidewalk") && r->places == NULL);
  // Old automatic places can be upgraded or retired without touching custom
  // text. A Decorate ownership marker takes precedence even over stock text.
  r->sector_type = SECT_CLUB;
  ensure_room_description(r);
  assert(r->places && !strcmp(r->places->keyword, "sofa"));
  const char *old_keyword = "seating area";
  const char *old_description = "Seats stand back from the dance floor, leaving room for quiet company.`x\n\r";
  auto legacy_sofa = [&]() {
    free_string(r->places->keyword);
    free_string(r->places->description);
    r->places->keyword = str_dup(old_keyword);
    r->places->description = str_dup(old_description);
  };
  legacy_sofa();
  r->description_decorated = TRUE;
  ensure_room_description(r);
  assert(!strcmp(r->places->keyword, old_keyword));
  assert(!strcmp(r->places->description, old_description));
  r->description_decorated = FALSE;
  ensure_room_description(r);
  assert(!strcmp(r->places->keyword, "sofa"));
  assert(strcmp(r->places->description, old_description));
  legacy_sofa();
  r->sector_type = SECT_SIDEWALK;
  ensure_room_description(r);
  assert(r->places == NULL);
  r->sector_type = SECT_CLUB;
  ensure_room_description(r);
  free_string(r->places->description);
  r->places->description = str_dup("A hand-painted sofa is embroidered with silver moths.`x\n\r");
  const char *custom_place = r->places->description;
  r->sector_type = SECT_SIDEWALK;
  ensure_room_description(r);
  assert(r->places && r->places->description == custom_place);
  // Newbie school uses its existing resets and real shop, not scenery-only
  // stock. Exercise the tutorial's numbered purchase with an ordinary PC.
  ch->trust = 0;
  ch->level = 1;
  ch->in_room = NULL;
  char_to_room(ch, get_room_index(52));
  ch->money = 100000;
  ch->pcdata->total_credit = 0;
  CHAR_DATA *keeper = find_keeper(ch);
  assert(keeper && keeper->pIndexData->vnum == 2);
  unsigned stock_count = 0;
  for (OBJ_DATA *item = keeper->carrying; item; item = item->next_content) ++stock_count;
  assert(stock_count >= 20);
  command(ch, do_list, "");
  assert(strstr(ch->desc->outbuf, "Syntax: Buy"));
  command(ch, do_buy, "1");
  assert(ch->carrying != NULL && ch->carrying->carried_by == ch);
  assert(ch->carrying->pIndexData->vnum == 50); // buy 1 is the lesson's white shorts
  assert(ch->money < 100000);
  command(ch, do_join, "shower");
  assert(!str_cmp(ch->pcdata->place, "shower"));
  assert(IS_SET(ch->in_room->room_flags, ROOM_BATHROOM));
  assert(IS_SET(ch->in_room->room_flags, ROOM_STASH));
  printf("PASS: newbie school shopkeeper, %u stocked items, list, buy 1, shower join, bathroom and stash flags.\n", stock_count);
  printf("PASS: %u loaded rooms, %u places, %u stock rooms; all 33 sectors, whitespace recovery, idempotence, authored preservation, procedural reset.\n", rooms, places, stock);
  puts("PASS: engine colour codes, Decorate/editor/join, place deletion priority, decorated load round-trip, deep copy, reset, transit changes.");
  return 0;
}
