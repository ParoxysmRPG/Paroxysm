#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>

extern "C" {
extern char str_boot_time[];
void do_cauterize(CHAR_DATA *, char *);
void do_look(CHAR_DATA *, char *);
CHAR_DATA *get_npc_target(CHAR_DATA *);
}

int main() {
  setvbuf(stdout, NULL, _IONBF, 0);
  current_time = time(NULL);
  strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  CHAR_DATA *ch = new_char();
  ch->pcdata = new_pcdata();
  free_string(ch->name); ch->name = str_dup("Moonregression");
  ch->level = 2; ch->race = RACE_HUMAN; ch->position = POS_STANDING;
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->desc->connected = CON_PLAYING;
  char_list.push_front(ch);
  char_to_room(ch, get_room_index(16068));
  CHAR_DATA *mob = create_mobile(get_mob_index(40));
  SET_FLAG(mob->act, ACT_FULL_MOON_PACK);
  mob->ttl = -1;
  char_to_room(mob, ch->in_room);
  assert(!forest_monster(mob));
  assert(full_moon_pack_target(mob, ch));
  assert(get_npc_target(mob) == ch);
  ch->race = RACE_NEWWEREWOLF;
  assert(is_werewolf(ch));
  assert(!full_moon_pack_target(mob, ch));
  assert(get_npc_target(mob) == NULL);
  ch->hit = 100;
  damage(ch, mob, 1000);
  assert(ch->hit == 100 && ch->wounds == 0);
  puts("PASS: packs target human PCs and cannot target or damage PC werewolves.");

  ch->race = RACE_HUMAN;
  damage(ch, mob, 1000);
  assert(ch->wounds == 3 && ch->hit == 0 && ch->death_timer == 720);
  assert(IS_FLAG(ch->act, PLR_WOLFBIT));
  assert(!full_moon_pack_target(mob, ch));
  damage(ch, mob, 1000);
  assert(ch->wounds == 3);
  puts("PASS: a pack defeat critically wounds and infects without follow-up killing.");

  const int spent = ch->spentkarma;
  const int reserves = base_lifeforce(ch);
  const int stored_lf = ch->lifeforce;
  const int used_lf = ch->lf_used, taken_lf = ch->lf_taken, sused_lf = ch->lf_sused;
  // Deliberately no account: treatment has no account/karma dependency.
  do_cauterize(ch, ch->name);
  assert(!IS_FLAG(ch->act, PLR_WOLFBIT));
  assert(ch->spentkarma == spent);
  assert(base_lifeforce(ch) == reserves);
  assert(ch->lifeforce == stored_lf && ch->lf_used == used_lf
         && ch->lf_taken == taken_lf && ch->lf_sused == sused_lf);
  const long until = current_time + 14L * 86400;
  assert(ch->pcdata->cauterize_until == until);
  assert(get_lifeforce(ch, TRUE, NULL) == 10);
  assert(get_display_lifeforce(ch) == 10);
  const int coma = ch->pcdata->coma, sleeping = ch->pcdata->sleeping;
  const int death_timer = ch->death_timer;
  for (int check = 0; check < 100; ++check) {
    assert(get_lifeforce(ch, TRUE, NULL) == 10);
    assert(get_lifeforce(ch, FALSE, NULL) == 10);
  }
  assert(base_lifeforce(ch) == reserves);
  assert(ch->pcdata->coma == coma && ch->pcdata->sleeping == sleeping);
  assert(ch->death_timer == death_timer && !IS_FLAG(ch->act, PLR_DEAD));
  ++current_time;
  do_cauterize(ch, ch->name);
  assert(ch->pcdata->cauterize_until == until);
  save_char_obj(ch, FALSE, FALSE);
  DESCRIPTOR_DATA *loaded = new_descriptor();
  assert(load_char_obj(loaded, ch->name));
  assert(loaded->character->pcdata->cauterize_until == until);
  assert(get_lifeforce(loaded->character, TRUE, NULL) == 10);
  assert(!IS_FLAG(loaded->character->act, PLR_DEAD));
  puts("PASS: cauterization leaves LF reserves intact and its low effective LF causes no collapse or death.");
  current_time = until;
  ch->wounds = 0; ch->pcdata->sleeping = 0;
  ch->lifeforce = 10000;
  assert(get_lifeforce(ch, TRUE, NULL) > 10);
  puts("PASS: free cauterization persists its LF penalty across reload and expires after fourteen days.");

  // Find a lunar night using the real calendar, then exercise bounded spawning.
  bool found = false;
  for (int hour = 0; hour < 24 * 40; ++hour, current_time += 3600) {
    if (full_moon_night()) { found = true; break; }
  }
  assert(found);
  mob->ttl = 0;
  full_moon_pack_update();
  int packs = 0;
  for (CHAR_DATA *m : char_list) if (full_moon_pack(m) && m->ttl != 0) ++packs;
  assert(packs == 6);
  full_moon_pack_update();
  int again = 0;
  for (CHAR_DATA *m : char_list) if (full_moon_pack(m) && m->ttl != 0) ++again;
  assert(again == packs);
  CHAR_DATA *live = NULL;
  for (CHAR_DATA *m : char_list)
    if (full_moon_pack(m) && m->ttl != 0) { live = m; break; }
  assert(live);
  char_from_room(ch); char_to_room(ch, live->in_room);
  ch->hit = max_hp(ch);
  ch->race = RACE_VETWEREWOLF;
  full_moon_pack_update();
  assert(!in_fight(ch));
  ch->race = RACE_HUMAN;
  full_moon_pack_update();
  assert(in_fight(ch) && in_fight(live));
  ch->desc->outtop = 0; ch->desc->outbuf[0] = '\0';
  do_look(ch, (char *)"");
  assert(strstr(ch->desc->outbuf, "IT IS THE FULL MOON"));
  puts("PASS: entering a pack room starts combat for humans, spares werewolves, and displays the moon notice.");
  while (full_moon_night()) current_time += 3600;
  full_moon_pack_update();
  for (CHAR_DATA *m : char_list) if (full_moon_pack(m)) assert(m->ttl == 0);
  puts("PASS: three pairs spawn once per lunar night and retire when the event ends.");
}
