# Saves & Recovery — TamaPoke Cardputer ADV v0.9.0

v0.9.0 is designed to preserve the original v0.7-era pet journal while storing most new Cardputer features in separate auxiliary files.

## Core pet journal

The primary pet save is the alternating two-slot journal:

```text
/tamapoke_v7_a.bin
/tamapoke_v7_b.bin
```

The two slots provide redundancy. The firmware can validate journal structure/checksums and use the valid copy when one slot is damaged.

These files contain the core pet state used by the original TamaPoke lineage, including the values needed for the current Pokémon, age/level, care, Bond/streak-related fields, genes, Pokédex registration and lifecycle data.

## Why v0.9.0 remains compatible

Instead of enlarging the pet journal every time a Cardputer feature was added, the fork stores most new systems in separate files. That lets a v0.7-compatible pet journal continue into v0.9.0 without a destructive migration.

## Main auxiliary files

Depending on which features have been used, the SD root can contain:

```text
/tamapoke_display.cfg
/tamapoke_events.log
/tamapoke_ultimate_home.cfg
/tamapoke_ultimate_economy.cfg
/tamapoke_ultimate_games.cfg
/tamapoke_ultimate_daily.cfg
/tamapoke_ultimate_dex.bin
/tamapoke_ultimate_secrets.cfg
/tamapoke_wifi.bin
```

### `/tamapoke_display.cfg`

Display-related preferences such as the Cardputer-specific timeout/recovery configuration.

### `/tamapoke_events.log`

Bounded Recent Events history.

### `/tamapoke_ultimate_home.cfg`

Home background and furniture/decor selection.

### `/tamapoke_ultimate_economy.cfg`

Coin balance and Inventory/Poke Shop item counts.

### `/tamapoke_ultimate_games.cfg`

High scores for the six v0.9.0 minigames.

### `/tamapoke_ultimate_daily.cfg`

Daily Life calendar state, reward/event tracking, care-coin limit and anniversary-related state.

### `/tamapoke_ultimate_dex.bin`

Deeper per-species history used by Pokédex History.

### `/tamapoke_ultimate_secrets.cfg`

Persistent optional easter-egg flags such as Mystery Gift and Ultra Shiny Aura.

The file name retains the development-era internal naming for compatibility; the public firmware itself is branded simply TamaPoke Cardputer ADV v0.9.0.

### `/tamapoke_wifi.bin`

Fallback saved-network record used by **Use Saved Wi-Fi** when internal preferences are unavailable or do not persist reliably on a particular setup.

Internal NVS/Preferences is the preferred saved-Wi-Fi source. The SD fallback is CRC-checked and the passphrase bytes are device-bound/obfuscated using the ESP32 hardware identity. This is a reliability measure, not a claim of strong cryptographic password encryption. Protect the SD card as you would any device containing saved network credentials.

## Internal preferences / NVS

The firmware also uses ESP32 internal nonvolatile preferences for selected persistent state. Saved Wi-Fi uses the `tpwifi` preferences namespace as its primary source.

The pet-save architecture can also use internal persistence as part of the overall recovery design, but the SD journal remains the portable pet-save record users should back up.

## Save Manager

Open with **O** from Home or **H → Save Manager**.

Available actions:

- Check Live Integrity
- Backup Slot 1
- Restore Slot 1
- Backup Slot 2
- Restore Slot 2
- Backup Slot 3
- Restore Slot 3
- Back

## Integrity check

**Check Live Integrity** validates the A/B pet journals. The result reports whether both, one or neither live journal slot is valid.

If one slot is still valid, do not immediately delete files. Make a computer backup of the entire SD card first.

## Backup slots

There are three backup slots. A backup copies a verified pet journal into the selected slot and includes important v0.9.0 auxiliary state where present.

Typical backup files use names such as:

```text
/tamapoke_backup1_a.bin
/tamapoke_backup1_b.bin
/tamapoke_backup1_home.cfg
/tamapoke_backup1_economy.cfg
/tamapoke_backup1_games.cfg
/tamapoke_backup1_daily.cfg
/tamapoke_backup1_dex.bin
/tamapoke_backup1_secrets.cfg
```

Slots 2 and 3 follow the same naming pattern.

The exact set can vary if a subsystem file did not yet exist when the backup was made.

## Restore safety

Restore is intentionally harder to trigger accidentally.

1. Select a Restore Slot entry.
2. Press Enter once to arm the restore.
3. The screen asks for Enter again.
4. Press Enter again within the confirmation window.
5. The firmware stages/copies the backup, validates the restored journal and required files, then restarts when successful.

If validation fails, the Save Manager reports failure instead of deliberately treating an unverified restore as successful.

## Computer backup recommendation

Before a firmware update or major experiment:

1. Power down TamaPoke cleanly if possible.
2. Remove the microSD card.
3. Copy the entire card to a dated folder on your computer.

Example:

```text
TamaPoke-backup-2026-09-05/
```

Keeping the entire card preserves pet saves, new-system state, sprites and Save Manager backups together.

## What happens if an auxiliary file is missing?

Most auxiliary systems are designed to initialize defaults or simply start without their previous optional state. The core pet journal is separate.

Examples:

- missing Home config: Home customization can return to defaults
- missing economy file: coin/item state may be recreated/defaulted
- missing game file: v0.9.0 minigame highscores can be lost
- missing Daily file: Daily Life tracking can restart/rebuild
- missing deeper Dex file: deeper history can be lost even though core registered species remain in the pet save

Because of that separation, do not assume “my Pokémon still loads” means every optional v0.9.0 subsystem has also been preserved.

## Reset Display is not a pet reset

The Settings recovery option for display preferences is intended to repair/reset display configuration. It does not intentionally erase the Pokémon journal.

## Firmware update vs save files

Installing a new firmware BIN normally changes the application firmware, not the files on the microSD card. Still, always back up first because user error, card corruption or a recovery procedure can affect storage.

## Moving an SD card to another Cardputer ADV

The core pet journal and most TamaPoke files are portable. The Wi-Fi fallback is intentionally bound to the original ESP32 hardware identity and should not be expected to reveal/reuse the original passphrase on another device. Re-enter Wi-Fi credentials on the new unit.

## If a save looks wrong

Do not repeatedly overwrite backup slots until you know which copy is good.

Recommended order:

1. Stop making new backups.
2. Copy the SD card to a computer.
3. Run Save Manager → Check Live Integrity.
4. Note which live/backup slots are reported valid.
5. Restore only a known-good slot.
6. If necessary, inspect the computer backup before deleting anything.

## v0.7 compatibility note

The public v0.9.0 release intentionally preserves `/tamapoke_v7_a.bin` and `/tamapoke_v7_b.bin` compatibility. New v0.9.0 features do not require converting those files into a new monolithic save format.
