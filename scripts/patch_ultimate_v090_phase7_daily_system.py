Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE7_DAILY_SYSTEM"


def fail(msg):
    print(f"[v0.9.0-ultimate-p7] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p7] daily system already applied")
    Return()
if "// ULTIMATE_V090_PHASE6_MORE_MINIGAMES" not in text:
    fail("Phase 6 must run first")

if "  ULT_GAME,\n  PLAY," not in text:
    fail("Phase 6 screen enum")
text = text.replace("  ULT_GAME,\n  PLAY,",
                    "  ULT_GAME,\n  DAILY,\n  PLAY,", 1)

helpers = r'''

// ULTIMATE_V090_PHASE7_DAILY_SYSTEM
static const char *ULT_DAILY_CFG_PATH = "/tamapoke_ultimate_daily.cfg";
static uint32_t ultimateLastRewardDay = 0;
static uint32_t ultimateAdoptionDay = 0;
static uint32_t ultimateLastEventDay = 0;
static uint32_t ultimateLastGreetingKey = 0;
static uint32_t ultimateCareCoinDay = 0;
static uint8_t ultimateCareCoinsToday = 0;
static uint8_t ultimateLastDailyEvent = 0;
static uint32_t ultimateRareEncounterUntil = 0;
static int16_t ultimateRareEncounterDex = 0;

struct __attribute__((packed)) UltimateDailyFile {
  uint32_t magic;
  uint8_t version;
  uint32_t lastRewardDay;
  uint32_t adoptionDay;
  uint32_t lastEventDay;
  uint32_t lastGreetingKey;
  uint32_t careCoinDay;
  uint8_t careCoinsToday;
  uint8_t lastEvent;
  uint8_t reserved[2];
  uint32_t crc;
};

static uint32_t ultimateDailyCrc(const UltimateDailyFile &c) {
  return displayCfgHash(reinterpret_cast<const uint8_t*>(&c), offsetof(UltimateDailyFile, crc));
}
static void saveUltimateDaily() {
  if (!sdReady) return;
  UltimateDailyFile c{};
  c.magic = 0x37444D54UL; // "TMD7"
  c.version = 1;
  c.lastRewardDay = ultimateLastRewardDay;
  c.adoptionDay = ultimateAdoptionDay;
  c.lastEventDay = ultimateLastEventDay;
  c.lastGreetingKey = ultimateLastGreetingKey;
  c.careCoinDay = ultimateCareCoinDay;
  c.careCoinsToday = ultimateCareCoinsToday;
  c.lastEvent = ultimateLastDailyEvent;
  c.crc = ultimateDailyCrc(c);
  SD.remove(ULT_DAILY_CFG_PATH);
  File f = SD.open(ULT_DAILY_CFG_PATH, FILE_WRITE);
  if (!f) return;
  f.write(reinterpret_cast<const uint8_t*>(&c), sizeof(c));
  f.flush(); f.close();
}
static void loadUltimateDaily() {
  if (!sdReady) return;
  File f = SD.open(ULT_DAILY_CFG_PATH, FILE_READ);
  if (!f || f.size() != sizeof(UltimateDailyFile)) { if (f) f.close(); return; }
  UltimateDailyFile c{};
  size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c)); f.close();
  if (got != sizeof(c) || c.magic != 0x37444D54UL || c.version != 1 || ultimateDailyCrc(c) != c.crc) return;
  ultimateLastRewardDay = c.lastRewardDay;
  ultimateAdoptionDay = c.adoptionDay;
  ultimateLastEventDay = c.lastEventDay;
  ultimateLastGreetingKey = c.lastGreetingKey;
  ultimateCareCoinDay = c.careCoinDay;
  ultimateCareCoinsToday = c.careCoinsToday;
  ultimateLastDailyEvent = c.lastEvent;
}

static uint32_t ultimateCalendarDay() {
  return pet.lastSeenEpoch ? pet.lastSeenEpoch / 86400UL : 0;
}

static const char* ultimateDailyEventName(uint8_t e) {
  switch (e) {
    case 1: return "FOUND BERRIES";
    case 2: return "TRAINING SPARK";
    case 3: return "COZY NAP";
    case 4: return "MUDDY ADVENTURE";
    case 5: return "COIN TREASURE";
    case 6: return "RARE VISITOR";
    default: return "QUIET DAY";
  }
}

static void ultimateAwardCareCoin() {
  uint32_t d = ultimateCalendarDay();
  if (d && d != ultimateCareCoinDay) {
    ultimateCareCoinDay = d;
    ultimateCareCoinsToday = 0;
  }
  // With no clock we still allow the ordinary reward; with a clock it is capped
  // so feeding cannot become an infinite shop-money exploit.
  if (!d || ultimateCareCoinsToday < 5) {
    ultimateAwardCoins(1);
    if (d) {
      ultimateCareCoinsToday++;
      saveUltimateDaily();
    }
  }
}

static void ultimateRunDailyEvent(uint32_t day) {
  ultimateLastEventDay = day;
  ultimateLastDailyEvent = 0;
  int r = random(100);
  if (r < 22) {
    ultimateLastDailyEvent = 1;
    uint8_t b = random(3); if (ultimateItems[b] < 99) ultimateItems[b]++;
    saveUltimateEconomy();
    say("Found a berry!");
  } else if (r < 40) {
    ultimateLastDailyEvent = 2;
    ultimateAwardCoins(8);
    pet.energy = ultAdd100(pet.energy, 8);
    say("Training inspiration!");
  } else if (r < 57) {
    ultimateLastDailyEvent = 3;
    pet.energy = ultAdd100(pet.energy, 18);
    pet.joy = ultAdd100(pet.joy, 8);
    say("A cozy little nap");
  } else if (r < 70) {
    ultimateLastDailyEvent = 4;
    pet.joy = ultAdd100(pet.joy, 15);
    pet.hygiene = ultAdd100(pet.hygiene, -8);
    say("Muddy adventure!");
  } else if (r < 92) {
    ultimateLastDailyEvent = 5;
    ultimateAwardCoins(12 + random(9));
    say("Found coin treasure!");
  } else if (r < 97) {
    ultimateLastDailyEvent = 6;
    static const int16_t rareDex[] = {144,145,146,149,150,151};
    ultimateRareEncounterDex = rareDex[random(6)];
    ultimateRareEncounterUntil = millis() + 6000;
    ultimateAwardCoins(25);
    say("Rare visitor!");
  }
  if (ultimateLastDailyEvent) noteEvent(String("Daily: ") + ultimateDailyEventName(ultimateLastDailyEvent));
  saveUltimateDaily();
  dirty = true;
}

static void checkUltimateDaily(uint32_t now) {
  (void)now;
  uint32_t day = ultimateCalendarDay();
  if (!day) return; // real daily calendar needs the existing NTP clock

  bool changed = false;
  if (!ultimateAdoptionDay) { ultimateAdoptionDay = day; changed = true; }
  if (ultimateCareCoinDay != day) {
    ultimateCareCoinDay = day;
    ultimateCareCoinsToday = 0;
    changed = true;
  }

  if (ultimateLastRewardDay != day) {
    ultimateLastRewardDay = day;
    uint16_t reward = (uint16_t)(10 + std::min<uint16_t>(25, pet.streak / 2));
    ultimateAwardCoins(reward);
    uint8_t berry = random(3); if (ultimateItems[berry] < 99) ultimateItems[berry]++;
    saveUltimateEconomy();
    noteEvent(String("Daily reward: ") + reward + " coins");
    say(String("Daily reward +") + reward + " coins!");
    changed = true;
  }

  if (ultimateLastEventDay != day && screen == HOME && !pet.isEgg()) {
    ultimateRunDailyEvent(day);
  }

  // Morning/night greeting once per period per day.
  int h = sceneHour();
  uint8_t period = (h >= 5 && h < 12) ? 1 : ((h >= 19 || h < 1) ? 2 : 0);
  uint32_t greetingKey = period ? day * 3UL + period : 0;
  if (period && greetingKey != ultimateLastGreetingKey && screen == HOME && !pet.isEgg()) {
    ultimateLastGreetingKey = greetingKey;
    say(period == 1 ? "Good morning!" : "Good night!");
    triggerAction(period == 1 ? PMD_HOP : PMD_NOD, 1400);
    changed = true;
  }

  // Adoption anniversary reward. The date is the first real-calendar day on
  // which Ultimate's daily system saw this save/device.
  if (ultimateAdoptionDay && day > ultimateAdoptionDay &&
      (day - ultimateAdoptionDay) % 365UL == 0 && ultimateLastRewardDay == day) {
    // lastRewardDay prevents repeated runs inside the same day; event log makes
    // the anniversary visible even after its toast disappears.
    static uint32_t anniversarySeenDay = 0;
    if (anniversarySeenDay != day) {
      anniversarySeenDay = day;
      ultimateAwardCoins(100);
      noteEvent("Adoption anniversary! +100 coins");
      say("Happy adoption anniversary!");
    }
  }
  if (changed) saveUltimateDaily();
}

static void drawUltimateDailyFx(uint32_t now) {
  if (idleTerrarium || !ultimateRareEncounterDex || now >= ultimateRareEncounterUntil) return;
  ui.fillRoundRect(42, 34, 156, 24, 7, C565(0xff,0xf0,0xb0));
  ui.drawRoundRect(42, 34, 156, 24, 7, UI_WARN);
  ui.setTextSize(1); ui.setTextColor(UI_INK);
  ui.drawCentreString("RARE VISITOR!", 120, 39, 1);
  String s = String("#") + ultimateRareEncounterDex + " " + dexName(ultimateRareEncounterDex);
  ui.drawCentreString(s, 120, 49, 1);
}

static void drawUltimateDaily() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK); ui.setTextSize(2);
  ui.drawCentreString("DAILY LIFE", 120, 4, 1);
  ui.setTextSize(1);
  uint32_t day = ultimateCalendarDay();
  if (!day) {
    ui.drawCentreString("Calendar clock not synced", 120, 34, 1);
    ui.drawCentreString("Set Wi-Fi in user_config.h for NTP", 120, 50, 1);
  } else {
    char line[42];
    snprintf(line, sizeof(line), "Care streak: %u   Best: %u", pet.streak, pet.bestStreak);
    ui.drawCentreString(line, 120, 28, 1);
    snprintf(line, sizeof(line), "Daily reward: CLAIMED");
    ui.drawCentreString(line, 120, 43, 1);
    snprintf(line, sizeof(line), "Today's event: %s", ultimateDailyEventName(ultimateLastDailyEvent));
    ui.drawCentreString(line, 120, 58, 1);
    uint32_t days = ultimateAdoptionDay && day >= ultimateAdoptionDay ? day - ultimateAdoptionDay : 0;
    snprintf(line, sizeof(line), "Together: %lu day%s", (unsigned long)days, days == 1 ? "" : "s");
    ui.drawCentreString(line, 120, 73, 1);
    snprintf(line, sizeof(line), "Care coins today: %u/5", ultimateCareCoinsToday);
    ui.drawCentreString(line, 120, 88, 1);
    ui.drawCentreString("Rare visitors can appear in daily events", 120, 104, 1);
  }
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ESC / ENTER = HOME", 120, 123, 1);
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text: fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

text = rep(text,
    "  loadUltimateGames();\n  displayLastActivity = millis();",
    "  loadUltimateGames();\n  loadUltimateDaily();\n  displayLastActivity = millis();",
    "setup daily load")

# Cap ordinary care-coin farming using the daily budget.
text = text.replace("  ultimateAwardCoins(1);\n  feedOpen = false;",
                    "  ultimateAwardCareCoin();\n  feedOpen = false;", 1)

# Rare encounter overlay sits with Home content, before the action panel.
home_anchor = "  drawBathFx(now);"
if home_anchor not in text: fail("Home bath FX anchor")
text = text.replace(home_anchor, "  drawUltimateDailyFx(now);\n" + home_anchor, 1)

# Render daily screen.
render_anchor = "      case ULT_GAME:   drawUltimateGame(now); break;"
if render_anchor not in text: fail("Phase 6 render")
text = text.replace(render_anchor, render_anchor + "\n      case DAILY:      drawUltimateDaily(); break;", 1)

# Loop service after pet update so calendar day advances with the synced clock.
text = rep(text,
    "  updateUltimateGame(now);",
    "  updateUltimateGame(now);\n  checkUltimateDaily(now);",
    "daily loop service")

# Input before GAMES.
input_anchor = "  } else if (screen == GAMES) {"
if input_anchor not in text: fail("Phase 6 input")
daily_input = r'''  } else if (screen == DAILY) {
    if (escEdge || backEdge || enterEdge || spaceEdge) { screen = HOME; dirty = true; }
'''
text = text.replace(input_anchor, daily_input + input_anchor, 1)

# Y opens Daily Life.
key_anchor = "      } else if (c == 'm') {"
if key_anchor not in text: fail("Phase 6 Home game key")
text = text.replace(key_anchor,
    "      } else if (c == 'y') {\n"
    "        screen = DAILY; dirty = true;\n"
    + key_anchor, 1)

text = text.replace('    "M: games   E: evolve   G: goodbye",',
                    '    "M: games   Y: daily   E: evolve",', 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p7] Added daily rewards, care cap, random events, greetings, anniversary and rare visitors")
