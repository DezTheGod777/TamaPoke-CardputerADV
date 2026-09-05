Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE10_AUDIO_UPGRADE"


def fail(msg):
    print(f"[v0.9.0-ultimate-p10] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p10] audio upgrade already applied")
    Return()
if "// ULTIMATE_V090_PHASE9_SAVE_MANAGER" not in text:
    fail("Phase 9 must run first")

helpers = r'''

// ULTIMATE_V090_PHASE10_AUDIO_UPGRADE
// Event audio only: no looping ambience or background music.
static int16_t ultimatePendingCryDex = 0;
static uint32_t ultimatePendingCryAt = 0;

static void ultimateScheduleCry(int16_t dex, uint32_t delayMs) {
  if (dex < 1 || dex > 151) return;
  ultimatePendingCryDex = dex;
  ultimatePendingCryAt = millis() + delayMs;
}

static void serviceUltimateEventAudio(uint32_t now) {
  audioUpdate();
  if (ultimatePendingCryDex > 0 && (int32_t)(now - ultimatePendingCryAt) >= 0) {
    int16_t d = ultimatePendingCryDex;
    ultimatePendingCryDex = 0;
    ultimatePendingCryAt = 0;
    cryPlay((uint16_t)d);
  }
}
'''
anchor = "static void drawHome(uint32_t now) {"
if anchor not in text: fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Sleep and wake now have distinct gentle one-shot cues.
text = rep(text,
    "    pet.toggleLight();\n    sfxPlay(SFX_TAP);\n    triggerAction(pet.sleeping ? PMD_SLEEP : PMD_HOP, 1300);",
    "    pet.toggleLight();\n    sfxPlay(pet.sleeping ? SFX_SLEEP : SFX_WAKE);\n    triggerAction(pet.sleeping ? PMD_SLEEP : PMD_HOP, 1300);",
    "sleep/wake sound")

# Evolution keeps its full jingle, then gives the evolved Pokemon a procedural
# species chirp once the visual transformation has finished.
text = rep(text,
    "    sfxPlay(SFX_EVOLVE);",
    "    sfxPlay(SFX_EVOLVE);\n    ultimateScheduleCry(pet.speciesId, EVOLVE_ANIM_MS + 250);",
    "evolution cry schedule")

# Shop purchases get a coin confirmation instead of a generic UI tick.
text = text.replace("  sfxPlay(SFX_TAP);\n  dirty = true;\n  return true;\n}\n\nstatic uint8_t ultAdd100",
                    "  sfxPlay(SFX_COIN);\n  dirty = true;\n  return true;\n}\n\nstatic uint8_t ultAdd100", 1)

# Daily calendar and rare-visitor events get short one-shot jingles.
daily_anchor = '    say(String("Daily reward +") + reward + " coins!");'
if daily_anchor not in text: fail("daily reward audio anchor")
text = text.replace(daily_anchor, daily_anchor + "\n    sfxPlay(SFX_DAILY);", 1)
rare_anchor = '    say("Rare visitor!");'
if rare_anchor not in text: fail("rare visitor audio anchor")
text = text.replace(rare_anchor, rare_anchor + "\n    sfxPlay(SFX_RARE);", 1)

# Q lets the player hear the current Pokemon's original procedural chirp.
key_anchor = "      } else if (c == 'o') {"
if key_anchor not in text: fail("Phase 9 Home save key")
text = text.replace(key_anchor,
    "      } else if (c == 'q' && !pet.isEgg()) {\n"
    "        cryPlay((uint16_t)pet.speciesId);\n"
    + key_anchor, 1)

# Advance the non-blocking event melody sequencer every loop. Anchor on the
# loop prologue itself so later gameplay services between now/pet.update do not
# make this patch whitespace/order-sensitive.
loop_anchor = "void loop() {\n  M5Cardputer.update();\n  uint32_t now = millis();"
if loop_anchor not in text:
    fail("audio loop service")
text = text.replace(loop_anchor,
    loop_anchor + "\n  serviceUltimateEventAudio(now);",
    1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p10] Added non-looping event jingles, sleep/wake cues, coin/daily/rare sounds and procedural species cries")
