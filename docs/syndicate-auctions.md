# Syndicate auctions

`commit syndicate <target>` hands another bound player in the same room over
to the syndicate. Faction and society members can be handed over; membership
protects them from random abductions only. Self-handover, NPCs, combat and
handover from the nightmare are rejected.

The seller receives 50% of the final price in their bank account when the buyer
pays and collects the prisoner. Amounts are calculated in cents, so a $301 sale
pays $150.50. The seller and prisoner can be offline at collection. The buyer's
balance is checked again, and collection identifies the specific prisoner and
auction rather than taking whoever is in the cell.

All three capture paths (random abduction, Cortex handover and player handover)
use the same auction setup. Every valid society receives a scout report,
regardless of its scout attribute or online membership. Eligible diplomatic
patrollers also receive invitations. Other characters can attend and use
`patrol bid <amount>` while bidding is open. Sellers cannot bid on their own
consignments. Bidding lasts 15 minutes; collection is available for 30 minutes
after winning. Bids replace earlier bids and are paid on collection.

Prisoners enter the cell without hand or foot bindings. Both cells have a fixed
landline usable with `call <number>` and block nightmare entry, pulls and entry
from adjoining nightmare rooms. Purchased prisoners are bound for delivery.
The detention deadline is 24 real hours after capture and is saved with the
player. Winning an auction does not shorten it. Unsold or uncollected prisoners
are released into the forest when it expires; offline prisoners are released
on login. Existing saves without a deadline receive one when first updated.

Run from WSL/Linux in the repository root:

```sh
make -C src -j4
python3 tools/test_syndicate.py
python3 tools/test_world_changes.py --enforcers-only
python3 tools/test_dissent_public.py
```

The integration suites boot disposable copies of the world and never write
live character saves. They cover membership immunity, player handover,
societies without scouts, phone calls, nightmare wards, bid replacement,
insufficient funds, offline settlement, unrelated cell visitors, duplicate
collection, saved auction state and the 24-hour release boundary.
