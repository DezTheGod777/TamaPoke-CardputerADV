Import("env")
from pathlib import Path

main = Path(env.subst("$PROJECT_DIR")) / "src" / "main.cpp"
text = main.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

# say() is forward-declared because display recovery helpers call it before the
# definition. Keep the default argument on the declaration so all one-argument
# calls throughout the existing UI remain valid.
text = text.replace(
    "static void say(const String &s, uint32_t ms);",
    "static void say(const String &s, uint32_t ms = 1800);",
    1,
)

# Battery/system-overlay helpers are inserted before sceneNight() is defined.
# C++ therefore needs a forward declaration.
needle = "static void sampleBattery(bool force = false) {"
if needle in text and "static bool sceneNight();\n\nstatic void sampleBattery" not in text:
    text = text.replace(needle, "static bool sceneNight();\n\n" + needle, 1)

# Make hardware testing unambiguous. If this exact build is installed, this
# splash appears before TamaPoke starts so stale BINs cannot be confused with
# the current release candidate.
boot_needle = '''  ui.fillScreen(BLACK);\n  ui.pushSprite(0, 0);\n\n  randomSeed((uint32_t)micros());'''
boot_repl = '''  ui.fillScreen(C565(0x13, 0x0d, 0x27));\n  ui.setTextColor(UI_WHITE);\n  ui.setTextSize(2);\n  ui.drawCentreString("TAMAPOKE ADV", 120, 31, 1);\n  ui.setTextSize(1);\n  ui.setTextColor(UI_WARN);\n  ui.drawCentreString("v0.8.5.4  FULL POLISH RC4", 120, 62, 1);\n  ui.setTextColor(UI_PINK);\n  ui.drawCentreString("OG FIRMWARE TEST BUILD", 120, 80, 1);\n  ui.setTextColor(UI_WHITE);\n  ui.drawCentreString("G0 TOGGLE + CLEAN TERRARIUM", 120, 99, 1);\n  ui.pushSprite(0, 0);\n  delay(1400);\n\n  randomSeed((uint32_t)micros());'''
if "FULL POLISH RC4" not in text:
    if boot_needle not in text:
        print("[v0.8.5.4] ERROR: could not locate setup boot canvas block")
        env.Exit(1)
    text = text.replace(boot_needle, boot_repl, 1)

main.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4] Applied compile-time fixups + RC4 boot identifier")
