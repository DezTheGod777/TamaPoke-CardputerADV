Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PERSISTENT_TIME_CYCLE"


def fail(msg):
    print(f"[v0.9.0-time-cycle] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-time-cycle] persistent time cycle already applied")
    Return()
if "// ULTIMATE_V090_SLEEP_ZZZ_ANIM" not in text:
    fail("sleep Z animation patch must run first")

old_scene = '''static int sceneHour() {
  struct tm ti;
  if (getLocalTime(&ti, 2)) return ti.tm_hour;
  return 13;
}'''
new_scene = '''// ULTIMATE_V090_PERSISTENT_TIME_CYCLE
static int sceneHour() {
  struct tm ti;

  // Prefer the live system clock whenever NTP/RTC time is available.
  if (getLocalTime(&ti, 2)) return ti.tm_hour;

  // On a reboot without an immediate network sync, keep the world on the
  // pet's last known real-world timeline instead of snapping back to 1 PM.
  // lastSeenEpoch is already persisted by the compatible v0.7 pet journal and
  // continues advancing during runtime, so the sky keeps cycling naturally.
  if (pet.lastSeenEpoch >= 1700000000UL) {
    time_t saved = (time_t)pet.lastSeenEpoch;
    if (localtime_r(&saved, &ti) != nullptr) return ti.tm_hour;
  }

  // Only brand-new installs that have never known real time use the neutral
  // daytime fallback until the first successful clock sync.
  return 13;
}'''
if old_scene not in text:
    fail("sceneHour function not found")
text = text.replace(old_scene, new_scene, 1)

# Set the configured timezone even before Wi-Fi/NTP connects so a persisted
# epoch converts to the same local hour immediately after reboot.
setup_anchor = '''  randomSeed((uint32_t)micros());
  audioBegin();'''
setup_new = '''  randomSeed((uint32_t)micros());
  audioBegin();

  // Keep persisted clock fallback in the configured local timezone even when
  // this boot has not connected to Wi-Fi yet.
  setenv("TZ", TAMAPOKE_TZ, 1);
  tzset();'''
if setup_anchor not in text:
    fail("setup timezone anchor not found")
text = text.replace(setup_anchor, setup_new, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-time-cycle] Sky now follows a persistent sunrise/day/sunset/night cycle across reboot")
