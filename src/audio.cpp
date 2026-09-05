#include <M5Cardputer.h>
#include "audio.h"

static bool s_enabled = true;

struct ToneNote {
  uint16_t hz;
  uint16_t ms;
  uint16_t gap;
};

static const ToneNote *s_seq = nullptr;
static uint8_t s_seqCount = 0;
static uint8_t s_seqIndex = 0;
static uint32_t s_nextAt = 0;
static ToneNote s_cry[4];

// Event-only melodies. There is deliberately NO background/biome ambience or
// looping music in Ultimate v0.9.0; every sequence ends on its own.
static const ToneNote SEQ_HATCH[] = {
  {1050,70,25},{1350,70,25},{1750,90,30},{2350,150,0}
};
static const ToneNote SEQ_EVOLVE[] = {
  {850,90,20},{1050,90,20},{1320,100,20},{1660,110,20},{2090,130,25},{2630,210,0}
};
static const ToneNote SEQ_MEDAL[] = {
  {1560,70,20},{1960,70,20},{2340,90,20},{3120,170,0}
};
static const ToneNote SEQ_BYE[] = {
  {1120,120,35},{930,120,35},{760,150,35},{560,230,0}
};
static const ToneNote SEQ_LEVEL[] = {
  {1500,60,15},{1950,70,15},{2600,130,0}
};
static const ToneNote SEQ_SLEEP[] = {
  {1050,110,40},{820,130,40},{620,180,0}
};
static const ToneNote SEQ_WAKE[] = {
  {720,80,20},{1040,90,20},{1540,140,0}
};
static const ToneNote SEQ_SHINY[] = {
  {2300,45,18},{2950,45,18},{3600,70,18},{3100,55,15},{4100,130,0}
};
static const ToneNote SEQ_DAILY[] = {
  {1200,60,18},{1600,60,18},{2050,70,18},{2750,145,0}
};
static const ToneNote SEQ_COIN[] = {
  {2100,45,12},{2850,75,0}
};
static const ToneNote SEQ_RARE[] = {
  {980,70,20},{1470,70,20},{2200,80,20},{3300,90,25},{3900,170,0}
};

static void startSequence(const ToneNote *seq, uint8_t count) {
  if (!s_enabled || !seq || !count) return;
  s_seq = seq;
  s_seqCount = count;
  s_seqIndex = 0;
  s_nextAt = millis();
}

void audioBegin() {
  M5Cardputer.Speaker.setVolume(96);
}

void audioSetEnabled(bool on) {
  s_enabled = on;
  if (!on) {
    s_seq = nullptr;
    s_seqCount = s_seqIndex = 0;
    M5Cardputer.Speaker.stop();
  }
}

bool audioEnabled() {
  return s_enabled;
}

void audioUpdate() {
  if (!s_enabled || !s_seq || s_seqIndex >= s_seqCount) return;
  uint32_t now = millis();
  if ((int32_t)(now - s_nextAt) < 0) return;
  ToneNote n = s_seq[s_seqIndex++];
  if (n.hz && n.ms) M5Cardputer.Speaker.tone(n.hz, n.ms);
  s_nextAt = now + n.ms + n.gap;
  if (s_seqIndex >= s_seqCount) {
    // Keep the last note free to finish; the sequence state can be cleared now.
    s_seq = nullptr;
    s_seqCount = s_seqIndex = 0;
  }
}

void sfxPlay(uint8_t id) {
  if (!s_enabled) return;

  switch (id) {
    case SFX_TAP:
      s_seq = nullptr; M5Cardputer.Speaker.tone(2350, 32); break;
    case SFX_EAT:
      s_seq = nullptr; M5Cardputer.Speaker.tone(1250, 62); break;
    case SFX_PLAY:
      s_seq = nullptr; M5Cardputer.Speaker.tone(1880, 42); break;
    case SFX_HEART:
      s_seq = nullptr; M5Cardputer.Speaker.tone(2780, 82); break;
    case SFX_DENY:
      s_seq = nullptr; M5Cardputer.Speaker.tone(410, 115); break;
    case SFX_HATCH:  startSequence(SEQ_HATCH, sizeof(SEQ_HATCH)/sizeof(SEQ_HATCH[0])); break;
    case SFX_EVOLVE: startSequence(SEQ_EVOLVE, sizeof(SEQ_EVOLVE)/sizeof(SEQ_EVOLVE[0])); break;
    case SFX_MEDAL:  startSequence(SEQ_MEDAL, sizeof(SEQ_MEDAL)/sizeof(SEQ_MEDAL[0])); break;
    case SFX_BYE:    startSequence(SEQ_BYE, sizeof(SEQ_BYE)/sizeof(SEQ_BYE[0])); break;
    case SFX_LEVEL:  startSequence(SEQ_LEVEL, sizeof(SEQ_LEVEL)/sizeof(SEQ_LEVEL[0])); break;
    case SFX_SLEEP:  startSequence(SEQ_SLEEP, sizeof(SEQ_SLEEP)/sizeof(SEQ_SLEEP[0])); break;
    case SFX_WAKE:   startSequence(SEQ_WAKE, sizeof(SEQ_WAKE)/sizeof(SEQ_WAKE[0])); break;
    case SFX_SHINY:  startSequence(SEQ_SHINY, sizeof(SEQ_SHINY)/sizeof(SEQ_SHINY[0])); break;
    case SFX_DAILY:  startSequence(SEQ_DAILY, sizeof(SEQ_DAILY)/sizeof(SEQ_DAILY[0])); break;
    case SFX_COIN:   startSequence(SEQ_COIN, sizeof(SEQ_COIN)/sizeof(SEQ_COIN[0])); break;
    case SFX_RARE:   startSequence(SEQ_RARE, sizeof(SEQ_RARE)/sizeof(SEQ_RARE[0])); break;
    default: break;
  }
  // Start the first note immediately. Remaining notes are advanced by audioUpdate().
  audioUpdate();
}

void cryPlay(uint16_t dex) {
  if (!s_enabled || dex < 1 || dex > 151) return;
  // Original procedural species chirp: stable per species but intentionally not
  // a reproduction of copyrighted game-console Pokemon cries.
  uint16_t base = (uint16_t)(650 + (dex * 37U) % 1150U);
  uint16_t step = (uint16_t)(110 + (dex * 17U) % 290U);
  bool fall = (dex & 1U) != 0;
  s_cry[0] = {base, 55, 15};
  s_cry[1] = {(uint16_t)(fall ? (base > step ? base - step : 360) : base + step), 65, 15};
  s_cry[2] = {(uint16_t)(base + ((dex % 5U) * 80U)), 55, 12};
  s_cry[3] = {(uint16_t)(fall ? base / 2U + 280U : base + step / 2U), 100, 0};
  startSequence(s_cry, 4);
  audioUpdate();
}
