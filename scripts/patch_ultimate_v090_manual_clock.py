Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_MANUAL_CLOCK"


def fail(msg):
    print(f"[v0.9.0-clock] ERROR: {msg}")
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
    print("[v0.9.0-clock] manual clock already applied")
    Return()
if "// ULTIMATE_V090_PERSISTENT_TIME_CYCLE" not in text:
    fail("persistent time-cycle patch must run first")

# settimeofday() is used so the same system clock that drives sceneHour(),
# daily events, and saved lastSeenEpoch immediately follows the manual setting.
if "#include <sys/time.h>" not in text:
    if "#include <time.h>" not in text:
        fail("time include anchor missing")
    text = text.replace("#include <time.h>\n", "#include <time.h>\n#include <sys/time.h>\n", 1)

# Add a dedicated static screen without disturbing any existing Ultimate screen.
if "  SET_CLOCK," not in text:
    enum_anchor = "  SETTINGS,\n  HELP,"
    if enum_anchor not in text:
        fail("screen enum anchor missing")
    text = text.replace(enum_anchor, "  SETTINGS,\n  SET_CLOCK,\n  HELP,", 1)

# Small editor state. 0=hour, 1=minute.
state_anchor = "static uint8_t settingsSel = 0;"
if state_anchor not in text:
    fail("settings state anchor missing")
text = text.replace(
    state_anchor,
    state_anchor + "\n"
    "static uint8_t manualClockField = 0;\n"
    "static int manualClockHour = 12;\n"
    "static int manualClockMinute = 0;\n"
    "static bool manualClockHadValidTime = false;\n"
    + MARKER,
    1,
)

# Insert clock helpers after sceneHour(), preserving the original TamaPoke
# sunrise/day/sunset/night thresholds exactly as they are.
scene_next = "static bool sceneNight() {"
pos = text.find(scene_next)
if pos < 0:
    fail("sceneNight anchor missing")
clock_helpers = r'''
static bool manualClockReadLocal(struct tm &ti) {
  time_t now = time(nullptr);
  if (now >= 1700000000 && localtime_r(&now, &ti) != nullptr) return true;

  if (pet.lastSeenEpoch >= 1700000000UL) {
    time_t saved = (time_t)pet.lastSeenEpoch;
    if (localtime_r(&saved, &ti) != nullptr) return true;
  }
  return false;
}

static void openManualClock() {
  struct tm ti{};
  manualClockHadValidTime = manualClockReadLocal(ti);
  if (manualClockHadValidTime) {
    manualClockHour = ti.tm_hour;
    manualClockMinute = ti.tm_min;
  } else {
    manualClockHour = 12;
    manualClockMinute = 0;
  }
  manualClockField = 0;
  screen = SET_CLOCK;
  dirty = true;
}

static void adjustManualClock(int delta) {
  if (manualClockField == 0) {
    manualClockHour = (manualClockHour + delta) % 24;
    if (manualClockHour < 0) manualClockHour += 24;
  } else {
    manualClockMinute = (manualClockMinute + delta) % 60;
    if (manualClockMinute < 0) manualClockMinute += 60;
  }
  dirty = true;
}

static void applyManualClock() {
  // Keep the known local calendar date and replace only hour/minute, just like
  // original TamaPoke's clock editor. If this device has never known a real
  // date, use a harmless seed date until a future NTP sync supplies the date.
  setenv("TZ", TAMAPOKE_TZ, 1);
  tzset();

  struct tm ti{};
  if (!manualClockReadLocal(ti)) {
    ti.tm_year = 2026 - 1900;
    ti.tm_mon = 0;
    ti.tm_mday = 1;
    ti.tm_isdst = -1;
  }
  ti.tm_hour = manualClockHour;
  ti.tm_min = manualClockMinute;
  ti.tm_sec = 0;
  ti.tm_isdst = -1;

  time_t chosen = mktime(&ti);
  if (chosen < 1700000000) {
    say("Clock save failed", 1800);
    screen = SETTINGS;
    dirty = true;
    return;
  }

  struct timeval tv{};
  tv.tv_sec = chosen;
  tv.tv_usec = 0;
  settimeofday(&tv, nullptr);

  // setClock deliberately does NOT apply offline progression. Manually fixing
  // the wall clock should not suddenly age or penalize the Pokemon.
  pet.setClock((uint32_t)chosen);

  char msg[32];
  snprintf(msg, sizeof(msg), "Clock set %02d:%02d", manualClockHour, manualClockMinute);
  noteEvent(msg);
  say("Time saved", 1500);
  screen = SETTINGS;
  dirty = true;
}
'''
text = text[:pos] + clock_helpers + "\n" + text[pos:]

# Replace Settings with the same menu plus one SET CLOCK row. Nothing else in
# Settings changes.
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

  const char *items[11] = {
    audioEnabled() ? "SOUND: ON" : "SOUND: OFF",
    brightnessLabel,
    timeoutLabel,
    "SET CLOCK",
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
  if (top > 5) top = 5;

  for (int row = 0; row < 6; ++row) {
    int i = top + row;
    int y = 24 + row * 16;
    bool sel = i == settingsSel;
    ui.fillRoundRect(34, y, 172, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(34, y, 172, 13, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextSize(1);
    ui.setTextColor(i == 9 ? UI_BAD : UI_INK);
    ui.drawCentreString(items[i], 120, y + 4, 1);
  }

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  if (top > 0) ui.drawString("^", 214, 25);
  if (top < 5) ui.drawString("v", 214, 105);
  ui.drawString(FIRMWARE_VERSION, 4, 123);
  ui.drawCentreString("LEFT/RIGHT ADJUST  ENTER SELECT", 128, 123, 1);
}'''
text = replace_function(text, "static void drawSettings() {", "static void drawHelp() {",
                        new_settings, "Settings with clock")

# Clock editor: large readable 24-hour time, field highlight, simple keyboard
# instructions. 24-hour editing avoids AM/PM ambiguity while the habitat still
# follows the original TamaPoke time boundaries.
clock_draw = r'''static void drawSetClock() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("SET CLOCK", 120, 5, 1);

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Manual time - 24 hour", 120, 25, 1);

  char hh[4], mm[4];
  snprintf(hh, sizeof(hh), "%02d", manualClockHour);
  snprintf(mm, sizeof(mm), "%02d", manualClockMinute);

  uint16_t hBg = manualClockField == 0 ? C565(0xff,0xeb,0xb8) : UI_WHITE;
  uint16_t mBg = manualClockField == 1 ? C565(0xff,0xeb,0xb8) : UI_WHITE;
  uint16_t hBd = manualClockField == 0 ? UI_WARN : UI_TRACK;
  uint16_t mBd = manualClockField == 1 ? UI_WARN : UI_TRACK;

  ui.fillRoundRect(48, 43, 55, 39, 8, hBg);
  ui.drawRoundRect(48, 43, 55, 39, 8, hBd);
  ui.fillRoundRect(137, 43, 55, 39, 8, mBg);
  ui.drawRoundRect(137, 43, 55, 39, 8, mBd);

  ui.setTextSize(3);
  ui.setTextColor(UI_INK);
  ui.drawCentreString(hh, 75, 52, 1);
  ui.drawCentreString(":", 120, 52, 1);
  ui.drawCentreString(mm, 164, 52, 1);

  ui.setTextSize(1);
  ui.setTextColor(UI_INK);
  ui.drawCentreString(manualClockField == 0 ? "^ HOUR ^" : "  HOUR  ", 75, 86, 1);
  ui.drawCentreString(manualClockField == 1 ? "^ MINUTE ^" : " MINUTE ", 164, 86, 1);

  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("LEFT/RIGHT = FIELD", 120, 101, 1);
  ui.drawCentreString("UP/DOWN = CHANGE", 120, 111, 1);
  ui.setTextColor(UI_INK);
  ui.drawCentreString("ENTER SAVE    ESC CANCEL", 120, 123, 1);
}'''
# Insert immediately before Help; Settings is already directly before Help.
help_anchor = "static void drawHelp() {"
if help_anchor not in text:
    fail("drawHelp anchor missing")
text = text.replace(help_anchor, clock_draw + "\n\n" + help_anchor, 1)

# Replace the final Settings input block with the same behavior plus SET CLOCK,
# then add input handling for the editor itself.
settings_input_start = text.find("  } else if (screen == SETTINGS) {")
settings_input_end = text.find("  } else if (screen == EVENTS || screen == ABOUT) {", settings_input_start)
if settings_input_start < 0 or settings_input_end < 0:
    fail("settings keyboard handler anchor missing")
new_settings_input = r'''  } else if (screen == SETTINGS) {
    if (upEdge) {
      settingsSel = settingsSel == 0 ? 10 : settingsSel - 1;
      dirty = true;
    }
    if (downEdge) {
      settingsSel = (settingsSel + 1) % 11;
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
        openManualClock();
      } else if (settingsSel == 4) {
        dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;
        screen = DEX_GRID;
        dexGridDirty = true;
        dirty = true;
      } else if (settingsSel == 5) {
        screen = HELP;
        dirty = true;
      } else if (settingsSel == 6) {
        screen = EVENTS;
        dirty = true;
      } else if (settingsSel == 7) {
        screen = ABOUT;
        dirty = true;
      } else if (settingsSel == 8) {
        resetDisplaySettings();
      } else if (settingsSel == 9) {
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
  } else if (screen == SET_CLOCK) {
    if (leftEdge || rightEdge) {
      manualClockField = manualClockField == 0 ? 1 : 0;
      dirty = true;
    }
    if (upEdge) adjustManualClock(1);
    if (downEdge) adjustManualClock(-1);
    if (enterEdge || spaceEdge) applyManualClock();
    if (escEdge || backEdge) {
      screen = SETTINGS;
      dirty = true;
    }
'''
text = text[:settings_input_start] + new_settings_input + text[settings_input_end:]

# Render the static editor like any other menu screen.
render_anchor = "      case SETTINGS:   drawSettings(); break;\n"
if render_anchor not in text:
    fail("render Settings case missing")
text = text.replace(render_anchor,
                    render_anchor + "      case SET_CLOCK:  drawSetClock(); break;\n", 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-clock] Added original-style manual clock editor to Settings; time-cycle thresholds unchanged")
