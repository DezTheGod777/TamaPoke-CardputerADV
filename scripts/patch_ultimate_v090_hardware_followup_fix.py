Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_HARDWARE_FOLLOWUP_FIX"


def fail(msg):
    print(f"[v0.9.0-hw-followup] ERROR: {msg}")
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
    print("[v0.9.0-hw-followup] already applied")
    Return()
if "// ULTIMATE_V090_WIFI_SCAN_HANG_FIX" not in text:
    fail("Wi-Fi scan hang fix must run first")

# Hardware follow-up: after a successful scan, do not tear the ESP32 Wi-Fi
# driver down at the exact moment the network picker appears. On Cardputer ADV
# that transition can leave the UI apparently frozen even though the scan
# completed. Keep STA idle (not connected) while the picker is visible and shut
# it down when leaving the picker or after a time-sync attempt.
scan_fn = r'''static void wifiTimeScan() {
  wifiTimeBusy("WI-FI TIME SYNC", "Scanning networks...");
  wifiSyncCount = 0;
  wifiSyncSel = 0;

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
    // Bound the operation so a driver problem can never trap the user forever.
    WiFi.mode(WIFI_OFF);
    wifiTimeSetResult(false, "SCAN TIMED OUT", "Try again or use saved Wi-Fi");
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
  // Intentionally keep STA idle here. There is no connection and no NTP
  // traffic; avoiding an immediate radio-driver teardown makes the picker
  // reliable on physical Cardputer ADV hardware. ESC/Back still powers it off.
  screen = WIFI_SYNC_PICK;
  dirty = true;
}'''
text = replace_cpp_function(text, "static void wifiTimeScan()", scan_fn,
                            "hardware-safe Wi-Fi scan")

picker_fn = r'''static void drawWifiTimePick() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("WI-FI TIME SYNC", 120, 3, 1);
  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString(wifiSyncCount ? "Choose a network" : "Choose saved Wi-Fi or scan", 120, 21, 1);

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
text = replace_cpp_function(text, "static void drawWifiTimePick()", picker_fn,
                            "hardware-safe Wi-Fi picker")

# Match the Home-screen battery treatment on the Ghost Clock. The meter itself
# remains visible, but its cream backing plate is omitted so the clock's dark
# gradient shows through cleanly instead of a solid rectangle.
battery_fn = r'''static void drawBatteryMeter() {
  sampleBattery();
  const int x = 216, y = 3;
  uint16_t outline = sceneNight() ? UI_INK_NIGHT : UI_INK;
  uint16_t fill = UI_OK;
  if (batteryLevel >= 0 && batteryLevel <= 15) fill = UI_BAD;
  else if (batteryLevel >= 0 && batteryLevel <= 35) fill = UI_WARN;

  const bool transparentHud = ((screen == HOME && !idleTerrarium) || screen == CLOCK_CALENDAR);
  if (!transparentHud) {
    ui.fillRoundRect(x - 1, y - 1, 21, 11, 3,
                     sceneNight() ? C565(0x14,0x1c,0x30) : UI_CREAM);
  }

  // On the Ghost Clock use the light lavender outline so it stays readable on
  // the dark purple sky while remaining visually transparent.
  if (screen == CLOCK_CALENDAR) outline = C565(0xd8,0xbf,0xf2);

  ui.drawRoundRect(x, y, 17, 8, 2, outline);
  ui.fillRect(x + 17, y + 2, 2, 4, outline);
  if (batteryLevel >= 0) {
    int fw = (13 * batteryLevel + 50) / 100;
    if (fw > 0) ui.fillRect(x + 2, y + 2, fw, 4, fill);
    if (batteryLevel <= 15 && !transparentHud) {
      ui.setTextSize(1);
      ui.setTextColor(UI_BAD);
      ui.drawString("!", x - 7, y);
    }
  } else {
    ui.drawLine(x + 4, y + 2, x + 12, y + 5, outline);
  }
}'''
text = replace_cpp_function(text, "static void drawBatteryMeter()", battery_fn,
                            "transparent Ghost Clock battery HUD")

text = text.replace("// ULTIMATE_V090_WIFI_SCAN_HANG_FIX",
                    "// ULTIMATE_V090_WIFI_SCAN_HANG_FIX\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-hw-followup] Hardened Wi-Fi picker transition and made Ghost Clock battery HUD transparent")
