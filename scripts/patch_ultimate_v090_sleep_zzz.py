Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_SLEEP_ZZZ_ANIM"


def fail(msg):
    print(f"[v0.9.0-sleep-zzz] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-sleep-zzz] animated sleep indicator already applied")
    Return()
if "// ULTIMATE_V090_EXACT_STABLE_CADENCE" not in text:
    fail("exact stable cadence patch must run first")

helpers = r'''

// ULTIMATE_V090_SLEEP_ZZZ_ANIM
static void drawSleepZzz(uint32_t now) {
  if (!pet.sleeping || pet.isEgg()) return;

  // Put the sleep trail beside the head, not straight above it. Normally it
  // rises up-and-right like a comic/manga sleep cue. If the Pokemon has walked
  // toward the right side of the habitat, mirror it up-and-left so it never
  // gets pinned against the screen edge.
  const int dir = petX > 142 ? -1 : 1;
  const int16_t groundY = ultimateHomeGroundY(now);
  const int baseX = petX + dir * 17;
  const int baseY = groundY - 48;
  const uint16_t zCol = sceneNight() ? UI_INK_NIGHT : UI_INK;

  // Three staggered letters continuously drift diagonally away from the head.
  // Each is at a different point in the same 1.8 s cycle, creating a natural
  // small-z -> medium-z -> large-Z comic trail rather than a vertical stack.
  for (int i = 0; i < 3; ++i) {
    uint32_t local = (now + (uint32_t)i * 600UL) % 1800UL;
    float t = local / 1800.0f;
    int x = baseX + dir * (i * 6 + (int)(t * 7.0f));
    int y = baseY - i * 7 - (int)(t * 7.0f);

    // Let the letter briefly disappear at the end of its travel before its
    // next staggered cycle starts; this avoids a mechanical-looking loop.
    if (t > 0.86f) continue;

    ui.setTextColor(zCol);
    ui.setTextSize(i == 2 ? 2 : 1);
    ui.drawString(i == 2 ? "Z" : "z", x, y);
  }
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text:
    fail("drawHome anchor missing")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

old = '''    if (pet.sleeping) {
      ui.setTextSize(2);
      ui.setTextColor(UI_INK_NIGHT);
      ui.drawString("Zz", 193, 33);
    }'''
new = '''    if (pet.sleeping) {
      drawSleepZzz(now);
    }'''
if old not in text:
    fail("static sleep Zz block not found")
text = text.replace(old, new, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-sleep-zzz] Replaced static corner Zz with a mirrored diagonal comic-style sleep trail near the Pokemon")
