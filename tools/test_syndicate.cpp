#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>
#include <string>

extern "C" {
extern char str_boot_time[];
void do_patrol(CHAR_DATA *, char *);
void do_shroud(CHAR_DATA *, char *);
void clear_pointers(CHAR_DATA *);
}

static void assign(char *&field, const char *value) {
  free_string(field); field = str_dup(value);
}
static CHAR_DATA *player(const char *name, int room = 16068) {
  auto *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->race = RACE_HUMAN; ch->position = POS_STANDING;
  ch->hit = 100; ch->id = get_pc_id(); ch->played = 100 * 3600;
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->desc->connected = CON_PLAYING; descriptor_list.push_back(ch->desc);
  char_list.push_front(ch); char_to_room(ch, get_room_index(room));
  return ch;
}
static void command(CHAR_DATA *ch, DO_FUN *fun, const char *text) {
  char input[MSL]; snprintf(input, sizeof(input), "%s", text); fun(ch, input);
}
static void move(CHAR_DATA *ch, ROOM_INDEX_DATA *room) {
  char_from_room(ch); char_to_room(ch, room);
}
static void logout(CHAR_DATA *ch) {
  save_char_obj(ch, FALSE, FALSE);
  clear_pointers(ch);
  char_from_room(ch); char_list.remove(ch);
  auto *d = ch->desc; descriptor_list.remove(d); ch->desc = nullptr;
  d->character = nullptr; free_descriptor(d); free_char(ch);
}
static CHAR_DATA *login(const char *name) {
  auto *d = new_descriptor();
  assert(load_char_obj(d, const_cast<char *>(name)));
  auto *ch = d->character;
  char_list.push_front(ch); char_to_room(ch, ch->in_room);
  d->connected = CON_PLAYING; descriptor_list.push_back(d);
  return ch;
}
static FACTION_TYPE *society(int id, int scouts) {
  auto *fac = new_faction(); fac->vnum = id; fac->type = FACTION_SOCIETY;
  fac->attributes[FACTION_SCOUTS] = scouts;
  FacVect.push_back(fac); invalidate_faction_index();
  return fac;
}
static int reports(FACTION_TYPE *fac) {
  int result = 0;
  for (char *message : fac->messages)
    if (strstr(message, "syndicate is auctioning")) ++result;
  return result;
}

static void random_prey() {
  auto *prey = player("Syndprey");
  prey->in_room->sector_type = SECT_STREET;
  prey->pcdata->tier_raised = 2 - get_tier(prey);
  prey->in_room->z = 0;
  assert(get_tier(prey) == 2 && valid_syndicate_prey(prey));
  for (int *membership : {&prey->fcore, &prey->fsociety, &prey->legacy_society,
                          &prey->faction, &prey->factiontwo, &prey->factiontrue}) {
    *membership = 123;
    assert(!valid_syndicate_prey(prey));
    *membership = 0;
    assert(valid_syndicate_prey(prey));
  }
  assert(!valid_syndicate_prey(nullptr));
  logout(prey);
  puts("PASS: random abductions exclude every faction and society membership slot.");
}

static void auctions() {
  auto *without_scouts = society(990101, 0);
  auto *with_scouts = society(990102, 1);
  without_scouts->closed = 1; // An offline/closed society still receives a report.
  auto *seller = player("Syndseller"), *victim = player("Syndvictim");
  auto *bidder = player("Syndbuyer"), *helper = player("Syndhelper");
  bidder->pcdata->total_money = 50000;
  bidder->pcdata->patrol_habits[PATROL_DIPLOMATICHABIT] = 1;
  victim->fsociety = with_scouts->vnum; // Protection applies only to random capture.
  command(seller, do_commit, "syndicate Syndseller");
  command(seller, do_commit, "syndicate Syndvictim");
  assert(!syndicate_cell(victim->in_room));
  SET_FLAG(victim->act, PLR_BOUND); SET_FLAG(victim->act, PLR_BOUNDFEET);
  command(seller, do_commit, "syndicate Syndvictim");
  assert(syndicate_cell(victim->in_room));
  assert(!IS_FLAG(victim->act, PLR_BOUND) && !IS_FLAG(victim->act, PLR_BOUNDFEET));
  assert(victim->pcdata->patrol_timer == 1440);
  assert(victim->pcdata->syndicate_release_at == current_time + 86400);
  assert(!strcmp(victim->pcdata->syndicate_seller, seller->name));
  assert(reports(with_scouts) == 1 && reports(without_scouts) == 1);
  assert(bidder->pcdata->patrol_status == PATROL_BIDDING);

  for (int vnum : {ROOM_PRISON_WEST, ROOM_PRISON_EAST}) {
    auto *cell = get_room_index(vnum);
    assert(IS_SET(cell->room_flags, ROOM_LANDLINE) && IS_SET(cell->room_flags, ROOM_NOSHROUD));
    assert(strstr(cell->description, "fixed telephone"));
  }
  auto *phone = create_object(get_obj_index(OBJ_VNUM_PHONE), 0);
  phone->item_type = ITEM_PHONE; phone->value[0] = 990777;
  REMOVE_BIT(phone->extra_flags, ITEM_OFF);
  obj_to_char(phone, helper); equip_char(helper, phone, WEAR_HOLD);
  assert(!get_phone(victim));
  command(victim, do_call, "990777");
  assert(victim->pcdata->connected_to == helper && helper->pcdata->connected_to == victim);
  command(victim, do_hangup, "");
  command(victim, do_shroud, "");
  assert(!IS_FLAG(victim->act, PLR_SHROUD));
  assert(strstr(victim->desc->outbuf, "wards"));
  auto *cell = victim->in_room;
  move(helper, cell);
  command(helper, do_shroud, "pull Syndvictim");
  assert(!IS_FLAG(victim->act, PLR_SHROUD) && !IS_FLAG(helper->act, PLR_SHROUD));
  move(helper, get_room_index(16068));

  command(bidder, do_patrol, "bid 100");
  assert(bidder->pcdata->patrol_amount == 0); // Must attend.
  move(bidder, bidder->pcdata->patrol_room);
  move(seller, bidder->in_room);
  command(seller, do_patrol, "bid 101");
  assert(seller->pcdata->patrol_status == 0); // Cannot buy your own consignment.
  command(bidder, do_patrol, "bid 100");
  command(bidder, do_patrol, "bid 301"); // Replaces the previous bid.
  assert(bidder->pcdata->patrol_amount == 301);
  bidder->pcdata->patrol_timer = 1; patrol_update(bidder);
  assert(bidder->pcdata->patrol_status == PATROL_COLLECTING);
  assert(victim->pcdata->patrol_timer == 1440); // Winning does not shorten detention.
  move(bidder, get_room_index(16068));
  bidder->pcdata->total_money = 100;
  command(bidder, do_patrol, "collect");
  assert(victim->in_room == cell && seller->pcdata->total_money == 0);
  bidder->pcdata->total_money = 50000;
  move(helper, cell); // Visitors must never be delivered as a bonus prisoner.
  logout(seller); logout(victim); logout(bidder);
  bidder = login("Syndbuyer");
  assert(bidder->pcdata->patrol_room == cell);
  command(bidder, do_patrol, "collect");
  assert(bidder->pcdata->total_money == 19900 && bidder->pcdata->patrol_status == 0);
  assert(helper->in_room == cell);
  seller = login("Syndseller"); victim = login("Syndvictim");
  assert(seller->pcdata->total_money == 15050);
  assert(strstr(seller->pcdata->messages, "$150.50"));
  assert(victim->in_room == bidder->in_room && victim->pcdata->patrol_status == 0);
  assert(IS_FLAG(victim->act, PLR_BOUND));
  command(bidder, do_patrol, "collect");
  assert(seller->pcdata->total_money == 15050 && bidder->pcdata->total_money == 19900);
  move(helper, get_room_index(16068));
  puts("PASS: bound-only consignments, reports without scouts, fixed phone, nightmare wards, paid collection and exact 50% offline commission.");
  puts("PASS: insufficient funds, seller bidding, reconnects, duplicate collection and unrelated cell visitors.");

  auto *unsold = player("Syndunsold");
  assert(start_syndicate_auction(unsold));
  auto deadline = unsold->pcdata->syndicate_release_at;
  // A society member arriving from a report can join without a diplomatic habit.
  move(helper, get_room_index(unsold->in_room->vnum == ROOM_PRISON_WEST ? ROOM_MEETING_WEST : ROOM_MEETING_EAST));
  helper->pcdata->total_money = 10000;
  command(helper, do_patrol, "bid 5");
  assert(helper->pcdata->patrol_status == PATROL_BIDDING && helper->pcdata->patrol_amount == 5);
  current_time = deadline - 1; unsold->pcdata->patrol_timer = 0;
  patrol_update(unsold);
  assert(syndicate_cell(unsold->in_room) && unsold->pcdata->patrol_timer == 1);
  logout(unsold);
  current_time = deadline;
  unsold = login("Syndunsold");
  logon_char(unsold);
  assert(!syndicate_cell(unsold->in_room) && unsold->pcdata->patrol_status == 0);
  assert(!IS_FLAG(unsold->act, PLR_BOUND));
  puts("PASS: arrivals can bid; the 24-hour deadline survives logout and releases on login.");
}

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  random_prey(); auctions();
}
