#include "merc.h"
#include "recycle.h"
#include <dirent.h>
#include <cstring>
#include <sstream>
#include <climits>
#include <set>
#include <cctype>

extern "C" {

void fread_population_char(CHAR_DATA *ch, FILE *fp);

int containment_priority_count(FACTION_TYPE *fac, CHAR_DATA *recovering) {
  if (!fac || (fac->type == FACTION_SOCIETY && fac->axes[AXES_CORRUPT] == AXES_DEMONIC)) return 0;
  int count = 0;
  std::set<std::string> seen;
  auto name_key = [](const char *name) {
    std::string key = name ? name : "";
    for (char &c : key) c = std::tolower(static_cast<unsigned char>(c));
    return key;
  };
  auto inspect = [&](CHAR_DATA *member) {
    if (!member || IS_NPC(member) || !member->pcdata) return;
    if (!seen.insert(name_key(member->name)).second) return;
    if (member->fcore != fac->vnum && member->fsociety != fac->vnum && member->legacy_society != fac->vnum) return;
    if (is_containment_priority(member)
        && !(fac->vnum == FACTION_CORTEX && cortex_loyalty_chip(member))) ++count;
  };
  // The recovering character can be loaded offline and absent from char_list.
  inspect(recovering);
  for (CHAR_DATA *member : char_list) inspect(member);
  for (int i = 0; i < 100; ++i) {
    const std::string key = name_key(fac->member_names[i]);
    if (key.empty() || seen.count(key)
        || key.find_first_not_of("abcdefghijklmnopqrstuvwxyz") != std::string::npos) continue;
    const std::string path = std::string(PLAYER_DIR) + capitalize(fac->member_names[i]);
    FILE *fp = fopen(path.c_str(), "r");
    if (!fp) continue;
    // Read character data without inventory, login normalization or save writes.
    if (!str_cmp(fread_word(fp), "#PLAYER")) {
      CHAR_DATA *member = new_char();
      member->pcdata = new_pcdata();
      free_string(member->name);
      member->name = str_dup(fac->member_names[i]);
      fread_population_char(member, fp);
      inspect(member);
      free_char(member);
    }
    fclose(fp);
  }
  return count;
}

void invalidate_wound_treatment(CHAR_DATA *ch) {
  if (ch && !IS_NPC(ch) && ch->pcdata && ch->pcdata->recovery) {
    ch->pcdata->recovery->wounds_treated = false;
    ch->pcdata->recovery->operation_wound = false;
  }
}

bool treat_wounds(CHAR_DATA *healer, CHAR_DATA *victim) {
  if (!healer || !victim || healer == victim || IS_NPC(healer) || IS_NPC(victim)
      || !victim->pcdata || !victim->pcdata->recovery || victim->wounds < 1
      || victim->wounds > 3 || !healer->in_room || healer->in_room != victim->in_room)
    return false;
  victim->pcdata->recovery->wounds_treated = true;
  return true;
}

long next_sanctuary_recovery() {
  // get_hour(NULL) is the server clock; rooms and accounts may override it.
  const long hour_start = current_time - current_time % 3600;
  int hours = (6 - get_hour(NULL) + 24) % 24;
  if (hours == 0) hours = 24;
  return hour_start + hours * 3600L;
}

static int recovery_payer(CHAR_DATA *ch) {
  if (personal_sanctuary(ch)) {
    FACTION_TYPE *patron = ch->vassal > 0 ? clan_lookup(ch->vassal) : NULL;
    return patron && patron->valid ? patron->vnum : RECOVERY_PERSONAL_PAYER;
  }
  const int candidates[] = {ch->fsociety, ch->legacy_society, ch->vassal, ch->fcore, ch->faction};
  for (int id : candidates) {
    FACTION_TYPE *fac = id > 0 ? clan_lookup(id) : NULL;
    if (fac && fac->valid) return id;
  }
  return 0; // No organization exists to bill; do not invent one on recovery.
}

static RecoveryIncident incident(CHAR_DATA *ch, CHAR_DATA *actor, bool monster) {
  RecoveryIncident record;
  if (!ch || IS_NPC(ch) || !ch->pcdata) return record;
  record.serial = ++ch->pcdata->recovery->serial;
  record.receipt = std::string(ch->name) + ":" + std::to_string(ch->id) + ":"
                 + std::to_string(current_time) + ":" + std::to_string(record.serial);
  record.forest = monster || (actor && forest_monster(actor));
  if (record.forest) return record;
  // Capture active coverage at the incident, including for ritual protection.
  // An affect can remain present while Sanctuary is revoked or suspended.
  if (sanctuary_population_blocked()) return record;
  const bool black = under_black(ch, actor ? actor : ch);
  if (!black && !under_sanctuary(ch, actor ? actor : ch)) return record;
  if (black) record.cost_percent = 20;
  if (IS_AFFECTED(ch, AFF_UNDERSTANDING)) record.source = RECOVERY_RITUAL;
  else {
    record.source = RECOVERY_SANCTUARY;
    record.payer = recovery_payer(ch);
  }
  return record;
}

void record_critical_injury(CHAR_DATA *ch, CHAR_DATA *actor, bool monster) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || ch->wounds == 3) return;
  // The engine has one critical wound / bleed-out timer, not a wound stack.
  ch->pcdata->recovery->critical = incident(ch, actor, monster);
}

void record_death_recovery(CHAR_DATA *ch, CHAR_DATA *actor, bool wound, bool monster) {
  RecoveryState &state = *ch->pcdata->recovery;
  state.death = wound ? state.critical : incident(ch, actor, monster);
  if (wound) state.death.serial = ++state.serial;
  if (state.death.source != RECOVERY_NONE && !state.death.forest)
    state.death.due = next_sanctuary_recovery();
  state.critical = RecoveryIncident();
}

static std::string maim_description(const RecoveryState &state) {
  std::string result;
  for (const auto &record : state.maims) {
    if (!result.empty()) result += " and ";
    result += record.description;
  }
  return result;
}

static void reconcile_maims(CHAR_DATA *ch) {
  RecoveryState &state = *ch->pcdata->recovery;
  std::string visible = ch->pcdata->maim ? ch->pcdata->maim : "";
  if (visible == maim_description(state)) return;
  // Legacy saves and explicit medical/admin edits never acquire insurance.
  state.maims.clear();
  if (!visible.empty()) {
    RecoveryIncident legacy;
    legacy.description = visible;
    state.maims.push_back(legacy);
  }
}

void record_maim(CHAR_DATA *ch, const char *text, CHAR_DATA *actor, bool monster) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !text || !*text) return;
  reconcile_maims(ch);
  RecoveryIncident record = incident(ch, actor, monster);
  record.description = text;
  if (record.source != RECOVERY_NONE && !record.forest) record.due = next_sanctuary_recovery();
  ch->pcdata->recovery->maims.push_back(record);
  std::string description = maim_description(*ch->pcdata->recovery);
  free_string(ch->pcdata->maim);
  ch->pcdata->maim = str_dup(description.c_str());
}

static bool charge_recovery(CHAR_DATA *ch, const RecoveryIncident &record, int cost) {
  if (record.source != RECOVERY_SANCTUARY || record.forest || record.payer == 0) return true;
  if (record.payer == RECOVERY_PERSONAL_PAYER) {
    // Unaffiliated humans pay per death only, never for maims or weekly upkeep.
    // The balance and consumed incident are saved together by the recovery pass.
    if (cost != SANCTUARY_DEATH_COST) return true;
    const long fee = PERSONAL_SANCTUARY_DEATH_COST * record.cost_percent / 100;
    if (ch->pcdata->total_money < LONG_MIN + fee) return false;
    ch->pcdata->total_money -= fee;
    printf_to_char(ch, "Sanctuary death recovery costs $%ld, charged to your personal bank account.\n\r", fee / 100);
    if (ch->pcdata->total_money < 0)
      send_to_char("You are an indentured servant until your bank debt is repaid: sixteen-hour work days cap LF at 30 and provide double full-time base pay.\n\r", ch);
    if (ch->pcdata->total_money <= -PERSONAL_SANCTUARY_DEBT_LIMIT)
      send_to_char("Your debt has reached the sanctuary limit. Further deaths will not be covered without a society or vassal patron.\n\r", ch);
    return true;
  }
  FACTION_TYPE *fac = clan_lookup(record.payer);
  if (!fac) return false; // Retain the record if its saved payer is unavailable.
  const std::string receipt = "|" + record.receipt + "|";
  if (strstr(fac->recovery_receipts, receipt.c_str())) return true;
  // Bill the recovered character's current tier, with T5 as the maximum rate.
  cost *= URANGE(1, get_tier(ch), 5);
  // Every non-exempt priority raises both recovery fees by 25%, additively.
  // Round resource units up and preserve the durable receipt's one-charge rule.
  const long long charged = (static_cast<long long>(cost)
      * (100LL + 25LL * containment_priority_count(fac, ch)) * record.cost_percent + 9999) / 10000;
  if (charged > INT_MAX) return false;
  cost = static_cast<int>(charged);
  if (fac->resource < INT_MIN + cost) return false;
  std::string receipts = std::string(fac->recovery_receipts) + receipt;
  const int old_balance = fac->resource;
  const std::string old_receipts = fac->recovery_receipts;
  fac->resource -= cost;
  free_string(fac->recovery_receipts);
  fac->recovery_receipts = str_dup(receipts.c_str());
  // Balance and receipt share a save. A stale player save cannot bill twice.
  if (!save_clans(FALSE)) {
    fac->resource = old_balance;
    free_string(fac->recovery_receipts);
    fac->recovery_receipts = str_dup(old_receipts.c_str());
    return false;
  }
  return true;
}

void operation_recovery_wake(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !ch->pcdata->recovery) return;
  RecoveryState &state = *ch->pcdata->recovery;
  if (state.operation_active) return;
  state.operation_active = true;
  state.operation_wound = false;
  state.operation_saved_wounds = ch->wounds;
  state.operation_saved_heal_timer = ch->heal_timer;
  state.operation_saved_treatment = state.wounds_treated;
  if (!IS_FLAG(ch->act, PLR_DEAD)) return;
  state.operation_dead = true;
  state.operation_ghost = IS_FLAG(ch->act, PLR_GHOST);
  REMOVE_FLAG(ch->act, PLR_DEAD);
  REMOVE_FLAG(ch->act, PLR_GHOST);
  ch->hit = max_hp(ch);
}

void operation_recovery_return(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !ch->pcdata->recovery) return;
  if (ch->factiontrue > -1) {
    ch->faction = ch->factiontrue;
    ch->factiontrue = -1;
  }
  RecoveryState &state = *ch->pcdata->recovery;
  const bool had_snapshot = state.operation_active;
  if (state.operation_active) {
    state.operation_active = false;
    if (!state.operation_wound || ch->wounds <= state.operation_saved_wounds) {
      ch->wounds = state.operation_saved_wounds;
      ch->heal_timer = state.operation_saved_heal_timer;
      state.wounds_treated = state.operation_saved_treatment;
      state.operation_wound = false;
    }
  }
  if (!state.operation_dead) return;
  // Old player saves may contain operation_dead without a wound snapshot.
  // Preserve their wounds instead of treating zero-initialized fields as one.
  if (had_snapshot) {
    ch->wounds = state.operation_saved_wounds;
    ch->heal_timer = state.operation_saved_heal_timer;
    state.wounds_treated = state.operation_saved_treatment;
  }
  state.operation_wound = false;
  state.operation_dead = false;
  SET_FLAG(ch->act, PLR_DEAD);
  if (state.operation_ghost) SET_FLAG(ch->act, PLR_GHOST);
  state.operation_ghost = false;
}

int operation_heal_timer(CHAR_DATA *ch, int timer) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !ch->pcdata->recovery) return timer;
  RecoveryState &state = *ch->pcdata->recovery;
  if (!state.operation_wound) return timer;
  if (ch->wounds <= state.operation_saved_wounds) {
    // The nightmare injury is gone. Resume the preexisting wound unchanged.
    state.operation_wound = false;
    state.wounds_treated = state.operation_saved_treatment;
    return state.operation_saved_heal_timer;
  }
  return UMAX(1, timer / 50);
}

bool process_character_recovery(CHAR_DATA *ch) {
  if (!ch || IS_NPC(ch) || !ch->pcdata || !ch->in_room) return false;
  RecoveryState &state = *ch->pcdata->recovery;
  if (ch->wounds == 0) state.operation_wound = false;
  if (state.operation_active && !battleground(ch->in_room))
    operation_recovery_return(ch);
  if (state.operation_dead) {
    if (battleground(ch->in_room)) return false;
    operation_recovery_return(ch);
  }
  bool changed = false;
  if (ch->wounds != 3) state.critical = RecoveryIncident();
  reconcile_maims(ch);
  if (!IS_FLAG(ch->act, PLR_DEAD)) state.death = RecoveryIncident();
  if (state.death.due > 0 && state.death.due <= current_time
      && state.death.source != RECOVERY_NONE && !state.death.forest) {
    ROOM_INDEX_DATA *room = NULL;
    std::set<int> stops;
    int available = 0;
    for (int i = 0; i < trolly_stop_count; ++i) {
      if (!stops.insert(trolly_stops[i]).second) continue;
      ROOM_INDEX_DATA *candidate = get_room_index(trolly_stops[i]);
      // Give each distinct, existing stop the same chance of selection.
      if (candidate && number_range(1, ++available) == 1) room = candidate;
    }
    if (room && charge_recovery(ch, state.death, SANCTUARY_DEATH_COST)) {
      REMOVE_FLAG(ch->act, PLR_DEAD);
      REMOVE_FLAG(ch->act, PLR_GHOST);
      REMOVE_FLAG(ch->act, PLR_SHROUD);
      REMOVE_FLAG(ch->act, PLR_DEEPSHROUD);
      ch->pcdata->spectre = 0;
      ch->pcdata->final_death_date = 0;
      ch->wounds = 0;
      ch->hit = max_hp(ch);
      ch->position = POS_STANDING;
      char_from_room(ch);
      char_to_room(ch, room);
      release_clinic_after_respawn(ch);
      state.death = RecoveryIncident();
      changed = true;
      send_to_char("You wake at a trolley stop. Your possessions remain with your corpse.\n\r", ch);
    }
  }
  for (auto it = state.maims.begin(); it != state.maims.end();) {
    if (it->due > 0 && it->due <= current_time && it->source != RECOVERY_NONE
        && !it->forest && charge_recovery(ch, *it, SANCTUARY_MAIM_COST)) {
      it = state.maims.erase(it);
      changed = true;
    } else ++it;
  }
  if (changed) {
    std::string description = maim_description(state);
    free_string(ch->pcdata->maim);
    ch->pcdata->maim = str_dup(description.c_str());
    save_char_obj(ch, FALSE, FALSE);
  }
  return changed;
}

void process_daily_recoveries() {
  for (CHAR_DATA *ch : char_list) process_character_recovery(ch);
  // Scan offline saves at startup and each server 06:00 boundary. Online
  // players are processed above, including overdue records after copyover.
  static long next_scan = 0;
  if (current_time < next_scan) return;
  next_scan = next_sanctuary_recovery();
  DIR *directory = opendir(PLAYER_DIR);
  if (!directory) { next_scan = current_time + 60; return; }
  while (dirent *entry = readdir(directory)) {
    const std::string name = entry->d_name;
    if (name.empty() || name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz") != std::string::npos) continue;
    if (get_char_world_pc(const_cast<char *>(name.c_str()))) continue;
    std::ifstream file(std::string(PLAYER_DIR) + name);
    std::string line;
    bool pending = false;
    while (std::getline(file, line)) {
      if (line.compare(0, 16, "RecoveryIncident") == 0) { pending = true; break; }
    }
    if (!pending) continue;
    DESCRIPTOR_DATA *descriptor = new_descriptor();
    if (load_char_obj(descriptor, const_cast<char *>(name.c_str()))) {
      // There is no live socket for an offline recovery.
      descriptor->character->desc = NULL;
      process_character_recovery(descriptor->character);
    }
    if (descriptor->character) {
      if (descriptor->character->in_room) char_from_room(descriptor->character);
      free_char(descriptor->character);
      descriptor->character = NULL;
    }
    free_descriptor(descriptor);
  }
  closedir(directory);
}

void write_recovery(FILE *fp, CHAR_DATA *ch) {
  reconcile_maims(ch);
  const RecoveryState &state = *ch->pcdata->recovery;
  fprintf(fp, "WoundsTreated %d\n", ch->wounds >= 2 && state.wounds_treated);
  fprintf(fp, "RecoveryState %lu %d %d\n", state.serial, state.operation_dead, state.operation_ghost);
  fprintf(fp, "OperationRecovery %d %d %d %d %d\n", state.operation_active, state.operation_wound,
      state.operation_saved_wounds, state.operation_saved_heal_timer, state.operation_saved_treatment);
  auto write = [fp](int kind, const RecoveryIncident &record) {
    fprintf(fp, "RecoveryIncidentV3 %d %d %d %d %ld %lu %d %s~ %s~\n", kind, record.source,
            record.payer, record.forest, record.due, record.serial, record.cost_percent,
            record.description.c_str(), record.receipt.c_str());
  };
  if (state.death.serial) write(0, state.death);
  if (state.critical.serial && ch->wounds == 3) write(1, state.critical);
  for (const auto &record : state.maims) write(2, record);
}

bool read_recovery(FILE *fp, CHAR_DATA *ch, const char *word) {
  RecoveryState &state = *ch->pcdata->recovery;
  if (!str_cmp(word, "OperationRecovery")) {
    state.operation_active = fread_number(fp) != 0;
    state.operation_wound = fread_number(fp) != 0;
    state.operation_saved_wounds = fread_number(fp);
    state.operation_saved_heal_timer = fread_number(fp);
    state.operation_saved_treatment = fread_number(fp) != 0;
    return true;
  }
  if (!str_cmp(word, "WoundsTreated")) {
    state.wounds_treated = fread_number(fp) != 0;
    return true;
  }
  if (!str_cmp(word, "RecoveryState")) {
    state.serial = fread_number(fp);
    state.operation_dead = fread_number(fp) != 0;
    state.operation_ghost = fread_number(fp) != 0;
    return true;
  }
  const bool version2 = !str_cmp(word, "RecoveryIncidentV2");
  const bool version3 = !str_cmp(word, "RecoveryIncidentV3");
  if (!version2 && !version3 && str_cmp(word, "RecoveryIncident")) return false;
  int kind = fread_number(fp);
  RecoveryIncident record;
  record.source = fread_number(fp);
  record.payer = fread_number(fp);
  record.forest = fread_number(fp) != 0;
  record.due = fread_number(fp);
  record.serial = fread_number(fp);
  if (version3) record.cost_percent = fread_number(fp) == 20 ? 20 : 100;
  char *text = fread_string(fp);
  record.description = text;
  free_string(text);
  if (version2 || version3) {
    text = fread_string(fp);
    record.receipt = text;
    free_string(text);
  } else record.receipt = std::string(ch->name) + ":" + std::to_string(ch->id) + ":" + std::to_string(record.serial);
  if (record.source < RECOVERY_NONE || record.source > RECOVERY_RITUAL || record.forest) {
    record.source = RECOVERY_NONE;
    record.due = 0;
  }
  state.serial = std::max(state.serial, record.serial);
  if (kind == 0) state.death = record;
  if (kind == 1) state.critical = record;
  if (kind == 2) state.maims.push_back(record);
  return true;
}
}
