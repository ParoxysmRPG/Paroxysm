// Boots only in the disposable world prepared by run_school_integration.py.
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <initializer_list>
#include <set>
#include <string>
#include "merc.h"
#include "recycle.h"

extern "C" {
extern char str_boot_time[];
void boot_db();
void do_zip(CHAR_DATA *ch, char *argument);
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

static void readable_uniform_text(const char *text) {
  assert(text && strstr(text, "`w") && strstr(text, "`x"));
  assert(!strstr(text, "`d") && !strstr(text, "`D"));
  char plain[MSL]; remove_color(plain, text);
  assert(!strchr(plain, '`') && strlen(plain) > 10);
}

struct UniformSpec {
  const char *keyword;
  std::set<int> covers;
  std::set<int> opens;
};

static UniformSpec uniform_spec(int vnum) {
  const std::set<int> jacket = {COVERS_UPPER_CHEST, COVERS_BREASTS,
      COVERS_LOWER_CHEST, COVERS_UPPER_BACK, COVERS_LOWER_BACK,
      COVERS_UPPER_ARMS, COVERS_LOWER_ARMS};
  const std::set<int> front = {COVERS_UPPER_CHEST, COVERS_BREASTS, COVERS_LOWER_CHEST};
  const std::set<int> trousers = {COVERS_ARSE, COVERS_GROIN, COVERS_THIGHS, COVERS_LOWER_LEGS};
  if (vnum >= 45020 && vnum <= 45035) {
    switch ((vnum - 45020) % 4) {
      case 0: return {"blazer", jacket, front};
      case 1: return {"trousers", trousers, {COVERS_GROIN}};
      case 2: return {"skirt", {COVERS_ARSE, COVERS_GROIN, COVERS_THIGHS}, {}};
      case 3: return {"tie", {COVERS_NECK}, {}};
    }
  }
  switch (vnum) {
    case 45036: {
      std::set<int> shirt = jacket, buttons = front;
      shirt.insert(COVERS_NECK); buttons.insert(COVERS_NECK);
      return {"shirt", shirt, buttons};
    }
    case 45037: return {"sweater", jacket, {}};
    case 45038: return {"socks", {COVERS_LOWER_LEGS, COVERS_FEET}, {}};
    case 45039: return {"loafers", {COVERS_FEET}, {}};
    case 45040: return {"helmet", {COVERS_HAIR, COVERS_FOREHEAD}, {}};
    case 45041: return {"respirator", {COVERS_EYES, COVERS_LOWER_FACE}, {}};
    case 45042: {
      std::set<int> coat = jacket, buttons = front;
      coat.insert({COVERS_NECK, COVERS_ARSE, COVERS_GROIN, COVERS_THIGHS});
      buttons.insert({COVERS_NECK, COVERS_GROIN});
      return {"coat", coat, buttons};
    }
    case 45043: return {"armor", {COVERS_UPPER_CHEST, COVERS_BREASTS,
        COVERS_LOWER_CHEST, COVERS_UPPER_BACK, COVERS_LOWER_BACK, COVERS_UPPER_ARMS}, {}};
    case 45044: return {"trousers", trousers, {COVERS_GROIN}};
    case 45045: return {"gauntlets", {COVERS_HANDS, COVERS_LOWER_ARMS}, {}};
    case 45046: return {"boots", {COVERS_FEET, COVERS_LOWER_LEGS}, {}};
    case 45047: return {"belt", {COVERS_LOWER_CHEST, COVERS_LOWER_BACK}, {}};
  }
  assert(false && "Missing uniform coverage specification");
  return {};
}

static void check_coverage(CHAR_DATA *ch, OBJ_DATA *obj, const std::set<int> &expected) {
  // Check every region, including the regions this garment must leave bare.
  for (int i = 0; i < MAX_COVERS; ++i) {
    const int region = cover_table[i];
    const bool covered = expected.count(region) != 0;
    if (does_cover(obj, region) != covered || is_covered(ch, region) != covered)
      fprintf(stderr, "Coverage mismatch: item %d, region %d, expected %d\n",
              obj->pIndexData->vnum, region, covered);
    assert(does_cover(obj, region) == covered);
    assert(is_covered(ch, region) == covered);
  }
}

static void audit_worn_uniform(CHAR_DATA *ch, OBJ_DATA *obj) {
  assert(obj->wear_loc != WEAR_NONE);
  for (OBJ_DATA *other = ch->carrying; other; other = other->next_content)
    assert(other == obj || other->wear_loc == WEAR_NONE);
  const UniformSpec spec = uniform_spec(obj->pIndexData->vnum);
  check_coverage(ch, obj, spec.covers);

  // LOOK <ordinary item name> must show the authored paragraph, not just its price.
  const char *detail = get_extra_descr("all", obj->pIndexData->extra_descr);
  assert(detail && strlen(detail) > 100 && strchr(detail, '`') && strstr(detail, "`x"));
  char plain[MSL]; remove_color(plain, detail);
  ch->desc->outtop = 0; ch->desc->outbuf[0] = '\0';
  command(ch, do_look, spec.keyword);
  if (!strstr(ch->desc->outbuf, plain))
    fprintf(stderr, "LOOK %s missed item %d detail:\n%s\n", spec.keyword,
            obj->pIndexData->vnum, ch->desc->outbuf);
  assert(strstr(ch->desc->outbuf, plain));

  const int original = obj->value[0];
  std::set<int> open = spec.covers;
  for (int region : spec.opens) {
    assert(open.erase(region) == 1);
  }
  command(ch, do_zip, spec.keyword);
  check_coverage(ch, obj, open);
  if (spec.opens.empty()) {
    assert(obj->value[1] == 0 && obj->value[0] == original);
  } else {
    assert(obj->value[0] != original);
    command(ch, do_zip, spec.keyword);
    assert(obj->value[0] == original);
    check_coverage(ch, obj, spec.covers);
  }
}

static OBJ_DATA *buy_number(CHAR_DATA *ch, int number, int vnum) {
  char arg[8]; snprintf(arg, sizeof(arg), "%d", number);
  command(ch, do_buy, arg);
  assert(ch->carrying && ch->carrying->pIndexData->vnum == vnum);
  return ch->carrying;
}

static void check_academy_outfits(CHAR_DATA *ch) {
  assert(!ch->carrying);
  for (int base : {45020, 45024, 45028, 45032}) {
    for (int bottom : {base + 1, base + 2}) {
      for (bool reversed : {false, true}) {
        const int vnums[] = {45038, 45039, 45036, bottom, base + 3, 45037, base};
        OBJ_DATA *outfit[7];
        for (int n = 0; n < 7; ++n)
          outfit[n] = buy_number(ch, vnums[n] - 45019, vnums[n]);
        for (int n = 0; n < 7; ++n) {
          const int index = reversed ? 6 - n : n;
          command(ch, do_wear, uniform_spec(vnums[index]).keyword);
        }
        std::set<int> slots;
        for (OBJ_DATA *obj : outfit) {
          assert(obj->wear_loc != WEAR_NONE && slots.insert(obj->wear_loc).second);
        }
        // The V-neck and open collar leave the tie visible in either wear order.
        assert(can_see_wear(ch, outfit[4]->wear_loc));
        assert(can_see_wear(ch, outfit[6]->wear_loc));
        for (int region : {COVERS_NECK, COVERS_UPPER_CHEST, COVERS_BREASTS,
             COVERS_LOWER_CHEST, COVERS_UPPER_BACK, COVERS_LOWER_BACK,
             COVERS_UPPER_ARMS, COVERS_LOWER_ARMS, COVERS_ARSE, COVERS_GROIN,
             COVERS_THIGHS, COVERS_LOWER_LEGS, COVERS_FEET})
          assert(is_covered(ch, region));
        for (int region : {COVERS_EYES, COVERS_HAIR, COVERS_FOREHEAD,
             COVERS_LOWER_FACE, COVERS_HANDS})
          assert(!is_covered(ch, region));
        while (ch->carrying) extract_obj(ch->carrying);
      }
    }
  }
}

int main() {
  current_time = time(NULL); strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  CHAR_DATA *ch = new_char();
  if (!ch->pcdata) ch->pcdata = new_pcdata();
  ch->name = str_dup("UniformAudit");
  ch->level = 1; ch->trust = 0; ch->position = POS_STANDING; ch->hit = 1000;
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->money = 1000000; ch->pcdata->total_credit = 0; ch->lines = 0;
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
    audit_worn_uniform(ch, bought);
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

  extract_obj(ch->carrying);
  check_academy_outfits(ch);
  puts("PASS: academy coverage, ordinary LOOK descriptions, fastening round trips, all colors and both full outfit variants in either wear order");

  // One ordinary flight UP reaches the Cortex seller on the named landing.
  walk(ch, DIR_UP, 9475);
  ROOM_INDEX_DATA *cortex_shop = ch->in_room;
  assert(!strcmp(cortex_shop->name, "the second floor landing"));
  assert(cortex_shop->sector_type == SECT_SHOP && cortex_shop->description_decorated);
  assert(get_extra_descr("counter", cortex_shop->places));
  assert(get_extra_descr("fitting mirror", cortex_shop->places));
  CHAR_DATA *cortex_keeper = find_keeper(ch);
  assert(cortex_keeper && cortex_keeper->pIndexData->vnum == 45019);
  assert(cortex_keeper->pIndexData->pShop->open_hour == 0);
  assert(cortex_keeper->pIndexData->pShop->close_hour == 23);
  readable_uniform_text(cortex_keeper->short_descr);
  readable_uniform_text(cortex_keeper->long_descr);
  readable_uniform_text(cortex_keeper->description);
  for (const char *accent : {"`R", "`g", "`y"})
    assert(strstr(cortex_keeper->description, accent));
  assert(stock_count(cortex_keeper) == 8);
  inventory.clear();
  std::string cortex_colors;
  ch->desc->outtop = 0; ch->desc->outbuf[0] = '\0';
  assert(!IS_FLAG(ch->act, PLR_COLOR));
  command(ch, do_list, "");
  assert(strstr(ch->desc->outbuf, "Syntax: Buy"));
  for (OBJ_DATA *o = cortex_keeper->carrying; o; o = o->next_content) {
    inventory.insert(o->pIndexData->vnum);
    assert(o->item_type == ITEM_CLOTHING && IS_SET(o->wear_flags, ITEM_WEAR_BODY));
    assert(IS_SET(o->extra_flags, ITEM_INVENTORY) && o->cost > 0 && o->value[0]);
    assert(o->pIndexData->extra_descr);
    readable_uniform_text(o->short_descr);
    readable_uniform_text(o->description);
    readable_uniform_text(o->pIndexData->extra_descr->description);
    assert(strlen(o->pIndexData->extra_descr->description) > 100);
    // This ordinary PC has color disabled, so compare its rendered listing.
    char plain_listing[MSL]; remove_color(plain_listing, o->description);
    assert(strstr(ch->desc->outbuf, plain_listing));
    cortex_colors += o->short_descr;
  }
  for (int n = 45040; n <= 45047; ++n) assert(inventory.count(n));
  for (const char *accent : {"`R", "`g", "`y"})
    assert(cortex_colors.find(accent) != std::string::npos);
  // Audit each numbered purchase alone, then wear the full outfit together.
  const char *pieces[] = {"helmet", "respirator", "coat", "armor",
                          "trousers", "gauntlets", "boots", "belt"};
  OBJ_DATA *outfit[8];
  ch->money = 1000000;
  for (int n = 1; n <= 8; ++n) {
    char number[8]; snprintf(number, sizeof(number), "%d", n);
    int balance = ch->money;
    command(ch, do_buy, number);
    OBJ_DATA *bought = ch->carrying;
    assert(bought && bought->pIndexData->vnum == 45039 + n);
    assert(strstr(bought->name, pieces[n - 1]));
    assert(ch->money < balance && stock_count(cortex_keeper) == 8);
    assert(!IS_SET(bought->extra_flags, ITEM_INVENTORY));
    outfit[n - 1] = bought;
    command(ch, do_wear, pieces[n - 1]);
    assert(bought->wear_loc != WEAR_NONE);
    audit_worn_uniform(ch, bought);
    unequip_char_silent(ch, bought);
  }
  for (int n = 0; n < 8; ++n) command(ch, do_wear, pieces[n]);
  std::set<int> outfit_slots;
  for (OBJ_DATA *o : outfit) {
    assert(o->wear_loc != WEAR_NONE);
    assert(outfit_slots.insert(o->wear_loc).second);
  }
  command(ch, do_buy, "1");
  assert(ch->carrying && ch->carrying->pIndexData->vnum == 45040);
  assert(ch->carrying != outfit[0] && ch->carrying->wear_loc == WEAR_NONE);
  reset_room(cortex_shop, false);
  assert(find_keeper(ch) == cortex_keeper && stock_count(cortex_keeper) == 8);
  keepers = 0;
  for (CHAR_DATA *mob : *cortex_shop->people)
    if (IS_NPC(mob) && mob->pIndexData->vnum == 45019) ++keepers;
  assert(keepers == 1);
  extract_obj(ch->carrying); // The repeat helmet is not part of this outfit.
  for (OBJ_DATA *o : outfit) unequip_char_silent(ch, o);
  // Wearing the belt first must not let the later cuirass hide its pouches.
  for (int n : {7, 3, 2, 4, 0, 1, 5, 6}) command(ch, do_wear, pieces[n]);
  for (OBJ_DATA *o : outfit) assert(o->wear_loc != WEAR_NONE);
  assert(can_see_wear(ch, outfit[7]->wear_loc));
  for (int i = 0; i < MAX_COVERS; ++i) assert(is_covered(ch, cover_table[i]));
  while (ch->carrying) extract_obj(ch->carrying);
  walk(ch, DIR_DOWN, 18074);
  puts("PASS: Cortex landing stairs, readable seller and stock colors, eight numbered purchases, full wearable outfit, repeat purchase and reset");
  puts("PASS: Cortex coverage, ordinary LOOK descriptions, fastening round trips, and visible belt when worn before armor");

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
