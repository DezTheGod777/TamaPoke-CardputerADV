Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_DAILY_TOGETHER_FIX"


def fail(msg):
    print(f"[v0.9.0-daily-together] ERROR: {msg}")
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
    print("[v0.9.0-daily-together] fix already applied")
    Return()
if "// ULTIMATE_V090_THIRD_AUDIT" not in text:
    fail("third audit must run first")

# Daily Life originally persisted an 'adoption day' the first time its calendar
# saw a valid clock. Early hardware-test builds could therefore preserve a stale
# date inherited from an incorrect/system clock and display impossible values
# such as thousands of days together. The pet journal already has the reliable
# elapsed lifetime counter (ageMinutes), so use that as the source of truth.

new_check = r'''static void checkUltimateDaily(uint32_t now) {
  (void)now;
  uint32_t day = ultimateCalendarDay();
  if (!day) return;

  bool changed = false;

  // Source of truth for time together: actual elapsed pet lifetime. This is
  // preserved through evolution, reset for a new life, and already receives the
  // original TamaPoke offline catch-up (capped at two weeks per sync).
  uint32_t togetherDays = pet.ageMinutes / 1440UL;
  uint32_t inferredAdoptionDay = day >= togetherDays ? day - togetherDays : day;
  if (ultimateAdoptionDay != inferredAdoptionDay) {
    ultimateAdoptionDay = inferredAdoptionDay;
    changed = true;
  }

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
    sfxPlay(SFX_DAILY);
    changed = true;
  }

  if (ultimateLastEventDay != day && screen == HOME && !pet.isEgg()) {
    ultimateRunDailyEvent(day);
  }

  // Morning/night greeting once per period per local calendar day.
  int h = sceneHour();
  uint8_t period = (h >= 5 && h < 12) ? 1 : ((h >= 19 || h < 1) ? 2 : 0);
  uint32_t greetingKey = period ? day * 3UL + period : 0;
  if (period && greetingKey != ultimateLastGreetingKey && screen == HOME && !pet.isEgg()) {
    ultimateLastGreetingKey = greetingKey;
    say(period == 1 ? "Good morning!" : "Good night!");
    triggerAction(period == 1 ? PMD_HOP : PMD_NOD, 1400);
    changed = true;
  }

  // Anniversary follows actual elapsed time together rather than a potentially
  // stale historical calendar value. Pay at most once on the local day on which
  // a 365-day milestone is observed.
  if (!pet.isEgg() && togetherDays > 0 && (togetherDays % 365UL) == 0 &&
      ultimateLastAnniversaryDay != day) {
    ultimateLastAnniversaryDay = day;
    ultimateAwardCoins(100);
    noteEvent("Adoption anniversary! +100 coins");
    say("Happy adoption anniversary!");
    changed = true;
  }

  if (changed) saveUltimateDaily();
}'''
text = replace_function(text,
    "static void checkUltimateDaily(uint32_t now) {",
    "static void drawUltimateDailyFx",
    new_check,
    "Daily Life service")

new_draw = r'''static void drawUltimateDaily() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK); ui.setTextSize(2);
  ui.drawCentreString("DAILY LIFE", 120, 4, 1);
  ui.setTextSize(1);
  uint32_t day = ultimateCalendarDay();
  if (!day) {
    ui.drawCentreString("Date & time not set", 120, 34, 1);
    ui.drawCentreString("Settings > Set Date / Time", 120, 50, 1);
    ui.drawCentreString("Wi-Fi sync is optional", 120, 66, 1);
  } else {
    char line[42];
    snprintf(line, sizeof(line), "Care streak: %u   Best: %u", pet.streak, pet.bestStreak);
    ui.drawCentreString(line, 120, 28, 1);
    snprintf(line, sizeof(line), "Daily reward: CLAIMED");
    ui.drawCentreString(line, 120, 43, 1);
    snprintf(line, sizeof(line), "Today's event: %s", ultimateDailyEventName(ultimateLastDailyEvent));
    ui.drawCentreString(line, 120, 58, 1);

    // Display elapsed full days with the current Pokemon. Do not calculate this
    // from a persisted calendar date, which can be poisoned by an old bad clock.
    uint32_t days = pet.ageMinutes / 1440UL;
    snprintf(line, sizeof(line), "Together: %lu day%s", (unsigned long)days, days == 1 ? "" : "s");
    ui.drawCentreString(line, 120, 73, 1);

    snprintf(line, sizeof(line), "Care coins today: %u/5", ultimateCareCoinsToday);
    ui.drawCentreString(line, 120, 88, 1);
    ui.drawCentreString("Rare visitors can appear in daily events", 120, 104, 1);
  }
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ESC / ENTER = HOME", 120, 123, 1);
}'''
text = replace_function(text,
    "static void drawUltimateDaily() {",
    "static void drawHome(uint32_t now) {",
    new_draw,
    "Daily Life screen")

# Marker beside the generated Daily Life code for build/audit proof.
text = text.replace("// ULTIMATE_V090_THIRD_AUDIT",
                    "// ULTIMATE_V090_THIRD_AUDIT\n" + MARKER, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-daily-together] Together/anniversary now use actual pet age instead of stale calendar adoption data")
