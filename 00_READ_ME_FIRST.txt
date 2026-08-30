TAMAPOKE CARDPUTER ADV v0.8.5.3 - STABLE BIN NAME + GITHUB UPDATER / ONE CLICK BUILD

1. Extract this ZIP.
2. Double-click: 00_BUILD_BIN_ONE_CLICK.bat
3. Wait for BUILD SUCCESSFUL.
4. Explorer opens and highlights the finished BIN.

Preferred output:
  TamaPoke-CardputerADV.bin

DISPLAY FEATURES
- Settings -> BRIGHTNESS:
    10% / 25% / 50% / 75% / 100%
- Settings -> SCREEN OFF:
    OFF / 30 SEC / 1 MIN / 2 MIN / 5 MIN
- Settings -> SCREEN OFF NOW
- Safe screen-off uses backlight only (no hardware LCD sleep)
- Any keyboard key wakes the display
- The wake key is swallowed so it cannot accidentally trigger an action
- Display preferences are remembered on microSD:
    /tamapoke_display.cfg
- Pet/game logic and automatic saving continue while the display is asleep
- Auto screen-off is disabled during active Play/Training minigames

IMPORTANT SAVE COMPATIBILITY
v0.8 deliberately keeps the existing v0.7 pet save format and files:
  /tamapoke_v7_a.bin
  /tamapoke_v7_b.bin

Do NOT delete those files if you want to keep the current pet/progress.

All v0.7 UI, autosave, larger sprites, sharp header and keyboard fixes remain.

V0.8.1 FIX:
- Fixes the C++ declaration-order compile failure introduced in v0.8.

V0.8.2 BLACK-SCREEN FIX:
- Removes M5Cardputer.Display.sleep() / wakeup().
- Screen-off now only sets the backlight to 0.
- Any key restores the selected brightness.
- Automatic screen-off now defaults to OFF.
- Existing /tamapoke_display.cfg may still contain your old timeout setting.
  If the screen turns off automatically, wake it with a key and set SCREEN OFF
  to OFF in Settings once; the new value will be saved.

V0.8.3 ANIMATION FIX:
- Fixes Pokemon suddenly becoming tiny during certain PMD animations.
- Idle/Walk/Sleep/Eat/Hurt/Attack/Pose/Hop/Nod/etc. now share one stable
  pixel scale derived from that Pokemon's IDLE animation.
- Larger action canvases are treated as movement space instead of a reason
  to shrink the Pokemon.
- The existing ~25% larger home-screen Pokemon size is retained.

V0.8.4 SIZE FIX:
- v0.8.3 kept animation size consistent but used the full transparent IDLE
  canvas as its scale reference. Some Pokemon therefore became much too small.
- v0.8.4 measures the actual visible Pokemon pixels inside IDLE.
- That visible size becomes the stable scale for every animation.
- The Pokemon should now remain large and readable without shrinking during
  Walk/Eat/Hurt/Attack/Pose/etc.
- Home screen still receives the existing ~25% size boost.

V0.8.5 UI UPDATE:
- Press number 1 to hide the entire top Pokemon name / level / mood panel.
- Press number 1 again to show it.
- With the panel hidden, the habitat background remains visible in that area.
- The Pokemon is also a small step larger than v0.8.4.
- Animation scale remains stable across Idle/Walk/Eat/Hurt/Attack/etc.

V0.8.5.1 FIX:
- Fixes the build error: edgeChar was not part of this keyboard input system.
- Number 1 now uses chars['1'] + prevChars['1'] rising-edge detection.
- One press toggles the top name/level/status panel once.
- Pokemon size remains exactly the same as v0.8.5.

V0.8.5.2 PUBLISHING UPDATE:
- The preferred merged firmware is now ALWAYS named:
    TamaPoke-CardputerADV.bin
- Future versions can keep this same public firmware filename.
- The app-only PlatformIO image remains versioned separately.
- New helper:
    00_UPDATE_GITHUB_ONE_CLICK.bat
  This clones your existing TamaPoke-CardputerADV repository, updates the
  source files, commits the changes, and pushes them to GitHub.
- Do not delete your GitHub repository or old Releases when updating.

V0.8.5.3 GITHUB BIN CLEANUP:
- Build first. The finished public image is:
    TamaPoke-CardputerADV.bin
- Then run:
    00_UPDATE_GITHUB_ONE_CLICK.bat
- The updater removes old root files matching:
    TamaPoke-CardputerADV-v*-MERGED.bin
- It uploads/keeps only:
    TamaPoke-CardputerADV.bin
  as the current firmware file in the main repository.
- Existing GitHub Releases are NOT deleted.
