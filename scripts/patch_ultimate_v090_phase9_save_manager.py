Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE9_SAVE_MANAGER"


def fail(msg):
    print(f"[v0.9.0-ultimate-p9] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p9] save manager already applied")
    Return()
if "// ULTIMATE_V090_PHASE8_DEEPER_POKEDEX" not in text:
    fail("Phase 8 must run first")

if "  DEX_STATS,\n  PLAY," not in text:
    fail("Phase 8 screen enum")
text = text.replace("  DEX_STATS,\n  PLAY,", "  DEX_STATS,\n  SAVE_MANAGER,\n  PLAY,", 1)

helpers = r'''

// ULTIMATE_V090_PHASE9_SAVE_MANAGER
static uint8_t ultimateSaveManagerSel = 0;
static String ultimateSaveManagerStatus = "Ready";
static int8_t ultimateRestoreArmedSlot = -1;
static uint32_t ultimateRestoreArmedUntil = 0;

static uint32_t ultimateFnvUpdate(uint32_t h, uint8_t b) {
  h ^= b; h *= 16777619UL; return h;
}

static bool ultimateValidateJournal(const char *path) {
  File f = SD.open(path, FILE_READ);
  if (!f || f.size() < 20) { if (f) f.close(); return false; }
  size_t sz = f.size();
  uint8_t b4[4];
  if (f.read(b4, 4) != 4) { f.close(); return false; }
  uint32_t magic = (uint32_t)b4[0] | ((uint32_t)b4[1] << 8) | ((uint32_t)b4[2] << 16) | ((uint32_t)b4[3] << 24);
  if (magic != 0x37504B54UL) { f.close(); return false; }
  f.seek(0);
  uint32_t h = 2166136261UL;
  for (size_t i = 0; i < sz - 4; ++i) {
    int c = f.read(); if (c < 0) { f.close(); return false; }
    h = ultimateFnvUpdate(h, (uint8_t)c);
  }
  uint8_t crcBytes[4];
  if (f.read(crcBytes, 4) != 4) { f.close(); return false; }
  f.close();
  uint32_t stored = (uint32_t)crcBytes[0] | ((uint32_t)crcBytes[1] << 8) |
                    ((uint32_t)crcBytes[2] << 16) | ((uint32_t)crcBytes[3] << 24);
  return h == stored;
}

static bool ultimateCopyFile(const char *src, const char *dst) {
  File in = SD.open(src, FILE_READ);
  if (!in) return false;
  SD.remove(dst);
  File out = SD.open(dst, FILE_WRITE);
  if (!out) { in.close(); return false; }
  uint8_t buf[256];
  bool ok = true;
  while (in.available()) {
    int n = in.read(buf, sizeof(buf));
    if (n <= 0) { ok = false; break; }
    if (out.write(buf, n) != (size_t)n) { ok = false; break; }
  }
  out.flush(); in.close(); out.close();
  return ok;
}

static String ultimateBackupPath(uint8_t slot, const char *suffix) {
  return String("/tamapoke_backup") + slot + suffix;
}

static bool ultimateBackupAux(uint8_t slot, const char *src, const char *suffix) {
  if (!SD.exists(src)) return true;
  String dst = ultimateBackupPath(slot, suffix);
  return ultimateCopyFile(src, dst.c_str());
}

static bool ultimateBackupSlotValid(uint8_t slot) {
  String a = ultimateBackupPath(slot, "_a.bin");
  String b = ultimateBackupPath(slot, "_b.bin");
  return ultimateValidateJournal(a.c_str()) || ultimateValidateJournal(b.c_str());
}

static void ultimateIntegrityCheck() {
  bool a = ultimateValidateJournal("/tamapoke_v7_a.bin");
  bool b = ultimateValidateJournal("/tamapoke_v7_b.bin");
  if (a && b) ultimateSaveManagerStatus = "LIVE SAVE: A + B VALID";
  else if (a || b) ultimateSaveManagerStatus = a ? "LIVE SAVE: A VALID, B BAD" : "LIVE SAVE: B VALID, A BAD";
  else ultimateSaveManagerStatus = "LIVE SAVE: BOTH INVALID";
  noteEvent(ultimateSaveManagerStatus);
  sfxPlay((a || b) ? SFX_TAP : SFX_DENY);
  dirty = true;
}

static void ultimateCreateBackup(uint8_t slot) {
  if (!sdReady || slot < 1 || slot > 3) return;
  bool va = ultimateValidateJournal("/tamapoke_v7_a.bin");
  bool vb = ultimateValidateJournal("/tamapoke_v7_b.bin");
  if (!va && !vb) {
    ultimateSaveManagerStatus = "Backup failed: live save invalid";
    sfxPlay(SFX_DENY); dirty = true; return;
  }
  String a = ultimateBackupPath(slot, "_a.bin");
  String b = ultimateBackupPath(slot, "_b.bin");
  bool okA = va ? ultimateCopyFile("/tamapoke_v7_a.bin", a.c_str()) : ultimateCopyFile("/tamapoke_v7_b.bin", a.c_str());
  bool okB = vb ? ultimateCopyFile("/tamapoke_v7_b.bin", b.c_str()) : ultimateCopyFile("/tamapoke_v7_a.bin", b.c_str());
  bool aux = true;
  aux &= ultimateBackupAux(slot, ULTIMATE_HOME_CFG_PATH, "_home.cfg");
  aux &= ultimateBackupAux(slot, ULTIMATE_ECON_CFG_PATH, "_economy.cfg");
  aux &= ultimateBackupAux(slot, ULT_GAME_CFG_PATH, "_games.cfg");
  aux &= ultimateBackupAux(slot, ULT_DAILY_CFG_PATH, "_daily.cfg");
  aux &= ultimateBackupAux(slot, ULT_DEX_HISTORY_PATH, "_dex.bin");
  bool valid = okA && okB && aux && ultimateBackupSlotValid(slot);
  ultimateSaveManagerStatus = valid ? String("Backup slot ") + slot + " saved" : String("Backup slot ") + slot + " FAILED";
  if (valid) noteEvent(ultimateSaveManagerStatus);
  sfxPlay(valid ? SFX_MEDAL : SFX_DENY);
  dirty = true;
}

static bool ultimateRestoreAux(uint8_t slot, const char *dst, const char *suffix) {
  String src = ultimateBackupPath(slot, suffix);
  if (!SD.exists(src.c_str())) return true;
  return ultimateCopyFile(src.c_str(), dst);
}

static void ultimateRestoreBackup(uint8_t slot) {
  if (!ultimateBackupSlotValid(slot)) {
    ultimateSaveManagerStatus = String("Slot ") + slot + " has no valid save";
    sfxPlay(SFX_DENY); dirty = true; return;
  }
  String ba = ultimateBackupPath(slot, "_a.bin");
  String bb = ultimateBackupPath(slot, "_b.bin");
  bool va = ultimateValidateJournal(ba.c_str());
  bool vb = ultimateValidateJournal(bb.c_str());
  const char *srcA = va ? ba.c_str() : bb.c_str();
  const char *srcB = vb ? bb.c_str() : ba.c_str();
  bool ok = ultimateCopyFile(srcA, "/tamapoke_v7_a.bin") && ultimateCopyFile(srcB, "/tamapoke_v7_b.bin");
  ok &= ultimateRestoreAux(slot, ULTIMATE_HOME_CFG_PATH, "_home.cfg");
  ok &= ultimateRestoreAux(slot, ULTIMATE_ECON_CFG_PATH, "_economy.cfg");
  ok &= ultimateRestoreAux(slot, ULT_GAME_CFG_PATH, "_games.cfg");
  ok &= ultimateRestoreAux(slot, ULT_DAILY_CFG_PATH, "_daily.cfg");
  ok &= ultimateRestoreAux(slot, ULT_DEX_HISTORY_PATH, "_dex.bin");
  if (!ok || (!ultimateValidateJournal("/tamapoke_v7_a.bin") && !ultimateValidateJournal("/tamapoke_v7_b.bin"))) {
    ultimateSaveManagerStatus = "Restore verification FAILED";
    sfxPlay(SFX_DENY); dirty = true; return;
  }
  ultimateSaveManagerStatus = String("Restored slot ") + slot + " - restarting";
  noteEvent(ultimateSaveManagerStatus);
  sfxPlay(SFX_MEDAL);
  ui.fillScreen(UI_CREAM); ui.setTextColor(UI_INK); ui.setTextSize(2);
  ui.drawCentreString("RESTORE COMPLETE", 120, 48, 1);
  ui.setTextSize(1); ui.drawCentreString("Restarting to load backup...", 120, 76, 1); ui.pushSprite(0,0);
  delay(1200);
  ESP.restart();
}

static void ultimateArmRestore(uint8_t slot) {
  uint32_t now = millis();
  if (ultimateRestoreArmedSlot == (int8_t)slot && now < ultimateRestoreArmedUntil) {
    ultimateRestoreArmedSlot = -1;
    ultimateRestoreBackup(slot);
    return;
  }
  ultimateRestoreArmedSlot = (int8_t)slot;
  ultimateRestoreArmedUntil = now + 5000;
  ultimateSaveManagerStatus = String("Press ENTER again: restore ") + slot;
  sfxPlay(SFX_DENY);
  dirty = true;
}

static void drawUltimateSaveManager() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK); ui.setTextSize(2);
  ui.drawCentreString("SAVE MANAGER", 120, 3, 1);
  const char *items[8] = {
    "CHECK LIVE INTEGRITY", "BACKUP SLOT 1", "RESTORE SLOT 1", "BACKUP SLOT 2",
    "RESTORE SLOT 2", "BACKUP SLOT 3", "RESTORE SLOT 3", "BACK"
  };
  int top = ultimateSaveManagerSel > 2 ? ultimateSaveManagerSel - 2 : 0;
  if (top > 2) top = 2;
  for (int row = 0; row < 6; ++row) {
    int i = top + row;
    int y = 22 + row * 15;
    bool sel = i == ultimateSaveManagerSel;
    ui.fillRoundRect(20, y, 200, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(20, y, 200, 13, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextSize(1); ui.setTextColor((i == 2 || i == 4 || i == 6) ? UI_BAD : UI_INK);
    ui.drawCentreString(items[i], 120, y + 4, 1);
  }
  ui.setTextColor(UI_INK); ui.setTextSize(1);
  String s = ultimateSaveManagerStatus; if (s.length() > 38) s = s.substring(0,38);
  ui.drawCentreString(s, 120, 115, 1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("Restore requires double ENTER", 120, 126, 1);
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text: fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Render save manager.
render_anchor = "      case DEX_STATS:  drawUltimateDexStats(); break;"
if render_anchor not in text: fail("Phase 8 render")
text = text.replace(render_anchor, render_anchor + "\n      case SAVE_MANAGER: drawUltimateSaveManager(); break;", 1)

# Input before DEX_STATS.
input_anchor = "  } else if (screen == DEX_STATS) {"
if input_anchor not in text: fail("Phase 8 input")
save_input = r'''  } else if (screen == SAVE_MANAGER) {
    if (upEdge) { ultimateSaveManagerSel = ultimateSaveManagerSel == 0 ? 7 : ultimateSaveManagerSel - 1; dirty = true; }
    if (downEdge) { ultimateSaveManagerSel = (ultimateSaveManagerSel + 1) % 8; dirty = true; }
    if (enterEdge || spaceEdge) {
      if (ultimateSaveManagerSel == 0) ultimateIntegrityCheck();
      else if (ultimateSaveManagerSel == 1) ultimateCreateBackup(1);
      else if (ultimateSaveManagerSel == 2) ultimateArmRestore(1);
      else if (ultimateSaveManagerSel == 3) ultimateCreateBackup(2);
      else if (ultimateSaveManagerSel == 4) ultimateArmRestore(2);
      else if (ultimateSaveManagerSel == 5) ultimateCreateBackup(3);
      else if (ultimateSaveManagerSel == 6) ultimateArmRestore(3);
      else { screen = HOME; dirty = true; }
    }
    if (escEdge || backEdge) { ultimateRestoreArmedSlot = -1; screen = HOME; dirty = true; }
'''
text = text.replace(input_anchor, save_input + input_anchor, 1)

# O opens save manager from Home.
key_anchor = "      } else if (c == 'j' && !pet.isEgg()) {"
if key_anchor not in text: fail("Phase 8 Home history key")
text = text.replace(key_anchor,
    "      } else if (c == 'o') {\n"
    "        ultimateSaveManagerSel = 0; ultimateSaveManagerStatus = \"Ready\"; screen = SAVE_MANAGER; dirty = true;\n"
    + key_anchor, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p9] Added CRC integrity check, three full backup slots, verified restore and recovery UI")
