Import("env")
from pathlib import Path

PROJECT = Path(env.subst("$PROJECT_DIR"))
MAIN = PROJECT / "src" / "main.cpp"
MARKER = "// ULTIMATE_V090_GAME_BACKGROUNDS"


def fail(msg):
    print(f"[v0.9.0-game-bg] ERROR: {msg}")
    env.Exit(1)


text = MAIN.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
if MARKER in text:
    print("[v0.9.0-game-bg] customized game backgrounds already applied")
    Return()
if "// ULTIMATE_V090_PHASE4_HOME_CUSTOMIZATION" not in text:
    fail("Home customization must run first")

old_play = '''static void drawPlay(uint32_t now) {
  uint8_t biome = pet.speciesId > 0 ? DEX_TBL[pet.speciesId].biome : 0;
  drawScene(biome, now, sceneNight(), 135);'''
new_play = '''// ULTIMATE_V090_GAME_BACKGROUNDS
static void drawPlay(uint32_t now) {
  uint8_t biome = pet.speciesId > 0 ? DEX_TBL[pet.speciesId].biome : 0;
  biome = ultimateSelectedHomeBiome(biome);
  drawScene(biome, now, sceneNight(), 135);'''
if old_play not in text:
    fail("drawPlay biome block")
text = text.replace(old_play, new_play, 1)

old_train = '''static void drawTrain(uint32_t now) {
  uint8_t biome = pet.speciesId > 0 ? DEX_TBL[pet.speciesId].biome : 0;
  drawScene(biome, now, sceneNight(), 135);'''
new_train = '''static void drawTrain(uint32_t now) {
  uint8_t biome = pet.speciesId > 0 ? DEX_TBL[pet.speciesId].biome : 0;
  biome = ultimateSelectedHomeBiome(biome);
  drawScene(biome, now, sceneNight(), 135);'''
if old_train not in text:
    fail("drawTrain biome block")
text = text.replace(old_train, new_train, 1)

MAIN.write_text(text, encoding="utf-8", newline="\n")
print("[v0.9.0-game-bg] Play and Strength Training now use the selected Home Customize background")
