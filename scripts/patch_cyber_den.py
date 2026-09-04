Import("env")

from pathlib import Path

project_dir = Path(env.subst("$PROJECT_DIR"))
main_path = project_dir / "src" / "main.cpp"
text = main_path.read_text(encoding="utf-8")

if '#include "cyber_den.h"' in text:
    print("CYBER DEN: main.cpp already patched")
    Return()


def replace_once(old, new, label):
    global text
    if old not in text:
        raise RuntimeError("CYBER DEN patch failed at: " + label)
    text = text.replace(old, new, 1)


replace_once(
    '#include "user_config.h"\n',
    '#include "user_config.h"\n#include "cyber_den.h"\n',
    "include",
)

replace_once(
    '  TRAIN,\n  RENAME,\n  DIALOG\n};',
    '  TRAIN,\n  RENAME,\n  CYBER_DEN,\n  DIALOG\n};',
    "screen enum",
)

replace_once(
    '''  const char *items[8] = {\n    audioEnabled() ? "SOUND: ON" : "SOUND: OFF",\n    brightnessLabel,\n    timeoutLabel,\n    "SCREEN OFF NOW",\n    "POKEDEX",\n    "CONTROLS",\n    "RELEASE POKEMON",\n    "BACK"\n  };''',
    '''  const char *items[9] = {\n    audioEnabled() ? "SOUND: ON" : "SOUND: OFF",\n    brightnessLabel,\n    timeoutLabel,\n    "SCREEN OFF NOW",\n    "CYBER DEN",\n    "POKEDEX",\n    "CONTROLS",\n    "RELEASE POKEMON",\n    "BACK"\n  };''',
    "settings items",
)

replace_once(
    '  if (top > 2) top = 2;',
    '  if (top > 3) top = 3;',
    "settings scroll max",
)
replace_once(
    '  if (top < 2) ui.drawString("v", 214, 105);',
    '  if (top < 3) ui.drawString("v", 214, 105);',
    "settings scroll indicator",
)

replace_once(
    '    "Any key restores screen",',
    '    "C: Cyber Den   Any key wakes",',
    "help hint",
)

replace_once(
    '''    if (upEdge) {\n      settingsSel = settingsSel == 0 ? 7 : settingsSel - 1;\n      dirty = true;\n    }\n    if (downEdge) {\n      settingsSel = (settingsSel + 1) % 8;\n      dirty = true;\n    }''',
    '''    if (upEdge) {\n      settingsSel = settingsSel == 0 ? 8 : settingsSel - 1;\n      dirty = true;\n    }\n    if (downEdge) {\n      settingsSel = (settingsSel + 1) % 9;\n      dirty = true;\n    }''',
    "settings navigation",
)

replace_once(
    '''      } else if (settingsSel == 4) {\n        dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;\n        screen = DEX_GRID;\n        dexGridDirty = true;\n        dirty = true;\n      } else if (settingsSel == 5) {\n        screen = HELP;\n        dirty = true;\n      } else if (settingsSel == 6) {\n        if (!pet.isEgg()) openDialog(DLG_RELEASE);\n      } else {\n        screen = HOME;\n        dirty = true;\n      }''',
    '''      } else if (settingsSel == 4) {\n        cyberDenSetPet(pet.speciesId, pet.shiny, currentName());\n        cyberDenEnter();\n        screen = CYBER_DEN;\n        dirty = true;\n      } else if (settingsSel == 5) {\n        dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;\n        screen = DEX_GRID;\n        dexGridDirty = true;\n        dirty = true;\n      } else if (settingsSel == 6) {\n        screen = HELP;\n        dirty = true;\n      } else if (settingsSel == 7) {\n        if (!pet.isEgg()) openDialog(DLG_RELEASE);\n      } else {\n        screen = HOME;\n        dirty = true;\n      }''',
    "settings actions",
)

replace_once(
    '''  } else if (screen == HELP) {\n    if (escEdge || backEdge || enterEdge || spaceEdge) {\n      screen = SETTINGS;\n      dirty = true;\n    }''',
    '''  } else if (screen == CYBER_DEN) {\n    bool denKey = upEdge || downEdge || leftEdge || rightEdge ||\n                  enterEdge || spaceEdge || escEdge || backEdge;\n    if (cyberDenHandleInput(upEdge, downEdge, leftEdge, rightEdge,\n                            enterEdge, spaceEdge, escEdge, backEdge)) {\n      cyberDenLeave();\n      screen = HOME;\n      dirty = true;\n    } else if (denKey) {\n      dirty = true;\n    }\n  } else if (screen == HELP) {\n    if (escEdge || backEdge || enterEdge || spaceEdge) {\n      screen = SETTINGS;\n      dirty = true;\n    }''',
    "cyber den input",
)

replace_once(
    '''      } else if (c == 'i' && !pet.isEgg()) {\n        cardPage = 0;''',
    '''      } else if (c == 'c') {\n        cyberDenSetPet(pet.speciesId, pet.shiny, currentName());\n        cyberDenEnter();\n        screen = CYBER_DEN;\n        dirty = true;\n      } else if (c == 'i' && !pet.isEgg()) {\n        cardPage = 0;''',
    "home hotkey",
)

replace_once(
    '''  if (screen == DEX_DETAIL) return true;\n  if (screen == PLAY || screen == TRAIN) return true;''',
    '''  if (screen == DEX_DETAIL) return true;\n  if (screen == CYBER_DEN) return cyberDenAnimated();\n  if (screen == PLAY || screen == TRAIN) return true;''',
    "animated screen",
)

replace_once(
    '''      case HELP:       drawHelp(); break;\n      case PLAY:       drawPlay(now); break;''',
    '''      case HELP:       drawHelp(); break;\n      case CYBER_DEN:  cyberDenDraw(ui, now); break;\n      case PLAY:       drawPlay(now); break;''',
    "render switch",
)

replace_once(
    '''  dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;\n  dirty = true;''',
    '''  cyberDenBegin(sdReady);\n  cyberDenSetPet(pet.speciesId, pet.shiny, currentName());\n  dexCursor = pet.speciesId > 0 ? pet.speciesId : 1;\n  dirty = true;''',
    "setup",
)

replace_once(
    '''  pet.update(now);\n  onKeyboard();\n\n  serviceDisplaySleep(now);''',
    '''  pet.update(now);\n  onKeyboard();\n  cyberDenUpdate(now);\n\n  serviceDisplaySleep(now);''',
    "loop update",
)

main_path.write_text(text, encoding="utf-8")
print("CYBER DEN: patched main.cpp for final-candidate visual build")
