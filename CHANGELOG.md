# Changelog

## v0.9.0 — Hardware-approved release

v0.9.0 is the largest Cardputer ADV expansion so far. It keeps the original TamaPoke pet journal and time-based progression while adding a broad set of new Cardputer-focused systems.

### Added

- Persistent gene-derived personality traits: Playful, Bold, Gentle, Calm, Curious, Stubborn, Lazy, Affectionate, Energetic and Shy.
- Live mood system: Content, Excited, Bored, Sleepy, Hungry, Lonely, Proud, Annoyed, Sick, Curious, Affectionate and Dirty.
- Richer idle life with species-family, habitat and time-of-day reactions.
- Foreground check-ins and broader PMD animation use.
- Home Customize screen.
- Background choices: Auto, Meadow, Beach, Forest, Volcano, Mountain, Snow, Starfield and Dream.
- Earned plants, beds, toys, trophies and decor.
- Inventory/Bag and Poke Shop.
- Coin economy and ten item types.
- Evo Charm that improves care/evolution readiness without bypassing species level/path.
- Six additional minigames: Berry Catch, Reaction, Memory Match, Poke Race, Target and Species Challenge.
- Persistent high scores for the new games.
- Daily Life calendar system with daily reward, events, greetings, care-coin limits, visitors, time-together and anniversary handling.
- Deeper per-species Pokédex history/favorite/evolution records.
- Three-slot Save Manager with live integrity check, backup and verified staged restore.
- Expanded event-driven audio: hatch/evolution/medal/farewell/level/sleep/wake/shiny/daily/coin/rare sounds and species cries.
- Additional evolution, shiny, recovery, sleep/wake and general animation polish.
- Clock / Calendar with 12-hour time, seconds, AM/PM, weekday and full date.
- Original PMD Gastly/Haunter/Gengar sprites on the Clock/Calendar screen.
- Full offline Year/Month/Day/Hour/Minute editor.
- One-shot Wi-Fi/NTP time sync.
- Case-sensitive Wi-Fi password entry.
- Saved Wi-Fi reuse with internal Preferences plus a device-bound SD fallback.
- `T` Clock shortcut and central `H` TamaPoke Hub.
- `Q` current Pokémon cry shortcut.
- Additional SD auxiliary files while preserving the v0.7 pet journal.

### Changed

- Public firmware branding is now simply **TamaPoke Cardputer ADV v0.9.0**; development `ULTIMATE` branding is removed from the user-facing release.
- Hub title is **TAMAPOKE HUB**.
- Public firmware filename is `TamaPoke-CardputerADV-v0.9.0.bin`.
- Starfield and Dream are ordinary selectable backgrounds instead of hidden unlocks.
- Dream background was redesigned with a layered twilight sky, crescent moon, stars, drifting clouds and mist.
- Play and Strength Training can use the selected Home background.
- Sleeping Z graphics are placed near the Pokémon instead of using a static corner label.
- Poop icon uses a modest faceless Tamagotchi-style swirl with a complete dark outline.
- Clock battery indicator uses the clean transparent style.
- Clock ghost artwork uses the original PMD sprites instead of custom drawings.
- Gastly/Haunter/Gengar clock layout was resized/rebalanced after physical hardware testing.
- Gengar was moved lower so the full-date line does not cover the sprite.
- Daily Together calculation now uses the current Pokémon's actual age in full days.
- Local-calendar Bond/streak logic was hardened to avoid UTC-day drift.
- Caress/pet Bond is explicitly saved.
- Wi-Fi menu input handling was restored after an earlier UI patch accidentally removed its handlers.
- Wi-Fi sync entry no longer touches the radio until a scan/saved connection is actually requested.
- Wi-Fi scans/connections are bounded and the radio is shut back down after sync.
- Stable Home animation cadence was restored so new personality behavior does not make the pet excessively active.

### Removed / retired

- 151 Master Border completely removed.
- `151` secret code retired.
- Old Starfield button-combination unlock retired.
- Dream is no longer gated by the `mew` word.
- Development-only Hub phase-count subtitle removed.
- Development-only Clock title removed.
- Experimental transition behavior that interfered with instant navigation removed.

### Preserved from original/stable behavior

- 1 real minute = 1 in-game minute.
- +1 level every real hour.
- Care does not directly accelerate leveling.
- Care mistakes can delay evolution.
- Species evolution path/level requirements remain intact.
- Offline catch-up remains capped at approximately 14 days when a genuinely newer valid wall clock is available.
- Original sunrise/day/sunset/night thresholds remain unchanged.
- Live poop roll remains the original 15% chance per awake real-minute tick when sufficiently fed, max three.
- v0.7-compatible `/tamapoke_v7_a.bin` and `/tamapoke_v7_b.bin` journal remains the core pet save.
- No looping background music/audio ambience is added.

### Hardware validation

The final v0.9.0 feature set was hardware-tested on a physical M5Stack Cardputer ADV and explicitly approved for release preparation.

---

## v0.8.5.4

Stable polish release before v0.9.0.

Highlights included:

- display timeout/black-screen race fix
- G0/BtnA display toggle
- battery meter and low-battery warning
- clean terrarium mode
- classic habitat renderer restoration
- graphical need meters
- SAVE indicator
- About/Version screen
- Recent Events
- Reset Display
- richer PMD idle behavior
- Gastly-line visual atmosphere
- improved evolution presentation
- deeper Pokédex detail screen
- shiny sparkle polish
- v0.7 save compatibility

Cyber Den was not included in the stable release.
