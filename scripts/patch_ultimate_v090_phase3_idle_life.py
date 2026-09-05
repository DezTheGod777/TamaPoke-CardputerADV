Import("env")
from pathlib import Path
import re

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE3_IDLE_LIFE"


def fail(msg):
    print(f"[v0.9.0-ultimate-p3] ERROR: {msg}")
    env.Exit(1)


def must_replace(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p3] richer idle life already applied")
    Return()
if "// ULTIMATE_V090_LIVING_BEHAVIOR_M2" not in text:
    fail("Phase 2 living behavior must run first")

helpers = r'''

// ULTIMATE_V090_PHASE3_IDLE_LIFE
// Transient Phase 3 idle states. Nothing here changes the saved pet journal.
enum UltimateIdleMoment : uint8_t {
  UIM_NONE = 0, UIM_SKYWATCH, UIM_STRETCH, UIM_DOZE, UIM_APPROACH, UIM_SPECIES
};
static UltimateIdleMoment ultimateIdleMoment = UIM_NONE;
static uint32_t ultimateIdleMomentUntil = 0;

static void ultimateSetIdleMoment(UltimateIdleMoment m, uint32_t now, uint32_t duration) {
  ultimateIdleMoment = m;
  ultimateIdleMomentUntil = now + duration;
}
static void ultimateExpireIdleMoment(uint32_t now) {
  if (ultimateIdleMoment != UIM_NONE && now >= ultimateIdleMomentUntil) {
    ultimateIdleMoment = UIM_NONE;
    ultimateIdleMomentUntil = 0;
  }
}
static int8_t ultimateHomeSpriteScale(uint32_t now) {
  ultimateExpireIdleMoment(now);
  if (idleTerrarium) return -1;
  return ultimateIdleMoment == UIM_APPROACH ? 3 : -1;
}
static int16_t ultimateHomeGroundY(uint32_t now) {
  ultimateExpireIdleMoment(now);
  if (idleTerrarium) return 118;
  return ultimateIdleMoment == UIM_APPROACH ? 98 : 88;
}

static void drawUltimateIdleMomentFx(uint32_t now) {
  ultimateExpireIdleMoment(now);
  if (idleTerrarium || ultimateIdleMoment == UIM_NONE || pet.isEgg() || pet.sleeping) return;
  uint16_t ink = sceneNight() ? UI_INK_NIGHT : UI_INK;
  if (ultimateIdleMoment == UIM_SKYWATCH) {
    int sx = petX < 120 ? petX + 25 : petX - 25;
    int sy = 34 + (int)((now / 260) % 3);
    ui.drawFastHLine(sx - 3, sy, 7, UI_WARN);
    ui.drawFastVLine(sx, sy - 3, 7, UI_WARN);
    ui.fillRect(sx + 10, sy - 8, 2, 2, UI_WHITE);
  } else if (ultimateIdleMoment == UIM_STRETCH) {
    ui.drawLine(petX - 28, 55, petX - 22, 51, ink);
    ui.drawLine(petX + 28, 55, petX + 22, 51, ink);
  } else if (ultimateIdleMoment == UIM_DOZE) {
    ui.setTextSize(1);
    ui.setTextColor(sceneNight() ? UI_INK_NIGHT : C565(0x55,0x62,0x78));
    ui.drawString("z", petX + 21, 37);
    ui.drawString("Z", petX + 27, 29);
  } else if (ultimateIdleMoment == UIM_APPROACH) {
    ui.fillCircle(120, 31, 2, UI_WARN);
    ui.drawFastHLine(115, 31, 11, UI_WARN);
    ui.drawFastVLine(120, 26, 11, UI_WARN);
  } else if (ultimateIdleMoment == UIM_SPECIES) {
    int sx = petX + (((now / 240) & 1) ? 23 : -23);
    ui.fillRect(sx, 38, 2, 2, UI_WARN);
  }
}

static bool ultimatePhase3SpeciesMoment(uint32_t now) {
  const int16_t d = pet.speciesId;
  if (d <= 0) return false;

  if (d >= 1 && d <= 3) {
    static const uint8_t a[] = {PMD_BREATH, PMD_POSE, PMD_NOD};
    ultimateSetIdleMoment(UIM_STRETCH, now, 1900); ultimateFlair(now,a,3,1200,900); return true;
  }
  if (d >= 4 && d <= 6) {
    static const uint8_t a[] = {PMD_ATTACK, PMD_POSE, PMD_HOP};
    ultimateSetIdleMoment(UIM_SPECIES, now, 1700); ultimateFlair(now,a,3,900,900); return true;
  }
  if (d >= 7 && d <= 9) {
    static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_BREATH};
    ultimateSetIdleMoment(UIM_SPECIES, now, 1700); ultimateFlair(now,a,3,950,900); return true;
  }
  if ((d >= 16 && d <= 18) || (d >= 21 && d <= 22) || d == 83) {
    static const uint8_t a[] = {PMD_POSE, PMD_HOP, PMD_NOD};
    ultimateSetIdleMoment(UIM_SKYWATCH, now, 1900); ultimateFlair(now,a,3,1050,950); return true;
  }
  if (d == 39 || d == 40) {
    static const uint8_t a[] = {PMD_SIT, PMD_NOD, PMD_BREATH};
    ultimateSetIdleMoment(UIM_DOZE, now, 2000); ultimateFlair(now,a,3,1450,900); return true;
  }
  if (d == 54 || d == 55) {
    static const uint8_t a[] = {PMD_NOD, PMD_SIT, PMD_POSE};
    ultimateSetIdleMoment(UIM_SKYWATCH, now, 1750); ultimateFlair(now,a,3,1100,850); return true;
  }
  if (d >= 63 && d <= 65) {
    static const uint8_t a[] = {PMD_SIT, PMD_BREATH, PMD_POSE};
    ultimateSetIdleMoment(UIM_DOZE, now, 2200); ultimateFlair(now,a,3,1600,1000); return true;
  }
  if (d == 132) {
    static const uint8_t a[] = {PMD_POSE, PMD_BREATH, PMD_HOP};
    ultimateSetIdleMoment(UIM_SPECIES, now, 1800); ultimateFlair(now,a,3,1100,900); return true;
  }
  if (d >= 133 && d <= 136) {
    static const uint8_t a[] = {PMD_NOD, PMD_POSE, PMD_HOP};
    petTargetX = 120; ultimateSetIdleMoment(UIM_APPROACH, now, 1700); ultimateFlair(now,a,3,950,800); return true;
  }
  if (d >= 144 && d <= 146) {
    static const uint8_t a[] = {PMD_ATTACK, PMD_POSE, PMD_HOP};
    ultimateSetIdleMoment(UIM_SKYWATCH, now, 2100); ultimateFlair(now,a,3,1000,1100); return true;
  }
  return false;
}

static bool ultimateHabitatReaction(uint32_t now) {
  if (pet.speciesId <= 0 || pet.speciesId > DEX_COUNT) return false;
  uint8_t biome = DEX_TBL[pet.speciesId].biome;
  int h = sceneHour();
  if (biome == 5) {
    static const uint8_t a[] = {PMD_HOP,PMD_POSE,PMD_BREATH};
    ultimateSetIdleMoment(UIM_SKYWATCH,now,1850); ultimateFlair(now,a,3,1050,900); return true;
  }
  if (biome == 2) {
    static const uint8_t a[] = {PMD_NOD,PMD_POSE,PMD_BREATH};
    ultimateSetIdleMoment(UIM_SKYWATCH,now,1750); ultimateFlair(now,a,3,1100,850); return true;
  }
  if (biome == 1) {
    static const uint8_t a[] = {PMD_HOP,PMD_NOD,PMD_POSE};
    ultimateSetIdleMoment(UIM_SPECIES,now,1650); ultimateFlair(now,a,3,950,850); return true;
  }
  if (biome == 3) {
    static const uint8_t a[] = {PMD_POSE,PMD_ATTACK,PMD_BREATH};
    ultimateSetIdleMoment(UIM_SPECIES,now,1750); ultimateFlair(now,a,3,1000,900); return true;
  }
  if ((h >= 19 || h < 6) && (biome == 0 || biome == 4)) {
    static const uint8_t a[] = {PMD_POSE,PMD_BREATH,PMD_NOD};
    ultimateSetIdleMoment(UIM_SKYWATCH,now,1950); ultimateFlair(now,a,3,1250,900); return true;
  }
  return false;
}
'''

anchor = "static void updateAmbient(uint32_t now) {"
if anchor not in text: fail("updateAmbient anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

text = must_replace(text,
    "static void updateAmbient(uint32_t now) {\n  if (!mon.loaded() || pet.isEgg() || pet.sleeping || pet.evolving() || pet.ceremony) return;",
    "static void updateAmbient(uint32_t now) {\n  ultimateExpireIdleMoment(now);\n  if (!mon.loaded() || pet.isEgg() || pet.sleeping || pet.evolving() || pet.ceremony) return;",
    "Phase 3 updateAmbient prologue")

text = must_replace(text,
    "  if (mood == UDM_SLEEPY) {\n    static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH, PMD_IDLE};",
    "  if (mood == UDM_SLEEPY) {\n    ultimateSetIdleMoment(UIM_DOZE, now, 2300);\n    static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH, PMD_IDLE};",
    "sleepy idle moment")

text = must_replace(text,
    "    static const uint8_t a[] = {PMD_NOD, PMD_BREATH, PMD_SIT};\n    ultimateFlair(now, a, 3, 1200, 1200);",
    "    ultimateSetIdleMoment(UIM_APPROACH, now, 1750);\n    static const uint8_t a[] = {PMD_NOD, PMD_BREATH, PMD_SIT};\n    ultimateFlair(now, a, 3, 1200, 1200);",
    "lonely approach")

text = must_replace(text,
    "    static const uint8_t a[] = {PMD_NOD, PMD_POSE, PMD_HOP, PMD_BREATH};\n    ultimateFlair(now, a, 4, 850, 1000);",
    "    ultimateSetIdleMoment(UIM_APPROACH, now, 1650);\n    static const uint8_t a[] = {PMD_NOD, PMD_POSE, PMD_HOP, PMD_BREATH};\n    ultimateFlair(now, a, 4, 850, 1000);",
    "affectionate approach")

text = must_replace(text,
    "      static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH};\n      ultimateFlair(now, a, 3, 1700, 1600);",
    "      ultimateSetIdleMoment(UIM_DOZE, now, 2400);\n      static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH};\n      ultimateFlair(now, a, 3, 1700, 1600);",
    "night doze")

text = must_replace(text,
    "  // Occasional species/biome signature action.\n  if (r >= 18 && r < 31 && ultimateSpeciesMoment(now)) return;",
    "  // Phase 3: wider species-family and habitat-condition reactions.\n  if (r >= 18 && r < 27 && ultimatePhase3SpeciesMoment(now)) return;\n  if (r >= 27 && r < 35 && ultimateHabitatReaction(now)) return;\n  if (r >= 35 && r < 44) {\n    ultimateSetIdleMoment(UIM_SPECIES, now, 1700);\n    if (ultimateSpeciesMoment(now)) return;\n    ultimateIdleMoment = UIM_NONE; ultimateIdleMomentUntil = 0;\n  }",
    "species/habitat reaction slot")

text = must_replace(text,
    "  if (random(100) < 18) {\n    petTargetX = random(2) ? 92 : 148;\n    static const uint8_t sky[] = {PMD_POSE, PMD_BREATH};\n    ultimateFlair(now, sky, 2, 1500, 1200);\n    return;\n  }",
    "  if (random(100) < 22) {\n    petTargetX = random(2) ? 92 : 148;\n    UltimateIdleMoment beat = random(100) < 52 ? UIM_SKYWATCH : UIM_STRETCH;\n    ultimateSetIdleMoment(beat, now, 2100);\n    static const uint8_t sky[] = {PMD_POSE, PMD_BREATH};\n    ultimateFlair(now, sky, 2, 1500, 1200);\n    return;\n  }\n\n  UltimateTrait checkTrait = ultimateTrait();\n  if (random(100) < 9 && (pet.bond >= 65 || checkTrait == UT_CURIOUS || checkTrait == UT_AFFECTIONATE)) {\n    petTargetX = 120;\n    ultimateSetIdleMoment(UIM_APPROACH, now, 1800);\n    static const uint8_t hello[] = {PMD_NOD, PMD_POSE, PMD_BREATH};\n    ultimateFlair(now, hello, 3, 1000, 750);\n    return;\n  }",
    "sky/stretch and foreground check-in")

# Earlier stable polish changes Home's ground line for clean terrarium mode.
# Match either shape so Phase 3 remains robust and preserves clean terrarium.
pat = re.compile(
    r"mon\.draw\(ui,\s*currentAction\(now\),\s*petX,\s*"
    r"(?:idleTerrarium\s*\?\s*118\s*:\s*88|88),\s*now,\s*-1\s*\);"
)
m = pat.search(text)
if not m:
    fail("could not locate Home sprite draw")
replacement = ("mon.draw(ui, currentAction(now), petX, ultimateHomeGroundY(now), now, "
               "ultimateHomeSpriteScale(now));\n      drawUltimateIdleMomentFx(now);")
text = text[:m.start()] + replacement + text[m.end():]

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p3] Added foreground check-ins, visible idle moments, wider species behavior and habitat/time reactions")
