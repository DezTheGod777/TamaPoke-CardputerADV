Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_REMOVE_151_BORDER"


def fail(msg):
    print(f"[v0.9.0-no-151-border] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-no-151-border] 151 border removal already applied")
    Return()
if "// ULTIMATE_V090_GHOST_CLOCK" not in text:
    fail("Ghost Clock patch must run first")

# Retire the 151 Master Border completely. Existing users who already unlocked
# it should not need to reset their save: the persisted flag is cleared once at
# boot, and the visual renderer is removed.
load_anchor = "  loadUltimateSecrets();\n  displayLastActivity = millis();"
if load_anchor not in text:
    fail("secret config load anchor missing")
text = text.replace(
    load_anchor,
    "  loadUltimateSecrets();\n"
    "  if (ultimateSecretFlags & ULT_SECRET_MASTER151) {\n"
    "    ultimateSecretFlags &= (uint16_t)~ULT_SECRET_MASTER151;\n"
    "    saveUltimateSecrets();\n"
    "  }\n"
    "  displayLastActivity = millis();",
    1,
)

border_block = '''  if ((ultimateSecretFlags & ULT_SECRET_MASTER151) && !idleTerrarium) {
    uint16_t c = ((now / 300) & 1) ? UI_WARN : UI_PINK;
    ui.drawRoundRect(1, 1, 238, 133, 8, c);
    ui.drawRoundRect(3, 3, 234, 129, 7, UI_BLUE);
  }

'''
if border_block not in text:
    fail("151 Master Border renderer missing")
text = text.replace(border_block, "", 1)

# The second-audit secret handler returns bool so a completed code consumes its
# final key. Keep that behavior, but make 151 a retired/no-op code.
secret_branch = '''  if (ultimateSecretWordEnds("151")) {
    ultimateUnlockSecret(ULT_SECRET_MASTER151, "151 MASTER BORDER", 3);
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  if (ultimateSecretWordEnds("ultimate")) {'''
secret_replacement = '''  if (ultimateSecretWordEnds("151")) {
    // Retired secret: consume the old code silently so it cannot unlock or
    // display anything in current builds.
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  if (ultimateSecretWordEnds("ultimate")) {'''
if secret_branch not in text:
    fail("151 secret input branch missing")
text = text.replace(secret_branch, secret_replacement, 1)

# Marker in generated main.cpp for CI/hardware audit proof.
text = text.replace("// ULTIMATE_V090_GHOST_CLOCK",
                    "// ULTIMATE_V090_GHOST_CLOCK\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-no-151-border] Removed 151 Master Border, disabled its code, and clears old unlock state automatically")
