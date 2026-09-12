// Completion effects for timed crafting, treatment and research actions.
#include <sys/stat.h>
#include <cmath>
#include "merc.h"
#include "text_format.h"
#include "olc.h"
#include "gsn.h"
#include "recycle.h"
#include "lookup.h"
#include "global.h"
extern "C" {
bool targeted_ritual_vnum(int number);
int ritual_cost(CHAR_DATA *ch, int ritual, CHAR_DATA *victim);
int ritual_buff_power(CHAR_DATA *ch);
int pc_anima_value(CHAR_DATA *ch);
  int chainsaw_bonus(CHAR_DATA *ch) {
    OBJ_DATA *obj;
    obj = get_eqr_char(ch, WEAR_HOLD);
    if (obj != NULL) {
      if (is_name("chainsaw", obj->name))
      return 40;
      else if (is_name("axe", obj->name))
      return 20;
    }
    obj = get_eq_char(ch, WEAR_HOLD_2);
    if (obj != NULL) {
      if (is_name("chainsaw", obj->name))
      return 40;
      else if (is_name("axe", obj->name))
      return 20;
    }
    return 0;
  }
  void conclude_process(CHAR_DATA *ch, int type) {
    if (type == PROCESS_RITUAL && ch->pcdata->process_subtype == RITUAL_DREAMSNARE) {
      ch->pcdata->process = 0;
      ch->pcdata->process_timer = 0;
      send_to_char("Dream snares are disabled.\n\r", ch);
      return;
    }
    OBJ_DATA *obj;
    char buf[MSL];

    ch->pcdata->last_develop_type = 0;
    ch->pcdata->last_develop_time = 0;

    if (type == PROCESS_TRAVEL_PREP) {
      ch->pcdata->travel_prepped = TRUE;
      do_function(ch, &do_travel, ch->pcdata->process_argumentone);
      return;
    }
    if (type == PROCESS_FISH) {
      ch->pcdata->process = 0;
      if (!nearby_water(ch)) {
        send_to_char("You are no longer near water.\n\r", ch);
        return;
      }
      switch (number_percent() % 24) {
      case 1:
        sprintf(buf, "Acadian redfish");
        break;
      case 2:
        sprintf(buf, "Alewife fish");
        break;
      case 3:
        sprintf(buf, "American dab");
        break;
      case 4:
        sprintf(buf, "American eel");
        break;
      case 5:
        sprintf(buf, "Atlantic blue marlin");
        break;
      case 6:
        sprintf(buf, "Atlantic bonito");
        break;
      case 7:
        sprintf(buf, "Atlantic cod");
        break;
      case 8:
        sprintf(buf, "Atlantic halibut");
        break;
      case 9:
        sprintf(buf, "Atlantic herring");
        break;
      case 10:
        sprintf(buf, "Atlantic mackerel");
        break;
      case 11:
        sprintf(buf, "Atlantic menhaden");
        break;
      case 12:
        sprintf(buf, "Black sea bass");
        break;
      case 13:
        sprintf(buf, "Blue shark");
        break;
      case 14:
        sprintf(buf, "Bluefin tuna");
        break;
      case 15:
        sprintf(buf, "Bluefish");
        break;
      case 16:
        sprintf(buf, "Cusk fish");
        break;
      case 17:
        sprintf(buf, "Haddock");
        break;
      case 18:
        sprintf(buf, "Monkfish");
        break;
      case 19:
        sprintf(buf, "Rainbow smelt");
        break;
      case 20:
        sprintf(buf, "Scup");
        break;
      case 21:
        sprintf(buf, "Striped bass");
        break;
      case 22:
        sprintf(buf, "Summer flounder");
        break;
      case 23:
        sprintf(buf, "Tautog");
        break;
      case 0:
      default:
        sprintf(buf, "Yellowfin tuna");
        break;
      }
      std::string tmp;
      obj = create_object(get_obj_index(45250), 0);
      free_string(obj->short_descr);
      obj->short_descr = str_dup(buf);
      free_string(obj->description);
      tmp = haven::format_text("%s %s", a_or_an(buf), buf);
      obj->description = str_dup(tmp.data());
      free_string(obj->name);
      tmp = haven::format_text("fish food %s", buf);
      obj->name = str_dup(tmp.data());
      obj_to_char(obj, ch);
      tmp = haven::format_text("You catch %s.", obj->description);
      act(tmp.data(), ch, NULL, NULL, TO_CHAR);
      tmp = haven::format_text("$n catches %s.", obj->description);
      act(tmp.data(), ch, NULL, NULL, TO_ROOM);
      return;
    }
    if (type == PROCESS_RITUAL) {
      CHAR_DATA *victim = NULL;
      bool online = FALSE;
      int power = 100;
      if (targeted_ritual_vnum(ch->pcdata->process_subtype)) {
        DESCRIPTOR_DATA d;
        struct stat sb;
        Buffer outbuf;
        d.original = NULL;
        if ((victim = get_char_world_pc(ch->pcdata->process_argumentone)) !=
            NULL) // Victim is online.
        online = TRUE;
        else {
          log_string("DESCRIPTOR: Finish Ritual");

          if (!load_char_obj(&d, ch->pcdata->process_argumentone)) {
            send_to_char("You can't find them.\n\r", ch);
            return;
          }

          sprintf(buf, "%s%s", PLAYER_DIR, capitalize(ch->pcdata->process_argumentone));
          stat(buf, &sb);
          victim = d.character;
        }
        if (IS_NPC(victim)) {
          send_to_char("You can't find them.\n\r", ch);
          if (!online)
          free_char(victim);
          return;
        }
        if (str_cmp(ch->name, "Ritualist") && in_world(ch) != in_world(victim) && !higher_power(victim)) {
          send_to_char("You can't find them.\n\r", ch);
          if (!online)
          free_char(victim);
          return;
        }
      }

      int st = ch->pcdata->process_subtype;
      int cost = ritual_cost(ch, ch->pcdata->process_subtype, victim);
      if (st != RITUAL_SHADOWCLOAK && st != RITUAL_CLEANSE && st != RITUAL_SANCTUARY && st != RITUAL_SCRY && st != RITUAL_PROTECT && st != RITUAL_RAISEWARD && st != RITUAL_UNBINDING && st != RITUAL_MINDWARD && st != RITUAL_WAKEBOUND && st != RITUAL_SACRIFICE && st != RITUAL_SHROUDSHIELD && st != RITUAL_AGETHEFT && st != RITUAL_TRACE && st != RITUAL_ENCROACHMENT && (st < RITUAL_FREEZETIME || st > RITUAL_NATURALIZEWEATHER)) {
        villain_mod(ch, 20, "Ritual");
        if (victim != NULL && is_weakness(ch, victim))
        cost /= 5;
      }
      if (victim != NULL && !IS_NPC(victim) && st != RITUAL_SCRY && st != RITUAL_TRACE) {
        free_string(victim->pcdata->last_ritual);
        victim->pcdata->last_ritual = str_dup(ch->name);
      }
      if (ch->pcdata->process_subtype == RITUAL_TRACE) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        printf_to_char(ch, "%s comes into view in your scrying implement.\n\r", victim->pcdata->last_ritual);
        if (str_cmp(victim->pcdata->last_ritual, victim->pcdata->ritual_maintainer) && safe_strlen(victim->pcdata->ritual_maintainer) > 1)
        printf_to_char(ch, "%s comes into view in your scrying implement.\n\r", victim->pcdata->ritual_maintainer);

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SUMMONING) {
        if (!higher_power(victim)) {
          send_to_char("Your spell fails.\n\r", ch);
          return;
        }
        if (!online) {
          send_to_char("Your spell fails.\n\r", ch);
          free_char(victim);
          victim = NULL;
          return;
        }
        if (victim->pcdata->summon_bound < 0) {
          send_to_char("Your spell fails.\n\r", ch);
          return;
        }
        if (victim->in_room == NULL || victim->in_room->vnum <= 300) {
          send_to_char("Your spell fails.\n\r", ch);
          return;
        }
        if (higher_power(victim))
        security_wipeout(victim->name);

        power = ritual_debuff_power(ch, victim);
        char_from_room(victim);
        char_to_room(victim, ch->in_room);
        free_string(victim->pcdata->place);
        victim->pcdata->place = str_dup("binding circle");
        victim->pcdata->summon_bound = power;
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
      }
      if (ch->pcdata->process_subtype == RITUAL_IMPRINT) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        auto_imprint_timed(victim, ch->pcdata->process_argumenttwo, IMPRINT_INFLUENCE, power * 3);
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_IMPRINTBODY) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        auto_imprint_timed(victim, ch->pcdata->process_argumenttwo, IMPRINT_BODYCOMPULSION, power * 3);
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }

      if (ch->pcdata->process_subtype == RITUAL_SEXCHANGE) {
        if (ch == victim)
        cost /= 2;
        if (is_faeborn(victim))
        cost /= 2;
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        if (victim->pcdata->sexchange_time <= 0) {
          if (victim->pcdata->penis > 0) {
            victim->pcdata->truepenis = victim->pcdata->penis;
            victim->pcdata->penis = 0;
          }
          else {
            victim->pcdata->truepenis = victim->pcdata->penis;
            victim->pcdata->penis = 70;
          }
          if (victim->pcdata->bust > 0) {
            victim->pcdata->truebreasts = victim->pcdata->bust;
            victim->pcdata->bust = 0;
          }
          else {
            victim->pcdata->truebreasts = victim->pcdata->bust;
            victim->pcdata->bust = number_range(3, 8);
          }
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            victim->pcdata->sexchange_time = 2;
          }
          else
          victim->pcdata->sexchange_time = power * 3;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
        else
        send_to_char("Your body tingles.\n\r", victim);
      }
      if (ch->pcdata->process_subtype == RITUAL_PREDATE) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        victim->pcdata->ritual_prey_timer = power*3;
        free_string(victim->pcdata->ritual_prey_target);
        victim->pcdata->ritual_prey_target = str_dup(ch->name);
        if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
          victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
          free_string(victim->pcdata->ritual_maintainer);
          victim->pcdata->ritual_maintainer = str_dup(ch->name);
          free_string(ch->pcdata->maintained_target);
          ch->pcdata->maintained_target = str_dup(victim->name);
          cost /= 2;
          victim->pcdata->ritual_prey_timer = power*2;
          free_string(victim->pcdata->ritual_prey_target);
          victim->pcdata->ritual_prey_target = str_dup(ch->name);
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_DREAMBELIEF) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
          victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
          free_string(victim->pcdata->ritual_maintainer);
          victim->pcdata->ritual_maintainer = str_dup(ch->name);
          free_string(ch->pcdata->maintained_target);
          ch->pcdata->maintained_target = str_dup(victim->name);
          cost /= 2;
          victim->pcdata->dream_identity_timer = 2;
        }
        else
        victim->pcdata->dream_identity_timer = power * 3;
        free_string(victim->pcdata->identity_world);
        victim->pcdata->identity_world = str_dup(ch->pcdata->ritual_dreamworld);
        free_string(victim->pcdata->dream_identity);
        victim->pcdata->dream_identity = str_dup("");
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_DREAMIDENTITY) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
          victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
          free_string(victim->pcdata->ritual_maintainer);
          victim->pcdata->ritual_maintainer = str_dup(ch->name);
          free_string(ch->pcdata->maintained_target);
          ch->pcdata->maintained_target = str_dup(victim->name);
          cost /= 2;
          victim->pcdata->dream_identity_timer = 2;
        }
        else
        victim->pcdata->dream_identity_timer = power * 3;
        free_string(victim->pcdata->identity_world);
        victim->pcdata->identity_world = str_dup(ch->pcdata->ritual_dreamworld);
        free_string(victim->pcdata->dream_identity);
        victim->pcdata->dream_identity = str_dup(ch->pcdata->process_argumenttwo);
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SACRIFICE) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        if (ch->pcdata->apparant_age < 5)
        give_lifeforce(ch, 1500 * power / 100, "sacrifice ritual");
        ch->pcdata->deaged -= 720 * power / 100;
        return;
      }
      if (ch->pcdata->process_subtype == RITUAL_AGETHEFT) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (victim->played / 3600 < 100) {
          send_to_char("They're too new to this location, your spell fails to latch on.\n\r", ch);
          return;
        }
        int diff = get_age(ch) - get_age(victim);
        diff *= 4;
        if (ch->in_room == victim->in_room)
        diff *= 3;
        if (get_tier(victim) == 1)
        diff /= 2;
        if (diff > 0) {
          ch->pcdata->deaged += diff;
          victim->pcdata->deaged -= diff;
        }
        sprintf(buf, "AGETHEFT: %s steals %d from %s.", ch->name, diff, victim->name);
        log_string(buf);
        if (ch->in_room != victim->in_room && number_percent() % 3 == 0) {
          sprintf(
          buf, "You have a horrible dream about a figure looking like %s pinning you down and sucking the air from your body in a stream.\n\r", get_intro(ch));
          free_string(victim->pcdata->nightmare);
          victim->pcdata->nightmare = str_dup(buf);
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SLEEPWALK) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        bool walker = FALSE;
        if (is_dreaming(victim) && !is_gm(victim) && victim->in_room != NULL && !IS_FLAG(victim->comm, COMM_AFK) && victim->desc != NULL && !locked_room(victim->in_room, victim) && !IS_FLAG(victim->act, PLR_BOUND) && !IS_FLAG(victim->act, PLR_BOUNDFEET) && in_haven(victim->in_room)) {
          walker = TRUE;
        }
        else if (!is_gm(victim) && victim->in_room != NULL && !IS_FLAG(victim->comm, COMM_AFK) && !is_helpless(victim) && !in_fight(victim) && !IS_FLAG(victim->act, PLR_DEAD) && victim->desc != NULL && !locked_room(victim->in_room, victim) && in_haven(victim->in_room)) {
          if ((victim->pcdata->time_since_action > 30 * 100 / power && pc_pop(victim->in_room) < 2) || victim->pcdata->time_since_action > 90 * 100 / power) {
            walker = TRUE;
          }
        }
        if (walker == TRUE) {
          int mindist = 1000;
          int minpointer = 0;
          for (int i = 0; i < MAX_TAXIS; i++) {
            if (get_dist(get_roomx(victim->in_room), get_roomy(victim->in_room), get_roomx(get_room_index(taxi_table[i].vnum)), get_roomy(get_room_index(taxi_table[i].vnum))) < mindist)
            ;
            {
              minpointer = i;
              mindist =
              get_dist(get_roomx(victim->in_room), get_roomy(victim->in_room), get_roomx(get_room_index(taxi_table[i].vnum)), get_roomy(get_room_index(taxi_table[i].vnum)));
            }
          }

          int f = taxi_table[minpointer].vnum;
          int xmod = number_range(-2, 2);
          int ymod = number_range(-2, 2);
          ymod *= 1000;
          ROOM_INDEX_DATA *to_room;
          if ((to_room = get_room_index(f + xmod + ymod)) != NULL) {
            act("$n wanders off in a daze.", victim, NULL, NULL, TO_ROOM);
            dact("$n wanders off in a daze.", victim, NULL, NULL, DISTANCE_MEDIUM);
            char_from_room(victim);
            char_to_room(victim, to_room);
            act("$n wanders in in a daze.", victim, NULL, NULL, TO_ROOM);
            dact("$n wanders in in a daze.", victim, NULL, NULL, DISTANCE_MEDIUM);
          }
          else {
            to_room = get_room_index(f);
            act("$n wanders off in a daze.", victim, NULL, NULL, TO_ROOM);
            dact("$n wanders off in a daze.", victim, NULL, NULL, DISTANCE_MEDIUM);
            char_from_room(victim);
            char_to_room(victim, to_room);
            act("$n wanders in in a daze.", victim, NULL, NULL, TO_ROOM);
            dact("$n wanders in in a daze.", victim, NULL, NULL, DISTANCE_MEDIUM);
          }

          free_string(victim->pcdata->title);
          victim->pcdata->title = str_dup(" is wandering in a daze");
        }
        else {
          send_to_char("The spell fails.\n\r", ch);
          return;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SILENCE) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL && !is_base(in_prop(victim)) && in_prop(victim)->blackout == 0) {
          in_prop(victim)->blackout = 18 * power / 100;

          CHAR_DATA *to;

          for (DescList::iterator it = descriptor_list.begin();
          it != descriptor_list.end(); ++it) {
            DESCRIPTOR_DATA *d = *it;

            if (d != NULL && d->character != NULL && d->connected == CON_PLAYING) {
              to = d->character;
              if (to == NULL)
              continue;
              if (IS_NPC(to))
              continue;
              if (in_prop(to) == in_prop(victim))
              send_to_char("`DThe power goes out.`x\n\r", to);
            }
          }
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_DECAY) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          in_prop(victim)->decay += power;
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SHROUDSHIELD) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          in_prop(victim)->shroudshield =
          UMIN(250, in_prop(victim)->shroudshield + power);
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SHIELDBREAK) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          in_prop(victim)->shroudshield =
          UMAX(0, in_prop(victim)->shroudshield - power);
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_NATURALIZETIME) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          in_prop(victim)->timefrozen = 0;
          in_prop(victim)->timeshift = 0;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_NATURALIZEWEATHER) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          in_prop(victim)->weather = 0;
          in_prop(victim)->tempfrozen = 0;
          in_prop(victim)->tempshift = 0;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_LOCALIZEDWEATHER) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          if (!str_cmp(ch->pcdata->process_argumenttwo, "clear"))
          in_prop(victim)->weather = PROPWEATHER_CLEAR;
          else if (!str_cmp(ch->pcdata->process_argumenttwo, "cloudy"))
          in_prop(victim)->weather = PROPWEATHER_CLOUDY;
          else if (!str_cmp(ch->pcdata->process_argumenttwo, "rain"))
          in_prop(victim)->weather = PROPWEATHER_RAIN;
          else if (!str_cmp(ch->pcdata->process_argumenttwo, "snow"))
          in_prop(victim)->weather = PROPWEATHER_SNOW;
          else if (!str_cmp(ch->pcdata->process_argumenttwo, "hail"))
          in_prop(victim)->weather = PROPWEATHER_HAIL;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_TEMPERATURESHIFT) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          int hour = atoi(ch->pcdata->process_argumenttwo);
          if (hour < 100 && hour > -100)
          in_prop(victim)->tempshift = hour;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_FREEZETEMPERATURE) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          int hour = atoi(ch->pcdata->process_argumenttwo);
          if (hour > -50 && hour < 150)
          in_prop(victim)->tempfrozen = hour;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_TIMESHIFT) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          int hour = atoi(ch->pcdata->process_argumenttwo);
          if (hour < 24 && hour > -24)
          in_prop(victim)->timeshift = hour;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_FREEZETIME) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          int hour = atoi(ch->pcdata->process_argumenttwo);
          if (hour < 24 && hour > 0)
          in_prop(victim)->timefrozen = hour;
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }

      if (ch->pcdata->process_subtype == RITUAL_ENCROACHMENT) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        PROP_TYPE *prop = in_prop(victim);
        if(prop == NULL)
        {
          send_to_char("They are not in a property.\n\r", ch);
          if (!online) {
            free_char(victim);
            victim = NULL;
          }

          return;
        }
        if(prop->last_encroach > current_time - (3600*24*5))
        {
          send_to_char("A property can only be targeted by this ritual once every five days.\n\r", ch);
          if (!online) {
            free_char(victim);
            victim = NULL;
          }

          return;
        }
        prop->last_encroach = current_time;
        encroach_property(prop);
        save_char_obj(victim, FALSE, FALSE);
        save_properties(FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }

      if (ch->pcdata->process_subtype == RITUAL_CLOAKING) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL && !is_base(in_prop(victim)) && in_prop(victim)->blackout == 0) {
          in_prop(victim)->cloaked += power;
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SHADOWCLOAK) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        if (!IS_FLAG(victim->comm, COMM_SHADOWCLOAK))
        SET_FLAG(victim->comm, COMM_SHADOWCLOAK);

        save_char_obj(victim, FALSE, FALSE);
        if (!online)
        free_char(victim);
      }
      if (ch->pcdata->process_subtype == RITUAL_CLEANSE) {
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        OBJ_DATA *obj;
        OBJ_DATA *obj_next;

        for (obj = ch->carrying; obj != NULL; obj = obj_next) {
          obj_next = obj->next_content;
          if (IS_SET(obj->extra_flags, ITEM_WARDROBE))
          continue;
          if (IS_SET(obj->extra_flags, ITEM_CURSED))
          REMOVE_BIT(obj->extra_flags, ITEM_CURSED);
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_DREAM) {
        FANTASY_TYPE *fant = NULL;
        for (vector<FANTASY_TYPE *>::iterator it = FantasyVect.begin();
        it != FantasyVect.end(); ++it) {
          if ((*it)->valid == FALSE || (*it)->active == FALSE) {
            continue;
          }
          if (!str_cmp((*it)->name, ch->pcdata->ritual_dreamworld)) {
            fant = (*it);
          }
        }
        if (fant == NULL)
        return;
        if (guestmonster(victim) || higher_power(victim)) {
          return;
        }

        char buf[MSL];
        sprintf(buf, "suspended%s", victim->name);
        bool suspended = FALSE;
        for (int i = 0; i < 200; i++) {
          if (!str_cmp(buf, fant->participants[i]))
          suspended = TRUE;
        }
        if (suspended == TRUE) {
          for (int i = 0; i < 200; i++) {
            if (!str_cmp(victim->name, fant->participants[i])) {
              free_string(fant->participants[i]);
              fant->participants[i] = str_dup("");
            }
          }
        }
        else {
          for (int i = 0; i < 200; i++) {
            if (!str_cmp(victim->name, fant->participants[i])) {
              free_string(fant->participants[i]);
              fant->participants[i] = str_dup(buf);
            }
          }
        }
        if (IS_FLAG(victim->act, PLR_SHROUD) && victim->pcdata->spectre == 0)
        enter_dreamworld(victim, fant);
        else if (victim->pcdata->spectre == 0) {
          to_spectre(victim, FALSE);
          enter_dreamworld(victim, fant);
        }
        else
        enter_dreamworld(victim, fant);

        to_spectre(ch, FALSE);
        enter_dreamworld(ch, fant);
        int point = -1;
        for (int i = 0; i < 200; i++) {
          if (!str_cmp(victim->name, fant->participants[i]))
          point = i;
        }
        gain_dexp(victim, 10);
        victim->pcdata->dream_room = ch->pcdata->dream_room;
        ch->pcdata->tempdreamgodworld = fantasy_number(fant);
        ch->pcdata->tempdreamgodchar = point;
        villain_mod(ch, 10, "Dream invasion");
        if (!online)
        cost /= 2;
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        send_to_char("You invade their dreams, use 'wake' to leave the dream early.\n\r", ch);
        send_to_char("You fall asleep.\n\r", victim);
        act("$n falls asleep.", ch, NULL, NULL, TO_ROOM);
        act("$n falls asleep.", victim, NULL, NULL, TO_ROOM);
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_DREAMSNARE) {
        FANTASY_TYPE *fant = NULL;
        for (vector<FANTASY_TYPE *>::iterator it = FantasyVect.begin();
        it != FantasyVect.end(); ++it) {
          if ((*it)->valid == FALSE || (*it)->active == FALSE) {
            continue;
          }
          if (!str_cmp((*it)->name, ch->pcdata->ritual_dreamworld)) {
            fant = (*it);
          }
        }
        if (guestmonster(victim) || higher_power(victim)) {
          return;
        }
        if (fant == NULL)
        return;
        char buf[MSL];
        sprintf(buf, "suspended%s", victim->name);
        bool suspended = FALSE;
        for (int i = 0; i < 200; i++) {
          if (!str_cmp(buf, fant->participants[i]))
          suspended = TRUE;
        }
        if (suspended == TRUE) {
          for (int i = 0; i < 200; i++) {
            if (!str_cmp(victim->name, fant->participants[i])) {
              free_string(fant->participants[i]);
              fant->participants[i] = str_dup("");
            }
          }
        }
        else {
          for (int i = 0; i < 200; i++) {
            if (!str_cmp(victim->name, fant->participants[i])) {
              free_string(fant->participants[i]);
              fant->participants[i] = str_dup(buf);
            }
          }
        }
        if (IS_FLAG(victim->act, PLR_SHROUD) && victim->pcdata->spectre == 0)
        enter_dreamworld(victim, fant);
        else if (victim->pcdata->spectre == 0) {
          to_spectre(victim, FALSE);
          enter_dreamworld(victim, fant);
        }
        else
        enter_dreamworld(victim, fant);

        to_spectre(ch, FALSE);
        enter_dreamworld(ch, fant);
        int point = -1;
        for (int i = 0; i < 200; i++) {
          if (!str_cmp(victim->name, fant->participants[i]))
          point = i;
        }
        victim->pcdata->dream_room = ch->pcdata->dream_room;
        ch->pcdata->tempdreamgodworld = fantasy_number(fant);
        ch->pcdata->tempdreamgodchar = point;
        villain_mod(ch, 10, "Dream invasion");
        if (!online)
        cost /= 2;
        gain_dexp(victim, 10);
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        send_to_char("You invade their dreams, use 'wake' to leave the dream early.\n\r", ch);
        send_to_char("You fall asleep.\n\r", victim);
        act("$n falls asleep.", ch, NULL, NULL, TO_ROOM);
        act("$n falls asleep.", victim, NULL, NULL, TO_ROOM);
        if (!IS_FLAG(victim->comm, COMM_DREAMSNARED))
        SET_FLAG(victim->comm, COMM_DREAMSNARED);
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SANCTUARY) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        AFFECT_DATA af;
        af.where = TO_AFFECTS;
        af.type = 0;
        af.level = 10;
        af.duration = 12 * 60 * 24 * power / 100;
        af.location = APPLY_NONE;
        af.modifier = 0;
        af.caster = NULL;
        af.weave = FALSE;
        af.bitvector = AFF_UNDERSTANDING;
        affect_to_char(victim, &af);

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SCRY) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_world(ch) != get_world(victim) || silenced(victim) || is_blind(victim) || (is_dark(victim->in_room) && !can_see_dark(victim)))
        printf_to_char(ch, "\nThrough %s's eyes you see darkness.\n\r", PERS(victim, ch));
        else {
          printf_to_char(ch, "\nThrough %s's eyes you see:\n\r", PERS(victim, ch));
          ROOM_INDEX_DATA *orig_room = ch->in_room;
          char_from_room(ch);
          char_to_room(ch, victim->in_room);
          do_function(ch, &do_look, "");
          char_from_room(ch);
          char_to_room(ch, orig_room);
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_MUTE) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_MUTE;
          affect_to_char(victim, &af);
        }

        send_to_char("You suddenly find yourself unable to speak.\n\r", victim);

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_SHADOWALK) {
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        ch->pcdata->shadow_walk_room = ch->in_room->vnum;
        ch->pcdata->shadow_walk_cooldown = 0;
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_DREADWATCHER) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_SUFFER;
          affect_to_char(victim, &af);
        }

        send_to_char("You start finding the prospect of others pain more appealing.\n\r", victim);

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_ILLNESS) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_ILLNESS;
          affect_to_char(victim, &af);
        }

        send_to_char("You start to feel unwell.\n\r", victim);

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }

      if (ch->pcdata->process_subtype == RITUAL_ARTHRITIS) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_ARTHRITIS;
          affect_to_char(victim, &af);
        }

        send_to_char("Your joints start to ache.\n\r", victim);

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_PURIFY) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        free_string(victim->pcdata->last_sexed[0]);
        victim->pcdata->last_sexed[0] = str_dup("");
        free_string(victim->pcdata->last_sexed[1]);
        victim->pcdata->last_sexed[1] = str_dup("");
        free_string(victim->pcdata->last_sexed[2]);
        victim->pcdata->last_sexed[2] = str_dup("");

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_TECHHEX) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_NOTECH;
          affect_to_char(victim, &af);
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_CORRUPT) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0 && !mindwarded(victim)) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_TRIGGERED;
          affect_to_char(victim, &af);
        }
        do_function(victim, &do_imprint, "");
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_LUNACY) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0 && !mindwarded(victim)) {
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            victim->pcdata->lunacy_curse = 2;
          }
          else
          victim->pcdata->lunacy_curse = 120 * power / 100;
        }
        do_function(victim, &do_imprint, "");
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_DEAFEN) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_DEAF;
          affect_to_char(victim, &af);
        }

        send_to_char("All sounds dim as you stop being able to hear.\n\r", victim);
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_LURE) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_LURED;
          affect_to_char(victim, &af);
          victim->pcdata->lured_room = ch->in_room->vnum;
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_MADNESS) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else {
            if (get_skill(victim, SKILL_SPLITMIND) > 0)
            af.duration = 12 * 60 * 3 * power / 50;
            else
            af.duration = 12 * 60 * 3 * power / 100;
          }
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_MAD;
          affect_to_char(victim, &af);
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_PERSECUTION) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 3 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_PERSECUTED;
          affect_to_char(victim, &af);
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_ENFEEBLE) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
            victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
            free_string(victim->pcdata->ritual_maintainer);
            victim->pcdata->ritual_maintainer = str_dup(ch->name);
            free_string(ch->pcdata->maintained_target);
            ch->pcdata->maintained_target = str_dup(victim->name);
            cost /= 2;
            af.duration = 12 * 20;
          }
          else
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_WEAKEN;
          affect_to_char(victim, &af);
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_HAUNT) {
        power = ritual_debuff_power(ch, victim);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        free_string(victim->pcdata->haunter);
        victim->pcdata->haunter = str_dup(ch->name);
        if (!str_cmp(ch->pcdata->maintained_target, "casting")) {
          victim->pcdata->maintained_ritual = ch->pcdata->process_subtype;
          free_string(victim->pcdata->ritual_maintainer);
          victim->pcdata->ritual_maintainer = str_dup(ch->name);
          free_string(ch->pcdata->maintained_target);
          ch->pcdata->maintained_target = str_dup(victim->name);
          cost /= 2;
          victim->pcdata->haunt_timer = 2;
        }
        else
        victim->pcdata->haunt_timer = 12 * 60 * 3 * power / 100;
        ch->pcdata->watching = 600;
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
        else
        send_to_char("You feel watched.\n\r", victim);
      }
      if (ch->pcdata->process_subtype == RITUAL_PROTECT) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_PROTECT;
          affect_to_char(victim, &af);
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_RAISEWARD) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL && !is_base(in_prop(victim)) && in_prop(victim)->blackout == 0) {
          in_prop(victim)->warded += power;
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_LOWERWARD) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (in_prop(victim) != NULL) {
          in_prop(victim)->warded -= power;
          if (in_prop(victim)->warded < 75)
          send_to_char("The wards break.\n\r", ch);

          CHAR_DATA *to;
          for (DescList::iterator it = descriptor_list.begin();
          it != descriptor_list.end(); ++it) {
            DESCRIPTOR_DATA *d = *it;
            if (d != NULL && d->character != NULL && d->connected == CON_PLAYING) {
              to = d->character;
              if (to == NULL)
              continue;
              if (IS_NPC(to))
              continue;
              if (in_prop(to) == in_prop(victim))
              send_to_char("`DThe lights flicker.`x\n\r", to);
            }
          }
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_MIST) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);
        time_info.mist_timer += 10 * power / 100;
      }
      if (ch->pcdata->process_subtype == RITUAL_BANISH) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        CHAR_DATA *to;
        for (DescList::iterator it = descriptor_list.begin();
        it != descriptor_list.end(); ++it) {
          DESCRIPTOR_DATA *d = *it;

          if (d != NULL && d->character != NULL && d->connected == CON_PLAYING) {
            to = d->character;

            if (IS_NPC(to))
            continue;
            if (to == NULL)
            continue;
            if (to->in_room == NULL)
            continue;
            if (to->in_room != victim->in_room)
            continue;
            if(higher_power(to))
            {
              to->pcdata->wander_time = 180;
              to->possessing = NULL;
              send_domain_home(to);
              cost = cost/3;
            }
            else if (IS_FLAG(to->act, PLR_GHOSTWALKING)) {
              act("You feel the earth heave upward to swallow you.\n\r", ch, NULL, to, TO_VICT);
              char_from_room(to);
              char_to_room(to, get_room_index(to->pcdata->ghost_room));
              to->pcdata->ghost_wound = 60;
              REMOVE_FLAG(to->act, PLR_GHOSTWALKING);
            }
            else if (is_ghost(to)) {
              to->possessing = NULL;
              to->pcdata->timebanished = current_time + (3600 * 24 * 30);
              //                          REMOVE_FLAG( to->act, PLR_GHOST );
              char_from_room(to);
              char_to_room(to, graveyard_room());
              //                          to->pcdata->ghost_banishment=current_time;
              act("You feel the earth heave upward to swallow you.\n\r", ch, NULL, to, TO_VICT);
            }
          }
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_BINDING) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        CHAR_DATA *to;
        for (DescList::iterator it = descriptor_list.begin();
        it != descriptor_list.end(); ++it) {
          DESCRIPTOR_DATA *d = *it;

          if (d != NULL && d->character != NULL && d->connected == CON_PLAYING) {
            to = d->character;

            if (IS_NPC(to))
            continue;
            if (to == NULL)
            continue;
            if (to->in_room == NULL)
            continue;
            if (to->in_room != victim->in_room)
            continue;

            if(higher_power(to))
            {
              to->pcdata->wander_time = 120;
              cost = cost /3;
              to->possessing = NULL;
              send_domain_home(to);
            }
            if (is_ghost(to) && !higher_power(to)) {
              if (!IS_FLAG(to->act, PLR_GHOSTBOUND)) {
                SET_FLAG(to->act, PLR_GHOSTBOUND);
              }
              to->possessing = NULL;
              act("You feel suddenly stuck in this area.\n\r", ch, NULL, to, TO_VICT);
            }
          }
        }
        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_UNBINDING) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        CHAR_DATA *to;
        for (DescList::iterator it = descriptor_list.begin();
        it != descriptor_list.end(); ++it) {
          DESCRIPTOR_DATA *d = *it;

          if (d != NULL && d->character != NULL && d->connected == CON_PLAYING) {
            to = d->character;

            if (IS_NPC(to))
            continue;
            if (to == NULL)
            continue;
            if (to->in_room == NULL)
            continue;
            if (to->in_room != ch->in_room)
            continue;

            if (is_ghost(to)) {
              if (IS_FLAG(to->act, PLR_GHOSTBOUND)) {
                REMOVE_FLAG(to->act, PLR_GHOSTBOUND);
              }
              act("You feel released.\n\r", ch, NULL, to, TO_VICT);
            }
          }
        }
      }
      if (ch->pcdata->process_subtype == RITUAL_WAKEBOUND) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_WAKEBOUND;
          affect_to_char(victim, &af);
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }

      if (ch->pcdata->process_subtype == RITUAL_MINDWARD) {
        power = ritual_buff_power(ch);
        act("You conclude your ritual.", ch, NULL, NULL, TO_CHAR);
        act("$n finishes $s ritual.", ch, NULL, NULL, TO_ROOM);

        if (get_skill(victim, SKILL_RITUALPROOF) <= 0) {
          AFFECT_DATA af;
          af.where = TO_AFFECTS;
          af.type = 0;
          af.level = 10;
          af.duration = 12 * 60 * 6 * power / 100;
          af.location = APPLY_NONE;
          af.modifier = 0;
          af.caster = NULL;
          af.weave = FALSE;
          af.bitvector = AFF_MINDWARD;
          affect_to_char(victim, &af);
        }

        save_char_obj(victim, FALSE, FALSE);
        if (!online) {
          free_char(victim);
          victim = NULL;
        }
      }

      if (get_hour(ch->in_room) == 3) {
        if (prop_from_room(ch->in_room) == NULL || prop_from_room(ch->in_room)->timefrozen == 0)
        cost = cost * 2 / 3;
      }
      use_lifeforce(ch, cost, "Ritual.");
      if (base_lifeforce(ch) < 6000 && number_percent() % 3 == 0) {
        free_string(ch->pcdata->deathcause);
        ch->pcdata->deathcause = str_dup("a stroke.");
        act("$n slumps sideways to the ground.", ch, NULL, NULL, TO_ROOM);
        real_kill(ch, ch);
      }
      else if (base_lifeforce(ch) < 7500) {
        act("$n slumps sideways to the ground.", ch, NULL, NULL, TO_ROOM);
        act("You pass out.", ch, NULL, NULL, TO_CHAR);
        ch->pcdata->coma = current_time + (3600 * number_range(1, 5));
        ch->pcdata->sleeping = 10;
      }
      return;
    }

    if (type == PROCESS_DRAINPC) {
      if (ch->pcdata->process_target == NULL)
      return;
      if (!harvesting_room(ch->in_room))
      return;

      int val = pc_anima_value(ch->pcdata->process_target);
      if (val <= 0 || base_lifeforce(ch->pcdata->process_target) < 8200) {
        send_to_char("They're too weak to give anything worthwhile.\n\r", ch);
        return;
      }

      val /= 3;
      int amount = val * get_tier(ch->pcdata->process_target) *
      get_tier(ch->pcdata->process_target) / 5;
      // 1000 * tier. Tier 1 is val/10
      amount = amount * (5 + get_skill(ch, SKILL_ALCHEMY)) / 5;
      //	amount /= 2;

      obj = create_object(get_obj_index(36), 0);
      obj->level = amount;
      obj->value[0] = ch->pcdata->process_target->faction;
      obj_to_char(obj, ch);
      AFFECT_DATA af;
      af.where = TO_AFFECTS;
      af.type = 0;
      af.level = 10;
      if (ch->pcdata->process_target->faction == ch->faction)
      af.duration = 12 * 60 * 30;
      else
      af.duration = 12 * 60;
      af.location = APPLY_NONE;
      af.modifier = 0;
      af.caster = NULL;
      af.weave = FALSE;
      af.bitvector = AFF_DRAINED;
      affect_to_char(ch->pcdata->process_target, &af);
      take_lifeforce(ch->pcdata->process_target, val, "harvesting.");
      cortex_record_harvest(ch, val);

      act("You successfully drain $N and store the gathered energy in a small metal cylinder.", ch, NULL, ch->pcdata->process_target, TO_CHAR);
      act("$n finishes draining you and stores what $e gathered in a small metal cylinder.", ch, NULL, ch->pcdata->process_target, TO_VICT);
      act("$n finishes draining $N and stores the gathered material in a small metal cylinder.", ch, NULL, ch->pcdata->process_target, TO_NOTVICT);
      wound_char_absolute(ch->pcdata->process_target, 1);
    }
    if (type == PROCESS_EXORCISE) {
      if (ch->pcdata->process_target == NULL)
      return;

      act("You complete your exorcism.", ch, NULL, NULL, TO_CHAR);
      act("$n completes $s exorcism.", ch, NULL, NULL, TO_ROOM);

      if (IS_FLAG(ch->pcdata->process_target->act, PLR_SINSPIRIT)) {
        if (ch->pcdata->process_target->pcdata->spirit_type ==
            SPIRIT_MALEFICARUM) {
          act("$N's body twists and convulses before $E suddenly vomits black smoke.", ch->pcdata->process_target, NULL, NULL, TO_ROOM);
        }
        else {
          act("$N's body twists and convulses before $E suddenly vomits white smoke.", ch->pcdata->process_target, NULL, NULL, TO_ROOM);
        }
        real_quit(ch->pcdata->process_target);
        ch->pcdata->process_target = NULL;
      }
      else {
        act("Nothing seems to happen.", ch, NULL, NULL, TO_CHAR);
      }
      return;
    }
    if (type == PROCESS_DRAINABOM) {
    }
    if (type == PROCESS_SEARCH) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were searching originally.\n\r", ch);
        return;
      }
      send_to_char("You finish your search.\n\r", ch);
      EXTRA_DESCR_DATA *ed;
      for (ed = ch->in_room->extra_descr; ed; ed = ed->next) {
        if (is_name("!hidden", ed->keyword))
        break;
      }
      if (ed) {
        printf_to_char(ch, "%s\n\r", ed->description);
      }
      ed = NULL;
      for (ed = ch->in_room->extra_descr; ed; ed = ed->next) {
        if (is_name("!srhidden", ed->keyword))
        break;
      }
      if (ed) {
        printf_to_char(ch, "%s\n\r", ed->description);
      }
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end(); ++it) {
        if (!IS_NPC((*it)) && IS_FLAG((*it)->act, PLR_HIDE)) {
          REMOVE_FLAG((*it)->act, PLR_HIDE);
          act("You reveal $N.", ch, NULL, (*it), TO_CHAR);
          act("$n reveals you.", ch, NULL, (*it), TO_VICT);
          act("$n reveals $N.", ch, NULL, (*it), TO_NOTVICT);
        }
      }
      return;
    }

    if (type == PROCESS_REPAIR) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were repairing originally.\n\r", ch);
        return;
      }
      ch->in_room->encroachment = 0;
      for (int dir = 0; dir < 10; dir++) {
        if (ch->in_room->exit[dir] != NULL) {
          ch->in_room->exit[dir]->doorbroken = 0;
          if (ch->in_room->exit[dir]->wall > 0)
          ch->in_room->exit[dir]->wallcondition = 0;

          if (ch->in_room->exit[dir]->u1.to_room != NULL && ch->in_room->exit[dir]->u1.to_room->exit[rev_dir[dir]] != NULL) {
            ch->in_room->exit[dir]->u1.to_room->exit[rev_dir[dir]]->doorbroken =
            0;
            if (ch->in_room->exit[dir]->u1.to_room->exit[rev_dir[dir]]->wall > 0)
            ch->in_room->exit[dir]
            ->u1.to_room->exit[rev_dir[dir]]
            ->wallcondition = 0;
          }
        }
      }
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      act("You finish your repairs.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes $s repairs.", ch, NULL, NULL, TO_ROOM);
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          fch->pcdata->process = 0;
          fch->pcdata->process_timer = 0;
          fch->pcdata->last_develop_type = 0;
          fch->pcdata->last_develop_time = 0;
        }
      }
      return;
    }
    if (type == PROCESS_DEEPDIG) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were digging in originally.\n\r", ch);
        return;
      }
      ch->in_room->sector_type = SECT_WATER;
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      act("You finish digging your pit and fill it with deep water.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes digging $s pit and fills it with deep water.", ch, NULL, NULL, TO_ROOM);
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          fch->pcdata->process = 0;
          fch->pcdata->process_timer = 0;
          fch->pcdata->last_develop_type = 0;
          fch->pcdata->last_develop_time = 0;
        }
      }

      return;
    }
    if (type == PROCESS_SHALLOWDIG) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were digging in originally.\n\r", ch);
        return;
      }
      ch->in_room->sector_type = SECT_SHALLOW;
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      act("You finish digging your pit and fill it with shallow water.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes digging $s pit and fills it with shallow water.", ch, NULL, NULL, TO_ROOM);
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          fch->pcdata->process = 0;
          fch->pcdata->process_timer = 0;
          fch->pcdata->last_develop_type = 0;
          fch->pcdata->last_develop_time = 0;
        }
      }

      return;
    }
    if (type == PROCESS_SHRINE) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were building in originally.\n\r", ch);
        return;
      }
      DOMAIN_TYPE *dom = domain_by_name(ch->pcdata->process_argumentone);
      if (dom == NULL) {
        send_to_char("No such domain.\n\r", ch);
        return;
      }
      PROP_TYPE *prop = prop_from_room(ch->in_room);
      if (prop == NULL) {
        send_to_char("You aren't in a property.\n\r", ch);
        return;
      }
      if(!has_nonconsume(ch, ITEM_BLOOD))
      {
        send_to_char("You don't have any blood.\n\r", ch);
        return;
      }
      ch->pcdata->account->lastshrine = current_time + 3600 * 24 * 7;

      for (int i = 0; i < 250; i++) {
        if (dom->smallshrines[i] == 0) {
          OBJ_DATA *obj;
          OBJ_DATA *obj_next;

          for (obj = ch->carrying; obj != NULL; obj = obj_next) {
            obj_next = obj->next_content;

            if (IS_SET(obj->extra_flags, ITEM_WARDROBE))
            continue;

            if (obj->pIndexData->vnum == ITEM_BLOOD) {
              if(obj->level > i)
              {
                dom->smallshrines[i] = ch->in_room->vnum;
                act("You finish sanctifying the area.", ch, NULL, NULL, TO_CHAR);
                act("$n finishes sanctifying the area.", ch, NULL, NULL, TO_ROOM);
                extract_obj(obj);
                return;
              }
              else
              {
                act("Your attempt to santify the area fails.", ch, NULL, NULL, TO_CHAR);
                act("$n finishes attempting to sanctify the area.", ch, NULL, NULL, TO_ROOM);
                extract_obj(obj);
                return;
              }
            }
          }
        }
      }
      return;
    }
    if (type == PROCESS_NOSHRINE) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were digging in originally.\n\r", ch);
        return;
      }
      for (vector<DOMAIN_TYPE *>::iterator it = DomainVect.begin();
      it != DomainVect.end(); ++it) {
        for (int i = 0; i < 250; i++) {
          if ((*it)->bigshrines[i] == ch->in_room->vnum) {
            (*it)->bigshrines[i] = 0;
            act("You finish cleansing the area.", ch, NULL, NULL, TO_CHAR);
            act("$n finishes cleansing the area.", ch, NULL, NULL, TO_ROOM);
            return;
          }
          if ((*it)->medshrines[i] == ch->in_room->vnum) {
            (*it)->medshrines[i] = 0;
            act("You finish cleansing the area.", ch, NULL, NULL, TO_CHAR);
            act("$n finishes cleansing the area.", ch, NULL, NULL, TO_ROOM);
            return;
          }
          if ((*it)->smallshrines[i] == ch->in_room->vnum) {
            (*it)->smallshrines[i] = 0;
            act("You finish cleansing the area.", ch, NULL, NULL, TO_CHAR);
            act("$n finishes cleansing the area.", ch, NULL, NULL, TO_ROOM);
            return;
          }
        }
      }
      return;
    }
    if (type == PROCESS_FILLIN) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were digging in originally.\n\r", ch);
        return;
      }
      ch->in_room->sector_type = SECT_PARK;
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      act("You finish draining the water and filling in the pit.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes draining the water and filling in the pit.", ch, NULL, NULL, TO_ROOM);
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          fch->pcdata->process = 0;
          fch->pcdata->process_timer = 0;
          fch->pcdata->last_develop_type = 0;
          fch->pcdata->last_develop_time = 0;
        }
      }
      return;
    }
    if (type == PROCESS_CLEARING) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were clearing originally.\n\r", ch);
        return;
      }
      ch->in_room->sector_type = SECT_PARK;
      ch->in_room->encroachment = 0;
      act("You finish making a clearing.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes making a clearing.", ch, NULL, NULL, TO_ROOM);
      ch->pcdata->week_tracker[TRACK_TREES_CHOPPED]++;
      ch->pcdata->life_tracker[TRACK_TREES_CHOPPED]++;
      if (!IS_SET(ch->in_room->area->area_flags, AREA_CHANGED))
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);

      int pop = 0;
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          pop++;
        }
      }
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          fch->pcdata->process = 0;
          fch->pcdata->process_timer = 0;
          fch->pcdata->last_develop_type = 0;
          fch->pcdata->last_develop_time = 0;
          int fpenalty =
          100 -
          get_skill(fch, SKILL_STRENGTH) * get_skill(fch, SKILL_STRENGTH) -
          get_skill(fch, SKILL_DEXTERITY) * get_skill(fch, SKILL_DEXTERITY);
          fpenalty -= 3 * labor_points(fch) * labor_points(fch);
          fpenalty = fpenalty * (100 - chainsaw_bonus(fch)) / 100;
          fpenalty = UMAX(fpenalty, 10);
          fpenalty /= UMAX(1, pop);
          fch->pcdata->fatigue += fpenalty * 10;
        }
      }
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      return;
    }
    if (type == PROCESS_BUTCHER) {
      OBJ_DATA *obj = NULL;
      if ((obj = get_eq_char(ch, WEAR_HOLD)) == NULL || !is_name(ch->pcdata->process_argumentone, obj->name)) {
        obj = get_obj_carry(ch, ch->pcdata->process_argumentone, ch);
      }
      if (obj == NULL) {
        obj = get_obj_list(ch, ch->pcdata->process_argumentone, ch->in_room->contents);
      }
      if (obj == NULL) {
        send_to_char("You can't find it.\n\r", ch);
        return;
      }
      if (obj->item_type != ITEM_CORPSE_NPC) {
        send_to_char("That's not a corpse.\n\r", ch);
        return;
      }
      if (obj->value[3] == 0) {
        send_to_char("That isn't a harvestable corpse.\n\r", ch);
        return;
      }
      for (int i = 0; i < 33; i++) {
        if (obj->value[3] == monster_table[i].vnum) {
          OBJ_DATA *reward;
          reward = create_object(get_obj_index(38), 0);
          reward->level = 0;
          reward->size = 10;
          free_string(reward->name);
          reward->name = str_dup(monster_table[i].object);
          free_string(reward->short_descr);
          reward->short_descr = str_dup(monster_table[i].object);
          char tmp[MSL];
          sprintf(tmp, "%s %s", a_or_an(monster_table[i].object), monster_table[i].object);
          free_string(reward->description);
          reward->description = str_dup(tmp);
          reward->level = obj->value[4] * 3;
          char lstring[MSL];
          sprintf(lstring, "BUTCHER: %s butchers %s for material level %d.", ch->name, obj->description, reward->level);
          log_string(lstring);
          if (reward->level > 0 && get_skill(ch, SKILL_ALCHEMY) > 0) {
            reward->level =
            reward->level * (10 + get_skill(ch, SKILL_ALCHEMY)) / 10;
          }
          obj_to_char(reward, ch);
          act("You finish butchering the corpse and extract $a $p.", ch, reward, NULL, TO_CHAR);
          act("$n finishes butchering the corpse and extracts $a $p.", ch, reward, NULL, TO_ROOM);
          ch->pcdata->fatigue += (10 - get_skill(ch, SKILL_DEMONOLOGY));
          obj->value[4] = 0;
          obj->value[3] = 0;
          return;
        }
      }
      return;
    }
    if (type == PROCESS_ROAD) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were clearing originally.\n\r", ch);
        return;
      }
      ch->in_room->sector_type = SECT_STREET;
      ch->in_room->encroachment = 0;
      if (!IS_SET(ch->in_room->room_flags, ROOM_DIRTROAD))
      TOGGLE_BIT(ch->in_room->room_flags, ROOM_DIRTROAD);
      free_string(ch->in_room->name);
      ch->in_room->name = str_dup(ch->pcdata->process_argumentone);
      free_string(ch->in_room->description);
      ch->in_room->description = str_dup(ch->pcdata->process_argumenttwo);
      act("You finish making a dirt road.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes making a dirt road.", ch, NULL, NULL, TO_ROOM);
      ch->pcdata->week_tracker[TRACK_ROADS_BUILT]++;
      ch->pcdata->life_tracker[TRACK_ROADS_BUILT]++;
      if (!IS_SET(ch->in_room->area->area_flags, AREA_CHANGED))
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      ch->money -= 1000;
      int pop = 0;
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          pop++;
        }
      }
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          fch->pcdata->process = 0;
          fch->pcdata->process_timer = 0;
          fch->pcdata->last_develop_type = 0;
          fch->pcdata->last_develop_time = 0;
          int fpenalty =
          100 -
          get_skill(fch, SKILL_STRENGTH) * get_skill(fch, SKILL_STRENGTH) -
          get_skill(fch, SKILL_DEXTERITY) * get_skill(fch, SKILL_DEXTERITY);
          fpenalty -= 3 * labor_points(fch) * labor_points(fch);
          fpenalty = UMAX(fpenalty, 10);
          fpenalty /= UMAX(1, pop);
          fch->pcdata->fatigue += fpenalty * 2;
        }
      }
      return;
    }
    if (type == PROCESS_PAVING) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were clearing originally.\n\r", ch);
        return;
      }
      ch->in_room->sector_type = SECT_STREET;
      ch->in_room->encroachment = 0;
      if (IS_SET(ch->in_room->room_flags, ROOM_DIRTROAD))
      TOGGLE_BIT(ch->in_room->room_flags, ROOM_DIRTROAD);
      act("You finish paving the road.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes paving the road.", ch, NULL, NULL, TO_ROOM);
      free_string(ch->in_room->name);
      ch->in_room->name = str_dup(ch->pcdata->process_argumentone);
      free_string(ch->in_room->description);
      ch->in_room->description = str_dup(ch->pcdata->process_argumenttwo);

      if (!IS_SET(ch->in_room->area->area_flags, AREA_CHANGED))
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      ch->money -= 10000;
      int pop = 0;
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          pop++;
        }
      }
      for (CharList::iterator it = ch->in_room->people->begin();
      it != ch->in_room->people->end();) {
        CHAR_DATA *fch = *it;
        ++it;
        if (fch == NULL || IS_NPC(fch))
        continue;
        if (fch->pcdata->process == type) {
          fch->pcdata->process = 0;
          fch->pcdata->process_timer = 0;
          fch->pcdata->last_develop_type = 0;
          fch->pcdata->last_develop_time = 0;
          int fpenalty =
          100 -
          get_skill(fch, SKILL_STRENGTH) * get_skill(fch, SKILL_STRENGTH) -
          get_skill(fch, SKILL_DEXTERITY) * get_skill(fch, SKILL_DEXTERITY);
          fpenalty -= 3 * labor_points(fch) * labor_points(fch);
          fpenalty = UMAX(fpenalty, 10);
          fpenalty /= UMAX(1, pop);
          fch->pcdata->fatigue += fpenalty * 4;
        }
      }
      return;
    }

    if (type == PROCESS_RELAY) {
      if (ch->pcdata->process_subtype != ch->in_room->vnum) {
        send_to_char("This isn't the room you were clearing originally.\n\r", ch);
        return;
      }
      ch->in_room->encroachment = 0;
      act("You finish relaying the road.", ch, NULL, NULL, TO_CHAR);
      act("$n finishes relaying the road.", ch, NULL, NULL, TO_ROOM);
      free_string(ch->in_room->name);
      ch->in_room->name = str_dup(ch->pcdata->process_argumentone);
      free_string(ch->in_room->description);
      ch->in_room->description = str_dup(ch->pcdata->process_argumenttwo);

      if (!IS_SET(ch->in_room->area->area_flags, AREA_CHANGED))
      SET_BIT(ch->in_room->area->area_flags, AREA_CHANGED);
      return;
    }
    if (type == PROCESS_EXTERMINATE) {
      if (ch->pcdata->process_target == NULL)
      return;
      if (!operating_room(ch->in_room))
      return;

      ch->pcdata->process_target->pcdata->egg_daddy = 0;
      wound_char_absolute(ch->pcdata->process_target, 2);
      act("You finish $N's surgery, killing everything implanted into $M.", ch, NULL, ch->pcdata->process_target, TO_CHAR);
      act("$n finishes your surgery.", ch, NULL, ch->pcdata->process_target, TO_VICT);
      act("$n finishes $N's surgery.", ch, NULL, ch->pcdata->process_target, TO_NOTVICT);
    }
    if (type == PROCESS_TREATING) {
      if (ch->pcdata->process_target == NULL)
      return;
      if (!in_medical_facility(ch))
      return;

      CHAR_DATA *victim = ch->pcdata->process_target;
      if (!treat_wounds(ch, victim)) {
        send_to_char("Treatment requires another wounded character here.\n\r", ch);
        return;
      }
      int cost = 500;
      int faccost = 0;
      int cashcost = 0;
      if (ch->faction > 0 && has_trust(ch, TRUST_RESOURCES, ch->faction) && can_afford_faction_spending(clan_lookup(ch->faction), cost / 10, 5000 + faccost) && can_spend_resources(clan_lookup(ch->faction))) {
        faccost = cost / 10;
      }
      else
      cashcost = cost * 100;

      if (cashcost > 0) {
        printf_to_char(ch, "For %d dollars in supplies you treat %s's wounds\n\r", cashcost / 100, PERS(victim, ch));
        ch->money -= cashcost;
      }
      else {
        printf_to_char(ch, "For $%d society resources you treat %s's wounds\n\r", faccost * 10, PERS(victim, ch));
        use_resources(faccost, ch->faction, ch, "treating wounds.");
      }
      victim->heal_timer =
      victim->heal_timer * (90 - (get_skill(ch, SKILL_MEDICINE) * 10)) / 100;

      act("You finish treating $N's wounds.", ch, NULL, victim, TO_CHAR);
      act("$n finishes treating your wounds.", ch, NULL, victim, TO_VICT);
      act("$n finishes treating $N's wounds.", ch, NULL, victim, TO_NOTVICT);
    }
    if (type == PROCESS_RESEARCH) {
      if (!library_room(ch->in_room))
      return;

      lookup_research(ch, ch->pcdata->process_argumentone);
      send_to_char("You finish your research.\n\r", ch);
    }
    if (type == PROCESS_LOOKINGUP) {
      if (ch->pcdata->process_target == NULL)
      return;

      if (!library_room(ch->in_room))
      return;

      if (clan_lookup(ch->faction) == NULL)
      return;
      CHAR_DATA *victim = ch->pcdata->process_target;

      int cost = 10;

      if (ch != victim) {
        act("You finish collecting reading matieral for $N.", ch, NULL, victim, TO_CHAR);
      }
      else
      act("You finish collecting reading material.", ch, NULL, victim, TO_CHAR);

      clan_lookup(ch->faction)->research -= cost;
      sprintf(buf, "%s uses %d research.", ch->name, cost);
      send_log(ch->faction, buf);
    }
  }


}
