# Controls — TamaPoke Cardputer ADV v0.9.0

The Cardputer ADV keyboard is used throughout the firmware. The printed arrow keycaps (`; , . /`) are accepted directly as directional controls without requiring Fn.

## Global navigation

| Control | Action |
|---|---|
| Up / Down / Left / Right | Navigate menus, change selections or move in games |
| Enter | Confirm / select |
| Space | Alternate confirm, pet interaction or game action depending on screen |
| Esc | Back / cancel |
| Backspace | Back on ordinary screens; delete a character in text/password entry where applicable |
| G0 / BtnA | Manual display backlight on/off |

## Home shortcuts

| Key | Action |
|---|---|
| F | Feed |
| P | Play |
| L | Sleep / wake |
| B | Bath / clean |
| D | Pokédex |
| I | Pet information / profile |
| E | Evolve when evolution is ready |
| G | Farewell / runaway action when available |
| H | TamaPoke Hub |
| C | Home Customize |
| V | Inventory / Bag |
| K | Poke Shop |
| M | Minigames |
| Y | Daily Life |
| J | Pokédex History for the current Pokémon |
| O | Save Manager |
| Q | Play the current Pokémon's cry |
| T | Clock / Calendar |
| N | Rename from the profile flow |
| R | Release/contextual release action where available |
| S | Toggle sound |
| 1 | Toggle the Home name/status header |

Up from Home opens the pet card/status view. Down from Home opens Settings.

## TamaPoke Hub

Press **H** from Home. The Hub contains:

1. Home Customize
2. Inventory / Bag
3. Poke Shop
4. Minigames
5. Daily Life
6. Pokédex History
7. Save Manager
8. Back

Use Up/Down and Enter. Esc returns to Home.

## Home Customize

Press **C** or use the Hub.

- Up / Down: choose Background, Plant, Bed, Toy, Trophy or Decor
- Left / Right: cycle through available/unlocked choices
- Enter / Space: select/confirm where applicable
- Esc: Home

Backgrounds are freely selectable in v0.9.0, including Starfield and Dream. Furniture/decor variants may be locked until their gameplay requirements are met.

## Inventory / Bag

Press **V** or use the Hub.

- Up / Down: choose item
- Enter / Space: use item
- K: jump to Poke Shop
- Esc: Home

## Poke Shop

Press **K** or use the Hub.

- Up / Down: choose item
- Enter / Space: buy selected item
- V: jump to Inventory
- Esc: Home

## Minigame menu

Press **M** or use the Hub.

- Up / Down: select game
- Enter / Space: start
- Esc: Home

### Berry Catch

- Left / Right: move the basket
- Catch falling berries to score

### Reaction

- Wait for **GO!**
- Press Space or Enter as quickly as possible
- Pressing early counts as a false start for that round

### Memory Match

- Watch the displayed directional sequence
- Re-enter it with the arrow keys after the showing period ends

### Poke Race

- Repeatedly press Space / Enter to advance
- Speed stat contributes to each boost

### Target

- Arrow keys: move the cursor/player marker
- Space / Enter: attempt the target when aligned

### Species Challenge

- Press the arrow matching the displayed prompt

## Daily Life

Press **Y** or use the Hub.

Daily Life is primarily an information/reward screen. Esc, Enter or Space returns Home.

## Pokédex and Pokédex History

Press **D** for the ordinary Pokédex.

Use directional controls to browse species and pages. Enter opens/selects where available. Esc returns.

Press **J** from Home for the current species' deeper history. On the history screen, **F** toggles favorite where supported by the current page. Left/Right changes history pages. Esc returns.

## Save Manager

Press **O** or use the Hub.

- Up / Down: choose action
- Enter / Space: perform action
- Esc: cancel/return Home

Restore actions require **two confirmations**. Select a Restore Slot entry and press Enter once to arm it. Press Enter again within the confirmation window to actually restore. A successful restore verifies the result and restarts the Cardputer ADV.

## Settings

Press Down from Home.

- Up / Down: select setting
- Left / Right: adjust settings that expose values
- Enter / Space: open/confirm selected setting
- Esc: Home/back

Important v0.9.0 entries include **Set Date / Time**, **Wi-Fi Time Sync**, **Clock / Calendar**, display timeout, display reset/recovery, About/Version and Recent Events.

## Set Date / Time

- Left / Right: select Year, Month, Day, Hour or Minute
- Up / Down: change selected value
- Enter / Space: save date/time
- Esc: cancel

The Home Clock/Calendar itself displays 12-hour time even though the editor internally represents a clock value.

## Wi-Fi Time Sync

### Network picker

- Up / Down: move through **Use Saved Wi-Fi**, discovered networks and Scan/Rescan
- Enter / Space: choose
- Esc: Settings

### Password entry

- Type the password normally; case and symbols are preserved
- Backspace: delete
- Space: insert a space if the password contains one
- Enter: connect
- Esc: cancel/back

### Result screen

Enter, Space, Esc or Back returns to Settings.

## Clock / Calendar

Press **T** from Home or open it from Settings.

The screen shows live 12-hour time, seconds, AM/PM, weekday and full date. Esc/Back returns immediately.

## Feed flow

Press **F**. Choose a berry/treat with directional controls and confirm. Favorite berries provide better care results and Bond gain than a non-favorite berry.

## Play and training

The original TamaPoke play/training screens remain available. Follow the on-screen controls for the selected activity. v0.9.0 also uses the selected Home background in Play/Training where applicable.

## Dialogs

For evolution, farewell/runaway and other confirmation dialogs:

- Left / Right or Up / Down: change selection where shown
- Enter / Space: confirm
- Esc: cancel

## Text entry

For rename and Wi-Fi password screens, printable Cardputer keys enter characters. Wi-Fi passwords specifically preserve letter case because WPA/WPA2 passwords are case-sensitive.

## Hidden inputs

There are optional easter eggs that listen for printable words while you use the Home experience. They do not replace ordinary controls. See [Secrets & Unlockables](SECRETS.md) if you want spoilers.
