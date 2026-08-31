#include "cyber_den.h"

#include <WiFi.h>
#include <SD.h>
#include <esp_wifi.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <cstring>
#include <cstddef>

#include "pmd_stream.h"

namespace {

// -----------------------------------------------------------------------------
// Persistent progression
// -----------------------------------------------------------------------------
static constexpr uint32_t DEN_MAGIC = 0x314E4443UL; // "CDN1"
static constexpr uint8_t DEN_VERSION = 2;
static constexpr const char *DEN_SAVE_PATH = "/cyber_den.dat";
static constexpr const char *DEN_LOG_DIR = "/cyberden";
static constexpr const char *DEN_LOG_PATH = "/cyberden/events.log";
static constexpr int MAX_HASHES = 96;
static constexpr int MAX_APS = 24;
static constexpr int MAX_BLE = 12;
static constexpr int EVENT_LINES = 5;

struct __attribute__((packed)) DenSaveV1 {
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

struct __attribute__((packed)) DenSaveV2 {
  uint32_t magic;
  uint8_t version;
  uint8_t hashCount;
  uint16_t reserved;
  uint32_t xp;
  uint32_t uniqueAps;
  uint32_t scans;
  uint32_t bleSeen;
  uint32_t probesSeen;
  uint32_t eapolSeen;
  uint32_t packetsSeen;
  uint32_t hashes[MAX_HASHES];
  uint32_t crc;
};

struct DenAp {
  char ssid[27] = {0};
  char bssid[18] = {0};
  int16_t rssi = -127;
  uint8_t channel = 0;
  bool open = false;
  uint32_t hash = 0;
};

struct DenBle {
  char name[21] = {0};
  char address[18] = {0};
  int16_t rssi = -127;
};

enum DenPage : uint8_t {
  PAGE_MENU = 0,
  PAGE_PWN_PET,
  PAGE_WIFI_LIST,
  PAGE_WIFI_SPECTRUM,
  PAGE_WIFI_DETAIL,
  PAGE_HANDSHAKE,
  PAGE_PROBES,
  PAGE_BLE,
  PAGE_PACKETS,
  PAGE_LOGS,
  PAGE_PROFILE,
  PAGE_LAB
};

enum SniffMode : uint8_t {
  SNIFF_OFF = 0,
  SNIFF_PWN,
  SNIFF_HANDSHAKE,
  SNIFF_PROBES,
  SNIFF_PACKETS
};

static const char *MENU_ITEMS[12] = {
  "PWN PET",
  "WIFI SCANNER",
  "HANDSHAKE CAPTURE",
  "PROBE SNIFFER",
  "DEAUTH",
  "EVIL TWIN",
  "KARMA",
  "BLE SCANNER",
  "BLE SPAM",
  "PACKET MONITOR",
  "LOGS",
  "CYBER PROFILE"
};

// -----------------------------------------------------------------------------
// Runtime state
// -----------------------------------------------------------------------------
static bool gSdReady = false;
static bool gActive = false;
static DenPage gPage = PAGE_MENU;
static uint8_t gMenu = 0;
static uint8_t gMenuTop = 0;
static uint32_t gEnterAt = 0;
static uint32_t gPageAt = 0;

static int16_t gPetDex = -1;
static bool gPetShiny = false;
static char gPetName[16] = "PWN PET";

static uint32_t gXp = 0;
static uint32_t gUniqueAps = 0;
static uint32_t gScans = 0;
static uint32_t gBleSeen = 0;
static uint32_t gProbesSeen = 0;
static uint32_t gEapolSeen = 0;
static uint32_t gPacketsSeen = 0;
static uint8_t gHashCount = 0;
static uint32_t gHashes[MAX_HASHES] = {0};
static bool gSaveDirty = false;
static uint32_t gLastSave = 0;

static DenAp gAps[MAX_APS];
static uint8_t gApCount = 0;
static uint8_t gApSel = 0;
static uint8_t gWifiTop = 0;
static uint8_t gChannelCounts[14] = {0};
static bool gWifiScanRunning = false;
static bool gWifiScanPending = false;
static uint32_t gWifiScanAt = 0;

static DenBle gBle[MAX_BLE];
static uint8_t gBleCount = 0;
static uint8_t gBleSel = 0;
static uint8_t gBleTop = 0;
static bool gBleScanPending = false;
static bool gBleScanBusy = false;

static char gEvents[EVENT_LINES][44] = {{0}};
static uint8_t gEventHead = 0;
static uint8_t gEventCount = 0;

static String gLabTitle;
static String gLabLine1;
static String gLabLine2;
static uint8_t gLabGhost = 94;
static bool gLabPulse = false;

static PmdStream gMascot;
static int16_t gMascotDex = -999;
static bool gMascotShiny = false;

// Passive monitor callback state. Raw 802.11 frames are not persisted.
static portMUX_TYPE gMux = portMUX_INITIALIZER_UNLOCKED;
static SniffMode gSniffMode = SNIFF_OFF;
static uint8_t gChannel = 1;
static uint32_t gLastHop = 0;
static volatile uint32_t gPktMgmt = 0;
static volatile uint32_t gPktData = 0;
static volatile uint32_t gPktCtrl = 0;
static volatile uint32_t gProbeSession = 0;
static volatile uint32_t gEapolSession = 0;
static volatile int8_t gLastRssi = -127;
static volatile uint8_t gLastRxChannel = 0;
static char gLastProbeSsid[33] = {0};
static volatile uint32_t gLastProbeId = 0;
static uint32_t gPrevPktTotal = 0;
static uint32_t gPrevProbe = 0;
static uint32_t gPrevEapol = 0;
static uint32_t gLastEapolEvent = 0;

// -----------------------------------------------------------------------------
// Palette / drawing helpers
// -----------------------------------------------------------------------------
static uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)((((uint16_t)r >> 3) << 11) |
                    (((uint16_t)g >> 2) << 5) |
                    ((uint16_t)b >> 3));
}

static const uint16_t C_BG      = rgb565(8, 4, 18);
static const uint16_t C_BG2     = rgb565(20, 8, 36);
static const uint16_t C_PANEL   = rgb565(31, 15, 51);
static const uint16_t C_PANEL2  = rgb565(47, 23, 70);
static const uint16_t C_INK     = rgb565(255, 241, 218);
static const uint16_t C_DIM     = rgb565(157, 137, 173);
static const uint16_t C_PURPLE  = rgb565(141, 80, 255);
static const uint16_t C_VIOLET  = rgb565(182, 100, 255);
static const uint16_t C_MAGENTA = rgb565(255, 74, 187);
static const uint16_t C_PINK    = rgb565(255, 137, 208);
static const uint16_t C_CYAN    = rgb565(74, 224, 232);
static const uint16_t C_GOLD    = rgb565(255, 206, 92);
static const uint16_t C_CORAL   = rgb565(255, 127, 109);
static const uint16_t C_GREEN   = rgb565(106, 225, 152);
static const uint16_t C_RED     = rgb565(255, 88, 112);

static uint16_t lerp565(uint16_t a, uint16_t b, int i, int n) {
  if (n <= 0) return a;
  int ar = (a >> 11) & 31, ag = (a >> 5) & 63, ab = a & 31;
  int br = (b >> 11) & 31, bg = (b >> 5) & 63, bb = b & 31;
  return (uint16_t)(((ar + (br - ar) * i / n) << 11) |
                    ((ag + (bg - ag) * i / n) << 5) |
                    (ab + (bb - ab) * i / n));
}

static uint32_t fnv1a(const uint8_t *p, size_t n) {
  uint32_t h = 2166136261UL;
  for (size_t i = 0; i < n; ++i) {
    h ^= p[i];
    h *= 16777619UL;
  }
  return h;
}

static uint32_t saveCrcV1(const DenSaveV1 &s) {
  return fnv1a(reinterpret_cast<const uint8_t*>(&s), offsetof(DenSaveV1, crc));
}

static uint32_t saveCrcV2(const DenSaveV2 &s) {
  return fnv1a(reinterpret_cast<const uint8_t*>(&s), offsetof(DenSaveV2, crc));
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
    memmove(&gHashes[0], &gHashes[1], sizeof(uint32_t) * (MAX_HASHES - 1));
    gHashes[MAX_HASHES - 1] = h;
  }
}

static uint16_t cyberLevel() {
  uint32_t lv = 1 + gXp / 150UL;
  return (uint16_t)(lv > 999 ? 999 : lv);
}

static uint8_t badgeCount() {
  uint8_t b = 0;
  if (gUniqueAps >= 10) ++b;
  if (gUniqueAps >= 50) ++b;
  if (gProbesSeen >= 25) ++b;
  if (gPacketsSeen >= 1000) ++b;
  if (gEapolSeen >= 1) ++b;
  if (gBleSeen >= 25) ++b;
  if (gScans >= 25) ++b;
  if (cyberLevel() >= 10) ++b;
  return b;
}

static const char *moodName() {
  if (gWifiScanRunning || gBleScanBusy) return "HUNTING";
  if (gEapolSession) return "ALERT";
  if (gProbeSession >= 10) return "EXCITED";
  if (gApCount >= 10) return "CURIOUS";
  if (gApCount > 0) return "WATCHING";
  return "SPECTRAL";
}

static void panel(M5Canvas &ui, int x, int y, int w, int h,
                  uint16_t fill = C_PANEL, uint16_t edge = C_PURPLE,
                  int radius = 5) {
  ui.fillRoundRect(x + 1, y + 2, w, h, radius, C_BG);
  ui.fillRoundRect(x, y, w, h, radius, fill);
  ui.drawRoundRect(x, y, w, h, radius, edge);
}

static void drawStar(M5Canvas &ui, int x, int y, uint16_t c) {
  ui.drawFastHLine(x - 2, y, 5, c);
  ui.drawFastVLine(x, y - 2, 5, c);
}

static void drawBackground(M5Canvas &ui, uint32_t now) {
  for (int y = 0; y < 135; y += 7) {
    ui.fillRect(0, y, 240, 7, lerp565(C_BG, C_BG2, y, 134));
  }

  int off = (int)((now / 70) % 16);
  uint16_t grid = rgb565(50, 27, 72);
  for (int x = -off; x < 240; x += 16) ui.drawFastVLine(x, 23, 112, grid);
  for (int y = 31; y < 135; y += 16) ui.drawFastHLine(0, y, 240, grid);

  for (int i = 0; i < 8; ++i) {
    int x = (17 + i * 37 + (int)(now / 38)) % 240;
    int y = 28 + ((11 + i * 23 + (int)(now / 61)) % 96);
    ui.fillRect(x, y, 1 + (i & 1), 1 + (i & 1), (i & 1) ? C_MAGENTA : C_CYAN);
  }
}

static void drawHeader(M5Canvas &ui, const char *title, const char *tag = nullptr) {
  ui.fillRoundRect(4, 3, 232, 21, 6, C_PANEL);
  ui.drawRoundRect(4, 3, 232, 21, 6, C_MAGENTA);
  ui.setTextSize(1);
  ui.setTextColor(C_INK);
  ui.drawString(title, 11, 9);
  if (tag && *tag) {
    ui.setTextColor(C_CYAN);
    ui.drawRightString(tag, 229, 9, 1);
  }
}

static void drawFooter(M5Canvas &ui, const char *left, const char *mid, const char *right) {
  ui.fillRect(0, 118, 240, 17, C_BG);
  ui.drawFastHLine(0, 118, 240, C_PURPLE);
  ui.setTextSize(1);
  ui.setTextColor(C_DIM);
  if (left) ui.drawString(left, 5, 123);
  if (mid) ui.drawCentreString(mid, 120, 123, 1);
  if (right) ui.drawRightString(right, 235, 123, 1);
}

static void drawFallbackGhost(M5Canvas &ui, int dex, int cx, int cy, int scale = 1) {
  uint16_t body = dex == 92 ? C_VIOLET : (dex == 93 ? C_PURPLE : C_MAGENTA);
  int r = (dex == 92 ? 12 : 14) * scale;
  ui.fillCircle(cx, cy, r, body);
  if (dex == 93) {
    ui.fillTriangle(cx - r - 7 * scale, cy - 2 * scale,
                    cx - r + 4 * scale, cy - 8 * scale,
                    cx - r + 2 * scale, cy + 7 * scale, body);
    ui.fillTriangle(cx + r + 7 * scale, cy - 2 * scale,
                    cx + r - 4 * scale, cy - 8 * scale,
                    cx + r - 2 * scale, cy + 7 * scale, body);
  } else if (dex == 94) {
    ui.fillTriangle(cx - 9 * scale, cy - r + 2 * scale,
                    cx - 2 * scale, cy - r - 9 * scale,
                    cx + 1 * scale, cy - r + 2 * scale, body);
    ui.fillTriangle(cx + 4 * scale, cy - r + 2 * scale,
                    cx + 10 * scale, cy - r - 8 * scale,
                    cx + 12 * scale, cy - r + 4 * scale, body);
  }
  ui.fillCircle(cx - 5 * scale, cy - 2 * scale, 3 * scale, C_INK);
  ui.fillCircle(cx + 5 * scale, cy - 2 * scale, 3 * scale, C_INK);
  ui.fillCircle(cx - 4 * scale, cy - 2 * scale, 1 * scale, C_RED);
  ui.fillCircle(cx + 4 * scale, cy - 2 * scale, 1 * scale, C_RED);
  ui.drawFastHLine(cx - 5 * scale, cy + 7 * scale, 11 * scale, C_BG);
}

static void ensureMascot(int16_t dex, bool shiny = false) {
  if (!gSdReady || dex < 1 || dex > 151) {
    gMascot.unload();
    gMascotDex = dex;
    gMascotShiny = shiny;
    return;
  }
  if (gMascotDex == dex && gMascotShiny == shiny && gMascot.loaded()) return;
  gMascot.unload();
  gMascotDex = dex;
  gMascotShiny = shiny;
  gMascot.load((uint16_t)dex, shiny);
}

static void drawMascot(M5Canvas &ui, int16_t dex, bool shiny,
                       int cx, int groundY, uint32_t now,
                       uint8_t action = PMD_IDLE, int8_t forcedScale = 0) {
  ensureMascot(dex, shiny);
  if (gMascot.loaded()) {
    gMascot.draw(ui, action, cx, groundY, now, forcedScale);
  } else {
    int ghost = (dex >= 92 && dex <= 94) ? dex : 94;
    drawFallbackGhost(ui, ghost, cx, groundY - 18, forcedScale > 1 ? 2 : 1);
  }
}

static void drawPortalRings(M5Canvas &ui, int cx, int cy, uint32_t now, uint16_t c) {
  for (int i = 0; i < 4; ++i) {
    int r = 12 + (int)((now / 45 + i * 12) % 45);
    ui.drawCircle(cx, cy, r, i & 1 ? c : C_PURPLE);
  }
}

static void drawPortalIntro(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  uint32_t t = now - gEnterAt;
  int stage = t < 520 ? 0 : (t < 1040 ? 1 : 2);
  int dex = 92 + stage;
  const char *name = stage == 0 ? "GASTLY" : (stage == 1 ? "HAUNTER" : "GENGAR");
  uint16_t accent = stage == 0 ? C_VIOLET : (stage == 1 ? C_PURPLE : C_MAGENTA);

  drawPortalRings(ui, 120, 70, now, accent);
  drawMascot(ui, dex, false, 120, 101, now, stage == 2 ? PMD_POSE : PMD_IDLE, 1);

  ui.fillRoundRect(55, 7, 130, 18, 6, C_PANEL);
  ui.drawRoundRect(55, 7, 130, 18, 6, accent);
  ui.setTextColor(C_INK);
  ui.drawCentreString("CYBER DEN", 120, 12, 1);
  ui.setTextColor(accent);
  ui.drawCentreString(name, 120, 105, 1);
  ui.setTextColor(C_DIM);
  ui.drawCentreString("SPECTRAL LINK", 120, 120, 1);
}

// -----------------------------------------------------------------------------
// Logging / saving
// -----------------------------------------------------------------------------
static void addEvent(const char *text, bool writeSd = true) {
  if (!text) return;
  strncpy(gEvents[gEventHead], text, sizeof(gEvents[gEventHead]) - 1);
  gEvents[gEventHead][sizeof(gEvents[gEventHead]) - 1] = 0;
  gEventHead = (gEventHead + 1) % EVENT_LINES;
  if (gEventCount < EVENT_LINES) ++gEventCount;

  if (writeSd && gSdReady) {
    if (!SD.exists(DEN_LOG_DIR)) SD.mkdir(DEN_LOG_DIR);
    File f = SD.open(DEN_LOG_PATH, FILE_APPEND);
    if (f) {
      f.printf("%lu %s\n", (unsigned long)(millis() / 1000UL), text);
      f.close();
    }
  }
}

static void awardXp(uint16_t amount) {
  if (!amount) return;
  gXp += amount;
  gSaveDirty = true;
}

static void saveProgress(bool force = false) {
  if (!gSdReady) return;
  uint32_t now = millis();
  if (!force && (!gSaveDirty || now - gLastSave < 15000UL)) return;

  DenSaveV2 s{};
  s.magic = DEN_MAGIC;
  s.version = DEN_VERSION;
  s.hashCount = gHashCount;
  s.xp = gXp;
  s.uniqueAps = gUniqueAps;
  s.scans = gScans;
  s.bleSeen = gBleSeen;
  s.probesSeen = gProbesSeen;
  s.eapolSeen = gEapolSeen;
  s.packetsSeen = gPacketsSeen;
  memcpy(s.hashes, gHashes, sizeof(gHashes));
  s.crc = saveCrcV2(s);

  SD.remove(DEN_SAVE_PATH);
  File f = SD.open(DEN_SAVE_PATH, FILE_WRITE);
  if (f) {
    f.write(reinterpret_cast<const uint8_t*>(&s), sizeof(s));
    f.flush();
    f.close();
    gSaveDirty = false;
    gLastSave = now;
  }
}

static void loadProgress() {
  if (!gSdReady) return;
  File f = SD.open(DEN_SAVE_PATH, FILE_READ);
  if (!f) return;

  size_t sz = f.size();
  if (sz == sizeof(DenSaveV2)) {
    DenSaveV2 s{};
    size_t got = f.read(reinterpret_cast<uint8_t*>(&s), sizeof(s));
    f.close();
    if (got == sizeof(s) && s.magic == DEN_MAGIC && s.version == DEN_VERSION &&
        s.hashCount <= MAX_HASHES && saveCrcV2(s) == s.crc) {
      gXp = s.xp;
      gUniqueAps = s.uniqueAps;
      gScans = s.scans;
      gBleSeen = s.bleSeen;
      gProbesSeen = s.probesSeen;
      gEapolSeen = s.eapolSeen;
      gPacketsSeen = s.packetsSeen;
      gHashCount = s.hashCount;
      memcpy(gHashes, s.hashes, sizeof(gHashes));
    }
    return;
  }

  if (sz == sizeof(DenSaveV1)) {
    DenSaveV1 s{};
    size_t got = f.read(reinterpret_cast<uint8_t*>(&s), sizeof(s));
    f.close();
    if (got == sizeof(s) && s.magic == DEN_MAGIC && s.version == 1 &&
        s.hashCount <= MAX_HASHES && saveCrcV1(s) == s.crc) {
      gXp = s.xp;
      gUniqueAps = s.totalSeen;
      gScans = s.scans;
      gHashCount = s.hashCount;
      memcpy(gHashes, s.hashes, sizeof(gHashes));
      gSaveDirty = true; // migrate on next save
      addEvent("Cyber profile migrated", false);
    }
    return;
  }

  f.close();
}

// -----------------------------------------------------------------------------
// Passive Wi-Fi scanner
// -----------------------------------------------------------------------------
static void stopSniffer();

static void startWifiScan() {
  if (gWifiScanRunning) return;
  stopSniffer();
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, false);
  WiFi.scanDelete();
  int16_t rc = WiFi.scanNetworks(true, true, true, 220);
  if (rc == WIFI_SCAN_FAILED) {
    addEvent("WiFi scan failed");
    gWifiScanRunning = false;
    return;
  }
  gWifiScanRunning = true;
  gWifiScanAt = millis();
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

static void finishWifiScan(int16_t n) {
  gApCount = 0;
  gApSel = 0;
  gWifiTop = 0;
  memset(gChannelCounts, 0, sizeof(gChannelCounts));
  uint16_t newCount = 0;

  if (n < 0) n = 0;
  for (int i = 0; i < n; ++i) {
    DenAp ap{};
    String ss = WiFi.SSID(i);
    if (!ss.length()) ss = "<hidden>";
    ss.toCharArray(ap.ssid, sizeof(ap.ssid));
    String bs = WiFi.BSSIDstr(i);
    bs.toCharArray(ap.bssid, sizeof(ap.bssid));
    ap.rssi = WiFi.RSSI(i);
    int ch = WiFi.channel(i);
    ap.channel = (uint8_t)(ch < 0 ? 0 : ch);
    ap.open = WiFi.encryptionType(i) == WIFI_AUTH_OPEN;
    const uint8_t *b = WiFi.BSSID(i);
    ap.hash = b ? fnv1a(b, 6) : fnv1a(reinterpret_cast<const uint8_t*>(ap.ssid), strlen(ap.ssid));
    if (!ap.hash) ap.hash = 1;

    if (ap.channel >= 1 && ap.channel <= 13) ++gChannelCounts[ap.channel];
    if (!hashKnown(ap.hash)) {
      rememberHash(ap.hash);
      ++gUniqueAps;
      ++newCount;
      awardXp(6);
    }
    addApSorted(ap);
  }

  ++gScans;
  gSaveDirty = true;
  if (n > 0) awardXp((uint16_t)(n > 12 ? 12 : n));

  char ev[44];
  snprintf(ev, sizeof(ev), "WiFi sweep %d AP / %u new", (int)n, newCount);
  addEvent(ev);
  WiFi.scanDelete();
  gWifiScanRunning = false;
  gWifiScanPending = false;
  saveProgress();
}

// -----------------------------------------------------------------------------
// Passive BLE scanner
// -----------------------------------------------------------------------------
static void performBleScan() {
  gBleScanPending = false;
  gBleScanBusy = true;
  gBleCount = 0;
  gBleSel = 0;
  gBleTop = 0;
  stopSniffer();

  BLEDevice::init("");
  BLEScan *scan = BLEDevice::getScan();
  scan->setActiveScan(false);
  scan->setInterval(120);
  scan->setWindow(90);
  BLEScanResults results = scan->start(2, false);
  int found = results.getCount();
  int n = found > MAX_BLE ? MAX_BLE : found;

  for (int i = 0; i < n; ++i) {
    BLEAdvertisedDevice dev = results.getDevice(i);
    String nm = dev.haveName() ? String(dev.getName().c_str()) : String("<unnamed>");
    nm.toCharArray(gBle[i].name, sizeof(gBle[i].name));
    String ad = String(dev.getAddress().toString().c_str());
    ad.toCharArray(gBle[i].address, sizeof(gBle[i].address));
    gBle[i].rssi = dev.haveRSSI() ? dev.getRSSI() : -127;
    ++gBleCount;
  }

  scan->clearResults();
  BLEDevice::deinit(false);

  if (found > 0) {
    gBleSeen += (uint32_t)found;
    awardXp((uint16_t)((found > 20 ? 20 : found) * 2));
  }
  char ev[44];
  snprintf(ev, sizeof(ev), "BLE sweep %d devices", found);
  addEvent(ev);
  gSaveDirty = true;
  gBleScanBusy = false;
  saveProgress();
}

// -----------------------------------------------------------------------------
// Passive 802.11 monitor
// -----------------------------------------------------------------------------
static bool containsEapol(const uint8_t *frame, size_t len) {
  static const uint8_t snap[] = {0xAA,0xAA,0x03,0x00,0x00,0x00,0x88,0x8E};
  if (!frame || len < sizeof(snap)) return false;
  size_t start = len > 24 ? 20 : 0;
  for (size_t i = start; i + sizeof(snap) <= len; ++i) {
    if (memcmp(frame + i, snap, sizeof(snap)) == 0) return true;
  }
  return false;
}

static void promiscuousCb(void *buf, wifi_promiscuous_pkt_type_t type) {
  if (!buf || gSniffMode == SNIFF_OFF) return;
  const wifi_promiscuous_pkt_t *pkt = reinterpret_cast<const wifi_promiscuous_pkt_t*>(buf);
  const uint8_t *p = pkt->payload;
  size_t len = pkt->rx_ctrl.sig_len;
  if (!p || len < 2) return;

  portENTER_CRITICAL_ISR(&gMux);
  gLastRssi = pkt->rx_ctrl.rssi;
  gLastRxChannel = pkt->rx_ctrl.channel;
  if (type == WIFI_PKT_MGMT) ++gPktMgmt;
  else if (type == WIFI_PKT_DATA) ++gPktData;
  else if (type == WIFI_PKT_CTRL) ++gPktCtrl;

  if (type == WIFI_PKT_MGMT && len >= 24 && (p[0] & 0xFC) == 0x40) {
    ++gProbeSession;
    uint32_t sid = fnv1a(p + 10, 6);
    gLastProbeId = sid;

    size_t pos = 24;
    char ssid[33] = {0};
    strcpy(ssid, "<wildcard>");
    while (pos + 2 <= len) {
      uint8_t id = p[pos];
      uint8_t l = p[pos + 1];
      if (pos + 2 + l > len) break;
      if (id == 0) {
        size_t copy = l > 32 ? 32 : l;
        if (copy) {
          memcpy(ssid, p + pos + 2, copy);
          ssid[copy] = 0;
        }
        break;
      }
      pos += 2 + l;
    }
    strncpy(gLastProbeSsid, ssid, sizeof(gLastProbeSsid) - 1);
    gLastProbeSsid[sizeof(gLastProbeSsid) - 1] = 0;
  }

  if (type == WIFI_PKT_DATA && containsEapol(p, len)) ++gEapolSession;
  portEXIT_CRITICAL_ISR(&gMux);
}

static void startSniffer(SniffMode mode) {
  if (mode == SNIFF_OFF) return;
  if (gSniffMode == mode) return;
  stopSniffer();

  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, false);
  delay(10);

  wifi_promiscuous_filter_t filter{};
  filter.filter_mask = WIFI_PROMIS_FILTER_MASK_MGMT |
                       WIFI_PROMIS_FILTER_MASK_DATA |
                       WIFI_PROMIS_FILTER_MASK_CTRL;
  esp_wifi_set_promiscuous_filter(&filter);
  esp_wifi_set_promiscuous_rx_cb(&promiscuousCb);
  gChannel = 1;
  esp_wifi_set_channel(gChannel, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(true);
  gSniffMode = mode;
  gLastHop = millis();
}

static void stopSniffer() {
  if (gSniffMode != SNIFF_OFF) esp_wifi_set_promiscuous(false);
  gSniffMode = SNIFF_OFF;
}

static void syncPassiveCounters(uint32_t now) {
  uint32_t mg, da, ct, pr, ea;
  portENTER_CRITICAL(&gMux);
  mg = gPktMgmt;
  da = gPktData;
  ct = gPktCtrl;
  pr = gProbeSession;
  ea = gEapolSession;
  portEXIT_CRITICAL(&gMux);

  uint32_t pkt = mg + da + ct;
  if (pkt >= gPrevPktTotal) {
    uint32_t d = pkt - gPrevPktTotal;
    gPacketsSeen += d;
    if (d >= 50) awardXp((uint16_t)(d / 50 > 5 ? 5 : d / 50));
  }
  gPrevPktTotal = pkt;

  if (pr >= gPrevProbe) {
    uint32_t d = pr - gPrevProbe;
    gProbesSeen += d;
    if (d) awardXp((uint16_t)(d > 4 ? 4 : d));
  }
  gPrevProbe = pr;

  if (ea >= gPrevEapol) {
    uint32_t d = ea - gPrevEapol;
    if (d) {
      gEapolSeen += d;
      awardXp((uint16_t)(d > 4 ? 60 : d * 15));
      if (now - gLastEapolEvent > 3000UL) {
        char ev[44];
        snprintf(ev, sizeof(ev), "Passive EAPOL metadata +%lu", (unsigned long)d);
        addEvent(ev);
        gLastEapolEvent = now;
      }
    }
  }
  gPrevEapol = ea;

  if (pkt || pr || ea) gSaveDirty = true;
}

static void setPage(DenPage p) {
  if (gPage == p) return;
  stopSniffer();
  gPage = p;
  gPageAt = millis();
  gMascotDex = -999;

  if (p == PAGE_PWN_PET) startSniffer(SNIFF_PWN);
  else if (p == PAGE_HANDSHAKE) startSniffer(SNIFF_HANDSHAKE);
  else if (p == PAGE_PROBES) startSniffer(SNIFF_PROBES);
  else if (p == PAGE_PACKETS) startSniffer(SNIFF_PACKETS);
}

static void openLab(const char *title, const char *line1, const char *line2, uint8_t ghost) {
  gLabTitle = title;
  gLabLine1 = line1;
  gLabLine2 = line2;
  gLabGhost = ghost;
  gLabPulse = false;
  setPage(PAGE_LAB);
}

static void openMenuItem() {
  switch (gMenu) {
    case 0: setPage(PAGE_PWN_PET); break;
    case 1: gWifiScanPending = true; setPage(PAGE_WIFI_LIST); break;
    case 2: setPage(PAGE_HANDSHAKE); break;
    case 3: setPage(PAGE_PROBES); break;
    case 4: openLab("DEAUTH", "AUTHORIZED LAB TRAINER", "TX DISABLED - SAFE DEMO", 94); break;
    case 5: openLab("EVIL TWIN", "ROGUE AP VISUAL TRAINER", "NO CREDENTIAL COLLECTION", 93); break;
    case 6: openLab("KARMA", "PROBE RESPONSE TRAINER", "TX DISABLED - SAFE DEMO", 92); break;
    case 7: gBleScanPending = true; setPage(PAGE_BLE); break;
    case 8: openLab("BLE SPAM", "ADVERTISING LAB TRAINER", "NO FLOOD TRANSMISSION", 94); break;
    case 9: setPage(PAGE_PACKETS); break;
    case 10: setPage(PAGE_LOGS); break;
    case 11: setPage(PAGE_PROFILE); break;
  }
}

// -----------------------------------------------------------------------------
// Page drawing
// -----------------------------------------------------------------------------
static void drawMenuIcon(M5Canvas &ui, int idx, int x, int y, uint16_t c) {
  switch (idx) {
    case 0: ui.fillCircle(x + 6, y + 6, 5, c); ui.fillCircle(x + 4, y + 5, 1, C_BG); ui.fillCircle(x + 8, y + 5, 1, C_BG); break;
    case 1: case 2: case 3:
      ui.drawCircle(x + 6, y + 6, 5, c); ui.drawCircle(x + 6, y + 6, 2, C_CYAN); ui.drawLine(x + 6, y + 6, x + 12, y + 1, C_MAGENTA); break;
    case 4: ui.drawTriangle(x + 1, y + 1, x + 12, y + 1, x + 6, y + 11, c); break;
    case 5: ui.drawRoundRect(x, y + 2, 6, 8, 2, c); ui.drawRoundRect(x + 7, y + 2, 6, 8, 2, C_MAGENTA); break;
    case 6: ui.drawFastVLine(x + 1, y + 2, 7, c); ui.drawFastVLine(x + 11, y + 2, 7, c); ui.drawFastHLine(x + 1, y + 8, 11, C_CYAN); break;
    case 7: case 8:
      ui.drawLine(x + 6, y, x + 6, y + 11, c); ui.drawLine(x + 6, y, x + 11, y + 4, C_CYAN); ui.drawLine(x + 11, y + 4, x + 3, y + 8, C_CYAN); ui.drawLine(x + 3, y + 3, x + 11, y + 8, c); break;
    case 9: ui.fillRect(x, y + 7, 2, 4, c); ui.fillRect(x + 4, y + 4, 2, 7, C_CYAN); ui.fillRect(x + 8, y + 1, 2, 10, c); ui.fillRect(x + 12, y + 5, 2, 6, C_MAGENTA); break;
    case 10: for (int i = 0; i < 3; ++i) ui.drawFastHLine(x, y + 2 + i * 4, 13, i == 0 ? C_MAGENTA : c); break;
    case 11: ui.drawCircle(x + 6, y + 4, 3, C_GOLD); ui.drawTriangle(x + 2, y + 10, x + 10, y + 10, x + 6, y + 6, c); break;
  }
}

static void drawMenu(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  char tag[20];
  snprintf(tag, sizeof(tag), "LV%u  %u/8", cyberLevel(), badgeCount());
  drawHeader(ui, "CYBER DEN", tag);

  if (gMenu < gMenuTop) gMenuTop = gMenu;
  if (gMenu >= gMenuTop + 6) gMenuTop = gMenu - 5;

  for (int row = 0; row < 6; ++row) {
    int idx = gMenuTop + row;
    if (idx >= 12) break;
    int y = 28 + row * 15;
    bool sel = idx == gMenu;
    if (sel) {
      ui.fillRoundRect(5, y - 1, 163, 14, 4, C_PANEL2);
      ui.drawRoundRect(5, y - 1, 163, 14, 4, C_MAGENTA);
    }
    drawMenuIcon(ui, idx, 10, y, sel ? C_CYAN : C_PURPLE);
    ui.setTextColor(sel ? C_INK : C_DIM);
    ui.drawString(MENU_ITEMS[idx], 31, y + 2);
  }

  panel(ui, 174, 30, 61, 76, C_PANEL, C_PURPLE, 6);
  int ghost = 92 + (gMenu % 3);
  drawPortalRings(ui, 204, 67, now, ghost == 94 ? C_MAGENTA : C_PURPLE);
  drawMascot(ui, ghost, false, 204, 89, now, PMD_IDLE, 1);
  ui.setTextColor(C_PINK);
  ui.drawCentreString(ghost == 92 ? "GASTLY" : (ghost == 93 ? "HAUNTER" : "GENGAR"), 204, 95, 1);

  drawFooter(ui, "ESC HOME", "UP/DN", "ENTER");
}

static void drawPwnPet(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "PWN PET", moodName());

  int dex = (gPetDex >= 1 && gPetDex <= 151) ? gPetDex : 94;
  uint16_t glow = (dex >= 92 && dex <= 94) ? C_MAGENTA : C_CYAN;
  drawPortalRings(ui, 73, 72, now, glow);
  drawMascot(ui, dex, gPetShiny, 73, 102, now, PMD_IDLE, 1);

  panel(ui, 127, 31, 108, 73, C_PANEL, glow, 5);
  ui.setTextColor(C_INK);
  ui.drawString(gPetName, 135, 38);

  char line[38];
  snprintf(line, sizeof(line), "PWN LV %u", cyberLevel());
  ui.setTextColor(C_CYAN);
  ui.drawString(line, 135, 53);
  snprintf(line, sizeof(line), "XP %lu", (unsigned long)gXp);
  ui.setTextColor(C_PINK);
  ui.drawString(line, 135, 66);
  snprintf(line, sizeof(line), "BADGES %u/8", badgeCount());
  ui.setTextColor(C_GOLD);
  ui.drawString(line, 135, 79);
  snprintf(line, sizeof(line), "AP %lu  BLE %lu", (unsigned long)gUniqueAps, (unsigned long)gBleSeen);
  ui.setTextColor(C_DIM);
  ui.drawString(line, 135, 92);

  ui.setTextColor(C_DIM);
  ui.drawCentreString("Passive signals feed Cyber XP", 120, 108, 1);
  drawFooter(ui, "ESC MENU", "SPECTRAL LINK", "PASSIVE");
}

static void drawWifiList(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  char tag[18];
  snprintf(tag, sizeof(tag), "%u AP", gApCount);
  drawHeader(ui, "WIFI SCANNER", tag);

  if (gWifiScanRunning) {
    const char spin[] = {'|','/','-','\\'};
    char s[36];
    snprintf(s, sizeof(s), "%c PASSIVE SWEEP...", spin[(now / 150) & 3]);
    ui.setTextColor(C_CYAN);
    ui.drawCentreString(s, 120, 66, 1);
    ui.setTextColor(C_DIM);
    ui.drawCentreString("Listening for nearby AP beacons", 120, 82, 1);
  } else if (!gApCount) {
    ui.setTextColor(C_DIM);
    ui.drawCentreString("No scan results yet", 120, 57, 1);
    ui.setTextColor(C_CYAN);
    ui.drawCentreString("ENTER = passive scan", 120, 75, 1);
  } else {
    if (gApSel < gWifiTop) gWifiTop = gApSel;
    if (gApSel >= gWifiTop + 5) gWifiTop = gApSel - 4;
    for (int row = 0; row < 5; ++row) {
      int idx = gWifiTop + row;
      if (idx >= gApCount) break;
      int y = 29 + row * 17;
      bool sel = idx == gApSel;
      const DenAp &ap = gAps[idx];
      if (sel) ui.fillRoundRect(5, y - 1, 230, 15, 4, C_PANEL2);
      ui.setTextColor(sel ? C_INK : (ap.open ? C_GOLD : C_DIM));
      ui.drawString(ap.ssid, 9, y + 2);
      char meta[26];
      snprintf(meta, sizeof(meta), "CH%u  %ddBm", ap.channel, ap.rssi);
      ui.setTextColor(ap.open ? C_GOLD : C_CYAN);
      ui.drawRightString(meta, 231, y + 2, 1);
    }
  }
  drawFooter(ui, "ESC MENU", "ENTER SCAN", "RIGHT INFO");
}

static void drawWifiSpectrum(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "WIFI SPECTRUM", "CH 1-13");
  panel(ui, 8, 31, 224, 78, C_PANEL, C_PURPLE, 5);

  uint8_t maxCount = 1;
  for (int ch = 1; ch <= 13; ++ch) if (gChannelCounts[ch] > maxCount) maxCount = gChannelCounts[ch];
  for (int ch = 1; ch <= 13; ++ch) {
    int x = 15 + (ch - 1) * 16;
    int h = 55 * gChannelCounts[ch] / maxCount;
    uint16_t c = ch == 1 || ch == 6 || ch == 11 ? C_MAGENTA : C_CYAN;
    if (h > 0) ui.fillRoundRect(x, 92 - h, 10, h, 2, c);
    char n[4]; snprintf(n, sizeof(n), "%d", ch);
    ui.setTextColor(C_DIM);
    ui.drawCentreString(n, x + 5, 96, 1);
  }
  drawFooter(ui, "LEFT INFO", "ENTER SCAN", "RIGHT LIST");
}

static void drawWifiDetail(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "NETWORK DETAIL", "PASSIVE");
  if (!gApCount) {
    ui.setTextColor(C_DIM);
    ui.drawCentreString("No selected network", 120, 66, 1);
    drawFooter(ui, "ESC MENU", "", "");
    return;
  }
  const DenAp &ap = gAps[gApSel];
  panel(ui, 10, 31, 220, 76, C_PANEL, ap.open ? C_GOLD : C_PURPLE, 6);
  ui.setTextColor(C_INK);
  ui.drawString(ap.ssid, 18, 39);
  char line[42];
  snprintf(line, sizeof(line), "BSSID %s", ap.bssid);
  ui.setTextColor(C_DIM); ui.drawString(line, 18, 56);
  snprintf(line, sizeof(line), "RSSI %d dBm     CHANNEL %u", ap.rssi, ap.channel);
  ui.setTextColor(C_CYAN); ui.drawString(line, 18, 73);
  snprintf(line, sizeof(line), "SECURITY %s", ap.open ? "OPEN" : "PROTECTED");
  ui.setTextColor(ap.open ? C_GOLD : C_GREEN); ui.drawString(line, 18, 90);
  drawFooter(ui, "LEFT LIST", "ENTER SCAN", "RIGHT GRAPH");
}

static void drawHandshake(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "HANDSHAKE CAPTURE", "PASSIVE");
  drawMascot(ui, 94, false, 49, 87, now, PMD_POSE, 1);

  panel(ui, 89, 31, 145, 77, C_PANEL, C_MAGENTA, 6);
  ui.setTextColor(C_PINK);
  ui.drawString("EAPOL WATCH", 99, 39);
  char line[42];
  snprintf(line, sizeof(line), "SESSION %lu", (unsigned long)gEapolSession);
  ui.setTextColor(C_INK); ui.drawString(line, 99, 56);
  snprintf(line, sizeof(line), "TOTAL   %lu", (unsigned long)gEapolSeen);
  ui.setTextColor(C_CYAN); ui.drawString(line, 99, 70);
  snprintf(line, sizeof(line), "CHANNEL %u  RSSI %ddBm", gLastRxChannel, (int)gLastRssi);
  ui.setTextColor(C_DIM); ui.drawString(line, 99, 84);
  ui.setTextColor(C_GOLD); ui.drawString("NO DEAUTH / NO RAW KEYS SAVED", 99, 97);
  drawFooter(ui, "ESC MENU", "AUTO CHANNEL HOP", "LISTEN");
}

static void drawProbes(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "PROBE SNIFFER", "PASSIVE");
  drawMascot(ui, 92, false, 49, 87, now, PMD_IDLE, 1);
  panel(ui, 89, 31, 145, 77, C_PANEL, C_VIOLET, 6);
  char line[44];
  ui.setTextColor(C_PINK); ui.drawString("LAST REQUEST", 99, 39);
  ui.setTextColor(C_INK); ui.drawString(gLastProbeSsid[0] ? gLastProbeSsid : "<waiting>", 99, 55);
  snprintf(line, sizeof(line), "CLIENT ID %06lX", (unsigned long)(gLastProbeId & 0xFFFFFFUL));
  ui.setTextColor(C_DIM); ui.drawString(line, 99, 70);
  snprintf(line, sizeof(line), "SESSION %lu  TOTAL %lu", (unsigned long)gProbeSession, (unsigned long)gProbesSeen);
  ui.setTextColor(C_CYAN); ui.drawString(line, 99, 84);
  snprintf(line, sizeof(line), "CH %u  RSSI %ddBm", gLastRxChannel, (int)gLastRssi);
  ui.setTextColor(C_GOLD); ui.drawString(line, 99, 98);
  drawFooter(ui, "ESC MENU", "SSID METADATA", "LISTEN");
}

static void drawBle(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  char tag[18]; snprintf(tag, sizeof(tag), "%u DEV", gBleCount);
  drawHeader(ui, "BLE SCANNER", tag);
  if (gBleScanBusy) {
    ui.setTextColor(C_CYAN);
    ui.drawCentreString("PASSIVE BLE SWEEP...", 120, 64, 1);
  } else if (!gBleCount) {
    ui.setTextColor(C_DIM);
    ui.drawCentreString("No BLE results yet", 120, 58, 1);
    ui.setTextColor(C_CYAN);
    ui.drawCentreString("ENTER = passive scan", 120, 76, 1);
  } else {
    if (gBleSel < gBleTop) gBleTop = gBleSel;
    if (gBleSel >= gBleTop + 4) gBleTop = gBleSel - 3;
    for (int row = 0; row < 4; ++row) {
      int idx = gBleTop + row;
      if (idx >= gBleCount) break;
      int y = 30 + row * 21;
      bool sel = idx == gBleSel;
      if (sel) ui.fillRoundRect(5, y - 1, 230, 19, 4, C_PANEL2);
      ui.setTextColor(sel ? C_INK : C_DIM); ui.drawString(gBle[idx].name, 9, y + 1);
      ui.setTextColor(C_CYAN); ui.drawRightString(String(gBle[idx].rssi) + "dBm", 231, y + 1, 1);
      ui.setTextColor(C_PURPLE); ui.drawString(gBle[idx].address, 9, y + 10);
    }
  }
  drawFooter(ui, "ESC MENU", "ENTER SCAN", "PASSIVE");
}

static void drawPackets(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "PACKET MONITOR", "PASSIVE");
  panel(ui, 10, 31, 220, 75, C_PANEL, C_CYAN, 6);
  uint32_t total = gPktMgmt + gPktData + gPktCtrl;
  uint32_t maxv = gPktMgmt;
  if (gPktData > maxv) maxv = gPktData;
  if (gPktCtrl > maxv) maxv = gPktCtrl;
  if (maxv < 1) maxv = 1;
  const char *lab[3] = {"MGMT", "DATA", "CTRL"};
  uint32_t val[3] = {gPktMgmt, gPktData, gPktCtrl};
  uint16_t col[3] = {C_MAGENTA, C_CYAN, C_GOLD};
  for (int i = 0; i < 3; ++i) {
    int y = 40 + i * 19;
    ui.setTextColor(C_INK); ui.drawString(lab[i], 18, y);
    int w = (int)(128UL * val[i] / maxv);
    ui.fillRoundRect(63, y + 2, 132, 7, 3, C_BG2);
    if (w) ui.fillRoundRect(65, y + 4, w, 3, 2, col[i]);
    char n[18]; snprintf(n, sizeof(n), "%lu", (unsigned long)val[i]);
    ui.setTextColor(col[i]); ui.drawRightString(n, 219, y, 1);
  }
  char t[40]; snprintf(t, sizeof(t), "SESSION %lu   ALL-TIME %lu", (unsigned long)total, (unsigned long)gPacketsSeen);
  ui.setTextColor(C_DIM); ui.drawCentreString(t, 120, 96, 1);
  drawFooter(ui, "ESC MENU", "AUTO CHANNEL HOP", "LISTEN");
}

static void drawLogs(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "CYBER LOGS", gSdReady ? "SD+RAM" : "RAM");
  if (!gEventCount) {
    ui.setTextColor(C_DIM);
    ui.drawCentreString("No events yet", 120, 66, 1);
  } else {
    for (int i = 0; i < gEventCount; ++i) {
      int idx = (int)gEventHead - 1 - i;
      while (idx < 0) idx += EVENT_LINES;
      int y = 32 + i * 16;
      ui.fillRoundRect(8, y - 2, 224, 13, 3, (i & 1) ? C_PANEL : C_PANEL2);
      ui.setTextColor(i == 0 ? C_PINK : C_DIM);
      ui.drawString(gEvents[idx], 13, y);
    }
  }
  drawFooter(ui, "ESC MENU", "/cyberden/events.log", "METADATA");
}

static void drawBadge(M5Canvas &ui, int idx, int x, int y, bool unlocked) {
  uint16_t c = unlocked ? (idx & 1 ? C_MAGENTA : C_CYAN) : C_PANEL2;
  ui.fillCircle(x, y, 6, c);
  ui.drawCircle(x, y, 6, unlocked ? C_INK : C_DIM);
  if (unlocked) drawStar(ui, x, y, C_INK);
}

static void drawProfile(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, "CYBER PROFILE", "GHOST BADGES");
  drawMascot(ui, 94, false, 49, 88, now, PMD_POSE, 1);
  panel(ui, 86, 31, 148, 53, C_PANEL, C_MAGENTA, 6);
  char line[44];
  snprintf(line, sizeof(line), "PWN LEVEL %u   XP %lu", cyberLevel(), (unsigned long)gXp);
  ui.setTextColor(C_INK); ui.drawString(line, 95, 39);
  snprintf(line, sizeof(line), "AP %lu   BLE %lu", (unsigned long)gUniqueAps, (unsigned long)gBleSeen);
  ui.setTextColor(C_CYAN); ui.drawString(line, 95, 53);
  snprintf(line, sizeof(line), "PROBE %lu  EAPOL %lu", (unsigned long)gProbesSeen, (unsigned long)gEapolSeen);
  ui.setTextColor(C_PINK); ui.drawString(line, 95, 67);

  bool unlocked[8] = {
    gUniqueAps >= 10,
    gUniqueAps >= 50,
    gProbesSeen >= 25,
    gPacketsSeen >= 1000,
    gEapolSeen >= 1,
    gBleSeen >= 25,
    gScans >= 25,
    cyberLevel() >= 10
  };
  for (int i = 0; i < 8; ++i) drawBadge(ui, i, 78 + i * 20, 99, unlocked[i]);
  ui.setTextColor(C_DIM);
  ui.drawString("SCOUT SEEKER PROBE SPECTER ECHO BLE SWEEP BOND", 9, 109);
  drawFooter(ui, "ESC MENU", "8 BADGES", "PERSISTENT");
}

static void drawLab(M5Canvas &ui, uint32_t now) {
  drawBackground(ui, now);
  drawHeader(ui, gLabTitle.c_str(), "AUTHORIZED LAB");
  int pulse = gLabPulse ? 1 + (int)((now / 180) % 3) : 0;
  for (int i = 0; i < pulse; ++i) ui.drawCircle(59, 72, 24 + i * 8, i & 1 ? C_MAGENTA : C_PURPLE);
  drawMascot(ui, gLabGhost, false, 59, 99, now, PMD_ATTACK, 1);
  panel(ui, 103, 35, 130, 65, C_PANEL, C_GOLD, 6);
  ui.setTextColor(C_INK); ui.drawCentreString(gLabLine1.c_str(), 168, 47, 1);
  ui.setTextColor(C_GOLD); ui.drawCentreString(gLabLine2.c_str(), 168, 65, 1);
  ui.setTextColor(gLabPulse ? C_CYAN : C_DIM);
  ui.drawCentreString(gLabPulse ? "VISUAL SIMULATION ON" : "ENTER: VISUAL SIMULATION", 168, 83, 1);
  ui.setTextColor(C_DIM);
  ui.drawCentreString("No disruptive/spoofing TX", 120, 108, 1);
  drawFooter(ui, "ESC MENU", "SAFE TRAINER", "ENTER TOGGLE");
}

} // namespace

// -----------------------------------------------------------------------------
// Public API
// -----------------------------------------------------------------------------
void cyberDenBegin(bool sdReady) {
  gSdReady = sdReady;
  loadProgress();
  addEvent("Cyber Den ready", false);
}

void cyberDenSetPet(int16_t dex, bool shiny, const char *name) {
  gPetDex = dex;
  gPetShiny = shiny;
  if (name && *name) {
    strncpy(gPetName, name, sizeof(gPetName) - 1);
    gPetName[sizeof(gPetName) - 1] = 0;
  } else {
    strcpy(gPetName, "PWN PET");
  }
}

void cyberDenEnter() {
  gActive = true;
  gPage = PAGE_MENU;
  gMenu = 0;
  gMenuTop = 0;
  gEnterAt = millis();
  gPageAt = gEnterAt;
  gMascotDex = -999;
  addEvent("Cyber Den link opened");
}

void cyberDenLeave() {
  stopSniffer();
  if (gWifiScanRunning) WiFi.scanDelete();
  gWifiScanRunning = false;
  gWifiScanPending = false;
  gBleScanPending = false;
  gActive = false;
  gMascot.unload();
  gMascotDex = -999;
  saveProgress(true);
  WiFi.mode(WIFI_OFF);
}

void cyberDenUpdate(uint32_t nowMs) {
  if (!gActive) {
    saveProgress();
    return;
  }

  if (gWifiScanPending && !gWifiScanRunning) startWifiScan();
  if (gWifiScanRunning) {
    int16_t n = WiFi.scanComplete();
    if (n >= 0) finishWifiScan(n);
    else if (n == WIFI_SCAN_FAILED || nowMs - gWifiScanAt > 15000UL) {
      WiFi.scanDelete();
      gWifiScanRunning = false;
      gWifiScanPending = false;
      addEvent("WiFi scan timeout");
    }
  }

  if (gBleScanPending && !gBleScanBusy) performBleScan();

  if (gSniffMode != SNIFF_OFF && nowMs - gLastHop >= 420UL) {
    gLastHop = nowMs;
    gChannel = gChannel >= 13 ? 1 : gChannel + 1;
    esp_wifi_set_channel(gChannel, WIFI_SECOND_CHAN_NONE);
  }

  if (gSniffMode != SNIFF_OFF) syncPassiveCounters(nowMs);
  saveProgress();
}

void cyberDenDraw(M5Canvas &ui, uint32_t nowMs) {
  if (!gActive) return;
  if (nowMs - gEnterAt < 1650UL) {
    drawPortalIntro(ui, nowMs);
    return;
  }

  switch (gPage) {
    case PAGE_MENU:          drawMenu(ui, nowMs); break;
    case PAGE_PWN_PET:       drawPwnPet(ui, nowMs); break;
    case PAGE_WIFI_LIST:     drawWifiList(ui, nowMs); break;
    case PAGE_WIFI_SPECTRUM: drawWifiSpectrum(ui, nowMs); break;
    case PAGE_WIFI_DETAIL:   drawWifiDetail(ui, nowMs); break;
    case PAGE_HANDSHAKE:     drawHandshake(ui, nowMs); break;
    case PAGE_PROBES:        drawProbes(ui, nowMs); break;
    case PAGE_BLE:           drawBle(ui, nowMs); break;
    case PAGE_PACKETS:       drawPackets(ui, nowMs); break;
    case PAGE_LOGS:          drawLogs(ui, nowMs); break;
    case PAGE_PROFILE:       drawProfile(ui, nowMs); break;
    case PAGE_LAB:           drawLab(ui, nowMs); break;
  }
}

bool cyberDenHandleInput(bool upEdge,
                         bool downEdge,
                         bool leftEdge,
                         bool rightEdge,
                         bool enterEdge,
                         bool spaceEdge,
                         bool escEdge,
                         bool backEdge) {
  if (!gActive) return true;

  // Any key skips the short Gastly -> Haunter -> Gengar portal intro.
  if (millis() - gEnterAt < 1650UL &&
      (upEdge || downEdge || leftEdge || rightEdge || enterEdge || spaceEdge || escEdge || backEdge)) {
    gEnterAt = millis() - 1650UL;
    if (escEdge || backEdge) return true;
    return false;
  }

  if (escEdge || backEdge) {
    if (gPage == PAGE_MENU) return true;
    setPage(PAGE_MENU);
    return false;
  }

  if (gPage == PAGE_MENU) {
    if (upEdge) gMenu = gMenu == 0 ? 11 : gMenu - 1;
    if (downEdge) gMenu = (gMenu + 1) % 12;
    if (leftEdge) return true;
    if (rightEdge || enterEdge || spaceEdge) openMenuItem();
    return false;
  }

  if (gPage == PAGE_WIFI_LIST) {
    if (gApCount) {
      if (upEdge) gApSel = gApSel == 0 ? gApCount - 1 : gApSel - 1;
      if (downEdge) gApSel = (gApSel + 1) % gApCount;
    }
    if (enterEdge || spaceEdge) gWifiScanPending = true;
    if (rightEdge && gApCount) setPage(PAGE_WIFI_DETAIL);
    if (leftEdge) setPage(PAGE_MENU);
    return false;
  }

  if (gPage == PAGE_WIFI_DETAIL) {
    if (leftEdge) setPage(PAGE_WIFI_LIST);
    if (rightEdge) setPage(PAGE_WIFI_SPECTRUM);
    if (enterEdge || spaceEdge) { gWifiScanPending = true; setPage(PAGE_WIFI_LIST); }
    return false;
  }

  if (gPage == PAGE_WIFI_SPECTRUM) {
    if (leftEdge) setPage(PAGE_WIFI_DETAIL);
    if (rightEdge) setPage(PAGE_WIFI_LIST);
    if (enterEdge || spaceEdge) { gWifiScanPending = true; setPage(PAGE_WIFI_LIST); }
    return false;
  }

  if (gPage == PAGE_BLE) {
    if (gBleCount) {
      if (upEdge) gBleSel = gBleSel == 0 ? gBleCount - 1 : gBleSel - 1;
      if (downEdge) gBleSel = (gBleSel + 1) % gBleCount;
    }
    if (enterEdge || spaceEdge) gBleScanPending = true;
    if (leftEdge) setPage(PAGE_MENU);
    return false;
  }

  if (gPage == PAGE_LAB) {
    if (enterEdge || spaceEdge || rightEdge) gLabPulse = !gLabPulse;
    if (leftEdge) setPage(PAGE_MENU);
    return false;
  }

  if (leftEdge) setPage(PAGE_MENU);
  return false;
}

bool cyberDenAnimated() {
  return gActive;
}
