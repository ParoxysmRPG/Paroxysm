// Boots only in the disposable world prepared by run_school_integration.py.
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <set>
#include <string>
#include "merc.h"
#include "recycle.h"

extern "C" {
extern char str_boot_time[];
void boot_db();
}

static void command(CHAR_DATA *ch, void (*fn)(CHAR_DATA *, char *), const char *arg) {
  char text[MSL]; strcpy(text, arg); fn(ch, text);
}

static void walk(CHAR_DATA *ch, int direction, int destination) {
  ROOM_INDEX_DATA *from = ch->in_room;
  EXIT_DATA *e = from->exit[direction];
  assert(e && e->u1.to_room && e->u1.to_room->vnum == destination);
  assert(e->wall == WALL_NONE && !e->climb && !e->jump && !e->fall);
  EXIT_DATA *back = e->u1.to_room->exit[rev_dir[direction]];
  assert(back && back->u1.to_room == from && back->wall == WALL_NONE);
  if (IS_SET(e->exit_info, EX_CLOSED)) command(ch, do_open, dir_name[direction][0]);
  move_char(ch, direction, FALSE, FALSE);
  if (ch->in_room->vnum != destination)
    fprintf(stderr, "Movement failed: %d %s -> %d\n%s\n", from->vnum,
            dir_name[direction][0], destination, ch->desc->outbuf);
  assert(ch->in_room->vnum == destination);
}

static unsigned stock_count(CHAR_DATA *keeper) {
  unsigned n = 0;
  for (OBJ_DATA *o = keeper->carrying; o; o = o->next_content) ++n;
  return n;
}

int main() {
  current_time = time(NULL); strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  CHAR_DATA *ch = new_char();
  if (!ch->pcdata) ch->pcdata = new_pcdata();
  ch->name = str_dup("UniformAudit");
  ch->level = 1; ch->trust = 0; ch->position = POS_STANDING; ch->hit = 1000;
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->money = 100000; ch->pcdata->total_credit = 0;
  INSTITUTE_TYPE *enrollment = new_institute();
  enrollment->name = str_dup(ch->name); enrollment->college_prestige = 1;
  InVect.push_back(enrollment);
  char_to_room(ch, get_room_index(3970));

  // Public entrance, then directly UP from reception as advertised.
  walk(ch, DIR_WEST, 16119); walk(ch, DIR_WEST, 16132);
  assert(strstr(ch->in_room->description, "Uniform Shop"));
  walk(ch, DIR_UP, 18074);
  ROOM_INDEX_DATA *shop = ch->in_room;
  assert(shop->sector_type == SECT_SHOP && shop->description_decorated);
  assert(get_extra_descr("counter", shop->places));
  assert(get_extra_descr("fitting bench", shop->places));
  CHAR_DATA *keeper = find_keeper(ch);
  assert(keeper && keeper->pIndexData->vnum == 45018);
  assert(keeper->pIndexData->pShop->open_hour == 0 && keeper->pIndexData->pShop->close_hour == 23);
  assert(stock_count(keeper) == 20);
  std::set<int> inventory;
  for (OBJ_DATA *o = keeper->carrying; o; o = o->next_content) {
    inventory.insert(o->pIndexData->vnum);
    assert(o->item_type == ITEM_CLOTHING && IS_SET(o->wear_flags, ITEM_WEAR_BODY));
    assert(IS_SET(o->extra_flags, ITEM_INVENTORY) && o->cost > 0);
    assert(o->value[0] && o->pIndexData->extra_descr);
    assert(strlen(o->pIndexData->extra_descr->description) > 100);
    assert(strchr(o->short_descr, '`') && strstr(o->short_descr, "`x"));
    char plain[MSL]; remove_color(plain, o->short_descr);
    assert(!strchr(plain, '`') && strlen(plain) > 10);
  }
  for (int n = 45020; n < 45040; ++n) assert(inventory.count(n));
  command(ch, do_list, "");
  assert(strstr(ch->desc->outbuf, "Syntax: Buy"));
  for (const char *color : {"royal blue", "emerald green", "plum purple", "burgundy red"})
    assert(strstr(ch->desc->outbuf, color));
  // Numbered listings retain their order and stock after each purchase.
  for (int n = 1; n <= 20; ++n) {
    char number[8]; snprintf(number, sizeof(number), "%d", n);
    int balance = ch->money;
    command(ch, do_buy, number);
    OBJ_DATA *bought = ch->carrying;
    assert(bought && bought->pIndexData->vnum == 45019 + n);
    assert(ch->money < balance && stock_count(keeper) == 20);
    assert(!IS_SET(bought->extra_flags, ITEM_INVENTORY));
    if (n == 1) {
      command(ch, do_wear, "blazer");
      assert(bought->wear_loc != WEAR_NONE);
    } else {
      wear_obj(ch, bought, TRUE, TRUE);
      assert(bought->wear_loc != WEAR_NONE);
    }
    // Do not stack twenty separate uniform pieces onto the test character.
    extract_obj(bought);
  }
  command(ch, do_buy, "1");
  assert(ch->carrying && ch->carrying->pIndexData->vnum == 45020);
  reset_room(shop, false);
  assert(stock_count(find_keeper(ch)) == 20);
  unsigned keepers = 0;
  for (CHAR_DATA *mob : *shop->people)
    if (IS_NPC(mob) && mob->pIndexData->vnum == 45018) ++keepers;
  assert(keepers == 1);
  puts("PASS: reception stairs, shopkeeper, 20 colorful listings, every purchase and wearable item, repeat purchase and reset");

  // The repaired cafeteria doorway and both formerly sealed bookstore rooms.
  walk(ch, DIR_SOUTH, 18083); walk(ch, DIR_WEST, 18085);
  walk(ch, DIR_WEST, 18089); walk(ch, DIR_NORTH, 9262);
  walk(ch, DIR_EAST, 18072); walk(ch, DIR_EAST, 18074);
  walk(ch, DIR_DOWN, 16132); walk(ch, DIR_WEST, 16126);
  const int westward[] = {1643, 9900, 9901, 9902, 9904, 1732, 16295,
                         16294, 1641, 9800, 1734, 15641, 16156};
  for (int n : westward) walk(ch, DIR_WEST, n);
  walk(ch, DIR_UP, 3347);
  // Verify the advertised courtyard-to-arts path independently of teleporting.
  walk(ch, DIR_DOWN, 16156);
  for (int i = 11; i >= 5; --i) walk(ch, DIR_EAST, westward[i]);
  for (int n : {1588, 9582, 9584, 9439, 9607}) walk(ch, DIR_SOUTH, n);
  walk(ch, DIR_EAST, 1430);
  for (int n : {9031, 16166, 18074, 18083, 18087, 18085, 18089, 9262}) {
    ROOM_INDEX_DATA *r = get_room_index(n);
    assert(!IS_SET(r->room_flags, ROOM_BEDROOM) && !IS_SET(r->room_flags, ROOM_DARK));
  }
  for (int n : {16155, 15624, 9912}) assert(get_room_index(n)->sector_type == SECT_PARK);
  puts("PASS: cafeteria and bookstore access, reception-to-dorm route, courtyard-to-arts route, public room flags and lawns");
}
