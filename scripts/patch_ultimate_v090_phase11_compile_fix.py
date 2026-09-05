Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE11_EARLY_DECL_FIX"


def fail(msg):
    print(f"[v0.9.0-ultimate-p11-fix] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p11-fix] early declaration already applied")
    Return()
if "// ULTIMATE_V090_PHASE11_ANIMATION_POLISH" not in text:
    fail("Phase 11 must run first")

# drawEvolution() appears before the later Ultimate helper implementation in
# the generated translation unit. Put a harmless forward declaration beside
# the base globals so C++ sees it before drawEvolution().
anchor = "static M5Canvas ui(&M5Cardputer.Display);\n"
if anchor not in text:
    fail("global UI anchor")
insert = (
    anchor
    + "\n// ULTIMATE_V090_PHASE11_EARLY_DECL_FIX\n"
    + "static void drawUltimateEvolutionPolish(uint32_t now, float t);\n"
)
text = text.replace(anchor, insert, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p11-fix] Added early evolution polish declaration")
