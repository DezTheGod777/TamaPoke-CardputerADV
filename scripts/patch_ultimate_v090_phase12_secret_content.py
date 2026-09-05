Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE12_SECRET_CONTENT"


def fail(msg):
    print(f"[v0.9.0-ultimate-p12] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p12] secret content already applied")
    Return()
if "// ULTIMATE_V090_PHASE11_ANIMATION_POLISH" not in text:
    fail("Phase 11 must run first")

# Secret flags must be declared before Phase 4's background-unlock helpers.
early_anchor = "// ULTIMATE_V090_PHASE4_HOME_CUSTOMIZATION"
if early_anchor not in text: fail("Phase 4 marker")
early = r'''// ULTIMATE_V090_PHASE12_SECRET_CONTENT
static uint16_t ultimateSecretFlags = 0;
static constexpr uint16_t ULT_SECRET_STARFIELD = 1 << 0;
static constexpr uint16_t ULT_SECRET_DREAM = 1 << 1;
static constexpr uint16_t ULT_SECRET_MASTER151 = 1 << 2;
static constexpr uint16_t ULT_SECRET_ULTRA_SHINY = 1 << 3;
static constexpr uint16_t ULT_SECRET_MYSTERY_GIFT = 1 << 4;

'''
text = text.replace(early_anchor, early + early_anchor, 1)

# Extend Home customization with two genuinely secret backgrounds.
text = rep(text, "  if (c.bg <= 6) ultimateHomeBg = c.bg;",
                 "  if (c.bg <= 8) ultimateHomeBg = c.bg;", "secret background config range")
text = rep(text, "  if (row == 0) return v <= 6;",
                 "  if (row == 0) {\n"
                 "    if (v <= 6) return true;\n"
                 "    if (v == 7) return (ultimateSecretFlags & ULT_SECRET_STARFIELD) != 0;\n"
                 "    if (v == 8) return (ultimateSecretFlags & ULT_SECRET_DREAM) != 0;\n"
                 "    return false;\n"
                 "  }", "secret background unlock logic")
text = rep(text, "  return row == 0 ? 6 : 3;",
                 "  return row == 0 ? 8 : 3;", "secret background max")
text = rep(text,
    '  static const char *bg[] = {"AUTO","MEADOW","BEACH","FOREST","VOLCANO","MOUNTAIN","SNOW"};',
    '  static const char *bg[] = {"AUTO","MEADOW","BEACH","FOREST","VOLCANO","MOUNTAIN","SNOW","STARFIELD","DREAM"};',
    "secret background labels")
text = rep(text, "  if (row == 0) return bg[v <= 6 ? v : 0];",
                 "  if (row == 0) return bg[v <= 8 ? v : 0];", "secret background label range")
text = rep(text,
    "  if (ultimateHomeBg == 0) return speciesBiome < 6 ? speciesBiome : 0;\n  return (uint8_t)(ultimateHomeBg - 1);",
    "  if (ultimateHomeBg == 0) return speciesBiome < 6 ? speciesBiome : 0;\n"
    "  if (ultimateHomeBg <= 6) return (uint8_t)(ultimateHomeBg - 1);\n"
    "  return speciesBiome < 6 ? speciesBiome : 0;",
    "secret background biome fallback")

helpers = r'''

static const char *ULT_SECRET_CFG_PATH = "/tamapoke_ultimate_secrets.cfg";
static uint8_t ultimateSecretCodePos = 0;
static char ultimateSecretWord[10] = {0};
static uint8_t ultimateSecretWordLen = 0;
static uint32_t ultimateSecretAnimUntil = 0;
static uint8_t ultimateSecretAnimKind = 0;
static uint32_t ultimateSecretCheckAt = 0;

struct __attribute__((packed)) UltimateSecretFile {
  uint32_t magic;
  uint8_t version;
  uint16_t flags;
  uint8_t reserved[5];
  uint32_t crc;
};
static uint32_t ultimateSecretCrc(const UltimateSecretFile &c) {
  return displayCfgHash(reinterpret_cast<const uint8_t*>(&c), offsetof(UltimateSecretFile, crc));
}
static void saveUltimateSecrets() {
  if (!sdReady) return;
  UltimateSecretFile c{};
  c.magic = 0x32534354UL; // "TCS2"
  c.version = 1;
  c.flags = ultimateSecretFlags;
  c.crc = ultimateSecretCrc(c);
  SD.remove(ULT_SECRET_CFG_PATH);
  File f = SD.open(ULT_SECRET_CFG_PATH, FILE_WRITE);
  if (!f) return;
  f.write(reinterpret_cast<const uint8_t*>(&c), sizeof(c)); f.flush(); f.close();
}
static void loadUltimateSecrets() {
  if (!sdReady) return;
  File f = SD.open(ULT_SECRET_CFG_PATH, FILE_READ);
  if (!f || f.size() != sizeof(UltimateSecretFile)) { if (f) f.close(); return; }
  UltimateSecretFile c{};
  size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c)); f.close();
  if (got == sizeof(c) && c.magic == 0x32534354UL && c.version == 1 && ultimateSecretCrc(c) == c.crc)
    ultimateSecretFlags = c.flags;
}

static void ultimateUnlockSecret(uint16_t flag, const char *message, uint8_t animKind) {
  if (ultimateSecretFlags & flag) return;
  ultimateSecretFlags |= flag;
  saveUltimateSecrets();
  ultimateSecretAnimKind = animKind;
  ultimateSecretAnimUntil = millis() + 4200;
  noteEvent(String("SECRET: ") + message);
  say(String("SECRET UNLOCKED: ") + message);
  sfxPlay(SFX_RARE);
  triggerAction(mon.has(PMD_POSE) ? PMD_POSE : PMD_HOP, 2400);
  dirty = true;
}

static void ultimateSecretArrowCode(uint8_t code) {
  // Up Up Down Down Left Right Left Right B A
  static const uint8_t seq[10] = {0,0,2,2,1,3,1,3,4,5};
  if (code == seq[ultimateSecretCodePos]) {
    ultimateSecretCodePos++;
    if (ultimateSecretCodePos >= 10) {
      ultimateSecretCodePos = 0;
      ultimateUnlockSecret(ULT_SECRET_STARFIELD, "STARFIELD HOME", 1);
    }
  } else {
    ultimateSecretCodePos = (code == seq[0]) ? 1 : 0;
  }
}

static bool ultimateSecretWordEnds(const char *needle) {
  size_t n = strlen(needle);
  if (n > ultimateSecretWordLen) return false;
  return strncmp(ultimateSecretWord + ultimateSecretWordLen - n, needle, n) == 0;
}

static void ultimateSecretPrintable(char c) {
  if (!isalnum((unsigned char)c)) return;
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
    ultimateUnlockSecret(ULT_SECRET_DREAM, "DREAM HOME", 2);
    ultimateRareEncounterDex = 151;
    ultimateRareEncounterUntil = millis() + 8000;
    ultimateAwardCoins(50);
    if (ultimateItems[9] < 99) ultimateItems[9]++;
    saveUltimateEconomy();
  } else if (ultimateSecretWordEnds("151")) {
    ultimateUnlockSecret(ULT_SECRET_MASTER151, "151 MASTER BORDER", 3);
  } else if (ultimateSecretWordEnds("ultimate")) {
    ultimateUnlockSecret(ULT_SECRET_MYSTERY_GIFT, "MYSTERY GIFT", 4);
    uint8_t b = random(3); if (ultimateItems[b] < 99) ultimateItems[b]++;
    ultimateAwardCoins(75); saveUltimateEconomy();
  }
}

static void serviceUltimateSecrets(uint32_t now) {
  // An ultra-shiny aura is a true long-term secret reward: shiny + max bond +
  // substantial medal history. It is rare because the shiny itself is rare.
  if (!(ultimateSecretFlags & ULT_SECRET_ULTRA_SHINY) && !pet.isEgg() && pet.shiny &&
      pet.bond >= 100 && pet.totalMedals >= 8) {
    ultimateUnlockSecret(ULT_SECRET_ULTRA_SHINY, "ULTRA SHINY AURA", 5);
  }

  if (now < ultimateSecretCheckAt) return;
  ultimateSecretCheckAt = now + 60000UL;
  if (screen == HOME && !pet.isEgg() && pet.bond >= 80 && random(600) == 0) {
    ultimateUnlockSecret(ULT_SECRET_MYSTERY_GIFT, "MYSTERY GIFT", 4);
    ultimateRareEncounterDex = 151;
    ultimateRareEncounterUntil = now + 6500;
    ultimateAwardCoins(60);
    if (ultimateItems[8] < 99) ultimateItems[8]++;
    saveUltimateEconomy();
  }
}

static void drawUltimateSecretHomeFx(uint32_t now) {
  // Hidden backgrounds layer on top of the selected species habitat and remain
  // cosmetic; gameplay biome logic is unchanged.
  if (ultimateHomeBg == 7 && (ultimateSecretFlags & ULT_SECRET_STARFIELD)) {
    ui.fillRect(0, 0, 240, idleTerrarium ? 92 : 66, C565(0x09,0x0d,0x22));
    for (int i = 0; i < 26; ++i) {
      int x = (i * 47 + 13) % 238;
      int y = (i * 31 + (now / 900) % 7) % (idleTerrarium ? 88 : 64);
      uint16_t c = ((i + now / 320) & 1) ? UI_WHITE : UI_WARN;
      ui.fillRect(x, y, (i % 5 == 0) ? 2 : 1, (i % 5 == 0) ? 2 : 1, c);
    }
  } else if (ultimateHomeBg == 8 && (ultimateSecretFlags & ULT_SECRET_DREAM)) {
    int topH = idleTerrarium ? 92 : 66;
    ui.fillRect(0, 0, 240, topH, C565(0xc9,0xb9,0xf2));
    for (int i = 0; i < 8; ++i) {
      int x = (i * 43 + (now / 35)) % 270 - 15;
      int y = 18 + (i * 17) % std::max(24, topH - 20);
      ui.fillCircle(x, y, 5 + (i % 3) * 2, (i & 1) ? UI_PINK : UI_WHITE);
    }
  }

  if ((ultimateSecretFlags & ULT_SECRET_MASTER151) && !idleTerrarium) {
    uint16_t c = ((now / 300) & 1) ? UI_WARN : UI_PINK;
    ui.drawRoundRect(1, 1, 238, 133, 8, c);
    ui.drawRoundRect(3, 3, 234, 129, 7, UI_BLUE);
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
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text: fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Load persistent secret flags with the other independent configs.
text = rep(text,
    "  loadUltimateDexHistory();\n  displayLastActivity = millis();",
    "  loadUltimateDexHistory();\n  loadUltimateSecrets();\n  displayLastActivity = millis();",
    "setup secrets load")

# Service long-term unlock conditions and ultra-rare mystery events.
text = rep(text,
    "  serviceUltimateVisualState(now);",
    "  serviceUltimateVisualState(now);\n  serviceUltimateSecrets(now);",
    "secret loop service")

# Secret Home layer should come immediately after the base scene so ordinary
# earned furniture is still visible on top of it.
scene_anchor = "  drawUltimateHomeDecor(now, idleTerrarium ? 135 : 90);"
if scene_anchor not in text: fail("Phase 4 decor draw")
text = text.replace(scene_anchor,
    "  drawUltimateSecretHomeFx(now);\n" + scene_anchor,
    1)

# Feed arrow edges into the hidden combination only while truly on Home.
edge_anchor = "  bool escEdge = escNow && !prevEsc;"
if edge_anchor not in text: fail("keyboard edge anchor")
text = text.replace(edge_anchor,
    edge_anchor + "\n\n"
    "  if (screen == HOME && !feedOpen) {\n"
    "    if (upEdge) ultimateSecretArrowCode(0);\n"
    "    if (leftEdge) ultimateSecretArrowCode(1);\n"
    "    if (downEdge) ultimateSecretArrowCode(2);\n"
    "    if (rightEdge) ultimateSecretArrowCode(3);\n"
    "  }",
    1)

# Every new printable Home key also feeds hidden word codes and the B/A tail of
# the arrow combo. Ordinary controls continue to work normally.
print_anchor = "    if (screen == HOME && !feedOpen) {\n      if (c == 'f')"
if print_anchor not in text: fail("Home printable branch")
text = text.replace(print_anchor,
    "    if (screen == HOME && !feedOpen) {\n"
    "      ultimateSecretPrintable(c);\n"
    "      if (c == 'b') ultimateSecretArrowCode(4);\n"
    "      if (c == 'a') ultimateSecretArrowCode(5);\n"
    "      if (c == 'f')",
    1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p12] Added hidden codes, secret backgrounds, mystery gifts, master border and ultra-shiny aura")
