# Campus map and uniform shop

From Warden's Way (3970), go **west, west, up** to the Academy Uniform Shop
(18074). Open the reception door if it is closed. From Cortex Academy Reception
(16132), the shop is simply **up**. `list` shows stock; `buy <number>` purchases
an item. The academy outfitter (45018) is open all day.

Twenty wearable pieces (45020–45039) provide four coordinated color choices:

| Color | Trim | Pieces | Base prices |
| --- | --- | --- | --- |
| Royal blue | Gold | Blazer, trousers, skirt, tie | $35 / $20 / $20 / $6 |
| Emerald green | Gold | Blazer, trousers, skirt, tie | $35 / $20 / $20 / $6 |
| Plum purple | Silver | Blazer, trousers, skirt, tie | $35 / $20 / $20 / $6 |
| Burgundy red | Gold | Blazer, trousers, skirt, tie | $35 / $20 / $20 / $6 |

The remaining pieces are an ivory shirt ($12), teal sweater ($22), white knee
socks ($4), and black loafers ($18), all with gold detailing. Normal shop price
adjustments still apply. Students can choose any palette. The items have visible
color codes, descriptive text, clothing coverage and layers, and unlimited shop
stock. Mob/object templates live in `area/hvnshop.are`; their spawn and inventory
resets live with the shop room in `area/hvntown.are`.

## Map repairs and directions

- A two-way staircase now connects reception directly to the existing mezzanine
  above it, where the uniform shop operates. The older plaza stairs still work.
- A doorway south of the shop now reaches the cafeteria dining room. It was
  previously a solid glass boundary.
- The bookstore's sealed reference aisle (18089) and reading nook (9262) now
  connect to the main bookstore (18085) and union mezzanine (18072). They provide
  places to sit and study; the uniform shop has a fitting bench and counter.
- Public shops, cafeteria rooms, and two covered walkways no longer carry
  accidental darkness or bedroom flags. Three lawns beside the dormitories
  (16155, 15624, 9912) use park terrain instead of shallow water.
- Reception, the front walk, union plaza, courtyard, arts junction, and dormitory
  walkway have directions in their descriptions. `help campus map` and
  `help uniforms` give the main routes.

From reception, follow the plaza west to the Academy Courtyard (1732), then
continue west to the dormitory entrance (16156) and go up. From the courtyard,
the arts entrance (1430) is **five south, east**. The clinic and biodome are
north of the courtyard. See [student-dormitories.md](student-dormitories.md) for
the dorm houses and rental-room directory.

## Validation

The wider institute review and subsequent roof, house-room, and boundary
repairs are documented in [institute-map.md](institute-map.md).

After building the engine, run under Linux/WSL:

```sh
python3 tools/run_school_integration.py
python3 tools/run_dorm_integration.py
```

Both runners use disposable world copies. The school test exercises ordinary
student movement, all twenty purchases and wearable items, colored listings,
repeat purchases, restocking without duplicate keepers, and the repaired routes.
Restart the server to load the updated area files.
