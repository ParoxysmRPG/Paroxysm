#include "runtime_io.h"
#ifndef WIN32
#include <sys/stat.h>
#endif

#if defined(macintosh)
#include <types.h>
#else
#include <sys/types.h>
#endif
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <vector>
#include <map>
#include "merc.h"
#include "text_format.h"
#include "olc.h"
#include "gsn.h"
#include "recycle.h"
#include "lookup.h"
#include "global.h"

#if defined(__cplusplus)
extern "C" {
#endif

  /*Local Functions */
  int get_flee_direction args((CHAR_DATA * ch));
  void event_end(EVENT_TYPE *event);

  vector<EVENT_TYPE *> EventVect;
  EVENT_TYPE *nullevent;

#define EVENT_ONE_TIME 60 * 24 * 4

#define EVENT_TWO_TIME 60 * 24 * 8

#define EVENT_THREE_TIME 60 * 24 * 12

#define SCHEME_COST_ONE 10000
#define SCHEME_COST_TWO 20000
#define SCHEME_COST_THREE 40000

  int event_recruitment = 0;
  int event_teaching = 0;
  int event_occurance = 0;
  int event_operation = 0;

  int event_dominance = 0;
  int event_aegis = 0;
  int event_cleanse = 0;
  int event_catastrophe = 0;

  char *const event_names[] = {
    "None",        "MindControl",     "Discredit",   "Steal", "Outcast",     "Brainwash",       "Heist",       "Operation", "Recruitment", "Teaching",        "Occurance",   "Condition", "Dominance",   "Aegis",           "Cleanse",     "Catastrophe", "nothing",     "RevokeSanctuary", "Rob",         "disruption", "storm",       "flood",           "blackout",    "hurricane", "malady",      "haunt",           "dreambelief", "uninvite", "mute",        "sabotage",        "ambush", "compromised", "StateOfEmergency"};

  int scheme_cost(int type) {
    switch (type) {
    case EVENT_ROB:
    case EVENT_DISCREDIT:
    case EVENT_MINDCONTROL:
    case EVENT_OUTCAST:
    case EVENT_SUE:
    case EVENT_STORM:
      return 10000;
      break;
    case EVENT_STATE_OF_EMERGENCY:
    case EVENT_FLOOD:
    case EVENT_BLACKOUT:
    case EVENT_HAUNT:
      return 20000;
      break;
    case EVENT_AEGIS:
    case EVENT_CATASTROPHE:
    case EVENT_CLEANSE:
    case EVENT_DOMINANCE:
    case EVENT_UNDERSTANDINGPLUS:
    case EVENT_UNDERSTANDINGMINUS:
      return 100000;
      break;
    case EVENT_BRAINWASH:
    case EVENT_DREAMBELIEF:
    case EVENT_UNINVITED:
    case EVENT_MUTE:
    case EVENT_COMPROMISED:
    case EVENT_SABOTAGE:
    case EVENT_AMBUSH:
      return 30000;
      break;
    case EVENT_CONDITION:
    case EVENT_HEIST:
    case EVENT_HURRICANE:
    case EVENT_DISRUPTION:
    case EVENT_MALADY:
      return 40000;
      break;
    case EVENT_OCCURANCE:
    case EVENT_OPERATION:
    case EVENT_RECRUITMENT:
    case EVENT_TEACHING:
      return 60000;
      break;
    }

    return 10000;
  }
  int scheme_duration(int type) {
    switch (type) {
    case EVENT_ROB:
    case EVENT_MINDCONTROL:
    case EVENT_SUE:
    case EVENT_STORM:
    case EVENT_STATE_OF_EMERGENCY:
    case EVENT_FLOOD:
    case EVENT_BLACKOUT:
    case EVENT_HURRICANE:
    case EVENT_DISRUPTION:
    case EVENT_MALADY:
    case EVENT_DREAMBELIEF:
      return 72;
      break;
    case EVENT_BRAINWASH:
    case EVENT_HAUNT:
    case EVENT_MUTE:
    case EVENT_COMPROMISED:
    case EVENT_SABOTAGE:
    case EVENT_AMBUSH:
      return 48;
      break;
    case EVENT_AEGIS:
    case EVENT_CATASTROPHE:
    case EVENT_CLEANSE:
    case EVENT_DOMINANCE:
      return 168;
      break;
    case EVENT_UNDERSTANDINGPLUS:
    case EVENT_UNDERSTANDINGMINUS:
    case EVENT_UNINVITED:
      return 24;
      break;
    case EVENT_CONDITION:
    case EVENT_HEIST:
    case EVENT_DISCREDIT:
    case EVENT_OUTCAST:
      return 168;
      break;
    case EVENT_OCCURANCE:
    case EVENT_OPERATION:
    case EVENT_RECRUITMENT:
    case EVENT_TEACHING:
      return 120;
      break;
    }

    return 1;
  }

  void complete_event args((EVENT_TYPE * event));

  void fread_event(FILE *fp) {
    char buf[MSL];
    const char *word;
    bool fMatch;
    EVENT_TYPE *event;

    event = new_event();

    for (;;) {
      word = feof(fp) ? "End" : fread_word(fp);
      fMatch = FALSE;
      switch (UPPER(word[0])) {
      case '*':
        fMatch = TRUE;
        fread_to_eol(fp);
        break;

      case 'A':
        KEY("Author", event->author, fread_string(fp));
        KEY("ActiveTime", event->active_time, fread_number(fp));
        KEY("Account", event->account, fread_string(fp));
        break;
      case 'B':
        KEY("BatteryAuthor", event->karma_battery_author, fread_number(fp));
        KEY("BatteryStoryRunner", event->karma_battery_storyrunner, fread_number(fp));
        break;
      case 'C':
        KEY("Coauthors", event->coauthors, fread_string(fp));
        break;
      case 'D':
        KEY("Desc", event->description, fread_string(fp));
        KEY("DescIntro", event->introduction, fread_string(fp));
        KEY("DescThwart", event->thwart_method, fread_string(fp));
        KEY("DeactiveTime", event->deactive_time, fread_number(fp));
        break;
      case 'E':
        if (!str_cmp(word, "End")) {
          if (!event->author) {
            bug("Fread_Event: Name not found.", 0);
            free_event(event);
            return;
          }
          EventVect.push_back(event);
          return;
        }
        break;
      case 'F':
        KEY("Faction", event->faction, fread_number(fp));
        break;
      case 'I':
        KEY("Imprint", event->imprint, fread_string(fp));
        break;
      case 'L':
        KEY("Limited", event->limited, fread_number(fp));
        KEY("LaunchCost", event->launch_cost, fread_number(fp));
        break;
      case 'M':
        KEY("Message", event->message, fread_string(fp));
        break;
      case 'N':
        KEY("NoThwart", event->nothwart, fread_number(fp));
        break;
      case 'P':
        KEY("ProfessionalFocus", event->professional_focus, fread_number(fp));
        break;
      case 'R':
        KEY("Researched", event->researched, fread_string(fp));
        break;
      case 'S':
        KEY("SocialiteBonus", event->socialite_bonus, fread_number(fp));
        KEY("ShownNews", event->shown_news, fread_number(fp));
        KEY("Storyline", event->storyline, fread_string(fp));
        break;
      case 'T':
        KEY("Type", event->type, fread_number(fp));
        KEY("TypeTwo", event->typetwo, fread_number(fp));
        KEY("Target", event->target, fread_string(fp));
        KEY("ThwartAttempted", event->thwart_attempted, fread_number(fp));
        KEY("ThwartCooldown", event->thwart_cooldown, fread_number(fp));
        break;
      }
      if (!fMatch) {
        sprintf(buf, "Fread_event: no match: %s", word);
        bug(buf, 0);
      }
    }
  }

  void load_events() {
    nullevent = new_event();
    FILE *fp;

    if ((fp = fopen(EVENT_FILE, "r")) != NULL) {
      for (;;) {
        char letter;
        char *word;

        letter = fread_letter(fp);
        if (letter == '*') {
          fread_to_eol(fp);
          continue;
        }

        if (letter != '#') {
          bug("Load_Events: # not found.", 0);
          break;
        }

        word = fread_word(fp);
        if (!str_cmp(word, "EVENT")) {
          fread_event(fp);
          continue;
        }
        else if (!str_cmp(word, "END")) {
          break;
        }
        else {
          bug("Load_Events: bad section.", 0);
          continue;
        }
      }
      fclose(fp);

      // Check to see if you need to close after a dlopen.
    }
    else {
      bug("Cannot open events.txt", 0);
      exit(0);
    }
  }

  static void write_event(FILE *fpout, const EVENT_TYPE *event) {
    fprintf(fpout, "#EVENT\n");
    fprintf(fpout, "Author      %s~\n", event->author);
    fprintf(fpout, "ProfessionalFocus %d\n", event->professional_focus);
    fprintf(fpout, "SocialiteBonus %d\n", event->socialite_bonus);
    fprintf(fpout, "LaunchCost %d\n", event->launch_cost);
    fprintf(fpout, "ThwartCooldown %d\n", event->thwart_cooldown);
    fprintf(fpout, "Desc     %s~\n", event->description);
    fprintf(fpout, "DescIntro   %s~\n", event->introduction);
    fprintf(fpout, "Researched %s~\n", event->researched);
    fprintf(fpout, "Target  %s~\n", event->target);
    fprintf(fpout, "Faction    %d\n", event->faction);
    fprintf(fpout, "Type %d\n", event->type);
    fprintf(fpout, "TypeTwo %d\n", event->typetwo);

    fprintf(fpout, "Imprint %s~\n", event->imprint);
    fprintf(fpout, "Message %s~\n", event->message);
    fprintf(fpout, "DescThwart %s~\n", event->thwart_method);
    fprintf(fpout, "ActiveTime %d\n", event->active_time);
    fprintf(fpout, "DeactiveTime %d\n", event->deactive_time);
    fprintf(fpout, "ShownNews %d\n", event->shown_news);
    fprintf(fpout, "Account %s~\n", event->account);
    fprintf(fpout, "BatteryAuthor %d\n", event->karma_battery_author);
    fprintf(fpout, "BatteryStoryRunner %d\n", event->karma_battery_storyrunner);
    fprintf(fpout, "Storyline %s~\n", event->storyline);
    fprintf(fpout, "ThwartAttempted %d\n", event->thwart_attempted);
    fprintf(fpout, "Coauthors %s~\n", event->coauthors);
    fprintf(fpout, "NoThwart %d\n", event->nothwart);
    fprintf(fpout, "Limited %d\n", event->limited);
    fprintf(fpout, "End\n\n");
  }

  void save_events_backup() {
    FILE *fpout;
    int i = 0;
    char buf[MSL];
    if (time_info.day % 7 == 0)
    sprintf(buf, "../data/back1/events.txt");
    else if (time_info.day % 6 == 0)
    sprintf(buf, "../data/back2/events.txt");
    else if (time_info.day % 5 == 0)
    sprintf(buf, "../data/back3/events.txt");
    else if (time_info.day % 4 == 0)
    sprintf(buf, "../data/back4/events.txt");
    else if (time_info.day % 3 == 0)
    sprintf(buf, "../data/back5/events.txt");
    else if (time_info.day % 2 == 0)
    sprintf(buf, "../data/back6/events.txt");
    else
    sprintf(buf, "../data/back7/events.txt");

    if ((fpout = open_snapshot_file(buf)) == NULL) {
      bug("Cannot open events.txt for writing", 0);
      return;
    }

    for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
    it != EventVect.end(); ++it) {
      if (!(*it)->author || (*it)->author[0] == '\0') {
        bug("Save_events: Blank event in vector", i);
        continue;
      }
      if ((*it)->valid == FALSE)
      continue;

      if (current_time > (*it)->deactive_time + (3600 * 36))
      continue;

      write_event(fpout, *it);
    }

    fprintf(fpout, "#END\n");
    close_snapshot_file(fpout);

    /*
if(number_percent() % 3 == 0)
{
EventVect.clear();
load_events();
}
*/
  }

  void save_events() {
    FILE *fpout;
    int i = 0;
    if ((fpout = open_snapshot_file(EVENT_FILE)) == NULL) {
      bug("Cannot open events.txt for writing", 0);
      return;
    }

    for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
    it != EventVect.end(); ++it) {
      if (!(*it)->author || (*it)->author[0] == '\0') {
        bug("Save_events: Blank event in vector", i);
        continue;
      }
      if ((*it)->valid == FALSE)
      continue;
      if (current_time > (*it)->deactive_time + (3600 * 36))
      continue;

      write_event(fpout, *it);
    }

    fprintf(fpout, "#END\n");
    close_snapshot_file(fpout);

    /*
if(number_percent() % 3 == 0)
{
EventVect.clear();
load_events();
}
*/
    save_events_backup();
  }

  void event_message(int timer, char *message) {
    NEWS_TYPE *news;

    news = new_news();
    news->timer = timer;
    free_string(news->message);
    news->message = str_dup(message);
    free_string(news->author);
    news->author = str_dup("Town Events");
    NewsVect.push_back(news);
  }

  int get_event_timer(int type) { return 60 * 24; }

  EVENT_TYPE *get_event(int number) {
    int num = 1;

    for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
    it != EventVect.end(); ++it) {
      if ((*it)->valid == FALSE)
      continue;

      if ((*it)->active_time > current_time)
      continue;

      if (num == number)
      return (*it);

      num++;
    }

    return nullevent;
  }

  int get_event_number(EVENT_TYPE *event) {
    int i;
    i = 1;
    for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
    it != EventVect.end(); ++it) {
      if ((*it)->valid == FALSE)
      continue;

      if ((*it)->active_time > current_time)
      continue;

      if (event == *it)
      return i;
      i++;
    }
    return 0;
  }

  static int scheme_socialite_bonus(CHAR_DATA *ch) {
    return 5 * UMAX(0, get_skill(ch, SKILL_SOCIALFOCUS));
  }

  static void resolve_scheme_focus(EVENT_TYPE *event, CHAR_DATA *author) {
    // Preserve any launch values already saved when upgrading legacy schemes.
    if (event->professional_focus < 0)
      event->professional_focus = prof_focus(author);
    if (event->socialite_bonus < 0)
      event->socialite_bonus = scheme_socialite_bonus(author);
  }

  // Resolve missing legacy values together, loading an offline author only once.
  static int scheme_professional_focus(EVENT_TYPE *event) {
    if (event->professional_focus >= 0 && event->socialite_bonus >= 0)
      return event->professional_focus;
    if (!event->author || event->author[0] == '\0')
      return -1;

    CHAR_DATA *author = get_char_world_pc(event->author);
    if (author != NULL && author->pcdata != NULL) {
      resolve_scheme_focus(event, author);
      return event->professional_focus;
    }

    DESCRIPTOR_DATA descriptor = {};
    bool loaded = load_char_obj(&descriptor, event->author);
    if (loaded && descriptor.character != NULL && descriptor.character->pcdata != NULL)
      resolve_scheme_focus(event, descriptor.character);
    // load_char_obj also allocates a character when the player file is absent.
    if (descriptor.character != NULL)
      free_char(descriptor.character);
    return event->socialite_bonus >= 0 ? event->professional_focus : -1;
  }

  static bool listed_scheme(EVENT_TYPE *event) {
    return event != NULL && event != nullevent && event->valid &&
           event->active_time <= current_time;
  }

  static bool can_see_scheme(CHAR_DATA *ch, EVENT_TYPE *event) {
    if (ch == NULL || IS_NPC(ch) || ch->pcdata == NULL || !listed_scheme(event))
      return FALSE;
    // Reading a list or news never loads an offline author or rolls focus.
    return event->deactive_time < current_time ||
           !str_cmp(ch->name, event->author) ||
           is_exact_name(ch->name, event->researched);
  }

  bool can_see_scheme_news(CHAR_DATA *ch, NEWS_TYPE *news) {
    if (news == NULL || news->author == NULL || news->message == NULL)
    return FALSE;
    if (str_cmp(news->author, "Town Events"))
    return TRUE;
    // Introductions are already matched by message when publishing/removing news.
    // This also covers news saved before the focus requirement was introduced.
    for (vector<EVENT_TYPE *>::iterator it = EventVect.begin(); it != EventVect.end(); ++it) {
      EVENT_TYPE *event = *it;
      if (event->valid && event->active_time <= current_time &&
          event->deactive_time >= current_time && event->introduction != NULL &&
          !str_cmp(news->message, event->introduction) && !can_see_scheme(ch, event))
      return FALSE;
    }
    return TRUE;
  }

  bool state_of_emergency(void) {
    // Saved event windows handle restarts, thwarting and overlapping schemes.
    for (EVENT_TYPE *event : EventVect) {
      if (event->valid && current_time > event->active_time &&
          current_time < event->deactive_time &&
          (event->type == EVENT_STATE_OF_EMERGENCY ||
           event->typetwo == EVENT_STATE_OF_EMERGENCY))
        return TRUE;
    }
    return FALSE;
  }

  bool has_event(CHAR_DATA *ch) {

    for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
    it != EventVect.end(); ++it) {
      if (!(*it)->author || (*it)->author[0] == '\0') {
        continue;
      }
      if ((*it)->valid == FALSE)
      continue;

      if (!str_cmp(ch->name, (*it)->author))
      return TRUE;
    }
    return FALSE;
  }

  static int scheme_thwart_cost(EVENT_TYPE *event, CHAR_DATA *ch = NULL) {
    // Older saves did not record the payment. Reconstruct their launch rules.
    if (event->launch_cost <= 0)
      event->launch_cost = event->limited ? scheme_cost(event->type) / 2
        : UMAX(scheme_cost(event->type), scheme_cost(event->typetwo));
    const int cost = (event->launch_cost + 2) / 3;
    return has_territory_bonus(ch, TERRITORY_THWART_DISCOUNT)
      ? cost - cost * 15 / 100 : cost;
  }

  static int scheme_launch_cost(CHAR_DATA *ch, EVENT_TYPE *event, bool limited) {
    const int cost = limited ? scheme_cost(event->type) / 2
      : UMAX(scheme_cost(event->type), scheme_cost(event->typetwo));
    return has_territory_bonus(ch, TERRITORY_SCHEME_DISCOUNT) ? cost - cost / 10 : cost;
  }

  enum { SCHEME_GUARD_THWART = 1, SCHEME_GUARD_INVESTIGATION = 2, SCHEME_GUARD_TIME = 4 };

  static int scheme_character_defenses(CHAR_DATA *author) {
    return (has_territory_bonus(author, TERRITORY_THWART_DEFENSE) ? SCHEME_GUARD_THWART : 0)
      | (has_territory_bonus(author, TERRITORY_INVESTIGATE_DEFENSE) ? SCHEME_GUARD_INVESTIGATION : 0)
      | (has_territory_bonus(author, TERRITORY_BOUGHT_TIME) ? SCHEME_GUARD_TIME : 0);
  }

  static int scheme_territory_defenses(EVENT_TYPE *event) {
    if (!event->author || !event->author[0]) return 0;
    CHAR_DATA *author = get_char_world_pc(event->author);
    if (author && author->pcdata) return scheme_character_defenses(author);
    DESCRIPTOR_DATA descriptor = {};
    const bool loaded = load_char_obj(&descriptor, event->author);
    const int defenses = loaded && descriptor.character && descriptor.character->pcdata
      ? scheme_character_defenses(descriptor.character) : 0;
    if (descriptor.character) free_char(descriptor.character);
    return defenses;
  }

  char *thwart_status(EVENT_TYPE *event) {
    if (current_time <= event->active_time) return "`rPremature`x";
    if (current_time >= event->deactive_time) return "`rEnded`x";
    if (current_time < event->thwart_cooldown) return "`rCooldown`x";
    return "`gYes`x";
  }

  static bool scheme_contest(CHAR_DATA *ch, int schemer_focus, int socialite_bonus,
                             int &challenger_roll, int &schemer_roll,
                             int attack_bonus = 0, int defense_bonus = 0) {
    challenger_roll = number_range(1, 100) + 10 * prof_focus(ch) + scheme_socialite_bonus(ch) + attack_bonus;
    schemer_roll = number_range(1, 100) + 10 * schemer_focus + socialite_bonus + 5 + defense_bonus;
    return challenger_roll > schemer_roll;
  }

  void investigate_scheme(CHAR_DATA *ch, int number, bool prepaid) {
    if (!ch) return;
    EVENT_TYPE *event = get_event(number);
    if (IS_NPC(ch) || !ch->pcdata || !listed_scheme(event)) {
      send_to_char("No such scheme.\n\r", ch);
      return;
    }
    if (can_see_scheme(ch, event)) {
      send_to_char("You already know about that scheme. Use scheme info for details.\n\r", ch);
      return;
    }
    if (is_gm(ch) || !ch->pcdata->account) {
      send_to_char("You must investigate as a player character.\n\r", ch);
      return;
    }
    const int cost = prepaid ? 0 : territory_investigation_cost(ch, 500);
    if (ch->pcdata->influence + ch->pcdata->scheme_influence < cost) {
      printf_to_char(ch, "You need %d influence to investigate a scheme.\n\r", cost);
      return;
    }
    const int focus = scheme_professional_focus(event);
    if (focus < 0) {
      send_to_char("This scheme cannot be investigated right now.\n\r", ch);
      return;
    }
    if (cost > 0)
      charge_influence(ch, INFLUENCE_SCHEME, cost);
    const int defenses = scheme_territory_defenses(event);
    int investigator_roll, schemer_roll;
    if (scheme_contest(ch, focus, event->socialite_bonus, investigator_roll, schemer_roll,
        has_territory_bonus(ch, TERRITORY_INVESTIGATE_ATTACK) ? 10 : 0,
        (defenses & SCHEME_GUARD_INVESTIGATION) ? 10 : 0)) {
      std::string researchers = event->researched;
      researchers += " ";
      researchers += ch->name;
      free_string(event->researched);
      event->researched = str_dup(researchers.c_str());
      printf_to_char(ch, "Your investigation succeeds. Use scheme info %d to see what you uncovered.\n\r", number);
    }
    else {
      send_to_char("Your investigation fails. A SCHEME IS UNDERWAY, but you uncover no details.\n\r", ch);
    }
    save_char_obj(ch, FALSE, FALSE);
    save_events();
  }

  static void attempt_scheme_thwart(CHAR_DATA *ch, EVENT_TYPE *event) {
    if (event == nullevent || !can_see_scheme(ch, event)) {
      send_to_char("No such scheme.\n\r", ch);
      return;
    }
    if (current_time >= event->deactive_time) {
      send_to_char("That scheme is already over.\n\r", ch);
      return;
    }
    if (current_time <= event->active_time) {
      send_to_char("That scheme is not active yet.\n\r", ch);
      return;
    }
    if (is_gm(ch) || !ch->pcdata->account) {
      send_to_char("You must attempt a thwart as a player character.\n\r", ch);
      return;
    }
    if (!str_cmp(ch->name, event->author) ||
        !str_cmp(ch->pcdata->account->name, event->account)) {
      send_to_char("You cannot thwart your own scheme.\n\r", ch);
      return;
    }
    if (current_time < event->thwart_cooldown) {
      printf_to_char(ch, "This scheme cannot be thwarted again for %d minutes.\n\r",
                    (event->thwart_cooldown - (int)current_time + 59) / 60);
      return;
    }
    const int cost = scheme_thwart_cost(event, ch);
    if (ch->pcdata->influence + ch->pcdata->scheme_influence < cost) {
      printf_to_char(ch, "You need %d influence to attempt this thwart.\n\r", cost);
      return;
    }
    const int schemer_focus = scheme_professional_focus(event);
    if (schemer_focus < 0) {
      send_to_char("The schemer's professional focus is unavailable.\n\r", ch);
      return;
    }
    charge_influence(ch, INFLUENCE_SCHEME, cost);
    const int defenses = scheme_territory_defenses(event);
    int attacker_roll, defender_roll;
    const bool succeeded = scheme_contest(ch, schemer_focus, event->socialite_bonus, attacker_roll, defender_roll,
      has_territory_bonus(ch, TERRITORY_THWART_ATTACK) ? 10 : 0,
      (defenses & SCHEME_GUARD_THWART) ? 10 : 0);
    event->thwart_attempted = 1;
    printf_to_char(ch, "You spend %d influence. Your thwart roll: %d. Schemer's roll: %d.\n\r",
                  cost, attacker_roll, defender_roll);
    if (succeeded) {
      // End immediately without scene rewards, character conversion or movement.
      event->deactive_time = current_time - (3600 * 16);
      event->thwart_cooldown = 0;
      event_end(event);
      for (NEWS_TYPE *news : NewsVect)
        if (news->valid && !str_cmp(news->message, event->introduction)) news->timer = 0;
      ch->pcdata->week_tracker[TRACK_SCHEMES_THWARTED]++;
      ch->pcdata->life_tracker[TRACK_SCHEMES_THWARTED]++;
      send_to_char("You successfully thwart the scheme.\n\r", ch);
    }
    else {
      const int hours = (defenses & SCHEME_GUARD_TIME) ? 7 : 6;
      event->thwart_cooldown = current_time + hours * 3600;
      printf_to_char(ch, "Your thwart fails. Nobody can attempt to thwart this scheme for %s hours.\n\r",
                     hours == 7 ? "seven" : "six");
    }
    save_char_obj(ch, FALSE, FALSE);
    save_events();
    char notification[MSL];
    snprintf(notification, sizeof(notification),
             "%s attempted to thwart your scheme #%d and %s. %s",
             ch->name, get_event_number(event),
             succeeded ? "succeeded" : "failed",
             succeeded ? "Your scheme has ended."
               : (defenses & SCHEME_GUARD_TIME)
                 ? "Your scheme continues; further thwart attempts are blocked for seven hours."
                 : "Your scheme continues; further thwart attempts are blocked for six hours.");
    // This delivers immediately when online and saves the message for login.
    offline_message(event->author, notification);
  }

  void end_schemes_on_death(CHAR_DATA *ch) {
    if (ch == NULL || IS_NPC(ch) || ch->pcdata == NULL)
      return;

    bool ended = FALSE;
    for (EVENT_TYPE *event : EventVect) {
      if (event == NULL || event == nullevent || !event->valid ||
          event->deactive_time <= current_time || event->author == NULL ||
          str_cmp(event->author, ch->name))
        continue;

      // Pending launches must not start after their author dies either.
      if (event->active_time <= current_time)
        event_end(event);
      event->deactive_time = current_time - (3600 * 16);
      event->thwart_cooldown = 0;
      for (NEWS_TYPE *news : NewsVect)
        if (news->valid && !str_cmp(news->message, event->introduction))
          news->timer = 0;
      ended = TRUE;
    }
    if (ended) {
      save_events();
      send_to_char("Your death brings your schemes to a premature end.\n\r", ch);
    }
  }

  _DOFUN(do_event) {
    char arg1[MSL];
    AreaList::iterator it;
    char arg2[MSL];
    char arg3[MSL];
    struct stat sb;
    std::string buf;
    Buffer outbuf;
    DESCRIPTOR_DATA d;
    CHAR_DATA *victim;
    int i, j;

    EVENT_TYPE *event;

    argument = one_argument_nouncap(argument, arg1);
    argument = one_argument_nouncap(argument, arg2);
    argument = one_argument_nouncap(argument, arg3);

    if (!str_cmp(arg1, "list")) {
      send_to_char("`WCurrent Schemes`x\n\r", ch);
      int i = 1;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;

        if ((*it)->active_time > current_time)
        continue;

        int number = i++;
        printf_to_char(ch, "`W%d`c)`x\t", number);
        if (!can_see_scheme(ch, *it)) {
          send_to_char("A SCHEME IS UNDERWAY\n\r", ch);
          continue;
        }
        if ((*it)->typetwo != 0)
        printf_to_char(ch, "`W%s's %s-%s`x\n\r", (*it)->author, event_names[(*it)->type], event_names[(*it)->typetwo]);
        else
        printf_to_char(ch, "`W%s's %s`x\n\r", (*it)->author, event_names[(*it)->type]);
      }
      return;
    }
    if (!str_cmp(arg1, "aid")) {
      if (is_gm(ch) || IS_FLAG(ch->act, PLR_GUEST))
      return;
      int amount = atoi(arg3);
      if (amount < 0 || amount > ch->pcdata->influence) {
        send_to_char("You don't have that much to give.\n\r", ch);
        return;
      }
      if ((victim = get_char_room(ch, NULL, arg2)) == NULL || IS_NPC(victim)) {
        if ((victim = get_char_world_pc(arg2)) == NULL)
        {
          send_to_char("They're not here.\n\r", ch);
          return;
        }
      }
      if (ch == victim) {
        send_to_char("You cannot aid yourself.\n\r", ch);
        return;
      }
      charge_influence(ch, INFLUENCE_SCHEME, amount);
      victim->pcdata->scheme_influence += amount;
      printf_to_char(ch, "You send %d influence to %s be used in schemes.\n\r", amount, PERS(victim, ch));
      printf_to_char(victim, "%s sends you %d influence to be used in schemes.\n\r", PERS(ch, victim), amount);
    }
    if (!str_cmp(arg1, "delete")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;

        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          (*it)->valid = FALSE;
        }
      }
    }
    if (!str_cmp(arg1, "retarget")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;
        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          free_string((*it)->target);
          (*it)->target = str_dup(arg3);
        }
      }
    }
    if (!str_cmp(arg1, "remessage")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;
        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          string_append(ch, &(*it)->message);
        }
      }
    }
    if (!str_cmp(arg1, "refresh")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;
        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          int duration =
          (scheme_duration((*it)->type) * 3600 * number_range(75, 130)) / 100;
          (*it)->deactive_time = (*it)->active_time + duration;
        }
      }
    }
    if (!str_cmp(arg1, "ageup")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;
        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          (*it)->deactive_time -= (3600 * 12);
        }
      }
    }

    if (!str_cmp(arg1, "thwartattempted")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;
        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          (*it)->thwart_attempted = 1;
          send_to_char("Done.\n\r", ch);
        }
      }
    }
    if (!str_cmp(arg1, "reimprint")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;
        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          string_append(ch, &(*it)->imprint);
        }
      }
    }
    if (!str_cmp(arg1, "restoryrunner")) {
      if (!IS_IMMORTAL(ch))
      return;
      int i = 0;
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;
        if ((*it)->active_time > current_time)
        continue;

        i++;

        if (i == atoi(arg2)) {
          string_append(ch, &(*it)->coauthors);
        }
      }
    }
    if (!str_cmp(arg1, "investigate")) {
      if (!is_number(arg2) || atoi(arg2) <= 0) {
        send_to_char("Syntax: scheme investigate <number>. Each attempt costs 500 influence.\n\r", ch);
        return;
      }
      investigate_scheme(ch, atoi(arg2), FALSE);
      return;
    }
    if (!str_cmp(arg1, "thwart")) {
      if (!is_number(arg2) || atoi(arg2) <= 0) {
        send_to_char("Syntax: scheme thwart <number>. Each attempt costs one third of the scheme's launch influence, before territory discounts.\n\r", ch);
        return;
      }
      attempt_scheme_thwart(ch, get_event(atoi(arg2)));
      return;
    }
    if (!str_cmp(arg1, "info")) {
      const int i = is_number(arg2) ? atoi(arg2) : 0;
      EVENT_TYPE *event = get_event(i);
      if (!listed_scheme(event)) {
        send_to_char("No such scheme.\n\r", ch);
        return;
      }
      if (!can_see_scheme(ch, event)) {
        send_to_char("A SCHEME IS UNDERWAY\n\rUse scheme investigate <number> to uncover details.\n\r", ch);
        return;
      }
      printf_to_char(ch, "`W%d`c)`x\n\r", i);
      printf_to_char(ch, "Thwart cost: %d influence. Available: %s.\n\r", scheme_thwart_cost(event, ch), thwart_status(event));
      printf_to_char(ch, "Author: `W%s`x\n\r", event->author);
      if (current_time < event->deactive_time)
      send_to_char("`gActive`x\n\r", ch);
      else
      send_to_char("`DInactive`x\n\r", ch);

      printf_to_char(ch, "Introduction: %s\n\r", event->introduction);

      if (!str_cmp(ch->name, event->author) || is_exact_name(ch->name, event->researched)) {
        if (event->typetwo != 0)
        printf_to_char(ch, "Type: %s-%s\n\nDescription: %s\n\r", event_names[event->type], event_names[event->typetwo], event->description);
        else
        printf_to_char(ch, "Type: %s\n\nDescription: %s\n\r", event_names[event->type], event->description);
      }
      if (current_time > event->deactive_time) {
        printf_to_char(ch, "Thwart method: %s\n\r", event->thwart_method);
      }

      if (IS_IMMORTAL(ch)) {
        printf_to_char(ch, "Thwart cooldown until: %d\n\r", event->thwart_cooldown);
        printf_to_char(ch, "Type: %s  Target %s.\n\r", event_names[event->type], event->target);
        printf_to_char(ch, "Description: %s\n\n\r", event->description);
        printf_to_char(ch, "Message: %s\n\r", event->message);
      }
      return;
    }
    if (IS_AFFECTED(ch, AFF_OUTCAST)) {
      send_to_char("None of your friends seem to be talking to you at the moment.\n\r", ch);
      return;
    }

    if (!str_cmp(arg1, "create")) {
      if (ch->pcdata->making_event != NULL && !str_cmp(ch->pcdata->making_event->author, ch->name)) {
        send_to_char("You're already creating a scheme\n\r", ch);
        return;
      }
      if (ch->pcdata->influence + ch->pcdata->scheme_influence < 10000 && !IS_IMMORTAL(ch)) {
        send_to_char("You need more influence.\n\r", ch);
        return;
      }
      if (has_event(ch)) {
        send_to_char("You need to wait for your current schme to finish first.\n\r", ch);
        return;
      }
      if (IS_FLAG(ch->act, PLR_GUEST) && ch->pcdata->guest_type == GUEST_NIGHTMARE) {
        send_to_char("That would not be very secretive.\n\r", ch);
        return;
      }

      if (IS_FLAG(ch->act, PLR_DEAD))
      return;

      if (ch->pcdata->event_cooldown > 0) {
        send_to_char("You can't make a new scheme yet.\n\r", ch);
        return;
      }
      event = new_event();
      free_string(event->author);
      event->author = str_dup(ch->name);
      if (ch->pcdata->account != NULL) {
        free_string(event->account);
        event->account = str_dup(ch->pcdata->account->name);
      }
      event->faction = ch->faction;
      ch->pcdata->making_event = event;
      send_to_char("Scheme created.\n\r", ch);
      return;
    }
    if (!str_cmp(arg1, "launch")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to launch.\n\r", ch);
        return;
      }

      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to launch.\n\r", ch);
        return;
      }

      if (event->type == 0) {
        send_to_char("You have to set the scheme's type first.", ch);
        return;
      }
      if (higher_power(ch) && (event->type == EVENT_UNDERSTANDINGMINUS || event->type == EVENT_AEGIS || event->type == EVENT_CLEANSE || event->type == EVENT_DOMINANCE)) {
        send_to_char("Higher Powers cannot run these schemes.", ch);
        return;
      }
      if (higher_power(ch) && (event->typetwo == EVENT_UNDERSTANDINGMINUS || event->typetwo == EVENT_AEGIS || event->typetwo == EVENT_CLEANSE || event->typetwo == EVENT_DOMINANCE)) {
        send_to_char("Higher Powers cannot run these schemes.", ch);
        return;
      }

      if (!in_haven(ch->in_room)) {
        send_to_char("You have to get to Gravesend first.\n\r", ch);
        return;
      }
      const int launch_cost = scheme_launch_cost(ch, event, FALSE);
      if (launch_cost > ch->pcdata->influence + ch->pcdata->scheme_influence) {
        printf_to_char(ch, "You need at least %d influence to do that.\n\r", launch_cost);
        return;
      }

      if (safe_strlen(event->description) < 100) {
        send_to_char("The scheme needs more of a description first.\n\rscheme description\n\r", ch);
        return;
      }
      if (safe_strlen(event->introduction) < 80) {
        send_to_char("The scheme needs more of an introduction first.\n\rscheme introduction\n\r", ch);
        return;
      }
      if ((event->type >= EVENT_ROB && event->type <= EVENT_OUTCAST) || event->type == EVENT_CONDITION || event->type == EVENT_MALADY || event->type == EVENT_HAUNT || event->type == EVENT_DREAMBELIEF || event->type == EVENT_MUTE || event->type == EVENT_SABOTAGE || event->type == EVENT_AMBUSH || event->type == EVENT_COMPROMISED) {
        if (!event->target || event->target[0] == '\0' || safe_strlen(event->target) < 1) {
          send_to_char("You have to set a target first\n\rscheme target <charname>", ch);
          return;
        }
      }
      if ((event->typetwo >= EVENT_ROB && event->typetwo <= EVENT_OUTCAST) || event->typetwo == EVENT_CONDITION || event->typetwo == EVENT_MALADY || event->typetwo == EVENT_HAUNT || event->typetwo == EVENT_DREAMBELIEF || event->typetwo == EVENT_MUTE || event->typetwo == EVENT_SABOTAGE || event->typetwo == EVENT_AMBUSH || event->typetwo == EVENT_COMPROMISED) {
        if (!event->target || event->target[0] == '\0' || safe_strlen(event->target) < 1) {
          send_to_char("You have to set a target first\n\rscheme target <charname>", ch);
          return;
        }
      }

      if (event->type == EVENT_MINDCONTROL || event->type == EVENT_BRAINWASH || event->type == EVENT_CONDITION) {
        if (!event->imprint || event->imprint[0] == '\0' || safe_strlen(event->imprint) < 3) {
          send_to_char("You have to set an imprint first\n\rscheme imprint <message>", ch);
          return;
        }
      }
      if (event->typetwo == EVENT_MINDCONTROL || event->typetwo == EVENT_BRAINWASH || event->typetwo == EVENT_CONDITION) {
        if (!event->imprint || event->imprint[0] == '\0' || safe_strlen(event->imprint) < 3) {
          send_to_char("You have to set an imprint first\n\rscheme imprint <message>", ch);
          return;
        }
      }

      if (event->type == EVENT_HAUNT || event->typetwo == EVENT_HAUNT) {
        if (!event->message || event->message[0] == '\0' || safe_strlen(event->message) < 3) {
          send_to_char("You have to set a message first\n\rscheme message", ch);
          return;
        }
      }

      event->professional_focus = prof_focus(ch);
      event->socialite_bonus = scheme_socialite_bonus(ch);
      event->active_time = current_time + (3600 * 24);
      int duration =
      (scheme_duration(event->type) * 3600 * number_range(75, 130)) / 100;
      int durboost = 0;
      for (int i = 0; i < MAX_CONTACTS; i++) {
        if (ch->pcdata->contact_jobs[i] == CJOB_SCHEMES && safe_strlen(ch->pcdata->contact_names[i]) > 2 && safe_strlen(ch->pcdata->contact_descs[i]) > 2)
        durboost += skillpoint(get_skill(ch, contacts_table[i]));
      }
      duration = duration * (10 + durboost) / 10;
      event->deactive_time = event->active_time + duration;

      send_to_char("Scheme launched!\n\r", ch);
      if (safe_strlen(event->storyline) > 1 && get_storyline(NULL, event->storyline) != NULL)
      get_storyline(NULL, event->storyline)->power += 3;

      ch->pcdata->week_tracker[TRACK_SCHEMES_LAUNCHED]++;
      ch->pcdata->life_tracker[TRACK_SCHEMES_LAUNCHED]++;
      if (event->type == EVENT_ROB || event->type == EVENT_DISCREDIT || event->type == EVENT_OUTCAST || event->type == EVENT_SUE || event->type == EVENT_BRAINWASH || event->type == EVENT_AMBUSH || event->type == EVENT_SABOTAGE) {
        villain_mod(ch, 40, "Scheme");
      }
      if (event->type == EVENT_STORM || event->type == EVENT_BLACKOUT || event->type == EVENT_FLOOD || event->type == EVENT_CONDITION || event->type == EVENT_MALADY || event->type == EVENT_UNINVITED || event->type == EVENT_HEIST || event->type == EVENT_MUTE || event->type == EVENT_COMPROMISED) {
        villain_mod(ch, 120, "Scheme");
      }
      if (event->type == EVENT_HURRICANE || event->type == EVENT_DISRUPTION || event->type == EVENT_UNDERSTANDINGMINUS) {
        villain_mod(ch, 200, "Scheme");
      }
      if (event->type == EVENT_AEGIS || event->type == EVENT_CLEANSE || event->type == EVENT_DOMINANCE || event->type == EVENT_HAUNT) {
        villain_mod(ch, 150, "Scheme");
      }

      if (event->type == EVENT_CATASTROPHE) {
        villain_mod(ch, 100, "Scheme");
      }
      if (event->typetwo == EVENT_ROB || event->typetwo == EVENT_DISCREDIT || event->typetwo == EVENT_OUTCAST || event->typetwo == EVENT_SUE || event->typetwo == EVENT_BRAINWASH || event->type == EVENT_AMBUSH || event->type == EVENT_SABOTAGE) {
        villain_mod(ch, 40, "Scheme");
      }
      if (event->typetwo == EVENT_STORM || event->typetwo == EVENT_BLACKOUT || event->typetwo == EVENT_FLOOD || event->typetwo == EVENT_CONDITION || event->typetwo == EVENT_MALADY || event->typetwo == EVENT_UNINVITED || event->typetwo == EVENT_MUTE || event->typetwo == EVENT_COMPROMISED) {
        villain_mod(ch, 120, "Scheme");
      }
      if (event->typetwo == EVENT_HEIST || event->typetwo == EVENT_HURRICANE || event->typetwo == EVENT_DISRUPTION || event->typetwo == EVENT_UNDERSTANDINGMINUS) {
        villain_mod(ch, 200, "Scheme");
      }
      if (event->typetwo == EVENT_AEGIS || event->typetwo == EVENT_CLEANSE || event->typetwo == EVENT_DOMINANCE || event->typetwo == EVENT_HAUNT) {
        villain_mod(ch, 150, "Scheme");
      }
      if (event->typetwo == EVENT_CATASTROPHE) {
        villain_mod(ch, 100, "Scheme");
      }

      if (event->type == EVENT_AEGIS)
      scout_report("Your contacts inform your society that an aegis will be occuring in one day.");
      else if (event->type == EVENT_CLEANSE)
      scout_report("Your contacts inform your society that a cleanse will occur in one day.");
      else if (event->type == EVENT_DOMINANCE)
      scout_report("Your contacts inform your society that a dominance ritual will occur in one day.");
      else if (event->type == EVENT_UNDERSTANDINGMINUS)
      scout_report("Your contacts inform your society that sanctuary will fail in one day.");
      if (event->typetwo == EVENT_AEGIS)
      scout_report("Your contacts inform your society that an aegis will be occuring in one day.");
      else if (event->typetwo == EVENT_CLEANSE)
      scout_report("Your contacts inform your society that a cleanse will occur in one day.");
      else if (event->typetwo == EVENT_DOMINANCE)
      scout_report("Your contacts inform your society that a dominance ritual will occur in one day.");
      else if (event->typetwo == EVENT_UNDERSTANDINGMINUS)
      scout_report("Your contacts inform your society that sanctuary will fail in one day.");

      ch->pcdata->event_cooldown = 100;

      event->launch_cost = launch_cost;
      charge_influence(ch, INFLUENCE_SCHEME, event->launch_cost);

      social_behave_mod(ch, 15, "running a scheme.");

      if (IS_IMMORTAL(ch)) {
        ch->pcdata->event_cooldown = 0;
      }
      EventVect.push_back(event);

      return;
    }
    if (!str_cmp(arg1, "limited")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to launch.\n\r", ch);
        return;
      }

      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to launch.\n\r", ch);
        return;
      }

      if (event->type == 0) {
        send_to_char("You have to set the scheme's type first.", ch);
        return;
      }

      if (!in_haven(ch->in_room)) {
        send_to_char("You have to get to Gravesend first.\n\r", ch);
        return;
      }
      const int launch_cost = scheme_launch_cost(ch, event, TRUE);
      if (launch_cost >
          ch->pcdata->influence + ch->pcdata->scheme_influence) {
        printf_to_char(ch, "You need at least %d influence to do that.\n\r", launch_cost);
        return;
      }

      if (safe_strlen(event->description) < 100) {
        send_to_char("The scheme needs more of a description first.\n\rscheme description\n\r", ch);
        return;
      }
      if (safe_strlen(event->introduction) < 80) {
        send_to_char("The scheme needs more of an introduction first.\n\rscheme introduction\n\r", ch);
        return;
      }
      if ((event->type >= EVENT_ROB && event->type <= EVENT_OUTCAST) || event->type == EVENT_CONDITION || event->type == EVENT_MALADY || event->type == EVENT_HAUNT || event->type == EVENT_DREAMBELIEF || event->type == EVENT_MUTE || event->type == EVENT_COMPROMISED) {
        if (!event->target || event->target[0] == '\0' || safe_strlen(event->target) < 1) {
          send_to_char("You have to set a target first\n\rscheme target <charname>", ch);
          return;
        }
      }
      if (event->type == EVENT_MINDCONTROL || event->type == EVENT_BRAINWASH || event->type == EVENT_CONDITION) {
        if (!event->imprint || event->imprint[0] == '\0' || safe_strlen(event->imprint) < 3) {
          send_to_char("You have to set an imprint first\n\rscheme imprint <message>", ch);
          return;
        }
      }
      if ((event->typetwo >= EVENT_ROB && event->typetwo <= EVENT_OUTCAST) || event->typetwo == EVENT_CONDITION || event->typetwo == EVENT_MALADY || event->typetwo == EVENT_HAUNT || event->typetwo == EVENT_DREAMBELIEF || event->type == EVENT_MUTE || event->type == EVENT_AMBUSH || event->typetwo == EVENT_AMBUSH || event->type == EVENT_SABOTAGE || event->typetwo == EVENT_SABOTAGE || event->typetwo == EVENT_COMPROMISED) {
        if (!event->target || event->target[0] == '\0' || safe_strlen(event->target) < 1) {
          send_to_char("You have to set a target first\n\rscheme target <charname>", ch);
          return;
        }
      }
      if (event->typetwo == EVENT_MINDCONTROL || event->typetwo == EVENT_BRAINWASH || event->typetwo == EVENT_CONDITION) {
        if (!event->imprint || event->imprint[0] == '\0' || safe_strlen(event->imprint) < 3) {
          send_to_char("You have to set an imprint first\n\rscheme imprint <message>", ch);
          return;
        }
      }

      if (event->type == EVENT_HAUNT || event->typetwo == EVENT_HAUNT) {
        if (!event->message || event->message[0] == '\0' || safe_strlen(event->message) < 3) {
          send_to_char("You have to set a message first\n\rscheme message", ch);
          return;
        }
      }
      if (event->type == EVENT_AEGIS || event->type == EVENT_CATASTROPHE || event->type == EVENT_CLEANSE || event->type == EVENT_DOMINANCE || event->type == EVENT_UNDERSTANDINGPLUS || event->type == EVENT_UNDERSTANDINGMINUS) {
        send_to_char("You cannot do that type of scheme as a limited scheme.\n\r", ch);
        return;
      }
      if (event->typetwo == EVENT_AEGIS || event->typetwo == EVENT_CATASTROPHE || event->typetwo == EVENT_CLEANSE || event->typetwo == EVENT_DOMINANCE || event->typetwo == EVENT_UNDERSTANDINGPLUS || event->typetwo == EVENT_UNDERSTANDINGMINUS) {
        send_to_char("You cannot do that type of scheme as a limited scheme.\n\r", ch);
        return;
      }

      event->professional_focus = prof_focus(ch);
      event->socialite_bonus = scheme_socialite_bonus(ch);
      event->active_time = current_time + (3600 * 24);
      event->deactive_time = event->active_time + (3600 * 24);
      event->limited = 1;
      event->thwart_attempted = 1;
      send_to_char("Scheme launched!\n\r", ch);
      if (safe_strlen(event->storyline) > 1 && get_storyline(NULL, event->storyline) != NULL)
      get_storyline(NULL, event->storyline)->power += 3;

      ch->pcdata->week_tracker[TRACK_SCHEMES_LAUNCHED]++;
      ch->pcdata->life_tracker[TRACK_SCHEMES_LAUNCHED]++;
      if (event->type == EVENT_ROB || event->type == EVENT_DISCREDIT || event->type == EVENT_OUTCAST || event->type == EVENT_SUE || event->type == EVENT_BRAINWASH || event->type == EVENT_SABOTAGE || event->type == EVENT_AMBUSH) {
        villain_mod(ch, 40, "Scheme");
      }
      if (event->type == EVENT_STORM || event->type == EVENT_BLACKOUT || event->type == EVENT_FLOOD || event->type == EVENT_CONDITION || event->type == EVENT_MALADY || event->type == EVENT_UNINVITED || event->type == EVENT_MUTE || event->type == EVENT_COMPROMISED) {
        villain_mod(ch, 120, "Scheme");
      }
      if (event->type == EVENT_HEIST || event->type == EVENT_HURRICANE || event->type == EVENT_DISRUPTION || event->type == EVENT_UNDERSTANDINGMINUS) {
        villain_mod(ch, 200, "Scheme");
      }
      if (event->type == EVENT_AEGIS || event->type == EVENT_CLEANSE || event->type == EVENT_DOMINANCE || event->type == EVENT_HAUNT) {
        villain_mod(ch, 100, "Scheme");
      }
      if (event->typetwo == EVENT_ROB || event->typetwo == EVENT_DISCREDIT || event->typetwo == EVENT_OUTCAST || event->typetwo == EVENT_SUE || event->typetwo == EVENT_BRAINWASH || event->typetwo == EVENT_SABOTAGE || event->typetwo == EVENT_AMBUSH) {
        villain_mod(ch, 40, "Scheme");
      }
      if (event->typetwo == EVENT_STORM || event->typetwo == EVENT_BLACKOUT || event->typetwo == EVENT_FLOOD || event->typetwo == EVENT_CONDITION || event->typetwo == EVENT_MALADY || event->typetwo == EVENT_UNINVITED || event->typetwo == EVENT_MUTE || event->typetwo == EVENT_COMPROMISED) {
        villain_mod(ch, 120, "Scheme");
      }
      if (event->typetwo == EVENT_HEIST || event->typetwo == EVENT_HURRICANE || event->typetwo == EVENT_DISRUPTION || event->typetwo == EVENT_UNDERSTANDINGMINUS) {
        villain_mod(ch, 200, "Scheme");
      }
      if (event->typetwo == EVENT_AEGIS || event->typetwo == EVENT_CLEANSE || event->typetwo == EVENT_DOMINANCE || event->typetwo == EVENT_HAUNT) {
        villain_mod(ch, 100, "Scheme");
      }

      ch->pcdata->event_cooldown = 100;

      event->launch_cost = launch_cost;
      charge_influence(ch, INFLUENCE_SCHEME, event->launch_cost);

      social_behave_mod(ch, 15, "running a scheme.");
      EventVect.push_back(event);

      return;
    }
    if (!str_cmp(arg1, "storyline")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      buf = haven::format_text("%s %s %s", arg2, arg3, argument);
      if (get_storyline(ch, buf.data()) != NULL) {
        free_string(event->storyline);
        event->storyline = str_dup(get_storyline(ch, buf.data())->name);
        send_to_char("Done.\n\r", ch);
        return;
      }
      send_to_char("No such storyline.\n\r", ch);
    }
    if (!str_cmp(arg1, "type")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      j = -1;
      if (!str_cmp(arg2, "state") && !str_cmp(arg3, "of") && !str_cmp(argument, "emergency"))
        j = EVENT_STATE_OF_EMERGENCY;
      for (i = 0; i < MAX_EVENT; i++) {
        if (!str_cmp(event_names[i], arg2))
        j = i;
      }
      if (j == -1) {
        for (i = 0; i < MAX_EVENT; i++) {
          printf_to_char(ch, "%s, ", event_names[i]);
        }
      }
      else {

        for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
        it != EventVect.end(); ++it) {
          if ((*it)->valid == FALSE)
          continue;

          if ((*it)->type == j) {
            //		send_to_char("Someone else is already running a scheme like
            //that.\n\r", ch); 		return;
          }
        }

        event->type = j;
        send_to_char("Done.\n\r", ch);
      }
    }
    if (!str_cmp(arg1, "typetwo")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      j = -1;
      if (!str_cmp(arg2, "state") && !str_cmp(arg3, "of") && !str_cmp(argument, "emergency"))
        j = EVENT_STATE_OF_EMERGENCY;
      for (i = 0; i < MAX_EVENT; i++) {
        if (!str_cmp(event_names[i], arg2))
        j = i;
      }
      if (j == -1) {
        for (i = 0; i < MAX_EVENT; i++) {
          printf_to_char(ch, "%s, ", event_names[i]);
        }
      }
      else {

        for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
        it != EventVect.end(); ++it) {
          if ((*it)->valid == FALSE)
          continue;

          if ((*it)->type == j) {
            //              send_to_char("Someone else is already running a scheme
            //              like that.\n\r", ch); return;
          }
        }

        event->typetwo = j;
        send_to_char("Done.\n\r", ch);
      }
    }
    if (!str_cmp(arg1, "target")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      send_to_char("Valid group target keywords: Supernaturals, Naturals, Vampires, Vampire, Werewolves, Werewolf, Faeborn, Angelborn, Demonborn, Demigods, [Society name without spaces], (Alliance Name), (Character name), Everyone\n\r", ch);
      if (event->type == EVENT_CONDITION || event->type == EVENT_MALADY || event->type == EVENT_HAUNT || event->type == EVENT_MUTE || event->type == EVENT_SABOTAGE || event->type == EVENT_AMBUSH) {
        buf = haven::format_text("%s %s %s", arg2, arg3, argument);
        free_string(event->target);
        event->target = str_dup(buf.data());
        send_to_char("Done.\n\r", ch);
        return;
      }
      if (event->typetwo == EVENT_CONDITION || event->typetwo == EVENT_MALADY || event->typetwo == EVENT_HAUNT || event->typetwo == EVENT_MUTE || event->typetwo == EVENT_SABOTAGE || event->typetwo == EVENT_AMBUSH) {
        buf = haven::format_text("%s %s %s", arg2, arg3, argument);
        free_string(event->target);
        event->target = str_dup(buf.data());
        send_to_char("Done.\n\r", ch);
        return;
      }
      if (event->type == EVENT_DREAMBELIEF || event->typetwo == EVENT_DREAMBELIEF) {
        if (fetch_fantasy(ch, atoi(arg2)) == NULL || fetch_fantasy(ch, atoi(arg2))->active == FALSE) {
          send_to_char("No such dreamworld.\n\r", ch);
          return;
        }
        if (fetch_fantasy(ch, atoi(arg2))->highlight_time == 0) {
          send_to_char("That world isn't close enough right now.\n\r", ch);
          return;
        }

        free_string(event->target);
        event->target = str_dup(fetch_fantasy(ch, atoi(arg2))->name);
        send_to_char("Done.\n\r", ch);
        return;
      }
      bool online = FALSE;
      d.original = NULL;
      if ((victim = get_char_world_pc_noname(ch, arg2)) !=
          NULL) // Victim is online.
      {
        online = TRUE;
      }
      else {
        if (!load_char_obj(&d, arg2)) {
          printf_to_char(ch, "\n\r%s is not a character!\n\r", capitalize(arg2));
          return;
        }

        buf = haven::format_text("%s%s", PLAYER_DIR, capitalize(arg2));
        stat(buf.data(), &sb);
        victim = d.character;
      }

      if (IS_NPC(victim)) {
        send_to_char("\n\rYou can't target mobiles!\n\r", ch);
        return;
      }
      for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
      it != EventVect.end(); ++it) {
        if ((*it)->valid == FALSE)
        continue;

        if (!str_cmp((*it)->target, victim->name)) {
          send_to_char("Someone else is already targeting that person.\n\r", ch);
          if (!online)
          free_char(victim);
          return;
        }
      }
      if (is_gm(victim) || higher_power(victim) || higher_power(ch)) {
        send_to_char("You cannot target them.\n\r", ch);
        if (!online)
        free_char(victim);
        return;
      }

      free_string(event->target);
      event->target = str_dup(victim->name);
      if (!online)
      free_char(victim);
      send_to_char("Done.\n\r", ch);
    }
    if (!str_cmp(arg1, "description")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      send_to_char("`WThis description is to set the information people can obtain by doing research\n\r`x", ch);
      string_append(ch, &event->description);
    }
    if (!str_cmp(arg1, "message")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      send_to_char("`WThis message will set what people will see when haunted, with a different message each line.\n\r`x", ch);
      string_append(ch, &event->message);
    }
    if (!str_cmp(arg1, "storyrunners")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      send_to_char("`WEnter coauthor account names, separated by spaces. Thwarts are resolved by contested rolls.`x\n\r", ch);

      string_append(ch, &event->coauthors);
    }
    if (!str_cmp(arg1, "introduction")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      send_to_char("`WThis description is to set the information people can obtain without doing any research\n\r`x", ch);
      string_append(ch, &event->introduction);
    }
    if (!str_cmp(arg1, "method")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      send_to_char("`WThis optional description records how the scheme could be stopped in the story. Thwarts use contested rolls.\n\r`x", ch);
      string_append(ch, &event->thwart_method);
    }
    if (!str_cmp(arg1, "imprint")) {
      event = ch->pcdata->making_event;

      if (event == NULL || event == nullevent) {
        send_to_char("You have no scheme to edit.\n\r", ch);
        return;
      }
      send_to_char("`WThis short string is the imprint message the target will receive.\n\r`x", ch);
      string_append(ch, &event->imprint);
    }
  }

  void event_apply(EVENT_TYPE *event) {
    CHAR_DATA *ch;
    int i;

    if (event->type == EVENT_RECRUITMENT || event->typetwo == EVENT_RECRUITMENT) {
      event_recruitment = event->faction;
    }
    if (event->type == EVENT_TEACHING || event->typetwo == EVENT_TEACHING) {
      event_teaching = event->faction;
    }
    if (event->type == EVENT_OCCURANCE || event->typetwo == EVENT_OCCURANCE) {
      event_occurance = event->faction;
    }
    if (event->type == EVENT_OPERATION || event->typetwo == EVENT_OPERATION) {
      event_operation = event->faction;
    }

    if (event->type == EVENT_DOMINANCE)
    event_dominance = 1;

    // Full moon temporarily suppresses these effects without ending the events.
    if (event->type == EVENT_AEGIS)
    event_aegis = !full_moon();

    if (event->type == EVENT_CLEANSE)
    event_cleanse = !full_moon();

    if (event->typetwo == EVENT_DOMINANCE)
    event_dominance = 1;

    if (event->typetwo == EVENT_AEGIS)
    event_aegis = !full_moon();

    if (event->typetwo == EVENT_CLEANSE)
    event_cleanse = !full_moon();

    if (event->type == EVENT_CATASTROPHE || event->typetwo == EVENT_CATASTROPHE) {
      event_catastrophe = 1;
      CHAR_DATA *victim = get_char_world_pc(event->author);
      if (victim != NULL && IS_FLAG(victim->act, PLR_ASCENDING) && get_tier(victim) < 5 && victim->pcdata->account != NULL) {
        int basekarma = charcost(victim);
        victim->pcdata->tier_raised++;
        int newkarma = charcost(victim);
        victim->pcdata->tier_raised--;
        int cost = newkarma - basekarma;
        if (cost <= available_karma(victim)) {
          victim->pcdata->account->karma -= cost;
          victim->spentkarma += cost;
          victim->pcdata->tier_raised++;
          REMOVE_FLAG(victim->act, PLR_ASCENDING);
        }
      }
    }
    if (event->type == EVENT_STORM)
    crisis_storm = 1;
    if (event->type == EVENT_FLOOD)
    crisis_flood = 1;
    if (event->type == EVENT_BLACKOUT)
    crisis_blackout = 1;
    if (event->type == EVENT_HURRICANE)
    crisis_hurricane = 1;
    if (event->type == EVENT_UNINVITED)
    crisis_uninvited = 1;
    if (event->type == EVENT_DISRUPTION)
    town_blackout = 10;
    if (event->typetwo == EVENT_STORM)
    crisis_storm = 1;
    if (event->typetwo == EVENT_FLOOD)
    crisis_flood = 1;
    if (event->typetwo == EVENT_BLACKOUT)
    crisis_blackout = 1;
    if (event->typetwo == EVENT_HURRICANE)
    crisis_hurricane = 1;
    if (event->typetwo == EVENT_UNINVITED)
    crisis_uninvited = 1;
    if (event->typetwo == EVENT_DISRUPTION)
    town_blackout = 10;

    if (event->type == EVENT_MINDCONTROL || event->typetwo == EVENT_MINDCONTROL) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;

        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (str_cmp(ch->name, event->target))
        continue;

        char buf[MSL];
        remove_newlines(buf, event->imprint);
        for (i = 0; i < 25; i++) {
          if (!str_cmp(ch->pcdata->imprint[i], buf)) {
            return;
          }
        }
        auto_imprint(ch, buf, IMPRINT_INFLUENCE);
      }
    }

    if (event->type == EVENT_DISCREDIT || event->typetwo == EVENT_DISCREDIT) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;

        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (str_cmp(ch->name, event->target))
        continue;

        if (IS_AFFECTED(ch, AFF_DISCREDIT))
        continue;

        AFFECT_DATA af;
        af.where = TO_AFFECTS;
        af.type = 0;
        af.level = 10;
        af.duration = 240;
        af.location = APPLY_NONE;
        af.modifier = 0;
        af.caster = NULL;
        af.weave = FALSE;
        af.bitvector = AFF_DISCREDIT;
        affect_to_char(ch, &af);
      }
    }
    if (event->type == EVENT_ROB || event->typetwo == EVENT_ROB) {
      if (time_info.minute % 32 != 0)
      return;
      CHAR_DATA *author;
      if ((author = get_char_world_pc(event->author)) == NULL) {
        return;
      }
      OBJ_DATA *obj;
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;

        if (d->connected != CON_PLAYING)
        continue;
        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;
        if (str_cmp(ch->name, event->target))
        continue;

        for (obj = ch->carrying; obj != NULL; obj = obj->next_content) {
          if (!IS_SET(obj->extra_flags, ITEM_WARDROBE))
          continue;
          if (number_percent() % 77 == 0 || (obj->item_type != ITEM_CLOTHING && number_percent() % 11 == 0)) {
            obj_from_char(obj);
            obj_to_char(obj, author);
            REMOVE_BIT(obj->extra_flags, ITEM_WARDROBE);
            printf_to_char(
            author, "You get %s in loot from %s as part of your scheme.\n\r", obj->description, NAME(ch));
            return;
          }
        }
      }
    }

    if (event->type == EVENT_SUE || event->typetwo == EVENT_SUE) {
      if (time_info.minute % 32 != 0)
      return;

      CHAR_DATA *author;
      if ((author = get_char_world_pc(event->author)) == NULL) {
        return;
      }
      struct stat sb;
      DESCRIPTOR_DATA d;
      CHAR_DATA *victim;
      bool online = FALSE;
      char buf[MSL];

      d.original = NULL;
      if ((victim = get_char_world_pc(event->target)) != NULL && !IS_NPC(victim)) // Victim is online.
      online = TRUE;
      else {
        if ((victim = get_char_world_pc(event->target)) !=
            NULL) // Victim is online.
        online = TRUE;
        else {

          if (!load_char_obj(&d, event->target)) {
            return;
          }

          sprintf(buf, "%s%s", PLAYER_DIR, capitalize(event->target));
          stat(buf, &sb);
          victim = d.character;
        }
      }
      if (IS_NPC(victim)) {
        if (!online)
        free_char(victim);

        return;
      }
      int amount = victim->pcdata->total_money / 4 + victim->money / 8;
      amount /= 25;
      amount = UMAX(amount, 1000);
      victim->pcdata->total_money -= amount;
      author->pcdata->total_money += amount;
      printf_to_char(author, "You get $%d in loot.\n\r", amount / 100);
      save_char_obj(victim, FALSE, FALSE);
      if (!online)
      free_char(victim);

      return;
    }

    if (event->type == EVENT_OUTCAST || event->typetwo == EVENT_OUTCAST) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;

        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (str_cmp(ch->name, event->target))
        continue;

        if (IS_AFFECTED(ch, AFF_OUTCAST))
        continue;

        AFFECT_DATA af;
        af.where = TO_AFFECTS;
        af.type = 0;
        af.level = 10;
        af.duration = 120;
        af.location = APPLY_NONE;
        af.modifier = 0;
        af.caster = NULL;
        af.weave = FALSE;
        af.bitvector = AFF_OUTCAST;
        affect_to_char(ch, &af);
      }
    }

    if (event->type == EVENT_DREAMBELIEF || event->typetwo == EVENT_DREAMBELIEF) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;
        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;

        if (ch == NULL)
        continue;
        if (IS_NPC(ch))
        continue;

        if (!str_cmp(ch->name, event->author))
        continue;

        if (ch->pcdata->dream_identity_timer < 30) {
          if (!str_cmp(ch->pcdata->identity_world, event->target))
          ch->pcdata->dream_identity_timer = 60;
          else {
            int point = -1;
            free_string(ch->pcdata->identity_world);
            ch->pcdata->identity_world = str_dup(event->target);
            free_string(ch->pcdata->dream_identity);
            ch->pcdata->dream_identity = str_dup("");
            if ((get_tier(ch) < 2 || is_weakness(NULL, ch) || (get_tier(ch) == 2 && ch->faction == 0 && number_range(1, 43432) % 135 == 0)) && safe_strlen(dream_detail(ch, ch->pcdata->identity_world, DREAM_DETAIL_NAME)) <= 2) {
              for (vector<FANTASY_TYPE *>::iterator ft = FantasyVect.begin();
              ft != FantasyVect.end(); ++ft) {
                if ((*ft)->valid == FALSE)
                continue;
                if (!str_cmp((*ft)->name, event->target)) {
                  for (int i = 0; i < 200; i++) {
                    if (safe_strlen((*ft)->participants[i]) > 2 && daysidle((*ft)->participants[i]) > 10 && number_percent() % 4 == 0) {
                      free_string(ch->pcdata->dream_identity);
                      ch->pcdata->dream_identity =
                      str_dup((*ft)->participant_names[i]);
                      point = i;
                    }
                  }
                }
              }
            }
            if (point == -1)
            //                        printf_to_char(ch, "You believe you are %s
            //                        from the world of %s\n\r", //                        (dream_detail(ch, //                        ch->pcdata->identity_world, //                        DREAM_DETAIL_NAME), event->target));
            point = -1;
            else {
              for (vector<FANTASY_TYPE *>::iterator ft = FantasyVect.begin();
              ft != FantasyVect.end(); ++ft) {
                if ((*ft)->valid == FALSE)
                continue;
                if (!str_cmp((*ft)->name, event->target)) {
                  //                              printf_to_char(ch, "You believe
                  //                              you are %s, %s, from the world
                  //                              of %s. Known for %s\n\r", //                              (*ft)->participant_names[point], //                              (*ft)->participant_shorts[point], //                              (*ft)->name, //                              (*ft)->participant_fames[point]);
                }
              }
            }
          }
        }
      }
    }
    if (event->type == EVENT_BRAINWASH || event->typetwo == EVENT_BRAINWASH) {
      bool found;
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;

        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;

        if (ch == NULL)
        continue;
        if (IS_NPC(ch))
        continue;

        if (!str_cmp(ch->name, event->author))
        continue;

        found = FALSE;

        for (i = 0; i < 25; i++) {
          if (!str_cmp(ch->pcdata->imprint[i], event->imprint) && found == FALSE) {
            found = TRUE;
          }
        }
        if (found == FALSE) {
          for (i = 0; i < 25; i++) {
            if (!str_cmp(ch->pcdata->imprint[i], "") && found == FALSE) {
              auto_imprint(ch, event->imprint, IMPRINT_INFLUENCE);
              found = TRUE;
            }
          }
        }
      }
    }
    if (event->type == EVENT_HAUNT || event->typetwo == EVENT_HAUNT) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;
        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (!str_cmp(ch->name, event->author))
        continue;

        if (number_percent() % 17 != 0)
        continue;

        char targ1[MSL];
        one_argument_nouncap(event->target, targ1);

        if ((!str_cmp(targ1, "supernaturals") && is_super(ch)) || (!str_cmp(targ1, "naturals") && !is_super(ch)) || (!str_cmp(targ1, "vampires") && is_vampire(ch)) || (!str_cmp(targ1, "werewolves") && is_werewolf(ch)) || (!str_cmp(targ1, "vampire") && is_vampire(ch)) || (!str_cmp(targ1, "werewolf") && is_werewolf(ch)) || (!str_cmp(targ1, "faeborn") && is_faeborn(ch)) || (!str_cmp(targ1, "angelborn") && is_angelborn(ch)) || (!str_cmp(targ1, "demonborn") && is_demonborn(ch)) || (!str_cmp(targ1, "demigods") && is_demigod(ch)) || (part_of_alliance(ch, event->target)) || (part_of_alliance(ch, targ1)) || (!str_cmp(targ1, ch->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(event->target, clan_lookup(ch->faction)->name)) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(event->target, clan_lookup(ch->factiontwo)->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->faction)->name))) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->factiontwo)->name))) || !str_cmp(targ1, "everyone")) {
          int value = number_range(1, linecount(event->message));
          printf_to_char(ch, "%s\n\r", fetch_line(event->message, value));
          WAIT_STATE(ch, PULSE_PER_SECOND * 5);
        }
      }
    }

    if (event->type == EVENT_MUTE || event->typetwo == EVENT_MUTE) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;
        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (!str_cmp(ch->name, event->author))
        continue;

        char targ1[MSL];
        one_argument_nouncap(event->target, targ1);

        if (IS_AFFECTED(ch, AFF_MUTE))
        continue;


        if ((!str_cmp(targ1, "supernaturals") && is_super(ch)) || (!str_cmp(targ1, "naturals") && !is_super(ch)) || (!str_cmp(targ1, "vampires") && is_vampire(ch)) || (!str_cmp(targ1, "werewolves") && is_werewolf(ch)) || (!str_cmp(targ1, "vampire") && is_vampire(ch)) || (!str_cmp(targ1, "werewolf") && is_werewolf(ch)) || (!str_cmp(targ1, "faeborn") && is_faeborn(ch)) || (!str_cmp(targ1, "angelborn") && is_angelborn(ch)) || (!str_cmp(targ1, "demonborn") && is_demonborn(ch)) || (!str_cmp(targ1, "demigods") && is_demigod(ch)) || (!str_cmp(targ1, "everyone")) || (part_of_alliance(ch, event->target)) || (part_of_alliance(ch, targ1)) || (!str_cmp(targ1, ch->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(event->target, clan_lookup(ch->faction)->name)) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(event->target, clan_lookup(ch->factiontwo)->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->faction)->name))) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->factiontwo)->name)))) {

          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          af.duration = 120;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_MUTE;
          affect_to_char(ch, &af);
        }
      }
    }
    if (event->type == EVENT_SABOTAGE || event->typetwo == EVENT_SABOTAGE) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;
        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (ch->pcdata->travel_time <= -1 || ch->pcdata->travel_to <= -1 || ch->pcdata->travel_type <= -1)
        continue;

        if (ch->pcdata->travel_type != TRAVEL_CAR && ch->pcdata->travel_type != TRAVEL_BIKE)
        continue;

        if ((IS_FLAG(ch->comm, COMM_SLOW) || safety_bonus(ch) >= 5) && number_percent() % 3 != 0)
        continue;

        char targ1[MSL];
        one_argument_nouncap(event->target, targ1);

        if ((!str_cmp(targ1, "supernaturals") && is_super(ch)) || (!str_cmp(targ1, "naturals") && !is_super(ch)) || (!str_cmp(targ1, "vampires") && is_vampire(ch)) || (!str_cmp(targ1, "werewolves") && is_werewolf(ch)) || (!str_cmp(targ1, "vampire") && is_vampire(ch)) || (!str_cmp(targ1, "werewolf") && is_werewolf(ch)) || (!str_cmp(targ1, "faeborn") && is_faeborn(ch)) || (!str_cmp(targ1, "angelborn") && is_angelborn(ch)) || (!str_cmp(targ1, "demonborn") && is_demonborn(ch)) || (!str_cmp(targ1, "demigods") && is_demigod(ch)) || (part_of_alliance(ch, event->target)) || (part_of_alliance(ch, targ1)) || (!str_cmp(targ1, ch->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(event->target, clan_lookup(ch->faction)->name)) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(event->target, clan_lookup(ch->factiontwo)->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->faction)->name))) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->factiontwo)->name))) || !str_cmp(targ1, "everyone")) {
          act("Your vehicle is sabotaged.", ch, NULL, NULL, TO_CHAR);
          act("$n's vehicle is sabotaged.", ch, NULL, NULL, TO_ROOM);
          have_accident(ch);
        }
      }
    }

    if (event->type == EVENT_AMBUSH || event->typetwo == EVENT_AMBUSH) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;
        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (!in_haven(ch->in_room))
        continue;

        if (ch->recent_moved > -20)
        continue;

        if(ch->pcdata->spectre > 0)
        continue;

        if (IS_SET(ch->in_room->room_flags, ROOM_INDOORS))
        continue;

        if (public_room(ch->in_room) && !nighttime(ch->in_room))
        continue;

        int chance = 1;
        if (public_room(ch->in_room))
        chance = 5;
        else
        chance = 2;

        if (number_percent() % chance != 0)
        continue;

        char targ1[MSL];
        one_argument_nouncap(event->target, targ1);

        if ((!str_cmp(targ1, "supernaturals") && is_super(ch)) || (!str_cmp(targ1, "naturals") && !is_super(ch)) || (!str_cmp(targ1, "vampires") && is_vampire(ch)) || (!str_cmp(targ1, "werewolves") && is_werewolf(ch)) || (!str_cmp(targ1, "vampire") && is_vampire(ch)) || (!str_cmp(targ1, "werewolf") && is_werewolf(ch)) || (!str_cmp(targ1, "faeborn") && is_faeborn(ch)) || (!str_cmp(targ1, "angelborn") && is_angelborn(ch)) || (!str_cmp(targ1, "demonborn") && is_demonborn(ch)) || (!str_cmp(targ1, "demigods") && is_demigod(ch)) || (part_of_alliance(ch, event->target)) || (part_of_alliance(ch, targ1)) || (!str_cmp(targ1, ch->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(event->target, clan_lookup(ch->faction)->name)) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(event->target, clan_lookup(ch->factiontwo)->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->faction)->name))) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->factiontwo)->name))) || !str_cmp(targ1, "everyone")) {
          act("You are attacked!", ch, NULL, NULL, TO_CHAR);
          act("$n is attacked!", ch, NULL, NULL, TO_ROOM);
          if (ch->wounds == 0)
          wound_char_absolute(ch, 1);
          else
          ch->heal_timer += 5000;
          ch->recent_moved = 10;
        }
      }
    }
    if (event->type == EVENT_CONDITION || event->typetwo == EVENT_CONDITION) {
      bool found;
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;
        if (d->connected != CON_PLAYING)
        continue;

        ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (!str_cmp(ch->name, event->author))
        continue;

        char targ1[MSL];
        one_argument_nouncap(event->target, targ1);

        found = FALSE;

        if ((!str_cmp(targ1, "supernaturals") && is_super(ch)) || (!str_cmp(targ1, "naturals") && !is_super(ch)) || (!str_cmp(targ1, "vampires") && is_vampire(ch)) || (!str_cmp(targ1, "werewolves") && is_werewolf(ch)) || (!str_cmp(targ1, "vampire") && is_vampire(ch)) || (!str_cmp(targ1, "werewolf") && is_werewolf(ch)) || (!str_cmp(targ1, "faeborn") && is_faeborn(ch)) || (!str_cmp(targ1, "angelborn") && is_angelborn(ch)) || (!str_cmp(targ1, "demonborn") && is_demonborn(ch)) || (!str_cmp(targ1, "demigods") && is_demigod(ch)) || (!str_cmp(targ1, "everyone")) || (part_of_alliance(ch, event->target)) || (part_of_alliance(ch, targ1)) || (!str_cmp(targ1, ch->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(event->target, clan_lookup(ch->faction)->name)) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(event->target, clan_lookup(ch->factiontwo)->name)) || (ch->faction != 0 && clan_lookup(ch->faction) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->faction)->name))) || (ch->factiontwo != 0 && clan_lookup(ch->factiontwo) != NULL && !str_cmp(nospaces(event->target), nospaces(clan_lookup(ch->factiontwo)->name)))) {

          for (i = 0; i < 25; i++) {
            if (!str_cmp(ch->pcdata->imprint[i], event->imprint) && found == FALSE) {
              found = TRUE;
            }
          }
          if (found == FALSE) {
            for (i = 0; i < 25; i++) {
              if (!str_cmp(ch->pcdata->imprint[i], "") && found == FALSE) {
                auto_imprint(ch, event->imprint, IMPRINT_INFLUENCE);
                found = TRUE;
              }
            }
          }
        }
      }
    }
  }

  void event_end(EVENT_TYPE *event) {
    if (event->type == EVENT_RECRUITMENT) {
      event_recruitment = 0;
    }
    if (event->type == EVENT_TEACHING) {
      event_teaching = 0;
    }
    if (event->type == EVENT_OCCURANCE) {
      event_occurance = 0;
    }
    if (event->type == EVENT_DOMINANCE)
    event_dominance = 0;

    if (event->type == EVENT_AEGIS)
    event_aegis = 0;

    if (event->type == EVENT_CLEANSE)
    event_cleanse = 0;

    if (event->type == EVENT_CATASTROPHE)
    event_catastrophe = 0;
    if (event->type == EVENT_STORM)
    crisis_storm = 0;
    if (event->type == EVENT_FLOOD)
    crisis_flood = 0;
    if (event->type == EVENT_BLACKOUT)
    crisis_blackout = 0;
    if (event->type == EVENT_UNINVITED)
    crisis_uninvited = 0;
    if (event->type == EVENT_HURRICANE)
    crisis_hurricane = 0;
    if (event->type == EVENT_DISRUPTION)
    town_blackout = 0;

    if (event->typetwo == EVENT_RECRUITMENT) {
      event_recruitment = 0;
    }
    if (event->typetwo == EVENT_TEACHING) {
      event_teaching = 0;
    }
    if (event->typetwo == EVENT_OCCURANCE) {
      event_occurance = 0;
    }
    if (event->typetwo == EVENT_DOMINANCE)
    event_dominance = 0;

    if (event->typetwo == EVENT_AEGIS)
    event_aegis = 0;

    if (event->typetwo == EVENT_CLEANSE)
    event_cleanse = 0;

    if (event->typetwo == EVENT_CATASTROPHE)
    event_catastrophe = 0;
    if (event->typetwo == EVENT_STORM)
    crisis_storm = 0;
    if (event->typetwo == EVENT_FLOOD)
    crisis_flood = 0;
    if (event->typetwo == EVENT_BLACKOUT)
    crisis_blackout = 0;
    if (event->typetwo == EVENT_UNINVITED)
    crisis_uninvited = 0;
    if (event->typetwo == EVENT_HURRICANE)
    crisis_hurricane = 0;
    if (event->typetwo == EVENT_DISRUPTION)
    town_blackout = 0;
  }

  void event_update() {
    event_recruitment = 0;
    event_teaching = 0;
    event_occurance = 0;

    event_dominance = 0;
    event_aegis = 0;
    event_cleanse = 0;
    event_catastrophe = 0;

    for (vector<EVENT_TYPE *>::iterator it = EventVect.begin();
    it != EventVect.end(); ++it) {
      if ((*it)->valid == FALSE)
      continue;

      if (current_time > (*it)->deactive_time + (3600 * 24)) {
        (*it)->valid = FALSE;
        continue;
      }
      if ((*it)->type == EVENT_OCCURANCE || (*it)->type == EVENT_OPERATION || (*it)->type == EVENT_RECRUITMENT || (*it)->type == EVENT_TEACHING)
      (*it)->thwart_attempted = 1;
      if ((*it)->typetwo == EVENT_OCCURANCE || (*it)->typetwo == EVENT_OPERATION || (*it)->typetwo == EVENT_RECRUITMENT || (*it)->typetwo == EVENT_TEACHING)
      (*it)->thwart_attempted = 1;

      if (current_time > (*it)->active_time && current_time < (*it)->deactive_time) {
        bool found = FALSE;
        for (vector<NEWS_TYPE *>::iterator inn = NewsVect.begin();
        inn != NewsVect.end(); ++inn) {
          if (!(*inn)->author || (*inn)->author[0] == '\0') {
            continue;
          }
          if ((*inn)->valid == FALSE)
          continue;
          if ((*inn)->timer <= 0)
          continue;
          if (!str_cmp((*inn)->message, (*it)->introduction)) {
            found = TRUE;
            break;
          }
        }
        if (!found)
        event_message(2 * 60, (*it)->introduction);

        event_apply((*it));
      }

      if (current_time > (*it)->deactive_time && current_time < (*it)->deactive_time + 3600)
      event_end((*it));
    }
    ANNIVERSARY_TYPE *ann = get_anniversary_today();
    if(ann != NULL && strlen(ann->messages) > 2) {
      for (DescList::iterator it = descriptor_list.begin();
      it != descriptor_list.end(); ++it) {
        DESCRIPTOR_DATA *d = *it;
        if (d->valid == FALSE)
        continue;
        if (d->connected != CON_PLAYING)
        continue;

        CHAR_DATA *ch = d->character;
        if (ch == NULL)
        continue;

        if (IS_NPC(ch))
        continue;

        if (number_percent() % 17 != 0)
        continue;

        int value = number_range(1, linecount(ann->messages));
        printf_to_char(ch, "%s\n\r", fetch_line(ann->messages, value));

      }
    }

  }

  _DOFUN(do_swapout) {
    save_char_obj(ch, FALSE, FALSE);
    SET_FLAG(ch->act, PLR_GM);
    SET_FLAG(ch->act, PLR_NOSAVE);
    send_to_char("Done.\n\r", ch);
  }
  _DOFUN(do_swapin) {
    save_account(ch->pcdata->account, FALSE);
    char name[MSL];
    sprintf(name, "%s", ch->name);
    DESCRIPTOR_DATA *d = ch->desc;
    free_char(ch);
    load_char_obj(d, name);
    send_to_char("You return to your regular character.\n\r", d->character);
  }

#if defined(__cplusplus)
}
#endif
