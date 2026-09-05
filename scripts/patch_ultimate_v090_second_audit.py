Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
PET_CPP = PROJECT / "generated" / "pet.cpp"
MARKER = "// ULTIMATE_V090_SECOND_AUDIT"


def fail(msg):
    print(f"[v0.9.0-ultimate-audit2] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


def replace_function(text, start_sig, next_sig, body, label):
    start = text.find(start_sig)
    if start < 0:
        fail(f"could not locate {label} start")
    end = text.find(next_sig, start)
    if end < 0:
        fail(f"could not locate {label} end")
    return text[:start] + body.rstrip() + "\n\n" + text[end:]


# ---------------------------------------------------------------------------
# Main firmware second-pass audit fixes.
# ---------------------------------------------------------------------------
text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-audit2] second audit already applied")
    Return()
if "// ULTIMATE_V090_FINAL_HARDENING" not in text:
    fail("final hardening must run first")

# 1) Daily calendar must advance while the device stays powered on and must
# follow the configured LOCAL date rather than UTC midnight. Keep the serial
# compatible with Unix-day scale so existing Ultimate daily files are at most
# one day off when migrating from the earlier UTC-day implementation.
new_calendar_day = r'''static uint32_t ultimateCalendarDay() {
  struct tm ti{};
  if (!getLocalTime(&ti, 2)) return 0;
  int y = ti.tm_year + 1900;
  if (y < 1970) return 0;
  auto daysBeforeYear = [](int year) -> int64_t {
    int64_t z = (int64_t)year - 1;
    return 365LL * z + z / 4 - z / 100 + z / 400;
  };
  int64_t serial = daysBeforeYear(y) - daysBeforeYear(1970) + ti.tm_yday;
  return serial >= 0 ? (uint32_t)serial : 0;
}'''
text = replace_function(text,
    "static uint32_t ultimateCalendarDay() {",
    "static const char* ultimateDailyEventName",
    new_calendar_day,
    "live local daily calendar")

# 2) Preserve Phase-7 daily progress from pre-hardening v1 test builds instead
# of silently rejecting the smaller old config after the v2 anniversary field.
new_daily_loader = r'''static void loadUltimateDaily() {
  if (!sdReady) return;
  File f = SD.open(ULT_DAILY_CFG_PATH, FILE_READ);
  if (!f) return;
  size_t sz = f.size();

  if (sz == sizeof(UltimateDailyFile)) {
    UltimateDailyFile c{};
    size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c)); f.close();
    if (got != sizeof(c) || c.magic != 0x37444D54UL || c.version != 2 ||
        ultimateDailyCrc(c) != c.crc) return;
    ultimateLastRewardDay = c.lastRewardDay;
    ultimateAdoptionDay = c.adoptionDay;
    ultimateLastEventDay = c.lastEventDay;
    ultimateLastGreetingKey = c.lastGreetingKey;
    ultimateCareCoinDay = c.careCoinDay;
    ultimateLastAnniversaryDay = c.lastAnniversaryDay;
    ultimateCareCoinsToday = c.careCoinsToday;
    ultimateLastDailyEvent = c.lastEvent;
    return;
  }

  struct __attribute__((packed)) UltimateDailyFileV1 {
    uint32_t magic;
    uint8_t version;
    uint32_t lastRewardDay;
    uint32_t adoptionDay;
    uint32_t lastEventDay;
    uint32_t lastGreetingKey;
    uint32_t careCoinDay;
    uint8_t careCoinsToday;
    uint8_t lastEvent;
    uint8_t reserved[2];
    uint32_t crc;
  };

  if (sz == sizeof(UltimateDailyFileV1)) {
    UltimateDailyFileV1 c{};
    size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c)); f.close();
    uint32_t crc = displayCfgHash(reinterpret_cast<const uint8_t*>(&c),
                                  offsetof(UltimateDailyFileV1, crc));
    if (got != sizeof(c) || c.magic != 0x37444D54UL || c.version != 1 || crc != c.crc) return;
    ultimateLastRewardDay = c.lastRewardDay;
    ultimateAdoptionDay = c.adoptionDay;
    ultimateLastEventDay = c.lastEventDay;
    ultimateLastGreetingKey = c.lastGreetingKey;
    ultimateCareCoinDay = c.careCoinDay;
    ultimateLastAnniversaryDay = 0;
    ultimateCareCoinsToday = c.careCoinsToday;
    ultimateLastDailyEvent = c.lastEvent;
    saveUltimateDaily(); // one-time in-place migration to v2
    return;
  }

  f.close();
}'''
text = replace_function(text,
    "static void loadUltimateDaily() {",
    "static uint32_t ultimateCalendarDay",
    new_daily_loader,
    "daily v1 migration loader")

# 3) A completed secret word consumes its final key. Without this, the final E
# in ULTIMATE could immediately open the evolution dialog after awarding the
# mystery gift.
new_secret_printable = r'''static bool ultimateSecretPrintable(char c) {
  if (!isalnum((unsigned char)c)) return false;
  c = (char)tolower((unsigned char)c);
  if (ultimateSecretWordLen < sizeof(ultimateSecretWord) - 1) {
    ultimateSecretWord[ultimateSecretWordLen++] = c;
  } else {
    memmove(ultimateSecretWord, ultimateSecretWord + 1, sizeof(ultimateSecretWord) - 2);
    ultimateSecretWord[sizeof(ultimateSecretWord) - 2] = c;
    ultimateSecretWordLen = sizeof(ultimateSecretWord) - 1;
  }
  ultimateSecretWord[ultimateSecretWordLen] = 0;

  if (ultimateSecretWordEnds("mew")) {
    bool fresh = (ultimateSecretFlags & ULT_SECRET_DREAM) == 0;
    ultimateUnlockSecret(ULT_SECRET_DREAM, "DREAM HOME", 2);
    if (fresh) {
      ultimateRareEncounterDex = 151;
      ultimateRareEncounterUntil = millis() + 8000;
      ultimateAwardCoins(50);
      if (ultimateItems[9] < 99) ultimateItems[9]++;
      saveUltimateEconomy();
    }
    screen = HOME; feedOpen = false; dirty = true;
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  if (ultimateSecretWordEnds("151")) {
    ultimateUnlockSecret(ULT_SECRET_MASTER151, "151 MASTER BORDER", 3);
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  if (ultimateSecretWordEnds("ultimate")) {
    bool fresh = (ultimateSecretFlags & ULT_SECRET_MYSTERY_GIFT) == 0;
    ultimateUnlockSecret(ULT_SECRET_MYSTERY_GIFT, "MYSTERY GIFT", 4);
    if (fresh) {
      uint8_t b = random(3);
      if (ultimateItems[b] < 99) ultimateItems[b]++;
      ultimateAwardCoins(75);
      saveUltimateEconomy();
    }
    screen = HOME; feedOpen = false; dirty = true;
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  return false;
}'''
text = replace_function(text,
    "static void ultimateSecretPrintable(char c) {",
    "static void serviceUltimateSecrets",
    new_secret_printable,
    "secret key consumption")
text = rep(text,
    "    ultimateSecretPrintable(c);\n    if (screen == HOME && !feedOpen) {",
    "    if (ultimateSecretPrintable(c)) continue;\n    if (screen == HOME && !feedOpen) {",
    "consume completed secret key")

# 4) File copies now verify destination size; missing auxiliary files remove any
# stale copy from an older backup slot so a new snapshot cannot restore old
# inventory/home/daily/secret data by accident.
new_copy = r'''static bool ultimateCopyFile(const char *src, const char *dst) {
  File in = SD.open(src, FILE_READ);
  if (!in) return false;
  size_t expected = in.size();
  SD.remove(dst);
  File out = SD.open(dst, FILE_WRITE);
  if (!out) { in.close(); return false; }
  uint8_t buf[256];
  bool ok = true;
  while (in.available()) {
    int n = in.read(buf, sizeof(buf));
    if (n <= 0) { ok = false; break; }
    if (out.write(buf, n) != (size_t)n) { ok = false; break; }
  }
  out.flush(); in.close(); out.close();
  if (!ok) return false;
  File verify = SD.open(dst, FILE_READ);
  if (!verify) return false;
  bool same = verify.size() == expected;
  verify.close();
  return same;
}'''
text = replace_function(text,
    "static bool ultimateCopyFile(const char *src, const char *dst) {",
    "static String ultimateBackupPath",
    new_copy,
    "verified file copy")

new_backup_aux = r'''static bool ultimateBackupAux(uint8_t slot, const char *src, const char *suffix) {
  String dst = ultimateBackupPath(slot, suffix);
  if (!SD.exists(src)) {
    // Exact snapshot semantics: never leave an older slot's auxiliary file.
    SD.remove(dst.c_str());
    return true;
  }
  return ultimateCopyFile(src, dst.c_str());
}'''
text = replace_function(text,
    "static bool ultimateBackupAux(uint8_t slot, const char *src, const char *suffix) {",
    "static bool ultimateBackupSlotValid",
    new_backup_aux,
    "stale auxiliary backup cleanup")

# 5) Restore is staged before touching the live journal. If any read/copy stage
# fails, the current save remains untouched. Auxiliary files are staged too;
# absent files in the selected snapshot are removed on commit for exact restore.
new_restore = r'''static void ultimateRestoreBackup(uint8_t slot) {
  if (!ultimateBackupSlotValid(slot)) {
    ultimateSaveManagerStatus = String("Slot ") + slot + " has no valid save";
    sfxPlay(SFX_DENY); dirty = true; return;
  }

  String ba = ultimateBackupPath(slot, "_a.bin");
  String bb = ultimateBackupPath(slot, "_b.bin");
  bool va = ultimateValidateJournal(ba.c_str());
  bool vb = ultimateValidateJournal(bb.c_str());
  const char *srcA = va ? ba.c_str() : bb.c_str();
  const char *srcB = vb ? bb.c_str() : ba.c_str();

  const char *tmpA = "/tamapoke_restore_a.tmp";
  const char *tmpB = "/tamapoke_restore_b.tmp";
  SD.remove(tmpA); SD.remove(tmpB);
  bool staged = ultimateCopyFile(srcA, tmpA) && ultimateCopyFile(srcB, tmpB) &&
                ultimateValidateJournal(tmpA) && ultimateValidateJournal(tmpB);

  static const char *liveAux[] = {
    ULTIMATE_HOME_CFG_PATH, ULTIMATE_ECON_CFG_PATH, ULT_GAME_CFG_PATH,
    ULT_DAILY_CFG_PATH, ULT_DEX_HISTORY_PATH, "/tamapoke_ultimate_secrets.cfg"
  };
  static const char *suffix[] = {
    "_home.cfg", "_economy.cfg", "_games.cfg", "_daily.cfg", "_dex.bin", "_secrets.cfg"
  };
  static const char *tmpAux[] = {
    "/tp_restore_home.tmp", "/tp_restore_econ.tmp", "/tp_restore_games.tmp",
    "/tp_restore_daily.tmp", "/tp_restore_dex.tmp", "/tp_restore_secrets.tmp"
  };
  bool auxPresent[6] = {false,false,false,false,false,false};

  for (int i = 0; i < 6 && staged; ++i) {
    SD.remove(tmpAux[i]);
    String src = ultimateBackupPath(slot, suffix[i]);
    auxPresent[i] = SD.exists(src.c_str());
    if (auxPresent[i]) staged = ultimateCopyFile(src.c_str(), tmpAux[i]);
  }

  if (!staged) {
    SD.remove(tmpA); SD.remove(tmpB);
    for (int i = 0; i < 6; ++i) SD.remove(tmpAux[i]);
    ultimateSaveManagerStatus = "Restore staging FAILED - live save safe";
    sfxPlay(SFX_DENY); dirty = true; return;
  }

  auto commitTemp = [](const char *tmp, const char *dst) -> bool {
    SD.remove(dst);
    if (SD.rename(tmp, dst)) return true;
    bool ok = ultimateCopyFile(tmp, dst);
    SD.remove(tmp);
    return ok;
  };

  bool okA = commitTemp(tmpA, "/tamapoke_v7_a.bin");
  bool okB = commitTemp(tmpB, "/tamapoke_v7_b.bin");
  bool auxOk = true;
  for (int i = 0; i < 6; ++i) {
    if (auxPresent[i]) auxOk &= commitTemp(tmpAux[i], liveAux[i]);
    else { SD.remove(liveAux[i]); SD.remove(tmpAux[i]); }
  }

  bool liveValid = ultimateValidateJournal("/tamapoke_v7_a.bin") ||
                   ultimateValidateJournal("/tamapoke_v7_b.bin");
  if (!(okA || okB) || !liveValid) {
    ultimateSaveManagerStatus = "Restore commit FAILED";
    sfxPlay(SFX_DENY); dirty = true; return;
  }

  bool full = okA && okB && auxOk;
  ultimateSaveManagerStatus = full ? String("Restored slot ") + slot + " - restarting"
                                   : String("Restored pet; some extras reset");
  noteEvent(ultimateSaveManagerStatus);
  sfxPlay(full ? SFX_MEDAL : SFX_DENY);
  ui.fillScreen(UI_CREAM); ui.setTextColor(UI_INK); ui.setTextSize(2);
  ui.drawCentreString(full ? "RESTORE COMPLETE" : "RESTORE PARTIAL", 120, 48, 1);
  ui.setTextSize(1); ui.drawCentreString("Restarting to load restored save...", 120, 76, 1); ui.pushSprite(0,0);
  delay(1200);
  ESP.restart();
}'''
text = replace_function(text,
    "static void ultimateRestoreBackup(uint8_t slot) {",
    "static void ultimateArmRestore",
    new_restore,
    "staged restore")

# Marker in generated main for CI proof.
name_anchor = 'static constexpr const char *FIRMWARE_NAME = "TamaPoke Ultimate";\n// ULTIMATE_V090_FINAL_HARDENING'
text = rep(text, name_anchor, name_anchor + "\n" + MARKER, "second audit marker")
MAIN.write_text(text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# Pet persistence clock audit. The old runtime kept lastSeenEpoch frozen at
# boot, so a long powered-on session could be counted again as offline time on
# the next restart. Save a minute-quantized live system epoch into the SD
# journal and use the live clock for care-day/bond-day logic.
# ---------------------------------------------------------------------------
ptext = PET_CPP.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if "#include <time.h>" not in ptext:
    ptext = rep(ptext, "#include <cstring>", "#include <cstring>\n#include <time.h>", "pet time include")

ptext = rep(ptext,
    '  if (lastSeenEpoch) prefs.putUInt("seen", lastSeenEpoch);',
    '  time_t rtSeen = time(nullptr);\n'
    '  uint32_t seenNow = (rtSeen >= 1700000000) ? (uint32_t)rtSeen : lastSeenEpoch;\n'
    '  if (seenNow) prefs.putUInt("seen", seenNow);',
    "live Preferences seen time")

ptext = rep(ptext,
    '  d.lastSeenEpoch = lastSeenEpoch; d.ceremony = ceremony; d.lastEnd = lastEnd;',
    '  time_t rtJournal = time(nullptr);\n'
    '  uint32_t journalSeen = (rtJournal >= 1700000000)\n'
    '      ? ((uint32_t)rtJournal / 60UL) * 60UL : lastSeenEpoch;\n'
    '  d.lastSeenEpoch = journalSeen; d.ceremony = ceremony; d.lastEnd = lastEnd;',
    "minute-quantized SD seen time")

ptext = rep(ptext,
    '  uint32_t d = today();\n  if (d == 0 || d == lastCareDay) return;',
    '  time_t rtDay = time(nullptr);\n'
    '  uint32_t d = (rtDay >= 1700000000) ? (uint32_t)rtDay / 86400UL : today();\n'
    '  if (d == 0 || d == lastCareDay) return;',
    "live care day")

ptext = rep(ptext,
    'void Pet::addBond(uint8_t amt) {\n  if (bondToday >= 20) return;',
    'void Pet::addBond(uint8_t amt) {\n'
    '  time_t rtDay = time(nullptr);\n'
    '  uint32_t d = (rtDay >= 1700000000) ? (uint32_t)rtDay / 86400UL : today();\n'
    '  if (d && d != lastCareDay) bondToday = 0;\n'
    '  if (bondToday >= 20) return;',
    "live bond cap day reset")

PET_CPP.write_text(ptext, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-audit2] Fixed live calendar/offline clock drift, daily migration, secret key handling and staged backup restore")
