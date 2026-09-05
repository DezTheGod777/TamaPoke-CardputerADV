#pragma once
#include <stdint.h>

enum Sfx : uint8_t {
  SFX_TAP = 0,
  SFX_EAT,
  SFX_PLAY,
  SFX_HEART,
  SFX_HATCH,
  SFX_EVOLVE,
  SFX_MEDAL,
  SFX_DENY,
  SFX_BYE,
  SFX_LEVEL,
  SFX_SLEEP,
  SFX_WAKE,
  SFX_SHINY,
  SFX_DAILY,
  SFX_COIN,
  SFX_RARE,
  SFX_COUNT
};

void audioBegin();
void audioUpdate();
void sfxPlay(uint8_t id);
void cryPlay(uint16_t dex);
void audioSetEnabled(bool on);
bool audioEnabled();
