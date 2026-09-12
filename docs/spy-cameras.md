# Spy cameras

`plantcamera <phone>` consumes a spy camera and links recordings to that
phone's exact number. One active installation per room/number is allowed;
duplicates and invalid installations do not consume the item.

Lifetime is **one real week per effective Hacking point at installation**,
with a one-week minimum and five-week maximum. Later skill changes do not
alter an existing timer. The planting response reports the duration.

Expiry and bugsweeping remove each installation and send its planter a saved
player message naming the room and linked number. Online planters see it
immediately; offline planters receive it through the normal saved-message
system. A bugsweep reports that the camera was found and destroyed. Passive
wireless-signal detection does not destroy a camera or identify its planter.
Random short-outs have been removed.

The existing room `!bugs` metadata stores `number:expiry:planter`, with expiry
in Unix seconds. Normal area saves persist planting, removal, and migration,
including camera metadata beyond the ordinary 20-description save limit.
Expiry is checked every minute, even in empty rooms, and before recording,
detecting, planting, or sweeping. Expired cameras stop delivering at the
deadline; notifications may arrive up to a minute later.

Old number-only installations receive a one-week timer on first processing.
Their planter was never stored, so removal notices can only reach a loaded
linked phone's holder. New installations retain the planter for offline
notifications. Existing timestamps are never reset on restart.

Public rooms, school rooms, excluded areas, and locations outside Haven reject
installation. Darkness and mist pause recordings without changing the timer.
Reception requires a powered phone carried directly or inside unstashed nested
containers, with cell signal. The shared 16,000-character text inbox accepts
whole recordings only; clear space to resume a full inbox. Missed recordings
are not replayed. Long emotes cannot overflow the rendering buffer.

Regression checks (WSL/Linux):

```sh
python3 tools/test_spy_cameras.py
make -C src -j4
python3 tools/test_phone_delivery.py
```

The focused suite executes production camera code under ASan/UBSan. The engine
suite uses a disposable world and verifies online/offline saved notices as
well as phone delivery.
