Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_ORIGINAL_PACING"


def fail(msg):
    print(f"[v0.9.0-original-pacing] ERROR: {msg}")
    env.Exit(1)


def replace_once(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-original-pacing] original pacing already applied")
    Return()

if "// ULTIMATE_V090_LIVING_BEHAVIOR_M2" not in text:
    fail("Ultimate living behavior must run first")

# Keep all Ultimate personality/mood/species behavior, but restore the calmer
# cadence of the stable firmware. The PMD sprite frame durations themselves are
# untouched; only how frequently idle actions are selected/changed is bounded.
old_walk = '''static bool ultimateWalk(uint32_t now, int lo, int hi, uint32_t baseMs, uint32_t extraMs) {
  if (!mon.has(PMD_WALKL) && !mon.has(PMD_WALKR)) return false;
  petTargetX = (int16_t)random(lo, hi + 1);
  if (petTargetX == petX) petTargetX += petTargetX < hi ? 1 : -1;
  ambientAction = (petTargetX >= petX) ? PMD_WALKR : PMD_WALKL;
  if (!mon.has(ambientAction)) {
    ambientAction = mon.has(PMD_WALKR) ? PMD_WALKR : PMD_WALKL;
  }
  ambientUntil = now + baseMs + random(extraMs + 1);
  return true;
}'''
new_walk = '''static bool ultimateWalk(uint32_t now, int lo, int hi, uint32_t baseMs, uint32_t extraMs) {
  if (!mon.has(PMD_WALKL) && !mon.has(PMD_WALKR)) return false;
  petTargetX = (int16_t)random(lo, hi + 1);
  if (petTargetX == petX) petTargetX += petTargetX < hi ? 1 : -1;
  ambientAction = (petTargetX >= petX) ? PMD_WALKR : PMD_WALKL;
  if (!mon.has(ambientAction)) {
    ambientAction = mon.has(PMD_WALKR) ? PMD_WALKR : PMD_WALKL;
  }
  // Stable v0.8.5.4 walking cadence was about 1.8-3.5 seconds.
  // Ultimate may request slower behavior, but never faster than that baseline.
  uint32_t pacedBase = std::max<uint32_t>(baseMs, 1800UL);
  uint32_t pacedExtra = std::max<uint32_t>(extraMs, 1700UL);
  ambientUntil = now + pacedBase + random(pacedExtra + 1);
  return true;
}'''
text = replace_once(text, old_walk, new_walk, "ultimateWalk")

old_flair = '''static void ultimateFlair(uint32_t now, const uint8_t *choices, int count,
                          uint32_t baseMs, uint32_t extraMs) {
  ambientAction = chooseExisting(choices, count);
  ambientUntil = now + baseMs + random(extraMs + 1);
}'''
new_flair = '''static void ultimateFlair(uint32_t now, const uint8_t *choices, int count,
                          uint32_t baseMs, uint32_t extraMs) {
  ambientAction = chooseExisting(choices, count);
  // Stable flair actions were about 1.2-2.4 seconds. Preserve slower Ultimate
  // requests, but prevent energetic moods/species from cycling faster than the
  // original firmware's visual rhythm.
  uint32_t pacedBase = std::max<uint32_t>(baseMs, 1200UL);
  uint32_t pacedExtra = std::max<uint32_t>(extraMs, 1200UL);
  ambientUntil = now + pacedBase + random(pacedExtra + 1);
}'''
text = replace_once(text, old_flair, new_flair, "ultimateFlair")

# Phase 3 visual idle moments should not flick by more quickly than the old
# action cadence either. This keeps the new skywatch/stretch/doze/check-in
# effects while making them feel like the original TamaPoke pacing.
old_moment = '''static void ultimateSetIdleMoment(UltimateIdleMoment m, uint32_t now, uint32_t duration) {
  ultimateIdleMoment = m;
  ultimateIdleMomentUntil = now + duration;
}'''
if old_moment in text:
    new_moment = '''static void ultimateSetIdleMoment(UltimateIdleMoment m, uint32_t now, uint32_t duration) {
  ultimateIdleMoment = m;
  if (duration < 1800UL) duration = 1800UL;
  ultimateIdleMomentUntil = now + duration;
}'''
    text = text.replace(old_moment, new_moment, 1)

# Restore the stable quiet-idle range (roughly 1.8-4.4 sec). Previously high
# bond shortened this to ~1.2 sec, which was one of the reasons Ultimate could
# look noticeably faster/hyperactive.
old_idle = '  ambientAction = PMD_IDLE;\n  ambientUntil = now + (pet.bond >= 70 ? 1200 : 1700) + random(2200);'
new_idle = '  ambientAction = PMD_IDLE;\n  ambientUntil = now + 1800 + random(2600);'
text = replace_once(text, old_idle, new_idle, "Ultimate idle fallback")

# Marker is deliberately inserted near the behavior helpers for easy auditing.
text = text.replace("static bool ultimateWalk(uint32_t now, int lo, int hi, uint32_t baseMs, uint32_t extraMs) {",
                    MARKER + "\nstatic bool ultimateWalk(uint32_t now, int lo, int hi, uint32_t baseMs, uint32_t extraMs) {", 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-original-pacing] Restored stable idle/action pacing while keeping Ultimate behaviors")
