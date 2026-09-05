Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_UI_PREFERENCES"


def fail(msg):
    print(f"[v0.9.0-ui-pref] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ui-pref] user UI preferences already applied")
    Return()
if "// ULTIMATE_V090_VISIBLE_HUB" not in text:
    fail("visible Hub patch must run first")

# User preference: restore the original instant screen changes. Keep the other
# Phase 11 effects (evolution, shiny, recovery, sleep/wake) but remove only the
# menu/screen wipe transition.
text = rep(
    text,
    "static void render(uint32_t now) {\n"
    "  if ((int)screen != ultimateRenderedScreen) {\n"
    "    ultimateRenderedScreen = (int)screen;\n"
    "    ultimateTransitionStart = now;\n"
    "  }\n"
    "  if (pet.awaitingStarter()) {",
    "static void render(uint32_t now) {\n"
    "  if (pet.awaitingStarter()) {",
    "screen transition trigger",
)

text = rep(
    text,
    "  drawUltimateTransition(now);\n\n"
    "  // One complete RGB565 frame is pushed after all drawing is finished.",
    "  // One complete RGB565 frame is pushed after all drawing is finished.",
    "screen transition draw call",
)

# Final hardening made static screens animate while the wipe was active. With
# the wipe removed, restore the original scheduler behavior too.
text = rep(
    text,
    "static bool screenAnimated() {\n  if (ultimateTransitionStart) return true;\n",
    "static bool screenAnimated() {\n",
    "transition scheduler override",
)

# User preference: do not draw an H HUB badge on the Home screen. The H
# keyboard shortcut remains active, and the centralized Ultimate Hub itself is
# unchanged.
text = rep(
    text,
    "  drawUltimateDailyFx(now);\n  drawUltimateHubBadge();\n  drawBathFx(now);",
    "  drawUltimateDailyFx(now);\n  drawBathFx(now);",
    "Home Hub badge",
)

# Leave an explicit build marker for CI/source inspection.
name_anchor = 'static constexpr const char *FIRMWARE_NAME = "TamaPoke Ultimate";'
text = rep(text, name_anchor, name_anchor + "\n" + MARKER, "UI preference marker")

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ui-pref] Restored instant screen changes and removed Home H HUB badge; H shortcut remains")
