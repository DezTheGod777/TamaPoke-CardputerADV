Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
PMD = PROJECT / "src" / "pmd_stream.cpp"
MARKER = "// ULTIMATE_V090_CLOCK_SPRITE_FIT"


def fail(msg):
    print(f"[v0.9.0-clock-fit] ERROR: {msg}")
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
    print("[v0.9.0-clock-fit] already applied")
    Return()
if "// ULTIMATE_V090_WIFI_INPUT_RESTORE" not in text:
    fail("Wi-Fi input restore must run first")

# Hardware polish: the 1.5x sprites were a little too large and the center time
# panel visually covered the side characters. Keep the exact original PMD art,
# reduce the special clock scale to 1.25x, move Gastly/Haunter symmetrically
# toward the edges, and keep Gengar slightly raised.
sprite_fn = r'''static void ghostClockDrawOriginalSprites(uint32_t now) {
  ghostClockLoadOriginalSprites();

  if (ghostClockGastlyMon.loaded())
    ghostClockGastlyMon.draw(ui, PMD_IDLE, 27, 56, now, -2);
  if (ghostClockHaunterMon.loaded())
    ghostClockHaunterMon.draw(ui, PMD_IDLE, 213, 56, now, -2);
  if (ghostClockGengarMon.loaded())
    ghostClockGengarMon.draw(ui, PMD_IDLE, 120, 123, now, -2);
}'''
text = replace_cpp_function(text, "static void ghostClockDrawOriginalSprites(", sprite_fn,
                            "Ghost Clock sprite placement")

# Narrow the clock face just enough to stop it from sitting over Gastly/Haunter.
# Time remains centered and fully readable in 12-hour format with seconds.
repls = {
    "    ui.fillRoundRect(42, 27, 156, 44, 9, C565(0xf6,0xec,0xfa));":
    "    ui.fillRoundRect(50, 27, 140, 44, 9, C565(0xf6,0xec,0xfa));",
    "    ui.drawRoundRect(42, 27, 156, 44, 9, purple);":
    "    ui.drawRoundRect(50, 27, 140, 44, 9, purple);",
    "    ui.drawRoundRect(44, 29, 152, 40, 8, C565(0xc7,0xa8,0xdf));":
    "    ui.drawRoundRect(52, 29, 136, 40, 8, C565(0xc7,0xa8,0xdf));",
}
for old, new in repls.items():
    if old not in text:
        fail(f"clock panel anchor missing: {old}")
    text = text.replace(old, new, 1)

text = text.replace("// ULTIMATE_V090_WIFI_INPUT_RESTORE",
                    "// ULTIMATE_V090_WIFI_INPUT_RESTORE\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")

ptext = PMD.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
old_scale = '''  } else if (forcedScale == -2) {
    // Ghost Clock: modest 1.5x enlargement of the exact native PMD pixels.
    scaleNum = 3;
    scaleDen = 2;
  }'''
new_scale = '''  } else if (forcedScale == -2) {
    // Ghost Clock: subtle 1.25x enlargement of the exact native PMD pixels.
    scaleNum = 5;
    scaleDen = 4;
  }'''
if old_scale not in ptext:
    fail("Ghost Clock 1.5x scale block missing")
ptext = ptext.replace(old_scale, new_scale, 1)
PMD.write_text(ptext, encoding="utf-8", newline="\n")

print("[v0.9.0-clock-fit] Reduced/rebalanced original sprites and narrowed time panel")
