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
- Signal boosting checks its cooldown without setting it first. Removing a boost
  unlinks and frees its extra description safely.
- Empty sends and failed DM/group deliveries receive useful feedback. Full
  sender inboxes no longer prevent reading conversation history.

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
delivery tests; it does not write live player or account saves. The audit focused
on delivery, storage, lookup and phone controls; it is not a complete review of
the broader social/profile system or photo rendering.
