Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_CLOCK_TITLE_CLEANUP"


def fail(msg):
    print(f"[v0.9.0-clock-title] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-clock-title] already applied")
    Return()
if "// ULTIMATE_V090_WIFI_ENTRY_CLOCK_LAYOUT_FIX" not in text:
    fail("Wi-Fi entry / clock layout fix must run first")

old = '  ui.setTextSize(1); ui.setTextColor(lav); ui.drawCentreString("GHOST CLOCK", 120, 3, 1);\n'
if old not in text:
    fail("GHOST CLOCK title line not found")
text = text.replace(old, "", 1)

anchor = "// ULTIMATE_V090_WIFI_ENTRY_CLOCK_LAYOUT_FIX"
text = text.replace(anchor, anchor + "\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-clock-title] Removed GHOST CLOCK label from clock/calendar screen")
