#!/usr/bin/env python3
"""Linux/WSL behavior and operation-count checks for description rendering."""

from pathlib import Path
import re
import subprocess
import tempfile

# Frozen pre-optimization production functions; no git dependency at runtime.
BASELINES = {
    'get_focused': r'''
  char *get_focused(CHAR_DATA *ch, CHAR_DATA *victim, bool xray) {
    int i, j, len;
    int min = 2000;
    int lastmin = -2000;
    char string[MSL];
    string[0] = '\0';
    char buf[MSL];

    if (IS_NPC(victim)) {
      return victim->description;
    }
    if (has_xray(ch))
    xray = TRUE;

    for (j = 0; j < 20; j++) {
      if (victim->pcdata->focused_order[COVERS_ALL] < min && victim->pcdata->focused_order[COVERS_ALL] > lastmin)
      min = victim->pcdata->focused_order[COVERS_ALL];
      for (i = 0; i <= COVERS_SMELL; i++) {
        if (i < MAX_COVERS && (cover_table[i] == COVERS_ARSE || cover_table[i] == COVERS_GROIN || cover_table[i] == COVERS_THIGHS || cover_table[i] == COVERS_LOWER_LEGS || cover_table[i] == COVERS_FEET) && victim->shape == SHAPE_MERMAID)
        continue;

        if (victim->pcdata->focused_order[i] < min && victim->pcdata->focused_order[i] > lastmin)
        min = victim->pcdata->focused_order[i];
      }

      if (victim->pcdata->focused_order[COVERS_ALL] == min && str_cmp(victim->description, "") && safe_strlen(victim->description) > 0) {
        sprintf(buf, "%s", victim->description);
        len = safe_strlen(buf);
        if (len >= 2 && buf[len - 2] == '\n')
        buf[len - 2] = 0;
        strcat(string, buf);
      }

      for (i = 0; i <= COVERS_SMELL; i++) {
        if (i < MAX_COVERS && (cover_table[i] == COVERS_ARSE || cover_table[i] == COVERS_GROIN || cover_table[i] == COVERS_THIGHS || cover_table[i] == COVERS_LOWER_LEGS || cover_table[i] == COVERS_FEET) && victim->shape == SHAPE_MERMAID)
        continue;

        if (i == COVERS_SMELL && (safe_strlen(victim->pcdata->focused_descs[i]) > 2 && ch->in_room == victim->in_room && (get_skill(ch, SKILL_ACUTESMELL) > 0 || ch == victim))) {
          if (victim->pcdata->focused_order[i] == min && str_cmp(victim->pcdata->focused_descs[i], "")) {
            sprintf(buf, "%s", victim->pcdata->focused_descs[i]);
            len = safe_strlen(buf);
            if (len >= 2 && buf[len - 2] == '\n')
            buf[len - 2] = 0;
            strcat(string, buf);
          }
        }
        else if (i < MAX_COVERS) {
          if (victim->pcdata->focused_order[i] == min && str_cmp(victim->pcdata->focused_descs[i], "") && (!is_covered(victim, cover_table[i]) || xray == TRUE)) {
            sprintf(buf, "%s", victim->pcdata->focused_descs[i]);
            len = safe_strlen(buf);
            if (len >= 2 && buf[len - 2] == '\n')
            buf[len - 2] = 0;
            strcat(string, buf);
          }
          if (victim->pcdata->focused_order[i] == min && !is_covered(victim, cover_table[i]) && victim->pcdata->brandlocation == i && victim->pcdata->branddate > 0) {
            sprintf(buf, "%s has a symbol of %s on %s %s. ", (victim->sex == SEX_MALE) ? "He" : "She", victim->pcdata->brandstring, (victim->sex == SEX_MALE) ? "his" : "her", name_by_location(i));
            strcat(string, buf);
          }
          if (victim->pcdata->focused_order[i] == min && !is_covered(victim, cover_table[i]) && str_cmp(victim->pcdata->scars[i], "")) {
            sprintf(buf, "%s ", victim->pcdata->scars[i]);
            strcat(string, buf);
          }
        }
      }
      lastmin = min;
      min = 2000;
    }

    if (safe_strlen(victim->pcdata->mermaiddesc) > 2 && victim->shape == SHAPE_MERMAID) {
      sprintf(buf, " %s\n", victim->pcdata->mermaiddesc);
      strcat(string, buf);
    }

    if(victim->pcdata->attract[ATTRACT_MAKEUP] == 1 && safe_strlen(victim->pcdata->makeup_light) > 2)
    {
      sprintf(buf, " %s\n", victim->pcdata->makeup_light);
      strcat(string, buf);
    }
    if(victim->pcdata->attract[ATTRACT_MAKEUP] == 2 && safe_strlen(victim->pcdata->makeup_medium) > 2)
    {
      sprintf(buf, " %s\n", victim->pcdata->makeup_medium);
      strcat(string, buf);
    }
    if(victim->pcdata->attract[ATTRACT_MAKEUP] == 3 && safe_strlen(victim->pcdata->makeup_heavy) > 2)
    {
      sprintf(buf, " %s\n", victim->pcdata->makeup_heavy);
      strcat(string, buf);
    }

    if (safe_strlen(victim->pcdata->scent) > 2 && ch->in_room == victim->in_room && (get_skill(ch, SKILL_ACUTESMELL) > 0 || (same_place(ch, victim)) || ch == victim)) {
      sprintf(buf, " %s\n", victim->pcdata->scent);
      strcat(string, buf);
    }

    char *result = str_dup(string);
    return result;
  }

''',
    'show_location': r'''
  void show_location(CHAR_DATA *ch, CHAR_DATA *victim, int location) {
    int i;
    int len;
    char string[MSL];
    char buf[MSL];
    string[0] = '\0';
    char *pdesc;
    int iWear;
    OBJ_DATA *obj;

    if (IS_NPC(victim))
    return;
    if (victim->shape != SHAPE_HUMAN && victim->shape != SHAPE_MERMAID)
    return;

    for (iWear = MAX_WEAR - 1; iWear >= 0; iWear--) {
      if (iWear == WEAR_HOLD)
      continue;
      if (iWear == WEAR_HOLD_2)
      continue;

      if (location >= 0 && location < MAX_COVERS && (obj = get_eq_char(victim, iWear)) != NULL && does_undercover(obj, cover_table[location]) && can_see_obj(ch, obj) && (can_see_wear(victim, iWear) || (has_xray(ch) && victim != ch && (!IS_IMMORTAL(ch) || !is_spyshield(victim))))) {
        if (obj->wear_temp != NULL && obj->wear_temp[0] != '\0')
        strcat(string, obj->wear_temp);

        strcat(string, format_obj_to_char(obj, ch, FALSE));

        strcat(string, "\n\r");

        pdesc = get_extra_descr_obj("all", obj->extra_descr, obj);
        if (pdesc != NULL) {
          strcat(string, pdesc);
        }
        else {
          pdesc = get_extra_descr_obj("all", obj->pIndexData->extra_descr, obj);
          if (pdesc != NULL) {
            strcat(string, pdesc);
          }
        }
      }
    }

    strcat(string, "\n\r");

    for (i = 0; i < MAX_COVERS + 1; i++) {
      if (i != location)
      continue;
      if (i < MAX_COVERS && (cover_table[i] == COVERS_ARSE || cover_table[i] == COVERS_GROIN || cover_table[i] == COVERS_THIGHS || cover_table[i] == COVERS_LOWER_LEGS || cover_table[i] == COVERS_FEET) && victim->shape == SHAPE_MERMAID)
      continue;

      if (i == MAX_COVERS && (safe_strlen(victim->pcdata->focused_descs[i]) > 2 && ch->in_room == victim->in_room && (get_skill(ch, SKILL_ACUTESMELL) > 0 || ch == victim))) {
        sprintf(buf, "%s", victim->pcdata->focused_descs[i]);
      }
      else if (i < MAX_COVERS && (!is_covered(victim, cover_table[i]) || has_xray(ch))) {
        sprintf(buf, "%s", victim->pcdata->focused_descs[i]);
      }
      else
      continue;

      len = safe_strlen(buf);
      if (len >= 2) {
        if (buf[len - 2] == '\n')
        buf[len - 2] = 0;
        strcat(string, buf);
      }
      for (int j = 0; j < 300; j++) {
        if (victim->pcdata->stat_log_method[j] == TRAINED_TATTOO + location && victim->pcdata->stat_log_to[j] > 0 && (location >= 0 && location < MAX_COVERS && (!is_covered(victim, cover_table[location]) || has_xray(ch)))) {
          sprintf(buf, "%s has a tattoo of %s.\n\r", (victim->sex == SEX_MALE) ? "He" : "She", victim->pcdata->stat_log_string[j]);
          strcat(string, buf);
          j = 300;
        }
      }

      if (victim->pcdata->branddate > 0 && victim->pcdata->brandlocation == location && (location >= 0 && location < MAX_COVERS && (!is_covered(victim, cover_table[location]) || has_xray(ch)))) {
        sprintf(buf, "%s has a symbol of %s on %s %s. ", (victim->sex == SEX_MALE) ? "He" : "She", victim->pcdata->brandstring, (victim->sex == SEX_MALE) ? "his" : "her", name_by_location(location));
        strcat(string, buf);
      }
      if (safe_strlen(victim->pcdata->scars[location]) > 3 && (location >= 0 && location < MAX_COVERS && (!is_covered(victim, cover_table[location]) || has_xray(ch)))) {
        sprintf(buf, "%s ", victim->pcdata->scars[location]);
        strcat(string, buf);
      }

      strcat(string, "\n\r");

      /*
      if(str_cmp(victim->pcdata->focused_descs[i], "") && safe_strlen(victim->pcdata->focused_descs[i]) > 6
      &&(!is_covered(victim, cover_table[i]) || has_xray(ch)))
      {
      strcat(string, buf);
      }
      */
    }

    if (safe_strlen(victim->pcdata->detail_over[location]) > 3) {
      sprintf(buf, " %s", victim->pcdata->detail_over[location]);
      strcat(string, buf);
    }
    if (safe_strlen(victim->pcdata->detail_under[location]) > 3 && (location >= 0 && location < MAX_COVERS && (!is_covered(victim, cover_table[location]) || has_xray(ch)))) {
      sprintf(buf, " %s", victim->pcdata->detail_under[location]);
      strcat(string, buf);
    }
    strcat(string, "\n\r");

    send_to_char(wrap_string(string, get_wordwrap(ch)), ch);

    //    send_to_char(string, ch);

    /*
    char * result = str_dup(string);
    return result;
    */
  }

''',
    'show_multilocation': r'''
  void show_multilocation(CHAR_DATA *ch, CHAR_DATA *victim, int location) {
    int i;
    int len;
    char string[MSL];
    char buf[MSL];
    string[0] = '\0';
    char *pdesc;
    int iWear;
    OBJ_DATA *obj;

    for (iWear = MAX_WEAR - 1; iWear >= 0; iWear--) {
      if (iWear == WEAR_HOLD)
      continue;
      if (iWear == WEAR_HOLD_2)
      continue;

      if ((obj = get_eq_char(victim, iWear)) != NULL && does_multicover(obj, location) && can_see_obj(ch, obj) && (can_see_wear(victim, iWear) || (has_xray(ch) && victim != ch && (!IS_IMMORTAL(ch) || !is_spyshield(victim))))) {
        if (obj->wear_temp != NULL && obj->wear_temp[0] != '\0')
        strcat(string, obj->wear_temp);

        strcat(string, format_obj_to_char(obj, ch, FALSE));

        strcat(string, "\n\r");

        pdesc = get_extra_descr_obj("all", obj->extra_descr, obj);
        if (pdesc != NULL) {
          strcat(string, pdesc);
        }
        else {
          pdesc = get_extra_descr_obj("all", obj->pIndexData->extra_descr, obj);
          if (pdesc != NULL) {
            strcat(string, pdesc);
          }
        }
      }
    }
    strcat(string, "\n\r");

    for (i = 0; i < MAX_COVERS + 1; i++) {
      if (!valid_multiloc(i, location))
      continue;
      if (i < MAX_COVERS && (cover_table[i] == COVERS_ARSE || cover_table[i] == COVERS_GROIN || cover_table[i] == COVERS_THIGHS || cover_table[i] == COVERS_LOWER_LEGS || cover_table[i] == COVERS_FEET) && victim->shape == SHAPE_MERMAID)
      continue;

      if (i == MAX_COVERS && (safe_strlen(victim->pcdata->focused_descs[i]) > 2 && ch->in_room == victim->in_room && (get_skill(ch, SKILL_ACUTESMELL) > 0 || ch == victim))) {
        sprintf(buf, "%s", victim->pcdata->focused_descs[i]);
      }
      else if (i < MAX_COVERS && safe_strlen(victim->pcdata->focused_descs[i]) > 2) {
        sprintf(buf, "%s", victim->pcdata->focused_descs[i]);
      }
      else
      continue;

      len = safe_strlen(buf);
      if (len >= 2) {
        if (buf[len - 2] == '\n')
        buf[len - 2] = 0;
      }

      if (str_cmp(victim->pcdata->focused_descs[i], "") && safe_strlen(victim->pcdata->focused_descs[i]) > 6 && (i == COVERS_SMELL || (i < MAX_COVERS && (!is_covered(victim, cover_table[i]) || has_xray(ch))))) {
        strcat(string, buf);
      }
      if (safe_strlen(victim->pcdata->detail_over[i]) > 3) {
        sprintf(buf, " %s", victim->pcdata->detail_over[i]);
        strcat(string, buf);
      }
      if (safe_strlen(victim->pcdata->detail_under[i]) > 3 && (i < MAX_COVERS && (!is_covered(victim, cover_table[i]) || has_xray(ch)))) {
        sprintf(buf, " %s", victim->pcdata->detail_under[i]);
        strcat(string, buf);
      }
      if (victim->pcdata->branddate > 0 && victim->pcdata->brandlocation == i) {
        sprintf(buf, "%s has a symbol of %s on %s %s. ", (victim->sex == SEX_MALE) ? "He" : "She", victim->pcdata->brandstring, (victim->sex == SEX_MALE) ? "his" : "her", name_by_location(i));
        strcat(string, buf);
      }
      if (safe_strlen(victim->pcdata->scars[i]) > 3 && (i < MAX_COVERS && (!is_covered(victim, cover_table[i]) || has_xray(ch)))) {
        sprintf(buf, "%s ", victim->pcdata->scars[i]);
        strcat(string, buf);
      }

      strcat(string, "\n\r");
    }

    page_to_char(wrap_string(string, get_wordwrap(ch)), ch);

    //    send_to_char(string, ch);

    /*
    char * result = str_dup(string);
    return result;
    */
  }

''',
    'get_default_dreamdesc': r'''
  char *get_default_dreamdesc(CHAR_DATA *victim) {
    int i, j, len;
    int min = 2000;
    int lastmin = -2000;
    char string[MSL];
    string[0] = '\0';
    char buf[MSL];

    if (IS_NPC(victim)) {
      return victim->description;
    }

    // Default dream appearance includes only visible body locations, not smell.
    for (j = 0; j < 20; j++) {
      if (victim->pcdata->focused_order[COVERS_ALL] < min && victim->pcdata->focused_order[COVERS_ALL] > lastmin)
      min = victim->pcdata->focused_order[COVERS_ALL];
      for (i = 0; i < MAX_COVERS; i++) {
        if (cover_table[i] != COVERS_EYES && cover_table[i] != COVERS_HAIR && cover_table[i] != COVERS_LOWER_FACE && cover_table[i] != COVERS_NECK && cover_table[i] != COVERS_FOREHEAD && cover_table[i] != COVERS_HANDS)
        continue;
        if (victim->pcdata->focused_order[i] < min && victim->pcdata->focused_order[i] > lastmin)
        min = victim->pcdata->focused_order[i];
      }

      if (victim->pcdata->focused_order[COVERS_ALL] == min && str_cmp(victim->description, "") && safe_strlen(victim->description) > 0) {
        sprintf(buf, "%s", victim->description);
        len = safe_strlen(buf);
        if (len >= 2 && buf[len - 2] == '\n')
        buf[len - 2] = 0;
        strcat(string, buf);
      }

      for (i = 0; i < MAX_COVERS; i++) {
        if (cover_table[i] != COVERS_EYES && cover_table[i] != COVERS_HAIR && cover_table[i] != COVERS_LOWER_FACE && cover_table[i] != COVERS_NECK && cover_table[i] != COVERS_FOREHEAD && cover_table[i] != COVERS_HANDS)
        continue;

        if (victim->pcdata->focused_order[i] == min && str_cmp(victim->pcdata->focused_descs[i], "") && (!is_covered(victim, cover_table[i]))) {
          sprintf(buf, "%s", victim->pcdata->focused_descs[i]);
          len = safe_strlen(buf);
          if (len >= 2 && buf[len - 2] == '\n')
          buf[len - 2] = 0;
          strcat(string, buf);
        }
      }
      lastmin = min;
      min = 2000;
    }
    char *result = str_dup(string);
    return result;
  }

''',
}

ROOT = Path(__file__).resolve().parents[1]
ACT_INFO = (ROOT / 'src/act_info.c').read_text()


def function(text, name):
    """Extract a complete top-level definition, including comments in its body."""
    start = re.search(r'^  (?:char \*|void |bool )' + re.escape(name) + r'\([^;\n]*\) \{', text, re.M)
    if not start:
        raise AssertionError('Missing production definition: ' + name)
    # These source files indent function bodies; the matching close is unindented
    # relative to all body statements, including blocks nested inside comments.
    end = text.index('\n  }', start.end()) + len('\n  }')
    return text[start.start():end] + '\n'


source = r'''
#include "merc.h"
#include <cassert>
#include <climits>
#include <cstring>
#include <cstdlib>
#include <iostream>
int snapshot_count = 0, coverage_count = 0, skill_count = 0, lookup_count = 0;
#include "instrumented_equipment_snapshot.h"
std::vector<char *> allocations;
std::string output;
CHAR_DATA actor = {}, target = {};
PC_DATA actor_pc = {}, target_pc = {};
ROOM_INDEX_DATA room = {}, other_room = {};
OBJ_DATA garment = {}, second_garment = {};
OBJ_INDEX_DATA garment_index = {}, second_index = {};
EXTRA_DESCR_DATA item_extra = {}, index_extra = {};
bool xray = false, nearby = false, spyshield = false;
bool bath = false, water = false, stream = false;
int checks = 0;
char *str_dup(const char *s) {
  char *p = strdup(s ? s : ""); allocations.push_back(p); return p;
}
bool str_cmp(const char *a, const char *b) { return strcasecmp(a ? a : "", b ? b : "") != 0; }
size_t safe_strlen(const char *s) { return s ? strlen(s) : 0; }
void send_to_char(const char *s, CHAR_DATA *) { output += s; }
void page_to_char(const char *s, CHAR_DATA *) { output += s; }
char *wrap_string(char *s, int) { return s; }
int get_wordwrap(CHAR_DATA *) { return 80; }
bool has_xray(CHAR_DATA *) { return xray; }
bool same_place(CHAR_DATA *, CHAR_DATA *) { return nearby; }
bool is_spyshield(CHAR_DATA *) { return spyshield; }
int get_trust(CHAR_DATA *ch) { return ch->level; }
int get_skill(CHAR_DATA *ch, int skill) { ++skill_count; return ch->skills[skill]; }
bool in_bath(CHAR_DATA *) { return bath; }
bool deep_water(CHAR_DATA *) { return water; }
bool in_stream(CHAR_DATA *) { return stream; }
char *name_by_location(int i) {
  static char names[MAX_COVERS + 10][16];
  snprintf(names[i], sizeof(names[i]), "location%d", i);
  return names[i];
}
bool does_cover(OBJ_DATA *obj, int sel) {
  for (int i = 0; i < MAX_COVERS; ++i)
    if (cover_table[i] == sel) return (obj->value[0] & (1 << i)) != 0;
  return false;
}
bool does_undercover(OBJ_DATA *obj, int sel) {
  for (int i = 0; i < MAX_COVERS; ++i)
    if (cover_table[i] == sel) return (obj->value[1] & (1 << i)) != 0;
  return false;
}
bool can_see_obj(CHAR_DATA *, OBJ_DATA *obj) { return obj->value[3] == 0; }
bool can_see_wear_equipped(CHAR_DATA *, int slot, const haven::EquipmentSnapshot &equipment) {
  OBJ_DATA *obj = equipment.get(slot);
  return obj && obj->value[2] == 0;
}
bool can_see_wear(CHAR_DATA *ch, int slot) {
  haven::EquipmentSnapshot equipment(ch);
  return can_see_wear_equipped(ch, slot, equipment);
}
char *format_obj_to_char(OBJ_DATA *obj, CHAR_DATA *, bool) { return obj->short_descr; }
char *get_extra_descr_obj(const char *, EXTRA_DESCR_DATA *ed, OBJ_DATA *) {
  return ed ? ed->description : nullptr;
}
'''

# Use the real coverage policy and snapshot traversal. Stub unrelated formatting,
# room predicates and garment cover masks to keep the fixture deterministic.
source += function(ACT_INFO, 'is_covered_equipped').replace(
    '{\n', '{\n    ++coverage_count;\n', 1)
source += function(ACT_INFO, 'is_covered')
handler = (ROOT / 'src/handler.c').read_text()
start = handler.index('OBJ_DATA *get_eq_char(CHAR_DATA *ch, int iWear) {')
end = handler.index('\nOBJ_DATA *get_held(', start)
source += handler[start:end].replace('{\n', '{\n  ++lookup_count;\n', 1)
source += function(ACT_INFO, 'does_multicover')
source += function(ACT_INFO, 'valid_multiloc')
for name, reference in BASELINES.items():
    source += reference.replace(name + '(', 'baseline_' + name + '(', 1)
    source += function(ACT_INFO, name)

source += r'''
void reset_counts() { snapshot_count = coverage_count = skill_count = lookup_count = 0; }
void reset() {
  actor = {}; target = {}; actor_pc = {}; target_pc = {};
  garment = {}; second_garment = {}; garment_index = {}; second_index = {};
  item_extra = {}; index_extra = {};
  actor.pcdata = &actor_pc; target.pcdata = &target_pc;
  actor.in_room = target.in_room = &room;
  actor.name = (char *)"Actor"; target.name = (char *)"Target";
  target.description = (char *)"BASE \n\r";
  target.shape = SHAPE_HUMAN; target.sex = SEX_MALE;
  target_pc.brandlocation = 0; target_pc.branddate = 1;
  target_pc.brandstring = (char *)"BRAND";
  target_pc.mermaiddesc = (char *)"MERMAID";
  target_pc.makeup_light = (char *)"LIGHT MAKEUP";
  target_pc.makeup_medium = (char *)"MEDIUM MAKEUP";
  target_pc.makeup_heavy = (char *)"HEAVY MAKEUP";
  target_pc.scent = (char *)"SCENT";
  static char descs[MAX_COVERS + 10][32], scars[MAX_COVERS + 10][32];
  static char overs[MAX_COVERS + 10][32], unders[MAX_COVERS + 10][32];
  for (int i = 0; i < MAX_COVERS + 10; ++i) {
    snprintf(descs[i], sizeof(descs[i]), "DESC%d \n\r", i);
    snprintf(scars[i], sizeof(scars[i]), "SCAR%d", i);
    snprintf(overs[i], sizeof(overs[i]), "OVER%d", i);
    snprintf(unders[i], sizeof(unders[i]), "UNDER%d", i);
    target_pc.focused_descs[i] = descs[i]; target_pc.focused_order[i] = i;
    target_pc.scars[i] = scars[i]; target_pc.detail_over[i] = overs[i];
    target_pc.detail_under[i] = unders[i];
  }
  garment.wear_loc = WEAR_BODY_1; garment.pIndexData = &garment_index;
  garment.short_descr = (char *)"FIRST GARMENT"; garment.wear_temp = (char *)"WORN ";
  garment.value[0] = garment.value[1] = (1 << MAX_COVERS) - 1;
  second_garment.wear_loc = WEAR_BODY_2; second_garment.pIndexData = &second_index;
  second_garment.short_descr = (char *)"SECOND GARMENT";
  second_garment.value[0] = second_garment.value[1] = 1 << 17;
  garment.next_content = &second_garment;
  item_extra.description = (char *)"ITEM EXTRA\n\r";
  index_extra.description = (char *)"INDEX EXTRA\n\r";
  garment.extra_descr = &item_extra; garment_index.extra_descr = &index_extra;
  second_index.extra_descr = &index_extra;
  target_pc.stat_log_method[299] = TRAINED_TATTOO;
  target_pc.stat_log_to[299] = 1;
  target_pc.stat_log_string[299] = (char *)"TATTOO";
  xray = nearby = spyshield = bath = water = stream = false;
  output.clear(); reset_counts();
}
void same_output(const std::string &actual, const std::string &expected, const char *label) {
  if (actual != expected) {
    std::cerr << label << " differs\nACTUAL: " << actual << "\nEXPECTED: " << expected << '\n';
    abort();
  }
  ++checks;
}
std::string check_focused(CHAR_DATA *viewer = &actor, bool explicit_xray = false) {
  reset_counts();
  std::string expected = baseline_get_focused(viewer, &target, explicit_xray);
  const int baseline_coverage = coverage_count;
  reset_counts();
  std::string actual = get_focused(viewer, &target, explicit_xray);
  same_output(actual, expected, "get_focused");
  if (!IS_NPC(&target)) {
    assert(snapshot_count == 1);
    assert(coverage_count <= baseline_coverage);
    assert(lookup_count == 0);
  }
  return actual;
}
std::string check_dream() {
  reset_counts();
  std::string expected = baseline_get_default_dreamdesc(&target);
  const int baseline_coverage = coverage_count;
  reset_counts();
  std::string actual = get_default_dreamdesc(&target);
  same_output(actual, expected, "get_default_dreamdesc");
  if (!IS_NPC(&target)) {
    assert(snapshot_count == 1);
    assert(coverage_count <= baseline_coverage);
    assert(lookup_count == 0);
  }
  return actual;
}
std::string check_location(int location, bool multi = false, CHAR_DATA *viewer = &actor) {
  output.clear();
  if (multi) baseline_show_multilocation(viewer, &target, location);
  else baseline_show_location(viewer, &target, location);
  std::string expected = output;
  output.clear(); reset_counts();
  if (multi) show_multilocation(viewer, &target, location);
  else show_location(viewer, &target, location);
  same_output(output, expected, multi ? "show_multilocation" : "show_location");
  if (multi || (!IS_NPC(&target) && (target.shape == SHAPE_HUMAN || target.shape == SHAPE_MERMAID))) {
    assert(snapshot_count == 1);
    assert(coverage_count <= (multi ? MAX_COVERS : 2));
    assert(lookup_count == 0);
  }
  return output;
}
void check_all() {
  check_focused(); check_dream();
  for (int i = 0; i <= COVERS_SMELL; ++i) check_location(i);
  for (int i = 0; i <= 5; ++i) check_location(i, true);
}
bool contains(const std::string &s, const char *part) { return s.find(part) != std::string::npos; }
struct Counts { int snapshots, coverage, skills, lookups; };
Counts counts() { return {snapshot_count, coverage_count, skill_count, lookup_count}; }
void report(const char *label, Counts before, Counts after) {
  std::cout << label << ": snapshots " << before.snapshots << " -> " << after.snapshots
            << ", coverage " << before.coverage << " -> " << after.coverage
            << ", skill " << before.skills << " -> " << after.skills
            << ", slot lookups " << before.lookups << " -> " << after.lookups << '\n';
}
int main() {
  reset(); check_all();
  // Smell depends on room and acute smell/self; ordinary scent also uses proximity.
  assert(!contains(check_focused(), "DESC18 "));
  assert(!contains(check_focused(), "SCENT"));
  actor.skills[SKILL_ACUTESMELL] = 1;
  assert(contains(check_focused(), "DESC18 "));
  assert(skill_count <= 2);
  check_all();
  actor.in_room = &other_room;
  assert(!contains(check_focused(), "DESC18 "));
  assert(!contains(check_focused(), "SCENT")); check_all();
  actor.in_room = &room; actor.skills[SKILL_ACUTESMELL] = 0; nearby = true;
  std::string focused = check_focused();
  assert(!contains(focused, "DESC18 ") && contains(focused, "SCENT"));
  assert(contains(check_focused(&target), "DESC18 "));
  check_location(COVERS_SMELL, false, &target);
  check_location(4, true, &target);

  // X-ray exposes focused descriptions, but focused brands/scars remain covered.
  reset(); target.carrying = &garment;
  focused = check_focused();
  assert(!contains(focused, "DESC0 ") && !contains(focused, "BRAND") && !contains(focused, "SCAR0"));
  xray = true; focused = check_focused();
  assert(contains(focused, "DESC0 ") && !contains(focused, "BRAND") && !contains(focused, "SCAR0"));
  check_all(); xray = false; focused = check_focused(&actor, true);
  assert(contains(focused, "DESC0 ") && !contains(focused, "BRAND"));
  // Consecutive calls must observe changed exposure, equipment and environment.
  target_pc.exposed[0] = 111; focused = check_focused();
  assert(contains(focused, "DESC0 ") && contains(focused, "BRAND") && contains(focused, "SCAR0"));
  check_all(); target_pc.exposed[0] = 0; target.carrying = nullptr; check_all();
  assert(contains(check_focused(), "DESC0 "));
  target.carrying = &garment; assert(!contains(check_focused(), "DESC0 "));
  garment.value[0] = 0; check_all();
  bath = true; check_all(); bath = false; water = true; check_all();
  water = false; stream = true; check_all(); stream = false;
  SET_FLAG(target.comm, COMM_BLINDFOLD); check_all();

  // Item descriptions retain descending slot order, visibility, held exclusions,
  // object extra-descriptions and prototype fallback, including x-ray/spyshield.
  reset(); target.carrying = &garment; garment.value[2] = 1; check_all();
  xray = true; check_all(); actor.level = LEVEL_IMMORTAL; spyshield = true; check_all();
  spyshield = false; check_all(); garment.value[3] = 1; check_all();
  garment.value[3] = 0; garment.extra_descr = nullptr; check_all();
  garment.wear_loc = WEAR_HOLD; second_garment.wear_loc = WEAR_HOLD_2; check_all();
  check_location(0, false, &target); check_location(4, true, &target);

  reset(); target.shape = SHAPE_MERMAID; check_all();
  focused = check_focused();
  assert(contains(focused, "MERMAID") && !contains(focused, "DESC3 ") && !contains(focused, "DESC7 "));
  for (int makeup = 1; makeup <= 3; ++makeup) { target_pc.attract[ATTRACT_MAKEUP] = makeup; check_all(); }
  reset(); target.shape = 999; assert(check_location(0).empty());
  reset(); SET_FLAG(target.act, ACT_IS_NPC); target.pcdata = nullptr;
  assert(check_focused() == target.description && check_dream() == target.description);
  check_location(0);

  // Preserve tied and extreme order behavior, including repeated 2000 sentinels.
  reset();
  for (int i = 0; i <= COVERS_ALL; ++i) target_pc.focused_order[i] = 3;
  check_all();
  for (int i = 0; i <= COVERS_ALL; ++i) target_pc.focused_order[i] = 2000;
  check_focused(); check_dream();
  const int orders[] = {INT_MIN, -2001, -2000, -1999, -1, 0, 1, 3, 1999, 2000, 2001, INT_MAX};
  unsigned state = 17;
  for (int trial = 0; trial < 120; ++trial) {
    reset();
    for (int i = 0; i <= COVERS_ALL; ++i) {
      state = state * 1664525u + 1013904223u;
      target_pc.focused_order[i] = orders[state % (sizeof(orders) / sizeof(*orders))];
      if ((state & 7) == 0) target_pc.focused_descs[i] = (char *)"";
      else if ((state & 7) == 1) target_pc.focused_descs[i] = (char *)"x";
      else if ((state & 7) == 2) target_pc.focused_descs[i] = (char *)"short";
    }
    target_pc.brandlocation = trial % MAX_COVERS;
    target.shape = trial % 3 == 0 ? SHAPE_MERMAID : SHAPE_HUMAN;
    target.carrying = trial % 2 ? &garment : nullptr;
    xray = trial % 4 == 0;
    actor.skills[SKILL_ACUTESMELL] = trial % 2;
    check_all();
  }
  // Quantify repeated work using a typical complete description.
  reset(); target.carrying = &garment; garment.value[0] = 0;
  actor.skills[SKILL_ACUTESMELL] = 1;
  reset_counts(); baseline_get_focused(&actor, &target, false);
  const Counts before_focused = counts();
  reset_counts(); get_focused(&actor, &target, false);
  assert(snapshot_count == 1 && snapshot_count < before_focused.snapshots);
  assert(coverage_count <= MAX_COVERS && coverage_count < before_focused.coverage);
  assert(skill_count <= 2 && skill_count < before_focused.skills);
  std::cout << "PASS: " << checks << " exact baseline comparisons under ASan/UBSan.\n";
  report("Focused", before_focused, counts());
  reset_counts(); baseline_get_default_dreamdesc(&target);
  const Counts before_dream = counts();
  reset_counts(); get_default_dreamdesc(&target);
  assert(snapshot_count == 1 && coverage_count <= 6);
  report("Dream", before_dream, counts());
  reset_counts(); baseline_show_location(&actor, &target, 0);
  const Counts before_location = counts();
  reset_counts(); show_location(&actor, &target, 0);
  assert(snapshot_count == 1 && coverage_count <= 2 && lookup_count == 0);
  report("Single location", before_location, counts());
  reset_counts(); baseline_show_multilocation(&actor, &target, 4);
  const Counts before_multi = counts();
  reset_counts(); show_multilocation(&actor, &target, 4);
  assert(snapshot_count == 1 && coverage_count <= MAX_COVERS && lookup_count == 0);
  report("Multiple locations", before_multi, counts());
  for (char *p : allocations) free(p);
}
'''

with tempfile.TemporaryDirectory(prefix='haven-description-optimization-') as tmp:
    path = Path(tmp)
    header = (ROOT / 'src/equipment_snapshot.h').read_text()
    constructor = 'explicit EquipmentSnapshot(CHAR_DATA *ch) {'
    assert header.count(constructor) == 1
    (path / 'instrumented_equipment_snapshot.h').write_text(header.replace(
        constructor, constructor + '\n        ++snapshot_count;'))
    (path / 'test.cc').write_text(source)
    subprocess.run(['g++', '-std=gnu++17', '-w', '-ffunction-sections', '-fdata-sections',
                    '-Wl,--gc-sections', '-fsanitize=address,undefined', '-no-pie',
                    '-I', str(ROOT / 'src'), str(path / 'test.cc'), str(ROOT / 'src/tables.c'),
                    '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
