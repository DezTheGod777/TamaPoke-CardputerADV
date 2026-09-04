Import("env")
from pathlib import Path

main = Path(env.subst("$PROJECT_DIR")) / "src" / "main.cpp"
text = main.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

# Idle/terrarium mode should be presentation-only. Do not stamp an "IDLE"
# debug/status label over the world scene.
idle_block = '''  } else {
    ui.setTextSize(1);
    ui.setTextColor(sceneNight() ? UI_INK_NIGHT : UI_INK);
    ui.drawString("IDLE", 4, 124);
  }'''
if idle_block in text:
    text = text.replace(idle_block, "  }", 1)

# Keep the terrarium scene completely clean: the normal top-right battery HUD
# remains everywhere else, but disappears while idleTerrarium is active.
overlay_old = '''static void drawSystemOverlays(uint32_t now) {
  drawBatteryMeter();
  drawSaveIndicator(now);
}'''
overlay_new = '''static void drawSystemOverlays(uint32_t now) {
  if (!idleTerrarium) drawBatteryMeter();
  drawSaveIndicator(now);
}'''
if overlay_old in text:
    text = text.replace(overlay_old, overlay_new, 1)
elif overlay_new not in text:
    print("[v0.8.5.4-complete] ERROR: could not locate system overlay function")
    env.Exit(1)

# Keep STL calls explicit where template syntax is used.
text = text.replace("petX = min<int16_t>(petTargetX, petX + step);",
                    "petX = std::min<int16_t>(petTargetX, petX + step);")
text = text.replace("petX = max<int16_t>(petTargetX, petX - step);",
                    "petX = std::max<int16_t>(petTargetX, petX - step);")

# Make Arduino String numeric concatenation unambiguous across core versions.
text = text.replace('noteEvent(String("Level up: Lv.") + lv);',
                    'noteEvent(String("Level up: Lv.") + String(lv));')
text = text.replace('noteEvent(String("Pokedex unlocked: ") + reg + "/151");',
                    'noteEvent(String("Pokedex unlocked: ") + String(reg) + "/151");')
text = text.replace('noteEvent(String("Play record: ") + pet.gameHi);',
                    'noteEvent(String("Play record: ") + String(pet.gameHi));')
text = text.replace('noteEvent(String("Training record: ") + pet.strHi);',
                    'noteEvent(String("Training record: ") + String(pet.strHi));')
text = text.replace('noteEvent(String("Bond reached ") + m);',
                    'noteEvent(String("Bond reached ") + String(m));')

main.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4-complete] Removed idle label, hid idle battery HUD, and applied compile-safe fixups")
