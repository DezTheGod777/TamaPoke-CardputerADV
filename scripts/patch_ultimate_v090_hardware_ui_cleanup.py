Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_HARDWARE_UI_CLEANUP"


def fail(msg):
    print(f"[v0.9.0-ui-cleanup] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ui-cleanup] hardware UI cleanup already applied")
    Return()
if "// ULTIMATE_V090_MANUAL_CLOCK" not in text:
    fail("manual clock patch must run first")

# Hardware test cleanup 1: the Hub title is enough. Remove the development
# subtitle (version / phase count) so the screen looks like a normal release UI.
hub_old = '''  ui.setTextSize(1);\n  ui.setTextColor(C565(0x6d,0x6b,0x68));\n  ui.drawCentreString("v0.9.0  -  12 PHASES ACTIVE", 120, 19, 1);\n\n  static const char *items[8] = {'''
hub_new = '''  ui.setTextSize(1);\n  ui.setTextColor(C565(0x6d,0x6b,0x68));\n\n  static const char *items[8] = {'''
if hub_old not in text:
    fail("Ultimate Hub subtitle anchor missing")
text = text.replace(hub_old, hub_new, 1)

# Hardware test cleanup 2: this helper sentence was drawn at y=101 while the
# DECOR row occupies roughly y=99..111, causing the unreadable overlap seen on
# the physical Cardputer display. The unlock behavior is unchanged; only the
# overlapping helper label is removed.
custom_old = '''  ui.drawCentreString("BACK", 120, by + 4, 1);\n  ui.setTextColor(C565(0x6d,0x6b,0x68));\n  ui.drawCentreString("Props unlock by play, care & progress", 120, 101, 1);\n}'''
custom_new = '''  ui.drawCentreString("BACK", 120, by + 4, 1);\n}'''
if custom_old not in text:
    fail("Home Customize overlap anchor missing")
text = text.replace(custom_old, custom_new, 1)

# Hardware test cleanup 3: Settings already exposes About / Version. Remove the
# duplicate version string from the extreme bottom-left, where it crowds the
# footer on the physical 240x135 display.
settings_old = '''  ui.drawString(FIRMWARE_VERSION, 4, 123);\n  ui.drawCentreString("LEFT/RIGHT ADJUST  ENTER SELECT", 128, 123, 1);'''
settings_new = '''  ui.drawCentreString("LEFT/RIGHT ADJUST  ENTER SELECT", 120, 123, 1);'''
if settings_old not in text:
    fail("Settings version footer anchor missing")
text = text.replace(settings_old, settings_new, 1)

# Marker for CI / audit proof.
marker_anchor = "// ULTIMATE_V090_MANUAL_CLOCK"
text = text.replace(marker_anchor, marker_anchor + "\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ui-cleanup] Removed Hub dev subtitle, Customize overlap, and Settings footer version")
