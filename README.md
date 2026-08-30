# TamaPoke for M5Stack Cardputer ADV — v0.6 clean visual port

This project ports the **TamaPoke v1.5 pet/evolution engine** to the M5Stack
Cardputer ADV. It is deliberately a Cardputer-native UI instead of trying to
squeeze the original 466×466 round touchscreen interface into 240×135.

## What is working in v0.2

- Original TamaPoke `Pet` engine and Gen-1 Dex data, pinned to upstream commit
  `fdb24a7d19564ee641c9a7dfc776f6bce11cd78b`
- First-run Bulbasaur / Charmander / Squirtle choice
- Egg tapping / hatching
- Hunger, joy, energy, hygiene, weight and care mistakes
- Feeding: red / blue / green berries and candy
- Petting, sleep/wake and cleaning
- Play and strength-training mini-games
- Evolution and TamaPoke save data in NVS
- Pokédex browser
- Cardputer ADV speaker sound effects and microSD
- **All TPK2 PMD action slots are parsed from the original TamaPoke sprite file**
- **Idle, walk-left, walk-right, sleep, eat, hurt, attack, pose, hop, nod,
  breathing and sit animations are used when present**
- **Ambient Pokémon behavior**: the Pokémon changes pose and wanders around the
  Cardputer scene instead of standing frozen in the middle
- **Biome backgrounds** based on TamaPoke's Gen-1 Dex biome data: meadow,
  beach, forest, volcano, mountain and snow
- Night scene while sleeping, bath bubbles, heart indicator, graphical bottom
  action buttons, evolution/farewell prompts
- **Low-memory sprite streaming:** only one PMD frame is kept in RAM, so this
  works around the Cardputer ADV's lack of the original board's large PSRAM

## Controls

| Key | Action |
|---|---|
| Enter | Pet / tap egg / confirm starter / tap in mini-game |
| F | Feed menu |
| P | Play |
| T | Strength training |
| L | Sleep / wake |
| B | Bath / clean |
| E | Evolve when ready |
| D | Pokédex |
| I | Pet info |
| G | Farewell when the TamaPoke cycle allows it |
| S | Sound on/off |
| H | Help |
| Esc / Backspace | Back |
| Arrow keys | Starter / Pokédex navigation |

## Build in VS Code + PlatformIO

1. Extract this folder.
2. Open **the extracted `TamaPoke-CardputerADV` folder** in VS Code.
3. Install the PlatformIO extension if it is not already installed.
4. Click **PlatformIO: Build**.
5. The pre-build script automatically downloads the unmodified upstream
   `pet.cpp`, `pet.h`, and `dex.h` from the pinned TamaPoke commit.
6. Connect the Cardputer ADV by USB and choose **PlatformIO: Upload**.

The first Build needs internet access because it downloads the M5Cardputer
library and the pinned TamaPoke core.

## Pokémon sprites on the microSD

This port does **not** redistribute the Pokémon sprite pack.

Use the `/mons` directory produced by the original TamaPoke project. For a
normal sprite the Cardputer port looks for:

- `/mons/p001.bin`
- `/mons/p004.bin`
- `/mons/p025.bin`
- etc.

For shiny sprites it first tries `/mons/psNNN.bin`, then falls back to the
normal `/mons/pNNN.bin`.

If the SD card or a PMD sprite is missing, the game still runs; it shows a
placeholder message instead of the Pokémon animation.

### Cardputer ADV SD wiring used

- SCK: GPIO 40
- MISO: GPIO 39
- MOSI: GPIO 14
- CS: GPIO 12
- SPI clock: 25 MHz

## Clock / offline progression

The original hardware has a dedicated RTC. Cardputer ADV does not provide the
same RTC, so this first port handles it differently:

- With `TAMAPOKE_WIFI_SSID` left blank in `include/user_config.h`, gameplay
  progression works while the Cardputer is powered on, but **time spent fully
  powered off is not applied** and daily streaks do not have a real calendar.
- If you put your Wi-Fi SSID/password in `include/user_config.h`, the port
  connects briefly at boot, gets NTP time, calls TamaPoke's original
  `syncClock()`, then turns Wi-Fi back off. This restores offline progression
  and the calendar used for streaks.

## Remaining differences from the original round TamaPoke

The Cardputer ADV still uses its own 240×135 layout and keyboard instead of the
466×466 round touchscreen layout. The original gallery thumbnails, touchscreen
gesture UI, clock-setting screen and exact touch mini-games are not duplicated.
However, v0.2 now uses the original TPK2 Pokémon action animations and a much
more TamaPoke-like visual presentation.

## Source / credits / license

Original TamaPoke by Quique Tortosa:
https://github.com/socquique/TamaPoke

The upstream source code is MIT-licensed. See `LICENSE-UPSTREAM`.

Pokémon sprites and names are **not** covered by that MIT license. The upstream
project states that Pokémon material belongs to Nintendo / Game Freak / The
Pokémon Company and that PMD SpriteCollab pixel art is CC BY-NC 4.0 / for
personal non-commercial use. This port therefore does not bundle those assets.

## v0.3 clean-port changes

v0.3 replaces the prototype UI with a Cardputer-sized adaptation of the
original TamaPoke presentation. Rendering is performed into one 240x135
RGB565 canvas and then pushed to the LCD as a complete frame to avoid visible
clear/redraw flashing.

The home screen now uses the original design language: time-of-day habitat,
biome-specific ground, name/mood over the scene, lower need bars, and four
action icons. The pet card is split into Profile / Battle / Medals / Progress.
The Pokédex uses a 4x4 grid with streamed TPK2 first-frame previews and animated
detail view. Play is a keep-the-Pokéball-in-the-air game and training uses the
punching bag.

Cardputer arrow keycaps (; , . /) are accepted directly as Up / Left / Down /
Right, while the M5Cardputer Fn-arrow states are also supported.


## v0.4 reliability and display fixes

- TamaPoke's normal Preferences/NVS save remains the primary save system.
- A CRC-checked mirror of the known `tamapoke` NVS keys is written to
  `/tamapoke_save.bin` on the microSD only when the saved state changes.
- If NVS is uninitialized at boot, the microSD mirror is restored before
  `Pet::begin()` runs, preventing an unexpected blank NVS from starting over.
- The home header now uses one solid plate and one text pass for crisp glyphs.
- The home Pokemon render is 125% of the normal PMD integer scale using
  nearest-neighbor integer boundaries (no smoothing/filter blur).
- The Cardputer top-left backtick key is accepted directly as Esc/Back, in
  addition to the library's Fn-layer Esc state.


## v0.5 persistence fix

v0.5 moves persistence from a passive NVS mirror to an immediate save journal.

The pre-build upstream fetcher patches the pinned upstream `Pet::save()` with a
single `petSaveHook()` call after TamaPoke writes its Preferences keys. This
means every native TamaPoke save is mirrored immediately rather than waiting
for the main loop to notice a change.

The microSD contains two alternating CRC-checked slots:
`/tamapoke_save_a.bin` and `/tamapoke_save_b.bin`. On every boot, the newest
valid slot is restored into the `tamapoke` NVS namespace before `Pet::begin()`
loads the game. This deliberately treats the microSD journal as authoritative
for restart recovery.

The project also uses an explicit 8 MB partition table with an NVS partition
at 0x9000, OTA data at 0xE000, the application at 0x10000, and the remaining
upper flash reserved as SPIFFS.


## v0.6 direct Pet-class persistence

v0.6 patches the pinned upstream Pet class itself. Pet::save() writes the SD journal directly and Pet::begin() loads it before the first-run/starter check. The journal therefore includes private starter and egg fields that a separate NVS mirror cannot access directly. New files are `/tamapoke_v6_a.bin` and `/tamapoke_v6_b.bin`.


## v0.8 display controls

The Cardputer ADV Settings screen now includes:

- Brightness: 10%, 25%, 50%, 75%, 100%
- Automatic screen-off: Off, 30 sec, 1 min, 2 min, 5 min
- Manual `SLEEP DISPLAY NOW`

LCD sleep uses the M5 display sleep command plus backlight-off. Any keyboard
key wakes the display; the wake key is consumed so it cannot accidentally
trigger a game action. Display preferences are stored in
`/tamapoke_display.cfg` on the microSD.

The v0.7 Pet save journal filenames are intentionally unchanged so existing
pet progress remains compatible when updating to v0.8.


## v0.8.2 display stability fix

The Cardputer ADV port no longer sends the ST7789 controller into hardware
sleep. On some units/library revisions that could leave the screen black after
a wake attempt.

`SCREEN OFF NOW` and the automatic timeout now use **backlight-off only**.
The firmware continues running, the Pet keeps autosaving, and any keyboard key
restores the configured brightness. Automatic screen-off defaults to `OFF`.


## v0.8.3 animation scale fix

PMD animation actions can have different canvas dimensions even though the
Pokemon itself is intended to remain at the same pixel scale. Earlier
Cardputer builds recalculated scale from every current action canvas, which
could make the Pokemon suddenly appear very small during some animations.

v0.8.3 derives automatic scale from the Pokemon's IDLE action and keeps that
pixel scale for all other actions. Larger canvases now provide animation
movement space without changing the apparent size of the Pokemon.


## v0.8.4 visible-sprite scaling

v0.8.3 correctly stabilized animation scale but used the full IDLE canvas,
including transparent padding, as its reference. That made some species much
smaller than intended.

v0.8.4 scans the IDLE frames and caches the maximum **visible-pixel bounding
box**. Every animation action uses a scale derived from that same visible
reference. This keeps the Pokemon large enough for the Cardputer display while
preserving consistent size across animation actions.


## v0.8.5 home header toggle

Press the physical number `1` key to toggle the home-screen Pokemon
name/level/mood panel on or off. The habitat renders normally underneath it.

The home Pokemon size is also increased slightly from v0.8.4. The change is
deliberately modest: the home scale boost moves from 1.25x to roughly 1.33x,
while the stable visible-sprite animation scaling remains unchanged.


## Stable firmware filename

Starting with v0.8.5.2, the preferred merged firmware image is always:

`TamaPoke-CardputerADV.bin`

The version remains in the GitHub Release/tag and source history rather than
the firmware filename. This gives M5Burner and users one predictable filename
for every update.

## One-click GitHub updates

Run `00_UPDATE_GITHUB_ONE_CLICK.bat` from an extracted source package to update
the existing `TamaPoke-CardputerADV` repository. It clones the existing repo,
overlays the current source, commits changed files, and pushes to `main`.
Existing GitHub Releases are not deleted.
