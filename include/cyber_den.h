#pragma once

#include <Arduino.h>
#include <M5GFX.h>

// Cyber Den beta: a passive, Pwnagotchi-inspired Wi-Fi companion layer.
// It observes nearby Wi-Fi beacons, tracks discoveries, XP/level/mood, and
// stores lightweight progress on microSD. No deauth/injection/attack actions.

void cyberDenBegin(bool sdReady);
void cyberDenEnter();
void cyberDenLeave();
void cyberDenUpdate(uint32_t nowMs);
void cyberDenDraw(M5Canvas &ui, uint32_t nowMs);

// Returns true when the caller should leave the Cyber Den screen.
bool cyberDenHandleInput(bool upEdge,
                         bool downEdge,
                         bool leftEdge,
                         bool rightEdge,
                         bool enterEdge,
                         bool spaceEdge,
                         bool escEdge,
                         bool backEdge);

bool cyberDenAnimated();
