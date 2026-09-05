Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_SAVED_WIFI_FIX"


def fail(msg):
    print(f"[v0.9.0-saved-wifi] ERROR: {msg}")
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


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-saved-wifi] already applied")
    Return()
if "// ULTIMATE_V090_GHOST_CLOCK_ORIGINAL_SPRITES" not in text:
    fail("original Ghost Clock sprites patch must run first")

if "#include <Preferences.h>" not in text:
    if "#include <WiFi.h>\n" not in text:
        fail("WiFi include anchor missing")
    text = text.replace("#include <WiFi.h>\n", "#include <WiFi.h>\n#include <Preferences.h>\n", 1)

# Explicitly persist the last SUCCESSFUL Wi-Fi credentials in ESP32 NVS rather
# than depending on WiFi.begin()'s implicit SDK credential slot. This makes the
# UI's 'USE SAVED WI-FI' behavior deterministic across reboots and radio-off
# cycles. Credentials are not written to the SD card.
anchor = "static void wifiTimeRadioOff() {"
pos = text.find(anchor)
if pos < 0:
    fail("Wi-Fi helper anchor")

helpers = r'''static const char *WIFI_TIME_PREF_NS = "tpwifi";

static void wifiTimeSaveCredentials(const String &ssid, const String &password) {
  if (!ssid.length()) return;
  Preferences p;
  if (!p.begin(WIFI_TIME_PREF_NS, false)) return;
  p.putString("ssid", ssid);
  p.putString("pass", password);
  p.end();
}

static bool wifiTimeLoadCredentials(String &ssid, String &password) {
  Preferences p;
  if (!p.begin(WIFI_TIME_PREF_NS, true)) return false;
  ssid = p.getString("ssid", "");
  password = p.getString("pass", "");
  p.end();
  return ssid.length() > 0;
}

'''
text = text[:pos] + helpers + text[pos:]

radio = r'''static void wifiTimeRadioOff() {
  // Turn the radio off without erasing saved AP credentials.
  WiFi.disconnect(true, false);
  delay(30);
  WiFi.mode(WIFI_OFF);
}'''
text = replace_cpp_function(text, "static void wifiTimeRadioOff()", radio,
                            "Wi-Fi radio shutdown")

connect = r'''static void wifiTimeConnectAndSync(const char *ssid, const char *password, bool useSaved) {
  String connectSsid;
  String connectPass;

  if (useSaved) {
    if (!wifiTimeLoadCredentials(connectSsid, connectPass)) {
      wifiTimeRadioOff();
      wifiTimeSetResult(false, "NO SAVED WI-FI", "Connect once from the network list");
      return;
    }
  } else {
    connectSsid = ssid ? ssid : "";
    connectPass = password ? password : "";
    if (!connectSsid.length()) {
      wifiTimeRadioOff();
      wifiTimeSetResult(false, "CONNECTION FAILED", "No Wi-Fi network selected");
      return;
    }
  }

  String shown = useSaved ? String("Connecting to ") + connectSsid + "..."
                          : String("Connecting to ") + connectSsid + "...";
  wifiTimeBusy("WI-FI TIME SYNC", shown);

  // Start from a clean station state, but do NOT erase NVS credentials.
  WiFi.disconnect(false, false);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false);
  delay(80);
  WiFi.begin(connectSsid.c_str(), connectPass.c_str());

  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000UL) {
    delay(60);
    yield();
  }

  if (WiFi.status() != WL_CONNECTED) {
    wifiTimeClearPassword();
    connectPass = "";
    wifiTimeRadioOff();
    wifiTimeSetResult(false, "CONNECTION FAILED",
                      useSaved ? "Saved Wi-Fi could not connect" : "Check password / signal");
    return;
  }

  // Only remember credentials after a successful manual connection. Updating
  // a password therefore cannot destroy the previous working entry unless the
  // new credentials actually connect.
  if (!useSaved) wifiTimeSaveCredentials(connectSsid, connectPass);

  wifiTimeClearPassword();
  connectPass = "";

  wifiTimeBusy("WI-FI TIME SYNC", "Getting network time...");
  uint32_t epoch = wifiTimeFetchNtp();
  if (!epoch) {
    wifiTimeRadioOff();
    wifiTimeSetResult(false, "TIME SYNC FAILED", "Internet connected, NTP unavailable");
    return;
  }

  wifiTimeRadioOff();
  wifiTimeApplyEpoch(epoch);
}'''
text = replace_cpp_function(text, "static void wifiTimeConnectAndSync(", connect,
                            "deterministic saved Wi-Fi reconnect")

# Marker for generated-source audit proof.
text = text.replace("// ULTIMATE_V090_GHOST_CLOCK_ORIGINAL_SPRITES",
                    "// ULTIMATE_V090_GHOST_CLOCK_ORIGINAL_SPRITES\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-saved-wifi] Saved Wi-Fi now uses explicit NVS credentials from the last successful manual connection")
