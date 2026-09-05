Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_GHOST_CLOCK_ORIGINAL_SPRITES"


def fail(msg):
    print(f"[v0.9.0-ghost-sprites] ERROR: {msg}")
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
    print("[v0.9.0-ghost-sprites] already applied")
    Return()
if "// ULTIMATE_V090_HARDWARE_FOLLOWUP_FIX" not in text:
    fail("hardware follow-up fix must run first")

# Replace the hand-drawn approximations with the exact PMD/TPK2 sprites already
# used by TamaPoke for these species: Gastly #092, Haunter #093, Gengar #094.
# Dedicated streams keep the three animations loaded while the clock is open,
# avoiding repeated SD opens on every frame.
start = text.find("static void ghostClockGastly(")
end = text.find("static void drawGhostClock(uint32_t now) {", start)
if start < 0 or end < 0:
    fail("old Ghost Clock character helpers")

sprite_helpers = r'''// Exact original Pokemon sprites used by the rest of TamaPoke.
static PmdStream ghostClockGastlyMon;
static PmdStream ghostClockHaunterMon;
static PmdStream ghostClockGengarMon;
static bool ghostClockSpritesAttempted = false;

static void ghostClockLoadOriginalSprites() {
  if (ghostClockSpritesAttempted) return;
  ghostClockSpritesAttempted = true;
  if (!sdReady) return;
  ghostClockGastlyMon.load(92, false);  // Gastly
  ghostClockHaunterMon.load(93, false); // Haunter
  ghostClockGengarMon.load(94, false);  // Gengar
}

static void ghostClockUnloadOriginalSprites() {
  ghostClockGastlyMon.unload();
  ghostClockHaunterMon.unload();
  ghostClockGengarMon.unload();
  ghostClockSpritesAttempted = false;
}

static void ghostClockDrawOriginalSprites(uint32_t now) {
  ghostClockLoadOriginalSprites();

  // 1x preserves the native PMD pixel-art proportions instead of inventing
  // simplified shapes. IDLE remains animated using the original frame timing.
  if (ghostClockGastlyMon.loaded())
    ghostClockGastlyMon.draw(ui, PMD_IDLE, 24, 55, now, 1);
  if (ghostClockHaunterMon.loaded())
    ghostClockHaunterMon.draw(ui, PMD_IDLE, 216, 55, now, 1);
  if (ghostClockGengarMon.loaded())
    ghostClockGengarMon.draw(ui, PMD_IDLE, 120, 134, now, 1);
}'''
text = text[:start] + sprite_helpers.rstrip() + "\n\n" + text[end:]

# Replace the three old custom-character draw calls with one original-sprite pass.
text = text.replace(
    "  ghostClockGastly(22, 29, now); ghostClockHaunter(217, 29, now);\n",
    "  ghostClockDrawOriginalSprites(now);\n",
    1,
)
text = text.replace("  ghostClockGengar(120, 114, now);\n", "", 1)

# Free their SD file handles/frame buffers when leaving the clock. This keeps
# the rest of TamaPoke's sprite streaming behavior unchanged.
old_exit = "  } else if (screen == CLOCK_CALENDAR) {\n    if (escEdge || backEdge || enterEdge || spaceEdge) { screen = HOME; dirty = true; }"
new_exit = "  } else if (screen == CLOCK_CALENDAR) {\n    if (escEdge || backEdge || enterEdge || spaceEdge) { ghostClockUnloadOriginalSprites(); screen = HOME; dirty = true; }"
if old_exit not in text:
    fail("clock exit handler")
text = text.replace(old_exit, new_exit, 1)

text = text.replace("// ULTIMATE_V090_HARDWARE_FOLLOWUP_FIX",
                    "// ULTIMATE_V090_HARDWARE_FOLLOWUP_FIX\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ghost-sprites] Replaced custom Ghost Clock drawings with original Gastly/Haunter/Gengar PMD sprites")
