#include "cyber_den.h"

#include <WiFi.h>
#include <SD.h>
#include <cstring>
#include <cstddef>

namespace {

static constexpr uint32_t DEN_MAGIC = 0x314E4443UL; // "CDN1"
static constexpr uint8_t DEN_VERSION = 1;
static constexpr int MAX_APS = 18;
static constexpr int MAX_HASHES = 96;
static constexpr uint32_t AUTO_SCAN_MS = 18000UL;
static constexpr const char *DEN_SAVE_PATH = "/cyber_den.dat";

struct DenAp {
  char ssid[25];
  int16_t rssi;
  uint8_t channel;
  bool open;
  uint32_t hash;
};

struct __attribute__((packed)) DenSave {
  uint32_t magic;
  uint8_t version;
  uint8_t hashCount;
  uint16_t reserved;
  uint32_t xp;
  uint32_t totalSeen;
  uint32_t scans;
  uint32_t hashes[MAX_HASHES];
  uint32_t crc;
};

static bool gSdReady = false;
static bool gActive = false;
static bool gScanRunning = false;
static bool gManualScan = false;
static uint8_t gPage = 0;
static uint8_t gNetOffset = 0;
static uint32_t gLastScanStart = 0;
static uint32_t gLastScanDone = 0;
static uint32_t gSessionStart = 0;
static uint32_t gXp = 0;
static uint32_t gTotalSeen = 0;
static uint32_t gScans = 0;
static uint32_t gSessionNew = 0;
static uint16_t gLastNew = 0;
static uint8_t gHashCount = 0;
static uint32_t gHashes[MAX_HASHES] = {0};
static DenAp gAps[MAX_APS];
static uint8_t gApCount = 0;
static int16_t gStrongest = -127;
static uint8_t gBestChannel = 0;
static uint8_t gChannelCounts[15] = {0};

static uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)((((uint16_t)r >> 3) << 11) |
                    (((uint16_t)g >> 2) << 5) |
                    ((uint16_t)b >> 3));
}

static uint32_t fnv1a(const uint8_t *p, size_t n) {
  uint32_t h = 2166136261UL;
  for (size_t i = 0; i < n; ++i) {
    h ^= p[i];
    h *= 16777619UL;
  }
  return h;
}

static uint32_t saveCrc(const DenSave &s) {
  return fnv1a(reinterpret_cast<const uint8_t*>(&s), offsetof(DenSave, crc));
}

static uint32_t hashBssid(const uint8_t *bssid) {
  if (!bssid) return 0;
  uint32_t h = fnv1a(bssid, 6);
  return h ? h : 1;
}

static bool hashKnown(uint32_t h) {
  if (!h) return true;
  for (uint8_t i = 0; i < gHashCount; ++i) {
    if (gHashes[i] == h) return true;
  }
  return false;
}

static void rememberHash(uint32_t h) {
  if (!h || hashKnown(h)) return;
  if (gHashCount < MAX_HASHES) {
    gHashes[gHashCount++] = h;
  } else {
    // Keep a rolling memory of recently discovered networks once full.
    memmove(&gHashes[0], &gHashes[1], sizeof(uint32_t) * (MAX_HASHES - 1));
    gHashes[MAX_HASHES - 1] = h;
  }
}

static void saveProgress() {
  if (!gSdReady) return;
  DenSave s{};
  s.magic = DEN_MAGIC;
  s.version = DEN_VERSION;
  s.hashCount = gHashCount;
  s.xp = gXp;
  s.totalSeen = gTotalSeen;
  s.scans = gScans;
  memcpy(s.hashes, gHashes, sizeof(gHashes));
  s.crc = saveCrc(s);

  SD.remove(DEN_SAVE_PATH);
  File f = SD.open(DEN_SAVE_PATH, FILE_WRITE);
  if (!f) return;
  f.write(reinterpret_cast<const uint8_t*>(&s), sizeof(s));
  f.flush();
  f.close();
}

static void loadProgress() {
  if (!gSdReady) return;
  File f = SD.open(DEN_SAVE_PATH, FILE_READ);
  if (!f || f.size() != sizeof(DenSave)) {
    if (f) f.close();
    return;
  }

  DenSave s{};
  size_t got = f.read(reinterpret_cast<uint8_t*>(&s), sizeof(s));
  f.close();
  if (got != sizeof(s) || s.magic != DEN_MAGIC || s.version != DEN_VERSION ||
      s.hashCount > MAX_HASHES || saveCrc(s) != s.crc) return;

  gXp = s.xp;
  gTotalSeen = s.totalSeen;
  gScans = s.scans;
  gHashCount = s.hashCount;
  memcpy(gHashes, s.hashes, sizeof(gHashes));
}

static const char *moodName() {
  if (gScanRunning) return "HUNTING";
  if (gLastNew >= 4) return "EXCITED";
  if (gLastNew > 0) return "HAPPY";
  if (gApCount >= 10) return "CURIOUS";
  if (gApCount > 0) return "WATCHING";
  return "SLEEPY";
}

static const char *faceText() {
  if (gScanRunning) return "(o_o)";
  if (gLastNew >= 4) return "(^o^)";
  if (gLastNew > 0) return "(^_^)";
  if (gApCount >= 10) return "(O_O)";
  if (gApCount > 0) return "(-_-)";
  return "(u_u)";
}

static uint16_t level() {
  uint32_t lv = 1 + gXp / 100UL;
  return (uint16_t)(lv > 999 ? 999 : lv);
}

static void startScan(bool manual) {
  if (gScanRunning) return;

  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, false);
  WiFi.scanDelete();

  // async=true, show_hidden=true, passive=true. This observes nearby beacon
  // traffic without implementing deauth, injection, or attack actions.
  int16_t rc = WiFi.scanNetworks(true, true, true, 220);
  if (rc == WIFI_SCAN_FAILED) {
    gScanRunning = false;
    return;
  }

  gScanRunning = true;
  gManualScan = manual;
  gLastScanStart = millis();
}

static void addApSorted(const DenAp &ap) {
  int pos = gApCount;
  if (pos >= MAX_APS) {
    if (ap.rssi <= gAps[MAX_APS - 1].rssi) return;
    pos = MAX_APS - 1;
  } else {
    ++gApCount;
  }

  while (pos > 0 && gAps[pos - 1].rssi < ap.rssi) {
    if (pos < MAX_APS) gAps[pos] = gAps[pos - 1];
    --pos;
  }
  gAps[pos] = ap;
}

static void finishScan(int16_t n) {
  gApCount = 0;
  gLastNew = 0;
  gStrongest = -127;
  gBestChannel = 0;
  memset(gChannelCounts, 0, sizeof(gChannelCounts));

  if (n < 0) n = 0;
  for (int i = 0; i < n; ++i) {
    DenAp ap{};
    String ss = WiFi.SSID(i);
    if (!ss.length()) ss = "<hidden>";
    ss.toCharArray(ap.ssid, sizeof(ap.ssid));
    ap.rssi = WiFi.RSSI(i);
    int ch = WiFi.channel(i);
    ap.channel = (uint8_t)(ch < 0 ? 0 : ch);
    ap.open = WiFi.encryptionType(i) == WIFI_AUTH_OPEN;
    ap.hash = hashBssid(WiFi.BSSID(i));

    if (ap.rssi > gStrongest) gStrongest = ap.rssi;
    if (ap.channel < 15) ++gChannelCounts[ap.channel];

    if (!hashKnown(ap.hash)) {
      rememberHash(ap.hash);
      ++gTotalSeen;
      ++gSessionNew;
      ++gLastNew;
      gXp += 5;
    }

    addApSorted(ap);
  }

  uint8_t bestCount = 0;
  for (uint8_t ch = 1; ch < 15; ++ch) {
    if (gChannelCounts[ch] > bestCount) {
      bestCount = gChannelCounts[ch];
      gBestChannel = ch;
    }
  }

  ++gScans;
  if (gLastNew || (gScans % 10UL) == 0) saveProgress();

  WiFi.scanDelete();
  gScanRunning = false;
  gManualScan = false;
  gLastScanDone = millis();
  if (!gActive) WiFi.mode(WIFI_OFF);
}

static void drawTop(M5Canvas &ui, const char *title, uint16_t accent) {
  const uint16_t bg = rgb565(10, 15, 22);
  const uint16_t panel = rgb565(18, 28, 39);
  const uint16_t ink = rgb565(221, 236, 236);
  ui.fillScreen(bg);
  ui.fillRoundRect(5, 4, 230, 20, 6, panel);
  ui.drawRoundRect(5, 4, 230, 20, 6, accent);
  ui.setTextSize(1);
  ui.setTextColor(ink);
  ui.drawCentreString(title, 120, 10, 1);
}

static void drawDen(M5Canvas &ui, uint32_t now) {
  const uint16_t accent = rgb565(72, 214, 184);
  const uint16_t ink = rgb565(221, 236, 236);
  const uint16_t dim = rgb565(105, 129, 136);
  const uint16_t panel = rgb565(18, 28, 39);
  drawTop(ui, "CYBER DEN  BETA", accent);

  ui.setTextColor(accent);
  ui.setTextSize(3);
  ui.drawCentreString(faceText(), 120, 31, 1);
  ui.setTextSize(1);
  ui.setTextColor(ink);
  ui.drawCentreString(moodName(), 120, 59, 1);

  char lv[36];
  snprintf(lv, sizeof(lv), "LV %u   XP %lu", level(), (unsigned long)gXp);
  ui.drawCentreString(lv, 120, 72, 1);

  uint32_t inLevel = gXp % 100UL;
  ui.fillRoundRect(30, 84, 180, 7, 3, panel);
  int fill = (int)(176UL * inLevel / 100UL);
  if (fill > 0) ui.fillRoundRect(32, 86, fill, 3, 2, accent);

  char stats[48];
  snprintf(stats, sizeof(stats), "NEAR %u   NEW %u   SEEN %lu",
           gApCount, gLastNew, (unsigned long)gTotalSeen);
  ui.setTextColor(ink);
  ui.drawCentreString(stats, 120, 98, 1);

  if (gScanRunning) {
    const char spin[] = {'|','/','-','\\'};
    char line[30];
    snprintf(line, sizeof(line), "%c passive scan...", spin[(now / 180) & 3]);
    ui.setTextColor(accent);
    ui.drawCentreString(line, 120, 112, 1);
  } else {
    ui.setTextColor(dim);
    ui.drawCentreString("ENTER SCAN   < > PAGES", 120, 112, 1);
  }
  ui.drawCentreString("ESC BACK", 120, 124, 1);
}

static void drawNetworks(M5Canvas &ui) {
  const uint16_t accent = rgb565(72, 214, 184);
  const uint16_t ink = rgb565(221, 236, 236);
  const uint16_t dim = rgb565(105, 129, 136);
  const uint16_t openCol = rgb565(243, 181, 72);
  drawTop(ui, "NEARBY NETWORKS", accent);

  if (!gApCount) {
    ui.setTextColor(dim);
    ui.setTextSize(1);
    ui.drawCentreString(gScanRunning ? "Scanning..." : "No scan results yet", 120, 62, 1);
    ui.drawCentreString("ENTER = scan now", 120, 78, 1);
    return;
  }

  if (gNetOffset > gApCount - 1) gNetOffset = 0;
  for (int row = 0; row < 5; ++row) {
    int idx = gNetOffset + row;
    if (idx >= gApCount) break;
    int y = 29 + row * 18;
    const DenAp &ap = gAps[idx];

    ui.setTextSize(1);
    ui.setTextColor(ap.open ? openCol : ink);
    char ss[27];
    snprintf(ss, sizeof(ss), "%s", ap.ssid);
    ui.drawString(ss, 8, y);

    char meta[26];
    snprintf(meta, sizeof(meta), "CH%u %ddBm%s", ap.channel, ap.rssi,
             ap.open ? " OPEN" : "");
    ui.setTextColor(dim);
    ui.drawRightString(meta, 232, y, 1);
  }

  ui.setTextColor(dim);
  ui.drawCentreString("UP/DOWN SCROLL  ENTER SCAN", 120, 122, 1);
}

static void drawStats(M5Canvas &ui, uint32_t now) {
  const uint16_t accent = rgb565(72, 214, 184);
  const uint16_t ink = rgb565(221, 236, 236);
  const uint16_t dim = rgb565(105, 129, 136);
  drawTop(ui, "DEN STATS", accent);

  uint32_t sec = (now - gSessionStart) / 1000UL;
  char line[48];
  ui.setTextSize(1);
  ui.setTextColor(ink);

  snprintf(line, sizeof(line), "LEVEL        %u", level());
  ui.drawString(line, 26, 32);
  snprintf(line, sizeof(line), "XP           %lu", (unsigned long)gXp);
  ui.drawString(line, 26, 47);
  snprintf(line, sizeof(line), "UNIQUE SEEN  %lu", (unsigned long)gTotalSeen);
  ui.drawString(line, 26, 62);
  snprintf(line, sizeof(line), "SCANS        %lu", (unsigned long)gScans);
  ui.drawString(line, 26, 77);
  snprintf(line, sizeof(line), "SESSION NEW  %lu", (unsigned long)gSessionNew);
  ui.drawString(line, 26, 92);
  snprintf(line, sizeof(line), "UPTIME       %lum %lus", (unsigned long)(sec / 60), (unsigned long)(sec % 60));
  ui.drawString(line, 26, 107);

  ui.setTextColor(dim);
  if (gStrongest > -127) {
    snprintf(line, sizeof(line), "BEST %ddBm  BUSY CH %u", gStrongest, gBestChannel);
    ui.drawCentreString(line, 120, 122, 1);
  }
}

static void drawHelp(M5Canvas &ui) {
  const uint16_t accent = rgb565(72, 214, 184);
  const uint16_t ink = rgb565(221, 236, 236);
  const uint16_t dim = rgb565(105, 129, 136);
  drawTop(ui, "CYBER DEN HELP", accent);
  ui.setTextSize(1);
  ui.setTextColor(ink);
  const char *lines[] = {
    "Pwnagotchi-inspired companion",
    "Passive Wi-Fi discovery",
    "New networks earn 5 XP",
    "Mood changes with discoveries",
    "Progress saves to microSD",
    "LEFT/RIGHT: change page",
    "UP/DOWN: network list",
    "ENTER: passive rescan",
    "ESC/BACKSPACE: exit",
    "No deauth / injection tools"
  };
  for (int i = 0; i < 10; ++i) ui.drawString(lines[i], 16, 29 + i * 10);
  ui.setTextColor(dim);
  ui.drawCentreString("BETA 0.9", 120, 124, 1);
}

} // namespace

void cyberDenBegin(bool sdReady) {
  gSdReady = sdReady;
  gSessionStart = millis();
  loadProgress();
}

void cyberDenEnter() {
  gActive = true;
  gPage = 0;
  gNetOffset = 0;
  if (!gScanRunning && (gLastScanDone == 0 || millis() - gLastScanDone > 6000UL)) {
    startScan(false);
  }
}

void cyberDenLeave() {
  gActive = false;
  if (!gScanRunning) WiFi.mode(WIFI_OFF);
}

void cyberDenUpdate(uint32_t nowMs) {
  if (gScanRunning) {
    int16_t n = WiFi.scanComplete();
    if (n >= 0) finishScan(n);
    else if (n == WIFI_SCAN_FAILED || nowMs - gLastScanStart > 12000UL) {
      WiFi.scanDelete();
      gScanRunning = false;
      gManualScan = false;
      gLastScanDone = nowMs;
      if (!gActive) WiFi.mode(WIFI_OFF);
    }
    return;
  }

  if (gActive && nowMs - gLastScanDone >= AUTO_SCAN_MS) startScan(false);
}

void cyberDenDraw(M5Canvas &ui, uint32_t nowMs) {
  if (gPage == 0) drawDen(ui, nowMs);
  else if (gPage == 1) drawNetworks(ui);
  else if (gPage == 2) drawStats(ui, nowMs);
  else drawHelp(ui);
}

bool cyberDenHandleInput(bool upEdge,
                         bool downEdge,
                         bool leftEdge,
                         bool rightEdge,
                         bool enterEdge,
                         bool spaceEdge,
                         bool escEdge,
                         bool backEdge) {
  if (escEdge || backEdge) return true;

  if (leftEdge) {
    gPage = gPage == 0 ? 3 : gPage - 1;
    gNetOffset = 0;
  }
  if (rightEdge) {
    gPage = (gPage + 1) & 3;
    gNetOffset = 0;
  }

  if (gPage == 1) {
    if (upEdge && gNetOffset > 0) --gNetOffset;
    if (downEdge && gNetOffset + 5 < gApCount) ++gNetOffset;
  }

  if ((enterEdge || spaceEdge) && !gScanRunning) startScan(true);
  return false;
}

bool cyberDenAnimated() {
  return gActive && (gScanRunning || gPage == 0 || gPage == 2);
}
