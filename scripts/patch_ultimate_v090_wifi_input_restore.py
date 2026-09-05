Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_WIFI_INPUT_RESTORE"


def fail(msg):
    print(f"[v0.9.0-wifi-input-restore] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-wifi-input-restore] already applied")
    Return()
if "// ULTIMATE_V090_CLOCK_TITLE_CLEANUP" not in text:
    fail("clock title cleanup must run first")

# Root cause found during hardware testing:
# patch_ultimate_v090_wifi_time_sync.py originally inserted WIFI_SYNC_PICK and
# WIFI_SYNC_RESULT input handlers immediately before SET_CLOCK. Later, the
# Ghost Clock patch replaced the whole SETTINGS -> SET_CLOCK input region and
# accidentally removed those Wi-Fi input branches. The Wi-Fi picker still drew,
# but no Up/Down/Enter/Esc code was running, which looked exactly like a freeze.
# Restore the handlers LAST in the patch chain so later UI patches cannot erase
# them again.
if "} else if (screen == WIFI_SYNC_PICK) {" not in text:
    anchor = "  } else if (screen == SET_CLOCK) {"
    if anchor not in text:
        fail("SET_CLOCK input anchor missing")

    handlers = r'''  } else if (screen == WIFI_SYNC_PICK) {
    int total = 1 + wifiSyncCount + 1; // saved + discovered networks + scan/rescan
    if (total < 2) total = 2;

    if (upEdge) {
      wifiSyncSel = wifiSyncSel == 0 ? total - 1 : wifiSyncSel - 1;
      dirty = true;
    }
    if (downEdge) {
      wifiSyncSel = (wifiSyncSel + 1) % total;
      dirty = true;
    }
    if (enterEdge || spaceEdge) {
      wifiTimeChooseNetwork();
    }
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
    text = text.replace(anchor, handlers + anchor, 1)
else:
    print("[v0.9.0-wifi-input-restore] picker handler already present")

# Build-time assertions: fail CI rather than ship another unresponsive picker.
required = [
    "} else if (screen == WIFI_SYNC_PICK) {",
    "wifiSyncSel = wifiSyncSel == 0 ? total - 1 : wifiSyncSel - 1;",
    "wifiSyncSel = (wifiSyncSel + 1) % total;",
    "wifiTimeChooseNetwork();",
    "} else if (screen == WIFI_SYNC_RESULT) {",
]
for needle in required:
    if needle not in text:
        fail(f"restored handler assertion missing: {needle}")

text = text.replace("// ULTIMATE_V090_CLOCK_TITLE_CLEANUP",
                    "// ULTIMATE_V090_CLOCK_TITLE_CLEANUP\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-wifi-input-restore] Restored Wi-Fi picker/result keyboard handlers after Ghost Clock patch replacement")
