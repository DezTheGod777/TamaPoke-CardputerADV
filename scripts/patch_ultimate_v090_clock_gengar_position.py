Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_CLOCK_GENGAR_POSITION"


def fail(msg):
    print(f"[v0.9.0-gengar-position] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-gengar-position] already applied")
    Return()
if "// ULTIMATE_V090_CLOCK_SPRITE_FIT" not in text:
    fail("clock sprite fit patch must run first")

old = "    ghostClockGengarMon.draw(ui, PMD_IDLE, 120, 123, now, -2);"
new = "    ghostClockGengarMon.draw(ui, PMD_IDLE, 120, 129, now, -2);"
if old not in text:
    fail("Gengar clock position anchor missing")
text = text.replace(old, new, 1)

text = text.replace("// ULTIMATE_V090_CLOCK_SPRITE_FIT",
                    "// ULTIMATE_V090_CLOCK_SPRITE_FIT\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-gengar-position] Moved Gengar 6 px lower to clear the date text")
