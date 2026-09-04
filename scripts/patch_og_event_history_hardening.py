Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// OG_EVENT_HISTORY_HARDEN_RC5"


def fail(msg):
    print(f"[v0.8.5.4-rc5] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.8.5.4-rc5] event history hardening already applied")
    Return()

# sampleBattery() runs before noteEvent() is defined. Forward-declare noteEvent
# so low-battery notifications can be written to the same persistent history.
anchor = "static void pushEventMemory(const String &s);\n\nstatic void sampleBattery(bool force = false) {"
if anchor not in text:
    fail("could not locate battery/event forward declaration anchor")
text = text.replace(
    anchor,
    "static void pushEventMemory(const String &s);\n"
    "static void noteEvent(const String &s);\n\n"
    "static void sampleBattery(bool force = false) {",
    1,
)

# Persist the low-battery event instead of keeping it RAM-only.
old_low = '    pushEventMemory("Low battery");'
if old_low not in text:
    fail("could not locate low battery event")
text = text.replace(old_low, '    noteEvent("Low battery");', 1)

old_note = r'''static void noteEvent(const String &s) {
  pushEventMemory(s);
  if (!sdReady) return;
  File f = SD.open(EVENT_LOG_PATH, FILE_APPEND);
  if (!f) return;
  f.println(s);
  f.close();
}'''

new_note = r'''// OG_EVENT_HISTORY_HARDEN_RC5
static void noteEvent(const String &s) {
  pushEventMemory(s);
  if (!sdReady) return;

  // Keep the SD history bounded. Recent Events only displays six entries, so
  // once the text log exceeds 4 KiB we compact it to the six newest events.
  // This avoids an event file that grows forever over months of pet use.
  size_t existing = 0;
  File probe = SD.open(EVENT_LOG_PATH, FILE_READ);
  if (probe) {
    existing = probe.size();
    probe.close();
  }

  if (existing > 4096) {
    File out = SD.open(EVENT_LOG_PATH, FILE_WRITE);
    if (!out) return;
    for (int i = (int)recentEventCount - 1; i >= 0; --i) {
      if (recentEvents[i].length()) out.println(recentEvents[i]);
    }
    out.close();
    return;
  }

  File f = SD.open(EVENT_LOG_PATH, FILE_APPEND);
  if (!f) return;
  f.println(s);
  f.close();
}'''

if old_note not in text:
    fail("could not locate noteEvent implementation")
text = text.replace(old_note, new_note, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.8.5.4-rc5] Persistent low-battery events + bounded Recent Events log enabled")
