Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PUBLIC_SPECIAL_BACKGROUNDS"


def fail(msg):
    print(f"[v0.9.0-special-bg] ERROR: {msg}")
    env.Exit(1)


def replace_cpp_function(text, signature, replacement, label):
    start = text.find(signature)
    if start < 0:
        fail(f"could not locate {label} start")
    brace = text.find("{", start)
    if brace < 0:
        fail(f"could not locate {label} opening brace")

    depth = 0
    i = brace
    in_str = False
    in_chr = False
    in_line = False
    in_block = False
    esc = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line:
            if ch == "\n": in_line = False
            i += 1
            continue
        if in_block:
            if ch == "*" and nxt == "/":
                in_block = False
                i += 2
            else:
                i += 1
            continue
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if in_chr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == "'":
                in_chr = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block = True
            i += 2
            continue
        if ch == '"':
            in_str = True
            i += 1
            continue
        if ch == "'":
            in_chr = True
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                return text[:start] + replacement.rstrip() + text[end:]
        i += 1

    fail(f"could not locate {label} closing brace")


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-special-bg] special backgrounds already applied")
    Return()
if "// ULTIMATE_V090_REMOVE_151_BORDER" not in text:
    fail("151 border removal must run first")

# STARFIELD and DREAM are no longer secret-gated. They are normal Background
# choices in H > Home Customize alongside Meadow/Beach/etc.
unlocks = r'''static bool ultimateHomeChoiceUnlocked(uint8_t row, uint8_t v) {
  if (v == 0) return true;
  // Every background is freely selectable, including Starfield and Dream.
  if (row == 0) return v <= 8;
  if (row == 1) {
    if (v == 1) return pet.gameHi >= 3;
    if (v == 2) return pet.gameHi >= 8;
    return pet.totalMedals >= 3;
  }
  if (row == 2) {
    if (v == 1) return pet.bond >= 15;
    if (v == 2) return pet.bond >= 40;
    return pet.bestStreak >= 7;
  }
  if (row == 3) {
    if (v == 1) return pet.gameHi >= 5;
    if (v == 2) return pet.strHi >= 10;
    return pet.registeredCount() >= 25;
  }
  if (row == 4) {
    if (v == 1) return pet.totalMedals >= 1;
    if (v == 2) return pet.totalMedals >= 4;
    return pet.totalMedals >= 8;
  }
  if (row == 5) {
    if (v == 1) return pet.registeredCount() >= 5;
    if (v == 2) return pet.bestStreak >= 3;
    return pet.bond >= 60;
  }
  return true;
}'''
text = replace_cpp_function(text, "static bool ultimateHomeChoiceUnlocked(", unlocks,
                            "Home background unlock logic")

# Retire the old Konami-style Starfield unlock entirely. Arrow presses still
# call this helper, but it intentionally does nothing now.
arrow = r'''static void ultimateSecretArrowCode(uint8_t code) {
  (void)code;
}'''
text = replace_cpp_function(text, "static void ultimateSecretArrowCode(", arrow,
                            "retired Starfield secret code")

# DREAM is also a regular background now. Keep the hidden word "mew" only as a
# one-time Mew visitor/reward easter egg; it no longer gates the Dream scenery.
secret_words = r'''static bool ultimateSecretPrintable(char c) {
  if (!isalnum((unsigned char)c)) return false;
  c = (char)tolower((unsigned char)c);
  if (ultimateSecretWordLen < sizeof(ultimateSecretWord) - 1) {
    ultimateSecretWord[ultimateSecretWordLen++] = c;
  } else {
    memmove(ultimateSecretWord, ultimateSecretWord + 1, sizeof(ultimateSecretWord) - 2);
    ultimateSecretWord[sizeof(ultimateSecretWord) - 2] = c;
    ultimateSecretWordLen = sizeof(ultimateSecretWord) - 1;
  }
  ultimateSecretWord[ultimateSecretWordLen] = 0;

  if (ultimateSecretWordEnds("mew")) {
    bool fresh = (ultimateSecretFlags & ULT_SECRET_DREAM) == 0;
    ultimateUnlockSecret(ULT_SECRET_DREAM, "MEW VISITOR", 2);
    if (fresh) {
      ultimateRareEncounterDex = 151;
      ultimateRareEncounterUntil = millis() + 8000;
      ultimateAwardCoins(50);
      if (ultimateItems[9] < 99) ultimateItems[9]++;
      saveUltimateEconomy();
    }
    screen = HOME; feedOpen = false; dirty = true;
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  if (ultimateSecretWordEnds("151")) {
    // Retired code. Consume it silently so the removed border cannot return.
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  if (ultimateSecretWordEnds("ultimate")) {
    bool fresh = (ultimateSecretFlags & ULT_SECRET_MYSTERY_GIFT) == 0;
    ultimateUnlockSecret(ULT_SECRET_MYSTERY_GIFT, "MYSTERY GIFT", 4);
    if (fresh) {
      uint8_t b = random(3);
      if (ultimateItems[b] < 99) ultimateItems[b]++;
      ultimateAwardCoins(75);
      saveUltimateEconomy();
    }
    screen = HOME; feedOpen = false; dirty = true;
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
    return true;
  }
  return false;
}'''
text = replace_cpp_function(text, "static bool ultimateSecretPrintable(", secret_words,
                            "updated secret words")

# Rebuild the special-background renderer. Starfield is now a normal selectable
# scene. Dream gets a full polish pass: layered dusk gradient, crescent moon,
# drifting clouds, mist, stars and soft twinkles instead of the old flat field
# of large circles. This is visual-only and does not change gameplay ambience.
fx = r'''static void drawUltimateSecretHomeFx(uint32_t now) {
  int topH = idleTerrarium ? 92 : 66;

  if (ultimateHomeBg == 7) {
    // STARFIELD - deep space with subtle purple nebula and multi-depth stars.
    const uint16_t spaceTop = C565(0x07,0x0a,0x1d);
    const uint16_t spaceBot = C565(0x1c,0x16,0x38);
    for (int y = 0; y < topH; y += 4)
      ui.fillRect(0, y, 240, 4, lerp565(spaceTop, spaceBot, y, std::max(1, topH - 1)));

    int nebula = (int)((now / 110UL) % 270UL) - 30;
    ui.fillCircle(nebula, 22, 22, C565(0x2b,0x1b,0x52));
    ui.fillCircle(nebula + 19, 28, 17, C565(0x3b,0x235,0x64));

    for (int i = 0; i < 30; ++i) {
      int x = (i * 47 + 13 + (i % 3 == 0 ? (now / 900UL) : 0)) % 240;
      int y = (i * 31 + 7) % std::max(1, topH - 3);
      bool bright = (((now / 360UL) + i) & 1UL) == 0;
      uint16_t c = bright ? UI_WHITE : C565(0x9e,0x91,0xc8);
      if (i % 7 == 0) {
        ui.drawFastHLine(x - 2, y, 5, c);
        ui.drawFastVLine(x, y - 2, 5, c);
      } else {
        ui.drawPixel(x, y, c);
      }
    }
  } else if (ultimateHomeBg == 8) {
    // DREAM - soft twilight dreamscape, deliberately cleaner and more detailed
    // than the original flat lavender/circle implementation.
    const uint16_t dreamTop = C565(0x3a,0x2a,0x62);
    const uint16_t dreamMid = C565(0x75,0x5a,0x9d);
    const uint16_t dreamLow = C565(0xc6,0xad,0xdd);
    for (int y = 0; y < topH; y += 3) {
      uint16_t c;
      if (y < topH / 2)
        c = lerp565(dreamTop, dreamMid, y, std::max(1, topH / 2));
      else
        c = lerp565(dreamMid, dreamLow, y - topH / 2, std::max(1, topH - topH / 2));
      ui.fillRect(0, y, 240, 3, c);
    }

    // Crescent moon.
    int moonY = idleTerrarium ? 22 : 18;
    ui.fillCircle(196, moonY, 11, C565(0xff,0xee,0xb6));
    ui.fillCircle(201, moonY - 3, 10, C565(0x53,0x3d,0x79));
    ui.fillCircle(190, moonY + 1, 1, C565(0xff,0xf9,0xd8));

    // Small twinkling stars; restrained so the pet remains the focus.
    for (int i = 0; i < 14; ++i) {
      int x = 9 + (i * 37) % 221;
      int y = 6 + (i * 19) % std::max(10, topH - 24);
      uint16_t sc = (((now / 480UL) + i) & 1UL) ? C565(0xff,0xe9,0xbc) : C565(0xe6,0xd8,0xf2);
      if (i % 5 == 0) {
        ui.drawFastHLine(x - 1, y, 3, sc);
        ui.drawFastVLine(x, y - 1, 3, sc);
      } else {
        ui.drawPixel(x, y, sc);
      }
    }

    // Two slow cloud groups moving at different speeds.
    int cloudA = (int)((now / 85UL) % 300UL) - 45;
    int cloudB = 255 - (int)((now / 130UL) % 315UL);
    auto dreamCloud = [&](int x, int y, uint16_t c) {
      ui.fillCircle(x, y, 8, c);
      ui.fillCircle(x + 9, y - 3, 10, c);
      ui.fillCircle(x + 20, y, 8, c);
      ui.fillRoundRect(x - 5, y, 31, 8, 4, c);
    };
    dreamCloud(cloudA, idleTerrarium ? 47 : 40, C565(0xec,0xe3,0xf4));
    dreamCloud(cloudB, idleTerrarium ? 66 : 52, C565(0xd8,0xc6,0xe8));

    // Soft mist bank along the habitat horizon.
    int horizon = topH - 7;
    ui.fillRect(0, horizon, 240, 7, C565(0xb9,0x9f,0xd1));
    for (int i = 0; i < 10; ++i) {
      int x = i * 27 - 8 + (int)((now / 210UL) % 14UL);
      ui.fillCircle(x, horizon, 8 + (i & 1) * 2, C565(0xd2,0xc0,0xe2));
    }
  }

  if ((ultimateSecretFlags & ULT_SECRET_ULTRA_SHINY) && pet.shiny && !pet.isEgg()) {
    static const uint16_t cols[4] = {UI_PINK, UI_WARN, UI_BLUE, UI_OK};
    int spin = (int)(now / 60);
    for (int i = 0; i < 12; ++i) {
      float a = (float)(spin + i * 30) * 0.0174532925f;
      int r = 28 + (i & 1) * 9;
      int x = petX + (int)(cosf(a) * r);
      int y = 60 + (int)(sinf(a) * r * 0.58f);
      uint16_t c = cols[(i + now / 180) & 3];
      ui.drawFastHLine(x - 2, y, 5, c);
      ui.drawFastVLine(x, y - 2, 5, c);
    }
  }

  if (ultimateSecretAnimUntil > now && !idleTerrarium) {
    int phase = (int)((4200 - (ultimateSecretAnimUntil - now)) / 90);
    uint16_t c = ultimateSecretAnimKind & 1 ? UI_WARN : UI_PINK;
    for (int i = 0; i < 10; ++i) {
      int x = 20 + (i * 31 + phase * 5) % 205;
      int y = 24 + (i * 19 + phase * 3) % 55;
      ui.drawFastHLine(x - 2, y, 5, c);
      ui.drawFastVLine(x, y - 2, 5, c);
    }
  }
}'''
# Correct one deliberately invalid typo before writing generated C++.
fx = fx.replace("C565(0x3b,0x235,0x64)", "C565(0x3b,0x23,0x64)")
text = replace_cpp_function(text, "static void drawUltimateSecretHomeFx(", fx,
                            "special background renderer")

# Marker for generated-source audit proof.
text = text.replace("// ULTIMATE_V090_REMOVE_151_BORDER",
                    "// ULTIMATE_V090_REMOVE_151_BORDER\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-special-bg] Starfield/Dream are normal selectable backgrounds; retired Starfield code; redesigned Dream")
