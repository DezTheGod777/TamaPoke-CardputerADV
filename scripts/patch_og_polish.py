Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// OG_POLISH_V0854"


def fail(msg):
    print(f"[v0.8.5.4] ERROR: {msg}")
    env.Exit(1)


def replace_once(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.8.5.4] OG polish already applied")
    Return()

# ---------------------------------------------------------------------------
# Version + new screens/state
# ---------------------------------------------------------------------------
text = replace_once(
    text,
    "static constexpr uint16_t UI_PINK      = 0xECF3;\n",
    "static constexpr uint16_t UI_PINK      = 0xECF3;\n\n"
    f"{MARKER}\n"
    "static constexpr const char *FIRMWARE_VERSION = \"v0.8.5.4\";\n"
    "static constexpr const char *FIRMWARE_NAME = \"TamaPoke ADV\";\n",
    "UI palette",
)

text = replace_once(
    text,
    "  HELP,\n  PLAY,",
    "  HELP,\n  EVENTS,\n  ABOUT,\n  PLAY,",
    "screen enum",
)

text = replace_once(
    text,
    "static uint32_t displayLastActivity = 0;\nstatic const char *DISPLAY_CFG_PATH = \"/tamapoke_display.cfg\";",
    "static uint32_t displayLastActivity = 0;\n"
    "static bool idleTerrarium = false;\n"
    "static constexpr uint32_t IDLE_TERRARIUM_MS = 30000;\n"
    "static int batteryLevel = -1;\n"
    "static int batteryVoltage = 0;\n"
    "static uint32_t lastBatterySample = 0;\n"
    "static uint32_t saveIndicatorUntil = 0;\n"
    "static bool lowBatteryNotified = false;\n"
    "static String recentEvents[6];\n"
    "static uint8_t recentEventCount = 0;\n"
    "static const char *EVENT_LOG_PATH = \"/tamapoke_events.log\";\n"
    "static const char *DISPLAY_CFG_PATH = \"/tamapoke_display.cfg\";",
    "display state",
)

# Fix the stale-loop-time underflow that could instantly blank the backlight
# immediately after a key updated displayLastActivity with a newer millis().
old_service = '''static void serviceDisplaySleep(uint32_t now) {
  if (displaySleeping) return;
  uint16_t secs = DISPLAY_TIMEOUT_SEC[displayTimeoutIdx];
  if (!secs) return;

  // Don't blank the display in the middle of an active timing-based minigame.
  if (screen == PLAY || screen == TRAIN) return;

  if (now - displayLastActivity >= (uint32_t)secs * 1000UL) {
    sleepDisplay();
  }
}'''
new_service = '''static void serviceDisplaySleep(uint32_t /*now*/) {
  if (displaySleeping) return;
  uint16_t secs = DISPLAY_TIMEOUT_SEC[displayTimeoutIdx];
  if (!secs) return;

  // Don't blank the display in the middle of an active timing-based minigame.
  if (screen == PLAY || screen == TRAIN) return;

  // Always sample millis() AFTER input handling. The previous implementation
  // could compare an older loop timestamp with a newer displayLastActivity,
  // unsigned-wrap the subtraction, and falsely trigger an instant timeout.
  uint32_t current = millis();
  if ((uint32_t)(current - displayLastActivity) >= (uint32_t)secs * 1000UL) {
    sleepDisplay();
  }
}'''
text = replace_once(text, old_service, new_service, "display timeout service")

# ---------------------------------------------------------------------------
# Battery, save indicator, event history, About, recovery, special FX
# Insert after color helpers so C565/lerp565 are available.
# ---------------------------------------------------------------------------
helpers = r'''

static void sampleBattery(bool force = false) {
  uint32_t now = millis();
  if (!force && now - lastBatterySample < 5000) return;
  lastBatterySample = now;
  int lv = M5Cardputer.Power.getBatteryLevel();
  int mv = M5Cardputer.Power.getBatteryVoltage();
  if (lv >= 0 && lv <= 100) batteryLevel = lv;
  if (mv > 0) batteryVoltage = mv;

  if (batteryLevel >= 0 && batteryLevel <= 15 && !lowBatteryNotified) {
    lowBatteryNotified = true;
    recentEvents[0] = "Low battery";
    if (recentEventCount < 1) recentEventCount = 1;
  } else if (batteryLevel > 20) {
    lowBatteryNotified = false;
  }
}

static void pushEventMemory(const String &s) {
  if (!s.length()) return;
  if (recentEventCount < 6) ++recentEventCount;
  for (int i = recentEventCount - 1; i > 0; --i) recentEvents[i] = recentEvents[i - 1];
  recentEvents[0] = s;
}

static void noteEvent(const String &s) {
  pushEventMemory(s);
  if (!sdReady) return;
  File f = SD.open(EVENT_LOG_PATH, FILE_APPEND);
  if (!f) return;
  f.println(s);
  f.close();
}

static void loadRecentEvents() {
  recentEventCount = 0;
  if (!sdReady) return;
  File f = SD.open(EVENT_LOG_PATH, FILE_READ);
  if (!f) return;
  String line;
  while (f.available()) {
    char c = (char)f.read();
    if (c == '\n' || c == '\r') {
      line.trim();
      if (line.length()) pushEventMemory(line);
      line = "";
    } else if (line.length() < 46) {
      line += c;
    }
  }
  line.trim();
  if (line.length()) pushEventMemory(line);
  f.close();
}

static void drawBatteryMeter() {
  sampleBattery();
  const int x = 218, y = 3;
  uint16_t outline = sceneNight() ? UI_INK_NIGHT : UI_INK;
  uint16_t fill = UI_OK;
  if (batteryLevel >= 0 && batteryLevel <= 15) fill = UI_BAD;
  else if (batteryLevel >= 0 && batteryLevel <= 35) fill = UI_WARN;

  ui.drawRoundRect(x, y, 18, 9, 2, outline);
  ui.fillRect(x + 18, y + 3, 2, 3, outline);
  if (batteryLevel >= 0) {
    int fw = (14 * batteryLevel) / 100;
    if (fw > 0) ui.fillRect(x + 2, y + 2, fw, 5, fill);
  } else {
    ui.drawLine(x + 4, y + 2, x + 13, y + 6, outline);
  }
}

static void drawSaveIndicator(uint32_t now) {
  if (now >= saveIndicatorUntil) return;
  uint16_t bg = sceneNight() ? C565(0x18,0x20,0x34) : UI_WHITE;
  uint16_t ink = sceneNight() ? UI_INK_NIGHT : UI_OK;
  ui.fillRoundRect(2, 2, 31, 12, 4, bg);
  ui.drawRoundRect(2, 2, 31, 12, 4, ink);
  ui.setTextSize(1);
  ui.setTextColor(ink);
  ui.drawString("SAVE", 6, 5);
  ui.drawLine(25, 8, 27, 10, ink);
  ui.drawLine(27, 10, 31, 5, ink);
}

static void drawSystemOverlays(uint32_t now) {
  drawBatteryMeter();
  drawSaveIndicator(now);
}

static void resetDisplaySettings() {
  displayBrightnessIdx = 2; // 50%
  displayTimeoutIdx = 3;    // 2 minutes
  displaySleeping = false;
  displayLastActivity = millis();
  M5Cardputer.Display.setBrightness(displayBrightnessRaw());
  saveDisplayConfig();
  say("Display reset");
}

static void drawEvents() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("RECENT EVENTS", 120, 5, 1);
  ui.setTextSize(1);
  if (!recentEventCount) {
    ui.setTextColor(C565(0x6d,0x6b,0x68));
    ui.drawCentreString("No events yet", 120, 59, 1);
  } else {
    for (int i = 0; i < recentEventCount && i < 6; ++i) {
      int y = 26 + i * 15;
      ui.fillRoundRect(13, y, 214, 12, 3, i == 0 ? UI_WHITE : lerp565(UI_CREAM, UI_WHITE, 1, 3));
      ui.setTextColor(i == 0 ? UI_INK : C565(0x4f,0x4f,0x4f));
      String s = recentEvents[i];
      if (s.length() > 34) s = s.substring(0, 34);
      ui.drawString(s, 19, y + 3);
    }
  }
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ENTER / ESC = BACK", 120, 123, 1);
}

static void drawAbout() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("TAMAPOKE ADV", 120, 5, 1);
  ui.setTextSize(1);
  ui.setTextColor(UI_BAD);
  ui.drawCentreString(FIRMWARE_VERSION, 120, 25, 1);
  ui.setTextColor(UI_INK);
  ui.drawCentreString("M5Stack Cardputer ADV port", 120, 40, 1);
  ui.drawCentreString("Original: socquique/TamaPoke", 120, 54, 1);

  char sdLine[30];
  snprintf(sdLine, sizeof(sdLine), "microSD: %s", sdReady ? "READY" : "MISSING");
  ui.drawCentreString(sdLine, 120, 72, 1);

  sampleBattery(true);
  char bat[36];
  if (batteryLevel >= 0)
    snprintf(bat, sizeof(bat), "Battery: %d%%  %dmV", batteryLevel, batteryVoltage);
  else
    snprintf(bat, sizeof(bat), "Battery: unavailable");
  ui.drawCentreString(bat, 120, 86, 1);
  ui.drawCentreString("Save: /tamapoke_v7_a/b.bin", 120, 100, 1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ENTER / ESC = BACK", 120, 122, 1);
}

static void drawShinySparkles(int cx, int cy, uint32_t now) {
  static const int8_t p[8][2] = {{-28,-16},{25,-12},{-20,15},{30,11},{-36,1},{36,-1},{-8,-24},{12,22}};
  for (int i = 0; i < 8; ++i) {
    if (((now / 160) + i) & 1) continue;
    int x = cx + p[i][0], y = cy + p[i][1];
    ui.drawFastHLine(x - 2, y, 5, UI_WARN);
    ui.drawFastVLine(x, y - 2, 5, UI_WARN);
    ui.fillCircle(x, y, 1, UI_WHITE);
  }
}

static void drawGhostAtmosphere(uint32_t now) {
  if (pet.speciesId < 92 || pet.speciesId > 94) return;
  uint16_t purple = C565(0x84,0x4d,0xb8);
  uint16_t violet = C565(0x4c,0x2a,0x78);
  for (int i = 0; i < 6; ++i) {
    int x = (i * 47 + (int)(now / (70 + i * 8))) % 270 - 15;
    int y = 25 + (i * 17) % 55 + (int)(4 * sinf(now / 300.0f + i));
    int r = 7 + (i & 3);
    ui.drawCircle(x, y, r, (i & 1) ? purple : violet);
    if ((i & 1) == 0) ui.drawCircle(x, y, r + 3, violet);
  }
  if (pet.speciesId == 94) {
    for (int i = 0; i < 4; ++i) {
      int x = 50 + ((i * 43 + now / 45) % 145);
      int y = 38 + ((i * 19 + now / 80) % 38);
      ui.drawFastHLine(x - 2, y, 5, UI_PINK);
      ui.drawFastVLine(x, y - 2, 5, UI_PINK);
    }
  }
}
'''
text = replace_once(
    text,
    "static int sceneHour() {",
    helpers + "\nstatic int sceneHour() {",
    "sceneHour insertion",
)

# Forward declaration required because resetDisplaySettings() above calls say().
# Move say declaration before helpers by declaring it early.
text = replace_once(
    text,
    "static String toast;\nstatic uint32_t toastUntil = 0;",
    "static String toast;\nstatic uint32_t toastUntil = 0;\nstatic void say(const String &s, uint32_t ms);",
    "say forward declaration",
)
# Definition keeps a default only here.
text = text.replace("static void say(const String &s, uint32_t ms = 1800) {", "static void say(const String &s, uint32_t ms) {", 1)

# ---------------------------------------------------------------------------
# Richer ambient behavior + Ghost/Shiny visual treatment + true idle mode
# ---------------------------------------------------------------------------
text = replace_once(
    text,
    "static const uint8_t flair[] = {PMD_POSE, PMD_NOD, PMD_BREATH};",
    "static const uint8_t flair[] = {PMD_POSE, PMD_NOD, PMD_BREATH, PMD_SIT, PMD_HOP};",
    "ambient action list",
)

text = replace_once(
    text,
    "  drawScene(biome, now, sceneNight(), 90);\n\n  if (pet.isEgg()) {",
    "  drawScene(biome, now, sceneNight(), idleTerrarium ? 135 : 90);\n"
    "  if (!pet.isEgg()) drawGhostAtmosphere(now);\n\n"
    "  if (pet.isEgg()) {",
    "home scene",
)

text = replace_once(
    text,
    "      mon.draw(ui, currentAction(now), petX, 88, now, -1);\n    } else {",
    "      mon.draw(ui, currentAction(now), petX, idleTerrarium ? 118 : 88, now, -1);\n"
    "      if (pet.shiny) drawShinySparkles(petX, idleTerrarium ? 78 : 55, now);\n"
    "    } else {",
    "home sprite draw",
)

text = replace_once(
    text,
    "  drawBathFx(now);\n  if (showHomeHeader) drawHeaderText();\n  drawHomePanel();\n  drawFeedOverlay();\n  drawToast();",
    "  drawBathFx(now);\n"
    "  if (!idleTerrarium) {\n"
    "    if (showHomeHeader) drawHeaderText();\n"
    "    drawHomePanel();\n"
    "    drawFeedOverlay();\n"
    "    drawToast();\n"
    "  } else {\n"
    "    ui.setTextSize(1);\n"
    "    ui.setTextColor(sceneNight() ? UI_INK_NIGHT : UI_INK);\n"
    "    ui.drawString(\"IDLE\", 4, 124);\n"
    "  }",
    "home overlays",
)

# Pokédex: give shiny discoveries an unmistakable label/effect.
text = replace_once(
    text,
    "  if (mon.loaded()) mon.draw(ui, PMD_IDLE, 120, 91, known ? now : 0, 0, !known, UI_INK);\n\n  ui.setTextSize(1);",
    "  if (mon.loaded()) mon.draw(ui, PMD_IDLE, 120, 91, known ? now : 0, 0, !known, UI_INK);\n"
    "  if (known && pet.isShinyRegistered(dexCursor)) {\n"
    "    drawShinySparkles(120, 59, now);\n"
    "    ui.setTextSize(1); ui.setTextColor(UI_WARN); ui.drawString(\"SHINY\", 184, 22);\n"
    "  }\n\n"
    "  ui.setTextSize(1);",
    "dex shiny detail",
)

# ---------------------------------------------------------------------------
# Settings: remove manual-screen-off row, add Events/About/Recovery.
# ---------------------------------------------------------------------------
settings_start = text.find("static void drawSettings() {")
settings_end = text.find("\nstatic void drawHelp() {", settings_start)
if settings_start < 0 or settings_end < 0:
    fail("could not locate drawSettings function")
new_settings = r'''static void drawSettings() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("SETTINGS", 120, 4, 1);

  char brightnessLabel[28];
  snprintf(brightnessLabel, sizeof(brightnessLabel), "BRIGHTNESS: %u%%",
           DISPLAY_BRIGHTNESS_PCT[displayBrightnessIdx]);

  char timeoutLabel[30];
  snprintf(timeoutLabel, sizeof(timeoutLabel), "SCREEN OFF: %s",
           DISPLAY_TIMEOUT_LABEL[displayTimeoutIdx]);

  const char *items[10] = {
    audioEnabled() ? "SOUND: ON" : "SOUND: OFF",
    brightnessLabel,
    timeoutLabel,
    "POKEDEX",
    "CONTROLS",
    "RECENT EVENTS",
    "ABOUT / VERSION",
    "RESET DISPLAY",
    "RELEASE POKEMON",
    "BACK"
  };

  int top = 0;
  if (settingsSel > 2) top = settingsSel - 2;
  if (top > 4) top = 4;

  for (int row = 0; row < 6; ++row) {
    int i = top + row;
    int y = 24 + row * 16;
    bool sel = i == settingsSel;
    ui.fillRoundRect(34, y, 172, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(34, y, 172, 13, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextSize(1);
    ui.setTextColor(i == 8 ? UI_BAD : UI_INK);
    ui.drawCentreString(items[i], 120, y + 4, 1);
  }

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  if (top > 0) ui.drawString("^", 214, 25);
  if (top < 4) ui.drawString("v", 214, 105);
  ui.drawString(FIRMWARE_VERSION, 4, 123);
  ui.drawCentreString("LEFT/RIGHT ADJUST  ENTER SELECT", 128, 123, 1);
}'''
text = text[:settings_start] + new_settings + text[settings_end:]

old_settings_input = r'''  } else if (screen == SETTINGS) {
    if (upEdge) {
      settingsSel = settingsSel == 0 ? 7 : settingsSel - 1;
      dirty = true;
    }
    if (downEdge) {
      settingsSel = (settingsSel + 1) % 8;
      dirty = true;
    }

    if (leftEdge || rightEdge) {
      int delta = rightEdge ? 1 : -1;
      if (settingsSel == 1) adjustBrightness(delta);
      else if (settingsSel == 2) adjustDisplayTimeout(delta);
    }

    if (enterEdge || spaceEdge) {
      if (settingsSel == 0) {
        audioSetEnabled(!audioEnabled());
        if (audioEnabled()) sfxPlay(SFX_TAP);
        dirty = true;
      } else if (settingsSel == 1) {
        adjustBrightness(1);
      } else if (settingsSel == 2) {
        adjustDisplayTimeout(1);
      } else if (settingsSel == 3) {
        sleepDisplay();
      } else if (settingsSel == 4) {
        dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;
        screen = DEX_GRID;
        dexGridDirty = true;
        dirty = true;
      } else if (settingsSel == 5) {
        screen = HELP;
        dirty = true;
      } else if (settingsSel == 6) {
        if (!pet.isEgg()) openDialog(DLG_RELEASE);
      } else {
        screen = HOME;
        dirty = true;
      }
    }
    if (escEdge || backEdge) {
      screen = HOME;
      dirty = true;
    }
  } else if (screen == HELP) {'''
new_settings_input = r'''  } else if (screen == SETTINGS) {
    if (upEdge) {
      settingsSel = settingsSel == 0 ? 9 : settingsSel - 1;
      dirty = true;
    }
    if (downEdge) {
      settingsSel = (settingsSel + 1) % 10;
      dirty = true;
    }

    if (leftEdge || rightEdge) {
      int delta = rightEdge ? 1 : -1;
      if (settingsSel == 1) adjustBrightness(delta);
      else if (settingsSel == 2) adjustDisplayTimeout(delta);
    }

    if (enterEdge || spaceEdge) {
      if (settingsSel == 0) {
        audioSetEnabled(!audioEnabled());
        if (audioEnabled()) sfxPlay(SFX_TAP);
        dirty = true;
      } else if (settingsSel == 1) {
        adjustBrightness(1);
      } else if (settingsSel == 2) {
        adjustDisplayTimeout(1);
      } else if (settingsSel == 3) {
        dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;
        screen = DEX_GRID;
        dexGridDirty = true;
        dirty = true;
      } else if (settingsSel == 4) {
        screen = HELP;
        dirty = true;
      } else if (settingsSel == 5) {
        screen = EVENTS;
        dirty = true;
      } else if (settingsSel == 6) {
        screen = ABOUT;
        dirty = true;
      } else if (settingsSel == 7) {
        resetDisplaySettings();
      } else if (settingsSel == 8) {
        if (!pet.isEgg()) openDialog(DLG_RELEASE);
      } else {
        screen = HOME;
        dirty = true;
      }
    }
    if (escEdge || backEdge) {
      screen = HOME;
      dirty = true;
    }
  } else if (screen == EVENTS || screen == ABOUT) {
    if (escEdge || backEdge || enterEdge || spaceEdge) {
      screen = SETTINGS;
      dirty = true;
    }
  } else if (screen == HELP) {'''
text = replace_once(text, old_settings_input, new_settings_input, "settings input handler")

# Waking from the terrarium consumes the first key just like display wake.
text = replace_once(
    text,
    "  if (anyKeyNow) displayLastActivity = millis();\n\n  if (screen == RENAME) {",
    "  if (anyKeyNow) displayLastActivity = millis();\n"
    "  if (idleTerrarium && anyKeyNow) {\n"
    "    idleTerrarium = false;\n"
    "    dirty = true;\n"
    "    goto save_input_state;\n"
    "  }\n\n"
    "  if (screen == RENAME) {",
    "idle wake handling",
)

# Meaningful history entries.
text = replace_once(
    text,
    "    pet.rename(renameBuf);\n    screen = CARD;\n    say(\"Name saved\");",
    "    pet.rename(renameBuf);\n    noteEvent(String(\"Renamed to \") + renameBuf);\n    screen = CARD;\n    say(\"Name saved\");",
    "rename event",
)
text = replace_once(
    text,
    "    pet.evolve();\n    if (sdReady && old > 0) evoOld.load(old, oldShiny);",
    "    pet.evolve();\n    noteEvent(String(\"Evolved to \") + dexName(pet.speciesId));\n    if (sdReady && old > 0) evoOld.load(old, oldShiny);",
    "evolution event",
)
text = replace_once(
    text,
    "      say(String(dexName(STARTERS[starterSel])) + \" chosen!\");",
    "      noteEvent(String(\"Starter: \") + dexName(STARTERS[starterSel]));\n"
    "      say(String(dexName(STARTERS[starterSel])) + \" chosen!\");",
    "starter event",
)

# ---------------------------------------------------------------------------
# Rendering / loop integration: battery overlay, G0 screen toggle, idle mode,
# safe timeout timestamp, save confirmation.
# ---------------------------------------------------------------------------
text = replace_once(
    text,
    "      case SETTINGS:   drawSettings(); break;\n      case HELP:       drawHelp(); break;",
    "      case SETTINGS:   drawSettings(); break;\n"
    "      case HELP:       drawHelp(); break;\n"
    "      case EVENTS:     drawEvents(); break;\n"
    "      case ABOUT:      drawAbout(); break;",
    "render switch",
)

text = replace_once(
    text,
    "  // One complete RGB565 frame is pushed after all drawing is finished.\n  // The LCD never sees a black clear followed by partial drawing.\n  ui.pushSprite(0, 0);",
    "  drawSystemOverlays(now);\n\n"
    "  // One complete RGB565 frame is pushed after all drawing is finished.\n"
    "  // The LCD never sees a black clear followed by partial drawing.\n"
    "  ui.pushSprite(0, 0);",
    "system overlay render",
)

text = replace_once(
    text,
    "  loadDisplayConfig();\n  displayLastActivity = millis();",
    "  loadDisplayConfig();\n"
    "  displayLastActivity = millis();\n"
    "  sampleBattery(true);\n"
    "  loadRecentEvents();",
    "setup system state",
)

text = replace_once(
    text,
    "void loop() {\n  M5Cardputer.update();\n  uint32_t now = millis();\n\n  pet.update(now);\n  onKeyboard();\n\n  serviceDisplaySleep(now);",
    "void loop() {\n"
    "  M5Cardputer.update();\n"
    "  uint32_t now = millis();\n\n"
    "  // The physical G0/BtnA key is the manual display toggle. The side power\n"
    "  // switch remains a real hardware power switch and is not remapped.\n"
    "  if (M5Cardputer.BtnA.wasPressed()) {\n"
    "    if (displaySleeping) wakeDisplay();\n"
    "    else sleepDisplay();\n"
    "    now = millis();\n"
    "  }\n\n"
    "  pet.update(now);\n"
    "  onKeyboard();\n\n"
    "  if (!displaySleeping && screen == HOME && !feedOpen && !pet.evolving() &&\n"
    "      !pet.ceremony && !idleTerrarium &&\n"
    "      (uint32_t)(millis() - displayLastActivity) >= IDLE_TERRARIUM_MS) {\n"
    "    idleTerrarium = true;\n"
    "    dirty = true;\n"
    "  }\n\n"
    "  sampleBattery();\n"
    "  serviceDisplaySleep(millis());",
    "main loop input/display handling",
)

text = replace_once(
    text,
    "    if (pet.savePending() && screen != PLAY && screen != TRAIN) pet.flushSave();",
    "    if (pet.savePending() && screen != PLAY && screen != TRAIN) {\n"
    "      pet.flushSave();\n"
    "      saveIndicatorUntil = millis() + 1200;\n"
    "      dirty = true;\n"
    "    }",
    "save indicator",
)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4] Applied OG polish: timeout fix, G0 toggle, battery, idle mode, About, Events, recovery, Ghost/Shiny FX")
