Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
PET_CPP = PROJECT / "generated" / "pet.cpp"
MARKER = "// ULTIMATE_V090_THIRD_AUDIT"


def fail(msg):
    print(f"[v0.9.0-audit3] ERROR: {msg}")
    env.Exit(1)


def replace_function(text, start_sig, next_sig, body, label):
    start = text.find(start_sig)
    if start < 0:
        fail(f"could not locate {label} start")
    end = text.find(next_sig, start)
    if end < 0:
        fail(f"could not locate {label} end")
    return text[:start] + body.rstrip() + "\n\n" + text[end:]


# ---------------------------------------------------------------------------
# Final generated main.cpp audit.
# ---------------------------------------------------------------------------
text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-audit3] third audit already applied")
    Return()
if "// ULTIMATE_V090_WIFI_TIME_SYNC" not in text:
    fail("Wi-Fi time-sync patch must run first")

# 1) Restore a valid system wall clock on boot even when TamaPoke itself does
# not perform an NTP sync during this boot. The saved Pet timestamp already
# follows the live clock while running, so restoring it keeps Daily Life,
# local-day bond/streak logic and the sky calendar usable after a power cycle.
# If M5 Launcher (or another app) has left a newer valid system clock, prefer it
# and apply genuine offline progression through Pet::syncClock().
clock_start = text.find("  uint32_t epoch = getNtpEpoch();")
clock_end = text.find("  dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;", clock_start)
if clock_start < 0 or clock_end < 0:
    fail("setup clock block")
clock_block = r'''  uint32_t epoch = getNtpEpoch();
  if (epoch) {
    pet.syncClock(epoch);
    Serial.printf("Clock synced by configured NTP: %lu\n", (unsigned long)epoch);
  } else {
    time_t bootNow = time(nullptr);
    const uint32_t saved = pet.lastSeenEpoch;

    if (bootNow >= 1700000000) {
      uint32_t live = (uint32_t)bootNow;
      // Never move the wall clock significantly backward just because an
      // inherited system clock is stale. The save journal is the safer floor.
      if (saved >= 1700000000UL && live + 300UL < saved) {
        struct timeval tv{};
        tv.tv_sec = saved;
        tv.tv_usec = 0;
        settimeofday(&tv, nullptr);
        pet.setClock(saved);
        Serial.printf("Clock restored from TamaPoke save: %lu\n", (unsigned long)saved);
      } else {
        // A valid newer inherited clock may come from M5 Launcher or another
        // application. Treat it as real wall time and reconcile offline care.
        pet.syncClock(live);
        Serial.printf("Clock reused from system/Launcher: %lu\n", (unsigned long)live);
      }
    } else if (saved >= 1700000000UL) {
      struct timeval tv{};
      tv.tv_sec = saved;
      tv.tv_usec = 0;
      settimeofday(&tv, nullptr);
      pet.setClock(saved);
      Serial.printf("Clock restored from TamaPoke save: %lu\n", (unsigned long)saved);
    } else {
      Serial.println("Clock not set yet; use Settings date/time or Wi-Fi sync");
    }
  }

'''
text = text[:clock_start] + clock_block + text[clock_end:]

# 2) Password entry needs raw keyboard case. Normal TamaPoke controls are
# intentionally lower-cased, but WPA passwords are case-sensitive.
state_old = "  static bool prevChars[128] = {false};"
if state_old not in text:
    fail("keyboard previous-char state")
text = text.replace(state_old,
                    state_old + "\n  static bool prevWifiChars[128] = {false};", 1)

chars_old = '''  bool chars[128] = {false};
  for (char raw : st.word) {
    unsigned char u = (unsigned char)raw;
    if (u < 128) {
      char c = (char)tolower(u);
      chars[(uint8_t)c] = true;
    }
  }'''
chars_new = '''  bool chars[128] = {false};
  bool wifiChars[128] = {false};
  for (char raw : st.word) {
    unsigned char u = (unsigned char)raw;
    if (u < 128) {
      // Preserve exact case/symbol for Wi-Fi passwords.
      wifiChars[u] = true;
      // Existing game/menu shortcuts remain case-insensitive.
      char c = (char)tolower(u);
      chars[(uint8_t)c] = true;
    }
  }'''
if chars_old not in text:
    fail("keyboard char collection")
text = text.replace(chars_old, chars_new, 1)

call_old = "    handleWifiPasswordInput(chars, prevChars, backEdge, enterEdge, escEdge, spaceEdge);"
call_new = "    handleWifiPasswordInput(wifiChars, prevWifiChars, backEdge, enterEdge, escEdge, spaceEdge);"
if call_old not in text:
    fail("Wi-Fi password input call")
text = text.replace(call_old, call_new, 1)

save_old = "  memcpy(prevChars, chars, sizeof(prevChars));"
if save_old not in text:
    fail("keyboard save state")
text = text.replace(save_old,
                    save_old + "\n  memcpy(prevWifiChars, wifiChars, sizeof(prevWifiChars));", 1)

# 3) Keep sensitive password bytes only as long as needed and make long SSID/
# status lines fit safely on the physical 240-pixel display.
radio_and_clear = r'''static void wifiTimeRadioOff() {
  WiFi.disconnect(true);
  delay(20);
  WiFi.mode(WIFI_OFF);
}

static void wifiTimeClearPassword() {
  memset(wifiSyncPassword, 0, sizeof(wifiSyncPassword));
  wifiSyncPasswordLen = 0;
}'''
text = replace_function(text,
    "static void wifiTimeRadioOff() {",
    "static void wifiTimeBusy(",
    radio_and_clear,
    "Wi-Fi radio/password helpers")

busy = r'''static void wifiTimeBusy(const char *title, const String &line) {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString(title, 120, 28, 1);
  ui.setTextSize(1);
  String shown = line;
  if (shown.length() > 34) shown = shown.substring(0, 31) + "...";
  ui.drawCentreString(shown, 120, 61, 1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Wi-Fi turns off automatically", 120, 91, 1);
  ui.pushSprite(0, 0);
}'''
text = replace_function(text,
    "static void wifiTimeBusy(",
    "static uint32_t wifiTimeFetchNtpHost",
    busy,
    "Wi-Fi busy screen")

connect = r'''static void wifiTimeConnectAndSync(const char *ssid, const char *password, bool useSaved) {
  wifiTimeBusy("WI-FI TIME SYNC", useSaved ? "Connecting to saved network..." : String("Connecting to ") + ssid + "...");

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false);
  delay(60);
  if (useSaved) WiFi.begin();
  else WiFi.begin(ssid, password ? password : "");

  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) delay(80);

  if (WiFi.status() != WL_CONNECTED) {
    wifiTimeClearPassword();
    wifiTimeRadioOff();
    wifiTimeSetResult(false, "CONNECTION FAILED", useSaved ? "No usable saved Wi-Fi" : "Check password / signal");
    return;
  }

  // The ESP32 Wi-Fi stack has already consumed the passphrase; do not retain a
  // plaintext copy in TamaPoke RAM during the NTP request/result screen.
  wifiTimeClearPassword();

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
}'''
text = replace_function(text,
    "static void wifiTimeConnectAndSync(",
    "static void wifiTimeScan() {",
    connect,
    "Wi-Fi connection and shutdown")

password_handler = r'''static void handleWifiPasswordInput(const bool chars[128], const bool prevChars[128],
                                    bool backEdge, bool enterEdge, bool escEdge,
                                    bool spaceEdge) {
  if (escEdge) {
    wifiTimeClearPassword();
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
}'''
text = replace_function(text,
    "static void handleWifiPasswordInput(",
    "static void drawWifiTimePick() {",
    password_handler,
    "case-sensitive Wi-Fi password handler")

# Marker for generated-source audit proof.
text = text.replace("// ULTIMATE_V090_WIFI_TIME_SYNC",
                    "// ULTIMATE_V090_WIFI_TIME_SYNC\n" + MARKER, 1)

# Fail CI if the now-obsolete developer-only instruction survives anywhere in
# the generated user/runtime code.
if "runtime-only (set Wi-Fi in include/user_config.h for NTP)" in text:
    fail("stale user_config clock instruction survived")

MAIN.write_text(text, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Pet bond/streak calendar audit.
# ---------------------------------------------------------------------------
ptext = PET_CPP.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if "#include <time.h>" not in ptext:
    fail("pet.cpp must include time.h from second audit")

register_care = r'''static uint32_t petLocalCalendarDay() {
  time_t now = time(nullptr);
  if (now < 1700000000) return 0;
  struct tm ti{};
  if (localtime_r(&now, &ti) == nullptr) return 0;
  int y = ti.tm_year + 1900;
  if (y < 1970) return 0;
  auto daysBeforeYear = [](int year) -> int64_t {
    int64_t z = (int64_t)year - 1;
    return 365LL * z + z / 4 - z / 100 + z / 400;
  };
  int64_t serial = daysBeforeYear(y) - daysBeforeYear(1970) + ti.tm_yday;
  return serial >= 0 ? (uint32_t)serial : 0;
}

// Runtime tracker identifies which LOCAL calendar day bondToday belongs to.
// On first use after reboot it is initialized from the persisted lastCareDay,
// so rebooting cannot reset the anti-farming allowance.
static uint32_t bondCounterDay = 0;

// First care on the local calendar day advances the streak and grants the
// original +4 daily bond. The daily action counter is not erased if addBond()
// already counted the action that led into this function.
void Pet::registerCare() {
  if (isEgg() || ceremony != CER_NONE) return;
  uint32_t d = petLocalCalendarDay();
  if (d == 0) return;

  // One-time compatibility normalization: the previous audit used UTC day
  // numbers, which could advance lastCareDay several hours before local
  // midnight. Treat d+1 as already cared-for today, not as a new reward.
  if (lastCareDay == d + 1) {
    lastCareDay = d;
    if (bondCounterDay == 0 || bondCounterDay == d + 1) bondCounterDay = d;
    save();
    return;
  }

  // Moving the clock backward must never create extra streak/bond rewards.
  if (lastCareDay > d || lastCareDay == d) return;

  if (bondCounterDay == 0) bondCounterDay = lastCareDay;
  if (bondCounterDay != d) {
    bondToday = 0;
    bondCounterDay = d;
  }

  if (lastCareDay == 0 || d == lastCareDay + 1) {
    streak++;
  } else {
    streak = 1;
    lastMilestone = 0;
  }
  lastCareDay = d;
  if (streak > bestStreak) bestStreak = streak;
  bond = clamp100(bond + 4);
  uint16_t ms = (streak >= 100) ? 100 : (streak >= 30) ? 30
              : (streak >= 7)   ? 7   : (streak >= 3)  ? 3 : 0;
  if (ms > lastMilestone) {
    lastMilestone = ms;
    milestoneUntil = millis() + 4500;
  }
  checkMedals();
  save();
}'''
ptext = replace_function(ptext,
    "void Pet::registerCare() {",
    "void Pet::addBond(uint8_t amt) {",
    register_care,
    "local-day registerCare")

add_bond = r'''void Pet::addBond(uint8_t amt) {
  uint32_t d = petLocalCalendarDay();
  if (d) {
    // Compatibility with the older UTC-day counter during the local evening:
    // preserve today's already-spent allowance while normalizing the day.
    if (lastCareDay == d + 1) {
      if (bondCounterDay == 0) bondCounterDay = d;
    } else {
      // If the clock was moved backward by more than the known migration case,
      // do not allow bond farming against an earlier date.
      if (lastCareDay > d + 1) return;
      if (bondCounterDay == 0) bondCounterDay = lastCareDay;
      if (bondCounterDay != d) {
        bondToday = 0;
        bondCounterDay = d;
      }
    }
  }

  if (bondToday >= 20 || amt == 0) return;
  uint8_t room = (uint8_t)(20 - bondToday);
  uint8_t gain = amt < room ? amt : room;
  bond = clamp100(bond + gain);
  bondToday = (uint8_t)(bondToday + gain);
}'''
ptext = replace_function(ptext,
    "void Pet::addBond(uint8_t amt) {",
    "void Pet::checkMedals() {",
    add_bond,
    "exact local-day bond cap")

PET_CPP.write_text(ptext, encoding="utf-8", newline="\n")
print("[v0.9.0-audit3] Fixed boot clock restore, local-day bond/streak cap, case-sensitive Wi-Fi passwords, and Wi-Fi cleanup")
