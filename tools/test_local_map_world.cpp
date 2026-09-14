// Exercise the map in the loaded engine and real world, in a disposable copy.
#include <cassert>
#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <string>
#include "merc.h"
#include "recycle.h"
#include "local_map.h"
#include "combat_map.h"

extern "C" {
extern char str_boot_time[];
void boot_db();
void do_map(CHAR_DATA *, char *);
}

static void command(CHAR_DATA *ch, void (*fn)(CHAR_DATA *, char *), const char *arg) {
  ch->desc->outtop = 0;
  ch->desc->outbuf[0] = '\0';
  char text[MSL];
  strcpy(text, arg);
  fn(ch, text);
}

static void place(CHAR_DATA *ch, int vnum) {
  if (ch->in_room) char_from_room(ch);
  char_to_room(ch, get_room_index(vnum));
}

static std::string plain_text(const std::string &text) {
  std::string plain;
  for (size_t i = 0; i < text.size(); ++i) {
    if (text[i] == '\033' && i + 1 < text.size() && text[i + 1] == '[') {
      i += 2;
      while (i < text.size() && !(text[i] >= '@' && text[i] <= '~')) ++i;
    }
    else if (text[i] == '`' && i + 1 < text.size()) ++i;
    else if (text[i] != '\r' && text[i] != '\a') plain += text[i];
  }
  return plain;
}

static bool has_minimap(CHAR_DATA *ch) {
  return plain_text(ch->desc->outbuf).find("+-----------+") != std::string::npos;
}

static size_t description_width(CHAR_DATA *ch) {
  std::string source = std::string(ch->in_room->description) + "`x\n\r";
  const std::string text = plain_text(wrap_string(&source[0], get_wordwrap(ch)));
  size_t widest = 0;
  for (size_t at = 0; at < text.size();) {
    const size_t end = text.find('\n', at);
    const size_t stop = end == std::string::npos ? text.size() : end;
    size_t trimmed = stop;
    while (trimmed > at && text[trimmed - 1] == ' ') --trimmed;
    widest = std::max(widest, trimmed - at);
    at = stop + 1;
  }
  return std::min(widest, static_cast<size_t>(get_wordwrap(ch)));
}

static std::string without_minimap(const std::string &text) {
  std::string body;
  const size_t column = text.find("+-----------+");
  int row = 0;
  for (size_t at = 0; at < text.size(); ++row) {
    const size_t end = text.find('\n', at);
    const size_t stop = end == std::string::npos ? text.size() : end;
    size_t left_end = row < 7 && column != std::string::npos ? at + column : stop;
    assert(left_end <= stop);
    while (left_end > at && text[left_end - 1] == ' ') --left_end;
    body.append(text, at, left_end - at);
    body += '\n';
    at = stop + 1;
  }
  return body;
}

static std::string normalized_words(const std::string &text) {
  std::string words;
  for (unsigned char c : text) {
    if (std::isspace(c)) {
      if (!words.empty() && words.back() != ' ') words += ' ';
    }
    else words += c;
  }
  if (!words.empty() && words.back() == ' ') words.pop_back();
  return words;
}

static std::string color_before(CHAR_DATA *ch, const char *marker) {
  const std::string text = ch->desc->outbuf;
  const size_t token = text.find(marker);
  assert(token != std::string::npos);
  const size_t color = text.rfind("\033[", token);
  const size_t end = text.find('m', color);
  assert(color != std::string::npos && end < token);
  return text.substr(color, end - color + 1);
}

static void assert_look_layout(CHAR_DATA *ch, const char *title,
                               const char *description,
                               bool description_beside_map = true) {
  const std::string text = plain_text(ch->desc->outbuf);
  const size_t top = text.find("+-----------+");
  const size_t first_end = text.find('\n');
  assert(top != std::string::npos && top < first_end);
  assert(text.find(title) < top);
  assert(strstr(ch->desc->outbuf, (std::string(C_GREEN) + "+-----------+").c_str()));
  const size_t column = top;
  assert(column + 13 <= description_width(ch));
  size_t line = 0;
  for (int row = 0; row < 7; ++row) {
    const size_t end = text.find('\n', line);
    assert(end != std::string::npos);
    assert(end - line <= static_cast<size_t>(ch->linewidth));
    const char side = row == 0 || row == 6 ? '+' : '|';
    assert(text[line + column] == side);
    assert(text[line + column + 12] == side);
    line = end + 1;
  }
  const size_t prose = text.find(description);
  assert(prose != std::string::npos);
  if (description_beside_map) {
    assert(prose < line);
    // The normal room status follows the title immediately, without a spacer.
    const size_t second = first_end + 1;
    assert(text[second] != ' ' && text[second] != '\n');
  }
  const std::string body = without_minimap(text);
  assert(normalized_words(body).find(normalized_words(
      plain_text(ch->in_room->description))) != std::string::npos);
  assert(text.find("Nearby") == std::string::npos);
  assert(text.find("help map") == std::string::npos);
}

static char player_stairs(const std::string &map) {
  const std::string plain = plain_text(map);
  const size_t player = plain.find('@');
  assert(player != std::string::npos && player + 1 < plain.size());
  return plain[player + 1];
}

int main() {
  setvbuf(stdout, NULL, _IONBF, 0);
  current_time = time(NULL);
  strcpy(str_boot_time, ctime(&current_time));
  boot_db();
  CHAR_DATA *ch = new_char();
  if (!ch->pcdata) ch->pcdata = new_pcdata();
  ch->name = str_dup("LocalMapVisitor");
  ch->level = 1;
  ch->trust = 0;
  ch->position = POS_STANDING;
  ch->hit = 1000;
  ch->lines = 0;
  ch->linewidth = 80;
  ch->desc = new_descriptor();
  ch->desc->character = ch;
  ch->desc->connected = CON_PLAYING;
  ch->desc->fcommand = TRUE;
  ch->desc->ansi = TRUE;
  SET_FLAG(ch->act, PLR_COLOR);

  const int locations[] = {16132, 18074, 9475, 3970, 16386, 10199, 6180, 90052};
  for (int vnum : locations) {
    place(ch, vnum);
    haven::LocalMapStats small, large;
    const std::string mini = haven::render_local_map(ch, ch->in_room, true, &small);
    const std::string full = haven::render_local_map(ch, ch->in_room, false, &large);
    assert(mini.find('@') != std::string::npos && full.find('@') != std::string::npos);
    assert(small.rooms <= 9 && large.rooms <= 165);
    assert(small.exits_examined <= 90 && large.exits_examined <= 1650);
    printf("PASS: room %d, minimap %d rooms / %d exits; full %d / %d\n",
           vnum, small.rooms, small.exits_examined, large.rooms, large.exits_examined);
    if (vnum == 3970 || vnum == 16132 || vnum == 18074) {
      printf("MAP SAMPLE %d: %s\n%s\n", vnum, ch->in_room->name, mini.c_str());
      if (vnum == 3970) printf("LARGE MAP SAMPLE\n%s\n", full.c_str());
    }
  }

  // These legacy canopy rooms retain forest terrain and zero jump/climb/fall
  // metadata, but should never advertise ordinary stairs into the treetops.
  const int canopies[][2] = {{1904, 8178}, {2066, 6101}, {16011, 5276}};
  for (const auto &route : canopies) {
    place(ch, route[0]);
    const char up = player_stairs(haven::render_local_map(ch, ch->in_room, true));
    assert(up != '^' && up != '*');
    place(ch, route[1]);
    const char down = player_stairs(haven::render_local_map(ch, ch->in_room, true));
    assert(down != 'v' && down != '*');
  }
  place(ch, 16132);
  assert(player_stairs(haven::render_local_map(ch, ch->in_room, true)) == '^');
  place(ch, 18074);
  assert(player_stairs(haven::render_local_map(ch, ch->in_room, true)) == '*');
  puts("PASS: real academy stairs retained, six ground/canopy rooms have no false stair markers");

  place(ch, 16132);
  SET_BIT(ch->in_room->room_flags, ROOM_LIGHTON);
  REMOVE_BIT(ch->in_room->room_flags, ROOM_DARK | ROOM_UNLIT);
  // These changes affect only the fixture's disposable loaded world.
  char *original_title = ch->in_room->name;
  char *original_description = ch->in_room->description;
  ch->in_room->name = str_dup("`WLocalMapTitle`x");
  ch->in_room->description = str_dup(
      "DescriptionProbe. A quiet classroom with tall windows stands ready for its "
      "next lesson. Sunlight falls across the wooden desks and polished floor. "
      "Books and writing paper fill the shelves along the far wall, while a "
      "large chalkboard waits beside a neatly arranged stack of spare chairs. "
      "A soft breeze carries the scent of fresh grass through an open window, "
      "and the curtains stir gently beside a vase of small yellow flowers."
      "\n\r       \n\rParagraphProbe. The wide doorway leads into a peaceful corridor "
      "where another row of windows overlooks the garden and its old stone wall.             ");
  assert(!IS_FLAG(ch->comm, COMM_NOMINIMAP));
  command(ch, do_map, "");
  assert(strstr(ch->desc->outbuf, "help map"));
  const int map_wait = ch->wait;
  command(ch, do_look, "");
  assert_look_layout(ch, "LocalMapTitle", "DescriptionProbe.");
  const std::string compact_body = without_minimap(plain_text(ch->desc->outbuf));
  assert(compact_body.find("\n\nParagraphProbe.") != std::string::npos);
  // Once the map ends, the main description uses the complete prose column.
  const std::string compact_text = plain_text(ch->desc->outbuf);
  const size_t map_column = compact_text.find("+-----------+");
  size_t after_map = 0;
  for (int row = 0; row < 7; ++row)
    after_map = compact_text.find('\n', after_map) + 1;
  const size_t paragraph = compact_text.find("ParagraphProbe.");
  bool expanded_line = false;
  for (size_t at = after_map; at < paragraph;) {
    const size_t end = compact_text.find('\n', at);
    assert(end != std::string::npos);
    if (end - at > map_column) expanded_line = true;
    at = end + 1;
  }
  assert(expanded_line);
  printf("COMPACT LOOK SAMPLE\n%s\n", ch->desc->outbuf);
  command(ch, do_look, "auto");
  assert_look_layout(ch, "LocalMapTitle", "DescriptionProbe.");
  assert(ch->wait == map_wait);
  command(ch, do_look, "north");
  // Directional look turns the character and then performs look auto.
  assert_look_layout(ch, "LocalMapTitle", "DescriptionProbe.");
  command(ch, do_look, "unmappedtestobject");
  assert(!has_minimap(ch));

  // A red status message with no explicit reset must not recolor the plain
  // description when separate sends are collected into one flowing layout.
  const auto original_flags = ch->in_room->room_flags;
  const int original_encroachment = ch->in_room->encroachment;
  const int original_bloodstorm = time_info.bloodstorm;
  ch->in_room->room_flags = ROOM_INDOORS;
  ch->in_room->encroachment = 0;
  time_info.bloodstorm = 1;
  assert(in_haven(ch->in_room));
  command(ch, do_map, "off");
  command(ch, do_look, "");
  assert(strstr(ch->desc->outbuf, "A mystical storm"));
  const std::string plain_prose_color = color_before(ch, "DescriptionProbe.");
  command(ch, do_map, "on");
  command(ch, do_look, "");
  assert(has_minimap(ch));
  assert(strstr(ch->desc->outbuf, "A mystical storm"));
  assert(color_before(ch, "DescriptionProbe.") == plain_prose_color);
  ch->in_room->room_flags = original_flags;
  ch->in_room->encroachment = original_encroachment;
  time_info.bloodstorm = original_bloodstorm;
  puts("PASS: unclosed bloodstorm status color does not leak into plain room prose");

  free_string(ch->in_room->name);
  ch->in_room->name = str_dup("`WLocalMapTitle Amber Birch Copper Delta Emerald Fern Garnet Hazel Indigo Juniper Kestrel `RLongTitleEnd`x");
  ch->linewidth = 40;
  command(ch, do_look, "");
  assert_look_layout(ch, "LocalMapTitle", "DescriptionProbe.", false);
  for (const char *word : {"Amber", "Birch", "Copper", "Delta", "Emerald", "Fern",
                           "Garnet", "Hazel", "Indigo", "Juniper", "Kestrel", "LongTitleEnd"})
    assert(plain_text(ch->desc->outbuf).find(word) != std::string::npos);
  printf("WRAPPED LOOK SAMPLE\n%s\n", ch->desc->outbuf);

  free_string(ch->in_room->name);
  ch->in_room->name = str_dup("`WLocalMapTitle`/`YBreakLine `*OneBell`x");
  command(ch, do_look, "");
  assert_look_layout(ch, "LocalMapTitle", "DescriptionProbe.");
  const std::string break_text = plain_text(ch->desc->outbuf);
  const size_t second_line = break_text.find('\n') + 1;
  assert(break_text.find("BreakLine") >= second_line);
  assert(break_text.find("BreakLine") < break_text.find('\n', second_line));
  assert(break_text.find("OneBell") != std::string::npos);
  int bells = 0;
  for (const char *byte = ch->desc->outbuf; *byte; ++byte)
    if (*byte == '\a') ++bells;
  assert(bells <= 1);
  ch->linewidth = 20;
  char *probe_description = ch->in_room->description;
  ch->in_room->description = str_dup("A quiet test room.");
  command(ch, do_look, "");
  assert(!has_minimap(ch));
  free_string(ch->in_room->description);
  ch->in_room->description = probe_description;
  ch->linewidth = 80;

  // A real description already stored with line breaks must set the right
  // edge even when the player chooses a much wider terminal. Its hard-wrapped
  // source lines reflow beside the map without losing words or adding gaps.
  ROOM_INDEX_DATA *probe_room = ch->in_room;
  place(ch, 9385);
  SET_BIT(ch->in_room->room_flags, ROOM_LIGHTON);
  REMOVE_BIT(ch->in_room->room_flags, ROOM_DARK | ROOM_UNLIT);
  assert(ch->in_room->description && strstr(ch->in_room->description, "plaster"));
  char *unpadded_description = ch->in_room->description;
  std::string padded_description;
  for (const char *byte = unpadded_description; *byte; ++byte) {
    if (*byte == '\n') padded_description.append(12, ' ');
    padded_description += *byte;
  }
  ch->in_room->description = str_dup(padded_description.c_str());
  for (int width : {80, 120, 320}) {
    ch->linewidth = width;
    const size_t prose_width = description_width(ch);
    assert(prose_width < static_cast<size_t>(width));
    command(ch, do_look, "");
    assert_look_layout(ch, "repentance house", "The plaster");
    printf("PASS: stored room 9385 prose width %zu caps minimap at configured width %d\n",
           prose_width, width);
    if (width == 80) printf("REPENTANCE HOUSE LOOK SAMPLE\n%s\n", ch->desc->outbuf);
  }
  free_string(ch->in_room->description);
  ch->in_room->description = unpadded_description;
  place(ch, probe_room->vnum);
  ch->linewidth = 80;

  // Brief automatic looks retain a compact header but suppress the room prose;
  // explicit look still shows the description and flowing map layout.
  SET_FLAG(ch->comm, COMM_BRIEF);
  command(ch, do_look, "auto");
  assert(has_minimap(ch));
  assert(plain_text(ch->desc->outbuf).find("+-----------+") + 13 <= description_width(ch));
  assert(!strstr(ch->desc->outbuf, "DescriptionProbe."));
  command(ch, do_look, "");
  assert_look_layout(ch, "LocalMapTitle", "DescriptionProbe.");
  REMOVE_FLAG(ch->comm, COMM_BRIEF);

  command(ch, do_map, "off");
  assert(IS_FLAG(ch->comm, COMM_NOMINIMAP) && ch->wait == map_wait);
  for (const char *look : {"", "auto", "north"}) {
    command(ch, do_look, look);
    assert(!has_minimap(ch));
    assert(strstr(ch->desc->outbuf, "DescriptionProbe."));
  }
  command(ch, do_map, "local");
  assert(strstr(ch->desc->outbuf, "help map"));
  command(ch, do_map, "");
  assert(strstr(ch->desc->outbuf, "help map"));

  // Verify the real serializer/loader preserves both minimap preference states.
  SET_FLAG(ch->comm, COMM_CARDINAL);
  save_char_obj(ch, FALSE, FALSE);
  DESCRIPTOR_DATA *loaded_off = new_descriptor();
  assert(load_char_obj(loaded_off, ch->name));
  assert(IS_FLAG(loaded_off->character->comm, COMM_NOMINIMAP));
  assert(IS_FLAG(loaded_off->character->comm, COMM_CARDINAL));
  command(ch, do_map, "toggle");
  assert(!IS_FLAG(ch->comm, COMM_NOMINIMAP));
  save_char_obj(ch, FALSE, FALSE);
  DESCRIPTOR_DATA *loaded_on = new_descriptor();
  assert(load_char_obj(loaded_on, ch->name));
  assert(!IS_FLAG(loaded_on->character->comm, COMM_NOMINIMAP));
  assert(IS_FLAG(loaded_on->character->comm, COMM_CARDINAL));
  command(ch, do_look, "");
  assert(has_minimap(ch));
  REMOVE_FLAG(ch->comm, COMM_CARDINAL);
  free_string(ch->in_room->name);
  free_string(ch->in_room->description);
  ch->in_room->name = original_title;
  ch->in_room->description = original_description;
  puts("PASS: flowing look/auto/directional placement, prose-aligned width, colored title wrapping, brief/narrow views, saved on/off toggle");

  command(ch, do_map, "key");
  assert(strstr(ch->desc->outbuf, "LOCAL MAPS"));
  assert(strstr(ch->desc->outbuf, "STAIRS AND VERTICAL ROUTES"));
  assert(strstr(ch->desc->outbuf, "map off") && strstr(ch->desc->outbuf, "map on"));
  assert(strstr(ch->desc->outbuf, "map toggle"));
  command(ch, do_help, "minimap");
  assert(strstr(ch->desc->outbuf, "help map"));
  assert(strstr(ch->desc->outbuf, "map off") && strstr(ch->desc->outbuf, "map on"));
  assert(strstr(ch->desc->outbuf, "map toggle"));

  ch->pcdata->sleeping = 1;
  command(ch, do_look, "");
  assert(!has_minimap(ch));
  ch->pcdata->sleeping = 0;
  SET_FLAG(ch->comm, COMM_BLINDFOLD);
  command(ch, do_map, "local");
  assert(!strstr(ch->desc->outbuf, "help map"));
  command(ch, do_look, "");
  assert(!has_minimap(ch));
  REMOVE_FLAG(ch->comm, COMM_BLINDFOLD);
  SET_FLAG(ch->act, PLR_DEEPSHROUD);
  command(ch, do_map, "local");
  assert(!strstr(ch->desc->outbuf, "help map"));
  command(ch, do_look, "");
  assert(!has_minimap(ch));
  puts("PASS: real look/auto/map/help integration, no added command wait, visibility gates");

  // Exercise the actual combat-map command and visibility/output pipeline too.
  REMOVE_FLAG(ch->act, PLR_DEEPSHROUD);
  char_list.push_front(ch);
  register_live_character(ch);
  set_combat_state(ch, true);
  MOB_INDEX_DATA *prototype = get_mob_index(45018);
  assert(prototype);
  CHAR_DATA *opponent = create_mobile(prototype);
  char_to_room(opponent, ch->in_room);
  set_combat_state(opponent, true);
  ch->cfighting = opponent;
  ch->facing = DIR_NORTH;
  ch->x = ch->y = 25;
  opponent->x = opponent->y = 26;
  ch->mapcount = opponent->mapcount = 987;
  const haven::CombatMapSnapshot actors = haven::combat_map_snapshot(ch);
  bool target_visible = false;
  for (const auto &actor : actors.entries) {
    if (actor.character == opponent) {
      assert(actor.label.compare(0, 2, "`M") == 0);
      target_visible = true;
    }
  }
  assert(target_visible);
  ch->wait = 0;
  command(ch, do_map, "");
  assert(strstr(ch->desc->outbuf, "help combat map"));
  assert(strstr(ch->desc->outbuf, "Me"));
  assert(ch->wait == PULSE_PER_SECOND * 3);
  assert(ch->mapcount == 987 && opponent->mapcount == 987);
  printf("COMBAT MAP WORLD SAMPLE\n%s\n", ch->desc->outbuf);
  command(ch, do_map, "key");
  assert(strstr(ch->desc->outbuf, "COMBAT MAP"));
  assert(strstr(ch->desc->outbuf, "OBJECTIVES"));
  command(ch, do_help, "combat map");
  assert(strstr(ch->desc->outbuf, "three-second"));
  command(ch, do_map, "local");
  assert(strstr(ch->desc->outbuf, "help map"));
  command(ch, do_look, "");
  assert(has_minimap(ch));
  assert(!strstr(ch->desc->outbuf, "986 others"));
  ch->wait = 0;
  command(ch, do_map, "off");
  assert(IS_FLAG(ch->comm, COMM_NOMINIMAP) && ch->wait == 0);
  command(ch, do_look, "");
  assert(!has_minimap(ch));
  command(ch, do_map, "");
  assert(strstr(ch->desc->outbuf, "help combat map"));
  assert(ch->wait == PULSE_PER_SECOND * 3);
  command(ch, do_map, "local");
  assert(strstr(ch->desc->outbuf, "help map"));
  puts("PASS: loaded combat map/target/help, preserved command delay, fresh counts and local map during combat");

  // Use a production cover prototype and the actual ANSI output pipeline.
  MOB_INDEX_DATA *cover_prototype = get_mob_index(110);
  assert(cover_prototype && IS_FLAG(cover_prototype->act, ACT_COVER));
  CHAR_DATA *cover = create_mobile(cover_prototype);
  char_to_room(cover, ch->in_room);
  set_combat_state(cover, true);
  cover->x = ch->x;
  cover->y = ch->y;
  assert(is_in_cover(ch) && is_in_cover(opponent));
  const haven::CombatMapSnapshot sheltered = haven::combat_map_snapshot(ch);
  bool saw_cover = false, sheltered_viewer = false;
  for (const auto &entry : sheltered.entries) {
    if (entry.character == cover) {
      assert(entry.is_cover && entry.label == "`C[]`x");
      saw_cover = true;
    }
    if (entry.character == ch) {
      assert(entry.cover_entry >= 0 && entry.label == "`W<u>Me</u>`x");
      assert(sheltered.entries[entry.cover_entry].character == cover);
      sheltered_viewer = true;
    }
  }
  assert(saw_cover && sheltered_viewer);
  const char *styled_markers = "`W<u>Me</u>`x `C[]`x";
  auto rendered = [&](const char *text, int mode) {
    Buffer buffer;
    char *result = tyr_lor(buffer, text, ch->desc, mode);
    const std::string copy(result);
    free_string(result);
    return copy;
  };
  assert(rendered(styled_markers, COLOR_LENGTH) == "5");
  assert(rendered(styled_markers, COLOR_NOCOLOR) == "Me []");
  const std::string ansi_markers = rendered(styled_markers, COLOR_COLOR);
  assert(ansi_markers.find("\033[4mMe\033[24m") != std::string::npos);
  assert(ansi_markers.find("<u>") == std::string::npos);
  assert(rendered("`W2 < 3 and 5 > 4`x", COLOR_NOCOLOR) == "2 < 3 and 5 > 4");
  ch->desc->mxp = TRUE;
  const std::string mxp_markers = rendered(styled_markers, COLOR_COLOR);
  assert(mxp_markers.find("<u>Me</u>") != std::string::npos);
  ch->desc->mxp = FALSE;
  REMOVE_FLAG(ch->act, PLR_COLOR);
  assert(rendered(styled_markers, COLOR_COLOR) == "Me []");
  SET_FLAG(ch->act, PLR_COLOR);
  command(ch, do_map, "");
  assert(plain_text(ch->desc->outbuf).find("In cover:") != std::string::npos);
  assert(plain_text(ch->desc->outbuf).find("[Cover]") != std::string::npos);
  assert(strstr(ch->desc->outbuf, "\033[4m"));
  printf("COMBAT COVER WORLD SAMPLE\n%s\n", ch->desc->outbuf);
  cover->x += 8;
  cover->y += 8;
  assert(!is_in_cover(ch) && !is_in_cover(opponent));
  command(ch, do_map, "");
  assert(plain_text(ch->desc->outbuf).find("In cover:") == std::string::npos);
  assert(plain_text(ch->desc->outbuf).find("[Cover]") != std::string::npos);
  command(ch, do_map, "key");
  assert(strstr(ch->desc->outbuf, "COVER AND TURRETS"));
  assert(strstr(ch->desc->outbuf, "Underlined character markers"));
  puts("PASS: actual cover flags, engine proximity rules, ANSI underlining, named cover, movement refresh and loaded help");
}
