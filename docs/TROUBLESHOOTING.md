# Troubleshooting — TamaPoke Cardputer ADV v0.9.0

This page covers the most common problems on the physical M5Stack Cardputer ADV.

## Firmware does not start

- Confirm you installed the normal `TamaPoke-CardputerADV-v0.9.0.bin` file.
- Make sure the device has enough battery or connect USB power.
- If you used a complete/full-flash image unintentionally, reinstall the normal application BIN through your normal M5 Launcher workflow.
- If the display is simply off, press **G0 / BtnA** once to toggle the backlight.

## Screen goes dark after inactivity

This can be normal if a display timeout is enabled.

Go to Settings and choose the desired timeout:

- Off
- 30 seconds
- 1 minute
- 2 minutes
- 5 minutes

Home also has a clean terrarium/idle mode after roughly 30 seconds. That mode hides menu/HUD clutter while the Pokémon continues animating. Any key returns to the normal Home interface.

If display preferences become unusable, use **Reset Display** in Settings.

## Pokémon sprite is missing

Check the SD card and sprite path.

Normal example:

```text
/mons/p094.bin
```

Shiny example:

```text
/mons/ps094.bin
```

Checklist:

- SD card is FAT32 and detected.
- `mons` is at the root of the card.
- Filenames use three digits.
- The sprite is in the TamaPoke-compatible PMD binary format.
- The species file is not empty/corrupt.

The repository does not include the sprite pack.

## Clock / Calendar says date and time are not set

Use either:

**Settings → Set Date / Time**

or:

**Settings → Wi-Fi Time Sync**

Wi-Fi is optional. Manual date/time is enough for the day/night scene and local-calendar systems while the device retains a valid system clock.

## Clock is wrong after a complete power-off

The Cardputer ADV firmware cannot manufacture elapsed real-world wall time while fully powered off. TamaPoke stores the last valid timestamp, but true powered-off catch-up requires a newer valid clock when the program starts.

Possible sources of a newer valid clock include:

- a system/Launcher clock that remained valid
- a later manual correction
- one-shot Wi-Fi time sync

The saved timestamp acts as a floor so the clock does not intentionally jump far backward.

## Day/night background looks wrong

Confirm the local date/time and timezone are correct. v0.9.0 uses the original scene thresholds:

- 06:00–07:59 sunrise
- 08:00–17:59 day
- 18:00–19:59 sunset
- 20:00–05:59 night

Sleeping forces night.

The current Cardputer ADV release branch is configured for Eastern time during the tested build. If you compile for another region, set the appropriate timezone in `include/user_config.h` before building.

## Wi-Fi Time Sync menu does not respond

The hardware-approved v0.9.0 build restores dedicated keyboard handlers for the Wi-Fi picker/result screens. Up/Down should move the selection and Enter should choose.

If you are running an older development build that displays networks but ignores Up/Down, update to the final v0.9.0 release. Several pre-release builds had this exact UI-handler bug.

## Wi-Fi scan finds no networks

- Move closer to the access point.
- Rescan.
- Confirm the network is 2.4 GHz compatible with the Cardputer ADV's Wi-Fi hardware.
- Hidden SSIDs may not appear in the normal scan picker.
- Reboot and try again if the Wi-Fi driver was left in a bad state by a prior experimental build.

## Wi-Fi connects but time sync fails

If the network connection succeeds but NTP fails:

- Verify the network has internet access.
- Some guest/captive-portal networks block normal NTP/DNS until a browser login occurs.
- Try another network or phone hotspot.
- Use manual Set Date / Time as a fallback.

The firmware tries multiple NTP sources and then turns Wi-Fi back off.

## Use Saved Wi-Fi says there is no saved network

You must complete one **successful manual connection** in v0.9.0 first.

Recommended sequence:

1. Open Wi-Fi Time Sync.
2. Scan for networks.
3. Select your network.
4. Enter the password.
5. Let the time sync finish successfully.
6. Return to Wi-Fi Time Sync and choose **Use Saved Wi-Fi**.
7. Reboot and test **Use Saved Wi-Fi** again.

The final v0.9.0 code saves successful credentials to internal Preferences and also keeps a CRC-checked device-bound SD fallback. Older development builds did not always persist saved Wi-Fi correctly.

## Saved Wi-Fi works until I move the SD card to another device

That is expected for the SD fallback. The fallback password record is bound/obfuscated with the original ESP32 hardware identity. Enter the Wi-Fi password once on the new Cardputer ADV.

## Wi-Fi password fails even though it looks correct

Passwords are case-sensitive. The final input handler preserves uppercase/lowercase and symbols.

Check:

- capitalization
- spaces
- punctuation
- accidental trailing characters

Backspace deletes the last entered character.

## Battery icon looks different on some screens

The final Clock/Calendar battery indicator was specifically adjusted to use the clean/transparent treatment rather than an opaque plate. If you see the old opaque clock battery icon, you are probably running an earlier pre-release build.

## Clock Pokémon overlap the time/date

The final hardware-tested layout uses original PMD sprites for Gastly, Haunter and Gengar at a reduced clock-specific scale. Gastly and Haunter sit toward the sides, the time panel is narrower, and Gengar is positioned lower to clear the full-date text.

If you see the old oversized or hand-drawn ghost artwork, update from the earlier development build.

## Starfield code does nothing

Correct. The old secret button combination was retired during hardware testing.

**Starfield is now a normal Home background:**

**H → Home Customize → Background → Starfield**

## Dream code/background behavior changed

Correct. Dream is also a normal selectable Home background now.

The word `mew` remains an optional easter egg, but it no longer unlocks Dream. See the spoiler document for details.

## The 151 border disappeared

It was intentionally removed from v0.9.0 after hardware testing. The `151` code is retired and the firmware clears the old border unlock state. No pet reset is required.

## Bond seems stuck

Bond has an anti-farming limit.

Normal action-based Bond gain is capped at **+20 per valid local calendar day**. The first qualifying care on a new local day gives a separate **+4** daily Bond reward.

If Bond stops rising after repeated interactions on the same day, this may be correct behavior rather than a bug.

Also confirm:

- the clock/date is valid so the local-day allowance can reset
- you have not already hit the day's action cap
- the pet is not in an egg/sleep/ceremony state that blocks the interaction
- severe neglect is not creating care mistakes and small Bond losses

## Bond went down by 1

Severe neglect can count a care mistake after a cooldown and reduce Bond by one. This is intentional.

## Bond gain disappeared after reboot

The final v0.9.0 build explicitly saves caress/pet Bond after the interaction. Older pre-release builds could lose a very recent caress gain if the day's first-care save had already happened and the device restarted immediately.

## Care streak did not increase

The streak advances on the first qualifying care of a **new local calendar day**.

Check the date/time first. Repeated care on the same day does not keep increasing the streak.

If a full calendar day was skipped, the current streak resets instead of continuing.

## Flame icon at top-left looks like a warning

It is the **Care Streak indicator**. The number beside it is the current streak count.

## Pokémon is not leveling from games

That is expected. Original TamaPoke leveling is time-based:

- 1 real minute = 1 in-game minute
- +1 level every 60 real minutes

Games can affect care, records, stats/rewards or economy, but they do not grant arbitrary XP levels.

## Evo Charm did not evolve the Pokémon

The Evo Charm cannot bypass the real species evolution level/path.

It can:

- remove one care mistake
- raise all four care needs to at least 50
- open the normal evolution dialog if those repairs make the Pokémon ready

If the Pokémon is still below its required level, the charm will not force an evolution.

## Poop appears too frequently

The release intentionally keeps the original live poop roll: while awake and sufficiently fed, there is a 15% chance per real-minute tick, capped at three. Random streaks can make several appear close together.

The v0.9.0 change is mainly visual; it does not deliberately increase the roll.

## Daily Life shows strange time-together value

The final v0.9.0 build calculates **Together** from the current Pokémon's actual age in full elapsed days. Older pre-release builds could show a stale value such as thousands of days because of an adoption-day persistence bug.

Update to the release build if you see the old behavior.

## Daily reward does not reset

Daily Life depends on a valid local calendar. Confirm the date/time is correct. A bad or frozen wall clock can prevent a new local day from being recognized.

## Coins stop appearing from care

The ordinary care-coin source is intentionally bounded to prevent infinite farming. With a valid clock, it is capped at five for the local calendar day. With no valid calendar, the fallback is bounded for the current boot session rather than unlimited.

Games and other reward systems can still award coins separately.

## Save Manager says one live slot is bad

Do not panic if one of A/B is still valid. The journal is redundant.

Recommended steps:

1. Copy the whole SD card to a computer.
2. Do not overwrite all backup slots.
3. Run Check Live Integrity again.
4. Make a known-good backup if the manager permits it.
5. Restore only from a verified backup if needed.

See [Saves & Recovery](SAVES_AND_RECOVERY.md).

## Restore requires Enter twice

That is intentional. Restores are destructive enough that they require a second Enter within the confirmation window.

## Recent Events or new-system progress disappeared

The core pet and v0.9.0 auxiliary systems are stored separately. If an auxiliary file is missing/corrupt, the pet can still load while a newer feature's history/config resets.

Back up the **entire SD card**, not only the two pet journal files, if you want to preserve every v0.9.0 feature.

## SD card errors

Try:

- power off, reseat card, reboot
- verify FAT32 on a computer
- try another known-good microSD card
- check for filesystem corruption
- avoid removing the card while TamaPoke is actively saving

## Audio is silent

- Press **S** to ensure sound is enabled.
- Check the device volume/system speaker condition.
- Not every screen has continuous sound; v0.9.0 audio is event-driven.

There is intentionally no looping background music or looping audio ambience.

## Still having a problem?

When reporting a bug, include:

- exact firmware version shown in About/Version
- whether you installed the normal v0.9.0 BIN
- whether an SD card is inserted and detected
- exact steps to reproduce
- what the screen showed
- whether the problem survives a restart
- a clear photo/video if it is a layout or animation issue

For save issues, do not post Wi-Fi credential files or private network passwords publicly.
