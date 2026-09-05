Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_GHOST_CLOCK"


def fail(msg):
    print(f"[v0.9.0-ghost-clock] ERROR: {msg}")
    env.Exit(1)


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

# Dedicated screen: same local wall clock used by Daily Life/streaks/sky.
# Merely opening this screen never starts Wi-Fi.
text = rep(text,
    "  WIFI_SYNC_RESULT,\n  HELP,",
    "  WIFI_SYNC_RESULT,\n  CLOCK_CALENDAR,\n  HELP,",
    "clock screen enum")

settings_pos = text.find("static void drawSettings() {")
if settings_pos < 0:
    fail("drawSettings anchor missing")

helpers = r'''
// ULTIMATE_V090_GHOST_CLOCK
static void ghostClockGastly(int cx, int cy, uint32_t now) {
  uint16_t body = C565(0x69,0x3e,0x94), aura = C565(0x9a,0x69,0xc5);
  uint16_t eye = C565(0xff,0xf4,0xe9), ink = C565(0x20,0x12,0x32);
  cy += ((now / 430UL) & 1UL) ? 1 : -1;
  for (int i = 0; i < 8; ++i) {
    float a = (float)(i * 45 + (now / 40UL) % 360UL) * 0.0174532925f;
    ui.fillCircle(cx + (int)(cosf(a) * 13.0f), cy + (int)(sinf(a) * 10.0f), 2, aura);
  }
  ui.fillCircle(cx, cy, 9, body);
  ui.fillTriangle(cx - 7, cy - 3, cx - 2, cy - 1, cx - 6, cy + 1, eye);
  ui.fillTriangle(cx + 7, cy - 3, cx + 2, cy - 1, cx + 6, cy + 1, eye);
  ui.fillCircle(cx - 4, cy - 1, 1, ink); ui.fillCircle(cx + 4, cy - 1, 1, ink);
  ui.drawFastHLine(cx - 4, cy + 4, 9, ink);
}

static void ghostClockHaunter(int cx, int cy, uint32_t now) {
  uint16_t body = C565(0x73,0x45,0xa4), hi = C565(0xaa,0x7c,0xd1);
  uint16_t eye = C565(0xff,0xf4,0xe9), ink = C565(0x20,0x12,0x32);
  cy += ((now / 520UL) & 1UL) ? 1 : -1;
  ui.fillCircle(cx, cy, 9, body);
  ui.fillTriangle(cx - 9, cy - 4, cx - 4, cy - 14, cx - 2, cy - 6, body);
  ui.fillTriangle(cx + 9, cy - 4, cx + 4, cy - 14, cx + 2, cy - 6, body);
  ui.fillTriangle(cx - 7, cy + 5, cx - 2, cy + 12, cx, cy + 6, body);
  ui.fillTriangle(cx + 7, cy + 5, cx + 2, cy + 12, cx, cy + 6, body);
  ui.fillTriangle(cx - 7, cy - 3, cx - 2, cy - 1, cx - 6, cy + 1, eye);
  ui.fillTriangle(cx + 7, cy - 3, cx + 2, cy - 1, cx + 6, cy + 1, eye);
  ui.fillCircle(cx - 4, cy - 1, 1, ink); ui.fillCircle(cx + 4, cy - 1, 1, ink);
  int hand = (int)((now / 300UL) % 3UL) - 1;
  ui.fillCircle(cx - 16, cy + hand, 3, hi); ui.fillCircle(cx + 16, cy - hand, 3, hi);
  ui.drawLine(cx - 18, cy - 1 + hand, cx - 21, cy - 4 + hand, hi);
  ui.drawLine(cx + 18, cy - 1 - hand, cx + 21, cy - 4 - hand, hi);
}

static void ghostClockGengar(int cx, int cy, uint32_t now) {
  uint16_t body = C565(0x62,0x39,0x8b), eye = C565(0xff,0xf2,0xe8);
  uint16_t grin = C565(0xff,0xf8,0xef), ink = C565(0x20,0x12,0x32);
  cy += ((now / 650UL) & 1UL) ? 1 : 0;
  ui.fillRoundRect(cx - 13, cy - 9, 27, 18, 8, body);
  ui.fillTriangle(cx - 12, cy - 7, cx - 8, cy - 17, cx - 3, cy - 8, body);
  ui.fillTriangle(cx + 12, cy - 7, cx + 8, cy - 17, cx + 3, cy - 8, body);
  ui.fillCircle(cx - 11, cy + 8, 5, body); ui.fillCircle(cx + 11, cy + 8, 5, body);
  bool blink = ((now / 190UL) % 22UL) == 0;
  if (blink) {
    ui.drawFastHLine(cx - 9, cy - 3, 7, ink); ui.drawFastHLine(cx + 3, cy - 3, 7, ink);
  } else {
    ui.fillTriangle(cx - 10, cy - 5, cx - 2, cy - 3, cx - 8, cy, eye);
    ui.fillTriangle(cx + 10, cy - 5, cx + 2, cy - 3, cx + 8, cy, eye);
    ui.fillCircle(cx - 6, cy - 3, 1, ink); ui.fillCircle(cx + 6, cy - 3, 1, ink);
  }
  ui.fillRoundRect(cx - 8, cy + 2, 17, 5, 2, grin);
  ui.drawFastHLine(cx - 7, cy + 2, 15, ink);
  ui.drawLine(cx - 4, cy + 3, cx - 4, cy + 6, ink);
  ui.drawLine(cx, cy + 3, cx, cy + 6, ink);
  ui.drawLine(cx + 4, cy + 3, cx + 4, cy + 6, ink);
}

static void drawGhostClock(uint32_t now) {
  const uint16_t bg = C565(0x12,0x0b,0x26), bg2 = C565(0x2a,0x16,0x44);
  const uint16_t lav = C565(0xd8,0xbf,0xf2), purple = C565(0x8f,0x65,0xba);
  const uint16_t cream = C565(0xff,0xf5,0xe8), muted = C565(0xb8,0xa6,0xc8);

  for (int y = 0; y < 135; y += 5) ui.fillRect(0, y, 240, 5, lerp565(bg, bg2, y, 135));
  for (int i = 0; i < 15; ++i) {
    int x = (i * 47 + 9) % 238, y = 7 + (i * 29) % 120;
    uint16_t c = (((now / 420UL) + i) & 1UL) ? muted : lav;
    ui.fillRect(x, y, (i % 5 == 0) ? 2 : 1, (i % 5 == 0) ? 2 : 1, c);
  }

  ui.setTextSize(1); ui.setTextColor(lav); ui.drawCentreString("GHOST CLOCK", 120, 3, 1);
  ghostClockGastly(22, 29, now); ghostClockHaunter(217, 29, now);

  struct tm ti{};
  bool valid = getLocalTime(&ti, 2) && (ti.tm_year + 1900) >= 2020;
  if (!valid) {
    ui.fillRoundRect(38, 38, 164, 54, 9, C565(0xf4,0xe9,0xf8));
    ui.drawRoundRect(38, 38, 164, 54, 9, purple);
    ui.setTextColor(C565(0x35,0x21,0x48)); ui.setTextSize(2);
    ui.drawCentreString("TIME NOT SET", 120, 50, 1);
    ui.setTextSize(1); ui.drawCentreString("Settings > Set Date / Time", 120, 75, 1);
  } else {
    static const char *WD[7] = {"SUNDAY","MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY","SATURDAY"};
    static const char *MO[12] = {"JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE","JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER"};
    int h = ti.tm_hour % 12; if (!h) h = 12;
    char clockLine[24], dateLine[34];
    snprintf(clockLine, sizeof(clockLine), "%d:%02d:%02d %s", h, ti.tm_min, ti.tm_sec, ti.tm_hour >= 12 ? "PM" : "AM");
    snprintf(dateLine, sizeof(dateLine), "%s %d, %d", MO[ti.tm_mon], ti.tm_mday, ti.tm_year + 1900);

    ui.fillRoundRect(42, 27, 156, 44, 9, C565(0xf6,0xec,0xfa));
    ui.drawRoundRect(42, 27, 156, 44, 9, purple);
    ui.drawRoundRect(44, 29, 152, 40, 8, C565(0xc7,0xa8,0xdf));
    ui.setTextColor(C565(0x2c,0x18,0x42)); ui.setTextSize(2);
    ui.drawCentreString(clockLine, 120, 42, 1);
    ui.fillCircle(187, 35, 2, (ti.tm_sec & 1) ? C565(0xe8,0x78,0xb7) : C565(0xa8,0x72,0xd2));
    ui.setTextSize(1); ui.setTextColor(cream); ui.drawCentreString(WD[ti.tm_wday], 120, 77, 1);
    ui.setTextColor(lav); ui.drawCentreString(dateLine, 120, 90, 1);
  }

  ghostClockGengar(120, 114, now);
  ui.setTextSize(1); ui.setTextColor(muted);
  ui.drawString("ESC HOME", 4, 124, 1); ui.drawString("T CLOCK", 194, 124, 1);
}
'''
text = text[:settings_pos] + helpers.rstrip() + "\n\n" + text[settings_pos:]

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
text = rep(text, "    ui.setTextColor(i == 10 ? UI_BAD : UI_INK);", "    ui.setTextColor(i == 11 ? UI_BAD : UI_INK);", "Settings release row")

render_anchor = "      case WIFI_SYNC_RESULT: drawWifiTimeResult(); break;"
text = rep(text, render_anchor, render_anchor + "\n      case CLOCK_CALENDAR: drawGhostClock(now); break;", "clock render")
text = rep(text, "  if (screen == HOME) return true;", "  if (screen == HOME || screen == CLOCK_CALENDAR) return true;", "clock animation")

settings_start = text.find("  } else if (screen == SETTINGS) {")
settings_end = text.find("  } else if (screen == SET_CLOCK) {", settings_start)
if settings_start < 0 or settings_end < 0:
    fail("Settings input block anchors missing")
new_settings = r'''  } else if (screen == SETTINGS) {
    if (upEdge) { settingsSel = settingsSel == 0 ? 12 : settingsSel - 1; dirty = true; }
    if (downEdge) { settingsSel = (settingsSel + 1) % 13; dirty = true; }
    if (leftEdge || rightEdge) {
      int delta = rightEdge ? 1 : -1;
      if (settingsSel == 1) adjustBrightness(delta);
      else if (settingsSel == 2) adjustDisplayTimeout(delta);
    }
    if (enterEdge || spaceEdge) {
      if (settingsSel == 0) { audioSetEnabled(!audioEnabled()); if (audioEnabled()) sfxPlay(SFX_TAP); dirty = true; }
      else if (settingsSel == 1) adjustBrightness(1);
      else if (settingsSel == 2) adjustDisplayTimeout(1);
      else if (settingsSel == 3) openManualClock();
      else if (settingsSel == 4) openWifiTimeSync();
      else if (settingsSel == 5) { screen = CLOCK_CALENDAR; dirty = true; sfxPlay(SFX_TAP); }
      else if (settingsSel == 6) { dexCursor = pet.speciesId > 0 ? pet.speciesId : 1; screen = DEX_GRID; dexGridDirty = true; dirty = true; }
      else if (settingsSel == 7) { screen = HELP; dirty = true; }
      else if (settingsSel == 8) { screen = EVENTS; dirty = true; }
      else if (settingsSel == 9) { screen = ABOUT; dirty = true; }
      else if (settingsSel == 10) resetDisplaySettings();
      else if (settingsSel == 11) { if (!pet.isEgg()) openDialog(DLG_RELEASE); }
      else { screen = HOME; dirty = true; }
    }
    if (escEdge || backEdge) { screen = HOME; dirty = true; }
  } else if (screen == CLOCK_CALENDAR) {
    if (escEdge || backEdge || enterEdge || spaceEdge) { screen = HOME; dirty = true; }
'''
text = text[:settings_start] + new_settings.rstrip() + "\n" + text[settings_end:]

# T is unused as a normal Home shortcut. Preserve the hidden word "ultimate":
# immediately before its two T characters, the existing secret buffer ends in
# "ul" and "ultima" respectively, so those two keypresses remain secret input.
edge_anchor = "  bool escEdge = escNow && !prevEsc;"
if edge_anchor not in text:
    fail("keyboard edge anchor missing")
shortcut = r'''
  bool tClockEdge = chars[(uint8_t)'t'] && !prevChars[(uint8_t)'t'];
  if (screen == HOME && !feedOpen && tClockEdge &&
      !ultimateSecretWordEnds("ul") && !ultimateSecretWordEnds("ultima")) {
    screen = CLOCK_CALENDAR;
    dirty = true;
    sfxPlay(SFX_TAP);
  }'''
text = text.replace(edge_anchor, edge_anchor + shortcut, 1)

text = text.replace('    "H: Ultimate Hub   M: games",', '    "H: Hub   T: Clock   M: games",', 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ghost-clock] Added live 12-hour Ghost Clock/Calendar with T shortcut and Settings entry")
