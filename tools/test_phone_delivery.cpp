// Full-engine integration tests, run in a disposable world by test_phone_delivery.py.
#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>

extern "C" {
extern char str_boot_time[];
void do_text(CHAR_DATA *, char *);
void do_teletext(CHAR_DATA *, char *);
OBJ_DATA *find_phone(CHAR_DATA *, int);
}

static void assign(char *&field, const char *value) { free_string(field); field = str_dup(value); }
static CHAR_DATA *player(const char *name, int number) {
  auto *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->race = RACE_HUMAN; ch->position = POS_STANDING; ch->hit = 100;
  ch->id = get_pc_id(); ch->logon = current_time; ch->played = 100 * 3600;
  auto *account = new_account(); assign(account->name, name);
  account->maxhours = 100; ch->pcdata->account = account;
  assign(ch->pcdata->account_name, name);
  ch->desc = new_descriptor(); ch->desc->character = ch; ch->desc->account = account;
  ch->desc->connected = CON_PLAYING; descriptor_list.push_back(ch->desc);
  char_to_room(ch, get_room_index(16068)); char_list.push_front(ch);
  auto *phone = create_object(get_obj_index(OBJ_VNUM_PHONE), 0);
  phone->item_type = ITEM_PHONE; phone->value[0] = number;
  REMOVE_BIT(phone->extra_flags, ITEM_OFF); assign(phone->name, "phone"); assign(phone->material, "");
  obj_to_char(phone, ch); equip_char(ch, phone, WEAR_HOLD);
  assert(get_phone(ch) == phone && cell_signal(ch));
  return ch;
}
static void command(CHAR_DATA *ch, DO_FUN *handler, const char *value) {
  char input[MAX_INPUT_LENGTH]; snprintf(input, sizeof(input), "%s", value); handler(ch, input);
}
static bool has(CHAR_DATA *ch, const char *text) { return strstr(get_phone(ch)->material, text); }
static void clear(CHAR_DATA *ch) { assign(get_phone(ch)->material, ""); }

static void assert_history_saved(const char *message) {
  save_texthistories();
  std::ifstream saved(TEXTHISTORY_FILE);
  std::string contents(std::istreambuf_iterator<char>(saved), {});
  assert(contents.find(message) != std::string::npos);
}

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  bool found_help = false;
  for (HELP_DATA *help = help_first; help; help = help->next)
    if (!str_cmp(help->keyword, "compromised")) {
      found_help = strstr(help->text, "30,000") && strstr(help->text, "48 hours");
    }
  assert(found_help);
  auto *sender = player("PhoneSender", 990001);
  auto *target = player("PhoneTarget", 990002);
  auto *third = player("PhoneThird", 990003);
  auto *fourth = player("PhoneFourth", 990004);
  auto *event = new_event(); event->valid = true; event->type = EVENT_COMPROMISED;
  assign(event->target, sender->name); event->active_time = current_time - 1;
  event->deactive_time = current_time + 3600; EventVect.push_back(event);

  save_texthistories();
  command(sender, do_text, "990002 direct-message");
  assert_history_saved("direct-message");
  assert(has(target, "direct-message"));
  assert(has(third, "copied text") != has(fourth, "copied text"));
  assert(!has(sender, "copied text") && !has(target, "copied text"));
  clear(third); clear(fourth);
  command(sender, do_text, "990002"); // Empty text must not trigger a copy.
  assert(!has(third, "copied text") && !has(fourth, "copied text"));
  assign(get_phone(target)->material, std::string(16000, 'x').c_str());
  command(sender, do_text, "990002 full-inbox");
  assert(!has(third, "copied text") && !has(fourth, "copied text"));
  clear(target);

  auto *group = new_grouptext(); group->valid = true; assign(group->tname, "phone-audit");
  group->pnumber[0] = 990001; group->pnumber[1] = 990002; group->pnumber[2] = 990003;
  GTextVect.push_back(group);
  mark_grouptexts_dirty(); save_grouptexts();
  command(sender, do_text, "phone-audit group-message");
  save_grouptexts();
  {
    std::ifstream saved(GROUPTEXT_FILE);
    std::string contents(std::istreambuf_iterator<char>(saved), {});
    assert(contents.find("group-message") != std::string::npos);
  }
  assert(has(target, "group-message") && has(third, "group-message"));
  assert(!has(target, "copied text") && !has(third, "copied text"));
  assert(has(fourth, "copied text") && has(fourth, "group-message"));
  assert(strstr(group->history, "group-message"));
  command(fourth, do_text, "history phone-audit");
  assert(strstr(fourth->desc->outbuf, "You are not a member"));

  clear(third); clear(fourth);
  event->deactive_time = current_time;
  command(sender, do_text, "990002 expired-scheme");
  assert_history_saved("expired-scheme");
  assert(has(target, "expired-scheme"));
  assert(!has(third, "copied text") && !has(fourth, "copied text"));
  event->deactive_time = current_time + 3600;
  sender->skills[SKILL_ELECTROPATHIC] = 2;
  command(sender, do_teletext, "990002 anonymous-message");
  assert(has(target, "anonymous-message"));
  assert(has(third, "copied text") != has(fourth, "copied text"));
  clear(third); clear(fourth);
  auto *from_profile = new_profile(); assign(from_profile->name, sender->name);
  assign(from_profile->handle, "@phone-sender"); ProfileVect.push_back(from_profile);
  auto *to_profile = new_profile(); assign(to_profile->name, target->name);
  assign(to_profile->handle, "@phone-target"); ProfileVect.push_back(to_profile);
  assert(!dm_to_person(sender, target->name, (char *)"unmatched", FALSE));
  auto *match = new_match(); assign(match->nameone, sender->name); assign(match->nametwo, target->name);
  match->status_one = match->status_two = 1; MatchVect.push_back(match);
  command(sender, do_text, "@phone-target dm-message");
  assert_history_saved("dm-message");
  assert(has(target, "dm-message"));
  assert(has(third, "copied text") != has(fourth, "copied text"));
  clear(third); clear(fourth);
  auto *book = new PHONEBOOK_TYPE{}; book->number = 990002; book->owner = str_dup(target->name);
  PhoneVect.push_back(book);
  save_char_obj(target, FALSE, FALSE);
  descriptor_list.remove(target->desc); target->desc->character = nullptr; target->desc = nullptr;
  extract_char(target, TRUE);
  assert(!get_char_world_pc(book->owner));
  command(sender, do_text, "990002 offline-message");
  assert_history_saved("offline-message");
  assert(has(third, "copied text") != has(fourth, "copied text"));
  assert(dm_to_person(sender, book->owner, (char *)"phone", TRUE));
  DESCRIPTOR_DATA loaded = {};
  assert(load_char_obj(&loaded, book->owner));
  OBJ_DATA *stored = find_phone(loaded.character, 990002);
  assert(stored && strstr(stored->material, "offline-message") && strstr(stored->material, "A photo message"));
  free_char(loaded.character);
  puts("PASS: real direct/group/DM/teletext and offline delivery, single scheme copies, rejection paths and group-history access");
}
