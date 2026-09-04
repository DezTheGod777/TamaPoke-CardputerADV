# TamaPoke Cardputer ADV — v0.8.5.4

![TamaPoke Cardputer ADV v0.8.5.4](docs/tamapoke-cardputer-adv-v0.8.5.4.jpg)

An unofficial **M5Stack Cardputer ADV** port of the TamaPoke virtual Pokémon pet engine. The project keeps the original TamaPoke pet/evolution logic and adapts the experience to the Cardputer ADV's 240×135 display, keyboard, speaker, battery monitor and microSD.

> **Stable OG firmware line.** Cyber Den experiments are intentionally kept separate from this branch/version.

## v0.8.5.4 highlights

- Fixes the random black-screen bug caused by a stale loop timestamp racing a newer keyboard-activity timestamp.
- Keeps automatic display timeout choices: **Off / 30 sec / 1 min / 2 min / 5 min**.
- Removes `SCREEN OFF NOW` from Settings.
- **G0 / BtnA** now toggles the display backlight on/off manually.
- Any keyboard key still wakes a timed-out display without triggering an accidental game action.
- Small **battery meter** in the upper-right corner with low-battery color warning.
- Brief **SAVE** indicator after background persistence is flushed.
- Visible firmware version plus a dedicated **About / Version** screen.
- **Recent Events** page backed by `/tamapoke_events.log` on microSD.
- **Reset Display** recovery option resets brightness to 50% and timeout to 2 minutes without touching pet progress.
- **Terrarium idle mode** after 30 seconds on the Home screen: menus disappear and the Pokémon continues wandering/animating. Press any key to return. The normal configured screen timeout continues counting separately.
- Expanded PMD personality actions including pose, nod, breathing, sit and hop when those frames are available.
- Enhanced shiny sparkles in the Home screen and Pokédex detail view.
- Special purple spectral atmosphere for **Gastly #092, Haunter #093 and Gengar #094**.
- Existing evolution animation, habitats, bath effects, mini-games, pet cards, Pokédex and v0.7 save journal remain intact.

## Core TamaPoke features

- Bulbasaur / Charmander / Squirtle starter selection
- Egg tapping and hatching
- Hunger, joy, energy, hygiene, weight, bond and care mistakes
- Berries and candy
- Petting, sleep/wake and bathing
- Play and strength-training mini-games
- Evolution / farewell / runaway lifecycle
- Medals, streaks and records
- Gen-1 Pokédex with 151 Pokémon and shiny registration
- PMD SpriteCollab/TamaPoke TPK2 animation streaming from microSD
- Day/night scene treatment and biome backgrounds: meadow, beach, forest, volcano, mountain and snow
- Low-memory frame streaming designed for the Cardputer ADV, which does not have the large PSRAM used by the original target hardware

## Controls

| Control | Action |
|---|---|
| Left / Right | Select Home action / browse pages |
| Up | Pet card |
| Down | Settings |
| Enter | Confirm / selected action |
| Space | Pet / mini-game action |
| F | Feed |
| P | Play |
| L | Sleep / wake |
| B | Bath |
| D | Pokédex |
| I | Pet info |
| E | Evolve when ready |
| G | Farewell / runaway when available |
| N | Rename from Profile |
| R | Release |
| S | Sound on/off |
| 1 | Toggle Home name/status header |
| Esc / Backspace | Back |
| **G0 / BtnA** | **Manual display on/off** |

The Cardputer's printed arrow keycaps (`; , . /`) are also accepted directly without requiring Fn.

## Battery display

v0.8.5.4 uses the Cardputer ADV power API to read battery percentage and voltage. The compact battery icon is drawn in the upper-right without taking over the HUD. Battery details are also shown on the About screen.

Cardputer/Cardputer-ADV hardware cannot reliably report charging state/current, so the firmware does not display a fake charging indicator.

## Display behavior

Settings contains:

- Brightness: **10 / 25 / 50 / 75 / 100%**
- Automatic screen off: **Off / 30 sec / 1 min / 2 min / 5 min**
- Reset Display

Display-off is **backlight only**; the ST7789 controller remains awake. Pet logic and persistence continue while the screen is dark.

`RESET DISPLAY` only restores display preferences. It does **not** erase the Pokémon or Pokédex.

## Save compatibility

Pet persistence remains compatible with the v0.7 two-slot CRC-checked microSD journal:

```text
/tamapoke_v7_a.bin
/tamapoke_v7_b.bin
```

Display preferences are separate:

```text
/tamapoke_display.cfg
```

Recent event history is separate:

```text
/tamapoke_events.log
```

Updating from v0.8.5.3 to v0.8.5.4 is not intended to reset the existing pet.

## Pokémon sprites on microSD

The port does **not** bundle the Pokémon sprite pack. Generate the original TamaPoke/PMD files and place the `mons` directory at the root of a FAT32 microSD card:

```text
/mon​s/p001.bin
/mon​s/p002.bin
...
/mon​s/p151.bin
/mon​s/ps001.bin
...
/mon​s/ps151.bin
```

Normal sprites use `/mons/pNNN.bin`; shiny sprites use `/mons/psNNN.bin` with normal-sprite fallback.

### Cardputer ADV microSD pins

- SCK: GPIO 40
- MISO: GPIO 39
- MOSI: GPIO 14
- CS: GPIO 12
- SPI: 25 MHz

## Build with VS Code + PlatformIO

1. Clone or download this repository.
2. Open the repository folder in VS Code.
3. Install the PlatformIO extension.
4. Build environment `m5stack-cardputer-adv`.
5. The pre-build scripts fetch the pinned upstream TamaPoke pet/dex core and apply the Cardputer ADV v0.8.5.4 integration.
6. Flash with PlatformIO Upload or use the merged firmware artifact produced by GitHub Actions.

The stable merged filename is always:

```text
TamaPoke-CardputerADV.bin
```

A versioned application image is also generated as:

```text
TamaPoke-CardputerADV-v0.8.5.4-firmware.bin
```

## Clock / offline progression

The original TamaPoke hardware has a dedicated RTC; Cardputer ADV does not provide the same RTC. If `TAMAPOKE_WIFI_SSID` is configured in `include/user_config.h`, the firmware briefly obtains NTP time at boot, syncs TamaPoke, then disables Wi-Fi. With Wi-Fi credentials left blank, runtime progression works while powered on, but fully powered-off elapsed time cannot be reconstructed reliably.

## Source and credits

Original **TamaPoke** by Quique Tortosa / socquique:

https://github.com/socquique/TamaPoke

This port pins the upstream game core to commit:

```text
fdb24a7d19564ee641c9a7dfc776f6bce11cd78b
```

The upstream source is MIT licensed; see `LICENSE-UPSTREAM`.

Pokémon names/artwork and PMD SpriteCollab assets are not covered by that MIT license. This repository therefore does not bundle the Pokémon sprite pack.
