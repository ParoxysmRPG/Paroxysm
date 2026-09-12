#include "merc.h"
#include "recycle.h"
#include <climits>

// Load sellers/prisoners by name so disconnecting does not lose a sale.
// Temporary players never enter the live character or room lists.
class SyndicatePlayer {
 public:
  CHAR_DATA *ch;
  bool offline;
  DESCRIPTOR_DATA descriptor{};

  explicit SyndicatePlayer(char *name) : ch(NULL), offline(false) {
    if (!name || !name[0]) return;
    ch = get_char_world_pc(name);
    if (ch) return;
    descriptor.descriptor = -1;
    if (!load_char_obj(&descriptor, name)) {
      if (descriptor.character) free_char(descriptor.character);
      return;
    }
    ch = descriptor.character;
    ch->desc = NULL;
    offline = true;
  }
  ~SyndicatePlayer() {
    if (offline) free_char(ch);
  }
};

bool syndicate_cell(ROOM_INDEX_DATA *room) {
  return room && (room->vnum == ROOM_PRISON_WEST || room->vnum == ROOM_PRISON_EAST);
}

static void clear_syndicate_captivity(CHAR_DATA *ch) {
  ch->pcdata->patrol_status = 0;
  ch->pcdata->patrol_timer = 0;
  ch->pcdata->patrol_room = NULL;
  ch->pcdata->patrol_target = NULL;
  ch->pcdata->syndicate_release_at = 0;
  free_string(ch->pcdata->syndicate_seller);
  ch->pcdata->syndicate_seller = str_dup("");
}

void syndicate_captivity_update(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !ch->in_room
      || ch->pcdata->patrol_status != PATROL_KIDNAPPED) return;
  if (!syndicate_cell(ch->in_room)) {
    clear_syndicate_captivity(ch);
    save_char_obj(ch, FALSE, FALSE);
    return;
  }
  // Migrate prisoners saved before detention had a real-time deadline.
  if (!ch->pcdata->syndicate_release_at) {
    ch->pcdata->syndicate_release_at = current_time + 24 * 60 * 60;
    REMOVE_FLAG(ch->act, PLR_BOUND);
    REMOVE_FLAG(ch->act, PLR_BOUNDFEET);
    save_char_obj(ch, FALSE, FALSE);
  }
  ch->pcdata->patrol_room = ch->in_room;
  if (current_time < ch->pcdata->syndicate_release_at) {
    ch->pcdata->patrol_timer = (ch->pcdata->syndicate_release_at - current_time + 59) / 60;
    return;
  }
  ROOM_INDEX_DATA *release = random_inner_forest();
  if (!release) return;
  char_from_room(ch);
  char_to_room(ch, release);
  ch->walking = 0;
  REMOVE_FLAG(ch->act, PLR_BOUND);
  REMOVE_FLAG(ch->act, PLR_BOUNDFEET);
  clear_syndicate_captivity(ch);
  send_to_char("After 24 hours, the syndicate releases you in the forest.\n\r", ch);
  save_char_obj(ch, FALSE, FALSE);
}

_DOFUN(do_commit) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !ch->in_room) return;
  char destination[MIL], target[MIL];
  argument = one_argument_nouncap(argument, destination);
  argument = one_argument_nouncap(argument, target);
  if (str_cmp(destination, "syndicate") || !target[0]) {
    send_to_char("Syntax: commit syndicate <target>\n\r", ch);
    return;
  }
  CHAR_DATA *victim = get_char_room(ch, NULL, target);
  if (!victim || IS_NPC(victim) || !victim->pcdata || victim == ch) {
    send_to_char("Choose another character here to hand over.\n\r", ch);
    return;
  }
  if (!IS_FLAG(victim->act, PLR_BOUND)) {
    send_to_char("They must be bound before you can hand them over to the syndicate.\n\r", ch);
    return;
  }
  if (!free_to_act(ch) || in_fight(victim) || is_ghost(victim)
      || IS_FLAG(victim->act, PLR_DEAD) || IS_FLAG(ch->act, PLR_SHROUD)
      || IS_FLAG(ch->act, PLR_DEEPSHROUD) || IS_FLAG(victim->act, PLR_SHROUD)
      || IS_FLAG(victim->act, PLR_DEEPSHROUD)) {
    send_to_char("You cannot arrange a handover right now.\n\r", ch);
    return;
  }
  if (!start_syndicate_auction(victim, ch)) {
    send_to_char("The syndicate cannot accept another prisoner right now.\n\r", ch);
    return;
  }
  send_to_char("You hand them over to the syndicate. When a buyer pays and collects them, half the sale price will be deposited into your bank account.\n\r", ch);
}

bool syndicate_join_auction(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !ch->in_room) return FALSE;
  if (!free_to_act(ch) || IS_FLAG(ch->act, PLR_SHROUD) || IS_FLAG(ch->act, PLR_DEEPSHROUD)) {
    send_to_char("You cannot bid right now.\n\r", ch);
    return FALSE;
  }
  if (ch->pcdata->patrol_status <= PATROL_PATROL) {
    for (CHAR_DATA *victim : char_list) {
      if (!victim || IS_NPC(victim) || !victim->pcdata || !syndicate_cell(victim->in_room)
          || victim->pcdata->patrol_status != PATROL_KIDNAPPED) continue;
      const int venue = victim->in_room->vnum == ROOM_PRISON_WEST ? ROOM_MEETING_WEST : ROOM_MEETING_EAST;
      const time_t remaining = victim->pcdata->syndicate_release_at - 24 * 60 * 60 + 15 * 60 - current_time;
      if (ch->in_room->vnum != venue || remaining <= 0
          || !str_cmp(ch->name, victim->pcdata->syndicate_seller)) continue;
      ch->pcdata->patrol_status = PATROL_BIDDING;
      ch->pcdata->patrol_timer = (remaining + 59) / 60;
      ch->pcdata->patrol_room = ch->in_room;
      ch->pcdata->patrol_target = victim;
      ch->pcdata->patrol_amount = 0;
      ch->pcdata->syndicate_release_at = victim->pcdata->syndicate_release_at;
      free_string(ch->pcdata->syndicate_prisoner);
      ch->pcdata->syndicate_prisoner = str_dup(victim->name);
      break;
    }
  }
  if (ch->pcdata->patrol_status != PATROL_BIDDING || ch->pcdata->patrol_timer <= 0
      || ch->in_room != ch->pcdata->patrol_room) {
    send_to_char("You must be at an active syndicate auction to bid.\n\r", ch);
    return FALSE;
  }
  SyndicatePlayer prisoner(ch->pcdata->syndicate_prisoner);
  if (!prisoner.ch || prisoner.ch->pcdata->patrol_status != PATROL_KIDNAPPED
      || !syndicate_cell(prisoner.ch->in_room)
      || prisoner.ch->pcdata->syndicate_release_at != ch->pcdata->syndicate_release_at
      || current_time >= ch->pcdata->syndicate_release_at
      || !str_cmp(ch->name, prisoner.ch->pcdata->syndicate_seller)) {
    send_to_char("You cannot bid on that prisoner.\n\r", ch);
    return FALSE;
  }
  return TRUE;
}

void syndicate_collect(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata) return;
  if (ch->pcdata->patrol_status != PATROL_COLLECTING || ch->pcdata->patrol_timer <= 0) {
    send_to_char("You haven't won any auctions recently.\n\r", ch);
    return;
  }
  if (!ch->in_room || !in_haven(ch->in_room)) {
    send_to_char("Return to Gravesend to collect the prisoner.\n\r", ch);
    return;
  }
  SyndicatePlayer prisoner(ch->pcdata->syndicate_prisoner);
  CHAR_DATA *victim = prisoner.ch;
  if (!victim || victim == ch || !victim->pcdata || !syndicate_cell(victim->in_room)
      || victim->in_room != ch->pcdata->patrol_room
      || victim->pcdata->patrol_status != PATROL_KIDNAPPED
      || victim->pcdata->syndicate_release_at != ch->pcdata->syndicate_release_at
      || current_time >= victim->pcdata->syndicate_release_at) {
    send_to_char("That prisoner is no longer available for delivery.\n\r", ch);
    return;
  }
  const long price = (long)ch->pcdata->patrol_amount * 100;
  if (price <= 0 || ch->pcdata->total_money < price) {
    send_to_char("You do not have enough money in your bank account to pay your bid.\n\r", ch);
    return;
  }
  SyndicatePlayer seller(victim->pcdata->syndicate_seller);
  const long commission = price / 2;
  if (victim->pcdata->syndicate_seller[0]
      && (!seller.ch || seller.ch == ch || seller.ch == victim
          || seller.ch->pcdata->total_money > LONG_MAX - commission)) {
    send_to_char("The syndicate cannot settle this sale right now.\n\r", ch);
    return;
  }
  ch->pcdata->total_money -= price;
  if (seller.ch) {
    seller.ch->pcdata->total_money += commission;
    char receipt[MSL];
    snprintf(receipt, sizeof(receipt), "The syndicate deposits $%ld.%02ld into your bank account: your 50%% share of the auction sale.", commission / 100, commission % 100);
    if (seller.offline) {
      std::string messages = std::string(seller.ch->pcdata->messages) + "\n\r" + receipt;
      free_string(seller.ch->pcdata->messages);
      seller.ch->pcdata->messages = str_dup(messages.c_str());
    } else printf_to_char(seller.ch, "%s\n\r", receipt);
    save_char_obj(seller.ch, FALSE, FALSE);
  }
  if (prisoner.offline) victim->in_room = ch->in_room;
  else {
    char_from_room(victim);
    char_to_room(victim, ch->in_room);
  }
  victim->walking = 0;
  SET_FLAG(victim->act, PLR_BOUND);
  clear_syndicate_captivity(victim);
  act("Some men deliver $N to you.", ch, NULL, victim, TO_CHAR);
  act("Some men deliver $N to $n.", ch, NULL, victim, TO_NOTVICT);
  act("Some men deliver you to $n.", ch, NULL, victim, TO_VICT);
  clear_syndicate_captivity(ch);
  ch->pcdata->patrol_amount = 0;
  free_string(ch->pcdata->syndicate_prisoner);
  ch->pcdata->syndicate_prisoner = str_dup("");
  save_char_obj(victim, FALSE, FALSE);
  save_char_obj(ch, FALSE, FALSE);
}
