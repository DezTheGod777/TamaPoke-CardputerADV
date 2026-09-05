# Installation — TamaPoke Cardputer ADV v0.9.0

This guide covers the public **v0.9.0** firmware for the **M5Stack Cardputer ADV**.

## What you need

- M5Stack Cardputer ADV
- A USB-C cable for charging/recovery
- A FAT32 microSD card strongly recommended for the full experience
- `TamaPoke-CardputerADV-v0.9.0.bin`
- The original TamaPoke/PMD sprite files if you want animated Pokémon graphics

## Which BIN should I use?

Use:

```text
TamaPoke-CardputerADV-v0.9.0.bin
```

That is the normal application firmware BIN and is the file intended for ordinary installation, including **M5 Launcher**.

The build system may also produce:

```text
TamaPoke-CardputerADV-v0.9.0-full-flash.bin
```

That complete flash image is not the normal release/install file. Do not choose it unless you specifically need a full-flash recovery workflow and understand the difference.

## Installing with M5 Launcher

1. Make sure the Cardputer ADV has enough battery or keep it connected to USB power.
2. Make `TamaPoke-CardputerADV-v0.9.0.bin` available to M5 Launcher using your normal Launcher file/install workflow.
3. Select the v0.9.0 BIN in M5 Launcher and install it as firmware.
4. Allow the Cardputer ADV to restart into TamaPoke.
5. Insert the prepared microSD card if it is not already installed.

No custom flash offset is required for the normal release BIN.

## Updating from an older TamaPoke Cardputer ADV build

v0.9.0 keeps the v0.7-compatible pet journal, so an existing pet can carry forward. Before installing, copy these files somewhere safe if they exist:

```text
/tamapoke_v7_a.bin
/tamapoke_v7_b.bin
```

For the safest migration, back up the entire microSD card. v0.9.0 creates separate auxiliary files for its new systems rather than changing the core pet journal format.

After updating, let the firmware boot normally. You should not need to erase, recreate or reset your existing pet.

## Preparing the microSD card

FAT32 is recommended. Place the `mons` directory at the root of the card.

Expected normal sprite naming:

```text
/mons/p001.bin
/mons/p002.bin
...
/mons/p151.bin
```

Expected shiny sprite naming:

```text
/mons/ps001.bin
/mons/ps002.bin
...
/mons/ps151.bin
```

Normal Pokémon use `pNNN.bin`. Shiny Pokémon first look for `psNNN.bin` and can fall back to the normal sprite where supported.

The repository does not bundle the Pokémon/PMD sprite pack. Generate/use the same compatible PMD sprite resources used by the original TamaPoke project.

## First boot checklist

After the firmware starts:

1. Confirm the Pokémon sprite loads correctly.
2. Open **Settings** with Down.
3. Set your display timeout preference.
4. Set the correct date/time using **Set Date / Time**, or use **Wi-Fi Time Sync**.
5. Open **Clock / Calendar** and confirm the time, weekday and date are correct.
6. Press **H** to explore the TamaPoke Hub.
7. Open **Save Manager** and run **Check Live Integrity** after your pet has been saved to the SD card.

## Date and time without Wi-Fi

TamaPoke does not require an always-on internet connection. Use:

**Settings → Set Date / Time**

Controls on that screen:

- Left / Right: choose Year, Month, Day, Hour or Minute
- Up / Down: change the selected value
- Enter or Space: save
- Esc: cancel

The editor uses your configured local timezone and does not intentionally apply a large block of offline pet aging just because you corrected the clock.

## One-shot Wi-Fi time sync

Use:

**Settings → Wi-Fi Time Sync**

The Wi-Fi system is intentionally on-demand. It is not kept connected in the background.

A normal first-time setup is:

1. Open Wi-Fi Time Sync.
2. Choose **Scan For Networks**.
3. Select your Wi-Fi network.
4. Enter the password exactly; Wi-Fi passwords are case-sensitive.
5. Press Enter to connect and obtain network time.
6. After a successful sync, the Wi-Fi radio is shut back down.

After one successful connection, **Use Saved Wi-Fi** can reuse the saved network. v0.9.0 stores the saved credentials in internal preferences and keeps a device-bound fallback on the TamaPoke SD card for hardware reliability.

## If sprites do not appear

Check all of the following:

- The card is FAT32 and is detected by the device.
- The directory is exactly `/mons` at the SD root.
- Filenames use three digits: `p025.bin`, not `p25.bin`.
- The required species file exists.
- The file was generated in the compatible PMD/TamaPoke format.

See [Troubleshooting](TROUBLESHOOTING.md) for more.

## If you are starting completely fresh

A fresh install can create a new TamaPoke pet/save. Do not delete old journal files unless you actually want to discard that pet. If you are unsure, copy the SD card contents to a computer first.

## Building from source instead

Install PlatformIO, clone the repository and build:

```text
pio run -e m5stack-cardputer-adv
```

The project fetches a pinned upstream TamaPoke pet/dex source during the build and applies the Cardputer ADV patch chain. The final normal application firmware copy is created as:

```text
TamaPoke-CardputerADV-v0.9.0.bin
```

For source architecture and feature differences, see [Features](FEATURES.md).
