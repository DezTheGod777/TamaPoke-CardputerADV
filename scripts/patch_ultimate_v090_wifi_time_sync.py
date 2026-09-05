Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_WIFI_TIME_SYNC"


def fail(msg):
    print(f"[v0.9.0-wifi-time] ERROR: {msg}")
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
    print("[v0.9.0-wifi-time] Wi-Fi time sync already applied")
    Return()
if "// ULTIMATE_V090_OFFLINE_DATETIME" not in text:
    fail("offline date/time patch must run first")

# Direct NTP query over UDP lets us verify that a fresh network time was
# actually received even if a valid manual clock already exists.
if "#include <WiFiUdp.h>" not in text:
    if "#include <WiFi.h>\n" not in text:
        fail("WiFi include anchor missing")
    text = text.replace("#include <WiFi.h>\n", "#include <WiFi.h>\n#include <WiFiUdp.h>\n", 1)

# Three dedicated screens keep Wi-Fi completely user initiated: network picker,
# password entry, and result. The radio is OFF while browsing these screens.
enum_anchor = "  SET_CLOCK,\n  HELP,"
if enum_anchor not in text:
    fail("SET_CLOCK screen enum anchor missing")
text = text.replace(enum_anchor,
                    "  SET_CLOCK,\n  WIFI_SYNC_PICK,\n  WIFI_SYNC_PASS,\n  WIFI_SYNC_RESULT,\n  HELP,", 1)

# Wi-Fi UI/runtime state. Credentials entered here are handled by the ESP32 Wi-Fi
# stack; TamaPoke never writes them to SD. A successful manual connection can be
# reused later through the ESP32's saved-network slot.
state_anchor = "static bool manualClockHadValidTime = false;"
if state_anchor not in text:
    fail("manual clock state anchor missing")
text = text.replace(
    state_anchor,
    state_anchor + "\n"
    "static String wifiSyncSsids[8];\n"
    "static bool wifiSyncOpen[8] = {false};\n"
    "static uint8_t wifiSyncCount = 0;\n"
    "static uint8_t wifiSyncSel = 0;\n"
    "static String wifiSyncChosenSsid;\n"
    "static char wifiSyncPassword[65] = \"\";\n"
    "static uint8_t wifiSyncPasswordLen = 0;\n"
    "static String wifiSyncResultTitle;\n"
    "static String wifiSyncResultLine;\n"
    "static bool wifiSyncResultOk = false;\n"
    + MARKER,
    1,
)

# Insert all Wi-Fi helpers immediately before Settings rendering. At this point
# the common UI, toast/event helpers, Pet, and clock helpers already exist.
settings_pos = text.find("static void drawSettings() {")
if settings_pos < 0:
    fail("drawSettings anchor missing")

wifi_helpers = r'''
static void wifiTimeRadioOff() {
  WiFi.disconnect(true);
  delay(20);
  WiFi.mode(WIFI_OFF);
}

static void wifiTimeBusy(const char *title, const String &line) {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString(title, 120, 28, 1);
  ui.setTextSize(1);
  ui.drawCentreString(line, 120, 61, 1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Wi-Fi turns off automatically", 120, 91, 1);
  ui.pushSprite(0, 0);
}

static uint32_t wifiTimeFetchNtpHost(const char *host) {
  IPAddress server;
  if (WiFi.hostByName(host, server) != 1) return 0;

  WiFiUDP udp;
  if (!udp.begin(2390)) return 0;

  uint8_t packet[48] = {0};
  packet[0] = 0b11100011; // LI, version 4, client
  packet[1] = 0;
  packet[2] = 6;
  packet[3] = 0xEC;
  packet[12] = 49; packet[13] = 0x4E; packet[14] = 49; packet[15] = 52;

  if (!udp.beginPacket(server, 123)) { udp.stop(); return 0; }
  udp.write(packet, sizeof(packet));
  if (!udp.endPacket()) { udp.stop(); return 0; }

  uint32_t start = millis();
  while (millis() - start < 3000) {
    int len = udp.parsePacket();
    if (len >= 48) {
      uint8_t reply[48];
      int got = udp.read(reply, sizeof(reply));
      udp.stop();
      if (got < 48) return 0;
      uint32_t secs1900 = ((uint32_t)reply[40] << 24) |
                          ((uint32_t)reply[41] << 16) |
                          ((uint32_t)reply[42] << 8) |
                          (uint32_t)reply[43];
      if (secs1900 <= 2208988800UL) return 0;
      uint32_t epoch = secs1900 - 2208988800UL;
      return epoch >= 1700000000UL ? epoch : 0;
    }
    delay(40);
  }
  udp.stop();
  return 0;
}

static uint32_t wifiTimeFetchNtp() {
  static const char *hosts[] = {"pool.ntp.org", "time.google.com", "time.cloudflare.com"};
  for (const char *host : hosts) {
    uint32_t epoch = wifiTimeFetchNtpHost(host);
    if (epoch) return epoch;
  }
  return 0;
}

static void wifiTimeSetResult(bool ok, const String &title, const String &line) {
  wifiSyncResultOk = ok;
  wifiSyncResultTitle = title;
  wifiSyncResultLine = line;
  screen = WIFI_SYNC_RESULT;
  dirty = true;
}

static void wifiTimeApplyEpoch(uint32_t epoch) {
  struct timeval tv{};
  tv.tv_sec = epoch;
  tv.tv_usec = 0;
  setenv("TZ", TAMAPOKE_TZ, 1);
  tzset();
  settimeofday(&tv, nullptr);

  // This is a wall-clock correction initiated by the user, so do not apply a
  // surprise block of offline aging. Future runtime/offline progression uses
  // the newly corrected timestamp normally.
  pet.setClock(epoch);

  struct tm ti{};
  time_t t = (time_t)epoch;
  localtime_r(&t, &ti);
  char stamp[40];
  snprintf(stamp, sizeof(stamp), "%04d-%02d-%02d %02d:%02d",
           ti.tm_year + 1900, ti.tm_mon + 1, ti.tm_mday, ti.tm_hour, ti.tm_min);
  noteEvent(String("Wi-Fi clock sync: ") + stamp);
  wifiTimeSetResult(true, "TIME SYNCED", String(stamp));
}

static void wifiTimeConnectAndSync(const char *ssid, const char *password, bool useSaved) {
  wifiTimeBusy("WI-FI TIME SYNC", useSaved ? "Connecting to saved network..." : String("Connecting to ") + ssid + "...");

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false);
  delay(60);
  if (useSaved) WiFi.begin();
  else WiFi.begin(ssid, password ? password : "");

  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) delay(80);

  if (WiFi.status() != WL_CONNECTED) {
    wifiTimeRadioOff();
    wifiTimeSetResult(false, "CONNECTION FAILED", useSaved ? "No usable saved Wi-Fi" : "Check password / signal");
    return;
  }

  wifiTimeBusy("WI-FI TIME SYNC", "Getting network time...");
  uint32_t epoch = wifiTimeFetchNtp();
  if (!epoch) {
    wifiTimeRadioOff();
    wifiTimeSetResult(false, "TIME SYNC FAILED", "Internet connected, NTP unavailable");
    return;
  }

  // Shut the radio down BEFORE showing success. It stays off until the user
  // explicitly requests another sync, eliminating idle Wi-Fi battery drain.
  wifiTimeRadioOff();
  wifiTimeApplyEpoch(epoch);
}

static void wifiTimeScan() {
  wifiTimeBusy("WI-FI TIME SYNC", "Scanning networks...");
  wifiSyncCount = 0;
  wifiSyncSel = 0;

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false);
  delay(60);
  int n = WiFi.scanNetworks(false, true);
  if (n > 0) {
    for (int i = 0; i < n && wifiSyncCount < 8; ++i) {
      String ssid = WiFi.SSID(i);
      if (!ssid.length()) continue;
      bool duplicate = false;
      for (uint8_t j = 0; j < wifiSyncCount; ++j) {
        if (wifiSyncSsids[j] == ssid) { duplicate = true; break; }
      }
      if (duplicate) continue;
      wifiSyncSsids[wifiSyncCount] = ssid;
      wifiSyncOpen[wifiSyncCount] = WiFi.encryptionType(i) == WIFI_AUTH_OPEN;
      wifiSyncCount++;
    }
  }
  WiFi.scanDelete();
  wifiTimeRadioOff();
  screen = WIFI_SYNC_PICK;
  dirty = true;
}

static void openWifiTimeSync() {
  wifiSyncPasswordLen = 0;
  wifiSyncPassword[0] = 0;
  wifiTimeScan();
}

static void wifiTimeChooseNetwork() {
  // Row 0 always tries credentials previously saved by the ESP32 Wi-Fi stack.
  if (wifiSyncSel == 0) {
    wifiTimeConnectAndSync(nullptr, nullptr, true);
    return;
  }

  if (wifiSyncSel >= 1 && wifiSyncSel <= wifiSyncCount) {
    uint8_t idx = wifiSyncSel - 1;
    wifiSyncChosenSsid = wifiSyncSsids[idx];
    wifiSyncPasswordLen = 0;
    wifiSyncPassword[0] = 0;
    if (wifiSyncOpen[idx]) {
      wifiTimeConnectAndSync(wifiSyncChosenSsid.c_str(), "", false);
    } else {
      screen = WIFI_SYNC_PASS;
      dirty = true;
    }
    return;
  }

  // Final row is always RESCAN.
  wifiTimeScan();
}

static void handleWifiPasswordInput(const bool chars[128], const bool prevChars[128],
                                    bool backEdge, bool enterEdge, bool escEdge,
                                    bool spaceEdge) {
  if (escEdge) {
    wifiSyncPasswordLen = 0;
    wifiSyncPassword[0] = 0;
    screen = WIFI_SYNC_PICK;
    dirty = true;
    return;
  }
  if (backEdge && wifiSyncPasswordLen > 0) {
    wifiSyncPassword[--wifiSyncPasswordLen] = 0;
    dirty = true;
  }
  if (spaceEdge && wifiSyncPasswordLen < 63) {
    wifiSyncPassword[wifiSyncPasswordLen++] = ' ';
    wifiSyncPassword[wifiSyncPasswordLen] = 0;
    dirty = true;
  }
  if (enterEdge) {
    wifiTimeConnectAndSync(wifiSyncChosenSsid.c_str(), wifiSyncPassword, false);
    return;
  }
  for (int i = 33; i < 127; ++i) {
    if (!chars[i] || prevChars[i]) continue;
    if (wifiSyncPasswordLen < 63) {
      wifiSyncPassword[wifiSyncPasswordLen++] = (char)i;
      wifiSyncPassword[wifiSyncPasswordLen] = 0;
      dirty = true;
    }
  }
}

static void drawWifiTimePick() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("WI-FI TIME SYNC", 120, 3, 1);
  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Radio is OFF while choosing", 120, 21, 1);

  int total = 1 + wifiSyncCount + 1; // saved + networks + rescan
  if (wifiSyncSel >= total) wifiSyncSel = total - 1;
  int top = 0;
  if (wifiSyncSel > 2) top = wifiSyncSel - 2;
  if (top > total - 5) top = max(0, total - 5);

  for (int row = 0; row < 5; ++row) {
    int item = top + row;
    if (item >= total) break;
    int y = 34 + row * 17;
    bool sel = item == wifiSyncSel;
    ui.fillRoundRect(12, y, 216, 14, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(12, y, 216, 14, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextColor(UI_INK);

    String label;
    if (item == 0) label = "USE SAVED WI-FI";
    else if (item == total - 1) label = "RESCAN NETWORKS";
    else {
      uint8_t idx = item - 1;
      label = wifiSyncSsids[idx];
      if (label.length() > 25) label = label.substring(0, 22) + "...";
      label += wifiSyncOpen[idx] ? "  OPEN" : "  *";
    }
    ui.drawCentreString(label, 120, y + 4, 1);
  }

  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ENTER SELECT   ESC SETTINGS", 120, 123, 1);
}

static void drawWifiTimePassword() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("WI-FI PASSWORD", 120, 5, 1);
  ui.setTextSize(1);
  String ssid = wifiSyncChosenSsid;
  if (ssid.length() > 30) ssid = ssid.substring(0, 27) + "...";
  ui.drawCentreString(ssid, 120, 28, 1);

  ui.fillRoundRect(13, 48, 214, 28, 6, UI_WHITE);
  ui.drawRoundRect(13, 48, 214, 28, 6, UI_TRACK);
  String mask;
  int visible = min<int>(wifiSyncPasswordLen, 30);
  for (int i = 0; i < visible; ++i) mask += '*';
  if (wifiSyncPasswordLen > 30) mask = "..." + mask.substring(3);
  ui.setTextSize(1);
  ui.setTextColor(UI_INK);
  ui.drawCentreString(mask.length() ? mask : "TYPE PASSWORD", 120, 59, 1);

  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Password is hidden", 120, 86, 1);
  ui.drawCentreString("ENTER CONNECT   ESC BACK", 120, 108, 1);
  ui.drawCentreString("Wi-Fi shuts off after sync", 120, 122, 1);
}

static void drawWifiTimeResult() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(wifiSyncResultOk ? UI_OK : UI_BAD);
  ui.setTextSize(2);
  ui.drawCentreString(wifiSyncResultTitle, 120, 25, 1);
  ui.setTextSize(1);
  ui.setTextColor(UI_INK);
  ui.drawCentreString(wifiSyncResultLine, 120, 58, 1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Wi-Fi disconnected - radio OFF", 120, 83, 1);
  ui.drawCentreString("ENTER / ESC = SETTINGS", 120, 121, 1);
}
'''

text = text[:settings_pos] + wifi_helpers + "\n" + text[settings_pos:]

# Replace Settings menu: add the explicit one-shot Wi-Fi sync directly after the
# manual Date/Time editor. Existing rows retain their behavior, shifted by one.
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

  const char *items[12] = {
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
  };

  int top = 0;
  if (settingsSel > 2) top = settingsSel - 2;
  if (top > 6) top = 6;

  for (int row = 0; row < 6; ++row) {
    int i = top + row;
    int y = 24 + row * 16;
    bool sel = i == settingsSel;
    ui.fillRoundRect(34, y, 172, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(34, y, 172, 13, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextSize(1);
    ui.setTextColor(i == 10 ? UI_BAD : UI_INK);
    ui.drawCentreString(items[i], 120, y + 4, 1);
  }

  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  if (top > 0) ui.drawString("^", 214, 25);
  if (top < 6) ui.drawString("v", 214, 105);
  ui.drawCentreString("LEFT/RIGHT ADJUST  ENTER SELECT", 120, 123, 1);
}'''
text = replace_function(text, "static void drawSettings() {", "static void drawSetClock() {",
                        new_settings, "Settings with Wi-Fi sync")

# Settings navigation with the new row.
settings_start = text.find("  } else if (screen == SETTINGS) {")
settings_end = text.find("  } else if (screen == SET_CLOCK) {", settings_start)
if settings_start < 0 or settings_end < 0:
    fail("Settings input block anchors missing")
new_settings_input = r'''  } else if (screen == SETTINGS) {
    if (upEdge) {
      settingsSel = settingsSel == 0 ? 11 : settingsSel - 1;
      dirty = true;
    }
    if (downEdge) {
      settingsSel = (settingsSel + 1) % 12;
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
        dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;
        screen = DEX_GRID;
        dexGridDirty = true;
        dirty = true;
      } else if (settingsSel == 6) {
        screen = HELP;
        dirty = true;
      } else if (settingsSel == 7) {
        screen = EVENTS;
        dirty = true;
      } else if (settingsSel == 8) {
        screen = ABOUT;
        dirty = true;
      } else if (settingsSel == 9) {
        resetDisplaySettings();
      } else if (settingsSel == 10) {
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
'''
text = text[:settings_start] + new_settings_input + text[settings_end:]

# Picker and result use normal navigation. Password typing is intercepted before
# ordinary printable shortcuts so no password character can trigger a game key.
set_clock_anchor = "  } else if (screen == SET_CLOCK) {"
if set_clock_anchor not in text:
    fail("SET_CLOCK input anchor missing")
wifi_nav = r'''  } else if (screen == WIFI_SYNC_PICK) {
    int total = 1 + wifiSyncCount + 1;
    if (upEdge) {
      wifiSyncSel = wifiSyncSel == 0 ? total - 1 : wifiSyncSel - 1;
      dirty = true;
    }
    if (downEdge) {
      wifiSyncSel = (wifiSyncSel + 1) % total;
      dirty = true;
    }
    if (enterEdge || spaceEdge) wifiTimeChooseNetwork();
    if (escEdge || backEdge) {
      wifiTimeRadioOff();
      screen = SETTINGS;
      dirty = true;
    }
  } else if (screen == WIFI_SYNC_RESULT) {
    if (escEdge || backEdge || enterEdge || spaceEdge) {
      wifiTimeRadioOff();
      screen = SETTINGS;
      dirty = true;
    }
'''
text = text.replace(set_clock_anchor, wifi_nav + set_clock_anchor, 1)

special_anchor = "  if (screen == RENAME) {\n    handleRenameInput(chars, prevChars, backEdge, enterEdge, escEdge);"
if special_anchor not in text:
    fail("rename keyboard special-case anchor missing")
text = text.replace(
    special_anchor,
    "  if (screen == WIFI_SYNC_PASS) {\n"
    "    handleWifiPasswordInput(chars, prevChars, backEdge, enterEdge, escEdge, spaceEdge);\n"
    "    goto save_input_state;\n"
    "  }\n\n"
    + special_anchor,
    1,
)

# Render all three Wi-Fi screens.
render_anchor = "      case SET_CLOCK:  drawSetClock(); break;\n"
if render_anchor not in text:
    fail("SET_CLOCK render anchor missing")
text = text.replace(
    render_anchor,
    render_anchor +
    "      case WIFI_SYNC_PICK: drawWifiTimePick(); break;\n"
    "      case WIFI_SYNC_PASS: drawWifiTimePassword(); break;\n"
    "      case WIFI_SYNC_RESULT: drawWifiTimeResult(); break;\n",
    1,
)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-wifi-time] Added on-demand scan/password/saved-network NTP sync with automatic radio shutdown")
