# Compromised scheme and phone/text audit

Use `scheme type compromised` and
`scheme target <character name>`, then fill in the normal scheme description,
introduction and thwart method before launching. The scheme also works as
`typetwo`.

The default cost is 30,000 influence and the base duration is 48 hours, matching
Mute. Normal launch delay, duration modifiers, limited launches and thwarting
still apply. Existing event persistence stores the new type without changing
older event IDs.

While active, each successfully sent number text, text DM, group text or teletext
produces one extra copy for a random online player with a usable phone and enough
inbox space. Group texts produce one copy per send, rather than one per group
member. The sender and intended recipients are excluded, as are NPCs, dead
characters and GMs. If nobody is eligible, there is no copy. Multiple matching
schemes do not multiply the copies.

Copies identify the source phone number and say `(copied text)`; anonymous
teletexts retain `Unknown`. They are displayed and saved in the recipient's phone
inbox. Copies do not create conversation history, grant RP rewards or trigger
further copies. Failed, empty and moderation-suppressed texts do not trigger the
scheme. Photos are not text messages and do not trigger it.

## Audit fixes

- Group history now requires membership through the character's selected phone.
- Phone lookup checks the actual dialed number, including a second held phone,
  worn phones and phones inside containers. Wardrobe storage is excluded.
- Recipient ownership follows nested containers. Invalid/NPC recipients and
  missing DM matches are rejected before accessing player data.
- Number texts, group deliveries, DMs and teletexts check the complete incoming
  message against the 16,000-byte inbox limit before storing it. Ancillary text
  formatting is bounded. Call and text histories discard old entries safely.
- A receipt is rendered once for each delivery so its inbox, notification and
  recipient log agree during blackouts. Text history appends no longer use the
  legacy helper with ambiguous ownership; temporary color-stripping and sender
  strings no longer leak in these paths.
- Offline photo DMs are saved before unloading their recipients. Successful
  online number texts and teletexts are also saved immediately.
- `phone on` and `phone off` now honor the requested state. An off phone in
  inventory can be selected for powering on.
- Phone controls also select worn phones. Turning off the last usable phone
  ends an active call for both participants.
- Calls reject self-dialing and report unavailable numbers even when no matching
  object exists. Emergency calls select and notify a single responder only
  after the connection succeeds. Pickup rejects powered-off phones and stale
  connections; hangup cannot disconnect an unrelated call. Character extraction
  clears both the remaining caller's connection pointer and call stage.
- Signal boosting checks its cooldown without setting it first. Removing a boost
  unlinks and frees its extra description safely.
- Empty sends and failed DM/group deliveries receive useful feedback. Full
  sender inboxes no longer prevent reading conversation history.

## Loudspeaker

`phone loudspeaker` toggles the selected usable phone's loudspeaker;
`phone loudspeaker on` and `phone loudspeaker off` set it explicitly. The
setting is stored on the phone using its saved extra descriptions. It defaults
to off and persists until changed, independently of silent mode.

During a call, incoming `say`, `say to phone` and `telesay` speech also reaches
listeners in the receiving phone holder's room. The holder receives the normal
private call message once. Bystanders retain their own language comprehension
and hearing restrictions; the loudspeaker does not broadcast into other rooms.

Electropaths can use `phone <person> <command>` on another visible person in
the same room during that person's answered call. Supported controls are
`on`, `off`, `silent`, `loudspeaker [on/off]`, and `ringtone <string>`.
The electropath does not need their own phone. Both characters need a signal,
and blindness, dreaming, or a suppressed electropathy skill blocks control.
The target's call must still be connected at both ends; ringing and stale
connections do not qualify. Powering off the target's phone disconnects their
call, including when they carry a spare phone. The electropath's own phone,
call and camera state are unaffected. Shop services remain personal commands.

## Verification

Group text delivery builds one temporary lookup of loaded phone numbers for all
recipients, replacing a world-object scan per recipient. It retains first active
duplicate semantics and refreshes on each command, so power and inventory edits
are visible on the next send. Single-text and offline teletext commands reuse
their resolved phones throughout delivery. No phone pointer cache survives the
command. Offline group delivery keeps its temporary descriptor alive until the
recipient has been saved and unloaded; photo descriptors are initialized too.

Run in WSL/Linux from the repository root:

```sh
python3 tools/test_phones.py
make -C src -j4
python3 tools/test_phone_delivery.py
python3 tools/test_phone_delivery.py --sanitize
```

Build the sanitizer cache target described in
[runtime-hardening.md](runtime-hardening.md) before using `--sanitize`.
The first suite executes production helpers and phone controls under ASan/UBSan.
The second links the engine and boots a disposable copy of the world for text
delivery, call lifecycle and driving regression tests; it does not write live
player or account saves. The audit covers delivery, storage, lookup, calls and
phone controls; it is not a complete review of
the broader social/profile system or photo rendering.

The driving cases cover exhausted travel rooms, motorcycle passenger limits,
empty destinations, consistent driver/passenger routes under luring, and speed
controls. Drive/ride now skip missing travel rooms and fail before removing a
parked vehicle or cancelling an action if all travel rooms are occupied. Luring
resolves the destination before route validation and distance calculation, so
everyone in the vehicle receives the same destination and travel time. Ghost
possessors do not consume passenger capacity. Speed changes stay local while
parked, and horse passengers cannot override the driver's speed.

Driving still completes when pathfinding cannot find a route: its countdown is
at least two travel updates and arrival moves the occupants to the destination.
The integration suite verifies this with all exits from the origin disconnected.

Destination-based walking has a ten-minute elapsed-time limit per journey. On
the first walking update after ten minutes, a character still en route is moved
directly to the destination and walking stops, even if a movement wait is active.
Starting another walk or a new `walk around` leg resets the timer; stopping,
normal arrival and a failed path clear it. The timer is runtime-only, like the
walking destination. Invalid destinations (including `walk 0`) are rejected.
Run `python3 tools/test_walking.py` for focused ASan/UBSan deadline tests; the
engine integration suite also verifies arrival through the player update loop.
