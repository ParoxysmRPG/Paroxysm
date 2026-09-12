from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_bytes().decode('latin1').replace('\r\n', '\n')


def write(name, text):
    p = ROOT / name
    crlf = b'\r\n' in p.read_bytes()
    p.write_bytes(text.replace('\n', '\r\n' if crlf else '\n').encode('latin1'))


renames = {'SKILL_CHAND':'SKILL_CCORTEX', 'SKILL_CTEMPLE':'SKILL_CSCUM',
           'CONTACT_HAND':'CONTACT_CORTEX', 'CONTACT_TEMPLE':'CONTACT_SCUM',
           'HAND_LT':'CORTEX_LT', 'HAND_SOLDIER':'CORTEX_SOLDIER',
           'TEMPLE_LT':'SCUM_LT', 'TEMPLE_SOLDIER':'SCUM_SOLDIER'}
for p in list((ROOT / 'src').glob('*')) + list((ROOT / 'tools').glob('test_*.py')):
    if p.suffix not in ['.c', '.h', '.cc', '.py']: continue
    name = str(p.relative_to(ROOT)); s = read(name); updated = s
    for old, new in renames.items(): updated = updated.replace(old, new)
    if updated != s: write(name, updated)
s = read('src/tables.c')
s = re.sub(r'(\{SKILL_CCORTEX,\s*)"Hand"', r'\1"Cortex"', s)
s = re.sub(r'(\{SKILL_CSCUM,\s*)"Temple"', r'\1"Scum"', s)
write('src/tables.c', s)
s = read('src/world.c')
s = s.replace('str_cmp(arg2, "hand")', 'str_cmp(arg2, "cortex")').replace('str_cmp(arg2, "temple")', 'str_cmp(arg2, "scum")')
s = s.replace('hand/order/temple', 'cortex/order/scum')
# Keep historical file keys: these are storage schema, not faction names.
s = s.replace('        KEY("Hand",', '        // Legacy save key for Cortex influence.\n        KEY("Hand",', 1)
s = s.replace('        KEY("Temple",', '        // Legacy save key for Scum influence.\n        KEY("Temple",', 1)
write('src/world.c', s)
# These two labels predate the new names and are only used in disabled map code.
s = read('src/map.c').replace('COLOUR_HAND', 'COLOUR_CORTEX').replace('COLOUR_TEMPLE', 'COLOUR_SCUM')
s = s.replace('COLOUR_CORTEXTEMPLE', 'COLOUR_CORTEXSCUM').replace('COLOUR_ORDERTEMPLE', 'COLOUR_ORDERSCUM')
s = s.replace('str_prefix("Hand",', 'str_prefix("Cortex",')
write('src/map.c', s)
