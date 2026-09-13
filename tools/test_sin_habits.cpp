// Full-engine checks; test_sin_habits.py boots a disposable copy of the world.
#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>
#include <string>
#include <vector>

extern "C" {
extern char str_boot_time[];
void do_habit(CHAR_DATA *, char *);
void tier_prompt(CHAR_DATA *);
void mobile_update(CHAR_DATA *);
CHAR_DATA *get_npc_target(CHAR_DATA *);
void npc_combat_attack(CHAR_DATA *);
}

static void assign(char *&field, const char *value) { free_string(field); field = str_dup(value); }
static void clear_output(CHAR_DATA *ch) { ch->desc->outtop = 0; ch->desc->outbuf[0] = '\0'; }
static void habit(CHAR_DATA *ch, const char *choice) {
  char input[100]; snprintf(input, sizeof(input), "sin %s", choice); do_habit(ch, input);
}
static CHAR_DATA *player(const char *name) {
  CHAR_DATA *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->race = RACE_VETWEREWOLF; ch->position = POS_STANDING;
  ch->id = get_pc_id(); ch->logon = current_time; ch->played = 100 * 3600;
  ch->pcdata->account = new_account(); assign(ch->pcdata->account->name, name);
  assign(ch->pcdata->account_name, name); ch->pcdata->account->maxhours = 100;
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->desc->account = ch->pcdata->account; ch->desc->connected = CON_PLAYING;
  descriptor_list.push_back(ch->desc); char_list.push_front(ch);
  char_to_room(ch, get_room_index(16068));
  ch->disciplines[DIS_TOUGHNESS] = 40; ch->hit = max_hp(ch);
  assert(get_tier(ch) == 3);
  return ch;
}
static CHAR_DATA *vigilante() {
  for (CHAR_DATA *ch : char_list) if (sin_vigilante(ch) && ch->ttl > 0) return ch;
  return NULL;
}
static std::vector<CHAR_DATA *> guards() {
  std::vector<CHAR_DATA *> result;
  for (CHAR_DATA *ch : char_list) if (sin_cortex_guard(ch) && ch->ttl > 0) result.push_back(ch);
  return result;
}
static void ensure_public_fixture(ROOM_INDEX_DATA *room) {
  room->light = 100;
  REMOVE_BIT(room->room_flags, ROOM_UNLIT);
  for (int hour = 0; !public_room(room) && hour < 48; ++hour) current_time += 3600;
  assert(public_room(room));
}
static void interval(CHAR_DATA *ch, int minimum, int maximum) {
  assert(ch->pcdata->next_sin_event >= current_time + minimum * 86400);
  assert(ch->pcdata->next_sin_event <= current_time + maximum * 86400);
}

int main() {
  setvbuf(stdout, NULL, _IONBF, 0);
  current_time = time(NULL); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  CHAR_DATA *ch = player("Sinregression");
  CHAR_DATA *bystander = player("Sinbystander");
  ROOM_INDEX_DATA *room = ch->in_room;
  room->sector_type = SECT_STREET;
  REMOVE_BIT(room->room_flags, ROOM_INDOORS | ROOM_PRIVATE | ROOM_SAFE | ROOM_NO_MOB);
  SET_BIT(room->room_flags, ROOM_PUBLIC);
  assert(!institute_room(room) && !battleground(room));
  assert(sin_habit(ch) == SIN_MURDERER);
  sin_update(ch); assert(ch->pcdata->next_sin_event == 0);
  habit(ch, "invalid"); assert(sin_habit(ch) == SIN_MURDERER);
  habit(ch, "ScAmMeR"); assert(sin_habit(ch) == SIN_SCAMMER); interval(ch, 14, 18);
  const int initial_deadline = ch->pcdata->next_sin_event;
  habit(ch, "murderer"); habit(ch, "scammer");
  assert(ch->pcdata->next_sin_event == initial_deadline);
  clear_output(ch); do_habit(ch, (char *)""); assert(strstr(ch->desc->outbuf, "Sin: Scammer"));
  clear_output(ch); tier_prompt(ch);
  assert(strstr(ch->desc->outbuf, "RP Prompt:") && !strstr(ch->desc->outbuf, "sacrificed"));
  puts("PASS: habit command, default compatibility, tier prompt selection, grace period and unchanged cooldown on habit switches.");

  OBJ_DATA *phone = create_object(get_obj_index(OBJ_VNUM_PHONE), 0);
  phone->item_type = ITEM_PHONE; phone->value[0] = 991101;
  assign(phone->name, "phone"); assign(phone->material, "");
  REMOVE_BIT(phone->extra_flags, ITEM_OFF); obj_to_char(phone, ch); equip_char(ch, phone, WEAR_HOLD);
  assert(get_phone(ch) == phone && cell_signal(ch));
  current_time = initial_deadline - 1; sin_update(ch); assert(!phone->material[0]);
  ++current_time;
  SET_BIT(phone->extra_flags, ITEM_OFF); sin_update(ch); assert(!phone->material[0]);
  REMOVE_BIT(phone->extra_flags, ITEM_OFF);
  assign(phone->material, std::string(16000, 'x').c_str()); sin_update(ch);
  assert(strlen(phone->material) == 16000 && ch->pcdata->next_sin_event == initial_deadline);
  assign(phone->material, "");
  SET_FLAG(ch->affected_by, AFF_SILENCED); sin_update(ch); assert(!phone->material[0]);
  REMOVE_FLAG(ch->affected_by, AFF_SILENCED);
  SET_FLAG(ch->comm, COMM_AFK); sin_update(ch); assert(!phone->material[0]);
  REMOVE_FLAG(ch->comm, COMM_AFK);
  DESCRIPTOR_DATA *desc = ch->desc; ch->desc = NULL;
  sin_update(ch); assert(!phone->material[0]); ch->desc = desc;
  ch->pcdata->sleeping = 30; sin_update(ch); assert(!phone->material[0]); ch->pcdata->sleeping = 0;
  SET_FLAG(ch->act, PLR_SHROUD); sin_update(ch); assert(!phone->material[0]); REMOVE_FLAG(ch->act, PLR_SHROUD);
  set_combat_state(ch, TRUE); sin_update(ch); assert(!phone->material[0]); set_combat_state(ch, FALSE);
  ch->race = RACE_HUMAN; sin_update(ch); assert(!phone->material[0]); ch->race = RACE_VETWEREWOLF;
  SET_BIT(phone->extra_flags, ITEM_SILENT); clear_output(ch); clear_output(bystander);
  sin_update(ch); interval(ch, 14, 18);
  assert(strstr(phone->material, "Unknown number: "));
  assert(strstr(ch->desc->outbuf, "vibrates") && !strstr(bystander->desc->outbuf, "beeps"));
  std::string message = phone->material;
  const int story = ch->pcdata->last_sin_story;
  for (int i = 0; i < 500; ++i) sin_update(ch);
  assert(message == phone->material);
  DESCRIPTOR_DATA loaded = {};
  assert(load_char_obj(&loaded, ch->name));
  assert(sin_habit(loaded.character) == SIN_SCAMMER);
  assert(loaded.character->pcdata->next_sin_event == ch->pcdata->next_sin_event);
  assert(loaded.character->pcdata->last_sin_story == story);
  assert(get_phone(loaded.character) && message == get_phone(loaded.character)->material);
  current_time += 365 * 86400; assign(phone->material, ""); sin_update(ch);
  assert(strstr(phone->material, "Unknown number: ") && !strchr(phone->material, '\n'));
  assert(ch->pcdata->last_sin_story != story); interval(ch, 14, 18);
  puts("PASS: two-week delivery, phone availability, inbox limits, silent notification, saved inbox/cooldown, no spam or backlog and no immediate story repeat.");

  CHAR_DATA *fresh = player("Sincorrupt");
  habit(fresh, "corrupt"); interval(fresh, 28, 42);
  habit(ch, "corrupt");
  clear_output(ch); tier_prompt(ch);
  assert(strstr(ch->desc->outbuf, "RP Prompt:") && !strstr(ch->desc->outbuf, "sacrificed"));
  current_time = ch->pcdata->next_sin_event;
  ensure_public_fixture(room);
  ch->hit = max_hp(ch); ch->wounds = 1;
  sin_update(ch); assert(!vigilante()); ch->wounds = 0;
  --ch->hit; sin_update(ch); assert(!vigilante()); ch->hit = max_hp(ch);
  SET_BIT(room->room_flags, ROOM_PRIVATE); sin_update(ch); assert(!vigilante());
  REMOVE_BIT(room->room_flags, ROOM_PRIVATE);
  // A public building and an unmarked street cannot host either side.
  room->sector_type = SECT_SHOP; sin_update(ch); assert(!vigilante() && guards().empty());
  room->sector_type = SECT_STREET;
  const int area_vnum = room->area->vnum;
  room->area->vnum = 9999; REMOVE_BIT(room->room_flags, ROOM_PUBLIC);
  assert(!public_room(room)); sin_update(ch); assert(!vigilante() && guards().empty());
  room->area->vnum = area_vnum; SET_BIT(room->room_flags, ROOM_PUBLIC);
  ch->pcdata->travel_to = 1; sin_update(ch); assert(!vigilante()); ch->pcdata->travel_to = 0;
  clear_output(ch); sin_update(ch); interval(ch, 28, 42);
  CHAR_DATA *mob = vigilante(); assert(mob && in_fight(mob) && in_fight(ch));
  assert(strstr(mob->short_descr, "virtuous vigilante") && strstr(mob->description, "innocent"));
  assert(strstr(ch->desc->outbuf, "Cortex enforcers move to protect you"));
  auto assistance = guards(); assert(assistance.size() == 2);
  for (CHAR_DATA *guard : assistance) {
    assert(in_fight(guard) && cortex_enforcer(guard));
    assert(get_npc_target(guard) == mob && !str_cmp(guard->protecting, ch->name));
    assert(!sin_cortex_guard_target(guard, ch) && !sin_cortex_guard_target(guard, bystander));
    const int hp = ch->hit, bystander_hp = bystander->hit;
    damage(ch, guard, 100000); damage(bystander, guard, 100000);
    assert(ch->hit == hp && bystander->hit == bystander_hp);
  }
  sin_update(ch); assert(guards().size() == 2);
  SET_BIT(room->room_flags, ROOM_PRIVATE);
  assert(!get_npc_target(mob));
  for (CHAR_DATA *guard : assistance) assert(!get_npc_target(guard));
  REMOVE_BIT(room->room_flags, ROOM_PRIVATE);
  assert(max_hp(mob) == 25 && mob->disciplines[DIS_STRIKING] == 5);
  assert(mob->disciplines[DIS_TOUGHNESS] == 5 && get_npc_target(mob) == ch);
  assert(!public_target_excluded(ch, mob) && !public_target_excluded(mob, ch));
  assert(public_target_excluded(bystander, mob));
  assert(!sin_vigilante_target(mob, bystander));
  cortex_public_response(ch, mob);
  for (CHAR_DATA *other : char_list)
    assert(!cortex_public_enforcer(other) || str_cmp(other->aggression, ch->name));
  assert(!is_safe(ch, mob));
  // Remove assistance to exercise the unlikely losing path through real combat.
  for (CHAR_DATA *guard : assistance) { guard->ttl = 0; sin_cortex_guard_update(guard); }
  const int attacks = mob->fight_attacks;
  mob->attack_timer = 0; npc_combat_attack(mob);
  assert(mob->fight_attacks > attacks);
  int untouched = bystander->hit; damage(bystander, mob, 100000); assert(bystander->hit == untouched);
  sin_update(ch); assert(vigilante() == mob);
  const int x = ch->x, y = ch->y, possessions = ch->carry_number;
  const long money = ch->money;
  damage(ch, mob, 100000);
  assert(ch->in_room == room && ch->x == x && ch->y == y);
  assert(ch->hit == 0 && ch->pcdata->sleeping == 240 && ch->wounds == 0);
  assert(!IS_FLAG(ch->act, PLR_DEAD) && ch->carry_number == possessions && ch->money == money);
  assert(!in_fight(ch) && !in_fight(mob) && mob->ttl == 0 && !get_npc_target(mob));
  damage(ch, mob, 100000); assert(ch->wounds == 0 && ch->pcdata->sleeping == 240);
  assert(load_char_obj(&loaded, ch->name));
  assert(sin_habit(loaded.character) == SIN_CORRUPT && loaded.character->pcdata->sleeping == 240);
  assert(loaded.character->pcdata->next_sin_event == ch->pcdata->next_sin_event);
  puts("PASS: rare weak vigilante, safe encounter deferral, public-room retaliation, target-only damage and persistent knockout at the original location without wounds or losses.");

  end_fight(room); ch->pcdata->sleeping = 0; ch->hit = max_hp(ch);
  current_time = ch->pcdata->next_sin_event; ensure_public_fixture(room); sin_update(ch);
  mob = vigilante(); assert(mob && guards().size() == 2);
  assistance = guards();
  for (int turn = 0; mob->ttl > 0 && turn < 50; ++turn) {
    for (CHAR_DATA *guard : assistance) { guard->attack_timer = 0; npc_combat_attack(guard); }
  }
  assert(mob->ttl == 0 && !in_fight(mob));
  for (CHAR_DATA *guard : assistance) {
    sin_cortex_guard_update(guard); assert(guard->ttl == 0 && !in_fight(guard));
  }
  assert(ch->wounds == 0 && ch->pcdata->sleeping == 0);
  puts("PASS: explicitly virtuous vigilantes appear only on public streets; two Cortex enforcers protect the player, attack only that vigilante, and withdraw after defeating it.");

  end_fight(room); ch->hit = max_hp(ch);
  current_time = ch->pcdata->next_sin_event; ensure_public_fixture(room); sin_update(ch);
  mob = vigilante(); assert(mob);
  damage(mob, ch, 100000); assert(mob->ttl == 0 && !in_fight(mob));
  assert(!get_npc_target(mob));
  for (CHAR_DATA *guard : guards()) sin_cortex_guard_update(guard);
  end_fight(room); ch->hit = max_hp(ch);
  current_time = ch->pcdata->next_sin_event; ensure_public_fixture(room); sin_update(ch); mob = vigilante(); assert(mob);
  char_from_room(ch); char_to_room(ch, get_room_index(taxi_table[0].vnum));
  sin_vigilante_update(mob); assert(mob->ttl == 0 && !get_npc_target(mob));
  for (CHAR_DATA *guard : guards()) { sin_cortex_guard_update(guard); assert(guard->ttl == 0); }
  mobile_update(mob);
  puts("PASS: victory retires the vigilante; escaping ends pursuit and mobile update removes the encounter.");
}
