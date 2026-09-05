Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE6_MORE_MINIGAMES"


def fail(msg):
    print(f"[v0.9.0-ultimate-p6] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p6] minigames already applied")
    Return()
if "// ULTIMATE_V090_PHASE5_INVENTORY_SHOP" not in text:
    fail("Phase 5 must run first")

if "  SHOP,\n  PLAY," not in text:
    fail("Phase 5 screen enum")
text = text.replace("  SHOP,\n  PLAY,",
                    "  SHOP,\n  GAMES,\n  ULT_GAME,\n  PLAY,", 1)

helpers = r'''

// ULTIMATE_V090_PHASE6_MORE_MINIGAMES
enum UltimateGameMode : uint8_t {
  UGM_BERRY = 0, UGM_REACTION, UGM_MEMORY, UGM_RACE, UGM_TARGET, UGM_SPECIES, UGM_COUNT
};
static const char *ULT_GAME_NAME[UGM_COUNT] = {
  "BERRY CATCH", "REACTION", "MEMORY MATCH", "POKE RACE", "TARGET", "SPECIES CHALLENGE"
};
static const char *ULT_GAME_CFG_PATH = "/tamapoke_ultimate_games.cfg";
static uint8_t ultimateGameMenuSel = 0;
static UltimateGameMode ultimateGameMode = UGM_BERRY;
static bool ultimateGameActive = false;
static bool ultimateGameResult = false;
static uint32_t ultimateGameUntil = 0;
static uint32_t ultimateGameResultUntil = 0;
static uint16_t ultimateGameScore = 0;
static uint16_t ultimateGameHi[UGM_COUNT] = {0};
static bool ultimateGameNewHi = false;

// Shared lightweight game state.
static int ultimatePlayerX = 120, ultimatePlayerY = 102;
static int ultimateObjX = 120, ultimateObjY = 20;
static int ultimateObjV = 2;
static uint32_t ultimateGameStep = 0;
static uint8_t ultimateRound = 0;
static uint8_t ultimateReactionState = 0;
static uint32_t ultimatePromptAt = 0, ultimatePromptStart = 0;
static uint8_t ultimateMemorySeq[6] = {0};
static uint8_t ultimateMemoryInput = 0;
static uint32_t ultimateMemoryShowStart = 0;
static uint16_t ultimateRaceDistance = 0;
static int ultimateTargetX = 160, ultimateTargetY = 60;
static uint8_t ultimateSpeciesPrompt = 0;
static uint32_t ultimateSpeciesFlashUntil = 0;

struct __attribute__((packed)) UltimateGameFile {
  uint32_t magic;
  uint8_t version;
  uint16_t hi[UGM_COUNT];
  uint8_t reserved[3];
  uint32_t crc;
};

static uint32_t ultimateGameCfgCrc(const UltimateGameFile &c) {
  return displayCfgHash(reinterpret_cast<const uint8_t*>(&c), offsetof(UltimateGameFile, crc));
}
static void saveUltimateGames() {
  if (!sdReady) return;
  UltimateGameFile c{};
  c.magic = 0x36474D54UL; // "TMG6"
  c.version = 1;
  memcpy(c.hi, ultimateGameHi, sizeof(c.hi));
  c.crc = ultimateGameCfgCrc(c);
  SD.remove(ULT_GAME_CFG_PATH);
  File f = SD.open(ULT_GAME_CFG_PATH, FILE_WRITE);
  if (!f) return;
  f.write(reinterpret_cast<const uint8_t*>(&c), sizeof(c));
  f.flush(); f.close();
}
static void loadUltimateGames() {
  if (!sdReady) return;
  File f = SD.open(ULT_GAME_CFG_PATH, FILE_READ);
  if (!f || f.size() != sizeof(UltimateGameFile)) { if (f) f.close(); return; }
  UltimateGameFile c{};
  size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c)); f.close();
  if (got == sizeof(c) && c.magic == 0x36474D54UL && c.version == 1 &&
      ultimateGameCfgCrc(c) == c.crc) memcpy(ultimateGameHi, c.hi, sizeof(ultimateGameHi));
}

static void ultimateNewTarget() {
  ultimateTargetX = 35 + random(170);
  ultimateTargetY = 30 + random(70);
}

static void ultimateFinishGame(uint32_t now) {
  if (!ultimateGameActive) return;
  ultimateGameActive = false;
  ultimateGameResult = true;
  ultimateGameResultUntil = now + 3000;
  uint8_t m = (uint8_t)ultimateGameMode;
  ultimateGameNewHi = ultimateGameScore > ultimateGameHi[m];
  if (ultimateGameNewHi) {
    ultimateGameHi[m] = ultimateGameScore;
    saveUltimateGames();
    sfxPlay(SFX_MEDAL);
  } else {
    sfxPlay(SFX_LEVEL);
  }
  ultimateAwardCoins((uint16_t)(3 + std::min<uint16_t>(30, ultimateGameScore / 5)));
  dirty = true;
}

static void ultimateNextReaction(uint32_t now) {
  if (++ultimateRound >= 5) { ultimateFinishGame(now); return; }
  ultimateReactionState = 0;
  ultimatePromptAt = now + 1200 + random(2600);
}

static void startUltimateGame(UltimateGameMode mode) {
  if (pet.isEgg() || pet.sleeping || pet.ceremony) {
    sfxPlay(SFX_DENY);
    say(pet.isEgg() ? "Hatch the egg first" : "Wake your Pokemon first");
    return;
  }
  ultimateGameMode = mode;
  ultimateGameActive = true;
  ultimateGameResult = false;
  ultimateGameScore = 0;
  ultimateGameNewHi = false;
  ultimatePlayerX = 120; ultimatePlayerY = 105;
  ultimateObjX = 30 + random(180); ultimateObjY = 22; ultimateObjV = 2;
  ultimateGameStep = millis();
  ultimateRound = 0;
  ultimateReactionState = 0;
  ultimatePromptAt = millis() + 1400 + random(2500);
  ultimatePromptStart = 0;
  ultimateMemoryInput = 0;
  ultimateMemoryShowStart = millis();
  for (int i = 0; i < 6; ++i) ultimateMemorySeq[i] = random(4);
  ultimateRaceDistance = 0;
  ultimateNewTarget();
  ultimateSpeciesPrompt = random(4);
  ultimateSpeciesFlashUntil = 0;

  if (mode == UGM_BERRY) ultimateGameUntil = millis() + 20000;
  else if (mode == UGM_REACTION) ultimateGameUntil = millis() + 30000;
  else if (mode == UGM_MEMORY) ultimateGameUntil = millis() + 20000;
  else if (mode == UGM_RACE) ultimateGameUntil = millis() + 12000;
  else if (mode == UGM_TARGET) ultimateGameUntil = millis() + 18000;
  else ultimateGameUntil = millis() + 15000;
  screen = ULT_GAME;
  dirty = true;
}

static void updateUltimateGame(uint32_t now) {
  if (ultimateGameResult) {
    if (now >= ultimateGameResultUntil) {
      ultimateGameResult = false;
      screen = GAMES;
      dirty = true;
    }
    return;
  }
  if (!ultimateGameActive) return;
  if (now >= ultimateGameUntil) { ultimateFinishGame(now); return; }

  if (ultimateGameMode == UGM_BERRY) {
    if (now - ultimateGameStep >= 55) {
      uint32_t steps = (now - ultimateGameStep) / 55;
      if (steps > 4) steps = 4;
      ultimateGameStep += steps * 55;
      ultimateObjY += ultimateObjV * (int)steps;
      if (ultimateObjY >= 111) {
        if (abs(ultimateObjX - ultimatePlayerX) <= 23) {
          ultimateGameScore += 5;
          sfxPlay(SFX_TAP);
        }
        ultimateObjX = 25 + random(190);
        ultimateObjY = 18;
        ultimateObjV = 2 + std::min<int>(4, ultimateGameScore / 20);
      }
    }
  } else if (ultimateGameMode == UGM_REACTION) {
    if (ultimateReactionState == 0 && now >= ultimatePromptAt) {
      ultimateReactionState = 1;
      ultimatePromptStart = now;
      sfxPlay(SFX_TAP);
      dirty = true;
    } else if (ultimateReactionState == 1 && now - ultimatePromptStart > 1400) {
      ultimateNextReaction(now);
      dirty = true;
    }
  }
}

static void ultimateGameArrow(uint8_t dir, uint32_t now) {
  if (!ultimateGameActive || ultimateGameResult) return;
  if (ultimateGameMode == UGM_MEMORY) {
    if (now - ultimateMemoryShowStart < 3900) return;
    if (dir == ultimateMemorySeq[ultimateMemoryInput]) {
      ultimateGameScore += 10;
      sfxPlay(SFX_TAP);
      ultimateMemoryInput++;
      if (ultimateMemoryInput >= 6) ultimateFinishGame(now);
    } else {
      sfxPlay(SFX_DENY);
      ultimateFinishGame(now);
    }
  } else if (ultimateGameMode == UGM_TARGET) {
    if (dir == 0) ultimatePlayerY = std::max(25, ultimatePlayerY - 7);
    if (dir == 1) ultimatePlayerX = std::max(20, ultimatePlayerX - 7);
    if (dir == 2) ultimatePlayerY = std::min(108, ultimatePlayerY + 7);
    if (dir == 3) ultimatePlayerX = std::min(220, ultimatePlayerX + 7);
  } else if (ultimateGameMode == UGM_SPECIES) {
    if (dir == ultimateSpeciesPrompt) {
      ultimateGameScore += 8;
      ultimateSpeciesFlashUntil = now + 220;
      sfxPlay(SFX_PLAY);
    } else {
      sfxPlay(SFX_DENY);
    }
    ultimateSpeciesPrompt = random(4);
  }
  dirty = true;
}

static void ultimateGameAction(uint32_t now) {
  if (!ultimateGameActive || ultimateGameResult) return;
  if (ultimateGameMode == UGM_REACTION) {
    if (ultimateReactionState == 0) {
      sfxPlay(SFX_DENY); // false start
      ultimateNextReaction(now);
    } else {
      uint32_t ms = now - ultimatePromptStart;
      uint16_t pts = ms >= 1000 ? 1 : (uint16_t)(50 - std::min<uint32_t>(49, ms / 20));
      ultimateGameScore += pts;
      ultimateNextReaction(now);
      sfxPlay(SFX_PLAY);
    }
  } else if (ultimateGameMode == UGM_RACE) {
    uint16_t boost = (uint16_t)(3 + std::min<uint16_t>(3, pet.speStat() / 80));
    ultimateRaceDistance = (uint16_t)std::min<int>(999, ultimateRaceDistance + boost);
    ultimateGameScore = ultimateRaceDistance;
    sfxPlay(SFX_TAP);
  } else if (ultimateGameMode == UGM_TARGET) {
    if (abs(ultimatePlayerX - ultimateTargetX) <= 15 && abs(ultimatePlayerY - ultimateTargetY) <= 15) {
      ultimateGameScore += 12;
      sfxPlay(SFX_PLAY);
    } else {
      sfxPlay(SFX_DENY);
    }
    ultimateNewTarget();
  }
  dirty = true;
}

static const char* ultimateArrowGlyph(uint8_t d) {
  static const char *g[4] = {"^","<","v",">"};
  return g[d & 3];
}

static void drawUltimateGameMenu() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("MINIGAMES", 120, 4, 1);
  for (int i = 0; i < UGM_COUNT; ++i) {
    int y = 24 + i * 16;
    bool sel = ultimateGameMenuSel == i;
    ui.fillRoundRect(18, y, 204, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(18, y, 204, 13, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextSize(1); ui.setTextColor(UI_INK);
    ui.drawString(ULT_GAME_NAME[i], 25, y + 4);
    char hi[12]; snprintf(hi, sizeof(hi), "HI %u", ultimateGameHi[i]);
    ui.drawRightString(hi, 214, y + 4, 1);
  }
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ENTER PLAY   ESC HOME", 120, 123, 1);
}

static void drawUltimateGame(uint32_t now) {
  uint8_t biome = pet.speciesId > 0 ? DEX_TBL[pet.speciesId].biome : 0;
  drawScene(biome, now, sceneNight(), 135);
  uint16_t ink = sceneNight() ? UI_INK_NIGHT : UI_INK;

  if (ultimateGameResult) {
    ui.fillRoundRect(32, 29, 176, 76, 10, UI_CREAM);
    ui.drawRoundRect(32, 29, 176, 76, 10, UI_WARN);
    ui.setTextColor(UI_INK); ui.setTextSize(2);
    ui.drawCentreString(ultimateGameNewHi ? "NEW RECORD!" : "COMPLETE!", 120, 40, 1);
    char sc[28]; snprintf(sc, sizeof(sc), "SCORE %u", ultimateGameScore);
    ui.drawCentreString(sc, 120, 67, 1);
    ui.setTextSize(1); ui.drawCentreString("Coins earned automatically", 120, 91, 1);
    return;
  }

  char head[40]; snprintf(head, sizeof(head), "%s  %u", ULT_GAME_NAME[ultimateGameMode], ultimateGameScore);
  ui.setTextColor(ink); ui.setTextSize(1); ui.drawCentreString(head, 120, 3, 1);
  uint32_t left = ultimateGameUntil > now ? ultimateGameUntil - now : 0;
  ui.fillRoundRect(54, 14, 132, 5, 2, UI_TRACK);
  int fw = (int)std::min<uint32_t>(128, left * 128 / 30000UL);
  if (fw > 0) ui.fillRoundRect(56, 15, fw, 3, 1, UI_OK);

  if (ultimateGameMode == UGM_BERRY) {
    drawBerryIcon(ui, ultimateObjX, ultimateObjY, (ultimateObjX / 17) % 3 == 0 ? 0xF800 : UI_PINK);
    ui.fillRoundRect(ultimatePlayerX - 20, 110, 40, 9, 4, C565(0xb5,0x77,0x39));
    ui.drawRoundRect(ultimatePlayerX - 20, 110, 40, 9, 4, ink);
    ui.drawCentreString("LEFT / RIGHT", 120, 124, 1);
  } else if (ultimateGameMode == UGM_REACTION) {
    ui.setTextSize(4);
    ui.setTextColor(ultimateReactionState ? UI_OK : UI_WARN);
    ui.drawCentreString(ultimateReactionState ? "GO!" : "WAIT", 120, 49, 1);
    ui.setTextSize(1); ui.setTextColor(ink); ui.drawCentreString("SPACE / ENTER when GO appears", 120, 107, 1);
  } else if (ultimateGameMode == UGM_MEMORY) {
    uint32_t elapsed = now - ultimateMemoryShowStart;
    ui.setTextSize(4); ui.setTextColor(UI_WARN);
    if (elapsed < 3600) {
      int idx = std::min<int>(5, elapsed / 600);
      ui.drawCentreString(ultimateArrowGlyph(ultimateMemorySeq[idx]), 120, 49, 1);
      ui.setTextSize(1); ui.setTextColor(ink); ui.drawCentreString("MEMORIZE", 120, 100, 1);
    } else {
      ui.drawCentreString("?", 120, 49, 1);
      ui.setTextSize(1); ui.setTextColor(ink); ui.drawCentreString("REPEAT WITH ARROWS", 120, 100, 1);
    }
  } else if (ultimateGameMode == UGM_RACE) {
    ui.drawFastHLine(12, 105, 216, ink);
    int px = 22 + std::min<int>(190, ultimateRaceDistance / 3);
    ensureSprite(pet.speciesId, pet.shiny);
    if (mon.loaded()) mon.draw(ui, mon.has(PMD_WALKR) ? PMD_WALKR : PMD_IDLE, px, 104, now, 1);
    ui.setTextSize(1); ui.setTextColor(ink); ui.drawCentreString("MASH SPACE / ENTER", 120, 123, 1);
  } else if (ultimateGameMode == UGM_TARGET) {
    ui.drawCircle(ultimateTargetX, ultimateTargetY, 10, UI_BAD);
    ui.drawCircle(ultimateTargetX, ultimateTargetY, 4, UI_WARN);
    ui.drawFastHLine(ultimatePlayerX - 8, ultimatePlayerY, 17, ink);
    ui.drawFastVLine(ultimatePlayerX, ultimatePlayerY - 8, 17, ink);
    ui.setTextSize(1); ui.drawCentreString("ARROWS AIM   ENTER FIRE", 120, 123, 1);
  } else {
    ensureSprite(pet.speciesId, pet.shiny);
    if (mon.loaded()) {
      uint8_t a = now < ultimateSpeciesFlashUntil && mon.has(PMD_ATTACK) ? PMD_ATTACK : PMD_POSE;
      mon.draw(ui, a, 120, 100, now, 1);
    }
    ui.setTextSize(3); ui.setTextColor(DEX_TBL[pet.speciesId].accent);
    ui.drawCentreString(ultimateArrowGlyph(ultimateSpeciesPrompt), 120, 25, 1);
    ui.setTextSize(1); ui.setTextColor(ink);
    String line = String(dexName(pet.speciesId)) + " challenge - match the arrow";
    ui.drawCentreString(line, 120, 120, 1);
  }
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text:
    fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

text = rep(text,
    "  loadUltimateEconomy();\n  displayLastActivity = millis();",
    "  loadUltimateEconomy();\n  loadUltimateGames();\n  displayLastActivity = millis();",
    "setup game config load")

# Do not blank the display during any timing minigame.
text = text.replace("if (screen == PLAY || screen == TRAIN) return;",
                    "if (screen == PLAY || screen == TRAIN || screen == ULT_GAME) return;", 1)

# Render new screens.
render_anchor = "      case SHOP:       drawUltimateShop(); break;"
if render_anchor not in text: fail("Phase 5 render case")
text = text.replace(render_anchor,
    render_anchor + "\n      case GAMES:      drawUltimateGameMenu(); break;\n      case ULT_GAME:   drawUltimateGame(now); break;", 1)

# Update loop every frame/tick.
text = rep(text,
    "  updatePlay(now);\n  updateTrain(now);",
    "  updatePlay(now);\n  updateTrain(now);\n  updateUltimateGame(now);",
    "loop game update")

# Mark the active Ultimate minigame animated and use fast render cadence.
text = text.replace("if (screen == PLAY || screen == TRAIN) return true;",
                    "if (screen == PLAY || screen == TRAIN || screen == ULT_GAME) return true;", 1)
text = text.replace("uint32_t interval = (screen == PLAY || screen == TRAIN) ? 70 : 100;",
                    "uint32_t interval = (screen == PLAY || screen == TRAIN || screen == ULT_GAME) ? 70 : 100;", 1)

# Input before INVENTORY branch.
input_anchor = "  } else if (screen == INVENTORY) {"
if input_anchor not in text: fail("Phase 5 input branch")
game_input = r'''  } else if (screen == GAMES) {
    if (upEdge) { ultimateGameMenuSel = ultimateGameMenuSel == 0 ? UGM_COUNT - 1 : ultimateGameMenuSel - 1; dirty = true; }
    if (downEdge) { ultimateGameMenuSel = (ultimateGameMenuSel + 1) % UGM_COUNT; dirty = true; }
    if (enterEdge || spaceEdge) startUltimateGame((UltimateGameMode)ultimateGameMenuSel);
    if (escEdge || backEdge) { screen = HOME; dirty = true; }
  } else if (screen == ULT_GAME) {
    if (ultimateGameResult) {
      if (enterEdge || spaceEdge || escEdge || backEdge) { ultimateGameResult = false; screen = GAMES; dirty = true; }
    } else {
      if (upEdge) ultimateGameArrow(0, millis());
      if (leftEdge) ultimateGameArrow(1, millis());
      if (downEdge) ultimateGameArrow(2, millis());
      if (rightEdge) ultimateGameArrow(3, millis());
      if (ultimateGameMode == UGM_BERRY) {
        if (leftEdge) ultimatePlayerX = std::max(24, ultimatePlayerX - 14);
        if (rightEdge) ultimatePlayerX = std::min(216, ultimatePlayerX + 14);
      }
      if (enterEdge || spaceEdge) ultimateGameAction(millis());
      if (escEdge || backEdge) { ultimateGameActive = false; ultimateGameResult = false; screen = GAMES; dirty = true; }
    }
'''
text = text.replace(input_anchor, game_input + input_anchor, 1)

# M opens the expanded game center from Home.
key_anchor = "      } else if (c == 'v') {"
if key_anchor not in text: fail("Phase 5 Home keys")
text = text.replace(key_anchor,
    "      } else if (c == 'm') {\n"
    "        ultimateGameMenuSel = 0; screen = GAMES; dirty = true;\n"
    + key_anchor, 1)

# Controls hint.
text = text.replace('    "E: evolve   G: farewell/runaway",',
                    '    "M: games   E: evolve   G: goodbye",', 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p6] Added berry catch, reaction, memory, race, target and species challenge games")
