Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// OG_HOME_HUD_ICON_FIX"


def fail(msg):
    print(f"[v0.8.5.4-hud] ERROR: {msg}")
    env.Exit(1)


def replace_function(text, start_sig, next_sig, body, label):
    start = text.find(start_sig)
    if start < 0:
        fail(f"could not locate {label} start")
    end = text.find(next_sig, start)
    if end < 0:
        fail(f"could not locate {label} end")
    return text[:start] + body.rstrip() + "\n\n" + text[end:]


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.8.5.4-hud] Home HUD icon fix already applied")
    Return()

# The global battery HUD uses a small cream backing plate so it remains clean
# on normal cream menu screens. On Home that plate sits over the blue habitat
# sky and looks like a second box around the battery. Keep the backing plate on
# every other screen, but draw the battery directly on the habitat on Home.
new_battery_meter = r'''static void drawBatteryMeter() {
  sampleBattery();
  const int x = 216, y = 3;
  uint16_t outline = sceneNight() ? UI_INK_NIGHT : UI_INK;
  uint16_t fill = UI_OK;
  if (batteryLevel >= 0 && batteryLevel <= 15) fill = UI_BAD;
  else if (batteryLevel >= 0 && batteryLevel <= 35) fill = UI_WARN;

  const bool homeHabitat = (screen == HOME && !idleTerrarium);
  if (!homeHabitat) {
    ui.fillRoundRect(x - 1, y - 1, 21, 11, 3,
                     sceneNight() ? C565(0x14,0x1c,0x30) : UI_CREAM);
  }

  ui.drawRoundRect(x, y, 17, 8, 2, outline);
  ui.fillRect(x + 17, y + 2, 2, 4, outline);
  if (batteryLevel >= 0) {
    int fw = (13 * batteryLevel + 50) / 100;
    if (fw > 0) ui.fillRect(x + 2, y + 2, fw, 4, fill);
    if (batteryLevel <= 15 && !homeHabitat) {
      ui.setTextSize(1);
      ui.setTextColor(UI_BAD);
      ui.drawString("!", x - 7, y);
    }
  } else {
    ui.drawLine(x + 4, y + 2, x + 12, y + 5, outline);
  }
}'''
text = replace_function(
    text,
    "static void drawBatteryMeter() {",
    "static void drawSaveIndicator(uint32_t now) {",
    new_battery_meter,
    "battery meter",
)

# The old LIGHT icon made a crescent by painting a second bg-colored circle on
# top of a yellow circle. On the white Home button that mask reads as a loose
# white circle covering the icon. Replace it with a tiny light-bulb glyph that
# needs no masking and remains legible in both day and night themes.
new_light_icon = r'''static void drawMoonIcon(M5Canvas &g, int cx, int cy, uint16_t bg) {
  (void)bg;
  uint16_t outline = sceneNight() ? UI_INK_NIGHT : UI_INK;

  g.fillCircle(cx, cy - 2, 5, UI_WARN);
  g.drawCircle(cx, cy - 2, 5, outline);
  g.drawLine(cx - 2, cy + 2, cx - 2, cy + 5, outline);
  g.drawLine(cx + 2, cy + 2, cx + 2, cy + 5, outline);
  g.drawFastHLine(cx - 2, cy + 5, 5, outline);
  g.drawFastHLine(cx - 1, cy + 7, 3, outline);

  g.drawFastVLine(cx, cy - 10, 2, UI_WARN);
  g.drawLine(cx - 8, cy - 6, cx - 6, cy - 5, UI_WARN);
  g.drawLine(cx + 8, cy - 6, cx + 6, cy - 5, UI_WARN);
}'''
text = replace_function(
    text,
    "static void drawMoonIcon(M5Canvas &g, int cx, int cy, uint16_t bg) {",
    "static void drawBathIcon(M5Canvas &g, int cx, int cy) {",
    new_light_icon,
    "LIGHT icon",
)

# Marker is inserted after all replacements so a successful build can prove
# this final Home-HUD pass ran after the stable v0.8.5.4 polish chain.
anchor = "static constexpr const char *FIRMWARE_NAME = \"TamaPoke ADV\";"
if anchor not in text:
    fail("firmware marker anchor")
text = text.replace(anchor, anchor + "\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4-hud] Clean Home battery + LIGHT icon applied")
