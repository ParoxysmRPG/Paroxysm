# Prisoner sanctuary rescue

The prisoner-care block in `time_update()` is restored from the local
`HavenRPGOpenSource` checkout, commit `145f5f7` (`src/update.c`, originally
lines 3668–3692). The existing `autorelease()` implementation is unchanged.

The original rules apply to characters in Gravesend (`in_haven`) with full
sanctuary (`under_understanding(ch, ch)`), while no cleanse is active, who
are hand-bound, foot-bound, or in a room considered trapped by `trapped_room`.
Current sanctuary eligibility restrictions still apply; limited sanctuary
alone does not qualify.

- On the first qualifying update with `prison_mult == 0`, the multiplier
  becomes 1 and the care deadline is set to five hours ahead.
- Rescue occurs on an update strictly after the deadline.
- `carefor` adds twelve hours to the later of the existing deadline and now,
  capped at twenty hours ahead. Its existing cost and multiplier rules remain.
- While the character does not qualify, the deadline rolls to fourteen hours
  ahead. This preserves the historical behavior rather than substituting the
  help text's simplified fourteen-hour description for the initial grace period.
- The original early-release event checks are retained: valid sanctuary-loss
  or cleanse events in either event slot qualify while neither their start
  nor end time has passed. Already-started events are skipped by this check.

`autorelease()` removes hand/foot bindings and blindfolds. Institute students
and clinic patients are taken to exercise room 16295. Elsewhere, the existing
routine relocates a designated prisoner individually; for other captivity it
relocates connected occupants of the same room via its original floor-opening
rescue. The independent public-room escape timer remains unchanged.

Run `python3 tools/test_prisoner_sanctuary.py` under Linux/WSL for the production
timer, care-deadline and release regression checks.
