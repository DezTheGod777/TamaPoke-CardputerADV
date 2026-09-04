Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// OG_COMPLETE_POLISH_V0854"


def fail(msg):
    print(f"[v0.8.5.4-complete] ERROR: {msg}")
    env.Exit(1)


def replace_function(text, start_sig, next_sig, body, label):
    start = text.find(start_sig)
    if start < 0:
        fail(f"could not locate {label} start")
    end = text.find(next_sig, start)
    if end < 0:
        fail(f"could not locate {label} end")
    return text[:start] + body.rstrip() + "\n\n" + text[end:]


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.8.5.4-complete] full polish already applied")
    Return()

if "// OG_POLISH_V0854" not in text:
    fail("base OG polish must run first")
text = text.replace("// OG_POLISH_V0854", "// OG_POLISH_V0854\n" + MARKER, 1)

# ---------------------------------------------------------------------------
# Persistent runtime snapshots for meaningful notification/history events.
# ---------------------------------------------------------------------------
needle = "static uint32_t lastDraw = 0;"
if needle not in text:
    fail("lastDraw state")
text = text.replace(
    needle,
    needle + "\n"
    "static bool eventTrackingReady = false;\n"
    "static uint16_t trackedRegistered = 0;\n"
    "static uint16_t trackedMedals = 0;\n"
    "static uint16_t trackedGameHi = 0;\n"
    "static uint16_t trackedStrHi = 0;\n"
    "static uint8_t trackedCareMistakes = 0;\n"
    "static uint8_t trackedLevel = 0;\n"
    "static uint8_t trackedBond = 0;",
    1,
)

# ---------------------------------------------------------------------------
# Battery sampling: preserve library reading, with voltage fallback so the
# compact meter still works on ADV revisions where percentage is unavailable.
# ---------------------------------------------------------------------------
new_sample_battery = r'''static void sampleBattery(bool force = false) {
  uint32_t now = millis();
  if (!force && now - lastBatterySample < 5000) return;
  lastBatterySample = now;

  int lv = M5Cardputer.Power.getBatteryLevel();
  int mv = M5Cardputer.Power.getBatteryVoltage();
  if (mv > 0) batteryVoltage = mv;

  if (lv >= 0 && lv <= 100) {
    batteryLevel = lv;
  } else if (mv >= 3200 && mv <= 4400) {
    // Simple Li-ion fallback. It is intentionally approximate, but preferable
    // to hiding the battery HUD when the board does not expose a fuel gauge.
    int est = (mv - 3300) * 100 / 900;
    if (est < 0) est = 0;
    if (est > 100) est = 100;
    batteryLevel = est;
  }

  if (batteryLevel >= 0 && batteryLevel <= 15 && !lowBatteryNotified) {
    lowBatteryNotified = true;
    pushEventMemory("Low battery");
  } else if (batteryLevel > 20) {
    lowBatteryNotified = false;
  }
}'''
# sampleBattery appears before pushEventMemory in the first polish pass, so
# forward-declare pushEventMemory when replacing it.
text = text.replace(
    "static void sampleBattery(bool force = false) {",
    "static void pushEventMemory(const String &s);\n\nstatic void sampleBattery(bool force = false) {",
    1,
)
text = replace_function(
    text,
    "static void sampleBattery(bool force = false) {",
    "static void pushEventMemory(const String &s) {",
    new_sample_battery,
    "sampleBattery",
)

new_battery_meter = r'''static void drawBatteryMeter() {
  sampleBattery();
  const int x = 216, y = 3;
  uint16_t outline = sceneNight() ? UI_INK_NIGHT : UI_INK;
  uint16_t fill = UI_OK;
  if (batteryLevel >= 0 && batteryLevel <= 15) fill = UI_BAD;
  else if (batteryLevel >= 0 && batteryLevel <= 35) fill = UI_WARN;

  // 20x9 including terminal: deliberately tiny so it does not cover gameplay.
  ui.fillRoundRect(x - 1, y - 1, 21, 11, 3,
                   sceneNight() ? C565(0x14,0x1c,0x30) : UI_CREAM);
  ui.drawRoundRect(x, y, 17, 8, 2, outline);
  ui.fillRect(x + 17, y + 2, 2, 4, outline);
  if (batteryLevel >= 0) {
    int fw = (13 * batteryLevel + 50) / 100;
    if (fw > 0) ui.fillRect(x + 2, y + 2, fw, 4, fill);
    if (batteryLevel <= 15) {
      ui.setTextSize(1);
      ui.setTextColor(UI_BAD);
      ui.drawString("!", x - 7, y);
    }
  } else {
    ui.drawLine(x + 4, y + 2, x + 12, y + 5, outline);
  }
}'''
text = replace_function(
    text,
    "static void drawBatteryMeter() {",
    "static void drawSaveIndicator(uint32_t now) {",
    new_battery_meter,
    "battery meter",
)

# ---------------------------------------------------------------------------
# Helpers for richer Pokédex labels, shiny treatment, and history tracking.
# ---------------------------------------------------------------------------
helpers = r'''
static const char* primaryTypeName(uint16_t accent) {
  switch (accent) {
    case 0x3C49: return "GRASS";
    case 0xEA87: return "FIRE";
    case 0x4C98: return "WATER";
    case 0x7CC4: return "BUG";
    case 0x8C4D: return "NORMAL";
    case 0x8A73: return "POISON";
    case 0xBCA1: return "ELECTRIC";
    case 0xB447: return "GROUND";
    case 0xA2A5: return "FIGHTING";
    case 0xD28F: return "PSYCHIC";
    case 0x9407: return "ROCK";
    case 0x6AD3: return "GHOST";
    case 0x4DB8: return "ICE";
    case 0x5A98: return "DRAGON";
    default: return "SPECIAL";
  }
}

static const char* rarityName(uint8_t rarity) {
  switch (rarity) {
    case R_COMUN: return "COMMON";
    case R_RARO: return "RARE";
    case R_LEGENDARIO: return "LEGENDARY";
    default: return "EVOLUTION";
  }
}

static const char* habitatName(uint8_t biome) {
  static const char *names[6] = {"MEADOW","BEACH","FOREST","VOLCANO","MOUNTAIN","SNOW"};
  return names[biome < 6 ? biome : 0];
}

static const char* medalName(uint16_t bit) {
  switch (bit) {
    case MED_LV10: return "LEVEL 10";
    case MED_LV25: return "LEVEL 25";
    case MED_LV50: return "LEVEL 50";
    case MED_BERRY: return "BERRY FRIEND";
    case MED_STREAK7: return "7 DAY STREAK";
    case MED_BOND: return "MAX BOND";
    case MED_FINAL: return "FINAL FORM";
    case MED_FIT: return "FIT PET";
    default: return "NEW MEDAL";
  }
}

static void drawShinyBadge(int x, int y) {
  ui.fillRoundRect(x, y, 43, 11, 4, C565(0xff,0xe1,0x72));
  ui.drawRoundRect(x, y, 43, 11, 4, UI_WARN);
  ui.setTextSize(1);
  ui.setTextColor(UI_INK);
  ui.drawString("* SHINY", x + 4, y + 2);
}

static void initPetEventTracking() {
  trackedRegistered = pet.registeredCount();
  trackedMedals = pet.medals;
  trackedGameHi = pet.gameHi;
  trackedStrHi = pet.strHi;
  trackedCareMistakes = pet.careMistakes;
  trackedLevel = pet.level();
  trackedBond = pet.bond;
  eventTrackingReady = true;
}

static void checkPetEvents() {
  if (!eventTrackingReady || pet.isEgg()) return;

  uint8_t lv = pet.level();
  if (lv > trackedLevel) {
    noteEvent(String("Level up: Lv.") + lv);
  }

  uint16_t reg = pet.registeredCount();
  if (reg > trackedRegistered) {
    noteEvent(String("Pokedex unlocked: ") + reg + "/151");
  }

  if (pet.careMistakes > trackedCareMistakes) {
    noteEvent("Care mistake recorded");
  }

  uint16_t newBits = pet.medals & ~trackedMedals;
  if (newBits) {
    const uint16_t bits[] = {MED_LV10, MED_LV25, MED_LV50, MED_BERRY,
                             MED_STREAK7, MED_BOND, MED_FINAL, MED_FIT};
    for (uint16_t bit : bits) {
      if (newBits & bit) noteEvent(String("Medal: ") + medalName(bit));
    }
  }

  if (pet.gameHi > trackedGameHi)
    noteEvent(String("Play record: ") + pet.gameHi);
  if (pet.strHi > trackedStrHi)
    noteEvent(String("Training record: ") + pet.strHi);

  if (pet.bond > trackedBond) {
    const uint8_t marks[] = {25, 50, 75, 100};
    for (uint8_t m : marks) {
      if (trackedBond < m && pet.bond >= m)
        noteEvent(String("Bond reached ") + m);
    }
  }

  trackedRegistered = reg;
  trackedMedals = pet.medals;
  trackedGameHi = pet.gameHi;
  trackedStrHi = pet.strHi;
  trackedCareMistakes = pet.careMistakes;
  trackedLevel = lv;
  trackedBond = pet.bond;
}
'''
scene_anchor = "static int sceneHour() {"
if scene_anchor not in text:
    fail("sceneHour helper anchor")
text = text.replace(scene_anchor, helpers + "\n" + scene_anchor, 1)

# ---------------------------------------------------------------------------
# Richer six-biome world. Still intentionally inexpensive enough for the ADV.
# ---------------------------------------------------------------------------
new_scene = r'''static void drawScene(uint8_t biome, uint32_t now, bool night, int bottomY = 90) {
  if (biome > 5) biome = 0;
  int h = sceneHour();
  uint16_t top, bot;

  if (night) {
    top = C565(0x08, 0x0d, 0x22);
    bot = C565(0x22, 0x2c, 0x52);
  } else if (h < 8) {
    top = C565(0xd8, 0x72, 0xa0);
    bot = C565(0xff, 0xc0, 0x82);
  } else if (h < 18) {
    top = C565(0x76, 0xbb, 0xe8);
    bot = C565(0xe2, 0xf3, 0xec);
  } else {
    top = C565(0xbe, 0x50, 0x77);
    bot = C565(0xff, 0xaf, 0x62);
  }

  const int horizon = (bottomY * 62) / 100;
  for (int y = 0; y < horizon; y += 3)
    ui.fillRect(0, y, 240, 3, lerp565(top, bot, y, max(1, horizon)));

  if (night) {
    ui.fillCircle(207, 18, 10, C565(0xf0,0xee,0xd9));
    ui.fillCircle(212, 14, 9, lerp565(top, bot, 16, max(1, horizon)));
    const int stars[][2] = {{13,16},{32,37},{58,13},{89,27},{145,16},{172,35},{227,30}};
    for (auto &st : stars) {
      uint16_t c = (((now / 280) + st[0]) & 1) ? UI_WHITE : C565(0xa9,0xc9,0xee);
      ui.fillRect(st[0], st[1], 2, 2, c);
    }
  } else {
    ui.fillCircle(205, 20, 10, h < 8 ? C565(0xff,0xd4,0x8f) : C565(0xff,0xe8,0x91));
    int drift = (now / 105) % 310;
    drawCloud(drift - 38, 27, UI_WHITE);
    drawCloud(((drift + 155) % 310) - 38, 39, UI_WHITE);
  }

  uint16_t soil = BIOME_SOIL[biome];
  if (night) soil = lerp565(soil, C565(0x12,0x18,0x2b), 10, 16);
  uint16_t far = lerp565(soil, night ? top : UI_WHITE, 4, 16);
  uint16_t dark = lerp565(soil, C565(0x10,0x14,0x1f), night ? 11 : 7, 16);

  // Distant parallax ridge keeps every habitat from looking flat.
  ui.fillTriangle(-20, horizon, 46, horizon - 16, 112, horizon, far);
  ui.fillTriangle(72, horizon, 148, horizon - 20, 224, horizon, far);
  ui.fillTriangle(170, horizon, 226, horizon - 12, 270, horizon, far);

  if (biome == 1) { // beach
    uint16_t sea = night ? C565(0x19,0x37,0x58) : C565(0x37,0x94,0xc8);
    ui.fillRect(0, horizon - 12, 240, 15, sea);
    for (int i = 0; i < 3; ++i) {
      int wx = ((int)(now / (80 + i * 14)) + i * 77) % 220;
      ui.drawFastHLine(wx, horizon - 9 + i * 4, 18,
                       night ? C565(0x5f,0x79,0x98) : C565(0xd8,0xf6,0xff));
    }
    // tiny palm silhouette
    ui.drawLine(27, horizon + 11, 31, horizon - 15, dark);
    ui.drawLine(31, horizon - 15, 17, horizon - 20, dark);
    ui.drawLine(31, horizon - 15, 43, horizon - 22, dark);
    ui.drawLine(31, horizon - 15, 24, horizon - 28, dark);
    ui.drawLine(31, horizon - 15, 39, horizon - 27, dark);
  }

  ui.fillRect(0, horizon, 240, max(0, bottomY - horizon), soil);
  ui.fillRoundRect(-18, horizon - 4, 276, 18, 10, far);

  if (biome == 0) { // meadow
    for (int gx : {18,48,82,158,193,222}) {
      ui.drawLine(gx, horizon + 9, gx, horizon + 2, dark);
      ui.drawLine(gx, horizon + 4, gx - 3, horizon + 1, dark);
      if (!night && (gx & 1) == 0) ui.fillCircle(gx, horizon + 1, 2, UI_PINK);
      else if (!night) ui.fillCircle(gx, horizon + 1, 2, UI_WARN);
    }
  } else if (biome == 2) { // forest
    for (int tx : {17,44,70,179,205,229}) {
      ui.fillRect(tx - 2, horizon - 10, 4, 17, dark);
      ui.fillTriangle(tx, horizon - 34, tx - 11, horizon - 8, tx + 11, horizon - 8, dark);
      ui.fillTriangle(tx, horizon - 27, tx - 13, horizon - 2, tx + 13, horizon - 2, dark);
    }
    if (!night) {
      ui.fillCircle(99, horizon + 5, 3, C565(0xd8,0x55,0x5e));
      ui.fillRect(98, horizon + 5, 2, 4, UI_CREAM);
      ui.fillCircle(145, horizon + 7, 2, C565(0xf0,0xc2,0x67));
    }
  } else if (biome == 3) { // volcano
    ui.fillTriangle(120, horizon - 33, 72, horizon + 2, 168, horizon + 2, dark);
    ui.fillTriangle(120, horizon - 33, 109, horizon - 6, 132, horizon - 6,
                    night ? C565(0xf1,0x55,0x30) : C565(0xff,0x77,0x2d));
    for (int i = 0; i < 5; ++i) {
      int ex = 84 + ((i * 41 + now / 55) % 78);
      int ey = horizon - 5 - ((i * 19 + now / 45) % 36);
      ui.fillRect(ex, ey, 2, 2, (i & 1) ? UI_WARN : UI_BAD);
    }
    ui.drawLine(26, horizon + 8, 42, horizon + 2, UI_BAD);
    ui.drawLine(42, horizon + 2, 55, horizon + 9, UI_WARN);
    ui.drawLine(186, horizon + 8, 200, horizon + 2, UI_BAD);
  } else if (biome == 4) { // mountain
    ui.fillTriangle(57, horizon, 91, horizon - 35, 126, horizon, dark);
    ui.fillTriangle(121, horizon, 164, horizon - 29, 207, horizon, dark);
    if (!night) {
      ui.fillTriangle(79, horizon - 23, 91, horizon - 35, 103, horizon - 22, UI_WHITE);
      ui.fillTriangle(151, horizon - 20, 164, horizon - 29, 177, horizon - 19, UI_WHITE);
    }
    int bx = 25 + (now / 150) % 80;
    ui.drawLine(bx, 24, bx + 4, 21, dark);
    ui.drawLine(bx + 4, 21, bx + 8, 24, dark);
  } else if (biome == 5) { // snow
    for (int tx : {22,55,188,220}) {
      ui.fillRect(tx - 1, horizon - 8, 3, 14, dark);
      ui.fillTriangle(tx, horizon - 29, tx - 9, horizon - 8, tx + 9, horizon - 8, dark);
      ui.fillTriangle(tx, horizon - 21, tx - 11, horizon - 1, tx + 11, horizon - 1, dark);
    }
    for (int i = 0; i < 11; ++i) {
      int fx = (i * 37 + now / 55) % 238;
      int fy = (i * 19 + now / 31) % max(1, horizon);
      ui.fillRect(fx, fy, 2, 2, UI_WHITE);
    }
  }
}'''
text = replace_function(text, "static void drawScene(uint8_t biome, uint32_t now, bool night, int bottomY = 90) {",
                        "static void ensureSprite", new_scene, "drawScene")

# ---------------------------------------------------------------------------
# More personality: needs and mood influence which PMD animation is chosen.
# ---------------------------------------------------------------------------
new_ambient = r'''static void updateAmbient(uint32_t now) {
  if (!mon.loaded() || pet.isEgg() || pet.sleeping || pet.evolving() || pet.ceremony) return;

  uint32_t dt = now - lastMotion;
  lastMotion = now;
  if (petX < petTargetX) {
    int step = max(1, (int)(dt / 28));
    petX = min<int16_t>(petTargetX, petX + step);
  } else if (petX > petTargetX) {
    int step = max(1, (int)(dt / 28));
    petX = max<int16_t>(petTargetX, petX - step);
  }

  if (now < ambientUntil) return;

  // Needs change personality instead of the pet acting randomly all the time.
  if (pet.energy <= 22) {
    static const uint8_t tired[] = {PMD_SIT, PMD_BREATH, PMD_IDLE};
    ambientAction = chooseExisting(tired, 3);
    ambientUntil = now + 1800 + random(1700);
    return;
  }
  if (pet.fullness <= 18 || pet.hygiene <= 18 || pet.joy <= 18) {
    static const uint8_t unhappy[] = {PMD_HURT, PMD_SIT, PMD_BREATH, PMD_IDLE};
    ambientAction = chooseExisting(unhappy, 4);
    ambientUntil = now + 1400 + random(1500);
    return;
  }

  int r = random(100);
  if (pet.joy >= 78 && r < 38) {
    static const uint8_t happy[] = {PMD_HOP, PMD_NOD, PMD_POSE, PMD_ATTACK};
    ambientAction = chooseExisting(happy, 4);
    ambientUntil = now + 900 + random(1200);
  } else if (r < 62 && (mon.has(PMD_WALKL) || mon.has(PMD_WALKR))) {
    petTargetX = random(76, 165);
    ambientAction = (petTargetX >= petX) ? PMD_WALKR : PMD_WALKL;
    ambientUntil = now + 1500 + random(1800);
  } else if (r < 84) {
    static const uint8_t curious[] = {PMD_POSE, PMD_NOD, PMD_BREATH, PMD_SIT, PMD_HOP};
    ambientAction = chooseExisting(curious, 5);
    ambientUntil = now + 1100 + random(1600);
  } else {
    ambientAction = PMD_IDLE;
    ambientUntil = now + 1700 + random(2600);
  }
}'''
text = replace_function(text, "static void updateAmbient(uint32_t now) {",
                        "static uint8_t currentAction", new_ambient, "updateAmbient")

# ---------------------------------------------------------------------------
# Header and home HUD: all important care stats are visible at a glance.
# ---------------------------------------------------------------------------
new_header = r'''static void drawHeaderText() {
  const bool night = sceneNight();
  uint16_t accent = (!pet.isEgg() && pet.speciesId > 0) ? DEX_TBL[pet.speciesId].accent : UI_INK;
  uint16_t bg = night ? C565(0x16,0x20,0x35) : C565(0xff,0xf7,0xdf);
  uint16_t border = night ? C565(0x62,0x76,0x9a) : C565(0xc7,0xb9,0x94);

  ui.fillRoundRect(27, 1, 186, 30, 7, bg);
  ui.drawRoundRect(27, 1, 186, 30, 7, border);

  char name[36];
  if (pet.isEgg()) snprintf(name, sizeof(name), "EGG");
  else snprintf(name, sizeof(name), "%s  Lv.%u", currentName(), pet.level());

  const int len = strlen(name);
  ui.setTextSize(len <= 14 ? 2 : 1);
  ui.setTextColor(night ? UI_INK_NIGHT : accent);
  ui.drawCentreString(name, 120, len <= 14 ? 3 : 6, 1);

  ui.setTextSize(1);
  ui.setTextColor(night ? C565(0xc8,0xd5,0xeb) : UI_INK);
  const char *msg = pet.isEgg() ? "ENTER TO HATCH" : statusMsg();
  ui.drawCentreString(msg, 120, 21, 1);

  if (!pet.isEgg() && pet.shiny) {
    ui.setTextColor(UI_WARN);
    ui.drawString("*", 33, 4);
    ui.drawString("*", 202, 4);
  }

  if (pet.streak) {
    int x = 5, y = 5;
    ui.fillTriangle(x + 5, y, x, y + 10, x + 10, y + 10, UI_BAD);
    ui.fillTriangle(x + 5, y + 4, x + 2, y + 10, x + 8, y + 10, UI_WARN);
    ui.setTextSize(1);
    ui.setTextColor(night ? UI_INK_NIGHT : UI_INK);
    char s[8];
    snprintf(s, sizeof(s), "%u", pet.streak);
    ui.drawString(s, x + 12, y + 2);
  }
}'''
text = replace_function(text, "static void drawHeaderText() {", "static void drawEgg", new_header, "drawHeaderText")

new_home_panel = r'''static void drawHomePanel() {
  bool night = sceneNight();
  uint16_t panel = night ? C565(0x18,0x20,0x34) : UI_CREAM;
  uint16_t ink = night ? UI_INK_NIGHT : UI_INK;
  ui.fillRect(0, 90, 240, 45, panel);
  ui.drawFastHLine(0, 90, 240, night ? C565(0x4b,0x58,0x73) : UI_TRACK);

  struct MiniNeed { const char *lab; uint8_t val; };
  MiniNeed needs[4] = {{"FOOD", pet.fullness}, {"JOY", pet.joy},
                       {"ENE", pet.energy}, {"HYG", pet.hygiene}};
  const int mx[4] = {2, 62, 122, 182};
  for (int i = 0; i < 4; ++i) {
    uint16_t col = needs[i].val >= 55 ? UI_OK : (needs[i].val >= 25 ? UI_WARN : UI_BAD);
    ui.fillRoundRect(mx[i], 93, 56, 10, 3, night ? C565(0x22,0x2d,0x45) : UI_WHITE);
    ui.drawRoundRect(mx[i], 93, 56, 10, 3, col);
    ui.setTextSize(1);
    ui.setTextColor(ink);
    char b[13];
    snprintf(b, sizeof(b), "%s %u", needs[i].lab, needs[i].val);
    ui.drawString(b, mx[i] + 3, 95);
  }

  ui.setTextSize(1);
  ui.setTextColor(ink);
  char life[48];
  unsigned long days = pet.ageMinutes / 1440UL;
  snprintf(life, sizeof(life), "AGE %lud   WT %u   BOND %u   LV %u",
           days, pet.weight, pet.bond, pet.level());
  ui.drawCentreString(life, 120, 105, 1);

  const int xs[4] = {2, 62, 122, 182};
  const char *labs[4] = {"FEED", "PLAY", "LIGHT", "BATH"};
  for (int i = 0; i < 4; ++i) {
    bool disabled = pet.sleeping && i != 2;
    uint16_t box = night ? C565(0x20,0x2b,0x42) : UI_WHITE;
    uint16_t border = (i == homeSel) ? UI_WARN : ink;
    if (disabled) border = UI_TRACK;
    ui.fillRoundRect(xs[i], 114, 56, 19, 5, box);
    ui.drawRoundRect(xs[i], 114, 56, 19, 5, border);
    if (i == homeSel) ui.drawRoundRect(xs[i] + 1, 115, 54, 17, 4, border);

    int cx = xs[i] + 12, cy = 123;
    if (i == 0) drawBerryIcon(ui, cx, cy);
    else if (i == 1) drawBallIcon(ui, cx, cy);
    else if (i == 2) drawMoonIcon(ui, cx, cy, box);
    else drawBathIcon(ui, cx, cy);

    ui.setTextSize(1);
    ui.setTextColor(disabled ? UI_TRACK : ink);
    ui.drawString(labs[i], xs[i] + 23, 120);
  }
}'''
text = replace_function(text, "static void drawHomePanel() {", "static void drawToast", new_home_panel, "drawHomePanel")

# ---------------------------------------------------------------------------
# Evolution: old form -> accelerating silhouette swap -> flash -> full-color
# reveal. Existing SFX_EVOLVE is triggered by acceptDialog().
# ---------------------------------------------------------------------------
new_evolution = r'''static void drawEvolution(uint32_t now, uint8_t biome) {
  float t = pet.evolveT();
  bool reveal = t >= 0.91f;
  bool flash = t >= 0.80f && t < 0.91f;

  if (flash) ui.fillScreen(UI_WHITE);
  else drawScene(biome, now, reveal ? sceneNight() : false, 135);

  int cx = 120, cy = 70;
  if (!reveal) {
    int halo = 20 + (int)(t * 58) + (int)(4 * sinf(now * 0.022f));
    for (int k = 0; k < 4; ++k) {
      int r = halo - k * 7;
      if (r > 4) ui.drawCircle(cx, cy, r, flash ? UI_INK : UI_WHITE);
    }
    for (int i = 0; i < 12; ++i) {
      float a = now * 0.0045f + i * (float)(M_PI / 6.0f);
      int r = 32 + (i % 4) * 9 + (int)(t * 18);
      int x = cx + (int)(cosf(a) * r);
      int y = cy + (int)(sinf(a) * r);
      ui.fillCircle(x, y, 2, (i & 1) ? UI_WARN : UI_WHITE);
    }
  }

  ensureSprite(pet.speciesId, pet.shiny);
  if (reveal) {
    if (mon.loaded()) mon.draw(ui, PMD_POSE, 120, 111, now, 0);
    drawShinySparkles(120, 65, now);
    ui.fillRoundRect(63, 8, 114, 18, 6, C565(0xff,0xef,0xc0));
    ui.drawRoundRect(63, 8, 114, 18, 6, UI_WARN);
    ui.setTextColor(UI_INK);
    ui.setTextSize(2);
    ui.drawCentreString("EVOLVED!", 120, 12, 1);
    ui.setTextSize(1);
    ui.setTextColor(DEX_TBL[pet.speciesId].accent);
    ui.drawCentreString(dexName(pet.speciesId), 120, 29, 1);
    return;
  }

  int period = max(55, 240 - (int)(t * 210));
  bool showOld = t < 0.34f || (((now / period) & 1) && evoOld.loaded());
  uint16_t silhouette = flash ? UI_INK : (t > 0.58f ? UI_WHITE : UI_INK);
  if (showOld && evoOld.loaded())
    evoOld.draw(ui, PMD_IDLE, 120, 105, 0, 0, true, silhouette);
  else if (mon.loaded())
    mon.draw(ui, PMD_IDLE, 120, 105, 0, 0, true, silhouette);

  ui.setTextSize(2);
  ui.setTextColor(flash ? UI_INK : UI_WHITE);
  ui.drawCentreString(t < 0.42f ? "EVOLUTION!" : "CHANGING...", 120, 9, 1);
}'''
text = replace_function(text, "static void drawEvolution(uint32_t now, uint8_t biome) {",
                        "static void drawCeremony", new_evolution, "drawEvolution")

# ---------------------------------------------------------------------------
# Pokédex detail: animated preview plus status/type/habitat/rarity/stats/evo.
# ---------------------------------------------------------------------------
new_dex_detail = r'''static void drawDexDetail(uint32_t now) {
  ui.fillScreen(UI_CREAM);
  bool known = pet.isRegistered(dexCursor);
  bool shinyKnown = pet.isShinyRegistered(dexCursor);
  const DexEntry &d = DEX_TBL[dexCursor];

  char head[40];
  snprintf(head, sizeof(head), "#%03d  %s", dexCursor, known ? dexName(dexCursor) : "???");
  ui.setTextColor(known ? d.accent : UI_INK);
  ui.setTextSize(strlen(head) <= 17 ? 2 : 1);
  ui.drawCentreString(head, 120, 4, 1);

  ui.fillRoundRect(5, 22, 101, 94, 8, UI_WHITE);
  ui.drawRoundRect(5, 22, 101, 94, 8, known ? d.accent : UI_TRACK);

  ensureSprite(dexCursor, shinyKnown);
  uint8_t act = PMD_IDLE;
  if (known && mon.loaded()) {
    static const uint8_t seq[] = {PMD_IDLE, PMD_POSE, PMD_NOD, PMD_HOP};
    uint8_t wanted = seq[(now / 1500) % 4];
    act = mon.has(wanted) ? wanted : PMD_IDLE;
  }
  if (mon.loaded()) mon.draw(ui, act, 56, 102, known ? now : 0, 0, !known, UI_INK);
  if (known && shinyKnown) {
    drawShinySparkles(56, 65, now);
    drawShinyBadge(10, 26);
  }

  ui.setTextSize(1);
  ui.setTextColor(UI_INK);
  int x = 113;
  int y = 26;
  ui.drawString(pet.speciesId == dexCursor && !pet.isEgg() ? "STATUS: CURRENT" :
                (known ? "STATUS: RAISED" : "STATUS: UNKNOWN"), x, y); y += 13;

  char line[42];
  snprintf(line, sizeof(line), "TYPE: %s", known ? primaryTypeName(d.accent) : "???");
  ui.drawString(line, x, y); y += 13;
  snprintf(line, sizeof(line), "HOME: %s", known ? habitatName(d.biome) : "???");
  ui.drawString(line, x, y); y += 13;
  snprintf(line, sizeof(line), "RARITY: %s", known ? rarityName(d.rarity) : "???");
  ui.drawString(line, x, y); y += 13;

  if (known) {
    snprintf(line, sizeof(line), "HP %u  ATK %u", d.bHp, d.bAtk);
    ui.drawString(line, x, y); y += 12;
    snprintf(line, sizeof(line), "DEF %u  SPE %u", d.bDef, d.bSpe);
    ui.drawString(line, x, y); y += 12;
    if (d.evolvesTo) snprintf(line, sizeof(line), "EVOLVE #%03u Lv%u", d.evolvesTo, d.evolveLevel);
    else snprintf(line, sizeof(line), "FINAL FORM");
    ui.setTextColor(d.accent);
    ui.drawString(line, x, y);
  }

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("LEFT/RIGHT BROWSE   ESC GRID", 120, 124, 1);
}'''
text = replace_function(text, "static void drawDexDetail(uint32_t now) {",
                        "static void drawSettings", new_dex_detail, "drawDexDetail")

# ---------------------------------------------------------------------------
# About screen: clear port/upstream credits plus SD, sprite-pack and battery.
# ---------------------------------------------------------------------------
new_about = r'''static void drawAbout() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("TAMAPOKE ADV", 120, 4, 1);
  ui.setTextSize(1);
  ui.setTextColor(UI_BAD);
  ui.drawCentreString(FIRMWARE_VERSION, 120, 24, 1);

  ui.setTextColor(UI_INK);
  ui.drawCentreString("Cardputer ADV port: DezTheGod777", 120, 38, 1);
  ui.drawCentreString("Upstream: socquique/TamaPoke", 120, 50, 1);

  bool sprites = sdReady && SD.exists("/mons/p001.bin") && SD.exists("/mons/p151.bin");
  char line[42];
  snprintf(line, sizeof(line), "microSD: %s   Sprites: %s",
           sdReady ? "READY" : "MISSING", sprites ? "READY" : "MISSING");
  ui.setTextColor(sprites ? UI_OK : UI_BAD);
  ui.drawCentreString(line, 120, 66, 1);

  sampleBattery(true);
  if (batteryLevel >= 0)
    snprintf(line, sizeof(line), "Battery: %d%%  %dmV", batteryLevel, batteryVoltage);
  else
    snprintf(line, sizeof(line), "Battery: unavailable");
  ui.setTextColor(UI_INK);
  ui.drawCentreString(line, 120, 80, 1);
  ui.drawCentreString("Save journal: v0.7 compatible", 120, 94, 1);
  ui.drawCentreString("/tamapoke_v7_a.bin + _b.bin", 120, 106, 1);

  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ENTER / ESC = BACK", 120, 123, 1);
}'''
text = replace_function(text, "static void drawAbout() {",
                        "static void drawShinySparkles", new_about, "drawAbout")

# ---------------------------------------------------------------------------
# Setup/loop event integration. Existing first-pass save indicator, G0 toggle,
# terrarium idle mode, display recovery and timeout fix remain intact.
# ---------------------------------------------------------------------------
setup_needle = "  dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;\n  dirty = true;"
if setup_needle not in text:
    fail("setup event tracking anchor")
text = text.replace(setup_needle,
                    "  dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;\n"
                    "  initPetEventTracking();\n"
                    "  dirty = true;", 1)

loop_needle = "  pet.update(now);\n  onKeyboard();"
if loop_needle not in text:
    fail("loop event tracking anchor")
text = text.replace(loop_needle,
                    "  pet.update(now);\n"
                    "  checkPetEvents();\n"
                    "  onKeyboard();", 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4-complete] Applied full long-list polish: HUD, biomes, personality, evolution, Dex, battery and event history")
