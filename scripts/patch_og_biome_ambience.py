Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// OG_BIOME_AMBIENCE_RC5"


def fail(msg):
    print(f"[v0.8.5.4-rc5] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.8.5.4-rc5] biome ambience already applied")
    Return()

# Add ONLY small animated overlays. The classic drawScene() base geometry,
# terrain, palette, sky, hills and biome layout remain untouched.
helper = r'''

// OG_BIOME_AMBIENCE_RC5
static void drawBiomeAmbientFx(uint8_t biome, uint32_t now, bool night, int bottomY) {
  if (biome > 5) return;
  const int horizon = (bottomY * 64) / 100;
  if (horizon < 20) return;

  // Meadow: a few tiny drifting pollen specks in daylight.
  if (biome == 0 && !night) {
    uint16_t pollen = C565(0xff, 0xe6, 0x88);
    for (int i = 0; i < 3; ++i) {
      int x = (int)((now / (95 + i * 17) + i * 79) % 250) - 5;
      int y = 24 + ((i * 19 + (int)(now / 260)) % std::max(1, horizon - 28));
      ui.fillRect(x, y, 1, 1, pollen);
    }
  }

  // Beach: small water glints only; shoreline/sea artwork is unchanged.
  else if (biome == 1) {
    uint16_t glint = night ? C565(0x7d,0x9f,0xbc) : C565(0xe3,0xf6,0xff);
    for (int i = 0; i < 2; ++i) {
      int x = 24 + (int)((now / (120 + i * 25) + i * 103) % 185);
      int y = horizon - 9 + i * 4;
      ui.drawFastHLine(x, y, 4, glint);
    }
  }

  // Forest: sparse drifting leaf pixels above the tree line.
  else if (biome == 2) {
    uint16_t leaf = night ? C565(0x4c,0x68,0x4e) : C565(0x6f,0x9a,0x55);
    for (int i = 0; i < 3; ++i) {
      int x = (int)((now / (105 + i * 29) + i * 71) % 252) - 6;
      int y = 22 + ((i * 21 + (int)(now / 310)) % std::max(1, horizon - 26));
      ui.fillRect(x, y, 2, 1, leaf);
    }
  }

  // Volcano: tiny embers rise from the lower scene without changing terrain.
  else if (biome == 3) {
    uint16_t emberA = C565(0xff,0x9b,0x3a);
    uint16_t emberB = C565(0xff,0x5f,0x3f);
    for (int i = 0; i < 4; ++i) {
      int x = 38 + ((i * 53 + (int)(now / 85)) % 166);
      int rise = (int)((now / (55 + i * 11) + i * 13) % 24);
      int y = bottomY - 7 - rise;
      if (y > horizon - 8) ui.fillRect(x, y, 1, 2, (i & 1) ? emberA : emberB);
    }
  }

  // Mountain: one very small distant bird silhouette.
  else if (biome == 4 && !night) {
    int x = (int)((now / 140) % 285) - 22;
    int y = 25 + (int)((now / 500) % 5);
    uint16_t bird = C565(0x3c,0x52,0x66);
    ui.drawLine(x, y + 1, x + 3, y, bird);
    ui.drawLine(x + 3, y, x + 6, y + 1, bird);
  }

  // Snow already falls in the classic daytime scene. Add only a few flakes
  // at night so the original daytime amount is not changed.
  else if (biome == 5 && night) {
    for (int i = 0; i < 5; ++i) {
      int x = (i * 47 + (int)(now / 55)) % 238;
      int y = (i * 29 + (int)(now / 38)) % std::max(1, horizon);
      ui.fillRect(x, y, 1, 1, UI_WHITE);
    }
  }
}
'''

sig = "static void drawScene(uint8_t biome, uint32_t now, bool night, int bottomY = 90) {"
if sig not in text:
    fail("could not locate classic drawScene")
text = text.replace(sig, helper + "\n" + sig, 1)

old_tail = '''  } else if (biome == 0) {
    for (int gx : {24, 65, 176, 217}) {
      ui.drawLine(gx, horizon + 8, gx - 2, horizon + 2, dk);
      ui.drawLine(gx, horizon + 8, gx + 2, horizon + 1, dk);
    }
  }
}'''
new_tail = '''  } else if (biome == 0) {
    for (int gx : {24, 65, 176, 217}) {
      ui.drawLine(gx, horizon + 8, gx - 2, horizon + 2, dk);
      ui.drawLine(gx, horizon + 8, gx + 2, horizon + 1, dk);
    }
  }

  // Additive-only ambience: never replaces the original TamaPoke scene.
  drawBiomeAmbientFx(biome, now, night, bottomY);
}'''
if old_tail not in text:
    fail("could not locate classic drawScene tail")
text = text.replace(old_tail, new_tail, 1)

# Update the unmistakable boot identifier for this test build. The full-polish
# pass currently writes FULL POLISH RC4, while older builds used POLISH RC4.
# Handle both forms so there is no ambiguity on the physical Cardputer.
text = text.replace("v0.8.5.4  FULL POLISH RC4", "v0.8.5.4  FULL POLISH RC5")
text = text.replace("v0.8.5.4  POLISH RC4", "v0.8.5.4  POLISH RC5")

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4-rc5] Added subtle biome ambience on top of untouched classic backgrounds")
