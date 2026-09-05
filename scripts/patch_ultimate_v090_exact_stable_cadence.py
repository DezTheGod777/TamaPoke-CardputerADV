Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_EXACT_STABLE_CADENCE"


def fail(msg):
    print(f"[v0.9.0-exact-cadence] ERROR: {msg}")
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
    print("[v0.9.0-exact-cadence] exact stable cadence already applied")
    Return()
if "// ULTIMATE_V090_ORIGINAL_PACING" not in text:
    fail("original pacing patch must run first")
if "// ULTIMATE_V090_PHASE3_IDLE_LIFE" not in text:
    fail("Phase 3 idle life must run first")

# The previous pacing pass only imposed minimum hold times. That still allowed
# Ultimate's mood/trait logic to choose active actions much more often than the
# stable firmware. This pass restores the complete stable Home cadence:
#   38% walk, 29% flair, 33% quiet idle
#   walk 1.8-3.499 s, flair 1.2-2.399 s, idle 1.8-4.399 s
# Personality/mood/species still choose WHICH flair happens, not how often the
# Pokemon changes actions.

old_walk_tail = '''  // Stable v0.8.5.4 walking cadence was about 1.8-3.5 seconds.
  // Ultimate may request slower behavior, but never faster than that baseline.
  uint32_t pacedBase = std::max<uint32_t>(baseMs, 1800UL);
  uint32_t pacedExtra = std::max<uint32_t>(extraMs, 1700UL);
  ambientUntil = now + pacedBase + random(pacedExtra + 1);'''
new_walk_tail = '''  (void)baseMs;
  (void)extraMs;
  // Exact stable v0.8.5.4 walk hold time.
  ambientUntil = now + 1800UL + random(1700UL);'''
if old_walk_tail not in text:
    fail("paced ultimateWalk tail")
text = text.replace(old_walk_tail, new_walk_tail, 1)

old_flair_tail = '''  // Stable flair actions were about 1.2-2.4 seconds. Preserve slower Ultimate
  // requests, but prevent energetic moods/species from cycling faster than the
  // original firmware's visual rhythm.
  uint32_t pacedBase = std::max<uint32_t>(baseMs, 1200UL);
  uint32_t pacedExtra = std::max<uint32_t>(extraMs, 1200UL);
  ambientUntil = now + pacedBase + random(pacedExtra + 1);'''
new_flair_tail = '''  (void)baseMs;
  (void)extraMs;
  // Exact stable v0.8.5.4 flair hold time.
  ambientUntil = now + 1200UL + random(1200UL);'''
if old_flair_tail not in text:
    fail("paced ultimateFlair tail")
text = text.replace(old_flair_tail, new_flair_tail, 1)

new_ambient = r'''static void updateAmbient(uint32_t now) {
  ultimateExpireIdleMoment(now);
  if (!mon.loaded() || pet.isEgg() || pet.sleeping || pet.evolving() || pet.ceremony) return;

  // Movement speed is byte-for-byte the same rule used by stable v0.8.5.4.
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

  // A new cadence slot begins. Visual Phase 3 moments are allowed only inside
  // that slot; they no longer create extra action-selection opportunities.
  ultimateIdleMoment = UIM_NONE;
  ultimateIdleMomentUntil = 0;

  UltimateDeepMood mood = ultimateDeepMood();
  UltimateTrait trait = ultimateTrait();
  int r = random(100);

  // Exact stable branch #1: 38% walk when walking sprites exist.
  if (r < 38 && (mon.has(PMD_WALKL) || mon.has(PMD_WALKR))) {
    petTargetX = random(82, 159);
    ambientAction = (petTargetX >= petX) ? PMD_WALKR : PMD_WALKL;
    if (!mon.has(ambientAction)) {
      ambientAction = mon.has(PMD_WALKR) ? PMD_WALKR : PMD_WALKL;
    }
    ambientUntil = now + 1800UL + random(1700UL);
    return;
  }

  // Exact stable branch #2: cumulative 67%, therefore 29% flair. Ultimate
  // keeps its richer mood/personality/species vocabulary only inside this slot.
  if (r < 67) {
    // Occasionally use a species/habitat-specific flair, but never more often
    // than the stable firmware's original flair slot permits.
    int special = random(100);
    if (special < 18 && ultimatePhase3SpeciesMoment(now)) return;
    if (special >= 18 && special < 30 && ultimateHabitatReaction(now)) return;
    if (special >= 30 && special < 38 && ultimateSpeciesMoment(now)) {
      ultimateSetIdleMoment(UIM_SPECIES, now, 1800);
      return;
    }

    if (mood == UDM_SICK) {
      static const uint8_t a[] = {PMD_HURT, PMD_BREATH, PMD_SIT};
      ultimateFlair(now, a, 3, 1200, 1200);
    } else if (mood == UDM_HUNGRY || mood == UDM_DIRTY) {
      static const uint8_t a[] = {PMD_HURT, PMD_SIT, PMD_BREATH, PMD_IDLE};
      ultimateFlair(now, a, 4, 1200, 1200);
    } else if (mood == UDM_SLEEPY) {
      ultimateSetIdleMoment(UIM_DOZE, now, 1800);
      static const uint8_t a[] = {PMD_SLEEP, PMD_SIT, PMD_BREATH, PMD_IDLE};
      ultimateFlair(now, a, 4, 1200, 1200);
    } else if (mood == UDM_LONELY || mood == UDM_AFFECTIONATE) {
      ultimateSetIdleMoment(UIM_APPROACH, now, 1800);
      static const uint8_t a[] = {PMD_NOD, PMD_POSE, PMD_BREATH, PMD_SIT};
      ultimateFlair(now, a, 4, 1200, 1200);
    } else if (mood == UDM_ANNOYED) {
      static const uint8_t a[] = {PMD_ATTACK, PMD_POSE, PMD_SIT, PMD_BREATH};
      ultimateFlair(now, a, 4, 1200, 1200);
    } else if (mood == UDM_EXCITED) {
      static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_POSE, PMD_ATTACK};
      ultimateFlair(now, a, 4, 1200, 1200);
    } else {
      switch (trait) {
        case UT_PLAYFUL: {
          static const uint8_t a[] = {PMD_HOP, PMD_NOD, PMD_POSE, PMD_BREATH};
          ultimateFlair(now, a, 4, 1200, 1200); break;
        }
        case UT_BOLD:
        case UT_STUBBORN: {
          static const uint8_t a[] = {PMD_ATTACK, PMD_POSE, PMD_NOD, PMD_BREATH};
          ultimateFlair(now, a, 4, 1200, 1200); break;
        }
        case UT_CALM:
        case UT_LAZY:
        case UT_SHY: {
          static const uint8_t a[] = {PMD_SIT, PMD_BREATH, PMD_NOD, PMD_IDLE};
          ultimateFlair(now, a, 4, 1200, 1200); break;
        }
        case UT_CURIOUS: {
          ultimateSetIdleMoment(random(100) < 50 ? UIM_SKYWATCH : UIM_STRETCH, now, 1800);
          static const uint8_t a[] = {PMD_POSE, PMD_NOD, PMD_BREATH, PMD_SIT};
          ultimateFlair(now, a, 4, 1200, 1200); break;
        }
        case UT_AFFECTIONATE: {
          ultimateSetIdleMoment(UIM_APPROACH, now, 1800);
          static const uint8_t a[] = {PMD_NOD, PMD_POSE, PMD_BREATH};
          ultimateFlair(now, a, 3, 1200, 1200); break;
        }
        case UT_ENERGETIC: {
          static const uint8_t a[] = {PMD_HOP, PMD_POSE, PMD_NOD, PMD_ATTACK};
          ultimateFlair(now, a, 4, 1200, 1200); break;
        }
        default: {
          static const uint8_t a[] = {PMD_POSE, PMD_NOD, PMD_BREATH};
          ultimateFlair(now, a, 3, 1200, 1200); break;
        }
      }
    }
    return;
  }

  // Exact stable branch #3: 33% quiet idle, 1.8-4.399 seconds.
  ambientAction = PMD_IDLE;
  ambientUntil = now + 1800UL + random(2600UL);
}'''

text = replace_function(text,
                        "static void updateAmbient(uint32_t now) {",
                        "static uint8_t currentAction",
                        new_ambient,
                        "Ultimate updateAmbient")

# Place an explicit marker beside the generated behavior for CI auditing.
text = text.replace("static void updateAmbient(uint32_t now) {",
                    MARKER + "\nstatic void updateAmbient(uint32_t now) {", 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-exact-cadence] Restored exact stable Home cadence: 38% walk / 29% flair / 33% idle with original timing ranges")
