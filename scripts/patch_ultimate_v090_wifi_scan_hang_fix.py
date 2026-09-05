Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_WIFI_SCAN_HANG_FIX"


def fail(msg):
    print(f"[v0.9.0-wifi-scan-fix] ERROR: {msg}")
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
    print("[v0.9.0-wifi-scan-fix] already applied")
    Return()
if "// ULTIMATE_V090_PUBLIC_SPECIAL_BACKGROUNDS" not in text:
    fail("special backgrounds patch must run first")

# Do not launch a blocking Wi-Fi scan merely by entering Settings > Wi-Fi Time
# Sync. Opening the feature is now instant and leaves the radio off. The user
# can try saved Wi-Fi immediately or explicitly request a scan.
open_fn = r'''static void openWifiTimeSync() {
  wifiTimeClearPassword();
  wifiSyncCount = 0;
  wifiSyncSel = 0;
  wifiSyncChosenSsid = "";
  wifiTimeRadioOff();
  screen = WIFI_SYNC_PICK;
  dirty = true;
}'''
text = replace_cpp_function(text, "static void openWifiTimeSync()", open_fn,
                            "Wi-Fi time-sync opener")

# ESP32's synchronous scanNetworks(false, ...) can occasionally stall inside
# the driver and make the whole UI appear frozen. Use an asynchronous scan with
# an explicit 8-second watchdog instead. No scan path can hold the UI forever.
scan_fn = r'''static void wifiTimeScan() {
  wifiTimeBusy("WI-FI TIME SYNC", "Scanning networks...");
  wifiSyncCount = 0;
  wifiSyncSel = 0;

  // Start from a known radio state before asking the Wi-Fi driver to scan.
  WiFi.scanDelete();
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false);
  delay(80);

  int startResult = WiFi.scanNetworks(true, true); // async, include hidden
  if (startResult == WIFI_SCAN_FAILED) {
    WiFi.scanDelete();
    wifiTimeRadioOff();
    wifiTimeSetResult(false, "SCAN FAILED", "Wi-Fi scanner could not start");
    return;
  }

  uint32_t started = millis();
  int n = WIFI_SCAN_RUNNING;
  while (millis() - started < 8000UL) {
    n = WiFi.scanComplete();
    if (n != WIFI_SCAN_RUNNING) break;
    delay(40);
    yield();
  }

  if (n == WIFI_SCAN_RUNNING) {
    // Never leave the user trapped if the ESP32 driver fails to report scan
    // completion. The next attempt starts cleanly after the radio is reset.
    WiFi.scanDelete();
    wifiTimeRadioOff();
    wifiTimeSetResult(false, "SCAN TIMED OUT", "Try scan again or use saved Wi-Fi");
    return;
  }

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
}'''
text = replace_cpp_function(text, "static void wifiTimeScan()", scan_fn,
                            "bounded asynchronous Wi-Fi scan")

# Make the picker wording sensible before the first scan.
draw_fn = r'''static void drawWifiTimePick() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("WI-FI TIME SYNC", 120, 3, 1);
  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Radio is OFF while choosing", 120, 21, 1);

  int total = 1 + wifiSyncCount + 1; // saved + networks + scan/rescan
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
    else if (item == total - 1) label = wifiSyncCount ? "RESCAN NETWORKS" : "SCAN FOR NETWORKS";
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
}'''
text = replace_cpp_function(text, "static void drawWifiTimePick()", draw_fn,
                            "Wi-Fi picker labels")

# Marker for generated-source audit proof.
text = text.replace("// ULTIMATE_V090_PUBLIC_SPECIAL_BACKGROUNDS",
                    "// ULTIMATE_V090_PUBLIC_SPECIAL_BACKGROUNDS\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-wifi-scan-fix] Wi-Fi Time Sync now opens instantly; scans are async and time-bounded")
