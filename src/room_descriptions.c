/* Finished defaults for dynamically created rooms. Authored descriptions and
 * authored places are never overwritten. Stock strings are content markers,
 * so they survive area save/load and changes to a generated room's sector. */
#include <ctype.h>
#include <string.h>
#include "merc.h"
#include "recycle.h"
#include "room_default_text.h"

extern "C" {

bool unfinished_room_description(const char *text) {
  if (text == NULL) return TRUE;
  while (isspace((unsigned char)*text)) ++text;
  const char *end = text + strlen(text);
  while (end > text && isspace((unsigned char)end[-1])) --end;
  if (end == text) return TRUE;
  static const char *const placeholders[] = {
    "(null)", "todo", "tbd", "placeholder", "unfinished", "room description"
  };
  for (unsigned int i = 0; i < sizeof(placeholders)/sizeof(placeholders[0]); ++i) {
    const char *word = placeholders[i];
    if ((size_t)(end - text) != strlen(word)) continue;
    const char *cursor = text;
    while (*word && tolower((unsigned char)*cursor) == *word) { ++word; ++cursor; }
    if (!*word) return TRUE;
  }
  return FALSE;
}

bool room_uses_stock_description(ROOM_INDEX_DATA *room) {
  if (room != NULL && room->description_decorated) return FALSE;
  if (room == NULL || unfinished_room_description(room->description)) return TRUE;
  for (unsigned int i = 0; i < sizeof(room_terrain_text)/sizeof(room_terrain_text[0]); ++i)
    if (!strcmp(room->description, room_terrain_text[i])) return TRUE;
  for (unsigned int i = 0; i < sizeof(room_realm_forest_text)/sizeof(room_realm_forest_text[0]); ++i)
    if (!strcmp(room->description, room_realm_forest_text[i])) return TRUE;
  for (unsigned int i = 0; i < sizeof(room_transit_text)/sizeof(room_transit_text[0]); ++i)
    if (!strcmp(room->description, room_transit_text[i])) return TRUE;
  // The reusable travel pool retains a distinct cab interior through save/load
  // and can still clear automatic seats when the shell changes purpose.
  if (room->vnum >= 19000 && room->vnum <= 19099 &&
      !strcmp(room->description, room_taxi_text[room->vnum - 19000])) return TRUE;
  return FALSE;
}

static bool is_taxi_room(ROOM_INDEX_DATA *room) {
  return room->name && (!str_cmp(room->name, "Taxi") ||
                        !str_cmp(room->name, "The back of a Taxi"));
}

static int description_kind(ROOM_INDEX_DATA *room) {
  if (is_taxi_room(room)) return SECT_CAR;
  if (room->sector_type == SECT_ALLEY && room->name && strcasestr(room->name, "subway")) return -1;
  if (room->sector_type == SECT_CAR && !IS_SET(room->room_flags, ROOM_INDOORS)) return -2;
  if (room->sector_type == SECT_FOREST && room->name && strcasestr(room->name, "path")) return -3;
  if (room->sector_type == SECT_STREET && room->name && strcasestr(room->name, "sidewalk")) return SECT_SIDEWALK;
  return room->sector_type;
}

const char *default_room_description(ROOM_INDEX_DATA *room) {
  if (room == NULL) return room_terrain_text[0];
  int kind = description_kind(room);
  if (is_taxi_room(room)) {
    if (room->vnum >= 19000 && room->vnum <= 19099)
      return room_taxi_text[room->vnum - 19000];
    return room_terrain_text[SECT_CAR];
  }
  if (kind >= -3 && kind < 0) return room_transit_text[-kind - 1];
  if (room->sector_type == SECT_FOREST && room->area != NULL) {
    switch (room->area->vnum) {
    case OTHER_FOREST_VNUM: return room_realm_forest_text[0];
    case GODREALM_FOREST_VNUM: return room_realm_forest_text[1];
    case WILDS_FOREST_VNUM: return room_realm_forest_text[2];
    case HELL_FOREST_VNUM: return room_realm_forest_text[3];
    }
  }
  int sector = kind;
  if (sector < 0 || sector >= SECT_MAX) sector = 0;
  return room_terrain_text[sector];
}

static void default_place(ROOM_INDEX_DATA *room, const char *name, const char *text) {
  EXTRA_DESCR_DATA *place = new_extra_descr();
  place->keyword = str_dup(name);
  place->description = str_dup(text);
  place->next = room->places;
  room->places = place;
}

struct StockPlace {
  int sector;
  const char *name;
  const char *text;
  const char *previous_name;
  const char *previous_text;
};

// Area authoring and the engine use different line wrapping. Compare words
// exactly while treating whitespace runs alike, so a saved stock seat can be
// removed when a reusable vehicle becomes a sidewalk. Decorated rooms still
// return before this comparison, including intentionally stock-looking edits.
static bool same_place_text(const char *a, const char *b) {
  while (*a && *b) {
    if (isspace((unsigned char)*a) && isspace((unsigned char)*b)) {
      while (isspace((unsigned char)*a)) ++a;
      while (isspace((unsigned char)*b)) ++b;
    } else if (*a++ != *b++) return FALSE;
  }
  while (isspace((unsigned char)*a)) ++a;
  while (isspace((unsigned char)*b)) ++b;
  return !*a && !*b;
}

static const StockPlace stock_places[] = {
  { -1, "seats", "The subway seats are polished along the edges by countless passengers.\n\rMetal handholds hang above them, and the close spacing brings neighboring\n\rcompany within easy speaking distance.`x\n\r",
    "seats", "The subway seats line the passenger aisle beneath the metal handholds.`x\n\r" },
  { -2, "seat", "The narrow riding seat is smooth through the middle, with dust caught\n\ralong the seams. The compact frame stays close beneath it, leaving the\n\rrider open to the surrounding air.`x\n\r",
    "seat", "The narrow riding seat leaves its occupant open to the surrounding space.`x\n\r" },
  { SECT_CLUB, "sofa", "Deep cushions soften the low sofa beside the dance floor. The arms are\n\rrubbed smooth, and the upholstery holds a trace of old perfume. It's a\n\rcomfortable place to settle close to company and watch the room.`x\n\r",
    "seating area", "Seats stand back from the dance floor, leaving room for quiet company.`x\n\r" },
  { SECT_RESTERAUNT, "tables", "Dining chairs gather around tables marked by faint rings and tiny\n\rscratches. The close arrangement leaves room for a meal and the kind of\n\rconversation that lingers after the plates have gone.`x\n\r",
    "tables", "Chairs gather around the dining tables, facing inward for conversation.`x\n\r" },
  { SECT_SHOP, "counter", "The shop counter has a smooth edge beneath resting hands. Small\n\rhandling marks cloud the top, giving companions a shared surface for\n\rleaning in to discuss the surrounding displays.`x\n\r",
    "counter", "The counter provides a shared standing place along the customer side.`x\n\r" },
  { SECT_TAVERN, "bar", "Old drink rings overlap in the bar's dark finish. The long edge is\n\rsmooth beneath an elbow, bringing neighboring patrons within easy reach\n\rof a passing remark or a quietly exchanged confidence.`x\n\r",
    "bar", "The worn bar counter provides a long edge where people can gather.`x\n\r" },
  { SECT_TAVERN, "tables", "These tables sit a little apart from the bar, with chairs drawn close\n\raround their worn edges. Old rings remain beneath the finish, giving\n\reach group a comfortable pocket for conversation over a drink.`x\n\r",
    "tables", "Tables stand apart from the bar with their chairs facing inward.`x\n\r" },
  { SECT_CAFE, "counter", "A faint coffee smell lingers around the cafe counter. The nearest\n\redge is smooth from resting hands, with room to lean beside a companion\n\rand take in the small tables across the room.`x\n\r",
    "counter", "The counter faces the cafe's seating area.`x\n\r" },
  { SECT_CAFE, "tables", "Small cafe tables bring the chairs comfortably close. Pale cup rings\n\rtrace earlier visits across the wiped surfaces, leaving just enough\n\rroom for elbows and an unhurried conversation.`x\n\r",
    "tables", "The small tables provide close-set seating for conversation.`x\n\r" },
  { SECT_CAR, "seats", "The passenger seats fit closely inside the vehicle. Creased upholstery\n\rholds a faint fabric smell, and the padded backs offer a compact place\n\rto settle beside a traveling companion.`x\n\r",
    "seats", "The passenger seats provide a compact place to sit within the vehicle.`x\n\r" }
};

void clear_room_places(ROOM_INDEX_DATA *room) {
  if (room == NULL) return;
  while (room->places != NULL) {
    EXTRA_DESCR_DATA *place = room->places;
    room->places = place->next;
    free_extra_descr(place);
  }
}

void set_generated_room_description(ROOM_INDEX_DATA *room, const char *text) {
  if (room == NULL || room->description_decorated) return;
  // Duplicate first in case the caller passes the room's existing string.
  char *replacement = str_dup(unfinished_room_description(text)
    ? default_room_description(room) : text);
  free_string(room->description);
  room->description = replacement;
  ensure_room_description(room);
}

void copy_room_places(ROOM_INDEX_DATA *target, ROOM_INDEX_DATA *source) {
  if (target == NULL || source == NULL || target == source) return;
  ensure_room_description(source);
  target->description_decorated = source->description_decorated;
  clear_room_places(target);
  EXTRA_DESCR_DATA **tail = &target->places;
  for (EXTRA_DESCR_DATA *p = source->places; p; p = p->next) {
    EXTRA_DESCR_DATA *copy = new_extra_descr();
    copy->keyword = str_dup(p->keyword);
    copy->description = str_dup(p->description);
    copy->next = NULL;
    *tail = copy;
    tail = &copy->next;
  }
}

void ensure_room_description(ROOM_INDEX_DATA *room) {
  if (room == NULL || room->description_decorated || !room_uses_stock_description(room)) return;
  const char *text = default_room_description(room);
  if (room->description == NULL || strcmp(room->description, text)) {
    free_string(room->description);
    room->description = str_dup(text);
  }
  // Remove only our own obsolete places when a generated room changes type.
  // For example, a bus converted back into a sidewalk must not retain seats.
  EXTRA_DESCR_DATA **link = &room->places;
  int kind = description_kind(room);
  while (*link != NULL) {
    EXTRA_DESCR_DATA *place = *link;
    bool obsolete = FALSE;
    for (unsigned int i = 0; i < sizeof(stock_places)/sizeof(stock_places[0]); ++i) {
      const StockPlace &entry = stock_places[i];
      bool previous = !strcmp(place->keyword, entry.previous_name) &&
        same_place_text(place->description, entry.previous_text);
      bool current = !strcmp(place->keyword, entry.name) &&
        same_place_text(place->description, entry.text);
      if (!previous && !current) continue;
      if (entry.sector != kind) obsolete = TRUE;
      else if (previous) {
        // Recognize the exact previous automatic text, preserving custom places.
        free_string(place->keyword);
        free_string(place->description);
        place->keyword = str_dup(entry.name);
        place->description = str_dup(entry.text);
      }
      break;
    }
    if (obsolete) {
      *link = place->next;
      free_extra_descr(place);
    } else link = &place->next;
  }
  if (room->places != NULL) return;
  for (unsigned int i = 0; i < sizeof(stock_places)/sizeof(stock_places[0]); ++i) {
    const StockPlace &entry = stock_places[i];
    if (entry.sector == kind) default_place(room, entry.name, entry.text);
  }
}

} // extern "C"
