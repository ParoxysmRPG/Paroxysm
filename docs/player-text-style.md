# Player-facing text

New helpfiles and command output should follow the surrounding game text.
`help Decorate`, the patrol event helps, and the existing society information
screen provide useful examples.

- Use cyan (`` `c ``) for help headings and syntax labels, green (`` `g ``)
  for syntax punctuation and argument delimiters, and bright white
  (`` `W ``) for commands. Argument names and ordinary prose return to the
  default color (`` `x ``).
- Match the labels of the screen receiving a new field. Society information
  uses a white colon; territory details use white field headings. Preserve
  meaningful warning and positive-effect colors.
- Wrap help prose at 78 visible columns, excluding color codes. Keep syntax
  alternatives on separate lines and indent continuation lines. Long menus
  should not become one paragraph.
- End highlighted text with a reset. Command output uses `\n\r`, matching
  adjacent messages; keep area files in their existing line-ending format.
- Keep formatting separate from command parsing, calculations, permissions,
  and saved data. Formatting-only help edits retain keywords, metadata, and
  wording.

The formatting pass updates eleven help entries: Affect, Affects, Guest
Progression, White Oak, Higher Powers, Monster Guests, Guest, Cauterize,
Compromised, Societies, and Territory Rewards. It also updates lifeforce,
guest, society/patron, Cortex quota, dissent, and territory reward output.

Verification uses the existing affect, dissent/public-combat, feeding, and
guest-progression suites, plus the release build. A comparison with the
starting help file checks all 1,180 entries for unchanged wording and metadata.
