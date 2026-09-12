#include "merc.h"
#include <time.h>

// These intervals use real elapsed time, including time spent logged out.
int feeding_interval(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || is_gm(ch) || IS_IMMORTAL(ch)
      || IS_FLAG(ch->act, PLR_GUEST) || IS_FLAG(ch->act, PLR_DEAD)) return 0;
  int tier = get_tier(ch);
  if (tier < 3) return 0;
  return (tier == 3 ? 30 : tier == 4 ? 21 : 14) * 86400;
}

int feeding_stage(CHAR_DATA *ch) {
  int interval = feeding_interval(ch);
  if (!interval || ch->pcdata->last_feeding <= 0) return 0;
  time_t overdue = current_time - ch->pcdata->last_feeding - interval;
  if (overdue < 0) return 0;
  return 1 + (int)UMIN((time_t)3, overdue / (7 * 86400));
}

static const int feeding_penalties[] = {0, 500, 1500, 3000, 5000};

int feeding_lf_penalty(CHAR_DATA *ch) {
  return feeding_penalties[feeding_stage(ch)];
}

bool feeding_blocks_sanctuary(CHAR_DATA *ch) {
  return feeding_stage(ch) >= 4;
}

void record_feeding(CHAR_DATA *ch, int amount, const char *reason) {
  int interval = feeding_interval(ch);
  if (amount <= 0 || !interval || !reason) return;
  // Only actual feeding qualifies, never transfusions or generic LF grants.
  if (str_cmp(reason, "Vampire bite") && str_cmp(reason, "Fear Feeding")
      && str_cmp(reason, "Anger Feeding") && str_cmp(reason, "Lust feeding")
      && str_cmp(reason, "Ambiant feeding") && str_cmp(reason, "difficult prisoner")
      && str_cmp(reason, "summary victimize") && str_cmp(reason, "prisoner pass out")
      && str_cmp(reason, "victimize") && str_cmp(reason, "sacrifice ritual")) return;
  if (feeding_stage(ch) > 0)
    send_to_char("You feed, quieting your hunger. Your hunger penalties have lifted.\n\r", ch);
  ch->pcdata->last_feeding = current_time;
  ch->pcdata->feeding_reminder = current_time;
  printf_to_char(ch, "You are fully fed. Your hunger clock has reset; your next hunger symptoms will begin in %d days if you do not feed again.\n\r", interval / 86400);
}

void feeding_update(CHAR_DATA *ch) {
  int interval = feeding_interval(ch);
  if (!interval) {
    if (ch && !IS_NPC(ch) && ch->pcdata && get_tier(ch) < 3) {
      ch->pcdata->last_feeding = 0;
      ch->pcdata->feeding_reminder = 0;
    }
    return;
  }
  if (ch->pcdata->last_feeding <= 0 || ch->pcdata->last_feeding > current_time)
    ch->pcdata->last_feeding = current_time; // Grace period for legacy characters.
  if (!ch->desc || ch->desc->connected != CON_PLAYING) return;
  int stage = feeding_stage(ch);
  const int frequency = 7 * 86400;
  if (ch->pcdata->feeding_reminder > 0
      && current_time >= ch->pcdata->feeding_reminder
      && current_time - ch->pcdata->feeding_reminder < frequency) return;
  ch->pcdata->feeding_reminder = current_time;
  time_t first_symptoms = (time_t)ch->pcdata->last_feeding + interval;
  if (!stage) {
    int days = (int)((first_symptoms - current_time + 86399) / 86400);
    printf_to_char(ch, "Feeding reminder: Your tier's first hunger symptoms begin after %d days without feeding. Feed within %d day%s to avoid weakness and a %d LF penalty.\n\r",
        interval / 86400, days, days == 1 ? "" : "s", feeding_penalties[1] / 100);
  } else {
    printf_to_char(ch, "You are overdue to feed. Hunger currently reduces your lifeforce by %d LF.\n\r", feeding_lf_penalty(ch) / 100);
    if (stage == 4) {
      send_to_char("You are starving and have lost both full and limited sanctuary protection. Feed to remove the hunger penalty and restore your eligibility for sanctuary.\n\r", ch);
    } else {
      int days = (int)((first_symptoms + stage * 7 * 86400 - current_time + 86399) / 86400);
      printf_to_char(ch, "If you do not feed within %d day%s, your hunger penalty will increase to %d LF%s.\n\r",
          days, days == 1 ? "" : "s", feeding_penalties[stage + 1] / 100,
          stage == 3 ? " and you will lose both full and limited sanctuary protection" : "");
    }
    send_to_char("Feeding removes these hunger penalties and starts a new feeding interval.\n\r", ch);
  }
}

// Resource units represent $10. Settlement deliberately has no secrecy multiplier.
const int CORTEX_LF_QUOTA = 20;
const int CORTEX_QUOTA_FINE = 1000;
const int CORTEX_QUOTA_REWARD = 250;

void cortex_quota_update(void) {
  FACTION_TYPE *fac = clan_lookup(FACTION_CORTEX);
  if (!fac) return;
  struct tm *now = gmtime(&current_time);
  if (!now) return;
  int month = (now->tm_year + 1900) * 12 + now->tm_mon + 1;
  if (fac->lf_quota_month == month) return;
  if (fac->lf_quota_month <= 0 || fac->lf_quota_month > month) {
    fac->lf_quota_month = month;
    fac->lf_quota_harvested = 0;
    save_clans(FALSE);
    return;
  }
  int missed = month - fac->lf_quota_month - 1;
  bool met = fac->lf_quota_harvested >= CORTEX_LF_QUOTA;
  fac->resource += (met ? CORTEX_QUOTA_REWARD : -CORTEX_QUOTA_FINE)
      - missed * CORTEX_QUOTA_FINE;
  char buf[MSL];
  sprintf(buf, "Monthly LF harvest quota: %d/%d LF. %s $%d.%s",
      fac->lf_quota_harvested, CORTEX_LF_QUOTA,
      met ? "Reward:" : "Fine:", (met ? CORTEX_QUOTA_REWARD : CORTEX_QUOTA_FINE) * 10,
      missed ? " Additional missed months were fined $10000 each." : "");
  send_log(fac->vnum, buf);
  fac->lf_quota_harvested = 0;
  fac->lf_quota_month = month;
  save_clans(FALSE);
}

void cortex_record_harvest(CHAR_DATA *ch, int amount) {
  if (!ch || IS_NPC(ch) || amount <= 0 || ch->fcore != FACTION_CORTEX) return;
  cortex_quota_update(); // Settle the old month before crediting a new harvest.
  FACTION_TYPE *fac = clan_lookup(FACTION_CORTEX);
  if (!fac) return;
  // No carryover, and surplus cannot overflow the saved counter.
  fac->lf_quota_harvested += UMIN(amount, UMAX(0, CORTEX_LF_QUOTA - fac->lf_quota_harvested));
  save_clans(FALSE);
}

void show_cortex_quota(CHAR_DATA *ch, FACTION_TYPE *fac) {
  if (!fac || fac->vnum != FACTION_CORTEX
      || (ch->fcore != FACTION_CORTEX && !IS_IMMORTAL(ch))) return;
  cortex_quota_update();
  printf_to_char(ch, "`gMonthly LF harvest quota`W:`x %d/%d LF (%s). Resets at the start of each UTC calendar month.\n\r`gMonth-end fine`W:`x $%d; `greward`W:`x $%d.\n\r",
      fac->lf_quota_harvested, CORTEX_LF_QUOTA,
      fac->lf_quota_harvested >= CORTEX_LF_QUOTA ? "met" : "unmet",
      CORTEX_QUOTA_FINE * 10, CORTEX_QUOTA_REWARD * 10);
}
