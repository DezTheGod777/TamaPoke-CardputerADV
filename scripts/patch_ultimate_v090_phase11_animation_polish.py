Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE11_ANIMATION_POLISH"


def fail(msg):
    print(f"[v0.9.0-ultimate-p11] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p11] animation polish already applied")
    Return()
if "// ULTIMATE_V090_PHASE10_AUDIO_UPGRADE" not in text:
    fail("Phase 10 must run first")

helpers = r'''

// ULTIMATE_V090_PHASE11_ANIMATION_POLISH
static int ultimateRenderedScreen = -1;
static uint32_t ultimateTransitionStart = 0;
static uint32_t ultimateShinyEntranceUntil = 0;
static uint32_t ultimateRecoveryFxUntil = 0;
static uint32_t ultimateSleepWakeFxUntil = 0;
static bool ultimateSleepWakeToSleep = false;
static int16_t ultimateVisualLastSpecies = -1;
static bool ultimateVisualWasEgg = true;

static void initUltimateVisualState() {
  ultimateVisualWasEgg = pet.isEgg();
  ultimateVisualLastSpecies = pet.isEgg() ? -1 : pet.speciesId;
  ultimateRenderedScreen = (int)screen;
}

static void serviceUltimateVisualState(uint32_t now) {
  if (pet.isEgg()) {
    ultimateVisualWasEgg = true;
    ultimateVisualLastSpecies = -1;
    return;
  }
  if (ultimateVisualWasEgg || ultimateVisualLastSpecies != pet.speciesId) {
    if (pet.shiny) {
      ultimateShinyEntranceUntil = now + 2600;
      sfxPlay(SFX_SHINY);
    }
    ultimateVisualWasEgg = false;
    ultimateVisualLastSpecies = pet.speciesId;
  }
}

static void drawUltimateTransition(uint32_t now) {
  if (!ultimateTransitionStart) return;
  uint32_t elapsed = now - ultimateTransitionStart;
  if (elapsed >= 260) { ultimateTransitionStart = 0; return; }
  // Fast left-to-right reveal with a dithered trailing edge. It is intentionally
  // lightweight so the 240x135 Cardputer framebuffer stays smooth.
  int cover = (int)(240UL * (260 - elapsed) / 260UL);
  if (cover > 0) ui.fillRect(240 - cover, 0, cover, 135, UI_CREAM);
  int edge = 240 - cover;
  for (int y = 0; y < 135; y += 6) {
    int x = edge - ((y / 6) & 1 ? 4 : 1);
    if (x >= 0 && x < 240) ui.fillRect(x, y, 3, 3, UI_CREAM);
  }
}

static void drawUltimateEvolutionPolish(uint32_t now, float t) {
  int cx = 120, cy = 67;
  uint16_t col = (t > 0.70f) ? UI_WARN : UI_PINK;
  int spin = (int)(now / 70);
  for (int i = 0; i < 8; ++i) {
    float a = (float)(spin + i * 45) * 0.0174532925f;
    int r = 25 + (int)(t * 42) + (i & 1) * 5;
    int x = cx + (int)(cosf(a) * r);
    int y = cy + (int)(sinf(a) * r * 0.55f);
    ui.drawFastHLine(x - 2, y, 5, col);
    ui.drawFastVLine(x, y - 2, 5, col);
  }
  if (t > 0.86f) {
    int pulse = 7 + (int)(5 * sinf(now * 0.025f));
    ui.drawCircle(cx, cy, 44 + pulse, UI_WHITE);
    ui.drawCircle(cx, cy, 55 + pulse, UI_WARN);
  }
}

static void drawUltimateHomePolishFx(uint32_t now) {
  if (idleTerrarium || pet.isEgg()) return;
  if (ultimateShinyEntranceUntil > now) {
    uint32_t left = ultimateShinyEntranceUntil - now;
    int phase = (int)((2600 - left) / 90);
    for (int i = 0; i < 9; ++i) {
      float a = (float)(phase * 7 + i * 40) * 0.0174532925f;
      int r = 20 + ((phase + i * 5) % 28);
      int x = petX + (int)(cosf(a) * r);
      int y = 61 + (int)(sinf(a) * r * 0.60f);
      uint16_t c = (i & 1) ? UI_WARN : UI_WHITE;
      ui.drawFastHLine(x - 2, y, 5, c);
      ui.drawFastVLine(x, y - 2, 5, c);
    }
  }

  if (ultimateRecoveryFxUntil > now) {
    for (int i = 0; i < 5; ++i) {
      int x = petX - 30 + ((i * 17 + now / 22) % 60);
      int y = 70 - ((i * 19 + now / 17) % 34);
      ui.drawFastHLine(x - 2, y, 5, UI_OK);
      ui.drawFastVLine(x, y - 2, 5, UI_OK);
    }
  } else if (ultimateDetailedMood() == UDM_SICK) {
    uint16_t c = ((now / 260) & 1) ? UI_BAD : C565(0xa9,0x56,0x63);
    ui.drawLine(5, 31, 5, 75, c);
    ui.drawLine(234, 31, 234, 75, c);
    ui.drawLine(8, 34, 12, 30, c);
    ui.drawLine(231, 34, 227, 30, c);
  }

  if (ultimateSleepWakeFxUntil > now) {
    uint32_t left = ultimateSleepWakeFxUntil - now;
    int x = 25 + (int)((650 - std::min<uint32_t>(650, left)) * 190 / 650);
    int y = 32;
    if (ultimateSleepWakeToSleep) {
      ui.fillCircle(x, y, 8, UI_WARN);
      ui.fillCircle(x + 4, y - 3, 8, sceneNight() ? C565(0x14,0x1c,0x30) : C565(0x88,0xc8,0xee));
    } else {
      ui.fillCircle(x, y, 6, UI_WARN);
      ui.drawFastHLine(x - 10, y, 21, UI_WARN);
      ui.drawFastVLine(x, y - 10, 21, UI_WARN);
    }
  }
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text: fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Initialize and service visual state.
text = rep(text,
    "  initUltimateDexRuntime();",
    "  initUltimateDexRuntime();\n  initUltimateVisualState();",
    "visual init")
text = rep(text,
    "  serviceUltimateDexHistory();",
    "  serviceUltimateDexHistory();\n  serviceUltimateVisualState(now);",
    "visual loop service")

# Distinct sleep/wake sweep after the state toggles.
text = rep(text,
    "    pet.toggleLight();\n    sfxPlay(pet.sleeping ? SFX_SLEEP : SFX_WAKE);",
    "    pet.toggleLight();\n    ultimateSleepWakeToSleep = pet.sleeping;\n    ultimateSleepWakeFxUntil = millis() + 650;\n    sfxPlay(pet.sleeping ? SFX_SLEEP : SFX_WAKE);",
    "sleep/wake visual trigger")

# Medicine creates an obvious recovery sparkle instead of only changing numbers.
med_anchor = '    say("Feeling better!");'
if med_anchor not in text: fail("medicine recovery anchor")
text = text.replace(med_anchor,
    "    ultimateRecoveryFxUntil = millis() + 2200;\n" + med_anchor,
    1)

# Home polish FX sits above the Pokemon but below permanent HUD/menu elements.
home_anchor = "  drawUltimateDailyFx(now);"
if home_anchor not in text: fail("daily Home FX anchor")
text = text.replace(home_anchor,
    "  drawUltimateHomePolishFx(now);\n" + home_anchor,
    1)

# Add another visual layer to the existing evolution sequence.
evo_anchor = "  float t = pet.evolveT();"
if evo_anchor not in text: fail("evolution progress anchor")
text = text.replace(evo_anchor,
    evo_anchor + "\n  drawUltimateEvolutionPolish(now, t);",
    1)

# Detect screen changes at render time and reveal the destination with a quick
# lightweight wipe. Drawing the transition after the screen keeps every menu's
# existing layout untouched.
render_start = "static void render(uint32_t now) {\n  if (pet.awaitingStarter()) {"
if render_start not in text: fail("render start")
text = text.replace(render_start,
    "static void render(uint32_t now) {\n"
    "  if ((int)screen != ultimateRenderedScreen) {\n"
    "    ultimateRenderedScreen = (int)screen;\n"
    "    ultimateTransitionStart = now;\n"
    "  }\n"
    "  if (pet.awaitingStarter()) {",
    1)

push_anchor = "  // One complete RGB565 frame is pushed after all drawing is finished.\n  // The LCD never sees a black clear followed by partial drawing.\n  ui.pushSprite(0, 0);"
if push_anchor not in text: fail("render push anchor")
text = text.replace(push_anchor,
    "  drawUltimateTransition(now);\n\n" + push_anchor,
    1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p11] Added screen reveals, evolution sparkles, shiny entrance, recovery/damage and sleep/wake effects")
