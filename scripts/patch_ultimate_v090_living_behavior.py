Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
PET_CPP = PROJECT / "generated" / "pet.cpp"
MARKER = "// ULTIMATE_V090_LIVING_BEHAVIOR_M2"


def fail(msg):
    print(f"[v0.9.0-ultimate-m2] ERROR: {msg}")
    env.Exit(1)


def replace_function(text, start_sig, next_sig, body, label):
    start = text.find(start_sig)
    if start < 0:
        fail(f"could not locate {label} start")
    end = text.find(next_sig, start)
    if end < 0:
        fail(f"could not locate {label} end")
    return text[:start] + body.rstrip() + "\n\n" + text[end:]


# ---------------------------------------------------------------------------
# Home personality, full mood set, time/biome/species-aware idle behavior.
# ---------------------------------------------------------------------------
text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-m2] living behavior already applied")
    Return()

if "// ULTIMATE_V090_PERSONALITY_MOOD" not in text:
    fail("Ultimate personality foundation must run first")

helpers = r'''

// ULTIMATE_V090_LIVING_BEHAVIOR_M2
// Expanded stable temperament. It is derived only from values already stored
// in the v0.7 journal, so old saves remain byte-for-byte compatible.
enum UltimateTrait : uint8_t {
  UT_PLAYFUL = 0,
  UT_BOLD,
  UT_GENTLE,
  UT_CALM,
  UT_CURIOUS,
  UT_STUBBORN,
  UT_LAZY,
  UT_AFFECTIONATE,
  UT_ENERGETIC,
  UT_SHY
};

enum UltimateDeepMood : uint8_t {
  UDM_CONTENT = 0,
  UDM_EXCITED,
  UDM_BORED,
  UDM_SLEEPY,
  UDM_HUNGRY,
  UDM_LONELY,
  UDM_PROUD,
  UDM_ANNOYED,
  UDM_SICK,
  UDM_CURIOUS,
  UDM_AFFECTIONATE,
  UDM_DIRTY
};

static int ultimateGeneHi() {
  return std::max((int)pet.geneAtk, std::max((int)pet.geneDef, (int)pet.geneSpe));
}

static int ultimateGeneLo() {
  return std::min((int)pet.geneAtk, std::min((int)pet.geneDef, (int)pet.geneSpe));
}

static uint8_t ultimateTraitSignature() {
  uint32_t sid = pet.speciesId > 0 ? (uint32_t)pet.speciesId : 1UL;
  return (uint8_t)(((uint32_t)pet.geneAtk * 3UL +
                    (uint32_t)pet.geneDef * 5UL +
                    (uint32_t)pet.geneSpe * 7UL + sid * 11UL) % 12UL);
}

static UltimateTrait ultimateTrait() {
  const int a = pet.geneAtk;
  const int d = pet.geneDef;
  const int s = pet.geneSpe;
  const int hi = ultimateGeneHi();
  const int lo = ultimateGeneLo();
  const uint8_t sig = ultimateTraitSignature();

  if (hi - lo <= 2) {
    switch (sig % 3) {
      case 0: return UT_AFFECTIONATE;
      case 1: return UT_CURIOUS;
      default: return UT_GENTLE;
    }
  }
  if (s >= 106 && s >= a + 2 && s >= d + 2) return UT_ENERGETIC;
  if (s >= a + 3 && s >= d + 2) return UT_PLAYFUL;
  if (a >= 106 && a >= d + 2 && a >= s + 2) return UT_BOLD;
  if (d >= 106 && d >= a + 2 && d >= s + 2) return UT_CALM;
  if (s <= 94 && (a >= 100 || d >= 100)) return UT_LAZY;
  if (hi <= 100 && lo <= 94) return UT_SHY;
  if (a + d >= (s * 2) + 5) return UT_STUBBORN;
  if (d + s >= (a * 2) + 4) return UT_GENTLE;

  switch (sig % 4) {
    case 0: return UT_CURIOUS;
    case 1: return UT_AFFECTIONATE;
    case 2: return UT_SHY;
    default: return UT_GENTLE;
  }
}

static const char* ultimateTraitName(UltimateTrait t) {
  switch (t) {
    case UT_PLAYFUL: return "PLAYFUL";
    case UT_BOLD: return "BOLD";
    case UT_GENTLE: return "GENTLE";
    case UT_CALM: return "CALM";
    case UT_CURIOUS: return "CURIOUS";
    case UT_STUBBORN: return "STUBBORN";
    case UT_LAZY: return "LAZY";
    case UT_AFFECTIONATE: return "AFFECTIONATE";
    case UT_ENERGETIC: return "ENERGETIC";
    case UT_SHY: return "SHY";
    default: return "CURIOUS";
  }
}

static UltimateDeepMood ultimateDeepMood() {
  if (pet.sleeping) return UDM_SLEEPY;

  int critical = 0;
  if (pet.fullness <= 8) ++critical;
  if (pet.energy <= 8) ++critical;
  if (pet.hygiene <= 8) ++critical;
  if (pet.joy <= 8) ++critical;
  if (critical >= 2 || (pet.hygiene <= 10 && pet.poops >= 3)) return UDM_SICK;

  if (pet.fullness <= 20) return UDM_HUNGRY;
  if (pet.hygiene <= 20) return UDM_DIRTY;
  if (pet.energy <= 22) return UDM_SLEEPY;

  // Low joy with a real established bond reads as loneliness; a newer Pokemon
  // with low joy is simply bored. This prevents every fresh hatch from being
  // labelled lonely before the player has had a chance to bond with it.
  if (pet.joy <= 24 && pet.bond >= 35) return UDM_LONELY;
  if (pet.joy <= 20) return UDM_BORED;
  if (pet.joy <= 34 && pet.fullness > 30 && pet.energy > 30 && pet.hygiene > 30)
    return UDM_ANNOYED;

  if (pet.showHeart() || (pet.bond >= 90 && pet.joy >= 60)) return UDM_AFFECTIONATE;
  if (pet.joy >= 84 && pet.energy >= 65) return UDM_EXCITED;
  if (pet.medals != 0 && pet.bond >= 70 && pet.joy >= 65) return UDM_PROUD;

  // Curious is a stable healthy mood window instead of per-frame randomness.
  uint32_t moodKey = pet.ageMinutes + (pet.speciesId > 0 ? pet.speciesId : 0);
  if (pet.joy >= 60 && pet.energy >= 50 &&
      (ultimateTrait() == UT_CURIOUS || ultimateTrait() == UT_SHY) &&
      (moodKey % 5UL) == 0)
    return UDM_CURIOUS;

  return UDM_CONTENT;
}

static const char* ultimateDeepMoodName(UltimateDeepMood m) {
  switch (m) {
    case UDM_CONTENT: return "CONTENT";
    case UDM_EXCITED: return "EXCITED";
    case UDM_BORED: return "BORED";
    case UDM_SLEEPY: return "SLEEPY";
    case UDM_HUNGRY: return "HUNGRY";
    case UDM_LONELY: return "LONELY";
    case UDM_PROUD: return "PROUD";
    case UDM_ANNOYED: return "ANNOYED";
    case UDM_SICK: return "SICK";
    case UDM_CURIOUS: return "CURIOUS";
    case UDM_AFFECTIONATE: return "AFFECTIONATE";
    case UDM_DIRTY: return "DIRTY";
    default: return "CONTENT";
  }
}

static bool ultimateSpeciesMoment(uint32_t now) {
  const int16_t d = pet.speciesId;
  if (d <= 0) return false;

  // A few unmistakable species-line behaviors. Every requested action still
  // falls back through chooseExisting/mon.has so incomplete sprite packs are
  // safe.
  if (d == 143) { // Snorlax: frequent little dozes.
    static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH};
    ultimateFlair(now, a, 3, 1800, 1700);
    return true;
  }
  if (d == 129) { // Magikarp: flops/hops.
    static const uint8_t a[] = {PMD_HOP, PMD_HOP, PMD_BREATH};
    ultimateFlair(now, a, 3, 850, 900);
    return true;
  }
  if (d == 25 || d == 26) { // Pikachu line: alert, bouncy checks.
    static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_POSE};
    ultimateFlair(now, a, 3, 850, 1050);
    return true;
  }
  if (d >= 92 && d <= 94) { // Gastly line: hovering/posing presence.
    static const uint8_t a[] = {PMD_POSE, PMD_BREATH, PMD_HOP};
    ultimateFlair(now, a, 3, 1100, 1300);
    return true;
  }

  // Biome-linked reactions make species feel at home in their habitat without
  // adding any background audio/ambience.
  uint8_t biome = DEX_TBL[d].biome;
  if (biome == 3) {
    static const uint8_t a[] = {PMD_ATTACK, PMD_POSE, PMD_BREATH};
    ultimateFlair(now, a, 3, 950, 1200);
    return true;
  }
  if (biome == 1 || biome == 5) {
    static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_BREATH};
    ultimateFlair(now, a, 3, 1000, 1200);
    return true;
  }
  return false;
}
'''

anchor = "static void updateAmbient(uint32_t now) {"
if anchor not in text:
    fail("Ultimate updateAmbient anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

new_ambient = r'''static void updateAmbient(uint32_t now) {
  if (!mon.loaded() || pet.isEgg() || pet.sleeping || pet.evolving() || pet.ceremony) return;

  uint32_t dt = now - lastMotion;
  lastMotion = now;
  if (petX < petTargetX) {
    int step = std::max(1, (int)(dt / 28));
    petX = std::min<int16_t>(petTargetX, petX + step);
  } else if (petX > petTargetX) {
    int step = std::max(1, (int)(dt / 28));
    petX = std::max<int16_t>(petTargetX, petX - step);
  }

  if (now < ambientUntil) return;

  UltimateDeepMood mood = ultimateDeepMood();

  // Care states always win over personality.
  if (mood == UDM_SICK) {
    static const uint8_t a[] = {PMD_HURT, PMD_BREATH, PMD_SIT};
    ultimateFlair(now, a, 3, 1800, 1500);
    return;
  }
  if (mood == UDM_HUNGRY || mood == UDM_DIRTY) {
    static const uint8_t a[] = {PMD_HURT, PMD_SIT, PMD_BREATH, PMD_IDLE};
    ultimateFlair(now, a, 4, 1400, 1400);
    return;
  }
  if (mood == UDM_SLEEPY) {
    static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH, PMD_IDLE};
    ultimateFlair(now, a, 4, 1800, 1800);
    return;
  }
  if (mood == UDM_LONELY) {
    // Walk toward the middle before a quiet check-in: the closest the current
    // sprite format can get to deliberately approaching the player.
    if (random(100) < 55 && ultimateWalk(now, 108, 132, 1100, 900)) return;
    static const uint8_t a[] = {PMD_NOD, PMD_BREATH, PMD_SIT};
    ultimateFlair(now, a, 3, 1200, 1200);
    return;
  }
  if (mood == UDM_ANNOYED) {
    static const uint8_t a[] = {PMD_ATTACK, PMD_POSE, PMD_SIT, PMD_BREATH};
    ultimateFlair(now, a, 4, 1000, 1300);
    return;
  }
  if (mood == UDM_BORED) {
    if (random(100) < 38 && ultimateWalk(now, 72, 168, 1200, 1200)) return;
    static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_SIT, PMD_BREATH};
    ultimateFlair(now, a, 4, 1100, 1300);
    return;
  }
  if (mood == UDM_AFFECTIONATE) {
    if (random(100) < 40 && ultimateWalk(now, 106, 134, 900, 800)) return;
    static const uint8_t a[] = {PMD_NOD, PMD_POSE, PMD_HOP, PMD_BREATH};
    ultimateFlair(now, a, 4, 850, 1000);
    return;
  }
  if (mood == UDM_PROUD) {
    static const uint8_t a[] = {PMD_POSE, PMD_ATTACK, PMD_NOD};
    ultimateFlair(now, a, 3, 1000, 1200);
    return;
  }
  if (mood == UDM_CURIOUS) {
    if (random(100) < 50 && ultimateWalk(now, 64, 176, 1050, 1100)) return;
    static const uint8_t a[] = {PMD_POSE, PMD_NOD, PMD_HOP, PMD_BREATH};
    ultimateFlair(now, a, 4, 950, 1100);
    return;
  }
  if (mood == UDM_EXCITED) {
    if (random(100) < 42 && ultimateWalk(now, 64, 176, 900, 1000)) return;
    static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_POSE, PMD_ATTACK};
    ultimateFlair(now, a, 4, 750, 950);
    return;
  }

  int r = random(100);
  int h = sceneHour();

  // Time-of-day reactions. At night calm/lazy/shy Pokemon may briefly doze;
  // energetic/playful Pokemon greet the morning with more movement.
  if ((h >= 20 || h < 6) && r < 18) {
    UltimateTrait t = ultimateTrait();
    if (t == UT_CALM || t == UT_LAZY || t == UT_SHY) {
      static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH};
      ultimateFlair(now, a, 3, 1700, 1600);
      return;
    }
  }
  if (h >= 6 && h < 10 && r < 18) {
    static const uint8_t a[] = {PMD_HOP, PMD_POSE, PMD_NOD};
    ultimateFlair(now, a, 3, 900, 1050);
    return;
  }

  // Occasional species/biome signature action.
  if (r >= 18 && r < 31 && ultimateSpeciesMoment(now)) return;

  UltimateTrait trait = ultimateTrait();
  r = random(100);
  switch (trait) {
    case UT_PLAYFUL:
      if (r < 44 && ultimateWalk(now, 62, 178, 950, 1150)) return;
      if (r < 88) { static const uint8_t a[] = {PMD_HOP,PMD_NOD,PMD_POSE,PMD_ATTACK,PMD_BREATH}; ultimateFlair(now,a,5,800,1050); return; }
      break;
    case UT_BOLD:
      if (r < 30 && ultimateWalk(now, 68, 172, 1150, 1250)) return;
      if (r < 84) { static const uint8_t a[] = {PMD_ATTACK,PMD_POSE,PMD_HOP,PMD_NOD}; ultimateFlair(now,a,4,900,1150); return; }
      break;
    case UT_GENTLE:
      if (r < 25 && ultimateWalk(now, 82, 158, 1450, 1450)) return;
      if (r < 76) { static const uint8_t a[] = {PMD_NOD,PMD_BREATH,PMD_SIT,PMD_POSE}; ultimateFlair(now,a,4,1250,1450); return; }
      break;
    case UT_CALM:
      if (r < 16 && ultimateWalk(now, 88, 152, 1650, 1700)) return;
      if (r < 66) { static const uint8_t a[] = {PMD_SIT,PMD_BREATH,PMD_NOD,PMD_IDLE}; ultimateFlair(now,a,4,1500,1800); return; }
      break;
    case UT_CURIOUS:
      if (r < 40 && ultimateWalk(now, 62, 178, 1050, 1250)) return;
      if (r < 87) { static const uint8_t a[] = {PMD_POSE,PMD_NOD,PMD_HOP,PMD_BREATH,PMD_SIT}; ultimateFlair(now,a,5,950,1250); return; }
      break;
    case UT_STUBBORN:
      if (r < 20 && ultimateWalk(now, 74, 166, 1450, 1450)) return;
      if (r < 78) { static const uint8_t a[] = {PMD_POSE,PMD_ATTACK,PMD_SIT,PMD_BREATH}; ultimateFlair(now,a,4,1150,1500); return; }
      break;
    case UT_LAZY:
      if (r < 10 && ultimateWalk(now, 94, 146, 1900, 1800)) return;
      if (r < 72) { static const uint8_t a[] = {PMD_SLEEP,PMD_SIT,PMD_BREATH,PMD_IDLE}; ultimateFlair(now,a,4,1800,2100); return; }
      break;
    case UT_AFFECTIONATE:
      if (r < 34 && ultimateWalk(now, 104, 136, 1050, 950)) return;
      if (r < 86) { static const uint8_t a[] = {PMD_NOD,PMD_POSE,PMD_HOP,PMD_BREATH}; ultimateFlair(now,a,4,900,1150); return; }
      break;
    case UT_ENERGETIC:
      if (r < 50 && ultimateWalk(now, 58, 182, 850, 1000)) return;
      if (r < 91) { static const uint8_t a[] = {PMD_HOP,PMD_ATTACK,PMD_POSE,PMD_NOD}; ultimateFlair(now,a,4,700,950); return; }
      break;
    case UT_SHY:
      if (r < 18 && ultimateWalk(now, 90, 150, 1600, 1700)) return;
      if (r < 72) { static const uint8_t a[] = {PMD_BREATH,PMD_SIT,PMD_NOD,PMD_POSE}; ultimateFlair(now,a,4,1450,1750); return; }
      break;
  }

  // A neutral sky-watch/stretch-like beat: PMD has no dedicated LOOK/STRETCH
  // action, so POSE/BREATH are the graceful safe equivalents across the pack.
  if (random(100) < 18) {
    petTargetX = random(2) ? 92 : 148;
    static const uint8_t sky[] = {PMD_POSE, PMD_BREATH};
    ultimateFlair(now, sky, 2, 1500, 1200);
    return;
  }

  ambientAction = PMD_IDLE;
  ambientUntil = now + (pet.bond >= 70 ? 1200 : 1700) + random(2200);
}'''
text = replace_function(text, "static void updateAmbient(uint32_t now) {",
                        "static uint8_t currentAction", new_ambient,
                        "Milestone 2 updateAmbient")

new_status = r'''static const char* statusMsg() {
  if (pet.sleeping) return "Zzz...";
  UltimateDeepMood m = ultimateDeepMood();
  if (m == UDM_SICK) return "I don't feel well...";
  if (m == UDM_HUNGRY) return "I'm hungry...";
  if (m == UDM_DIRTY) return "Bath time...";
  if (m == UDM_SLEEPY) return "So sleepy...";
  if (m == UDM_LONELY) return "Stay with me...";
  if (m == UDM_BORED) return "Play with me!";
  if (m == UDM_ANNOYED) return "Hmph...";
  if (pet.showHeart()) return "<3";

  static char state[31];
  snprintf(state, sizeof(state), "%s / %s",
           ultimateTraitName(ultimateTrait()),
           ultimateDeepMoodName(m));
  return state;
}'''
text = replace_function(text, "static const char* statusMsg() {",
                        "static void drawHeaderText", new_status,
                        "Milestone 2 statusMsg")

MAIN.write_text(text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# Personality also changes care-need rates slightly. This is intentionally
# subtle: traits feel different over time without turning one personality into
# an objectively bad roll. The same logic is used for live and offline decay.
# ---------------------------------------------------------------------------
pet_text = PET_CPP.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

rate_helpers = r'''

// ULTIMATE_V090_LIVING_BEHAVIOR_M2
static uint8_t ultimatePetTraitCode(const Pet &p) {
  const int a = p.geneAtk, d = p.geneDef, s = p.geneSpe;
  int hi = a > d ? a : d; if (s > hi) hi = s;
  int lo = a < d ? a : d; if (s < lo) lo = s;
  uint32_t sid = p.speciesId > 0 ? (uint32_t)p.speciesId : 1UL;
  uint8_t sig = (uint8_t)(((uint32_t)a * 3UL + (uint32_t)d * 5UL +
                           (uint32_t)s * 7UL + sid * 11UL) % 12UL);
  if (hi - lo <= 2) return (sig % 3 == 0) ? 7 : ((sig % 3 == 1) ? 4 : 2);
  if (s >= 106 && s >= a + 2 && s >= d + 2) return 8;
  if (s >= a + 3 && s >= d + 2) return 0;
  if (a >= 106 && a >= d + 2 && a >= s + 2) return 1;
  if (d >= 106 && d >= a + 2 && d >= s + 2) return 3;
  if (s <= 94 && (a >= 100 || d >= 100)) return 6;
  if (hi <= 100 && lo <= 94) return 9;
  if (a + d >= (s * 2) + 5) return 5;
  if (d + s >= (a * 2) + 4) return 2;
  return (sig % 4 == 0) ? 4 : ((sig % 4 == 1) ? 7 : ((sig % 4 == 2) ? 9 : 2));
}

static void ultimateNeedRates(const Pet &p, uint32_t minute,
                              uint8_t &foodDrop, uint8_t &energyDrop,
                              uint8_t &hygieneDrop, uint8_t &joyDrop) {
  foodDrop = 2; energyDrop = 1; hygieneDrop = 1; joyDrop = 1;
  switch (ultimatePetTraitCode(p)) {
    case 0: // playful: wants play a little more often and burns energy.
      if ((minute % 3UL) == 0) energyDrop = 2;
      if ((minute % 4UL) == 0) joyDrop = 2;
      break;
    case 1: // bold: steady mood, slightly higher appetite after activity.
      if ((minute % 5UL) == 0) foodDrop = 3;
      break;
    case 2: // gentle: cleanliness matters a touch more; mood is resilient.
      if ((minute % 4UL) == 0) hygieneDrop = 2;
      if ((minute % 3UL) == 0) joyDrop = 0;
      break;
    case 3: // calm: slower energy and joy drain.
      if ((minute % 2UL) == 0) energyDrop = 0;
      if ((minute % 2UL) == 0) joyDrop = 0;
      break;
    case 4: // curious: explores, so a small occasional energy cost.
      if ((minute % 4UL) == 0) energyDrop = 2;
      break;
    case 5: // stubborn: appetite is steady; boredom builds a little faster.
      if ((minute % 5UL) == 0) joyDrop = 2;
      break;
    case 6: // lazy: conserves energy but gets bored if left alone.
      if ((minute % 2UL) == 0) energyDrop = 0;
      if ((minute % 3UL) == 0) joyDrop = 2;
      break;
    case 7: // affectionate: social attention matters most.
      if ((minute % 3UL) == 0) joyDrop = 2;
      break;
    case 8: // energetic: activity burns food, but mood holds up well.
      if ((minute % 4UL) == 0) foodDrop = 3;
      if ((minute % 3UL) == 0) joyDrop = 0;
      break;
    case 9: // shy: quieter pace conserves energy and mood.
      if ((minute % 3UL) == 0) energyDrop = 0;
      if ((minute % 3UL) == 0) joyDrop = 0;
      break;
  }
}
'''

anchor_pet = "void Pet::setClock(uint32_t nowEpoch) {"
if anchor_pet not in pet_text:
    fail("pet.cpp setClock anchor")
pet_text = pet_text.replace(anchor_pet, rate_helpers + "\n" + anchor_pet, 1)

old_offline = '''    fullness = dropTo(fullness, 2, 15);
    energy = dropTo(energy, 1, 15);
    hygiene = dropTo(hygiene, 1, 15);
    joy = dropTo(joy, 1, 15);'''
new_offline = '''    uint8_t foodDrop, energyDrop, hygieneDrop, joyDrop;
    ultimateNeedRates(*this, ageMinutes, foodDrop, energyDrop, hygieneDrop, joyDrop);
    fullness = dropTo(fullness, foodDrop, 15);
    energy = dropTo(energy, energyDrop, 15);
    hygiene = dropTo(hygiene, hygieneDrop, 15);
    joy = dropTo(joy, joyDrop, 15);'''
if old_offline not in pet_text:
    fail("offline awake decay block")
pet_text = pet_text.replace(old_offline, new_offline, 1)

old_live_a = '''  fullness = clamp100(fullness - 2);
  energy = clamp100(energy - 1);'''
new_live_a = '''  uint8_t foodDrop, energyDrop, hygieneDrop, joyDrop;
  ultimateNeedRates(*this, ageMinutes, foodDrop, energyDrop, hygieneDrop, joyDrop);
  fullness = clamp100((int)fullness - foodDrop);
  energy = clamp100((int)energy - energyDrop);'''
if old_live_a not in pet_text:
    fail("live food/energy decay block")
pet_text = pet_text.replace(old_live_a, new_live_a, 1)

old_live_b = '''  hygiene = clamp100(hygiene - 1 - 4 * poops);'''
new_live_b = '''  hygiene = clamp100((int)hygiene - hygieneDrop - 4 * poops);'''
if old_live_b not in pet_text:
    fail("live hygiene decay")
pet_text = pet_text.replace(old_live_b, new_live_b, 1)

old_live_c = '''  int dJoy = -1;'''
new_live_c = '''  int dJoy = -(int)joyDrop;'''
if old_live_c not in pet_text:
    fail("live joy decay")
pet_text = pet_text.replace(old_live_c, new_live_c, 1)

PET_CPP.write_text(pet_text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-m2] Added full mood set, 10 traits, richer idle life, species/time reactions, and subtle trait-based need rates")
