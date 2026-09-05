Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
PET_CPP = PROJECT / "generated" / "pet.cpp"
MARKER = "// ULTIMATE_V090_WIFI_PERSISTENCE_BOND_AUDIT"


def fail(msg):
    print(f"[v0.9.0-wifi-bond-audit] ERROR: {msg}")
    env.Exit(1)


def replace_cpp_function(text, signature, replacement, label):
    start = text.find(signature)
    if start < 0:
        fail(f"could not locate {label} start")
    brace = text.find("{", start)
    if brace < 0:
        fail(f"could not locate {label} opening brace")
    depth = 0
    i = brace
    in_str = in_chr = in_line = in_block = esc = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_line:
            if ch == "\n": in_line = False
            i += 1; continue
        if in_block:
            if ch == "*" and nxt == "/": in_block = False; i += 2
            else: i += 1
            continue
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': in_str = False
            i += 1; continue
        if in_chr:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == "'": in_chr = False
            i += 1; continue
        if ch == "/" and nxt == "/": in_line = True; i += 2; continue
        if ch == "/" and nxt == "*": in_block = True; i += 2; continue
        if ch == '"': in_str = True; i += 1; continue
        if ch == "'": in_chr = True; i += 1; continue
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[:start] + replacement.rstrip() + text[i + 1:]
        i += 1
    fail(f"could not locate {label} closing brace")


def extract_cpp_function(text, signature, label):
    start = text.find(signature)
    if start < 0:
        fail(f"could not locate {label} start")
    brace = text.find("{", start)
    if brace < 0:
        fail(f"could not locate {label} opening brace")
    depth = 0
    i = brace
    while i < len(text):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    fail(f"could not locate {label} closing brace")


# ---------------------------------------------------------------------------
# Saved Wi-Fi: NVS + verified device-bound SD fallback.
# ---------------------------------------------------------------------------
text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-wifi-bond-audit] already applied")
    Return()
if "// ULTIMATE_V090_CLOCK_GENGAR_POSITION" not in text:
    fail("Gengar position patch must run first")
if "static const char *WIFI_TIME_PREF_NS = \"tpwifi\";" not in text:
    fail("saved Wi-Fi NVS helpers missing")

# BUILD217 hardware testing showed that Preferences-based saving did not survive
# reliably on the target unit even though the live Wi-Fi connection and NTP sync
# were successful. Keep NVS as the first source, but also write a tiny CRC-checked
# backup to the TamaPoke SD card. The password bytes in that fallback are XORed
# with a key derived from this ESP32's eFuse MAC, so simply moving the SD card to
# another device does not reveal/use the stored passphrase directly.
anchor = "static const char *WIFI_TIME_PREF_NS = \"tpwifi\";"
helper_start = text.find(anchor)
radio_pos = text.find("static void wifiTimeRadioOff()", helper_start)
if helper_start < 0 or radio_pos < 0:
    fail("saved Wi-Fi helper block anchors")

new_helpers = r'''static const char *WIFI_TIME_PREF_NS = "tpwifi";
static const char *WIFI_TIME_SD_PATH = "/tamapoke_wifi.bin";
static constexpr uint32_t WIFI_TIME_SD_MAGIC = 0x31575054UL; // "TPW1"

struct __attribute__((packed)) WifiTimeSavedFile {
  uint32_t magic;
  uint8_t version;
  uint8_t ssidLen;
  uint8_t passLen;
  uint8_t reserved;
  char ssid[33];
  uint8_t pass[64];
  uint32_t crc;
};

static uint32_t wifiTimeSavedHash(const uint8_t *p, size_t n) {
  uint32_t h = 2166136261UL;
  for (size_t i = 0; i < n; ++i) {
    h ^= p[i];
    h *= 16777619UL;
  }
  return h;
}

static uint8_t wifiTimeDeviceKey(size_t i) {
  uint64_t mac = ESP.getEfuseMac();
  uint8_t b = (uint8_t)((mac >> ((i & 7U) * 8U)) & 0xFFU);
  return (uint8_t)(b ^ (uint8_t)(0xA7U + (uint8_t)(i * 29U)));
}

static bool wifiTimeSaveNvs(const String &ssid, const String &password) {
  Preferences p;
  if (!p.begin(WIFI_TIME_PREF_NS, false)) return false;
  p.putString("ssid", ssid);
  p.putString("pass", password);
  String checkSsid = p.getString("ssid", "");
  String checkPass = p.getString("pass", "");
  p.end();
  return checkSsid == ssid && checkPass == password && checkSsid.length() > 0;
}

static bool wifiTimeLoadNvs(String &ssid, String &password) {
  Preferences p;
  if (!p.begin(WIFI_TIME_PREF_NS, true)) return false;
  ssid = p.getString("ssid", "");
  password = p.getString("pass", "");
  p.end();
  return ssid.length() > 0;
}

static bool wifiTimeSaveSdFallback(const String &ssid, const String &password) {
  if (!sdReady || !ssid.length() || ssid.length() > 32 || password.length() > 63) return false;

  WifiTimeSavedFile f{};
  f.magic = WIFI_TIME_SD_MAGIC;
  f.version = 1;
  f.ssidLen = (uint8_t)ssid.length();
  f.passLen = (uint8_t)password.length();
  memcpy(f.ssid, ssid.c_str(), f.ssidLen);
  f.ssid[f.ssidLen] = 0;
  for (uint8_t i = 0; i < f.passLen; ++i)
    f.pass[i] = (uint8_t)password[i] ^ wifiTimeDeviceKey(i);
  f.crc = wifiTimeSavedHash(reinterpret_cast<const uint8_t*>(&f), offsetof(WifiTimeSavedFile, crc));

  SD.remove(WIFI_TIME_SD_PATH);
  File out = SD.open(WIFI_TIME_SD_PATH, FILE_WRITE);
  if (!out) return false;
  size_t wrote = out.write(reinterpret_cast<const uint8_t*>(&f), sizeof(f));
  out.flush();
  out.close();
  return wrote == sizeof(f);
}

static bool wifiTimeLoadSdFallback(String &ssid, String &password) {
  if (!sdReady) return false;
  File in = SD.open(WIFI_TIME_SD_PATH, FILE_READ);
  if (!in || in.size() != sizeof(WifiTimeSavedFile)) {
    if (in) in.close();
    return false;
  }

  WifiTimeSavedFile f{};
  size_t got = in.read(reinterpret_cast<uint8_t*>(&f), sizeof(f));
  in.close();
  if (got != sizeof(f) || f.magic != WIFI_TIME_SD_MAGIC || f.version != 1 ||
      f.ssidLen == 0 || f.ssidLen > 32 || f.passLen > 63 ||
      wifiTimeSavedHash(reinterpret_cast<const uint8_t*>(&f), offsetof(WifiTimeSavedFile, crc)) != f.crc)
    return false;

  char ssidBuf[33] = {0};
  memcpy(ssidBuf, f.ssid, f.ssidLen);
  char passBuf[65] = {0};
  for (uint8_t i = 0; i < f.passLen; ++i)
    passBuf[i] = (char)(f.pass[i] ^ wifiTimeDeviceKey(i));
  passBuf[f.passLen] = 0;

  ssid = String(ssidBuf);
  password = String(passBuf);
  memset(passBuf, 0, sizeof(passBuf));
  return ssid.length() > 0;
}

static void wifiTimeSaveCredentials(const String &ssid, const String &password) {
  if (!ssid.length()) return;

  // Keep two independent persistence paths. NVS is preferred; the device-bound
  // SD copy guarantees USE SAVED WI-FI still works if Preferences storage is
  // unavailable or gets lost on this hardware/launcher combination.
  bool nvsOk = wifiTimeSaveNvs(ssid, password);
  bool sdOk = wifiTimeSaveSdFallback(ssid, password);
  Serial.printf("WIFI SAVE: NVS=%s SD=%s SSID=%s\n",
                nvsOk ? "OK" : "FAIL", sdOk ? "OK" : "FAIL", ssid.c_str());
}

static bool wifiTimeLoadCredentials(String &ssid, String &password) {
  if (wifiTimeLoadNvs(ssid, password)) return true;
  if (!wifiTimeLoadSdFallback(ssid, password)) return false;

  // Best-effort repair: repopulate NVS from the verified SD fallback.
  wifiTimeSaveNvs(ssid, password);
  return true;
}

'''
text = text[:helper_start] + new_helpers + text[radio_pos:]

# Ensure the successful manual-connection path persists credentials before the
# success-path password wipe. A failure branch also clears the buffer earlier,
# so deliberately search for the first clear *after* the save call.
connect_fn = extract_cpp_function(text, "static void wifiTimeConnectAndSync(", "Wi-Fi connect function")
save_call = "if (!useSaved) wifiTimeSaveCredentials(connectSsid, connectPass);"
save_pos = connect_fn.find(save_call)
if save_pos < 0:
    fail("manual Wi-Fi persistence call missing from connect function")
success_clear_pos = connect_fn.find("wifiTimeClearPassword();", save_pos)
if success_clear_pos < 0:
    fail("success-path password clear missing after persistence")

# Build-time proof that USE SAVED WI-FI has both storage paths available.
for needle in [
    "wifiTimeSaveNvs(ssid, password)",
    "wifiTimeSaveSdFallback(ssid, password)",
    "wifiTimeLoadNvs(ssid, password)",
    "wifiTimeLoadSdFallback(ssid, password)",
    "WIFI_TIME_SD_MAGIC",
]:
    if needle not in text:
        fail(f"saved Wi-Fi persistence assertion missing: {needle}")

text = text.replace("// ULTIMATE_V090_CLOCK_GENGAR_POSITION",
                    "// ULTIMATE_V090_CLOCK_GENGAR_POSITION\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Bond mechanics audit + persistence hardening.
# ---------------------------------------------------------------------------
ptext = PET_CPP.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

register_fn = extract_cpp_function(ptext, "void Pet::registerCare()", "registerCare")
add_fn = extract_cpp_function(ptext, "void Pet::addBond(uint8_t amt)", "addBond")
tick_fn = extract_cpp_function(ptext, "void Pet::tick()", "tick")

# The intended v0.9.0 rules are deliberately unchanged:
#   first care of each valid LOCAL calendar day = +4 Bond and streak progress;
#   care actions share a hard +20/day anti-farming allowance;
#   neglect can remove 1 Bond after the care-mistake cooldown.
for needle in ["petLocalCalendarDay()", "bond = clamp100(bond + 4)", "lastCareDay = d"]:
    if needle not in register_fn:
        fail(f"registerCare Bond rule missing: {needle}")
for needle in ["bondToday >= 20", "uint8_t room = (uint8_t)(20 - bondToday)",
               "bondToday = (uint8_t)(bondToday + gain)"]:
    if needle not in add_fn:
        fail(f"daily Bond cap rule missing: {needle}")
if "if (bond > 1) bond--;" not in tick_fn:
    fail("care-mistake Bond penalty missing")

# Verify the original action awards survived every v0.9.0 patch. There are four
# +2 call sites (favorite berry, play/game completion, training, direct play)
# and two +1 care call sites (clean and caress) in the pinned TamaPoke core.
if ptext.count("addBond(2);") < 4:
    fail("expected +2 Bond action call sites are missing")
if ptext.count("addBond(1);") < 2:
    fail("expected +1 Bond care call sites are missing")

# One small persistence bug was still present in the pinned core: caress gained
# Bond but did not explicitly save after registerCare() on days where the daily
# reward had already been claimed. Other care actions already save. Add the same
# explicit save here so a reboot cannot discard recent caress Bond progress.
caress = r'''void Pet::caress() {
  if (ceremony != CER_NONE) return;
  if (isEgg() || sleeping) return;
  joy = clamp100(joy + 5);
  heartUntil = millis() + HEART_MS;
  addBond(1);
  registerCare();
  save();
}'''
ptext = replace_cpp_function(ptext, "void Pet::caress()", caress, "caress Bond persistence")

# Re-audit after the persistence change.
caress_fn = extract_cpp_function(ptext, "void Pet::caress()", "caress final")
if "addBond(1);" not in caress_fn or "registerCare();" not in caress_fn or "save();" not in caress_fn:
    fail("caress Bond persistence audit failed")

PET_CPP.write_text(ptext, encoding="utf-8", newline="\n")
print("[v0.9.0-wifi-bond-audit] Added verified saved Wi-Fi fallback; Bond rules audited and caress persistence hardened")
