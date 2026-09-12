#include "merc.h"
#include "recycle.h"
#include <dirent.h>
#include <cctype>
#include <sstream>

extern "C" {
void fread_population_char(CHAR_DATA *ch, FILE *fp);

bool power_operation_goal(int goal) {
  return goal == GOAL_WORSHIP || goal == GOAL_ATTACK_POWER;
}

DOMAIN_TYPE *power_domain(const char *name) {
  if (!name || !*name) return NULL;
  for (DOMAIN_TYPE *dom : DomainVect)
    if (dom && dom->valid && !str_cmp(dom->domain_of, name)) return dom;
  return NULL;
}

bool power_available(DOMAIN_TYPE *dom) {
  return dom && dom->valid && !dom->guest_retired && dom->claimed_territory > 0
      && territory_by_number(dom->claimed_territory) && dom->banished_until <= current_time;
}

static bool power_name_in_list(const char *name, const char *list) {
  if (!name || !list) return false;
  std::istringstream input(list);
  std::string word;
  while (input >> word) if (!str_cmp(word.c_str(), name)) return true;
  return false;
}

int power_relation(FACTION_TYPE *fac, const char *name) {
  if (!fac) return SOCIETY_PATRON_NONE;
  if (fac->vnum == FACTION_CORTEX) return SOCIETY_PATRON_OPPOSE;
  if (name && power_name_in_list(name, fac->power_worships)) return SOCIETY_PATRON_WORSHIP;
  if (name && power_name_in_list(name, fac->power_opposes)) return SOCIETY_PATRON_OPPOSE;
  if (name && !str_cmp(fac->eidilon, name)) return fac->patron_relation;
  return SOCIETY_PATRON_NONE;
}

static void remove_power_name(char *&list, const char *name) {
  std::istringstream input(list ? list : "");
  std::string word, result;
  while (input >> word) {
    if (!str_cmp(word.c_str(), name)) continue;
    if (!result.empty()) result += " ";
    result += word;
  }
  free_string(list);
  list = str_dup(result.c_str());
}

bool set_power_relation(FACTION_TYPE *fac, const char *name, int relation) {
  if (!fac || fac->vnum == FACTION_CORTEX || relation < SOCIETY_PATRON_NONE || relation > SOCIETY_PATRON_OPPOSE) return false;
  // Preserve the legacy primary patron on the first edit.
  if (safe_strlen(fac->eidilon) && fac->patron_relation != SOCIETY_PATRON_NONE) {
    char *&list = fac->patron_relation == SOCIETY_PATRON_WORSHIP ? fac->power_worships : fac->power_opposes;
    if (!power_name_in_list(fac->eidilon, list)) {
      std::string names = std::string(list) + " " + fac->eidilon;
      free_string(list); list = str_dup(names.c_str());
    }
  }
  if (!name || !*name) {
    if (relation != SOCIETY_PATRON_NONE) return false;
    free_string(fac->power_worships); fac->power_worships = str_dup("");
    free_string(fac->power_opposes); fac->power_opposes = str_dup("");
  } else {
    remove_power_name(fac->power_worships, name);
    remove_power_name(fac->power_opposes, name);
    if (relation != SOCIETY_PATRON_NONE) {
      char *&list = relation == SOCIETY_PATRON_WORSHIP ? fac->power_worships : fac->power_opposes;
      std::string names = std::string(list) + (safe_strlen(list) ? " " : "") + name;
      free_string(list); list = str_dup(names.c_str());
    }
  }
  // Keep old patron-dependent abilities attached to the most recently selected patron.
  fac->patron_relation = relation;
  free_string(fac->eidilon);
  fac->eidilon = str_dup(relation == SOCIETY_PATRON_NONE ? "" : name);
  return true;
}

void show_power_relations(CHAR_DATA *ch, FACTION_TYPE *fac) {
  if (fac->vnum == FACTION_CORTEX) {
    send_to_char("`cOpposes`W:`x every higher power (permanent).`x\n\r", ch);
    return;
  }
  std::string worships = fac->power_worships, opposes = fac->power_opposes;
  if (safe_strlen(fac->eidilon) && fac->patron_relation != SOCIETY_PATRON_NONE) {
    std::string &list = fac->patron_relation == SOCIETY_PATRON_WORSHIP ? worships : opposes;
    if (!power_name_in_list(fac->eidilon, list.c_str())) list += " " + std::string(fac->eidilon);
  }
  printf_to_char(ch, "`cWorships`W:`x %s`x\n\r`cOpposes`W:`x %s`x\n\r", worships.empty() ? "none" : worships.c_str(), opposes.empty() ? "none" : opposes.c_str());
}

const char *power_operation_error(int faction, int territory, int goal, const char *target) {
  FACTION_TYPE *fac = clan_lookup(faction);
  LOCATION_TYPE *loc = territory_by_number(territory);
  DOMAIN_TYPE *dom = power_domain(target);
  if (!power_operation_goal(goal)) return "That is not a higher-power goal.";
  if (!fac || (fac->type != FACTION_SOCIETY && fac->type != FACTION_CORE))
    return "Only a society or faction can run this operation.";
  if (!loc || (loc->base_faction_core != faction && loc->base_society != faction
      && loc->base_society_secondary != faction)) return "Your organization must hold a foothold in that territory.";
  if (!dom || dom->claimed_territory != territory) return "The target must be a higher power claiming that territory.";
  if (!power_available(dom)) return "That higher power is out of play and cannot be attacked or worshipped.";
  const int required = goal == GOAL_WORSHIP ? SOCIETY_PATRON_WORSHIP : SOCIETY_PATRON_OPPOSE;
  if (power_relation(fac, target) != required)
    return goal == GOAL_WORSHIP ? "Your society must publicly worship that higher power first."
                               : "Your society must publicly oppose that higher power first.";
  return NULL;
}

bool claim_power_territory(CHAR_DATA *ch, LOCATION_TYPE *territory) {
  if (!ch || !higher_power(ch) || !territory) return false;
  DOMAIN_TYPE *dom = power_domain(ch->name);
  if (dom && dom->claimed_territory > 0) return false;
  if (!dom) {
    dom = new_domain();
    for (DOMAIN_TYPE *other : DomainVect) dom->vnum = UMAX(dom->vnum, other->vnum);
    ++dom->vnum;
    free_string(dom->domain_of);
    dom->domain_of = str_dup(ch->name);
    dom->archetype = ch->race;
    dom->power = 5;
    DomainVect.push_back(dom);
  }
  dom->claimed_territory = number_from_territory(territory);
  SET_FLAG(ch->act, PLR_GUEST);
  ch->pcdata->guest_type = GUEST_HIGHERPOWER;
  ch->pcdata->guest_tier = 6;
  save_char_obj(ch, FALSE, FALSE);
  save_domains(FALSE);
  return true;
}

bool resolve_power_operation(int winner, OPERATION_TYPE *op) {
  // Only an actual battle victory by the sponsoring organization earns progress.
  // Mark it consumed before the next callback or save can see it again.
  if (!op || op != activeoperation || op->hour == 0 || op->power_resolved
      || !power_operation_goal(op->goal)) return false;
  op->power_resolved = true;
  if (winner != op->faction || op->competition != COMPETE_OPEN
      || power_operation_error(op->faction, op->territoryvnum, op->goal, op->target)) return false;
  DOMAIN_TYPE *dom = power_domain(op->target);
  if (op->goal == GOAL_WORSHIP) {
    dom->successful_worships = UMIN(WORSHIPS_FOR_T5, dom->successful_worships + 1);
  } else {
    dom->successful_worships = 0;
    dom->banished_until = current_time + POWER_BANISH_SECONDS;
    CHAR_DATA *power = get_char_world_pc(dom->domain_of);
    if (power) {
      send_to_char("Your worship progress is lost. You are banished from play for 30 days.\n\r", power);
      // End possession as well as removing the body from public rooms.
      if (power->possessing) power->possessing = NULL;
      if (power->in_room) char_from_room(power);
      char_to_room(power, get_room_index(GMHOME));
      save_char_obj(power, FALSE, FALSE);
    }
  }
  save_domains(FALSE);
  save_operations(FALSE);
  CHAR_DATA *power = get_char_world_pc(dom->domain_of);
  if (power && op->goal == GOAL_WORSHIP) show_guest_progress(power);
  else if (power) real_quit(power);
  return true;
}

int guest_remake_tier(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || ch->pcdata->guest_reward_used || IS_FLAG(ch->act, PLR_DEAD)) return 0;
  if (higher_power(ch)) {
    DOMAIN_TYPE *dom = power_domain(ch->name);
    if (!power_available(dom)) return 0;
    return dom->successful_worships >= WORSHIPS_FOR_T5 ? 5
         : dom->successful_worships >= WORSHIPS_FOR_T4 ? 4 : 0;
  }
  if (guestmonster(ch)) {
    const long milestone = UMAX(1, ch->pcdata->monster_reward_hours > 0
        ? ch->pcdata->monster_reward_hours : time_info.monster_hours);
    const long hours = ch->played / 3600;
    return hours > milestone * 2 ? 5 : hours > milestone ? 4 : 0;
  }
  return 0;
}

bool guest_out_of_play(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch)) return false;
  if (ch->pcdata->guest_reward_used) return true;
  if (!higher_power(ch)) return false;
  return !power_available(power_domain(ch->name));
}

void show_guest_progress(CHAR_DATA *ch) {
  if (higher_power(ch)) {
    DOMAIN_TYPE *dom = power_domain(ch->name);
    if (dom) printf_to_char(ch, "`cSuccessful worships`g:`W %d`x. T4 requires `W%d`x; T5 requires `W%d`x.\n\r",
        dom->successful_worships, WORSHIPS_FOR_T4, WORSHIPS_FOR_T5);
    if (dom && dom->banished_until > current_time)
      printf_to_char(ch, "`YBanished for another %ld days; worship and remaking are unavailable.`x\n\r",
          (dom->banished_until - current_time + 86399) / 86400);
  }
  int tier = guest_remake_tier(ch);
  if (!higher_power(ch) && !guestmonster(ch) && ch->pcdata->account)
    tier = ch->pcdata->account->guest_remake_reward;
  if (tier) printf_to_char(ch, "You may remake as a permanent `WT%d`x character:\n\r"
                             "  `Wguest remake t%d `g<`xnew name`g>`x.\n\r"
                             "This retires this guest.`x\n\r", tier, tier);
  else send_to_char("You have not yet earned a guest remake.\n\r", ch);
}

struct PopulationEntry { std::string account; long last; int tier; bool eligible; };
static std::map<std::string, PopulationEntry> population;
static bool population_blocked = false;

static PopulationEntry population_entry(CHAR_DATA *ch, bool online) {
  PopulationEntry entry;
  entry.account = ch->pcdata->account ? ch->pcdata->account->name : ch->pcdata->account_name;
  for (char &c : entry.account) c = std::tolower(static_cast<unsigned char>(c));
  if (online) ch->pcdata->population_last_active = current_time;
  entry.last = ch->pcdata->population_last_active > 0 ? ch->pcdata->population_last_active : ch->lastlogoff;
  entry.tier = get_tier(ch);
  entry.eligible = !entry.account.empty() && !IS_IMMORTAL(ch) && !is_gm(ch)
      && !IS_FLAG(ch->act, PLR_GUEST) && !higher_power(ch)
      && !IS_FLAG(ch->act, PLR_SINSPIRIT)
      && !IS_FLAG(ch->act, PLR_DEAD) && !IS_FLAG(ch->act, PLR_STASIS)
      && !ch->pcdata->guest_reward_used && ch->in_room && ch->in_room->vnum != ROOM_INDEX_GENESIS;
  return entry;
}

void refresh_sanctuary_character(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata) return;
  if (ch->pcdata->confirm_delete) population.erase(ch->name);
  else population[ch->name] = population_entry(ch, ch->desc && ch->desc->connected == CON_PLAYING);
}

void update_sanctuary_population() {
  static long next_scan = 0;
  if (current_time >= next_scan) {
    DIR *directory = opendir(PLAYER_DIR);
    if (directory) {
      population.clear();
      while (dirent *entry = readdir(directory)) {
        std::string name = entry->d_name;
        if (name.empty() || name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz") != std::string::npos) continue;
        CHAR_DATA *online = get_char_world_pc(const_cast<char *>(name.c_str()));
        if (online) {
          population[name] = population_entry(online, online->desc && online->desc->connected == CON_PLAYING);
          continue;
        }
        // Read just the character section; never load inventory or write a save.
        FILE *fp = fopen((std::string(PLAYER_DIR) + name).c_str(), "r");
        if (!fp) continue;
        if (!str_cmp(fread_word(fp), "#PLAYER")) {
          CHAR_DATA *offline = new_char();
          offline->pcdata = new_pcdata();
          free_string(offline->name);
          offline->name = str_dup(name.c_str());
          fread_population_char(offline, fp);
          population[name] = population_entry(offline, false);
          free_char(offline);
        }
        fclose(fp);
      }
      closedir(directory);
      next_scan = current_time + 3600;
    }
  }
  for (CHAR_DATA *ch : char_list)
    if (ch && !IS_NPC(ch) && ch->pcdata)
      population[ch->name] = population_entry(ch, ch->desc && ch->desc->connected == CON_PLAYING);
  std::map<std::string, int> accounts;
  for (const auto &item : population) {
    const PopulationEntry &entry = item.second;
    if (entry.eligible && entry.last >= current_time - SANCTUARY_ACTIVE_SECONDS)
      accounts[entry.account] = UMAX(accounts[entry.account], entry.tier);
  }
  std::size_t high = 0;
  for (const auto &item : accounts) if (item.second >= 4 && item.second <= 5) ++high;
  const bool blocked = !accounts.empty() && high * 100 > accounts.size() * SANCTUARY_HIGH_TIER_PERCENT;
  if (blocked != population_blocked) {
    population_blocked = blocked;
    NEWS_TYPE *news = new_news();
    free_string(news->author);
    news->author = str_dup("Sanctuary Watch");
    free_string(news->message);
    news->message = str_dup(blocked
        ? "Sanctuary Overwhelmed: The growing concentration of exceptionally powerful beings has overwhelmed Sanctuary. Its protection has failed for everyone and cannot return until the strain eases."
        : "Sanctuary Stabilized: The concentration of exceptionally powerful beings has fallen, easing the strain on Sanctuary. No longer overwhelmed, it has stabilized and its protection is restored.");
    news->timer = 2000;
    news->stats[0] = 0; // Everyone can read this, including unaffiliated naturals.
    NewsVect.push_back(news);
    // Save the transition state with the post so a restart cannot repeat it.
    save_news();
    for (DESCRIPTOR_DATA *d : descriptor_list)
      if (d->connected == CON_PLAYING && d->character)
        send_to_char(blocked ? "Sanctuary is overwhelmed by the concentration of powerful beings. Its protection has failed for everyone. See news.\n\r"
                             : "The strain on Sanctuary has eased. It has stabilized and its protection is restored. See news.\n\r", d->character);
  }
}

bool sanctuary_population_blocked() { return population_blocked; }
void restore_sanctuary_population(bool blocked) { population_blocked = blocked; }

}
