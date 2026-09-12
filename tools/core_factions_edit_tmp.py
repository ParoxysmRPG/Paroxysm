from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
def read(name): return (ROOT / name).read_bytes().decode('latin1').replace('\r\n', '\n')
def write(name, text):
    p = ROOT / name
    crlf = b'\r\n' in p.read_bytes()
    p.write_bytes(text.replace('\n', '\r\n' if crlf else '\n').encode('latin1'))
def section(s, start, end, replacement):
    a = s.index(start); b = s.index(end, a)
    return s[:a] + replacement + s[b:]
def remove_block(s, marker):
    a = s.index(marker); a = s.rfind('\n', 0, a) + 1
    brace = s.index('{', a); depth = 1; b = brace + 1
    while depth:
        if s[b] == '{': depth += 1
        elif s[b] == '}': depth -= 1
        b += 1
    if s[b:b+1] == '\n': b += 1
    return s[:a] + s[b:]

for p in list((ROOT / 'src').glob('*')) + list((ROOT / 'tools').glob('test_*.py')):
    if p.suffix not in ['.c', '.h', '.cc', '.py']: continue
    name = str(p.relative_to(ROOT)); s = read(name)
    new = s.replace('FACTION_HAND', 'FACTION_CORTEX').replace('FACTION_TEMPLE', 'FACTION_SCUM')
    new = new.replace('The Hand', 'The Cortex').replace('the Hand', 'the Cortex')
    new = new.replace('The Temple', 'The Scum').replace('the Temple', 'the Scum')
    if new != s: write(name, new)

s = read('src/clans.c')
# Stable faction IDs preserve memberships, bases, and saved support slots.
anchor = '  /*Local Functions */'
helpers = '''  void configure_core_faction(FACTION_TYPE *fac) {
    if (!fac) return;
    if (fac->vnum == FACTION_ORDER) {
      fac->closed = 1;
      return;
    }
    if (fac->vnum != FACTION_CORTEX && fac->vnum != FACTION_SCUM) return;
    const bool cortex = fac->vnum == FACTION_CORTEX;
    free_string(fac->name);
    fac->name = str_dup(cortex ? "The Cortex" : "The Scum");
    for (int axis = 1; axis <= AXES_MAX; ++axis) fac->axes[axis] = AXES_NEUTRAL;
    fac->axes[AXES_DEMOCRATIC] = cortex ? AXES_FARLEFT : AXES_FARRIGHT;
    fac->axes[AXES_SUPERNATURAL] = cortex ? AXES_FARRIGHT : AXES_MIDLEFT;
    if (cortex) fac->axes[AXES_CORRUPT] = AXES_FARLEFT;
    free_string(fac->description);
    fac->description = str_dup(cortex
        ? "The Cortex is a corrupt, authoritarian society strongly opposed to supernaturals. Its other ideological positions are neutral."
        : "The Scum is a strongly democratic society that moderately supports supernaturals. Its other ideological positions are neutral.");
    free_string(fac->manifesto);
    fac->manifesto = str_dup(cortex
        ? "The Cortex pursues power through corruption and authoritarian control. Its supernatural members are subject to faction chip control."
        : "The Scum champions democratic rule and supports supernatural participation.");
  }

  bool player_faction_join_allowed(CHAR_DATA *ch, FACTION_TYPE *fac, bool show) {
    if (!ch || !fac || fac->vnum == 0) return FALSE;
    if (!IS_NPC(ch) && fac->vnum == FACTION_ORDER) {
      if (show) send_to_char("The Order is not open to player membership.\\n\\r", ch);
      return FALSE;
    }
    return TRUE;
  }

'''
s = s.replace(anchor, helpers + anchor, 1)
s = s.replace('          FacVect.push_back(fac);', '          configure_core_faction(fac);\n          FacVect.push_back(fac);', 1)
s = s.replace('    if (fac->antagonist != 0)\n    return;\n\n    int i;', '    if (!player_faction_join_allowed(ch, fac, TRUE) || fac->antagonist != 0)\n      return;\n\n    int i;', 1)
s = s.replace('  void join_to_clan_two(CHAR_DATA *ch, int vnum) {\n    FACTION_TYPE *fac = clan_lookup(vnum);', '  void join_to_clan_two(CHAR_DATA *ch, int vnum) {\n    FACTION_TYPE *fac = clan_lookup(vnum);\n    if (!player_faction_join_allowed(ch, fac, TRUE)) return;')
s = s.replace('  bool can_join_faction(CHAR_DATA *ch, int faction, bool show) {', '  bool can_join_faction(CHAR_DATA *ch, int faction, bool show) {\n    if (!player_faction_join_allowed(ch, clan_lookup(faction), show)) return FALSE;')
s = s.replace('      if (ch->faction == 0 && ch->pcdata->lastidentity', '      if (!player_faction_join_allowed(ch, clan_lookup(clan_vnum_by_name(argument)), TRUE)) return;\n\n      if (ch->faction == 0 && ch->pcdata->lastidentity', 1)
s = s.replace('if (generic_faction_vnum(fac->vnum) || protected_faction_vnum(fac->vnum))\n    fac->closed = 0;', 'if (generic_faction_vnum(fac->vnum) || protected_faction_vnum(fac->vnum))\n    fac->closed = fac->vnum == FACTION_ORDER ? 1 : 0;')
# Do not retain the old factions' combat/arcane special restrictions on the
# renamed societies, whose combat/material axes are now explicitly neutral.
for faction in ['CORTEX', 'SCUM']:
    s = remove_block(s, f'      if (fac->vnum == FACTION_{faction}) {{')
    s = remove_block(s, f'            if (fac->vnum == FACTION_{faction} &&')
s = re.sub(r'    if \(fac->vnum == FACTION_(?:CORTEX|SCUM) &&[^\n]*\n    return FALSE;\n', '', s)
s = re.sub(r'          (?:if|else if)\(disp->vnum == FACTION_(?:CORTEX|SCUM)\)\n          printf_to_char\(ch, "`cRestrictions`x: [^\n]*\n', '', s)
s = s.replace('          else if(disp->vnum == FACTION_ORDER)', '          if(disp->vnum == FACTION_ORDER)')
# The supernatural axis now governs chip control, not status or LF penalties.
a = s.index('      if (fac->axes[AXES_SUPERNATURAL] == AXES_FARLEFT)')
b = s.index('    }\n\n    if (faction == ch->fcore)', a)
s = s[:a] + s[b:]
s = re.sub(r'    if \(fac->axes\[AXES_SUPERNATURAL\][^\n]*\n    return FALSE;\n', '', s)
for marker in ['if (!seems_super(member) && (fac->axes[AXES_SUPERNATURAL]', 'if (seems_super(member) && (fac->axes[AXES_SUPERNATURAL]']:
    s = remove_block(s, marker)
while re.search(r'    if \(\(get_real_age\(ch\).*AXES_SUPERNATURAL', s):
    s = remove_block(s, re.search(r'    if \(\(get_real_age\(ch\).*AXES_SUPERNATURAL', s)[0])
s = remove_block(s, 'if (fac->axes[AXES_CORRUPT] >= AXES_MIDRIGHT && fac->axes[AXES_SUPERNATURAL]')
s = s.replace('      send_to_char("`WThe Order\\n\\r`DThe Cortex\\n\\r`gThe Scum`x\\n\\n\\r", ch);', '      send_to_char("`DThe Cortex\\n\\r`gThe Scum`x\\n\\rThe Order (not open to player membership)\\n\\n\\r", ch);')
# Canonical command names; saved numeric IDs need no old command aliases.
s = s.replace('"Hand"', '"Cortex"').replace('"Temple"', '"Scum"').replace('Hand/Order/Temple', 'Cortex/Order/Scum')
s = s.replace('hand_divisions', 'cortex_divisions').replace('temple_divisions', 'scum_divisions')
s = s.replace('Peacekeeping Hand', 'Cortex Peacekeepers').replace('Shadow Hand', 'Cortex Shadows').replace('Whispering Hand', 'Cortex Intelligence')
s = s.replace('Temple Strike Force', 'Scum Strike Force').replace('Temple Intelligence', 'Scum Intelligence').replace('Temple Demolishers', 'Scum Demolishers')
# Operative creation/switching must not create new Order player memberships.
for start, end in [('  void create_ai_operative(', '  void become_operative('), ('  void become_operative(', '    char * oname = str_dup')]:
    a = s.index(start); b = s.index(end, a+len(start))
    part = s[a:b]
    needle = '    if(fac == NULL)'
    part = part.replace(needle, '    if (!player_faction_join_allowed(ch, fac, TRUE)) return;\n' + needle, 1)
    s = s[:a] + part + s[b:]
write('src/clans.c', s)

s = read('src/lookup.c')
a = s.index('  int clan_lifeforce_mod('); b = s.index('  int soc_lf_mod(', a)
part = s[a:b]
part = re.sub(r'      if \(fac->axes\[AXES_SUPERNATURAL\][^\n]*\n      val -= 10;\n', '', part)
part = section(part, '    if (fac->axes[AXES_SUPERNATURAL]', '    if (fac->axes[AXES_CORRUPT]', '')
s = s[:a] + part + s[b:]
write('src/lookup.c', s)

s = read('src/skills.c')
for faction in ['CORTEX', 'SCUM']:
    marker = re.search(r'        if\(skilltype\(skill_table\[i\].vnum\).*ch->fcore == FACTION_' + faction, s)
    if marker: s = remove_block(s, marker[0])
a = s.index('  int belief_match(')
b = s.index('    if (fac->axes[AXES_MATERIAL]', a)
start = s.index('    if (fac->axes[AXES_SUPERNATURAL]', a)
s = s[:start] + s[b:]
s = section(s, '  bool faction_slave(', '  _DOFUN(do_control)', '''  bool faction_chip_control(CHAR_DATA *ch, CHAR_DATA *victim) {
    if (!ch || !victim || ch == victim || IS_NPC(ch) || IS_NPC(victim)) return FALSE;
    const int memberships[][2] = {
      {ch->fcore, victim->fcore}, {ch->fcult, victim->fcult}, {ch->fsect, victim->fsect}
    };
    for (const auto &membership : memberships) {
      if (membership[0] == 0 || membership[0] != membership[1]) continue;
      FACTION_TYPE *fac = clan_lookup(membership[0]);
      if (!fac) continue;
      const int position = fac->axes[AXES_SUPERNATURAL];
      if (position == AXES_FARLEFT && seems_super(ch) && !seems_super(victim)) return TRUE;
      if (position == AXES_FARRIGHT && !seems_super(ch) && seems_super(victim)) return TRUE;
      // Retain corruption's existing tier-based control independently.
      if (fac->axes[AXES_CORRUPT] == AXES_FARLEFT && get_tier(ch) > 2 && get_tier(victim) <= 2) return TRUE;
      if (fac->axes[AXES_CORRUPT] > 0 && fac->axes[AXES_CORRUPT] <= AXES_NEARLEFT
          && get_tier(ch) > 1 && get_tier(victim) <= 1) return TRUE;
    }
    return FALSE;
  }

''')
s = s.replace('faction_slave(ch, rch)', 'faction_chip_control(ch, rch)')
write('src/skills.c', s)
s = read('src/comm.c').replace('"", "Hand", "Order", "Temple"', '"", "Cortex", "Order", "Scum"')
write('src/comm.c', s)
s = read('src/functions.h').replace('void normalize_alliance_data(void);', 'void configure_core_faction(FACTION_TYPE *fac);\nbool player_faction_join_allowed(CHAR_DATA *ch, FACTION_TYPE *fac, bool show);\nvoid normalize_alliance_data(void);')
write('src/functions.h', s)
