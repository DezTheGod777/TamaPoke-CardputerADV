# TamaPoke Cardputer ADV

![TamaPoke Cardputer ADV](docs/tamapoke-cardputer-adv-banner.svg)

**TamaPoke Cardputer ADV** is an unofficial M5Stack Cardputer ADV port and expansion of [socquique/TamaPoke](https://github.com/socquique/TamaPoke). It keeps the original virtual-pet lifecycle, Gen-1 Pokédex, time-based leveling and v0.7-compatible pet journal while adding a large Cardputer-focused feature set: personality and moods, customizable homes, inventory/shop/economy, more minigames, Daily Life, deeper history, save backups, expanded audio/animation, a live Clock/Calendar, one-shot Wi-Fi time sync and more.

> **Current release target: v0.9.0 — hardware-approved on a physical M5Stack Cardputer ADV.**

## Download

For the public v0.9.0 release, use the normal firmware file:

**`TamaPoke-CardputerADV-v0.9.0.bin`**

The release attachment is the normal application firmware BIN and is suitable for M5 Launcher. Do not use the optional `full-flash` image unless you specifically know you need a complete flash image.

Before updating, back up the files on your microSD card—especially `/tamapoke_v7_a.bin` and `/tamapoke_v7_b.bin`.

## Documentation

The v0.9.0 fork has grown far beyond the original Cardputer port, so the repository now includes a full manual:

- **[Installation](docs/INSTALLATION.md)** — firmware installation, microSD setup, sprite files and first boot.
- **[Controls](docs/CONTROLS.md)** — complete keyboard/shortcut reference.
- **[User Manual](docs/USER_MANUAL.md)** — full walkthrough of the firmware and its menus.
- **[Gameplay Guide](docs/GAMEPLAY.md)** — leveling, evolution, care, Bond, streaks, personality, moods, Daily Life and lifecycle mechanics.
- **[Features](docs/FEATURES.md)** — what this fork adds over the original project.
- **[Saves & Recovery](docs/SAVES_AND_RECOVERY.md)** — save journal, backups, restore behavior and auxiliary files.
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — common installation, SD, sprite, clock and Wi-Fi problems.
- **[Secrets & Unlockables](docs/SECRETS.md)** — **spoilers** for optional hidden content.
- **[Changelog](CHANGELOG.md)** — release history and v0.9.0 changes.

## v0.9.0 highlights

### A more living Pokémon

Each Pokémon has a persistent temperament derived from its existing hatch genes. Ten traits are supported: **Playful, Bold, Gentle, Calm, Curious, Stubborn, Lazy, Affectionate, Energetic and Shy**. Live moods include **Content, Excited, Bored, Sleepy, Hungry, Lonely, Proud, Annoyed, Sick, Curious, Affectionate and Dirty**.

Traits influence behavior and need-decay subtly, while urgent care needs always take priority. The Home habitat includes richer walking, poses, hops, short dozes, sky-watching, species-family reactions, time-of-day reactions and occasional foreground check-ins.

### Home Customize

Press **C** from Home or open **H → Home Customize**. Background choices include:

`AUTO · MEADOW · BEACH · FOREST · VOLCANO · MOUNTAIN · SNOW · STARFIELD · DREAM`

Starfield and Dream are normal selectable backgrounds in v0.9.0; neither requires a secret unlock. Furniture/decor categories include plants, beds, toys, trophies and decor, with additional variants earned through care, games, Bond, streaks, medals and Pokédex progress.

### Inventory, Poke Shop and coins

Press **V** for Inventory/Bag and **K** for the Poke Shop. The economy includes berries, treats, medicine, Evo Charm, Toy Box, Decor Box, Style Ticket and Lucky Charm. Coins are earned from care, games, Daily Life and special events.

### Six additional minigames

Press **M** or use the Hub:

- Berry Catch
- Reaction
- Memory Match
- Poke Race
- Target
- Species Challenge

High scores are saved to microSD and successful play awards coins.

### Daily Life

Press **Y** or choose Daily Life in the Hub. Once the clock is valid, Daily Life provides calendar-aware rewards, care-coin limits, random daily events, morning/night greetings, rare visitors, streak information and time-together tracking.

### Deeper Pokédex history

Press **J** from Home or select **Pokédex History** in the Hub. v0.9.0 records per-species history such as whether the species has been raised/shiny, highest level, time raised, medal history and evolution history, with favorite support.

### Save Manager

Press **O** or use the Hub. The Save Manager can check the live v7 journal, create three backup slots and restore a verified backup. Restores require a double-confirmation and restart the device after a successful staged restore.

### Clock / Calendar and time setup

Press **T** from Home or choose **Clock / Calendar** in Settings. The screen uses a 12-hour clock with live seconds, AM/PM, weekday and full date, plus original PMD sprites for Gastly, Haunter and Gengar.

Settings also includes **Set Date / Time** for fully offline use and **Wi-Fi Time Sync** for a one-shot NTP correction. Wi-Fi is not kept connected in the background; the radio is shut down after the sync attempt. After a successful connection, **Use Saved Wi-Fi** can reuse the saved network.

### Event-only audio

v0.9.0 adds more cries, jingles, evolution/level/sleep/wake/shiny/daily/coin/rare sounds and feedback. There is **no looping background music or audio ambience**.

## Original TamaPoke mechanics intentionally preserved

The fork does not turn progression into an XP grind. The original timing model remains:

- **1 real minute = 1 in-game minute.**
- A Pokémon gains **1 level per real hour**.
- Care does not directly accelerate levels.
- Care mistakes can delay evolution.
- Evolution still respects the species' normal path and level requirement.
- Offline aging is capped at approximately **two weeks** when a newer valid wall clock is available at startup.
- The original time-of-day windows remain: sunrise 06:00–07:59, daytime 08:00–17:59, sunset 18:00–19:59, night 20:00–05:59. Sleeping forces the night scene.

See [Gameplay Guide](docs/GAMEPLAY.md) for the full explanation.

## Quick controls

| Key | Action |
|---|---|
| Arrow keys | Navigate / select / game movement |
| Enter | Confirm / selected action |
| Space | Pet / game action / confirm where supported |
| F | Feed |
| P | Play |
| L | Sleep / wake |
| B | Bath |
| D | Pokédex |
| I | Pet info |
| E | Evolve when ready |
| G | Farewell / runaway when available |
| H | TamaPoke Hub |
| C | Home Customize |
| V | Inventory / Bag |
| K | Poke Shop |
| M | Minigames |
| Y | Daily Life |
| J | Pokédex History |
| O | Save Manager |
| Q | Pokémon cry |
| T | Clock / Calendar |
| N | Rename from Profile |
| S | Sound on/off |
| 1 | Toggle Home name/status header |
| Esc / Backspace | Back |
| G0 / BtnA | Manual display on/off |

The Cardputer's printed arrow keycaps (`; , . /`) are accepted directly without requiring Fn.

## Pokémon sprites on microSD

The repository does **not** bundle the Pokémon/PMD sprite pack. Put the generated TamaPoke/PMD files in a `mons` directory at the root of a FAT32 microSD card:

```text
/mons/p001.bin
...
/mons/p151.bin
/mons/ps001.bin
...
/mons/ps151.bin
```

Normal Pokémon use `pNNN.bin`; shiny Pokémon use `psNNN.bin` with normal-sprite fallback. The Clock/Calendar also uses the same original PMD sprite system for Gastly, Haunter and Gengar.

## Save compatibility

The primary pet save remains the v0.7-compatible alternating journal:

```text
/tamapoke_v7_a.bin
/tamapoke_v7_b.bin
```

v0.9.0 adds separate auxiliary files for new systems rather than changing the core pet journal. This preserves compatibility with existing v0.7-era pet progress. See [Saves & Recovery](docs/SAVES_AND_RECOVERY.md) for the complete file list.

## Building from source

The project uses PlatformIO and fetches a pinned upstream TamaPoke pet/dex source during the build.

```text
pio run -e m5stack-cardputer-adv
```

The normal release firmware produced by the build is:

```text
TamaPoke-CardputerADV-v0.9.0.bin
```

An optional complete flash image may also be generated as `TamaPoke-CardputerADV-v0.9.0-full-flash.bin`; it is not the normal release/install file.

## Credits and project relationship

- **Original TamaPoke:** [socquique/TamaPoke](https://github.com/socquique/TamaPoke)
- **Cardputer ADV port and v0.9.0 expansion:** [DezTheGod777](https://github.com/DezTheGod777)
- Pokémon/PMD artwork remains subject to its respective owners and PMD SpriteCollab licensing. Those assets are not bundled in this repository.
- The upstream license text is preserved in `LICENSE-UPSTREAM`.

This is an unofficial fan project and is not affiliated with Nintendo, Game Freak, The Pokémon Company or M5Stack.

## Release status

v0.9.0 has completed physical hardware testing and is approved for release preparation. The development history remains on `ultimate-v0.9.0` until the release PR is explicitly merged into `main`.
