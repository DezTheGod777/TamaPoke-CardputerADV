Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE8_DEEPER_POKEDEX"


def fail(msg):
    print(f"[v0.9.0-ultimate-p8] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p8] deeper Pokedex already applied")
    Return()
if "// ULTIMATE_V090_PHASE7_DAILY_SYSTEM" not in text:
    fail("Phase 7 must run first")

if "  DAILY,\n  PLAY," not in text:
    fail("Phase 7 screen enum")
text = text.replace("  DAILY,\n  PLAY,", "  DAILY,\n  DEX_STATS,\n  PLAY,", 1)

helpers = r'''

// ULTIMATE_V090_PHASE8_DEEPER_POKEDEX
static const char *ULT_DEX_HISTORY_PATH = "/tamapoke_ultimate_dex.bin";
static uint16_t ultimateRaised[151] = {0};
static uint16_t ultimateShinyRaised[151] = {0};
static uint8_t ultimateMaxLevel[151] = {0};
static uint32_t ultimateSpeciesMinutes[151] = {0};
static uint16_t ultimateSpeciesMedals[151] = {0};
static int16_t ultimateFavoriteDex = 0;
static int16_t ultimateEvoFrom[12] = {0};
static int16_t ultimateEvoTo[12] = {0};
static uint8_t ultimateEvoCount = 0;
static uint8_t ultimateDexStatsPage = 0;

static bool ultimateDexRuntimeReady = false;
static bool ultimateDexWasEgg = true;
static int16_t ultimateDexLastSpecies = -1;
static uint32_t ultimateDexLastAge = 0;
static uint16_t ultimateDexLastMedals = 0;

struct __attribute__((packed)) UltimateDexHistoryFile {
  uint32_t magic;
  uint8_t version;
  uint16_t raised[151];
  uint16_t shinyRaised[151];
  uint8_t maxLevel[151];
  uint32_t minutes[151];
  uint16_t speciesMedals[151];
  int16_t favoriteDex;
  int16_t evoFrom[12];
  int16_t evoTo[12];
  uint8_t evoCount;
  uint8_t reserved[3];
  uint32_t crc;
};

static uint32_t ultimateDexHistoryCrc(const UltimateDexHistoryFile &c) {
  return displayCfgHash(reinterpret_cast<const uint8_t*>(&c), offsetof(UltimateDexHistoryFile, crc));
}
static void saveUltimateDexHistory() {
  if (!sdReady) return;
  UltimateDexHistoryFile c{};
  c.magic = 0x38445854UL; // "TXD8"
  c.version = 1;
  memcpy(c.raised, ultimateRaised, sizeof(ultimateRaised));
  memcpy(c.shinyRaised, ultimateShinyRaised, sizeof(ultimateShinyRaised));
  memcpy(c.maxLevel, ultimateMaxLevel, sizeof(ultimateMaxLevel));
  memcpy(c.minutes, ultimateSpeciesMinutes, sizeof(ultimateSpeciesMinutes));
  memcpy(c.speciesMedals, ultimateSpeciesMedals, sizeof(ultimateSpeciesMedals));
  c.favoriteDex = ultimateFavoriteDex;
  memcpy(c.evoFrom, ultimateEvoFrom, sizeof(ultimateEvoFrom));
  memcpy(c.evoTo, ultimateEvoTo, sizeof(ultimateEvoTo));
  c.evoCount = ultimateEvoCount;
  c.crc = ultimateDexHistoryCrc(c);
  SD.remove(ULT_DEX_HISTORY_PATH);
  File f = SD.open(ULT_DEX_HISTORY_PATH, FILE_WRITE);
  if (!f) return;
  f.write(reinterpret_cast<const uint8_t*>(&c), sizeof(c)); f.flush(); f.close();
}
static void loadUltimateDexHistory() {
  if (!sdReady) return;
  File f = SD.open(ULT_DEX_HISTORY_PATH, FILE_READ);
  if (!f || f.size() != sizeof(UltimateDexHistoryFile)) { if (f) f.close(); return; }
  UltimateDexHistoryFile c{};
  size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c)); f.close();
  if (got != sizeof(c) || c.magic != 0x38445854UL || c.version != 1 || ultimateDexHistoryCrc(c) != c.crc) return;
  memcpy(ultimateRaised, c.raised, sizeof(ultimateRaised));
  memcpy(ultimateShinyRaised, c.shinyRaised, sizeof(ultimateShinyRaised));
  memcpy(ultimateMaxLevel, c.maxLevel, sizeof(ultimateMaxLevel));
  memcpy(ultimateSpeciesMinutes, c.minutes, sizeof(ultimateSpeciesMinutes));
  memcpy(ultimateSpeciesMedals, c.speciesMedals, sizeof(ultimateSpeciesMedals));
  ultimateFavoriteDex = c.favoriteDex;
  memcpy(ultimateEvoFrom, c.evoFrom, sizeof(ultimateEvoFrom));
  memcpy(ultimateEvoTo, c.evoTo, sizeof(ultimateEvoTo));
  ultimateEvoCount = c.evoCount > 12 ? 12 : c.evoCount;
}

static uint8_t ultimatePopcount16(uint16_t v) {
  uint8_t n = 0; while (v) { v &= (uint16_t)(v - 1); ++n; } return n;
}

static void ultimateRecordRaised(int16_t dex, bool shiny) {
  if (dex < 1 || dex > 151) return;
  uint16_t &r = ultimateRaised[dex - 1]; if (r < 65535) r++;
  if (shiny) { uint16_t &s = ultimateShinyRaised[dex - 1]; if (s < 65535) s++; }
}

static void ultimateRecordEvolution(int16_t from, int16_t to) {
  if (from < 1 || to < 1 || from == to) return;
  int limit = ultimateEvoCount < 12 ? ultimateEvoCount : 11;
  for (int i = limit; i > 0; --i) {
    ultimateEvoFrom[i] = ultimateEvoFrom[i - 1];
    ultimateEvoTo[i] = ultimateEvoTo[i - 1];
  }
  ultimateEvoFrom[0] = from; ultimateEvoTo[0] = to;
  if (ultimateEvoCount < 12) ultimateEvoCount++;
}

static void initUltimateDexRuntime() {
  ultimateDexRuntimeReady = true;
  ultimateDexWasEgg = pet.isEgg();
  ultimateDexLastSpecies = pet.isEgg() ? -1 : pet.speciesId;
  ultimateDexLastAge = pet.ageMinutes;
  ultimateDexLastMedals = pet.medals;
  if (!pet.isEgg() && pet.speciesId >= 1 && pet.speciesId <= 151) {
    int i = pet.speciesId - 1;
    if (ultimateRaised[i] == 0) {
      ultimateRecordRaised(pet.speciesId, pet.shiny); // existing pet on first Ultimate install
      saveUltimateDexHistory();
    }
    ultimateMaxLevel[i] = std::max<uint8_t>(ultimateMaxLevel[i], pet.level());
  }
}

static void serviceUltimateDexHistory() {
  if (!ultimateDexRuntimeReady) { initUltimateDexRuntime(); return; }
  bool changed = false;
  if (pet.isEgg()) {
    ultimateDexWasEgg = true;
    ultimateDexLastSpecies = -1;
    ultimateDexLastAge = pet.ageMinutes;
    ultimateDexLastMedals = 0;
    return;
  }

  int16_t cur = pet.speciesId;
  if (cur < 1 || cur > 151) return;

  if (ultimateDexWasEgg) {
    ultimateRecordRaised(cur, pet.shiny);
    ultimateDexWasEgg = false;
    ultimateDexLastSpecies = cur;
    ultimateDexLastAge = pet.ageMinutes;
    ultimateDexLastMedals = pet.medals;
    changed = true;
  }

  if (ultimateDexLastSpecies >= 1 && ultimateDexLastSpecies <= 151 &&
      pet.ageMinutes > ultimateDexLastAge) {
    uint32_t delta = pet.ageMinutes - ultimateDexLastAge;
    uint32_t &m = ultimateSpeciesMinutes[ultimateDexLastSpecies - 1];
    m = (0xFFFFFFFFUL - m < delta) ? 0xFFFFFFFFUL : m + delta;
    changed = true;
  }
  ultimateDexLastAge = pet.ageMinutes;

  if (ultimateDexLastSpecies > 0 && cur != ultimateDexLastSpecies) {
    ultimateRecordEvolution(ultimateDexLastSpecies, cur);
    ultimateRecordRaised(cur, pet.shiny);
    noteEvent(String("Evolution history: ") + dexName(ultimateDexLastSpecies) + " > " + dexName(cur));
    ultimateDexLastSpecies = cur;
    ultimateDexLastMedals = pet.medals;
    changed = true;
  }

  uint8_t lv = pet.level();
  if (lv > ultimateMaxLevel[cur - 1]) { ultimateMaxLevel[cur - 1] = lv; changed = true; }

  uint16_t newMedals = pet.medals & ~ultimateDexLastMedals;
  if (newMedals) {
    uint16_t &n = ultimateSpeciesMedals[cur - 1];
    uint16_t add = ultimatePopcount16(newMedals);
    n = (uint16_t)std::min<uint32_t>(65535, (uint32_t)n + add);
    ultimateDexLastMedals = pet.medals;
    changed = true;
  }

  if (changed) saveUltimateDexHistory();
}

static void ultimateSetFavorite(int16_t dex) {
  if (dex < 1 || dex > 151 || !pet.isRegistered(dex)) { sfxPlay(SFX_DENY); return; }
  ultimateFavoriteDex = ultimateFavoriteDex == dex ? 0 : dex;
  saveUltimateDexHistory();
  sfxPlay(SFX_HEART);
  say(ultimateFavoriteDex ? String(dexName(dex)) + " is your favorite!" : "Favorite cleared");
  dirty = true;
}

static void drawUltimateDexStats() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK); ui.setTextSize(2);
  ui.drawCentreString(ultimateDexStatsPage == 0 ? "POKEDEX HISTORY" : "EVOLUTION HISTORY", 120, 4, 1);
  ui.setTextSize(1);
  if (ultimateDexStatsPage == 0) {
    int d = dexCursor;
    bool known = pet.isRegistered(d);
    char head[42];
    snprintf(head, sizeof(head), "%s#%03d  %s", ultimateFavoriteDex == d ? "* " : "", d, known ? dexName(d) : "???");
    ui.setTextColor(known ? DEX_TBL[d].accent : UI_INK);
    ui.drawCentreString(head, 120, 25, 1);
    if (!known) {
      ui.setTextColor(UI_INK); ui.drawCentreString("Raise this Pokemon to unlock history", 120, 55, 1);
    } else {
      int i = d - 1;
      char line[48];
      snprintf(line, sizeof(line), "Raised: %u   Shiny: %u", ultimateRaised[i], ultimateShinyRaised[i]);
      ui.setTextColor(UI_INK); ui.drawCentreString(line, 120, 43, 1);
      snprintf(line, sizeof(line), "Highest level: %u", ultimateMaxLevel[i]); ui.drawCentreString(line, 120, 58, 1);
      uint32_t mins = ultimateSpeciesMinutes[i];
      snprintf(line, sizeof(line), "Time together: %luh %02lum", (unsigned long)(mins / 60), (unsigned long)(mins % 60));
      ui.drawCentreString(line, 120, 73, 1);
      snprintf(line, sizeof(line), "Medals earned as species: %u", ultimateSpeciesMedals[i]); ui.drawCentreString(line, 120, 88, 1);
      ui.drawCentreString(ultimateFavoriteDex == d ? "F: REMOVE FAVORITE" : "F: SET FAVORITE", 120, 103, 1);
    }
  } else {
    if (!ultimateEvoCount) {
      ui.drawCentreString("No evolutions recorded yet", 120, 58, 1);
    } else {
      for (int i = 0; i < ultimateEvoCount && i < 6; ++i) {
        char line[42];
        snprintf(line, sizeof(line), "%s  >  %s", dexName(ultimateEvoFrom[i]), dexName(ultimateEvoTo[i]));
        ui.drawCentreString(line, 120, 27 + i * 14, 1);
      }
    }
  }
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("UP/DOWN PAGE  LEFT/RIGHT BROWSE  ESC", 120, 123, 1);
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text: fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Load history before pet begins; initialize runtime immediately after pet begin.
text = rep(text,
    "  loadUltimateDaily();\n  displayLastActivity = millis();",
    "  loadUltimateDaily();\n  loadUltimateDexHistory();\n  displayLastActivity = millis();",
    "setup history load")
text = rep(text,
    "  pet.begin();",
    "  pet.begin();\n  initUltimateDexRuntime();",
    "runtime history init")

# Service history every loop; writes only when minute/species/medal state changes.
text = rep(text,
    "  checkUltimateDaily(now);",
    "  checkUltimateDaily(now);\n  serviceUltimateDexHistory();",
    "history loop service")

# Render new history screen.
render_anchor = "      case DAILY:      drawUltimateDaily(); break;"
if render_anchor not in text: fail("Phase 7 render")
text = text.replace(render_anchor, render_anchor + "\n      case DEX_STATS:  drawUltimateDexStats(); break;", 1)

# Input before DEX_GRID branch.
input_anchor = "  } else if (screen == DEX_GRID) {"
if input_anchor not in text: fail("Dex grid input")
stats_input = r'''  } else if (screen == DEX_STATS) {
    if (leftEdge && dexCursor > 1) { --dexCursor; dirty = true; }
    if (rightEdge && dexCursor < 151) { ++dexCursor; dirty = true; }
    if (upEdge || downEdge) { ultimateDexStatsPage ^= 1; dirty = true; }
    if (chars[(uint8_t)'f'] && !prevChars[(uint8_t)'f'] && ultimateDexStatsPage == 0) ultimateSetFavorite(dexCursor);
    if (escEdge || backEdge || enterEdge) { screen = DEX_DETAIL; monDex = -999; dirty = true; }
'''
text = text.replace(input_anchor, stats_input + input_anchor, 1)

# H opens history from Dex detail; F marks favorite there too.
print_anchor = "    } else if (screen == CARD) {"
if print_anchor not in text: fail("printable CARD branch")
# Add a new branch after CARD's closing section by replacing its known tail.
card_tail = "      }\n    }\n  }\n\nsave_input_state:"
if card_tail not in text:
    fail("printable key tail")
new_tail = r'''      }
    } else if (screen == DEX_DETAIL) {
      if (c == 'h') { ultimateDexStatsPage = 0; screen = DEX_STATS; dirty = true; }
      else if (c == 'f') ultimateSetFavorite(dexCursor);
    } else if (screen == DEX_STATS) {
      if (c == 'f' && ultimateDexStatsPage == 0) ultimateSetFavorite(dexCursor);
    }
  }

save_input_state:'''
text = text.replace(card_tail, new_tail, 1)

# J opens history for current Pokemon directly from Home.
key_anchor = "      } else if (c == 'y') {"
if key_anchor not in text: fail("Phase 7 daily key")
text = text.replace(key_anchor,
    "      } else if (c == 'j' && !pet.isEgg()) {\n"
    "        dexCursor = pet.speciesId; ultimateDexStatsPage = 0; screen = DEX_STATS; dirty = true;\n"
    + key_anchor, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p8] Added per-species raised/shiny/level/time/medal history, favorites and evolution log")
