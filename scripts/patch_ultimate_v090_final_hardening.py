Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_FINAL_HARDENING"


def fail(msg):
    print(f"[v0.9.0-ultimate-final] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


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
    print("[v0.9.0-ultimate-final] final hardening already applied")
    Return()
if "// ULTIMATE_V090_PHASE12_SECRET_CONTENT" not in text:
    fail("Phase 12 must run first")

# ---------------------------------------------------------------------------
# 1) Correct on-device identity. Phase 1 updates the constants, but the stable
# boot art also contained literal RC5/test strings.
# ---------------------------------------------------------------------------
text = rep(text, '"v0.8.5.4  FULL POLISH RC5"', '"v0.9.0  ULTIMATE"', "boot version label")
text = rep(text, '"OG FIRMWARE TEST BUILD"', '"ULTIMATE HARDWARE TEST"', "boot build label")

# ---------------------------------------------------------------------------
# 2) Personality must never change merely because the Pokemon evolves.
# Remove speciesId from the Phase 2 signature; only permanent hatch genes are
# used now.
# ---------------------------------------------------------------------------
old_sig = '''static uint8_t ultimateTraitSignature() {
  uint32_t sid = pet.speciesId > 0 ? (uint32_t)pet.speciesId : 1UL;
  return (uint8_t)(((uint32_t)pet.geneAtk * 3UL +
                    (uint32_t)pet.geneDef * 5UL +
                    (uint32_t)pet.geneSpe * 7UL + sid * 11UL) % 12UL);
}'''
new_sig = '''static uint8_t ultimateTraitSignature() {
  // Permanent hatch genes only: evolution must not change temperament.
  uint32_t mix = (uint32_t)pet.geneAtk * 3UL +
                 (uint32_t)pet.geneDef * 5UL +
                 (uint32_t)pet.geneSpe * 7UL;
  mix ^= ((uint32_t)pet.geneAtk << 16) ^
         ((uint32_t)pet.geneDef << 8) ^
         (uint32_t)pet.geneSpe;
  return (uint8_t)(mix % 12UL);
}'''
text = rep(text, old_sig, new_sig, "gene-only personality signature")

# ---------------------------------------------------------------------------
# 3) Screen reveals must keep static destination screens rendering until the
# wipe is finished. Without this, the first frame could remain fully covered.
# ---------------------------------------------------------------------------
text = rep(text,
    "static bool screenAnimated() {\n  if (pet.awaitingStarter()) return false;",
    "static bool screenAnimated() {\n  if (ultimateTransitionStart) return true;\n  if (pet.awaitingStarter()) return false;",
    "transition animation scheduler")

# ---------------------------------------------------------------------------
# 4) Daily system hardening: persistent anniversary claim and a bounded
# no-clock care reward. The calendar-backed cap remains 5/day; without NTP it
# becomes 5 per boot session instead of unlimited farming.
# ---------------------------------------------------------------------------
text = rep(text,
    "static uint8_t ultimateLastDailyEvent = 0;\nstatic uint32_t ultimateRareEncounterUntil = 0;",
    "static uint8_t ultimateLastDailyEvent = 0;\n"
    "static uint32_t ultimateLastAnniversaryDay = 0;\n"
    "static uint8_t ultimateUnsyncedCareCoinsSession = 0;\n"
    "static uint32_t ultimateRareEncounterUntil = 0;",
    "daily hardening state")

text = rep(text,
    "  uint32_t careCoinDay;\n  uint8_t careCoinsToday;\n  uint8_t lastEvent;\n  uint8_t reserved[2];",
    "  uint32_t careCoinDay;\n  uint32_t lastAnniversaryDay;\n  uint8_t careCoinsToday;\n  uint8_t lastEvent;\n  uint8_t reserved[2];",
    "daily file anniversary field")

text = rep(text,
    '  c.magic = 0x37444D54UL; // "TMD7"\n  c.version = 1;',
    '  c.magic = 0x37444D54UL; // "TMD7"\n  c.version = 2;',
    "daily config version save")
text = rep(text,
    "  c.careCoinDay = ultimateCareCoinDay;\n  c.careCoinsToday = ultimateCareCoinsToday;",
    "  c.careCoinDay = ultimateCareCoinDay;\n  c.lastAnniversaryDay = ultimateLastAnniversaryDay;\n  c.careCoinsToday = ultimateCareCoinsToday;",
    "daily config anniversary save")
text = rep(text,
    "c.magic != 0x37444D54UL || c.version != 1 || ultimateDailyCrc(c) != c.crc",
    "c.magic != 0x37444D54UL || c.version != 2 || ultimateDailyCrc(c) != c.crc",
    "daily config version load")
text = rep(text,
    "  ultimateCareCoinDay = c.careCoinDay;\n  ultimateCareCoinsToday = c.careCoinsToday;",
    "  ultimateCareCoinDay = c.careCoinDay;\n  ultimateLastAnniversaryDay = c.lastAnniversaryDay;\n  ultimateCareCoinsToday = c.careCoinsToday;",
    "daily config anniversary load")

new_care_coin = r'''static void ultimateAwardCareCoin() {
  uint32_t d = ultimateCalendarDay();
  if (!d) {
    // No real calendar: still bounded for the current boot instead of becoming
    // an unlimited coin source. A later NTP sync switches back to the real day.
    if (ultimateUnsyncedCareCoinsSession >= 5) return;
    ultimateUnsyncedCareCoinsSession++;
    ultimateAwardCoins(1);
    return;
  }
  if (d != ultimateCareCoinDay) {
    ultimateCareCoinDay = d;
    ultimateCareCoinsToday = 0;
  }
  if (ultimateCareCoinsToday >= 5) return;
  ultimateAwardCoins(1);
  ultimateCareCoinsToday++;
  saveUltimateDaily();
}'''
text = replace_function(text,
    "static void ultimateAwardCareCoin() {",
    "static void ultimateRunDailyEvent",
    new_care_coin,
    "bounded care coin reward")

old_anniversary = '''    // lastRewardDay prevents repeated runs inside the same day; event log makes
    // the anniversary visible even after its toast disappears.
    static uint32_t anniversarySeenDay = 0;
    if (anniversarySeenDay != day) {
      anniversarySeenDay = day;
      ultimateAwardCoins(100);
      noteEvent("Adoption anniversary! +100 coins");
      say("Happy adoption anniversary!");
    }'''
new_anniversary = '''    // Persist the claimed anniversary day so a reboot cannot pay it twice.
    if (ultimateLastAnniversaryDay != day) {
      ultimateLastAnniversaryDay = day;
      ultimateAwardCoins(100);
      noteEvent("Adoption anniversary! +100 coins");
      say("Happy adoption anniversary!");
      changed = true;
    }'''
text = rep(text, old_anniversary, new_anniversary, "persistent anniversary reward")

# ---------------------------------------------------------------------------
# 5) Evo Charm should do something useful before the exact evolution-ready
# instant while still respecting the species' real evolution path/level.
# ---------------------------------------------------------------------------
old_evo_charm = '''  } else if (item == 5) {
    // Evolutionary item: it intentionally respects TamaPoke's existing
    // evolution requirements and opens the normal confirmation/animation.
    if (!pet.wantEvolveButton()) used = false;
    else {
      dialogKind = DLG_EVOLVE;
      dialogSel = 0;
      screen = DIALOG;
      sfxPlay(SFX_TAP);
    }
  } else if (item == 6) {'''
new_evo_charm = '''  } else if (item == 5) {
    // Evolution Charm: improves evolution readiness without bypassing the
    // species' real evolution path. It repairs one care mistake and restores
    // the four care needs to a healthy minimum; if that makes evolution ready,
    // the normal confirmation/animation opens immediately.
    if (pet.isEgg() || pet.sleeping || pet.speciesId < 1 ||
        !DEX_TBL[pet.speciesId].evolvesTo) {
      used = false;
    } else {
      if (pet.careMistakes > 0) pet.careMistakes--;
      pet.fullness = std::max<uint8_t>(pet.fullness, 50);
      pet.joy = std::max<uint8_t>(pet.joy, 50);
      pet.energy = std::max<uint8_t>(pet.energy, 50);
      pet.hygiene = std::max<uint8_t>(pet.hygiene, 50);
      if (pet.wantEvolveButton()) {
        dialogKind = DLG_EVOLVE;
        dialogSel = 0;
        screen = DIALOG;
        sfxPlay(SFX_TAP);
        say("Evolution ready!");
      } else {
        triggerAction(mon.has(PMD_POSE) ? PMD_POSE : PMD_NOD, 1600);
        sfxPlay(SFX_LEVEL);
        say("Evolution boosted!");
      }
    }
  } else if (item == 6) {'''
text = rep(text, old_evo_charm, new_evo_charm, "useful Evo Charm")

# ---------------------------------------------------------------------------
# 6) Every minigame timer bar must scale to that game's actual duration.
# ---------------------------------------------------------------------------
text = rep(text,
    "  int fw = (int)std::min<uint32_t>(128, left * 128 / 30000UL);",
    "  uint32_t total = ultimateGameMode == UGM_BERRY ? 20000UL :\n"
    "                   ultimateGameMode == UGM_REACTION ? 30000UL :\n"
    "                   ultimateGameMode == UGM_MEMORY ? 20000UL :\n"
    "                   ultimateGameMode == UGM_RACE ? 12000UL :\n"
    "                   ultimateGameMode == UGM_TARGET ? 18000UL : 15000UL;\n"
    "  int fw = (int)std::min<uint32_t>(128, left * 128 / total);",
    "per-game timer scale")

# ---------------------------------------------------------------------------
# 7) Favorite toggle was handled once in the direct input branch and again in
# printable-key handling. Keep the latter so one F press equals one toggle.
# ---------------------------------------------------------------------------
text = rep(text,
    "    if (chars[(uint8_t)'f'] && !prevChars[(uint8_t)'f'] && ultimateDexStatsPage == 0) ultimateSetFavorite(dexCursor);\n",
    "",
    "single favorite toggle")

# ---------------------------------------------------------------------------
# 8) Phase 12 secret word handling. Feed printable characters globally so code
# entry can survive ordinary shortcut-driven screen changes; pay one-time gifts
# only on the first unlock.
# ---------------------------------------------------------------------------
new_secret_printable = r'''static void ultimateSecretPrintable(char c) {
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
    bool fresh = (ultimateSecretFlags & ULT_SECRET_DREAM) == 0;
    ultimateUnlockSecret(ULT_SECRET_DREAM, "DREAM HOME", 2);
    if (fresh) {
      ultimateRareEncounterDex = 151;
      ultimateRareEncounterUntil = millis() + 8000;
      ultimateAwardCoins(50);
      if (ultimateItems[9] < 99) ultimateItems[9]++;
      saveUltimateEconomy();
    }
    screen = HOME; feedOpen = false; dirty = true;
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
  } else if (ultimateSecretWordEnds("151")) {
    ultimateUnlockSecret(ULT_SECRET_MASTER151, "151 MASTER BORDER", 3);
    ultimateSecretWordLen = 0; ultimateSecretWord[0] = 0;
  } else if (ultimateSecretWordEnds("ultimate")) {
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
  }
}'''
text = replace_function(text,
    "static void ultimateSecretPrintable(char c) {",
    "static void serviceUltimateSecrets",
    new_secret_printable,
    "secret word input")

text = rep(text,
    "    if (screen == HOME && !feedOpen) {\n      ultimateSecretPrintable(c);\n      if (c == 'b') ultimateSecretArrowCode(4);",
    "    ultimateSecretPrintable(c);\n"
    "    if (screen == HOME && !feedOpen) {\n"
    "      if (c == 'b') ultimateSecretArrowCode(4);",
    "global secret word feed")

text = rep(text,
    "  if (screen == HOME && !pet.isEgg() && pet.bond >= 80 && random(600) == 0) {",
    "  if (!(ultimateSecretFlags & ULT_SECRET_MYSTERY_GIFT) &&\n"
    "      screen == HOME && !pet.isEgg() && pet.bond >= 80 && random(600) == 0) {",
    "one-time random mystery gift")

# ---------------------------------------------------------------------------
# 9) A 'full' backup must include Phase 12's persistent secret flags too.
# Literal paths avoid declaration-order coupling between Phase 9 and Phase 12.
# ---------------------------------------------------------------------------
text = rep(text,
    '  aux &= ultimateBackupAux(slot, ULT_DEX_HISTORY_PATH, "_dex.bin");',
    '  aux &= ultimateBackupAux(slot, ULT_DEX_HISTORY_PATH, "_dex.bin");\n'
    '  aux &= ultimateBackupAux(slot, "/tamapoke_ultimate_secrets.cfg", "_secrets.cfg");',
    "secret config backup")
text = rep(text,
    '  ok &= ultimateRestoreAux(slot, ULT_DEX_HISTORY_PATH, "_dex.bin");',
    '  ok &= ultimateRestoreAux(slot, ULT_DEX_HISTORY_PATH, "_dex.bin");\n'
    '  ok &= ultimateRestoreAux(slot, "/tamapoke_ultimate_secrets.cfg", "_secrets.cfg");',
    "secret config restore")

# Final marker is intentionally inserted into the generated source so CI logs
# and hardware diagnostics can prove this hardening layer ran.
name_anchor = 'static constexpr const char *FIRMWARE_NAME = "TamaPoke Ultimate";'
text = rep(text, name_anchor, name_anchor + "\n" + MARKER, "final hardening marker")

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-final] Fixed transitions, identity, personality stability, daily caps, anniversary persistence, Evo Charm, game timers, Dex favorite, secrets and full backups")
