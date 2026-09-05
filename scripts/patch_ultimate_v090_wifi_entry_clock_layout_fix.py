Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
PMD = PROJECT / "src" / "pmd_stream.cpp"
MARKER = "// ULTIMATE_V090_WIFI_ENTRY_CLOCK_LAYOUT_FIX"


def fail(msg):
    print(f"[v0.9.0-entry-clock-fix] ERROR: {msg}")
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
    print("[v0.9.0-entry-clock-fix] already applied")
    Return()
if "// ULTIMATE_V090_SAVED_WIFI_FIX" not in text:
    fail("saved Wi-Fi fix must run first")

# Hardware report: merely entering Wi-Fi Time Sync could still freeze. Make the
# entry path completely radio/driver-free. No WiFi.* function is called until
# the user explicitly chooses SCAN FOR NETWORKS or USE SAVED WI-FI.
open_fn = r'''static void openWifiTimeSync() {
  wifiSyncPasswordLen = 0;
  wifiSyncPassword[0] = 0;
  wifiSyncCount = 0;
  wifiSyncSel = 0;
  wifiSyncChosenSsid = "";
  screen = WIFI_SYNC_PICK;
  dirty = true;
}'''
text = replace_cpp_function(text, "static void openWifiTimeSync()", open_fn,
                            "driver-free Wi-Fi entry")

# Rebalance the real Gastly/Haunter/Gengar sprites. Keep the exact TamaPoke PMD
# artwork/animation, but render them 1.5x native size. Gastly and Haunter share
# the same baseline and mirrored spacing; Gengar is raised slightly from the
# bottom so it no longer sits too low.
sprite_fn = r'''static void ghostClockDrawOriginalSprites(uint32_t now) {
  ghostClockLoadOriginalSprites();

  if (ghostClockGastlyMon.loaded())
    ghostClockGastlyMon.draw(ui, PMD_IDLE, 30, 60, now, -2);
  if (ghostClockHaunterMon.loaded())
    ghostClockHaunterMon.draw(ui, PMD_IDLE, 210, 60, now, -2);
  if (ghostClockGengarMon.loaded())
    ghostClockGengarMon.draw(ui, PMD_IDLE, 120, 126, now, -2);
}'''
text = replace_cpp_function(text, "static void ghostClockDrawOriginalSprites(", sprite_fn,
                            "Ghost Clock sprite layout")

text = text.replace("// ULTIMATE_V090_SAVED_WIFI_FIX",
                    "// ULTIMATE_V090_SAVED_WIFI_FIX\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")

# Add a clock-only 3/2 native pixel scale mode to PmdStream. Existing scale
# modes remain byte-for-byte behaviorally unchanged: positive integer scales,
# auto scale, and -1 Home 4/3 auto boost all still work as before.
ptext = PMD.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
scale_old = '''  const int scaleNum = (forcedScale == -1) ? baseScale * 4 : baseScale;
  const int scaleDen = (forcedScale == -1) ? 3 : 1;'''
scale_new = '''  int scaleNum = baseScale;
  int scaleDen = 1;
  if (forcedScale == -1) {
    scaleNum = baseScale * 4;
    scaleDen = 3;
  } else if (forcedScale == -2) {
    // Ghost Clock: modest 1.5x enlargement of the exact native PMD pixels.
    scaleNum = 3;
    scaleDen = 2;
  }'''
if scale_old not in ptext:
    fail("PmdStream scale block")
ptext = ptext.replace(scale_old, scale_new, 1)
PMD.write_text(ptext, encoding="utf-8", newline="\n")

print("[v0.9.0-entry-clock-fix] Wi-Fi entry now makes zero driver calls; Ghost Clock sprites enlarged/rebalanced")
