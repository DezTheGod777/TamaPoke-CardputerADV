Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE4_HOME_CUSTOMIZATION"


def fail(msg):
    print(f"[v0.9.0-ultimate-p4] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p4] Home customization already applied")
    Return()
if "// ULTIMATE_V090_PHASE3_IDLE_LIFE" not in text:
    fail("Phase 3 must run first")

# Dedicated screen, intentionally separate from Settings so the main settings
# list stays compact and stable.
if "  ABOUT,\n  PLAY," in text:
    text = rep(text, "  ABOUT,\n  PLAY,", "  ABOUT,\n  CUSTOMIZE,\n  PLAY,", "screen enum after ABOUT")
elif "  HELP,\n  PLAY," in text:
    text = rep(text, "  HELP,\n  PLAY,", "  HELP,\n  CUSTOMIZE,\n  PLAY,", "screen enum after HELP")
else:
    fail("screen enum")

helpers = r'''

// ULTIMATE_V090_PHASE4_HOME_CUSTOMIZATION
// Home customization lives in its own tiny SD config so the v0.7 pet journal
// remains byte-for-byte compatible with older TamaPoke saves.
static const char *ULTIMATE_HOME_CFG_PATH = "/tamapoke_ultimate_home.cfg";
static uint8_t ultimateHomeBg = 0;       // 0 auto, 1..6 explicit biome
static uint8_t ultimatePlant = 0;        // 0 off, 1 sprout, 2 flower, 3 bonsai
static uint8_t ultimateBed = 0;          // 0 off, 1 cushion, 2 pokebed, 3 cloud
static uint8_t ultimateToy = 0;          // 0 off, 1 ball, 2 ring, 3 plush
static uint8_t ultimateTrophy = 0;       // 0 off, bronze/silver/gold
static uint8_t ultimateDecor = 0;        // 0 off, rock/sign/lantern
static uint8_t ultimateCustomizeSel = 0;

struct __attribute__((packed)) UltimateHomeConfigFile {
  uint32_t magic;
  uint8_t version;
  uint8_t bg;
  uint8_t plant;
  uint8_t bed;
  uint8_t toy;
  uint8_t trophy;
  uint8_t decor;
  uint8_t reserved[2];
  uint32_t crc;
};

static uint32_t ultimateHomeCfgCrc(const UltimateHomeConfigFile &c) {
  return displayCfgHash(reinterpret_cast<const uint8_t*>(&c),
                        offsetof(UltimateHomeConfigFile, crc));
}

static void saveUltimateHomeConfig() {
  if (!sdReady) return;
  UltimateHomeConfigFile c{};
  c.magic = 0x34484D54UL; // "TMH4"
  c.version = 1;
  c.bg = ultimateHomeBg;
  c.plant = ultimatePlant;
  c.bed = ultimateBed;
  c.toy = ultimateToy;
  c.trophy = ultimateTrophy;
  c.decor = ultimateDecor;
  c.crc = ultimateHomeCfgCrc(c);
  SD.remove(ULTIMATE_HOME_CFG_PATH);
  File f = SD.open(ULTIMATE_HOME_CFG_PATH, FILE_WRITE);
  if (!f) return;
  f.write(reinterpret_cast<const uint8_t*>(&c), sizeof(c));
  f.flush();
  f.close();
}

static void loadUltimateHomeConfig() {
  if (!sdReady) return;
  File f = SD.open(ULTIMATE_HOME_CFG_PATH, FILE_READ);
  if (!f || f.size() != sizeof(UltimateHomeConfigFile)) {
    if (f) f.close();
    return;
  }
  UltimateHomeConfigFile c{};
  size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c));
  f.close();
  if (got != sizeof(c) || c.magic != 0x34484D54UL || c.version != 1 ||
      ultimateHomeCfgCrc(c) != c.crc) return;
  if (c.bg <= 6) ultimateHomeBg = c.bg;
  if (c.plant <= 3) ultimatePlant = c.plant;
  if (c.bed <= 3) ultimateBed = c.bed;
  if (c.toy <= 3) ultimateToy = c.toy;
  if (c.trophy <= 3) ultimateTrophy = c.trophy;
  if (c.decor <= 3) ultimateDecor = c.decor;
}

static uint8_t ultimateSelectedHomeBiome(uint8_t speciesBiome) {
  if (ultimateHomeBg == 0) return speciesBiome < 6 ? speciesBiome : 0;
  return (uint8_t)(ultimateHomeBg - 1);
}

static bool ultimateHomeChoiceUnlocked(uint8_t row, uint8_t v) {
  if (v == 0) return true;
  // Backgrounds are freely selectable. Objects are earned through actual play,
  // care, medals, streaks and Pokédex progress rather than being static props.
  if (row == 0) return v <= 6;
  if (row == 1) {
    if (v == 1) return pet.gameHi >= 3;
    if (v == 2) return pet.gameHi >= 8;
    return pet.totalMedals >= 3;
  }
  if (row == 2) {
    if (v == 1) return pet.bond >= 15;
    if (v == 2) return pet.bond >= 40;
    return pet.bestStreak >= 7;
  }
  if (row == 3) {
    if (v == 1) return pet.gameHi >= 5;
    if (v == 2) return pet.strHi >= 10;
    return pet.registeredCount() >= 25;
  }
  if (row == 4) {
    if (v == 1) return pet.totalMedals >= 1;
    if (v == 2) return pet.totalMedals >= 4;
    return pet.totalMedals >= 8;
  }
  if (row == 5) {
    if (v == 1) return pet.registeredCount() >= 5;
    if (v == 2) return pet.bestStreak >= 3;
    return pet.bond >= 60;
  }
  return true;
}

static uint8_t* ultimateHomeChoicePtr(uint8_t row) {
  switch (row) {
    case 0: return &ultimateHomeBg;
    case 1: return &ultimatePlant;
    case 2: return &ultimateBed;
    case 3: return &ultimateToy;
    case 4: return &ultimateTrophy;
    case 5: return &ultimateDecor;
    default: return nullptr;
  }
}

static uint8_t ultimateHomeChoiceMax(uint8_t row) {
  return row == 0 ? 6 : 3;
}

static void cycleUltimateHomeChoice(uint8_t row, int delta) {
  uint8_t *p = ultimateHomeChoicePtr(row);
  if (!p) return;
  int maxv = ultimateHomeChoiceMax(row);
  int cur = *p;
  for (int tries = 0; tries <= maxv; ++tries) {
    cur += delta;
    if (cur < 0) cur = maxv;
    if (cur > maxv) cur = 0;
    if (ultimateHomeChoiceUnlocked(row, (uint8_t)cur)) {
      *p = (uint8_t)cur;
      saveUltimateHomeConfig();
      sfxPlay(SFX_TAP);
      dirty = true;
      return;
    }
  }
  sfxPlay(SFX_DENY);
}

static const char* ultimateHomeChoiceName(uint8_t row, uint8_t v) {
  static const char *bg[] = {"AUTO","MEADOW","BEACH","FOREST","VOLCANO","MOUNTAIN","SNOW"};
  static const char *plant[] = {"OFF","SPROUT","FLOWER","BONSAI"};
  static const char *bed[] = {"OFF","CUSHION","POKEBED","CLOUD BED"};
  static const char *toy[] = {"OFF","BALL","RING","PLUSH"};
  static const char *trophy[] = {"OFF","BRONZE","SILVER","GOLD"};
  static const char *decor[] = {"OFF","ROCK","SIGN","LANTERN"};
  if (row == 0) return bg[v <= 6 ? v : 0];
  if (row == 1) return plant[v <= 3 ? v : 0];
  if (row == 2) return bed[v <= 3 ? v : 0];
  if (row == 3) return toy[v <= 3 ? v : 0];
  if (row == 4) return trophy[v <= 3 ? v : 0];
  return decor[v <= 3 ? v : 0];
}

static void drawUltimateHomeDecor(uint32_t now, int bottomY) {
  // Keep all props above the normal four-button Home panel. In clean terrarium
  // mode they naturally move lower with the expanded habitat.
  int gy = bottomY >= 120 ? 118 : 82;
  uint16_t ink = sceneNight() ? UI_INK_NIGHT : UI_INK;

  if (ultimatePlant) {
    int x = 24;
    uint16_t pot = C565(0xa7,0x5a,0x3b);
    ui.fillRect(x - 6, gy - 8, 12, 8, pot);
    ui.drawRect(x - 6, gy - 8, 12, 8, ink);
    uint16_t leaf = ultimatePlant == 3 ? C565(0x3d,0x7a,0x48) : UI_OK;
    ui.drawFastVLine(x, gy - 20, 13, leaf);
    ui.fillCircle(x - 5, gy - 17, ultimatePlant == 3 ? 5 : 3, leaf);
    ui.fillCircle(x + 5, gy - 14, ultimatePlant == 3 ? 5 : 3, leaf);
    if (ultimatePlant == 2) ui.fillCircle(x, gy - 22, 4, UI_PINK);
    if (ultimatePlant == 3) ui.fillCircle(x, gy - 23, 5, leaf);
  }

  if (ultimateBed) {
    int x = 181;
    uint16_t bedCol = ultimateBed == 3 ? UI_WHITE : (ultimateBed == 2 ? UI_PINK : C565(0x8c,0xb5,0xdd));
    ui.fillRoundRect(x - 24, gy - 13, 48, 13, 6, bedCol);
    ui.drawRoundRect(x - 24, gy - 13, 48, 13, 6, ink);
    ui.fillRoundRect(x - 18, gy - 12, 17, 7, 3, UI_WHITE);
    if (ultimateBed == 2) ui.fillCircle(x + 12, gy - 7, 3, UI_WARN);
  }

  if (ultimateToy) {
    int x = 67, y = gy - 5;
    if (ultimateToy == 1) {
      drawBallIcon(ui, x, y - 3);
    } else if (ultimateToy == 2) {
      ui.drawCircle(x, y - 5, 7, UI_WARN);
      ui.drawCircle(x, y - 5, 4, UI_BAD);
    } else {
      ui.fillCircle(x, y - 8, 7, C565(0xd9,0x9a,0x68));
      ui.fillCircle(x - 5, y - 14, 3, C565(0xd9,0x9a,0x68));
      ui.fillCircle(x + 5, y - 14, 3, C565(0xd9,0x9a,0x68));
      ui.fillRect(x - 6, y - 2, 4, 4, C565(0xd9,0x9a,0x68));
      ui.fillRect(x + 2, y - 2, 4, 4, C565(0xd9,0x9a,0x68));
      ui.fillRect(x - 2, y - 8, 1, 1, ink);
      ui.fillRect(x + 2, y - 8, 1, 1, ink);
    }
  }

  if (ultimateTrophy) {
    int x = 211;
    uint16_t cup = ultimateTrophy == 1 ? C565(0xb7,0x69,0x3d)
                   : ultimateTrophy == 2 ? C565(0xd0,0xd4,0xdd) : UI_WARN;
    ui.fillRect(x - 5, gy - 18, 10, 10, cup);
    ui.drawRect(x - 5, gy - 18, 10, 10, ink);
    ui.drawCircle(x - 7, gy - 14, 4, cup);
    ui.drawCircle(x + 7, gy - 14, 4, cup);
    ui.fillRect(x - 1, gy - 8, 3, 6, cup);
    ui.fillRect(x - 7, gy - 3, 14, 3, cup);
  }

  if (ultimateDecor == 1) {
    ui.fillTriangle(126, gy, 137, gy, 132, gy - 9, C565(0x7b,0x7e,0x82));
    ui.drawLine(126, gy, 137, gy, ink);
  } else if (ultimateDecor == 2) {
    ui.fillRect(128, gy - 17, 3, 17, C565(0x77,0x4d,0x2c));
    ui.fillRoundRect(120, gy - 20, 20, 10, 2, C565(0xd7,0xb1,0x69));
    ui.drawRoundRect(120, gy - 20, 20, 10, 2, ink);
    ui.setTextSize(1);
    ui.setTextColor(ink);
    ui.drawString("HI", 125, gy - 18);
  } else if (ultimateDecor == 3) {
    int glow = 1 + ((now / 360) & 1);
    ui.fillRect(128, gy - 18, 3, 18, ink);
    ui.fillRoundRect(124, gy - 22, 11, 10, 2, C565(0xff,0xd0,0x6a));
    ui.drawRoundRect(124, gy - 22, 11, 10, 2, ink);
    if (glow) ui.fillCircle(129, gy - 17, 2, UI_WARN);
  }
}

static void drawUltimateCustomize() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("HOME CUSTOMIZE", 120, 4, 1);
  const char *rowNames[6] = {"BACKGROUND","PLANT","BED","TOY","TROPHY","DECOR"};
  for (int i = 0; i < 6; ++i) {
    int y = 24 + i * 15;
    bool sel = ultimateCustomizeSel == i;
    ui.fillRoundRect(12, y, 216, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(12, y, 216, 13, 4, sel ? UI_WARN : UI_TRACK);
    uint8_t *p = ultimateHomeChoicePtr(i);
    ui.setTextSize(1);
    ui.setTextColor(UI_INK);
    ui.drawString(rowNames[i], 18, y + 4);
    const char *val = ultimateHomeChoiceName(i, p ? *p : 0);
    ui.drawRightString(val, 220, y + 4, 1);
  }
  int by = 116;
  bool backSel = ultimateCustomizeSel == 6;
  ui.fillRoundRect(79, by, 82, 13, 4, backSel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
  ui.drawRoundRect(79, by, 82, 13, 4, backSel ? UI_WARN : UI_TRACK);
  ui.setTextColor(UI_INK);
  ui.drawCentreString("BACK", 120, by + 4, 1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Props unlock by play, care & progress", 120, 101, 1);
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text:
    fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Apply selected background only to Home; minigames and Pokédex keep the
# species' natural habitat so customization is cosmetic, not gameplay logic.
text = rep(text,
    "  if (!pet.isEgg() && pet.speciesId >= 1 && pet.speciesId <= DEX_COUNT)\n    biome = DEX_TBL[pet.speciesId].biome;",
    "  if (!pet.isEgg() && pet.speciesId >= 1 && pet.speciesId <= DEX_COUNT)\n    biome = DEX_TBL[pet.speciesId].biome;\n  biome = ultimateSelectedHomeBiome(biome);",
    "Home biome selection")

# Decorations belong to the habitat layer, behind the Pokemon and HUD.
scene_line = "  drawScene(biome, now, sceneNight(), idleTerrarium ? 135 : 90);"
if scene_line not in text:
    fail("Home scene draw")
text = text.replace(scene_line,
    scene_line + "\n  drawUltimateHomeDecor(now, idleTerrarium ? 135 : 90);",
    1)

# Render the customization screen.
render_anchor = "      case ABOUT:      drawAbout(); break;"
if render_anchor in text:
    text = text.replace(render_anchor,
        render_anchor + "\n      case CUSTOMIZE:  drawUltimateCustomize(); break;", 1)
else:
    render_anchor = "      case HELP:       drawHelp(); break;"
    if render_anchor not in text: fail("render switch")
    text = text.replace(render_anchor,
        render_anchor + "\n      case CUSTOMIZE:  drawUltimateCustomize(); break;", 1)

# Load cosmetic config after SD/display config are available.
text = rep(text,
    "  loadDisplayConfig();\n  displayLastActivity = millis();",
    "  loadDisplayConfig();\n  loadUltimateHomeConfig();\n  displayLastActivity = millis();",
    "setup Home config load")

# Keyboard navigation for the dedicated screen. Insert before HELP so it is
# independent of later minigame branches.
input_anchor = "  } else if (screen == HELP) {"
if input_anchor not in text:
    fail("input HELP branch")
custom_input = r'''  } else if (screen == CUSTOMIZE) {
    if (upEdge) {
      ultimateCustomizeSel = ultimateCustomizeSel == 0 ? 6 : ultimateCustomizeSel - 1;
      dirty = true;
    }
    if (downEdge) {
      ultimateCustomizeSel = (ultimateCustomizeSel + 1) % 7;
      dirty = true;
    }
    if ((leftEdge || rightEdge) && ultimateCustomizeSel < 6) {
      cycleUltimateHomeChoice(ultimateCustomizeSel, rightEdge ? 1 : -1);
    }
    if (enterEdge || spaceEdge) {
      if (ultimateCustomizeSel < 6) cycleUltimateHomeChoice(ultimateCustomizeSel, 1);
      else { screen = HOME; dirty = true; }
    }
    if (escEdge || backEdge) {
      screen = HOME;
      dirty = true;
    }
'''
text = text.replace(input_anchor, custom_input + input_anchor, 1)

# C opens customization directly from Home.
print_anchor = "      } else if (c == 'i' && !pet.isEgg()) {"
if print_anchor not in text:
    fail("Home printable key anchor")
text = text.replace(print_anchor,
    "      } else if (c == 'c') {\n"
    "        ultimateCustomizeSel = 0;\n"
    "        screen = CUSTOMIZE;\n"
    "        dirty = true;\n"
    + print_anchor,
    1)

# Make the feature discoverable in Controls without expanding the list count.
text = text.replace('    "D: Pokedex      E: evolution",',
                    '    "D: Pokedex      C: customize",', 1)
text = text.replace('    "G: farewell/runaway",',
                    '    "E: evolve   G: farewell/runaway",', 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p4] Added selectable habitats and earned plant/bed/toy/trophy/decor customization")
