# rmmvlt

RPG Maker MV Localization Thingy

Extract, manage, and patch translations for RPG Maker MV games. There are probably a lot of better solutions to pick from if you're starting a fresh project but this came from a need to localize games that were already shipped. This is in kinda rough shape and only really tooled for our workflow but I figure I'd release it and maybe someone someday will find it useful. Used for the [Osteoblasts](https://store.steampowered.com/app/1450650/Osteoblasts/) and [Ginger's Letter to Santa](https://store.steampowered.com/app/3392430/Gingers_Letter_to_Santa/) Japanese releases!

## Quick Start

```bash
# 1. From /game/ scan your project to extract all translatable strings
python3 rmmvlt.py init

# 2. Export to Excel for a translator
python3 rmmvlt.py export -l ja                    # creates rmmvlt.xlsx, hand this off to a translator

# 3. Import the translated Excel back
python3 rmmvlt.py import translated.xlsx -l ja

# 4. Patch your project files
python3 rmmvlt.py patch -l ja
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Scan project and create `rmmvlt.json` strings file |
| `export -l LANG` | Export strings to Excel for translation |
| `import FILE -l LANG` | Import translated Excel back into strings file |
| `patch -l LANG` | Apply translations to project files |

## Options

```bash
rmmvlt init [-p PROJECT] [-o OUTPUT]
rmmvlt export [-l LANG] [-o XLSX] [strings_file]
rmmvlt import [-s STRINGS] [-o OUTPUT] -l LANG excel_file
rmmvlt patch [-s STRINGS] [-p PROJECT] -l LANG
```

## Workflow

1. **Initialize** once per project to create `rmmvlt.json`
2. **Export** whenever you want to send strings for translation
3. **Import** when you receive translated Excel files back
4. **Patch** to write translations into your game files

Excel format is really rigid, manually mold it back into the original shape before importing (or make Mr. AI do it...)

## Misc Strings

Create `rmmvlt_misc.json` in /game/data/ for other misc strings (like plugin text) that you may want included. These will have to be reinserted yourself.

```json
{
  "misc_strings": [
    {"id": "intro_text", "text": "Welcome to the game!"},
    {"id": "game_over", "text": "Game Over"}
  ]
}
```

## CJK Word Wrap

Throwing in an edited version of YEP_MessageCore.js that will handle CJK wordwrapping. If you already use it this should be a fairly drop in replacement, if the versions are off just rip the extra code out and add it to yours. You'll see it.
