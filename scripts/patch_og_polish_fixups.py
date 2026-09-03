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

main.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4] Applied compile-time forward-declaration fixups")
