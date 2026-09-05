# Features — TamaPoke Cardputer ADV v0.9.0

This page summarizes what the Cardputer ADV fork adds while preserving the original TamaPoke core.

## Project scope

The project began as an M5Stack Cardputer ADV port of TamaPoke. v0.9.0 expands it into a much more complete handheld virtual-pet experience while intentionally keeping the original pet journal, level clock and evolution philosophy.

The upstream project remains the gameplay foundation. New Cardputer-specific systems are layered around it through separate configuration/history files whenever possible so older pet saves remain compatible.

## Hardware adaptation

The Cardputer ADV fork adds or adapts:

- 240×135 display layouts
- physical keyboard controls and shortcuts
- Cardputer arrow-key handling
- speaker audio
- battery meter and low-battery warning
- G0/BtnA manual display toggle
- configurable display timeout
- microSD pet journal and auxiliary persistence
- clean idle/terrarium mode
- one-shot Wi-Fi/NTP time synchronization

## Stable v0.8.5.4 foundation retained

v0.9.0 includes the previous stable polish work:

- black-screen/display-timeout race fix
- Off / 30 sec / 1 min / 2 min / 5 min timeout choices
- compact battery meter
- clean terrarium mode with no unnecessary HUD overlays
- classic TamaPoke habitat renderer
- graphical Food/Joy/Energy/Hygiene meters
- SAVE activity indicator during normal UI use
- About / Version screen
- Recent Events history
- Reset Display recovery option
- richer PMD animation use
- improved shiny presentation
- special Gastly/Haunter/Gengar atmosphere
- improved evolution presentation
- deeper normal Pokédex detail view

## v0.9.0 personality system

Each Pokémon receives one of ten stable traits derived from the hatch genes already stored in the existing pet journal:

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

The trait survives restart and evolution because species ID is not used as the permanent identity source.

## v0.9.0 mood system

The live condition system can display:

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

Care emergencies outrank personality flavor.

## Richer Home life

New Home behavior includes:

- broader walking/wandering
- richer idle-action selection
- species-family signature moments
- habitat-condition reactions
- morning/night reactions
- short dozes
- sky-watching and quieter pauses
- foreground check-ins
- trait-driven action preference

The underlying stable cadence was restored after development so the Home screen does not become hyperactive. Personality changes *which* action is preferred more than it changes the basic rhythm.

## Home Customize

Open with **C** or from the Hub.

Backgrounds:

- Auto
- Meadow
- Beach
- Forest
- Volcano
- Mountain
- Snow
- Starfield
- Dream

Starfield and Dream are regular public background options in the release. The earlier secret-gating experiments were retired during hardware testing.

Furniture/decor categories:

- Plant
- Bed
- Toy
- Trophy
- Decor

Variants are earned through care, Bond, streaks, minigame records, medals and Pokédex progress.

## Inventory and Poke Shop

Open Inventory with **V** and the Shop with **K**.

Inventory items:

- Red Berry
- Blue Berry
- Green Berry
- Treat
- Medicine
- Evo Charm
- Toy Box
- Decor Box
- Style Ticket
- Lucky Charm

The economy uses its own persistent coin/item file and does not change the core v0.7 pet journal format.

## Expanded minigames

Open with **M** or from the Hub.

v0.9.0 adds:

1. Berry Catch
2. Reaction
3. Memory Match
4. Poke Race
5. Target
6. Species Challenge

Each game has a persistent high score and awards coins. The original TamaPoke Play and Strength Training activities remain available as well.

## Daily Life

Open with **Y** or from the Hub.

Daily Life adds:

- calendar-aware daily reward
- berry reward
- care-coin anti-farming cap
- random daily event
- morning/night greeting
- care streak display
- time-together tracking
- rare visitor events
- adoption anniversary reward

A correct date/time is required for true local-calendar behavior.

## Deeper Pokédex History

Open with **J** or from the Hub.

The history layer tracks more long-term information per species, including raised/shiny history, highest level, time raised, medals/favorite state and evolution history. It lives in its own SD file instead of enlarging the core pet journal.

## Save Manager

Open with **O** or from the Hub.

Features:

- verify live A/B journal integrity
- three backup slots
- include important v0.9.0 auxiliary progress in backups
- double-confirm restore
- staged/verified restoration
- automatic restart after successful restore

## Audio upgrade

v0.9.0 adds more event-driven audio without turning TamaPoke into a continuously playing music app.

Supported event categories include:

- hatch
- evolution
- medal
- farewell
- level
- sleep/wake
- shiny
- daily reward
- coin reward
- rare event
- procedural/species cry

**No looping background music or looping audio ambience is added.**

## Animation polish

v0.9.0 adds or improves:

- evolution sparkles/reveal
- shiny presentation
- recovery/damage feedback
- sleep/wake effects
- comic-style sleeping Z trail
- more polished poop icon with a complete dark outline
- cleaned Play/Poké Ball icon

Development screen-transition experiments were removed where they interfered with the direct feel of the UI.

## Clock / Calendar

Open with **T** from Home or from Settings.

Features:

- 12-hour time
- live seconds
- AM/PM
- weekday
- full date
- transparent battery HUD treatment consistent with Home
- original PMD sprites for Gastly #092, Haunter #093 and Gengar #094

The clock screen itself never activates Wi-Fi.

## Offline/manual date and time

Settings includes a full Year/Month/Day/Hour/Minute editor. This lets the device run Daily Life and the day/night scenery without needing a permanent network connection.

## One-shot Wi-Fi time sync

Settings includes an on-demand network scan/password/NTP flow.

- Wi-Fi is activated only when the user requests a connection or scan.
- The radio is turned back off after the sync attempt.
- Password input preserves case and symbols.
- **Use Saved Wi-Fi** reuses the last successfully saved network.
- Saved-network persistence uses internal preferences plus a device-bound SD fallback for reliability.

## Bond and streak hardening

v0.9.0 keeps the intended Bond system but improves local-calendar correctness and persistence.

- normal action Bond awards use a +20/day anti-farming cap
- first qualifying care on a new local day awards +4 Bond and advances the streak
- neglect can remove a small amount of Bond
- Bond/streak day handling follows local time rather than raw UTC-day changes
- caress/pet Bond is explicitly saved so a reboot does not discard a recent gain

## Original progression preserved

v0.9.0 intentionally does **not** change the project into an XP system.

- +1 level per real hour remains
- evolution still follows species path/level
- care mistakes can delay evolution
- good care does not grant arbitrary extra levels
- Evo Charm repairs readiness but does not bypass the real species level/path
- offline catch-up remains bounded

## Background scene timing preserved

The original thresholds remain:

- sunrise: 06:00–07:59
- daytime: 08:00–17:59
- sunset: 18:00–19:59
- night: 20:00–05:59

Sleeping forces night.

## Secret-content cleanup after hardware testing

During development, Starfield, Dream and a 151 border were experimented with as secret unlocks. The release behavior is intentionally simpler:

- Starfield: normal selectable background
- Dream: normal selectable background
- 151 Master Border: completely removed
- old Starfield button combination: retired
- `151` code: retired/does nothing

Optional Mew/Mystery Gift/Ultra Shiny easter eggs remain. See [Secrets & Unlockables](SECRETS.md) for spoilers.

## Save compatibility philosophy

The core pet still uses:

```text
/tamapoke_v7_a.bin
/tamapoke_v7_b.bin
```

Most new v0.9.0 systems use separate auxiliary files. This is why existing v0.7-era pet progress can move into v0.9.0 without a wholesale pet-save migration.

## Not included

- Cyber Den is not part of the stable v0.9.0 release.
- The Pokémon/PMD sprite pack is not bundled.
- No cloud account is required.
- No background Wi-Fi connection is required.
- No looping background music/ambience is included.
