Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PERSONALITY_MOOD"


def fail(msg):
    print(f"[v0.9.0-ultimate] ERROR: {msg}")
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
    print("[v0.9.0-ultimate] personality/mood foundation already applied")
    Return()

if "// OG_HOME_HUD_ICON_FIX" not in text:
    fail("stable Home HUD fix must run before Ultimate v0.9.0")

# Identify this branch on-device without changing the v0.7 pet save journal.
text = text.replace(
    'static constexpr const char *FIRMWARE_VERSION = "v0.8.5.4";',
    'static constexpr const char *FIRMWARE_VERSION = "v0.9.0 ULTIMATE";',
    1,
)
text = text.replace(
    'static constexpr const char *FIRMWARE_NAME = "TamaPoke ADV";',
    'static constexpr const char *FIRMWARE_NAME = "TamaPoke Ultimate";',
    1,
)

helpers = r'''
// ULTIMATE_V090_PERSONALITY_MOOD
// Personality is derived from the Pokemon's permanent hatch genes. Those
// values already live in the v0.7 save journal, so personality survives
// restarts and evolution without changing save compatibility.
enum UltimatePersonality : uint8_t {
  UP_PLAYFUL = 0,
  UP_BOLD,
  UP_GENTLE,
  UP_CALM,
  UP_CURIOUS,
  UP_STUBBORN
};

enum UltimateMood : uint8_t {
  UM_CONTENT = 0,
  UM_EXCITED,
  UM_HUNGRY,
  UM_SLEEPY,
  UM_BORED,
  UM_DIRTY,
  UM_AFFECTIONATE,
  UM_PROUD
};

static UltimatePersonality ultimatePersonality() {
  const int a = pet.geneAtk;
  const int d = pet.geneDef;
  const int s = pet.geneSpe;
  const int hi = std::max(a, std::max(d, s));
  const int lo = std::min(a, std::min(d, s));

  // Near-balanced genes produce the social/curious personalities instead of
  // arbitrarily picking whichever stat won by one point.
  if (hi - lo <= 2) {
    return ((a + d + s) & 1) ? UP_CURIOUS : UP_GENTLE;
  }
  if (s >= a + 3 && s >= d + 2) return UP_PLAYFUL;
  if (a >= d + 3 && a >= s + 2) return UP_BOLD;
  if (d >= a + 3 && d >= s + 2) return UP_CALM;
  if (a + d >= (s * 2) + 4) return UP_STUBBORN;
  if (d + s >= (a * 2) + 3) return UP_GENTLE;
  return UP_CURIOUS;
}

static const char* ultimatePersonalityName(UltimatePersonality p) {
  switch (p) {
    case UP_PLAYFUL: return "PLAYFUL";
    case UP_BOLD: return "BOLD";
    case UP_GENTLE: return "GENTLE";
    case UP_CALM: return "CALM";
    case UP_CURIOUS: return "CURIOUS";
    case UP_STUBBORN: return "STUBBORN";
    default: return "CURIOUS";
  }
}

static UltimateMood ultimateMood() {
  if (pet.sleeping) return UM_SLEEPY;
  if (pet.eating()) return UM_EXCITED;
  if (pet.fullness <= 20) return UM_HUNGRY;
  if (pet.hygiene <= 20) return UM_DIRTY;
  if (pet.energy <= 22) return UM_SLEEPY;
  if (pet.joy <= 20) return UM_BORED;
  if (pet.showHeart() || pet.bond >= 90) return UM_AFFECTIONATE;
  if (pet.joy >= 82 && pet.energy >= 65) return UM_EXCITED;
  if (pet.bond >= 70 && pet.medals != 0) return UM_PROUD;
  return UM_CONTENT;
}

static const char* ultimateMoodName(UltimateMood m) {
  switch (m) {
    case UM_CONTENT: return "CONTENT";
    case UM_EXCITED: return "EXCITED";
    case UM_HUNGRY: return "HUNGRY";
    case UM_SLEEPY: return "SLEEPY";
    case UM_BORED: return "BORED";
    case UM_DIRTY: return "DIRTY";
    case UM_AFFECTIONATE: return "AFFECTIONATE";
    case UM_PROUD: return "PROUD";
    default: return "CONTENT";
  }
}

static bool ultimateWalk(uint32_t now, int lo, int hi, uint32_t baseMs, uint32_t extraMs) {
  if (!mon.has(PMD_WALKL) && !mon.has(PMD_WALKR)) return false;
  petTargetX = (int16_t)random(lo, hi + 1);
  if (petTargetX == petX) petTargetX += petTargetX < hi ? 1 : -1;
  ambientAction = (petTargetX >= petX) ? PMD_WALKR : PMD_WALKL;
  if (!mon.has(ambientAction)) {
    ambientAction = mon.has(PMD_WALKR) ? PMD_WALKR : PMD_WALKL;
  }
  ambientUntil = now + baseMs + random(extraMs + 1);
  return true;
}

static void ultimateFlair(uint32_t now, const uint8_t *choices, int count,
                          uint32_t baseMs, uint32_t extraMs) {
  ambientAction = chooseExisting(choices, count);
  ambientUntil = now + baseMs + random(extraMs + 1);
}
'''

anchor = "static void updateAmbient(uint32_t now) {"
if anchor not in text:
    fail("updateAmbient anchor")
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

  UltimateMood mood = ultimateMood();

  // Needs always outrank personality so the Pokemon visibly asks for care.
  if (mood == UM_SLEEPY) {
    static const uint8_t tired[] = {PMD_SIT, PMD_BREATH, PMD_IDLE};
    ultimateFlair(now, tired, 3, 1800, 1700);
    return;
  }
  if (mood == UM_HUNGRY || mood == UM_DIRTY || mood == UM_BORED) {
    static const uint8_t unhappy[] = {PMD_HURT, PMD_SIT, PMD_BREATH, PMD_IDLE};
    ultimateFlair(now, unhappy, 4, 1400, 1500);
    return;
  }
  if (mood == UM_AFFECTIONATE) {
    static const uint8_t loving[] = {PMD_NOD, PMD_POSE, PMD_HOP, PMD_BREATH};
    ultimateFlair(now, loving, 4, 900, 1100);
    return;
  }

  UltimatePersonality personality = ultimatePersonality();
  int r = random(100);

  switch (personality) {
    case UP_PLAYFUL: {
      if (r < 40 && ultimateWalk(now, 66, 174, 1050, 1250)) return;
      if (r < 86) {
        static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_POSE, PMD_ATTACK, PMD_BREATH};
        ultimateFlair(now, a, 5, 800, 1100);
        return;
      }
      break;
    }

    case UP_BOLD: {
      if (r < 27 && ultimateWalk(now, 70, 170, 1250, 1350)) return;
      if (r < 82) {
        static const uint8_t a[] = {PMD_ATTACK, PMD_POSE, PMD_HOP, PMD_NOD};
        ultimateFlair(now, a, 4, 900, 1250);
        return;
      }
      break;
    }

    case UP_GENTLE: {
      if (r < 24 && ultimateWalk(now, 82, 158, 1500, 1600)) return;
      if (r < 72) {
        static const uint8_t a[] = {PMD_NOD, PMD_BREATH, PMD_SIT, PMD_POSE};
        ultimateFlair(now, a, 4, 1300, 1500);
        return;
      }
      break;
    }

    case UP_CALM: {
      if (r < 16 && ultimateWalk(now, 88, 152, 1700, 1800)) return;
      if (r < 61) {
        static const uint8_t a[] = {PMD_SIT, PMD_BREATH, PMD_NOD, PMD_IDLE};
        ultimateFlair(now, a, 4, 1600, 1900);
        return;
      }
      break;
    }

    case UP_CURIOUS: {
      if (r < 36 && ultimateWalk(now, 68, 172, 1200, 1450)) return;
      if (r < 82) {
        static const uint8_t a[] = {PMD_POSE, PMD_NOD, PMD_HOP, PMD_BREATH, PMD_SIT};
        ultimateFlair(now, a, 5, 1000, 1400);
        return;
      }
      break;
    }

    case UP_STUBBORN: {
      if (r < 20 && ultimateWalk(now, 76, 164, 1500, 1550)) return;
      if (r < 74) {
        static const uint8_t a[] = {PMD_POSE, PMD_ATTACK, PMD_SIT, PMD_BREATH};
        ultimateFlair(now, a, 4, 1200, 1600);
        return;
      }
      break;
    }
  }

  ambientAction = PMD_IDLE;
  // High bond makes even quiet personalities check in a little more often.
  uint32_t idleBase = pet.bond >= 70 ? 1250 : 1750;
  ambientUntil = now + idleBase + random(2200);
}'''

text = replace_function(
    text,
    "static void updateAmbient(uint32_t now) {",
    "static uint8_t currentAction",
    new_ambient,
    "Ultimate updateAmbient",
)

new_status = r'''static const char* statusMsg() {
  if (pet.sleeping) return "Zzz...";
  UltimateMood m = ultimateMood();
  if (m == UM_HUNGRY) return "I'm hungry...";
  if (m == UM_DIRTY) return "Bath time...";
  if (m == UM_SLEEPY) return "So sleepy...";
  if (m == UM_BORED) return "Play with me!";
  if (pet.showHeart()) return "<3";

  // During healthy play, the Home header exposes both the permanent
  // personality and the live mood instead of always saying only "Happy".
  static char state[30];
  snprintf(state, sizeof(state), "%s / %s",
           ultimatePersonalityName(ultimatePersonality()),
           ultimateMoodName(m));
  return state;
}'''

text = replace_function(
    text,
    "static const char* statusMsg() {",
    "static void drawHeaderText",
    new_status,
    "Ultimate statusMsg",
)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate] Added persistent gene-based personality, live moods, and personality-driven idle behavior")
