Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_VISIBLE_HUB"


def fail(msg):
    print(f"[v0.9.0-ultimate-hub] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-hub] visible Ultimate Hub already applied")
    Return()
if "// ULTIMATE_V090_SECOND_AUDIT" not in text:
    fail("second audit must run first")

# The earlier 12 phases were intentionally conservative about changing the
# stable Home layout. That made too many Ultimate systems shortcut-only and
# therefore easy to miss. Add one visible, centralized Hub without disturbing
# the v0.7 pet save journal.
text = rep(text,
    "  DEX_STATS,\n  SAVE_MANAGER,\n  PLAY,",
    "  DEX_STATS,\n  SAVE_MANAGER,\n  ULTIMATE_HUB,\n  PLAY,",
    "screen enum")

helpers = r'''

// ULTIMATE_V090_VISIBLE_HUB
static uint8_t ultimateHubSel = 0;

static void openUltimateHub() {
  ultimateHubSel = 0;
  screen = ULTIMATE_HUB;
  dirty = true;
  sfxPlay(SFX_TAP);
}

static void drawUltimateHub() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("ULTIMATE HUB", 120, 3, 1);
  ui.setTextSize(1);
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("v0.9.0  -  12 PHASES ACTIVE", 120, 19, 1);

  static const char *items[8] = {
    "HOME CUSTOMIZE",
    "INVENTORY / BAG",
    "POKE SHOP",
    "MINIGAMES",
    "DAILY LIFE",
    "POKEDEX HISTORY",
    "SAVE MANAGER",
    "BACK"
  };

  int top = 0;
  if (ultimateHubSel > 2) top = ultimateHubSel - 2;
  if (top > 3) top = 3;

  for (int row = 0; row < 5; ++row) {
    int i = top + row;
    if (i >= 8) break;
    int y = 34 + row * 17;
    bool sel = i == ultimateHubSel;
    ui.fillRoundRect(18, y, 204, 14, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(18, y, 204, 14, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextColor(UI_INK);
    ui.setTextSize(1);
    ui.drawCentreString(items[i], 120, y + 4, 1);
  }

  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.setTextSize(1);
  ui.drawCentreString("ARROWS + ENTER     ESC = HOME", 120, 122, 1);
}

static void drawUltimateHubBadge() {
  if (idleTerrarium || feedOpen || pet.isEgg()) return;
  // A small always-visible entry point so Ultimate no longer looks identical
  // to stable v0.8.5.4. It avoids the center evolution/farewell banner area.
  ui.fillRoundRect(190, 69, 47, 14, 4, C565(0xff,0xeb,0xb8));
  ui.drawRoundRect(190, 69, 47, 14, 4, UI_WARN);
  ui.setTextColor(UI_INK);
  ui.setTextSize(1);
  ui.drawCentreString("H HUB", 213, 73, 1);
}
'''

anchor = "static void drawHome(uint32_t now) {"
if anchor not in text:
    fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Make the Hub visibly reachable from Home.
home_anchor = "  drawUltimateDailyFx(now);\n  drawBathFx(now);"
if home_anchor not in text:
    fail("Home daily/bath anchor")
text = text.replace(home_anchor,
    "  drawUltimateDailyFx(now);\n  drawUltimateHubBadge();\n  drawBathFx(now);",
    1)

# Render the Hub.
render_anchor = "      case SAVE_MANAGER: drawUltimateSaveManager(); break;"
if render_anchor not in text:
    fail("save manager render anchor")
text = text.replace(render_anchor,
    render_anchor + "\n      case ULTIMATE_HUB: drawUltimateHub(); break;",
    1)

# Dedicated Hub navigation. Each option opens an already-implemented phase.
input_anchor = "  } else if (screen == SAVE_MANAGER) {"
if input_anchor not in text:
    fail("save manager input anchor")
hub_input = r'''  } else if (screen == ULTIMATE_HUB) {
    if (upEdge) {
      ultimateHubSel = ultimateHubSel == 0 ? 7 : ultimateHubSel - 1;
      dirty = true;
    }
    if (downEdge) {
      ultimateHubSel = (ultimateHubSel + 1) % 8;
      dirty = true;
    }
    if (enterEdge || spaceEdge) {
      if (ultimateHubSel == 0) {
        ultimateCustomizeSel = 0; screen = CUSTOMIZE;
      } else if (ultimateHubSel == 1) {
        ultimateInventorySel = 0; screen = INVENTORY;
      } else if (ultimateHubSel == 2) {
        ultimateShopSel = 0; screen = SHOP;
      } else if (ultimateHubSel == 3) {
        ultimateGameMenuSel = 0; screen = GAMES;
      } else if (ultimateHubSel == 4) {
        screen = DAILY;
      } else if (ultimateHubSel == 5) {
        if (!pet.isEgg()) {
          dexCursor = pet.speciesId;
          ultimateDexStatsPage = 0;
          screen = DEX_STATS;
        } else {
          sfxPlay(SFX_DENY);
          say("Hatch the egg first");
        }
      } else if (ultimateHubSel == 6) {
        ultimateSaveManagerSel = 0;
        ultimateSaveManagerStatus = "Ready";
        screen = SAVE_MANAGER;
      } else {
        screen = HOME;
      }
      dirty = true;
    }
    if (escEdge || backEdge) {
      screen = HOME;
      dirty = true;
    }
'''
text = text.replace(input_anchor, hub_input + input_anchor, 1)

# H opens the Hub from Home. Use H instead of U so the existing hidden
# "ultimate" secret word remains typeable.
key_anchor = "    if (screen == HOME && !feedOpen) {\n      if (c == 'b') ultimateSecretArrowCode(4);"
if key_anchor not in text:
    fail("Home printable branch")
text = text.replace(key_anchor,
    "    if (screen == HOME && !feedOpen) {\n"
    "      if (c == 'b') ultimateSecretArrowCode(4);\n"
    "      if (c == 'h') { openUltimateHub(); continue; }",
    1)

# Controls screen should say where the new visible entry point is.
text = text.replace('    "M: games   Y: daily   E: evolve",',
                    '    "H: Ultimate Hub   M: games",', 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-hub] Added visible Home badge and centralized Ultimate Hub for all major phase systems")
