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
  return FALSE;
}

static int description_kind(ROOM_INDEX_DATA *room) {
  if (room->sector_type == SECT_ALLEY && room->name && strcasestr(room->name, "subway")) return -1;
  if (room->sector_type == SECT_CAR && !IS_SET(room->room_flags, ROOM_INDOORS)) return -2;
  if (room->sector_type == SECT_FOREST && room->name && strcasestr(room->name, "path")) return -3;
  if (room->sector_type == SECT_STREET && room->name && strcasestr(room->name, "sidewalk")) return SECT_SIDEWALK;
  return room->sector_type;
}

const char *default_room_description(ROOM_INDEX_DATA *room) {
  if (room == NULL) return room_terrain_text[0];
  int kind = description_kind(room);
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
};

static const StockPlace stock_places[] = {
  { -1, "seats", "The subway seats line the passenger aisle beneath the metal handholds.`x\n\r" },
  { -2, "seat", "The narrow riding seat leaves its occupant open to the surrounding space.`x\n\r" },
  { SECT_CLUB, "seating area", "Seats stand back from the dance floor, leaving room for quiet company.`x\n\r" },
  { SECT_RESTERAUNT, "tables", "Chairs gather around the dining tables, facing inward for conversation.`x\n\r" },
  { SECT_SHOP, "counter", "The counter provides a shared standing place along the customer side.`x\n\r" },
  { SECT_TAVERN, "bar", "The worn bar counter provides a long edge where people can gather.`x\n\r" },
  { SECT_TAVERN, "tables", "Tables stand apart from the bar with their chairs facing inward.`x\n\r" },
  { SECT_CAFE, "counter", "The counter faces the cafe's seating area.`x\n\r" },
  { SECT_CAFE, "tables", "The small tables provide close-set seating for conversation.`x\n\r" },
  { SECT_CAR, "seats", "The passenger seats provide a compact place to sit within the vehicle.`x\n\r" }
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
      if (entry.sector != kind && !strcmp(place->keyword, entry.name) &&
          !strcmp(place->description, entry.text)) obsolete = TRUE;
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
