Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_POOP_POLISH"


def fail(msg):
    print(f"[v0.9.0-poop] ERROR: {msg}")
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
    print("[v0.9.0-poop] poop polish already applied")
    Return()

if "static void drawPoops() {" not in text:
    fail("drawPoops function")

new_poops = r'''// ULTIMATE_V090_POOP_POLISH
// Larger, clean Tamagotchi-inspired swirl with no face/pink. The upper tiers
// get a tiny idle sway, and an occasional soft stink puff keeps it alive without
// making the Home screen busy.
static void drawPoopIcon(int cx, int baseY, uint32_t now, uint8_t index) {
  const uint16_t outline = sceneNight() ? UI_INK_NIGHT : UI_INK;
  const uint16_t dark = C565(0x78,0x45,0x27);
  const uint16_t mid  = C565(0x9a,0x5b,0x31);
  const uint16_t light = C565(0xbd,0x78,0x3f);
  const uint16_t hi = C565(0xd7,0x99,0x58);

  // One-pixel upper-body sway every few beats; the base stays planted.
  uint32_t beat = (now / 420UL + index * 2UL) % 8UL;
  int sway = beat == 2UL ? -1 : (beat == 5UL ? 1 : 0);

  // Dark pixel-art silhouette, deliberately a little larger than the old icon.
  ui.fillRoundRect(cx - 9, baseY - 6, 19, 7, 3, outline);
  ui.fillRoundRect(cx - 7 + sway, baseY - 12, 15, 8, 3, outline);
  ui.fillRoundRect(cx - 5 + sway, baseY - 17, 11, 7, 3, outline);
  ui.fillTriangle(cx - 2 + sway, baseY - 20,
                  cx + 5 + sway, baseY - 16,
                  cx - 4 + sway, baseY - 16, outline);

  // Brown inner swirl. No eyes, mouth, cheeks, or pink accents.
  ui.fillRoundRect(cx - 7, baseY - 5, 15, 5, 2, dark);
  ui.fillRoundRect(cx - 5 + sway, baseY - 11, 11, 6, 2, mid);
  ui.fillRoundRect(cx - 3 + sway, baseY - 16, 7, 5, 2, light);
  ui.fillTriangle(cx - 1 + sway, baseY - 18,
                  cx + 3 + sway, baseY - 15,
                  cx - 2 + sway, baseY - 15, light);

  // Tiny highlights give the swirl some depth at Cardputer resolution.
  ui.fillRect(cx - 4 + sway, baseY - 14, 2, 2, hi);
  ui.fillRect(cx - 6, baseY - 4, 3, 1, mid);

  // Occasional manga/cartoon stink puff. Each pile is phase-shifted so three
  // poops do not puff in perfect sync.
  uint32_t puff = (now / 500UL + index * 5UL) % 18UL;
  if (puff >= 13UL && puff <= 16UL) {
    int px = cx + 8;
    int py = baseY - 19 - (int)(puff - 13UL) * 2;
    uint16_t smoke = sceneNight() ? C565(0x8b,0x91,0x96) : C565(0xa9,0xa0,0x82);
    if (puff == 13UL) {
      ui.drawCircle(px, py, 2, smoke);
    } else if (puff == 14UL) {
      ui.drawCircle(px + 2, py, 3, smoke);
      ui.fillCircle(px - 2, py + 2, 1, smoke);
    } else if (puff == 15UL) {
      ui.drawCircle(px + 4, py - 1, 3, smoke);
      ui.drawCircle(px, py + 3, 2, smoke);
    } else {
      ui.drawCircle(px + 5, py - 2, 2, smoke);
      ui.fillCircle(px + 1, py + 2, 1, smoke);
    }
  }
}

static void drawPoops(uint32_t now) {
  for (int i = 0; i < pet.poops && i < 3; ++i) {
    // 21 px spacing keeps the larger 19 px silhouette separated cleanly.
    drawPoopIcon(13 + i * 22, 86, now, (uint8_t)i);
  }
}'''

text = replace_function(text,
                        "static void drawPoops() {",
                        "static void drawNeedBar",
                        new_poops,
                        "drawPoops")

if "    drawPoops();" not in text:
    fail("drawPoops call")
text = text.replace("    drawPoops();", "    drawPoops(now);", 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-poop] Added larger faceless Tamagotchi-style poop swirl with subtle wobble and occasional stink puff")
