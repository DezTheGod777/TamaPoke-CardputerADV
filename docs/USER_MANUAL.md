# User Manual — TamaPoke Cardputer ADV v0.9.0

Welcome to the full manual for **TamaPoke Cardputer ADV v0.9.0**. This fork keeps the original TamaPoke virtual-pet foundation while adding a large set of Cardputer-specific systems. The goal of this manual is to make sure new users can find the important features without having to read source code or discover every shortcut by accident.

For installation first, see [Installation](INSTALLATION.md). For a compact keyboard reference, see [Controls](CONTROLS.md).

---

## 1. What TamaPoke Cardputer ADV is

TamaPoke Cardputer ADV is an unofficial port/expansion of the original TamaPoke project for the M5Stack Cardputer ADV.

The original core remains recognizable:

- egg/starter lifecycle
- feeding and favorite berries
- joy, energy and hygiene care
- poop/bathing
- sleep/wake
- play/training
- Bond and streaks
- medals
- time-based levels
- evolution
- farewell/runaway lifecycle
- Gen-1 Pokédex

v0.9.0 adds personality, moods, customizable scenery, inventory/shop/economy, six additional games, Daily Life, deeper Pokédex history, a Save Manager, expanded audio/animations, local clock/calendar tools, on-demand Wi-Fi time sync and optional easter eggs.

---

## 2. Starting the firmware

After installing `TamaPoke-CardputerADV-v0.9.0.bin`, the firmware boots into the TamaPoke experience.

If you already have a v0.7-compatible pet journal on the SD card, v0.9.0 is designed to continue using it. If this is a fresh save, follow the starter/egg flow shown on screen.

A microSD card is strongly recommended because it stores the pet journal, PMD sprites and v0.9.0 auxiliary feature files.

---

## 3. The Home screen

Home is the main living habitat for your Pokémon.

You will normally see:

- your animated Pokémon
- habitat/background
- Food/Joy/Energy/Hygiene meters
- status/personality/mood information depending on current state
- current action buttons/menu areas
- battery meter during normal UI mode
- care-streak indicator when a streak exists
- occasional SAVE activity indicator

After about 30 seconds of no Home input, **clean terrarium mode** removes interface clutter so the habitat and Pokémon can remain visible. Any key returns to the normal Home interface.

The display timeout is separate from terrarium mode. If a timeout is enabled, the screen can eventually turn off after the configured duration.

### Home battery icon

The battery meter sits in the upper-right during normal UI views. Very low battery can generate a warning/event. The Clock/Calendar uses the same clean transparent visual treatment rather than an opaque battery plate.

### Care Streak icon

The small flame-like symbol near the upper-left is the **Care Streak** indicator. The number beside it is the current streak count; it is not a danger warning.

---

## 4. Essential Home shortcuts

The fastest way to use TamaPoke is through direct Home keys:

| Key | Feature |
|---|---|
| F | Feed |
| P | Play |
| L | Sleep/Wake |
| B | Bath/Clean |
| D | Pokédex |
| I | Pet information |
| E | Evolve when ready |
| G | Farewell/Runaway when available |
| H | TamaPoke Hub |
| C | Home Customize |
| V | Inventory/Bag |
| K | Poke Shop |
| M | Minigames |
| Y | Daily Life |
| J | Pokédex History |
| O | Save Manager |
| Q | Pokémon cry |
| T | Clock/Calendar |
| S | Sound toggle |
| 1 | Toggle Home header |

Use Up from Home for pet-card/status information and Down for Settings.

---

## 5. TamaPoke Hub

Press **H** to open the central feature menu.

The release calls this screen **TAMAPOKE HUB**.

Entries:

- Home Customize
- Inventory / Bag
- Poke Shop
- Minigames
- Daily Life
- Pokédex History
- Save Manager
- Back

The Hub exists so users do not have to memorize every shortcut. Shortcuts remain available for experienced users.

---

## 6. Feeding and favorite berries

Press **F** from Home to feed the Pokémon.

Berry color matters because each Pokémon has a favorite-berry behavior inherited from the original TamaPoke mechanics. A favorite berry provides better care results and adds **+2 Bond**.

v0.9.0 also includes berries as Inventory/Shop items. Using a berry from Inventory invokes the same pet feeding behavior rather than creating a completely separate care system.

Treats/candy provide another feeding option.

Ordinary care/feeding can award coins, but the v0.9.0 economy caps the ordinary daily care-coin source so it cannot be farmed infinitely.

---

## 7. Bathing and poop

Press **B** to clean/bathe where applicable.

Cleaning:

- clears poop
- restores hygiene strongly
- provides a small Bond gain

The live poop frequency intentionally follows original TamaPoke behavior. v0.9.0 redesigned the icon into a small faceless Tamagotchi-style swirl with a complete dark outline and subtle motion, but did not intentionally increase the poop roll.

---

## 8. Sleep and wake

Press **L** to sleep/wake when allowed.

During sleep:

- energy recovers
- needs decline more slowly and have safety floors
- normal awake poop generation does not run
- the scene is forced to night
- the Pokémon displays a comic-style Z trail near its sprite

Sleeping does not stop time-based leveling.

---

## 9. Levels and evolution

Levels are still based on real time, not XP.

- 1 real minute = 1 in-game minute
- +1 level every 60 real minutes

Good care does not directly grant extra levels. Games do not award XP levels.

Evolution requires the original species path/level plus acceptable care conditions. Care mistakes can delay the level threshold.

When evolution is ready, press **E** and follow the confirmation flow.

v0.9.0 improves the visual evolution presentation with silhouette/reveal/sparkle effects while keeping the original progression rules.

### Evo Charm

The Shop sells an **Evo Charm**. It does not bypass evolution level/path.

When eligible it can:

- remove one care mistake
- raise Food/Joy/Energy/Hygiene to at least 50
- open the normal evolution dialog if those repairs make evolution ready

If the species is still under-level, the item cannot force an evolution.

---

## 10. Bond

Bond is shown on a 0–100 scale and represents your relationship with the current Pokémon.

Typical Bond gains:

- favorite berry: +2
- play: +2
- training: +2
- clean: +1
- caress/pet: +1
- first qualifying care on a new local day: +4

Normal action-based Bond gain is capped at **+20 per local calendar day**. The first-care daily +4 is separate.

A severe neglect/care-mistake event can reduce Bond by 1 after its cooldown.

v0.9.0 specifically hardens Bond day-reset logic to use the local calendar and explicitly saves caress/pet gains.

Bond affects long-term care rewards such as future egg quality/shiny bonus and some Home decor unlocks.

---

## 11. Care streak

The first qualifying care action on a new valid local day advances the streak.

If the previous cared-for day was yesterday, the streak continues. If you skip calendar days, the current streak starts over.

Best streak remains tracked separately.

Milestone thresholds include 3, 7, 30 and 100 days.

---

## 12. Personality

v0.9.0 assigns a stable trait from the Pokémon's permanent hatch genes:

- Playful
- Bold
- Gentle
- Calm
- Curious
- Stubborn
- Lazy
- Affectionate
- Energetic
- Shy

The trait is intentionally stable through reboot and evolution.

It affects behavior selection and subtly influences need-decay. It is not a stat class that makes one Pokémon objectively superior.

---

## 13. Moods

Mood reflects current state. Possible moods include:

- Content
- Excited
- Bored
- Sleepy
- Hungry
- Lonely
- Proud
- Annoyed
- Sick
- Curious
- Affectionate
- Dirty

Urgent needs override normal personality/mood flavor so care problems remain visible.

---

## 14. Richer idle behavior

While healthy and awake, the pet can:

- wander
- pause quietly
- sit
- breathe
- pose
- nod
- hop
- briefly doze
- react to time of day
- react to habitat visuals
- use species-family signature behavior
- occasionally move into a foreground check-in

The final release preserves the stable Home pacing rather than making the pet constantly hyperactive.

---

## 15. Home Customize

Open with **C** or through the Hub.

Rows:

1. Background
2. Plant
3. Bed
4. Toy
5. Trophy
6. Decor

### Backgrounds

All release backgrounds are selectable without hidden unlock requirements:

- Auto
- Meadow
- Beach
- Forest
- Volcano
- Mountain
- Snow
- Starfield
- Dream

**Auto** follows the species habitat.

**Starfield** uses deep-space scenery with stars/nebula motion.

**Dream** uses a purple twilight scene with crescent moon, clouds, stars and horizon mist.

### Plant unlocks

- Sprout: Play high score ≥ 3
- Flower: Play high score ≥ 8
- Bonsai: total medals ≥ 3

### Bed unlocks

- Cushion: Bond ≥ 15
- Pokébed: Bond ≥ 40
- Cloud Bed: best streak ≥ 7

### Toy unlocks

- Ball: Play high score ≥ 5
- Ring: Strength Training high score ≥ 10
- Plush: registered Pokédex count ≥ 25

### Trophy unlocks

- Bronze: total medals ≥ 1
- Silver: total medals ≥ 4
- Gold: total medals ≥ 8

### Decor unlocks

- Rock: registered count ≥ 5
- Sign: best streak ≥ 3
- Lantern: Bond ≥ 60

Shop items can directly place certain variants even if you reached them through the economy route rather than the normal progression requirement.

---

## 16. Inventory / Bag

Press **V**.

The Bag displays your coin balance and stored items.

Items:

| Item | What it does |
|---|---|
| Red Berry | Feeds red berry |
| Blue Berry | Feeds blue berry |
| Green Berry | Feeds green berry |
| Treat | Candy/treat feeding |
| Medicine | Strong multi-need recovery and poop clear |
| Evo Charm | Repairs evolution readiness without bypassing level/path |
| Toy Box | Places Plush toy |
| Decor Box | Places Lantern decor |
| Style Ticket | Applies Flower + Pokébed styling |
| Lucky Charm | Joy/Energy boost and +3 Bond |

Egg/sleep/state restrictions can block use of some care items.

---

## 17. Poke Shop

Press **K**.

Prices:

| Item | Coins |
|---|---:|
| Red Berry | 3 |
| Blue Berry | 3 |
| Green Berry | 3 |
| Treat | 5 |
| Medicine | 8 |
| Evo Charm | 18 |
| Toy Box | 14 |
| Decor Box | 14 |
| Style Ticket | 12 |
| Lucky Charm | 20 |

The shop prevents purchases when you do not have enough coins or an item stack has reached its limit.

---

## 18. Coins

Coins are a v0.9.0 auxiliary currency.

They can come from:

- ordinary care/feeding reward source
- original Play/Training performance
- six v0.9.0 minigames
- daily reward
- daily event outcomes
- optional easter eggs

Ordinary care coins have anti-farming limits, while games and special events have their own reward logic.

---

## 19. Original Play and Strength Training

The original activities remain intact.

v0.9.0 adds coin rewards based on performance and uses the selected Home background in Play/Training where supported.

Play/Training still interact with original pet stats/care rather than being replaced by the new six-game menu.

---

## 20. Additional Minigames

Press **M** or use the Hub.

### Berry Catch

Move left/right to catch berries. Correct catches add score; falling speed rises with score.

### Reaction

Wait for GO and press Space/Enter quickly. Early presses are false starts. Five rounds are used.

### Memory Match

Watch a six-step arrow sequence, then reproduce it after the display phase.

### Poke Race

Tap Space/Enter repeatedly. The Pokémon's Speed stat contributes to progress per press.

### Target

Move with arrows, line up with the target, then press Space/Enter.

### Species Challenge

Respond to the changing arrow prompt.

Each game stores a persistent high score and awards coins after completion.

---

## 21. Daily Life

Press **Y** or choose Daily Life in the Hub.

Daily Life depends on a valid local date/time.

The screen shows information such as:

- current care streak and best streak
- daily reward state
- today's event
- time Together with the current Pokémon
- care-coin usage

Daily mechanics include:

- one daily reward with coin amount influenced partly by streak
- berry reward
- one random daily event
- morning/night greeting
- up to five ordinary care coins per valid day
- rare visitor chance through daily events
- anniversary reward

The Together counter uses actual pet age in full days.

---

## 22. Random Daily Events

Possible daily event names include:

- Found Berries
- Training Spark
- Cozy Nap
- Muddy Adventure
- Coin Treasure
- Rare Visitor
- Quiet Day

Events can award items/coins or modify care values. Rare Visitor can briefly display special Gen-1 species such as legendary birds, Dragonite or Mew/Mewtwo-class visitors depending on the event table.

A visitor does not replace your current Pokémon.

---

## 23. Pokédex

Press **D** for the ordinary Gen-1 Pokédex.

The Cardputer fork includes an improved detail view with animated preview, rarity/habitat/stat/evolution information, shiny treatment and current/raised status.

The original registered/shiny registration core remains part of the pet save.

---

## 24. Pokédex History

Press **J** from Home or choose it in the Hub.

This newer layer records additional long-term information per species in a separate SD file.

Tracked history includes categories such as:

- raised history
- shiny history
- highest level
- minutes/time raised
- medals earned while raising
- favorite status
- evolution history

Use Left/Right to change pages where shown and F to toggle favorite on the supported page.

---

## 25. Save Manager

Press **O** or use the Hub.

The Save Manager provides:

- live A/B journal integrity check
- Backup Slots 1–3
- Restore Slots 1–3

### Checking integrity

Use **Check Live Integrity** to see whether the A and B journal copies validate.

### Creating a backup

Choose Backup Slot 1, 2 or 3. The manager copies valid journal data and associated v0.9.0 subsystem files where they exist.

### Restoring

Restore requires **double Enter**. The first confirmation arms the restore. The second performs it. A successful staged restore validates the result and restarts the Cardputer ADV.

See [Saves & Recovery](SAVES_AND_RECOVERY.md) before experimenting with save files manually.

---

## 26. Recent Events

Settings includes a Recent Events view.

The bounded event history records useful milestones/status events such as:

- levels
- Pokédex discoveries
- medals
- records
- care mistakes
- Bond/streak events
- renames
- evolution
- daily rewards/events
- save-manager status
- secrets/easter eggs

The exact list depends on what has happened on your save.

---

## 27. Clock / Calendar

Press **T** from Home or open it from Settings.

The final hardware-approved clock screen displays:

- live 12-hour time
- seconds
- AM/PM
- weekday
- full date such as `September 5, 2026`
- battery indicator
- original PMD Gastly, Haunter and Gengar sprites

The custom hand-drawn ghost art used in early testing was removed; the final screen uses the original Pokémon PMD assets.

The screen does not connect to Wi-Fi just because you open it.

---

## 28. Set Date / Time

Use this when you want fully offline timekeeping.

**Settings → Set Date / Time**

Controls:

- Left/Right: select field
- Up/Down: edit
- Enter/Space: save
- Esc: cancel

Fields:

- Year
- Month
- Day
- Hour
- Minute

Leap-year/month-day limits are handled by the editor.

The clock display uses 12-hour AM/PM format even though date/time calculations use normal system time internally.

---

## 29. Wi-Fi Time Sync

Open **Settings → Wi-Fi Time Sync**.

The final release uses on-demand Wi-Fi only.

### First connection

1. Choose Scan For Networks.
2. Pick your SSID.
3. Enter the password.
4. Press Enter.
5. Wait for connection and NTP.
6. The firmware applies the clock correction and shuts Wi-Fi back down.

### Use Saved Wi-Fi

After one successful connection, the firmware stores the last successful network. Later, select **Use Saved Wi-Fi** to reconnect without retyping the password.

The final hardware-tested persistence system uses internal ESP32 Preferences first and a CRC-checked, device-bound SD fallback if needed.

### Privacy/security note

The SD fallback is device-bound/obfuscated for practical protection/reliability, but it should not be treated as strong encryption. Do not share the saved Wi-Fi file publicly.

---

## 30. Day/night cycle

The scene still follows original TamaPoke thresholds:

- 06:00–07:59 sunrise
- 08:00–17:59 daytime
- 18:00–19:59 sunset
- 20:00–05:59 night

Sleeping forces night.

The visual Home background and these clock windows are separate concepts.

---

## 31. Offline time behavior

The pet stores a last-seen timestamp. If the firmware later starts with a genuinely newer valid wall clock, it can apply bounded offline progression.

Catch-up is capped at approximately two weeks.

A completely powered-off Cardputer cannot continuously advance a software clock by itself. If no external/inherited clock advanced while powered down, the saved timestamp cannot know the real elapsed duration until the user/system provides a newer valid time.

Manual and on-demand network clock corrections are deliberately treated as clock corrections rather than surprise giant aging jumps.

---

## 32. Audio

Press **S** to toggle sound.

v0.9.0 adds event-based sounds for categories such as:

- hatch
- evolution
- medals
- farewell
- level
- sleep/wake
- shiny
- daily
- coin
- rare event
- species cry

Press **Q** from Home to hear the current Pokémon cry.

There is no looping background music or looping audio ambience.

---

## 33. Display controls

### G0 / BtnA

Manually toggles the display backlight.

### Display timeout

Settings choices:

- Off
- 30 seconds
- 1 minute
- 2 minutes
- 5 minutes

### Reset Display

Use this if display preferences become problematic. It does not intentionally erase pet progress.

---

## 34. Battery behavior

The Cardputer fork adds a compact battery meter and low-battery warning/event support.

Clean terrarium mode hides unnecessary overlays so the Pokémon scene remains uncluttered.

---

## 35. Shiny Pokémon

Shiny status remains part of the core lifecycle/Pokédex behavior.

v0.9.0 adds more visible shiny sparkle treatment and an optional late-game Ultra Shiny Aura reward.

Normal shiny sprite naming uses:

```text
/mons/psNNN.bin
```

with fallback behavior where available.

---

## 36. Egg/shiny care bonus

The next egg's shiny/rarity experience can be improved by good long-term care, especially Bond/streak and a proper farewell.

Approximate base shiny denominators before care bonus:

- ordinary new egg path: about 1/48
- proper farewell path: about 1/24

The care bonus can improve those odds while a floor prevents absurd values.

---

## 37. Farewell and runaway

The original lifecycle logic remains. The final stage is presented to the user rather than silently replacing the Pokémon in the background.

A properly completed farewell gives better next-egg care context than a bad runaway ending.

Use **G** when the relevant goodbye/runaway action becomes available and follow the dialog.

---

## 38. Secrets and easter eggs

Major visual features are not hidden behind obscure codes in the release.

- Starfield: normal background
- Dream: normal background
- 151 border: removed

There are still optional Mew Visitor, Mystery Gift and Ultra Shiny easter eggs. Read [Secrets & Unlockables](SECRETS.md) only if you want spoilers.

---

## 39. Save files

Core journal:

```text
/tamapoke_v7_a.bin
/tamapoke_v7_b.bin
```

New v0.9.0 systems are mostly separate files. Back up the **whole SD card** if you want to preserve every subsystem, not only the pet journal.

See [Saves & Recovery](SAVES_AND_RECOVERY.md) for the full file list.

---

## 40. Recommended first-day setup

For a new v0.9.0 user:

1. Install the normal v0.9.0 BIN.
2. Insert a FAT32 SD card with PMD sprites.
3. Confirm the pet loads.
4. Set Date/Time or run one Wi-Fi sync.
5. Open the Clock/Calendar to confirm local time.
6. Press H and explore the Hub.
7. Choose a Home background.
8. Check Inventory/Shop.
9. Try the six Minigames.
10. Open Daily Life.
11. Run Save Manager → Check Live Integrity.
12. Make Backup Slot 1 once you are satisfied the save is healthy.

---

## 41. Where to go next

- [Installation](INSTALLATION.md)
- [Controls](CONTROLS.md)
- [Gameplay](GAMEPLAY.md)
- [Features](FEATURES.md)
- [Saves & Recovery](SAVES_AND_RECOVERY.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Secrets & Unlockables](SECRETS.md) — spoilers
- [Changelog](../CHANGELOG.md)

If you are coming from the original TamaPoke, the most important thing to remember is that v0.9.0 adds many surrounding systems, but the core pet is still fundamentally **time-raised and care-driven**, not XP-grinded.
