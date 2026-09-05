Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// V090_PUBLIC_RELEASE_BRANDING"


def fail(msg):
    print(f"[v0.9.0-release] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-release] public branding already applied")
    Return()
if "// ULTIMATE_V090_WIFI_PERSISTENCE_BOND_AUDIT" not in text:
    fail("final hardware audit must run first")

# Public v0.9.0 branding. Development script/function names intentionally stay
# unchanged so the tested patch chain remains stable; only user-visible release
# strings are normalized here.
required = {
    'static constexpr const char *FIRMWARE_VERSION = "v0.9.0 ULTIMATE";':
        'static constexpr const char *FIRMWARE_VERSION = "v0.9.0";',
    'static constexpr const char *FIRMWARE_NAME = "TamaPoke Ultimate";':
        'static constexpr const char *FIRMWARE_NAME = "TamaPoke Cardputer ADV";',
    'ui.drawCentreString("ULTIMATE HUB", 120, 3, 1);':
        'ui.drawCentreString("TAMAPOKE HUB", 120, 3, 1);',
}
for old, new in required.items():
    if old not in text:
        fail(f"release branding anchor missing: {old}")
    text = text.replace(old, new, 1)

# Optional help/control wording that may survive earlier UI cleanup patches.
text = text.replace('"H: Ultimate Hub   M: games"', '"H: TamaPoke Hub   M: games"')
text = text.replace('"H: ULTIMATE HUB   M: games"', '"H: TAMAPOKE HUB   M: games"')

# Do not alter the hidden printable word "ultimate". It remains an intentional
# Mystery Gift easter egg, not public firmware branding.
text = text.replace("// ULTIMATE_V090_WIFI_PERSISTENCE_BOND_AUDIT",
                    "// ULTIMATE_V090_WIFI_PERSISTENCE_BOND_AUDIT\n" + MARKER, 1)
MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-release] Public firmware branding set to TamaPoke Cardputer ADV v0.9.0")
