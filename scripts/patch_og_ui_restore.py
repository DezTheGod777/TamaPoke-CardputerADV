Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// OG_UI_RESTORE_RC4"


def fail(msg):
    print(f"[v0.8.5.4-rc4] ERROR: {msg}")
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
    print("[v0.8.5.4-rc4] classic UI restoration already applied")
    Return()

# Keep the new functionality, but restore the exact pre-polish habitat renderer
# so the normal TamaPoke backgrounds look the way they did before RC3.
classic_scene = r'''static void drawScene(uint8_t biome, uint32_t now, bool night, int bottomY = 90) {
  if (biome > 5) biome = 0;
  int h = sceneHour();
  uint16_t top, bot;

  if (night) {
    top = C565(0x0c, 0x12, 0x24);
    bot = C565(0x1e, 0x26, 0x46);
  } else if (h < 8) {
    top = C565(0xd1, 0x6a, 0x86);
    bot = C565(0xf3, 0xb8, 0x7c);
  } else if (h < 18) {
    top = C565(0x8f, 0xc8, 0xea);
    bot = C565(0xdc, 0xee, 0xe6);
  } else {
    top = C565(0xc7, 0x5a, 0x4a);
    bot = C565(0xf0, 0xae, 0x64);
  }

  const int horizon = (bottomY * 64) / 100;
  for (int y = 0; y < horizon; y += 4) {
    ui.fillRect(0, y, 240, 4, lerp565(top, bot, y, horizon));
  }

  if (night) {
    ui.fillCircle(208, 18, 10, C565(0xe8, 0xee, 0xf5));
    ui.fillCircle(212, 15, 9, lerp565(top, bot, 18, horizon));
    const int stars[][2] = {{18,17},{40,31},{70,13},{153,20},{181,37},{226,31}};
    for (auto &st : stars) ui.fillRect(st[0], st[1], 2, 2, UI_WHITE);
  } else if (h < 18) {
    ui.fillCircle(206, 22, 11, h < 8 ? C565(0xff,0xd9,0x8a) : C565(0xff,0xe7,0x9f));
    int drift = (now / 90) % 300;
    drawCloud((int)drift - 30, 30, UI_WHITE);
    drawCloud((int)((drift + 145) % 300) - 30, 42, UI_WHITE);
  } else {
    ui.fillCircle(120, horizon - 3, 14, C565(0xff,0xf1,0xc8));
  }

  uint16_t soil = BIOME_SOIL[biome];
  if (night) soil = lerp565(soil, C565(0x16,0x1c,0x30), 9, 16);

  if (biome == 1) {
    uint16_t sea = night ? C565(0x1c,0x34,0x52) : C565(0x4f,0x96,0xc4);
    ui.fillRect(0, horizon - 10, 240, 10, sea);
    for (int i = 0; i < 3; ++i) {
      int wx = 18 + ((now / 80 + i * 71) % 190);
      ui.drawFastHLine(wx, horizon - 8 + i * 3, 18,
                       night ? C565(0x3a,0x58,0x78) : C565(0xbf,0xe6,0xf5));
    }
  }

  ui.fillRect(0, horizon, 240, bottomY - horizon, soil);
  uint16_t hill = lerp565(soil, night ? top : UI_WHITE, 3, 16);
  ui.fillRoundRect(-20, horizon - 5, 280, 23, 12, hill);

  uint16_t dk = lerp565(soil, C565(0x10,0x18,0x20), night ? 11 : 7, 16);
  if (biome == 2) {
    for (int tx : {24, 54, 190, 220}) {
      ui.fillTriangle(tx, horizon - 22, tx - 8, horizon, tx + 8, horizon, dk);
      ui.fillTriangle(tx, horizon - 30, tx - 6, horizon - 13, tx + 6, horizon - 13, dk);
    }
  } else if (biome == 3) {
    ui.fillTriangle(37, horizon, 18, horizon + 14, 56, horizon + 14, dk);
    ui.fillTriangle(205, horizon, 185, horizon + 15, 225, horizon + 15, dk);
    if (!night) {
      for (int i = 0; i < 4; ++i)
        ui.fillRect(68 + i * 38, horizon + 6 + (i & 1) * 4, 2, 2, C565(0xff,0x9b,0x3a));
    }
  } else if (biome == 4) {
    ui.fillTriangle(72, horizon, 35, horizon, 82, horizon - 28, dk);
    ui.fillTriangle(177, horizon, 135, horizon, 178, horizon - 22, dk);
    if (!night) {
      ui.fillTriangle(72, horizon - 20, 82, horizon - 28, 90, horizon - 19, UI_WHITE);
      ui.fillTriangle(168, horizon - 17, 178, horizon - 22, 187, horizon - 16, UI_WHITE);
    }
  } else if (biome == 5 && !night) {
    for (int i = 0; i < 9; ++i) {
      int fx = (i * 37 + now / 45) % 238;
      int fy = (i * 23 + now / 25) % std::max(1, horizon);
      ui.fillRect(fx, fy, 2, 2, UI_WHITE);
    }
  } else if (biome == 0) {
    for (int gx : {24, 65, 176, 217}) {
      ui.drawLine(gx, horizon + 8, gx - 2, horizon + 2, dk);
      ui.drawLine(gx, horizon + 8, gx + 2, horizon + 1, dk);
    }
  }
}'''
text = replace_function(
    text,
    "static void drawScene(uint8_t biome, uint32_t now, bool night, int bottomY = 90) {",
    "static void ensureSprite",
    classic_scene,
    "classic drawScene",
)

# Restore the original graphical need meters. Do not replace them with raw
# numeric FOOD 82 / JOY 92 style boxes. Age/weight/bond remain available on
# the pet information/card screens.
classic_home_panel = r'''static void drawHomePanel() {
  bool night = sceneNight();
  uint16_t panel = night ? C565(0x18,0x20,0x34) : UI_CREAM;
  ui.fillRect(0, 90, 240, 45, panel);
  ui.drawFastHLine(0, 90, 240, night ? C565(0x4b,0x58,0x73) : UI_TRACK);

  drawNeedBar(5,   94, "FOOD", pet.fullness);
  drawNeedBar(123, 94, "JOY",  pet.joy);
  drawNeedBar(5,  104, "ENE",  pet.energy);
  drawNeedBar(123,104, "HYG",  pet.hygiene);

  const int xs[4] = {2, 62, 122, 182};
  const char *labs[4] = {"FEED", "PLAY", "LIGHT", "BATH"};
  for (int i = 0; i < 4; ++i) {
    bool disabled = pet.sleeping && i != 2;
    uint16_t box = night ? C565(0x20,0x2b,0x42) : UI_WHITE;
    uint16_t border = (i == homeSel) ? UI_WARN : (night ? UI_INK_NIGHT : UI_INK);
    if (disabled) border = UI_TRACK;

    ui.fillRoundRect(xs[i], 114, 56, 19, 5, box);
    ui.drawRoundRect(xs[i], 114, 56, 19, 5, border);
    if (i == homeSel) ui.drawRoundRect(xs[i] + 1, 115, 54, 17, 4, border);

    int cx = xs[i] + 12, cy = 123;
    if (i == 0) drawBerryIcon(ui, cx, cy);
    else if (i == 1) drawBallIcon(ui, cx, cy);
    else if (i == 2) drawMoonIcon(ui, cx, cy, box);
    else drawBathIcon(ui, cx, cy);

    ui.setTextSize(1);
    ui.setTextColor(disabled ? UI_TRACK : (night ? UI_INK_NIGHT : UI_INK));
    ui.drawString(labs[i], xs[i] + 23, 120);
  }
}'''
text = replace_function(
    text,
    "static void drawHomePanel() {",
    "static void drawToast",
    classic_home_panel,
    "classic drawHomePanel",
)

# Idle mode is intended to be a clean terrarium view. Apply a hard guard here
# as well as the earlier fixup so neither battery nor SAVE overlays can leak
# into an idle frame.
overlay = r'''static void drawSystemOverlays(uint32_t now) {
  if (screen == HOME && idleTerrarium) return;
  drawBatteryMeter();
  drawSaveIndicator(now);
}'''
text = replace_function(
    text,
    "static void drawSystemOverlays(uint32_t now) {",
    "static void resetDisplaySettings",
    overlay,
    "idle overlay guard",
)

# Make the test build identifier unmistakable.
text = text.replace("v0.8.5.4  POLISH RC2", "v0.8.5.4  POLISH RC4")
text = text.replace("v0.8.5.4  POLISH RC3", "v0.8.5.4  POLISH RC4")

# Marker proves this final corrective pass ran after all earlier polish passes.
text = text.replace("static constexpr const char *FIRMWARE_NAME = \"TamaPoke ADV\";",
                    "static constexpr const char *FIRMWARE_NAME = \"TamaPoke ADV\";\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4-rc4] Restored classic backgrounds + graphical need bars; idle overlays fully hidden")
