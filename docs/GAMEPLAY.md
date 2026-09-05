# Gameplay Guide — TamaPoke Cardputer ADV v0.9.0

This document explains the gameplay rules that matter most in the Cardputer ADV fork, including which mechanics remain faithful to the original TamaPoke and which are new in v0.9.0.

## Core lifecycle

A TamaPoke run follows the same general lifecycle as the original project:

1. Egg / starter selection
2. Hatch
3. Raise the Pokémon through feeding, play, bathing, sleep and other care
4. Gain levels over real time
5. Evolve when the species requirement and care condition are met
6. Continue raising the final form
7. Eventually farewell/release or experience the runaway path depending on the lifecycle state
8. A new egg begins the next cycle

v0.9.0 adds many systems around that loop without replacing it.

## Time and leveling

The original time-based progression is intentionally preserved.

- **1 real minute = 1 in-game minute.**
- The pet's `ageMinutes` increases once per real minute while active.
- **1 level is gained every 60 real minutes.**
- Level is derived from age rather than XP.
- Playing games or giving excellent care does **not** make levels arrive faster.
- A neglected Pokémon can have evolution delayed by care mistakes, but its age/level clock itself still follows time.

This means v0.9.0 is not an XP-grinding fork. The new minigames, economy and Daily Life provide rewards and variety, but do not replace the original level clock.

## Offline progression

When the firmware starts with a valid wall clock newer than the last saved timestamp, TamaPoke can reconcile elapsed time. Catch-up is capped at roughly **14 days**.

Important Cardputer ADV detail: a powered-off device cannot invent elapsed wall time by itself. Offline catch-up depends on a genuinely newer valid clock being available when the firmware starts, such as a valid inherited system clock or a later network-time correction. The saved timestamp is a safe floor, but it does not continuously advance while the hardware is completely powered off.

Manual Date/Time correction and the user-requested Wi-Fi time-sync flow are designed as clock corrections and do not intentionally dump a surprise block of offline aging onto the pet.

## Day/night scene cycle

The original scene windows are locked and unchanged:

| Local time | Scene |
|---|---|
| 06:00–07:59 | Sunrise |
| 08:00–17:59 | Daytime |
| 18:00–19:59 | Sunset |
| 20:00–05:59 | Night |

Sleeping forces the night presentation regardless of the clock.

The selected Home background changes the habitat style, but does not redefine these time windows.

## Needs

The familiar care needs remain central:

- Food / fullness
- Joy
- Energy
- Hygiene

The v0.9.0 personality system can slightly change the rate at which some needs decline so different Pokémon feel a little different. Those trait effects are intentionally subtle; no temperament is meant to be overwhelmingly better or worse.

Urgent care states always take priority over personality flavor. A hungry, exhausted, dirty or sick Pokémon will act like it needs care even if its normal personality is energetic or playful.

## Poop behavior

Poop frequency remains based on the original TamaPoke logic.

While awake and sufficiently fed, the original live tick has a **15% chance per real minute** to add poop, up to three. Sleeping avoids the normal live poop roll. Offline awake catch-up can add approximately one poop per four hours, also capped at three.

v0.9.0 changes only the visual presentation of the poop icon and related polish; it does not intentionally make the poop roll more frequent.

## Personality traits

v0.9.0 gives the Pokémon a stable personality derived from permanent hatch genes already stored in the v0.7-compatible pet journal. Because it is gene-based, the personality survives restarts and does not change simply because the Pokémon evolves.

Possible traits:

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

Personality mainly influences idle action selection, movement flavor, reactions and subtle need-decay differences.

## Live moods

Moods reflect the current condition rather than being permanent. The system supports:

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

A healthy Pokémon may show its trait and current mood in the Home header. Critical care needs override the normal healthy-status wording.

## Richer idle behavior

The pet can use available PMD animations for walking, sitting, breathing, nodding, posing, hopping, attacking, sleeping and more. v0.9.0 adds:

- broader wandering
- short dozes
- sky-watching / quiet pauses
- time-of-day reactions
- habitat-condition reactions
- species-family behavior
- occasional foreground check-ins

Species without a particular PMD animation fall back safely to animations they actually provide.

## Bond

Bond is a 0–100 relationship value. It is meant to rise through repeated care over time rather than infinite button farming.

### Bond gains

Typical gains include:

- Favorite berry: **+2 Bond**
- Play: **+2 Bond**
- Training: **+2 Bond**
- Clean/bath care: **+1 Bond**
- Caress/pet interaction: **+1 Bond**
- First qualifying care on a new valid local calendar day: **+4 Bond**

The normal action-based Bond awards share a hard **+20 per local calendar day** anti-farming allowance. The first-care daily +4 is a separate calendar reward, so an excellent active day can exceed the action-only 20-point allowance.

The Lucky Charm item can also directly add a small Bond boost as part of the item effect.

### Bond loss

Severe neglect can create a care mistake. After the mistake cooldown allows another mistake to be counted, the neglect path can reduce Bond by **1**. It is deliberately mild so Bond does not collapse faster than it can reasonably be earned.

### Bond and egg quality

Bond contributes to the care bonus used by the next egg/shiny calculations along with the care streak. It does not add levels to the current Pokémon.

## Care streak

The flame-like indicator near the top-left of Home is the **Care Streak**, not a warning icon.

The first qualifying care action on a new valid **local calendar day** advances or starts the streak. Missing calendar days resets the current streak while preserving the best-streak record.

Streak milestones are recognized at larger thresholds such as 3, 7, 30 and 100 days.

The streak also contributes to the care bonus used in future egg/shiny rolls.

## Shiny odds and care bonus

The base shiny roll for a normal new egg is roughly **1 in 48** before care bonuses. A proper completed farewell improves the base path to roughly **1 in 24** before the additional care bonus.

Care streak and Bond can improve the roll, with a floor preventing the denominator from becoming too small. At very high combined care bonuses, a farewell-derived egg can become much more favorable than the base odds.

The previously raised Pokémon's care state helps the **next** egg roll. A newly hatched Pokémon begins its own Bond progression from the appropriate fresh state.

## Evolution

Evolution keeps the original species path and age/level requirement.

The core readiness check requires:

- the pet is not an egg
- it is not sleeping
- no ceremony is in progress
- the species has an evolution
- the current level reaches the species evolution level **plus care-mistake delay**
- the lowest need is in a healthy-enough state

The exact level path is still the original TamaPoke path. v0.9.0 does not allow games, coins or items to grant arbitrary levels.

### Care mistakes and evolution

Care mistakes effectively raise the level threshold for evolution. This is how neglect delays evolution without changing the underlying real-time level clock.

### Evo Charm

The Evo Charm does **not** bypass a species evolution or add levels. When used on an eligible non-egg Pokémon with an evolution path, it:

- removes one care mistake if one exists
- raises Food, Joy, Energy and Hygiene to at least 50
- opens the normal evolution confirmation immediately if those repairs make the Pokémon ready

If the level/path is still not ready, the charm can improve readiness without forcing an invalid evolution.

## Home backgrounds and gameplay

The selectable backgrounds are:

- Auto
- Meadow
- Beach
- Forest
- Volcano
- Mountain
- Snow
- Starfield
- Dream

Auto follows the species habitat. Starfield and Dream are ordinary selectable options in v0.9.0 and do not require codes.

Play and Strength Training use the selected Home background so the visual theme remains consistent.

## Furniture/decor unlocks

Backgrounds are freely selectable. Furniture/decor variants are earned.

### Plant

- Sprout: Play high score at least 3
- Flower: Play high score at least 8
- Bonsai: at least 3 total medals

### Bed

- Cushion: Bond at least 15
- Pokébed: Bond at least 40
- Cloud Bed: best streak at least 7

### Toy

- Ball: Play high score at least 5
- Ring: Strength Training high score at least 10
- Plush: at least 25 registered Pokédex species

### Trophy

- Bronze: at least 1 total medal
- Silver: at least 4 total medals
- Gold: at least 8 total medals

### Decor

- Rock: at least 5 registered species
- Sign: best streak at least 3
- Lantern: Bond at least 60

Shop items can also place some specific decor directly.

## Coins and economy

A new economy file stores coins and inventory separately from the core pet journal. A fresh economy starts with a small coin balance.

Coins are earned from:

- ordinary care/feeding rewards with a daily anti-farming limit
- original Play/Training performance
- the six v0.9.0 minigames
- Daily Life rewards/events
- optional secrets/easter eggs

Coin storage is capped to prevent overflow.

## Shop items

| Item | Price | Main effect |
|---|---:|---|
| Red Berry | 3 | Feed a red berry |
| Blue Berry | 3 | Feed a blue berry |
| Green Berry | 3 | Feed a green berry |
| Treat | 5 | Candy/treat feeding action |
| Medicine | 8 | Restores multiple needs strongly and clears poop |
| Evo Charm | 18 | Improves evolution readiness without bypassing level/path |
| Toy Box | 14 | Places the Plush toy |
| Decor Box | 14 | Places the Lantern decor |
| Style Ticket | 12 | Applies a styled Flower + Pokébed combination |
| Lucky Charm | 20 | Boosts Joy/Energy and adds a small Bond increase |

Medicine's designed restoration is approximately +18 Food, +22 Joy, +28 Energy and +35 Hygiene, capped at 100, while clearing poop.

Lucky Charm gives approximately +18 Joy, +12 Energy and +3 Bond, capped at the normal maximum.

## Additional minigames

v0.9.0 adds six games with their own saved high scores.

### Berry Catch

Move left/right and catch falling berries. The game lasts about 20 seconds. Berry speed increases as the score rises.

### Reaction

Five reaction rounds. Wait for GO and respond quickly. An early press is treated as a false start for that round. The overall safety timer is about 30 seconds.

### Memory Match

Watch a six-direction sequence, then replay it with the arrow keys. Correct inputs award points; a mistake ends the run. The game has an overall timer around 20 seconds.

### Poke Race

Repeated action presses advance your Pokémon. The Speed stat contributes to each boost. The run lasts about 12 seconds.

### Target

Move to the target with the arrow keys and press the action key when aligned. A correct hit gives points and generates a new target. The run lasts about 18 seconds.

### Species Challenge

Respond to changing arrow prompts. Correct responses score; the run lasts about 15 seconds.

Game completion awards coins automatically. High scores are saved to `/tamapoke_ultimate_games.cfg`.

## Daily Life

Daily Life becomes fully calendar-aware when the clock is valid.

Features include:

- one daily coin reward, scaled partly by care streak
- one random daily event
- a daily berry reward
- morning and night greetings
- up to five ordinary care coins per valid calendar day
- rare visitor events
- adoption/time-together tracking
- anniversary rewards

The daily event pool can include found berries, training inspiration, cozy nap, muddy adventure, coin treasure and rare visitor outcomes.

The **Together** value uses the current Pokémon's actual age in full elapsed days, not a stale stored adoption-day calculation.

## Clock and calendar

The Clock / Calendar screen is informational and does not itself connect to Wi-Fi. Once the system time is valid, it runs locally and displays:

- 12-hour time
- live seconds
- AM/PM
- weekday
- full date
- original PMD Gastly, Haunter and Gengar sprites

## Wi-Fi behavior

Wi-Fi is only used on demand for time synchronization. It is not background ambience, networking or cloud gameplay.

After a successful NTP sync, the radio is shut down. Saved credentials can be reused later through **Use Saved Wi-Fi**.

## Audio

Audio is event-driven rather than continuous. v0.9.0 includes additional:

- species cries
- hatch/evolution sounds
- level/medal cues
- sleep/wake cues
- shiny and rare-event cues
- daily/coin feedback

There is no looping background music or looping audio ambience.

## Secrets

Secrets are optional. The 151 border has been removed, and Starfield/Dream are no longer secret-gated. The remaining hidden content is documented separately with spoiler warnings in [Secrets & Unlockables](SECRETS.md).
