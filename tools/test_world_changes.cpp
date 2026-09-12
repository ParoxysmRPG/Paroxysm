#include "merc.h"
#include "recycle.h"
#include <cassert>
#include <cstring>
#include <ctime>
#include <string>

extern "C" {
extern char str_boot_time[];
void pc_update(CHAR_DATA *, int);
void do_storyidea(CHAR_DATA *, char *);
void do_treat(CHAR_DATA *, char *);
}

static void assign(char *&field, const char *value) {
  free_string(field); field = str_dup(value);
}
static CHAR_DATA *player(const char *name) {
  CHAR_DATA *ch = new_char(); ch->pcdata = new_pcdata();
  assign(ch->name, name); assign(ch->pcdata->intro_desc, name);
  ch->level = 2; ch->position = POS_STANDING;
  ch->race = RACE_HUMAN; ch->id = 12345;
  char_to_room(ch, get_room_index(16068)); char_list.push_front(ch);
  ch->desc = new_descriptor(); ch->desc->character = ch;
  ch->desc->connected = CON_PLAYING;
  return ch;
}
static void command(CHAR_DATA *ch, const std::string &text) {
  char input[MSL]; snprintf(input, sizeof(input), "%s", text.c_str());
  do_storyidea(ch, input);
}
static void stories() {
  auto *author = player("Worldauthor"), *other = player("Worldother");
  auto *staff = player("Worldstaff"); staff->level = MAX_LEVEL;
  size_t before = StoryIdeaVect.size();
  command(author, "create Adventure"); assert(StoryIdeaVect.size() == before);
  command(author, "create WorldChange"); assert(StoryIdeaVect.size() == before + 1);
  const std::string id = std::to_string(StoryIdeaVect.size());
  STORYIDEA_TYPE *idea = StoryIdeaVect.back();
  assert(idea->type == PLOT_WORLDCHANGE);
  command(author, "description " + id + " Restore a public garden through an approved community project.");
  command(other, "submit " + id); assert(idea->status == STATUS_INCOMPLETE);
  command(author, "submit " + id); assert(idea->status == STATUS_PENDING);
  current_time += 60 * 86400; save_storyideas();
  assert(idea->status == STATUS_PENDING);
  command(author, "approve " + id + " Give myself a new power.");
  assert(idea->status == STATUS_PENDING);
  command(staff, "approve " + id); assert(idea->status == STATUS_PENDING);
  command(staff, "approve " + id + " Organize three public cleanup scenes and supply the agreed materials.");
  assert(idea->status == STATUS_APPROVED && strstr(idea->secrets, "three public"));
  command(author, "description " + id + " Replace the approved proposal.");
  assert(strstr(idea->description, "garden"));
  command(author, "complete " + id); assert(idea->status == STATUS_APPROVED);
  command(staff, "complete " + id); assert(idea->status == 9);
  StoryIdeaVect.clear(); load_storyideas();
  bool found = false;
  for (auto *saved : StoryIdeaVect) {
    if (strcmp(saved->author, author->name)) continue;
    assert(saved->status == 9 && saved->type == PLOT_WORLDCHANGE);
    assert(strstr(saved->description, "garden") && strstr(saved->secrets, "three public"));
    found = true;
  }
  assert(found);
  puts("PASS: WorldChange-only submissions, ownership, mandatory staff goal, no timed approval, completion and durable history.");
}
static void wounds() {
  auto *patient = player("Woundpatient"), *doctor = player("Wounddoctor");
  patient->wounds = 1; assert(can_heal(patient));
  for (int severity : {2, 3}) {
    patient->wounds = 0;
    wound_char_absolute(patient, severity, doctor);
    assert(!can_heal(patient));
    patient->heal_timer = 1000;
    patient->skills[SKILL_REGEN] = 3;
    patient->skills[SKILL_HYPERREGEN] = 3;
    pc_update(patient, -1);
    assert(patient->heal_timer == 1000 && patient->wounds == severity);
    assert(!treat_wounds(patient, patient));
    assert(treat_wounds(doctor, patient) && can_heal(patient));
    FILE *fp = tmpfile(); assert(fp); write_recovery(fp, patient); rewind(fp);
    invalidate_wound_treatment(patient); assert(!can_heal(patient));
    int next;
    while ((next = fgetc(fp)) != EOF) {
      if (next == '\n' || next == '\r' || next == ' ') continue;
      ungetc(next, fp);
      char *word = fread_word(fp);
      if (!word[0]) break;
      assert(read_recovery(fp, patient, word));
    }
    fclose(fp); assert(can_heal(patient));
    pc_update(patient, -1); assert(patient->heal_timer < 1000);
    wound_char_absolute(patient, severity, doctor); assert(!can_heal(patient));
  }
  patient->wounds = 4; assert(!can_heal(patient));
  // Treatment gates recovery but must not alter its original rates or locations.
  patient->skills[SKILL_REGEN] = patient->skills[SKILL_HYPERREGEN] = 0;
  patient->wounds = 0; wound_char_absolute(patient, 3, doctor);
  patient->heal_timer = 1000;
  assert(treat_wounds(doctor, patient));
  const int original_sector = patient->in_room->sector_type;
  const std::string original_subarea = patient->in_room->subarea;
  patient->in_room->sector_type = SECT_STREET;
  assign(patient->in_room->subarea, "");
  assert(!in_hospital(patient));
  int death_timer = patient->death_timer;
  pc_update(patient, -1);
  assert(patient->heal_timer == 1000 && patient->death_timer == death_timer - 1);
  assign(patient->in_room->subarea, "hospital");
  invalidate_wound_treatment(patient);
  pc_update(patient, -1);
  assert(patient->heal_timer == 1000 && patient->death_timer == death_timer - 1);
  doctor->money = 100000;
  char name[] = "Woundpatient";
  do_treat(doctor, name);
  assert(doctor->pcdata->process == PROCESS_TREATING && !can_heal(patient));
  conclude_process(doctor, PROCESS_TREATING);
  assert(can_heal(patient));
  int timer = patient->heal_timer;
  pc_update(patient, -1); assert(patient->heal_timer == timer - 2);
  patient->heal_timer = 1; pc_update(patient, -1);
  assert(patient->wounds == 2 && patient->heal_timer == 125000 && can_heal(patient));
  pc_update(patient, -1); assert(patient->heal_timer == 124998);
  for (int severity : {2, 3}) {
    patient->wounds = 0; wound_char_absolute(patient, severity, doctor);
    patient->heal_timer = 10000;
    patient->activeat = current_time - 600;
    logon_char(patient);
    assert(patient->heal_timer == 10000);
    assert(treat_wounds(doctor, patient));
    patient->activeat = current_time - 600;
    logon_char(patient);
    assert(patient->heal_timer == (severity == 2 ? 9520 : 9800));
  }
  patient->in_room->sector_type = original_sector;
  assign(patient->in_room->subarea, original_subarea.c_str());
  puts("PASS: untreated severe/critical wounds resist regeneration, treatment requires another character, save/load and reinjury reset.");
  puts("PASS: treatment completion unlocks unchanged healing rates, wound downgrades, hospital requirements and bleed-out behavior.");
  puts("PASS: offline recovery waits for treatment and then uses the existing severe and critical recovery rates.");
}
static void enforcers() {
  auto *target = player("Alarmtarget");
  assert(in_haven(target->in_room));
  assert(!cortex_alarm(target, 0));
  size_t gossip_before = NewsVect.size();
  bool spawned = false;
  for (int i = 0; i < 1000 && !spawned; ++i) spawned = cortex_alarm(target, 2);
  assert(spawned && in_fight(target));
  int count = 0; CHAR_DATA *attacker = nullptr;
  for (auto *mob : char_list) if (cortex_enforcer(mob)) {
    ++count; attacker = mob;
    assert(mob->in_room == target->in_room && !strcmp(mob->aggression, target->name));
    assert(in_fight(mob) && mob->faction == FACTION_CORTEX);
  }
  assert(count >= 2 && count <= 4 && NewsVect.size() == gossip_before + 1);
  assert(strstr(NewsVect.back()->message, "Alarmtarget") && strstr(NewsVect.back()->message, "Cortex enforcers"));
  assert(!cortex_alarm(target, 2) && NewsVect.size() == gossip_before + 1);
  target->pcdata->sleeping = 240;
  cortex_enforcer_defeat(attacker, target);
  assert(target->pcdata->sleeping == 0 && in_fight(target));
  bool monster = false;
  for (auto *mob : char_list) {
    if (cortex_enforcer(mob)) assert(mob->ttl == 1 && !in_fight(mob));
    if (forest_monster(mob) && cortex_breach_monster(mob) && mob->in_room == target->in_room) {
      monster = true; assert(in_fight(mob));
    }
  }
  assert(monster);
  puts("PASS: randomized alarm squad, combat, one automatic rumor, duplicate prevention and monster ambush after defeat.");
}
int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  current_time = time(nullptr); strcpy(str_boot_time, ctime(&current_time)); boot_db();
  stories(); wounds(); enforcers();
  return 0;
}
