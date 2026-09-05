Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_PHASE5_INVENTORY_SHOP"


def fail(msg):
    print(f"[v0.9.0-ultimate-p5] ERROR: {msg}")
    env.Exit(1)


def rep(text, old, new, label):
    if old not in text:
        fail(f"could not locate {label}")
    return text.replace(old, new, 1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-ultimate-p5] inventory/shop already applied")
    Return()
if "// ULTIMATE_V090_PHASE4_HOME_CUSTOMIZATION" not in text:
    fail("Phase 4 must run first")

# Add dedicated economy screens.
if "  CUSTOMIZE,\n  PLAY," not in text:
    fail("Phase 4 screen enum")
text = text.replace("  CUSTOMIZE,\n  PLAY,",
                    "  CUSTOMIZE,\n  INVENTORY,\n  SHOP,\n  PLAY,", 1)

helpers = r'''

// ULTIMATE_V090_PHASE5_INVENTORY_SHOP
static const char *ULTIMATE_ECON_CFG_PATH = "/tamapoke_ultimate_economy.cfg";
static constexpr uint8_t ULT_ITEM_COUNT = 10;
static uint16_t ultimateCoins = 25;
static uint8_t ultimateItems[ULT_ITEM_COUNT] = {0};
static uint8_t ultimateInventorySel = 0;
static uint8_t ultimateShopSel = 0;

static const char *ULT_ITEM_NAME[ULT_ITEM_COUNT] = {
  "RED BERRY", "BLUE BERRY", "GREEN BERRY", "TREAT", "MEDICINE",
  "EVO CHARM", "TOY BOX", "DECOR BOX", "STYLE TICKET", "LUCKY CHARM"
};
static const uint16_t ULT_ITEM_PRICE[ULT_ITEM_COUNT] = {3,3,3,5,8,18,14,14,12,20};

struct __attribute__((packed)) UltimateEconomyFile {
  uint32_t magic;
  uint8_t version;
  uint16_t coins;
  uint8_t items[ULT_ITEM_COUNT];
  uint8_t reserved[3];
  uint32_t crc;
};

static uint32_t ultimateEconomyCrc(const UltimateEconomyFile &c) {
  return displayCfgHash(reinterpret_cast<const uint8_t*>(&c),
                        offsetof(UltimateEconomyFile, crc));
}

static void saveUltimateEconomy() {
  if (!sdReady) return;
  UltimateEconomyFile c{};
  c.magic = 0x35454354UL; // "TCE5"
  c.version = 1;
  c.coins = ultimateCoins;
  memcpy(c.items, ultimateItems, sizeof(c.items));
  c.crc = ultimateEconomyCrc(c);
  SD.remove(ULTIMATE_ECON_CFG_PATH);
  File f = SD.open(ULTIMATE_ECON_CFG_PATH, FILE_WRITE);
  if (!f) return;
  f.write(reinterpret_cast<const uint8_t*>(&c), sizeof(c));
  f.flush();
  f.close();
}

static void loadUltimateEconomy() {
  if (!sdReady) return;
  File f = SD.open(ULTIMATE_ECON_CFG_PATH, FILE_READ);
  if (!f || f.size() != sizeof(UltimateEconomyFile)) {
    if (f) f.close();
    saveUltimateEconomy();
    return;
  }
  UltimateEconomyFile c{};
  size_t got = f.read(reinterpret_cast<uint8_t*>(&c), sizeof(c));
  f.close();
  if (got != sizeof(c) || c.magic != 0x35454354UL || c.version != 1 ||
      ultimateEconomyCrc(c) != c.crc) return;
  ultimateCoins = c.coins;
  memcpy(ultimateItems, c.items, sizeof(ultimateItems));
}

static void ultimateAwardCoins(uint16_t amount) {
  if (!amount) return;
  uint32_t next = (uint32_t)ultimateCoins + amount;
  ultimateCoins = (uint16_t)(next > 9999 ? 9999 : next);
  saveUltimateEconomy();
}

static bool ultimateBuyItem(uint8_t item) {
  if (item >= ULT_ITEM_COUNT) return false;
  uint16_t price = ULT_ITEM_PRICE[item];
  if (ultimateCoins < price || ultimateItems[item] >= 99) {
    sfxPlay(SFX_DENY);
    return false;
  }
  ultimateCoins -= price;
  ultimateItems[item]++;
  saveUltimateEconomy();
  sfxPlay(SFX_TAP);
  dirty = true;
  return true;
}

static uint8_t ultAdd100(uint8_t v, int n) {
  int x = (int)v + n;
  return (uint8_t)(x > 100 ? 100 : (x < 0 ? 0 : x));
}

static bool ultimateUseItem(uint8_t item) {
  if (item >= ULT_ITEM_COUNT || ultimateItems[item] == 0) {
    sfxPlay(SFX_DENY);
    return false;
  }
  if (item <= 4 && pet.isEgg()) {
    sfxPlay(SFX_DENY);
    say("Hatch the egg first");
    return false;
  }

  bool used = true;
  if (item <= 2) {
    if (pet.sleeping) used = false;
    else {
      pet.feedBerry(item);
      triggerAction(PMD_EAT, 2200);
      sfxPlay(SFX_EAT);
    }
  } else if (item == 3) {
    if (pet.sleeping) used = false;
    else {
      pet.feedCandy();
      triggerAction(PMD_EAT, 2200);
      sfxPlay(SFX_EAT);
    }
  } else if (item == 4) {
    pet.fullness = ultAdd100(pet.fullness, 18);
    pet.joy = ultAdd100(pet.joy, 22);
    pet.energy = ultAdd100(pet.energy, 28);
    pet.hygiene = ultAdd100(pet.hygiene, 35);
    pet.poops = 0;
    sfxPlay(SFX_HEART);
    say("Feeling better!");
  } else if (item == 5) {
    // Evolutionary item: it intentionally respects TamaPoke's existing
    // evolution requirements and opens the normal confirmation/animation.
    if (!pet.wantEvolveButton()) used = false;
    else {
      dialogKind = DLG_EVOLVE;
      dialogSel = 0;
      screen = DIALOG;
      sfxPlay(SFX_TAP);
    }
  } else if (item == 6) {
    ultimateToy = 3; // shop-exclusive shortcut to the plush home toy
    saveUltimateHomeConfig();
    say("Plush placed!");
    sfxPlay(SFX_TAP);
  } else if (item == 7) {
    ultimateDecor = 3; // lantern
    saveUltimateHomeConfig();
    say("Lantern placed!");
    sfxPlay(SFX_TAP);
  } else if (item == 8) {
    ultimatePlant = 2;
    ultimateBed = 2;
    saveUltimateHomeConfig();
    say("Home styled!");
    sfxPlay(SFX_TAP);
  } else if (item == 9) {
    if (pet.isEgg()) used = false;
    else {
      pet.joy = ultAdd100(pet.joy, 18);
      pet.energy = ultAdd100(pet.energy, 12);
      pet.bond = ultAdd100(pet.bond, 3);
      sfxPlay(SFX_HEART);
      say("Lucky boost!");
    }
  }

  if (!used) {
    sfxPlay(SFX_DENY);
    say(item == 5 ? "Evolution not ready" : "Can't use that now");
    return false;
  }
  ultimateItems[item]--;
  saveUltimateEconomy();
  dirty = true;
  return true;
}

static void drawUltimateInventory() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("INVENTORY", 120, 4, 1);
  char money[24];
  snprintf(money, sizeof(money), "%u COINS", ultimateCoins);
  ui.setTextSize(1);
  ui.setTextColor(UI_WARN);
  ui.drawRightString(money, 228, 7, 1);

  int top = ultimateInventorySel > 2 ? ultimateInventorySel - 2 : 0;
  if (top > ULT_ITEM_COUNT - 6) top = ULT_ITEM_COUNT - 6;
  for (int row = 0; row < 6; ++row) {
    int i = top + row;
    int y = 24 + row * 16;
    bool sel = i == ultimateInventorySel;
    ui.fillRoundRect(15, y, 210, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(15, y, 210, 13, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextColor(UI_INK);
    ui.drawString(ULT_ITEM_NAME[i], 21, y + 4);
    char count[8];
    snprintf(count, sizeof(count), "x%u", ultimateItems[i]);
    ui.drawRightString(count, 217, y + 4, 1);
  }
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ENTER USE   K SHOP   ESC HOME", 120, 123, 1);
}

static void drawUltimateShop() {
  ui.fillScreen(UI_CREAM);
  ui.setTextColor(UI_INK);
  ui.setTextSize(2);
  ui.drawCentreString("POKE SHOP", 120, 4, 1);
  char money[24];
  snprintf(money, sizeof(money), "%u COINS", ultimateCoins);
  ui.setTextSize(1);
  ui.setTextColor(UI_WARN);
  ui.drawRightString(money, 228, 7, 1);

  int top = ultimateShopSel > 2 ? ultimateShopSel - 2 : 0;
  if (top > ULT_ITEM_COUNT - 6) top = ULT_ITEM_COUNT - 6;
  for (int row = 0; row < 6; ++row) {
    int i = top + row;
    int y = 24 + row * 16;
    bool sel = i == ultimateShopSel;
    ui.fillRoundRect(15, y, 210, 13, 4, sel ? C565(0xff,0xeb,0xb8) : UI_WHITE);
    ui.drawRoundRect(15, y, 210, 13, 4, sel ? UI_WARN : UI_TRACK);
    ui.setTextColor(UI_INK);
    ui.drawString(ULT_ITEM_NAME[i], 21, y + 4);
    char price[12];
    snprintf(price, sizeof(price), "%uC", ULT_ITEM_PRICE[i]);
    ui.drawRightString(price, 217, y + 4, 1);
  }
  ui.setTextColor(C565(0x6d,0x6b,0x68));
  ui.drawCentreString("ENTER BUY   V BAG   ESC HOME", 120, 123, 1);
}
'''

# Insert economy helpers after Phase 4 helper area and before drawHome.
anchor = "static void drawHome(uint32_t now) {"
if anchor not in text:
    fail("drawHome anchor")
text = text.replace(anchor, helpers + "\n" + anchor, 1)

# Load economy with the other independent Ultimate configs.
text = rep(text,
    "  loadUltimateHomeConfig();\n  displayLastActivity = millis();",
    "  loadUltimateHomeConfig();\n  loadUltimateEconomy();\n  displayLastActivity = millis();",
    "setup economy load")

# Currency from actual game performance and ordinary care.
text = rep(text,
    "        pet.playResult((uint8_t)std::min<uint16_t>(255, playScore));",
    "        pet.playResult((uint8_t)std::min<uint16_t>(255, playScore));\n"
    "        ultimateAwardCoins((uint16_t)(2 + std::min<uint16_t>(20, playScore / 2)));",
    "play coin reward")
text = rep(text,
    "    trainGain = pet.trainStrength(trainHits);",
    "    trainGain = pet.trainStrength(trainHits);\n"
    "    ultimateAwardCoins((uint16_t)(2 + std::min<uint16_t>(20, trainHits / 4)));",
    "training coin reward")
text = rep(text,
    "static void chooseFeed() {\n  if (feedSel < 3) pet.feedBerry(feedSel);\n  else pet.feedCandy();",
    "static void chooseFeed() {\n  if (feedSel < 3) pet.feedBerry(feedSel);\n  else pet.feedCandy();\n  ultimateAwardCoins(1);",
    "care coin reward")

# Render economy screens.
render_anchor = "      case CUSTOMIZE:  drawUltimateCustomize(); break;"
if render_anchor not in text:
    fail("Phase 4 render case")
text = text.replace(render_anchor,
    render_anchor + "\n      case INVENTORY:  drawUltimateInventory(); break;\n      case SHOP:       drawUltimateShop(); break;",
    1)

# Input handlers before CUSTOMIZE.
input_anchor = "  } else if (screen == CUSTOMIZE) {"
if input_anchor not in text:
    fail("Phase 4 input branch")
econ_input = r'''  } else if (screen == INVENTORY) {
    if (upEdge) { ultimateInventorySel = ultimateInventorySel == 0 ? ULT_ITEM_COUNT - 1 : ultimateInventorySel - 1; dirty = true; }
    if (downEdge) { ultimateInventorySel = (ultimateInventorySel + 1) % ULT_ITEM_COUNT; dirty = true; }
    if (enterEdge || spaceEdge) ultimateUseItem(ultimateInventorySel);
    if (chars[(uint8_t)'k'] && !prevChars[(uint8_t)'k']) { screen = SHOP; dirty = true; }
    if (escEdge || backEdge) { screen = HOME; dirty = true; }
  } else if (screen == SHOP) {
    if (upEdge) { ultimateShopSel = ultimateShopSel == 0 ? ULT_ITEM_COUNT - 1 : ultimateShopSel - 1; dirty = true; }
    if (downEdge) { ultimateShopSel = (ultimateShopSel + 1) % ULT_ITEM_COUNT; dirty = true; }
    if (enterEdge || spaceEdge) {
      if (ultimateBuyItem(ultimateShopSel)) say(String("Bought ") + ULT_ITEM_NAME[ultimateShopSel]);
      else say("Not enough coins");
    }
    if (chars[(uint8_t)'v'] && !prevChars[(uint8_t)'v']) { screen = INVENTORY; dirty = true; }
    if (escEdge || backEdge) { screen = HOME; dirty = true; }
'''
text = text.replace(input_anchor, econ_input + input_anchor, 1)

# Direct Home shortcuts: V = inventory, K = shop.
key_anchor = "      } else if (c == 'c') {"
if key_anchor not in text:
    fail("Home customize key")
text = text.replace(key_anchor,
    "      } else if (c == 'v') {\n"
    "        screen = INVENTORY; dirty = true;\n"
    "      } else if (c == 'k') {\n"
    "        screen = SHOP; dirty = true;\n"
    + key_anchor,
    1)

# Controls discoverability.
text = text.replace('    "D: Pokedex      C: customize",',
                    '    "D: Dex  C: home  V: bag  K: shop",', 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-ultimate-p5] Added persistent coins, inventory, shop, care/game earnings and usable items")
