#pragma once

#include <Arduino.h>
#include <M5GFX.h>

// Cyber Den final-candidate interface.
// Passive discovery/monitoring pages are functional. Deauth, Evil Twin,
// Karma and BLE Spam are intentionally visual lab simulators only: no
// disruptive/spoofing transmission is implemented.

void cyberDenBegin(bool sdReady);
void cyberDenSetPet(int16_t dex, bool shiny, const char *name);
void cyberDenEnter();
void cyberDenLeave();
void cyberDenUpdate(uint32_t nowMs);
void cyberDenDraw(M5Canvas &ui, uint32_t nowMs);

// Returns true only when the caller should leave Cyber Den entirely.
bool cyberDenHandleInput(bool upEdge,
                         bool downEdge,
                         bool leftEdge,
                         bool rightEdge,
                         bool enterEdge,
                         bool spaceEdge,
                         bool escEdge,
                         bool backEdge);

bool cyberDenAnimated();
