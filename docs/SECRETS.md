# Secrets & Unlockables — TamaPoke Cardputer ADV v0.9.0

> **SPOILER WARNING:** This page documents optional hidden content. If you want to discover easter eggs naturally, stop reading here.

## What is no longer secret in v0.9.0

Two backgrounds that were secret during development are now normal Home Customize choices:

- **Starfield**
- **Dream**

Open:

**H → Home Customize → Background**

and cycle to either one.

The old Starfield button combination is retired and does nothing in the release.

## What was removed

The experimental **151 Master Border** was removed completely after hardware testing.

Typing:

```text
151
```

no longer unlocks a border. The release also clears the old saved border flag so users who tested it previously do not keep the unwanted effect.

## Mew Visitor easter egg

Type:

```text
mew
```

The first time it is recognized, the firmware triggers the hidden **Mew Visitor** event.

First-time reward:

- temporary Mew #151 visitor presentation
- **50 coins**
- **1 Lucky Charm**

This does **not** give you Mew as your current pet and does not replace/evolve your Pokémon.

Dream is already a normal selectable background, so `mew` no longer exists to unlock Dream.

The reward is one-time; repeating the word does not keep paying another 50 coins/Lucky Charm.

## Mystery Gift code

Type:

```text
ultimate
```

The first successful entry triggers **Mystery Gift**.

Reward:

- **75 coins**
- **1 random berry**: Red, Blue or Green
- secret unlock animation/message
- rare-event sound/pose feedback

The reward is one-time. The hidden word remains as a development-history easter egg even though the public firmware branding is simply **TamaPoke Cardputer ADV v0.9.0**.

The Clock/Calendar shortcut uses **T**, but the final input handling allows the hidden word to be recognized without the `t` letters accidentally breaking the code flow.

## Natural Mystery Gift route

Mystery Gift can also occur very rarely without typing the code.

Requirements include:

- Mystery Gift has not already been claimed
- current Pokémon is not an egg
- Home screen is active
- Bond is at least **80**

The firmware performs a very rare periodic roll while those conditions are met. The check runs about once per minute with roughly a **1 in 600** chance per eligible check.

If this natural route triggers first, the event includes:

- temporary Mew visitor presentation
- **60 coins**
- **1 Style Ticket**
- Mystery Gift secret flag

Once Mystery Gift is claimed through either route, the other route is not intended to become a repeatable farming method.

## Ultra Shiny Aura

There is no keyboard code for this one. It must be earned.

Requirements:

- current Pokémon is **Shiny**
- Bond is **100**
- at least **8 total medals** have been earned

Once all conditions are met, **Ultra Shiny Aura** permanently unlocks for the secret-state save and adds an animated multi-color sparkle/aura treatment around the shiny Pokémon.

This is a prestige cosmetic reward. It does not give extra levels or bypass evolution.

## Secret persistence

Optional secret flags are stored separately from the core pet journal in:

```text
/tamapoke_ultimate_secrets.cfg
```

The development-era filename is retained for save compatibility. Save Manager backups include the secrets file when it exists.

## Why Starfield and Dream were changed

During hardware testing, the original hidden Starfield combination was easy to miss/unreliable from a user-experience perspective, while Dream was more useful as an ordinary visual choice. The release therefore makes both backgrounds available directly in Home Customize.

That keeps hidden content focused on actual easter eggs/rewards instead of hiding major scenery features from users who might never discover a code.

## Retired secret summary

| Old development secret | v0.9.0 release behavior |
|---|---|
| Starfield button combo | Retired; Starfield is selectable normally |
| `mew` unlocks Dream | Retired as a background gate; `mew` is now Mew Visitor reward only |
| `151` Master Border | Removed completely |
| `ultimate` | Still active as Mystery Gift |
| Ultra Shiny condition | Still active and earned through gameplay |
