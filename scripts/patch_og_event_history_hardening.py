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
# beside the existing event-memory declaration. Other polish passes may insert
# declarations between this line and sampleBattery(), so do not depend on exact
# surrounding whitespace/order.
anchor = "static void pushEventMemory(const String &s);"
if anchor not in text:
    fail("could not locate pushEventMemory forward declaration")
if "static void noteEvent(const String &s);" not in text:
    text = text.replace(
        anchor,
        anchor + "\nstatic void noteEvent(const String &s);",
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

  // Keep the SD history bounded. Recent Events displays six entries, so once
  // the text log exceeds 4 KiB compact it to the six newest events.
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
