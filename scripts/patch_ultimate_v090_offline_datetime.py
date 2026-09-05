Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_OFFLINE_DATETIME"


def fail(msg):
    print(f"[v0.9.0-datetime] ERROR: {msg}")
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
    print("[v0.9.0-datetime] offline date/time editor already applied")
    Return()
if "// ULTIMATE_V090_HARDWARE_UI_CLEANUP" not in text:
    fail("hardware UI cleanup must run first")

# Expand the original hour/minute editor into a complete local calendar editor.
old_state = '''static uint8_t manualClockField = 0;\nstatic int manualClockHour = 12;\nstatic int manualClockMinute = 0;\nstatic bool manualClockHadValidTime = false;'''
new_state = '''static uint8_t manualClockField = 0; // 0 year, 1 month, 2 day, 3 hour, 4 minute\nstatic int manualClockYear = 2026;\nstatic int manualClockMonth = 1;\nstatic int manualClockDay = 1;\nstatic int manualClockHour = 12;\nstatic int manualClockMinute = 0;\nstatic bool manualClockHadValidTime = false;'''
if old_state not in text:
    fail("manual clock state anchor missing")
text = text.replace(old_state, new_state, 1)

helpers = r'''static bool manualClockReadLocal(struct tm &ti) {
  time_t now = time(nullptr);
  if (now >= 1700000000 && localtime_r(&now, &ti) != nullptr) return true;

  if (pet.lastSeenEpoch >= 1700000000UL) {
    time_t saved = (time_t)pet.lastSeenEpoch;
    if (localtime_r(&saved, &ti) != nullptr) return true;
  }
  return false;
}

static bool manualClockLeapYear(int y) {
  return (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0);
}

static int manualClockDaysInMonth(int y, int m) {
  static const uint8_t days[12] = {31,28,31,30,31,30,31,31,30,31,30,31};
  if (m < 1 || m > 12) return 31;
  if (m == 2 && manualClockLeapYear(y)) return 29;
  return days[m - 1];
}

static void manualClockClampDay() {
  int maxDay = manualClockDaysInMonth(manualClockYear, manualClockMonth);
  if (manualClockDay < 1) manualClockDay = 1;
  if (manualClockDay > maxDay) manualClockDay = maxDay;
}

static void openManualClock() {
  struct tm ti{};
  manualClockHadValidTime = manualClockReadLocal(ti);
  if (manualClockHadValidTime) {
    manualClockYear = ti.tm_year + 1900;
    manualClockMonth = ti.tm_mon + 1;
    manualClockDay = ti.tm_mday;
    manualClockHour = ti.tm_hour;
    manualClockMinute = ti.tm_min;
  } else {
    // Safe visible defaults for a device that has never had valid time. The
    // user can set the complete date/time offline without Wi-Fi.
    manualClockYear = 2026;
    manualClockMonth = 1;
    manualClockDay = 1;
    manualClockHour = 12;
    manualClockMinute = 0;
  }
  manualClockClampDay();
  manualClockField = 0;
  screen = SET_CLOCK;
  dirty = true;
}

static void adjustManualClock(int delta) {
  if (manualClockField == 0) {
    manualClockYear += delta;
    if (manualClockYear < 2020) manualClockYear = 2099;
    if (manualClockYear > 2099) manualClockYear = 2020;
    manualClockClampDay();
  } else if (manualClockField == 1) {
    manualClockMonth += delta;
    if (manualClockMonth < 1) manualClockMonth = 12;
    if (manualClockMonth > 12) manualClockMonth = 1;
    manualClockClampDay();
  } else if (manualClockField == 2) {
    int maxDay = manualClockDaysInMonth(manualClockYear, manualClockMonth);
    manualClockDay += delta;
    if (manualClockDay < 1) manualClockDay = maxDay;
    if (manualClockDay > maxDay) manualClockDay = 1;
  } else if (manualClockField == 3) {
    manualClockHour += delta;
    if (manualClockHour < 0) manualClockHour = 23;
    if (manualClockHour > 23) manualClockHour = 0;
  } else {
    manualClockMinute += delta;
    if (manualClockMinute < 0) manualClockMinute = 59;
    if (manualClockMinute > 59) manualClockMinute = 0;
  }
  dirty = true;
}

static void applyManualClock() {
  setenv("TZ", TAMAPOKE_TZ, 1);
  tzset();

  struct tm ti{};
  ti.tm_year = manualClockYear - 1900;
  ti.tm_mon = manualClockMonth - 1;
  ti.tm_mday = manualClockDay;
  ti.tm_hour = manualClockHour;
  ti.tm_min = manualClockMinute;
  ti.tm_sec = 0;
  ti.tm_isdst = -1;

  time_t chosen = mktime(&ti);
  if (chosen < 1700000000) {
    say("Date/time save failed", 1800);
    dirty = true;
    return;
  }

  struct timeval tv{};
  tv.tv_sec = chosen;
  tv.tv_usec = 0;
  if (settimeofday(&tv, nullptr) != 0) {
    say("Date/time save failed", 1800);
    dirty = true;
    return;
  }

  // Manual correction changes the wall clock only. It deliberately does NOT
  // apply offline progression, so correcting the date cannot suddenly age or
  // penalize the Pokemon.
  pet.setClock((uint32_t)chosen);

  char msg[48];
  snprintf(msg, sizeof(msg), "Clock set %04d-%02d-%02d %02d:%02d",
           manualClockYear, manualClockMonth, manualClockDay,
           manualClockHour, manualClockMinute);
  noteEvent(msg);
  say("Date & time saved", 1500);
  screen = SETTINGS;
  dirty = true;
}'''
text = replace_function(text,
    "static bool manualClockReadLocal(struct tm &ti) {",
    "static bool sceneNight() {",
    helpers,
    "complete manual date/time helpers")

# Settings wording now accurately describes the full editor.
if '    "SET CLOCK",' not in text:
    fail("Settings clock label missing")
text = text.replace('    "SET CLOCK",', '    "SET DATE / TIME",', 1)

new_draw = r'''static void drawSetClock() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("SET DATE & TIME", 120, 3, 1);

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("DATE", 120, 21, 1);

  char yy[6], mo[4], dd[4], hh[4], mm[4];
  snprintf(yy, sizeof(yy), "%04d", manualClockYear);
  snprintf(mo, sizeof(mo), "%02d", manualClockMonth);
  snprintf(dd, sizeof(dd), "%02d", manualClockDay);
  snprintf(hh, sizeof(hh), "%02d", manualClockHour);
  snprintf(mm, sizeof(mm), "%02d", manualClockMinute);

  auto box = [&](int x, int y, int w, const char *value, uint8_t field) {
    bool sel = manualClockField == field;
    ui.fillRoundRect(x, y, w, 25, 6, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(x, y, w, 25, 6, sel ? UI_WARN : UI_TRACK);
    ui.setTextColor(UI_INK);
    ui.setTextSize(2);
    ui.drawCentreString(value, x + w / 2, y + 6, 1);
  };

  box(10, 31, 74, yy, 0);
  box(91, 31, 57, mo, 1);
  box(155, 31, 57, dd, 2);

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("YEAR", 47, 58, 1);
  ui.drawCentreString("MONTH", 119, 58, 1);
  ui.drawCentreString("DAY", 183, 58, 1);
  ui.drawCentreString("TIME", 120, 70, 1);

  box(49, 79, 58, hh, 3);
  box(133, 79, 58, mm, 4);
  ui.setTextSize(2); ui.setTextColor(UI_INK); ui.drawCentreString(":", 120, 85, 1);

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("HOUR", 78, 106, 1);
  ui.drawCentreString("MIN", 162, 106, 1);
  ui.drawCentreString("L/R FIELD   U/D CHANGE", 120, 116, 1);
  ui.setTextColor(UI_INK);
  ui.drawCentreString("ENTER SAVE   ESC CANCEL", 120, 126, 1);
}'''
text = replace_function(text,
    "static void drawSetClock() {",
    "static void drawHelp() {",
    new_draw,
    "complete date/time editor UI")

old_input = r'''  } else if (screen == SET_CLOCK) {
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
new_input = r'''  } else if (screen == SET_CLOCK) {
    if (leftEdge) {
      manualClockField = manualClockField == 0 ? 4 : manualClockField - 1;
      dirty = true;
    }
    if (rightEdge) {
      manualClockField = (manualClockField + 1) % 5;
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
if old_input not in text:
    fail("SET_CLOCK input block missing")
text = text.replace(old_input, new_input, 1)

# Remove the developer-only Wi-Fi instruction from Daily Life. Manual date/time
# is now a first-class offline path; NTP remains optional if credentials are
# compiled in later.
old_daily = '''    ui.drawCentreString("Calendar clock not synced", 120, 34, 1);\n    ui.drawCentreString("Set Wi-Fi in user_config.h for NTP", 120, 50, 1);'''
new_daily = '''    ui.drawCentreString("Date & time not set", 120, 34, 1);\n    ui.drawCentreString("Settings > Set Date / Time", 120, 50, 1);\n    ui.drawCentreString("Wi-Fi sync is optional", 120, 66, 1);'''
if old_daily not in text:
    fail("Daily Life unsynced message missing")
text = text.replace(old_daily, new_daily, 1)

# Marker for CI/audit proof.
text = text.replace("// ULTIMATE_V090_HARDWARE_UI_CLEANUP",
                    "// ULTIMATE_V090_HARDWARE_UI_CLEANUP\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-datetime] Added full offline date/time editor and Daily Life offline calendar support")
