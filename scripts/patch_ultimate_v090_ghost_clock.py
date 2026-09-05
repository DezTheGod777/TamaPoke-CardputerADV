Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_GHOST_CLOCK"


def fail(msg):
    print(f"[v0.9.0-ghost-clock] ERROR: {msg}")
    env.Exit(1)


def replace_function(text, start_sig, next_sig, body, label):
    start = text.find(start_sig)
    if start < 0:
        fail(f"could not locate {label} start")
    end = text.find(next_sig, start)
    if end < 0:
        fail(f"could not locate {label} end")
    return text[:start] + body.rstrip() + "\n\n" + text[end:]


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ghost-clock] Ghost Clock already applied")
    Return()
if "// ULTIMATE_V090_DAILY_TOGETHER_FIX" not in text:
    fail("Daily Together fix must run first")

# Dedicated live clock/calendar screen. It reads the exact same local system
# clock used by Daily Life, streaks, Bond-day rollover and the Home day/night
# scene. No Wi-Fi is started here.
enum_anchor = "  WIFI_SYNC_RESULT,\n  HELP,"
if enum_anchor not in text:
    fail("Wi-Fi result screen enum anchor missing")
text = text.replace(enum_anchor,
                    "  WIFI_SYNC_RESULT,\n  CLOCK_CALENDAR,\n  HELP,", 1)

# Screen drawing helpers are inserted directly before Settings.
settings_pos = text.find("static void drawSettings() {")
if settings_pos < 0:
    fail("drawSettings anchor missing")

clock_helpers = r'''
// ULTIMATE_V090_GHOST_CLOCK
static void drawGhostClockGastly(int cx, int cy, uint32_t now) {
  const uint16_t aura1 = C565(0x72,0x45,0xa8);
  const uint16_t aura2 = C565(0x9a,0x67,0xc9);
  const uint16_t body  = C565(0x68,0x3b,0x91);
  const uint16_t dark  = C565(0x24,0x15,0x38);
  const uint16_t eye   = C565(0xff,0xf2,0xe4);
  int bob = ((now / 430UL) & 1UL) ? 1 : -1;
  cy += bob;

  // Soft gaseous aura made from small orbiting puffs.
  for (int i = 0; i < 8; ++i) {
    float a = (float)(i * 45 + (now / 35UL) % 360UL) * 0.0174532925f;
    int x = cx + (int)(cosf(a) * 13.0f);
    int y = cy + (int)(sinf(a) * 10.0f);
    ui.fillCircle(x, y, (i & 1) ? 3 : 2, (i & 1) ? aura1 : aura2);
  }
  ui.fillCircle(cx, cy, 9, body);
  ui.fillTriangle(cx - 7, cy - 3, cx - 2, cy - 1, cx - 6, cy + 1, eye);
  ui.fillTriangle(cx + 7, cy - 3, cx + 2, cy - 1, cx + 6, cy + 1, eye);
  ui.fillCircle(cx - 4, cy - 1, 1, dark);
  ui.fillCircle(cx + 4, cy - 1, 1, dark);
  ui.drawFastHLine(cx - 4, cy + 4, 9, dark);
  ui.drawPixel(cx - 4, cy + 3, dark);
  ui.drawPixel(cx + 4, cy + 3, dark);
}

static void drawGhostClockHaunter(int cx, int cy, uint32_t now) {
  const uint16_t body = C565(0x71,0x43,0xa2);
  const uint16_t hi   = C565(0xa7,0x78,0xd0);
  const uint16_t dark = C565(0x22,0x13,0x34);
  const uint16_t eye  = C565(0xff,0xf3,0xe7);
  int bob = ((now / 520UL) & 1UL) ? 1 : -1;
  cy += bob;

  ui.fillCircle(cx, cy, 9, body);
  ui.fillTriangle(cx - 9, cy - 4, cx - 4, cy - 14, cx - 2, cy - 6, body);
  ui.fillTriangle(cx + 9, cy - 4, cx + 4, cy - 14, cx + 2, cy - 6, body);
  ui.fillTriangle(cx - 7, cy + 5, cx - 2, cy + 12, cx, cy + 6, body);
  ui.fillTriangle(cx + 7, cy + 5, cx + 2, cy + 12, cx, cy + 6, body);
  ui.fillTriangle(cx - 7, cy - 3, cx - 2, cy - 1, cx - 6, cy + 1, eye);
  ui.fillTriangle(cx + 7, cy - 3, cx + 2, cy - 1, cx + 6, cy + 1, eye);
  ui.fillCircle(cx - 4, cy - 1, 1, dark);
  ui.fillCircle(cx + 4, cy - 1, 1, dark);
  ui.drawFastHLine(cx - 4, cy + 4, 9, dark);

  // Detached little hands float beside Haunter.
  int hand = ((now / 300UL) % 3UL) - 1;
  ui.fillCircle(cx - 15, cy + hand, 3, hi);
  ui.drawLine(cx - 17, cy - 1 + hand, cx - 20, cy - 4 + hand, hi);
  ui.drawLine(cx - 15, cy - 2 + hand, cx - 16, cy - 6 + hand, hi);
  ui.fillCircle(cx + 15, cy - hand, 3, hi);
  ui.drawLine(cx + 17, cy - 1 - hand, cx + 20, cy - 4 - hand, hi);
  ui.drawLine(cx + 15, cy - 2 - hand, cx + 16, cy - 6 - hand, hi);
}

static void drawGhostClockGengar(int cx, int cy, uint32_t now) {
  const uint16_t body = C565(0x63,0x3a,0x8d);
  const uint16_t dark = C565(0x21,0x13,0x32);
  const uint16_t eye  = C565(0xff,0xf0,0xe2);
  const uint16_t grin = C565(0xff,0xf7,0xee);
  int bob = ((now / 650UL) & 1UL) ? 1 : 0;
  cy += bob;

  ui.fillRoundRect(cx - 13, cy - 9, 27, 18, 8, body);
  ui.fillTriangle(cx - 12, cy - 7, cx - 8, cy - 17, cx - 3, cy - 8, body);
  ui.fillTriangle(cx + 12, cy - 7, cx + 8, cy - 17, cx + 3, cy - 8, body);
  ui.fillCircle(cx - 11, cy + 8, 5, body);
  ui.fillCircle(cx + 11, cy + 8, 5, body);

  bool blink = ((now / 190UL) % 22UL) == 0;
  if (blink) {
    ui.drawFastHLine(cx - 9, cy - 3, 7, dark);
    ui.drawFastHLine(cx + 3, cy - 3, 7, dark);
  } else {
    ui.fillTriangle(cx - 10, cy - 5, cx - 2, cy - 3, cx - 8, cy, eye);
    ui.fillTriangle(cx + 10, cy - 5, cx + 2, cy - 3, cx + 8, cy, eye);
    ui.fillCircle(cx - 6, cy - 3, 1, dark);
    ui.fillCircle(cx + 6, cy - 3, 1, dark);
  }

  ui.fillRoundRect(cx - 8, cy + 2, 17, 5, 2, grin);
  ui.drawFastHLine(cx - 7, cy + 2, 15, dark);
  ui.drawLine(cx - 4, cy + 3, cx - 4, cy + 6, dark);
  ui.drawLine(cx, cy + 3, cx, cy + 6, dark);
  ui.drawLine(cx + 4, cy + 3, cx + 4, cy + 6, dark);
}

static void drawGhostClock(uint32_t now) {
  const uint16_t bg = C565(0x12,0x0b,0x26);
  const uint16_t bg2 = C565(0x28,0x14,0x42);
  const uint16_t lavender = C565(0xd7,0xbd,0xf2);
  const uint16_t purple = C565(0x8e,0x64,0xb9);
  const uint16_t cream = C565(0xff,0xf5,0xe8);
  const uint16_t muted = C565(0xb7,0xa6,0xc7);

  // Tiny vertical gradient and twinkling stars keep the clock alive without
  // becoming busy or affecting the normal Home ambience.
  for (int y = 0; y < 135; y += 5)
    ui.fillRect(0, y, 240, 5, lerp565(bg, bg2, y, 135));
  for (int i = 0; i < 15; ++i) {
    int x = (i * 47 + 9) % 238;
    int y = 7 + (i * 29) % 120;
    uint16_t c = (((now / 420UL) + i) & 1UL) ? muted : lavender;
    ui.fillRect(x, y, (i % 5 == 0) ? 2 : 1, (i % 5 == 0) ? 2 : 1, c);
  }

  ui.setTextSize(1);
  ui.setTextColor(lavender);
  ui.drawCentreString("GHOST CLOCK", 120, 3, 1);

  drawGhostClockGastly(22, 29, now);
  drawGhostClockHaunter(217, 29, now);

  struct tm ti{};
  bool valid = getLocalTime(&ti, 2) && (ti.tm_year + 1900) >= 2020;
  if (!valid) {
    ui.fillRoundRect(38, 38, 164, 54, 9, C565(0xf4,0xe9,0xf8));
    ui.drawRoundRect(38, 38, 164, 54, 9, purple);
    ui.setTextColor(C565(0x35,0x21,0x48));
    ui.setTextSize(2);
    ui.drawCentreString("TIME NOT SET", 120, 50, 1);
    ui.setTextSize(1);
    ui.drawCentreString("Settings > Set Date / Time", 120, 75, 1);
  } else {
    static const char *WEEKDAY[7] = {
      "SUNDAY","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY"
    };
    static const char *MONTH[12] = {
      "JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE",
      "JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"
    };

    int hour12 = ti.tm_hour % 12;
    if (hour12 == 0) hour12 = 12;
    const char *ampm = ti.tm_hour >= 12 ? "PM" : "AM";

    char timeLine[24];
    char dateLine[34];
    snprintf(timeLine, sizeof(timeLine), "%d:%02d:%02d %s",
             hour12, ti.tm_min, ti.tm_sec, ampm);
    snprintf(dateLine, sizeof(dateLine), "%s %d, %d",
             MONTH[ti.tm_mon], ti.tm_mday, ti.tm_year + 1900);

    ui.fillRoundRect(42, 27, 156, 44, 9, C565(0xf6,0xec,0xfa));
    ui.drawRoundRect(42, 27, 156, 44, 9, purple);
    ui.drawRoundRect(44, 29, 152, 40, 8, C565(0xc7,0xa8,0xdf));

    ui.setTextColor(C565(0x2c,0x18,0x42));
    ui.setTextSize(2);
    ui.drawCentreString(timeLine, 120, 42, 1);

    // Small pulse beside the clock makes the once-per-second movement obvious.
    uint16_t pulse = (ti.tm_sec & 1) ? C565(0xe8,0x78,0xb7) : C565(0xa8,0x72,0xd2);
    ui.fillCircle(187, 35, 2, pulse);

    ui.setTextColor(cream);
    ui.setTextSize(1);
    ui.drawCentreString(WEEKDAY[ti.tm_wday], 120, 77, 1);
    ui.setTextColor(lavender);
    ui.drawCentreString(dateLine, 120, 90, 1);
  }

  drawGhostClockGengar(120, 114, now);

  ui.setTextSize(1);
  ui.setTextColor(muted);
  ui.drawString("ESC HOME", 4, 124, 1);
  ui.drawRightString("T CLOCK", 236, 124, 1);
}
'''

text = text[:settings_pos] + clock_helpers.rstrip() + "\n\n" + text[settings_pos:]

# Add Clock / Calendar to Settings immediately below Wi-Fi Time Sync.
old_items = '''  const char *items[12] = {
    audioEnabled() ? "SOUND: ON" : "SOUND: OFF",
    brightnessLabel,
    timeoutLabel,
    "SET DATE / TIME",
    "WI-FI TIME SYNC",
    "POKEDEX",
    "CONTROLS",
    "RECENT EVENTS",
    "ABOUT / VERSION",
    "RESET DISPLAY",
    "RELEASE POKEMON",
    "BACK"
  };'''
new_items = '''  const char *items[13] = {
    audioEnabled() ? "SOUND: ON" : "SOUND: OFF",
    brightnessLabel,
    timeoutLabel,
    "SET DATE / TIME",
    "WI-FI TIME SYNC",
    "CLOCK / CALENDAR",
    "POKEDEX",
    "CONTROLS",
    "RECENT EVENTS",
    "ABOUT / VERSION",
    "RESET DISPLAY",
    "RELEASE POKEMON",
    "BACK"
  };'''
text = rep(text, old_items, new_items, "Settings item list")
text = rep(text, "  if (top > 6) top = 6;", "  if (top > 7) top = 7;", "Settings scroll range")
text = rep(text, "    ui.setTextColor(i == 10 ? UI_BAD : UI_INK);",
                 "    ui.setTextColor(i == 11 ? UI_BAD : UI_INK);",
                 "Settings release row color")

# Render and animate the live clock at the normal non-game 10 fps cadence.
render_anchor = "      case WIFI_SYNC_RESULT: drawWifiTimeResult(); break;"
if render_anchor not in text:
    fail("Wi-Fi render anchor missing")
text = text.replace(render_anchor,
                    render_anchor + "\n      case CLOCK_CALENDAR: drawGhostClock(now); break;", 1)
text = rep(text, "  if (screen == HOME) return true;",
                 "  if (screen == HOME || screen == CLOCK_CALENDAR) return true;",
                 "animated screen list")

# Settings navigation now has 13 rows. Clock is index 5; subsequent rows shift.
settings_start = text.find("  } else if (screen == SETTINGS) {")
settings_end = text.find("  } else if (screen == SET_CLOCK) {", settings_start)
if settings_start < 0 or settings_end < 0:
    fail("Settings input block anchors missing")
new_settings_input = r'''  } else if (screen == SETTINGS) {
    if (upEdge) {
      settingsSel = settingsSel == 0 ? 12 : settingsSel - 1;
      dirty = true;
    }
    if (downEdge) {
      settingsSel = (settingsSel + 1) % 13;
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
        openWifiTimeSync();
      } else if (settingsSel == 5) {
        screen = CLOCK_CALENDAR;
        dirty = true;
        sfxPlay(SFX_TAP);
      } else if (settingsSel == 6) {
        dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;
        screen = DEX_GRID;
        dexGridDirty = true;
        dirty = true;
      } else if (settingsSel == 7) {
        screen = HELP;
        dirty = true;
      } else if (settingsSel == 8) {
        screen = EVENTS;
        dirty = true;
      } else if (settingsSel == 9) {
        screen = ABOUT;
        dirty = true;
      } else if (settingsSel == 10) {
        resetDisplaySettings();
      } else if (settingsSel == 11) {
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
  } else if (screen == CLOCK_CALENDAR) {
    if (escEdge || backEdge || enterEdge || spaceEdge) {
      screen = HOME;
      dirty = true;
    }
'''
text = text[:settings_start] + new_settings_input.rstrip() + "\n" + text[settings_end:]

# T is free as a normal Home shortcut, but the existing hidden word "ultimate"
# contains two T characters. Feed the secret buffer first, then suppress Clock
# only when that T is currently forming the valid secret prefixes "ult" or
# "ultimat". This preserves all Phase-12 secret content exactly.
secret_call = "      ultimateSecretPrintable(c);"
if secret_call not in text:
    fail("secret printable Home call missing")
text = text.replace(secret_call,
    secret_call + "\n"
    "      if (c == 't' && !ultimateSecretWordEnds(\"ult\") && !ultimateSecretWordEnds(\"ultimat\")) {\n"
    "        screen = CLOCK_CALENDAR; dirty = true; sfxPlay(SFX_TAP); continue;\n"
    "      }",
    1)

# Mention the shortcut on Controls when the expected Hub line is still present.
text = text.replace('    "H: Ultimate Hub   M: games",',
                    '    "H: Hub   T: Clock   M: games",', 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ghost-clock] Added live 12-hour Ghost Clock/Calendar with T shortcut and Settings entry")
