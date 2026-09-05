Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PLAY_ICON_CLEANUP"


def fail(msg):
    print(f"[v0.9.0-play-icon] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-play-icon] Play icon cleanup already applied")
    Return()
if "// ULTIMATE_V090_UI_PREFERENCES" not in text:
    fail("UI preferences patch must run first")

old = '''static void drawBallIcon(M5Canvas &g, int cx, int cy) {
  g.fillCircle(cx, cy, 7, UI_WHITE);
  g.fillRect(cx - 6, cy - 6, 13, 6, UI_BAD);
  g.drawFastHLine(cx - 7, cy, 15, UI_INK);
  g.fillCircle(cx, cy, 2, UI_WHITE);
  g.drawCircle(cx, cy, 2, UI_INK);
  g.drawCircle(cx, cy, 7, UI_INK);
}'''

new = '''static void drawBallIcon(M5Canvas &g, int cx, int cy) {
  // ULTIMATE_V090_PLAY_ICON_CLEANUP
  // Keep the original 15px Pokeball footprint, but clip the red top half to
  // the circular silhouette. The old rectangular fill leaked red pixels past
  // the black outline at the two upper corners.
  g.fillCircle(cx, cy, 7, UI_WHITE);

  // Pixel-shaped upper hemisphere, intentionally one pixel inside the outline.
  g.drawFastHLine(cx - 3, cy - 6, 7, UI_BAD);
  g.drawFastHLine(cx - 4, cy - 5, 9, UI_BAD);
  g.drawFastHLine(cx - 5, cy - 4, 11, UI_BAD);
  g.drawFastHLine(cx - 5, cy - 3, 11, UI_BAD);
  g.drawFastHLine(cx - 6, cy - 2, 13, UI_BAD);
  g.drawFastHLine(cx - 6, cy - 1, 13, UI_BAD);

  // Redraw all black structure last for crisp edges.
  g.drawCircle(cx, cy, 7, UI_INK);
  g.drawFastHLine(cx - 7, cy, 15, UI_INK);
  g.fillCircle(cx, cy, 2, UI_WHITE);
  g.drawCircle(cx, cy, 2, UI_INK);
}'''

if old not in text:
    fail("original Pokeball icon function")
text = text.replace(old, new, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-play-icon] Cleaned Pokeball upper corners and preserved original icon size/style")
