# Infinity Gauntlet (NeoForge 1.21.1)

**Still untested in-game:** the code has not been compiled against Minecraft or loaded yet, so expect a few small fixes.
All block IDs and block states used by the structures were validated against the 1.21.1 block list.

## Build (easiest: let GitHub do it)
1. Put this folder in a GitHub repository (include the hidden `.github` folder).
2. Actions tab → **Build mod jar** → Run workflow. Download the `infinitygauntlet-jar` artifact.
3. Drop the jar in your instance's `mods` folder (ATM10 = NeoForge 1.21.1).

Local build: Java 21 + Gradle 8.10+, then `gradle build`. If `neo_version` doesn't resolve, set the latest `21.1.x` in `gradle.properties`.

## What's in it
**Stones** (animated, glowing, each with its own gem cut), the **Infinity Gauntlet**, **Loki's Scepter**, and the **Snap**.

### The gauntlet shows what you have
Six sockets on the item (four knuckles, thumb, back of the hand). Empty sockets are dark; every stone you socket lights up
its slot, and a full gauntlet pulses. (Done with 64 model variants switched by `custom_model_data`.)

### Abilities (3-4 per stone)
| Stone | Abilities |
|---|---|
| Power | Power Blast, Smite, Titan Leap, **Power Beam** (new: piercing beam, never breaks blocks) |
| Space | Blink, Gravity Well, Home Warp |
| Reality | Transmute, Reality Warp, Reality Feast |
| Soul | Soul Heal, Soul Drain, Soul Ward |
| Time | Time Freeze, Time Surge, Chrono Bloom, **Time Rewind** (new: back to where you were ~10 s ago, with that health) |
| Mind | Mind Control, Telepathy, Pacify |
| All six | **Snap**: dusts about half of the hostile mobs nearby, costs health. Config `snapAffectsPassive` extends it to passive mobs (never tamed or name-tagged ones). |

Use: right-click. Cycle ability: sneak + right-click. Socket: stone in the other hand, right-click.

## Where things come from (all MCU locations)
| Item | Structure | Biomes |
|---|---|---|
| Space Stone | **Asgardian Vault** (`tesseract_vault`): rainbow Bifrost bridge, golden hall, the Tesseract in a glass cage | taiga / snowy plains |
| Power Stone | **Morag Temple** (`power_orb_temple`): ruined round temple, broken colonnade, the Orb | badlands / desert |
| Reality Stone | **Aether Shrine** (`aether_chamber`): Dark-Elf pavilion, 36-block ladder shaft, crimson vault with the swirling Aether | plains, desert, savanna, snowy plains, forests |
| Soul Stone | **Vormir** (`vormir`): cliff chasm, Stonekeeper's altar, jump pier; the stone is on a ledge at the bottom. Jump in: the pool breaks your fall (ladder to climb back) | mountains |
| Mind Stone + Scepter | **Hydra Outpost** (`hydra_outpost`): walled base, corner towers, Hydra emblem, lab with containment tubes, vault | forests / plains |
| Time Stone | **Sanctum Sanctorum** (`sanctum_sanctorum`): brick townhouse, round Seal window, library, sling-ring portal, the Eye on its altar | plains, meadow, cherry grove |
| Gauntlet | Crafting (gold blocks, netherite, leather) | |

The Time Stone can still be crafted as a fallback (echo shards, clocks, nether star). Delete
`data/infinitygauntlet/recipe/time_stone.json` (or override it in a datapack) to make it structure-only.
The Vormir altar chest holds only treasure; the stone is at the bottom.

## Modpack hooks
- `config/infinitygauntlet-common.toml`: damage/cooldown multipliers, snap tuning, disable abilities or dimensions.
- Tag `infinitygauntlet:snap_immune` (entity types): add modded bosses.
- Tag `infinitygauntlet:infinity_stones` (items).
- `AbilityUseEvent` on `NeoForge.EVENT_BUS` is cancellable.
- Structures, loot, biome tags and structure sets are plain datapack files and can be overridden.
- Locate with `/locate structure infinitygauntlet:vormir` (or any structure name above).

## Regenerating art and structures
`pip install pillow`, then `python3 tools/generate_resources.py`.
- `tools/tex.py`: textures (32x32, animated stones, 64 gauntlet variants, scepter)
- `tools/structs.py`: all six structures (plain Python, one function each)
