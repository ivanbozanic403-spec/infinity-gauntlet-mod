#!/usr/bin/env python3
"""Generates textures, models, structure NBTs and all JSON/data resources.

    pip install pillow
    python3 tools/generate_resources.py

Edit tex.py (textures) or structs.py (structures) and re-run to redesign anything."""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tex, structs  # noqa: E402

RES = os.path.normpath(os.path.join(HERE, '..', 'src', 'main', 'resources'))
MOD = 'infinitygauntlet'
ASSETS = f'assets/{MOD}'


def out(rel, data, mode='w'):
    p = os.path.join(RES, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, mode) as f:
        f.write(data)


def jout(rel, obj):
    out(rel, json.dumps(obj, indent=2) + '\n')


# start from a clean slate for generated folders
for sub in (f'{ASSETS}/textures/item', f'{ASSETS}/models/item', f'data/{MOD}/structure'):
    shutil.rmtree(os.path.join(RES, sub), ignore_errors=True)

STONES = list(tex.STONE_RGB)  # power, space, reality, soul, time, mind  (bit order)

ABILITIES = {
    'power_blast': 'Power Blast', 'smite': 'Smite', 'titan_leap': 'Titan Leap', 'power_beam': 'Power Beam',
    'blink': 'Blink', 'gravity_well': 'Gravity Well', 'home_warp': 'Home Warp',
    'transmute': 'Transmute', 'reality_warp': 'Reality Warp', 'reality_feast': 'Reality Feast',
    'soul_heal': 'Soul Heal', 'soul_drain': 'Soul Drain', 'soul_ward': 'Soul Ward',
    'time_freeze': 'Time Freeze', 'time_surge': 'Time Surge', 'chrono_bloom': 'Chrono Bloom',
    'time_rewind': 'Time Rewind',
    'mind_control': 'Mind Control', 'telepathy': 'Telepathy', 'pacify': 'Pacify',
    'snap': 'Snap',
}

LORE = {
    'power': 'Contained in the Orb on Morag. Raw, unrestrained force.',
    'space': 'The Tesseract. A doorway to anywhere.',
    'reality': 'The Aether. It makes what you want true.',
    'soul': 'Vormir keeps it. The price is someone you love.',
    'time': 'The Eye of Agamotto. What was can be again.',
    'mind': 'Set in a sceptre by Hydra. Thoughts are not your own.',
}

# ----------------------------------------------------------------- textures
tex_dir = os.path.join(RES, ASSETS, 'textures', 'item')
os.makedirs(os.path.join(tex_dir, 'gauntlet'), exist_ok=True)
for name in STONES:
    frames = [tex.gem_frame(name, f) for f in range(tex.FRAMES)]
    tex.save_strip(os.path.join(tex_dir, f'{name}_stone.png'), frames)
    jout(f'{ASSETS}/textures/item/{name}_stone.png.mcmeta', {"animation": {"frametime": 3, "interpolate": True}})
    jout(f'{ASSETS}/models/item/{name}_stone.json',
         {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/{name}_stone"}})

import math  # noqa: E402
for mask in range(64):
    if mask == 63:
        frames = [tex.gauntlet(63, 0.5 + 0.5 * math.sin(2 * math.pi * f / tex.FRAMES)) for f in range(tex.FRAMES)]
        tex.save_strip(os.path.join(tex_dir, 'gauntlet', 's63.png'), frames)
        jout(f'{ASSETS}/textures/item/gauntlet/s63.png.mcmeta', {"animation": {"frametime": 4, "interpolate": True}})
    else:
        tex.gauntlet(mask).save(os.path.join(tex_dir, 'gauntlet', f's{mask}.png'))
    jout(f'{ASSETS}/models/item/gauntlet/s{mask}.json',
         {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD}:item/gauntlet/s{mask}"}})

# the gauntlet model switches on custom_model_data (= bitmask of socketed stones)
jout(f'{ASSETS}/models/item/infinity_gauntlet.json', {
    "parent": "minecraft:item/generated",
    "textures": {"layer0": f"{MOD}:item/gauntlet/s0"},
    "overrides": [{"predicate": {"custom_model_data": m}, "model": f"{MOD}:item/gauntlet/s{m}"}
                  for m in range(1, 64)]})

frames = [tex.scepter(f) for f in range(tex.FRAMES)]
tex.save_strip(os.path.join(tex_dir, 'scepter.png'), frames)
jout(f'{ASSETS}/textures/item/scepter.png.mcmeta', {"animation": {"frametime": 3, "interpolate": True}})
jout(f'{ASSETS}/models/item/scepter.json',
     {"parent": "minecraft:item/handheld", "textures": {"layer0": f"{MOD}:item/scepter"}})

# --------------------------------------------------------------------- lang
lang = {
    f"itemGroup.{MOD}": "Infinity Gauntlet",
    f"item.{MOD}.infinity_gauntlet": "Infinity Gauntlet",
    f"item.{MOD}.scepter": "Scepter",
    f"message.{MOD}.inserted": "%s socketed",
    f"message.{MOD}.no_stones": "The gauntlet has no stones. Hold one in your other hand and right-click.",
    f"message.{MOD}.selected": "Ability: %s",
    f"message.{MOD}.cooldown": "%s recharging (%ss)",
    f"message.{MOD}.disabled": "That ability is disabled.",
    f"message.{MOD}.disabled_dimension": "Abilities are disabled in this dimension.",
    f"message.{MOD}.no_effect": "Nothing happened.",
    f"message.{MOD}.snap": "Snap. %s turned to dust.",
    f"tooltip.{MOD}.selected": "Selected: %s",
    f"tooltip.{MOD}.gauntlet_hint": "Right-click: use | Sneak + right-click: cycle | Stone in other hand: socket",
    f"tooltip.{MOD}.stone_hint": "Right-click alone for a weak cast, or socket into the gauntlet",
    f"tooltip.{MOD}.scepter": "Right-click a creature to bend its will.",
}
for s in STONES:
    lang[f"item.{MOD}.{s}_stone"] = f"{s.capitalize()} Stone"
    lang[f"tooltip.{MOD}.lore.{s}"] = LORE[s]
for k, v in ABILITIES.items():
    lang[f"ability.{MOD}.{k}"] = v
jout(f'{ASSETS}/lang/en_us.json', lang)

# --------------------------------------------------------- recipes & tags
jout(f'data/{MOD}/recipe/infinity_gauntlet.json', {
    "type": "minecraft:crafting_shaped", "category": "equipment",
    "pattern": ["GGG", "GNG", "LLL"],
    "key": {"G": {"item": "minecraft:gold_block"}, "N": {"item": "minecraft:netherite_ingot"},
            "L": {"item": "minecraft:leather"}},
    "result": {"id": f"{MOD}:infinity_gauntlet", "count": 1}})
jout(f'data/{MOD}/recipe/time_stone.json', {
    "type": "minecraft:crafting_shaped", "category": "misc",
    "pattern": ["ECE", "CNC", "ECE"],
    "key": {"E": {"item": "minecraft:echo_shard"}, "C": {"item": "minecraft:clock"},
            "N": {"item": "minecraft:nether_star"}},
    "result": {"id": f"{MOD}:time_stone", "count": 1}})
jout(f'data/{MOD}/tags/item/infinity_stones.json', {"values": [f"{MOD}:{s}_stone" for s in STONES]})
jout(f'data/{MOD}/tags/entity_type/snap_immune.json',
     {"values": ["minecraft:ender_dragon", "minecraft:wither", "minecraft:warden", "minecraft:elder_guardian"]})

# --------------------------------------------------------------- structures
BUILDERS = {
    'tesseract_vault': structs.tesseract_vault, 'power_orb_temple': structs.power_orb_temple,
    'aether_chamber': structs.aether_chamber, 'vormir': structs.vormir,
    'hydra_outpost': structs.hydra_outpost, 'sanctum_sanctorum': structs.sanctum_sanctorum,
}
TEMPLATES = {}
for name, fn in BUILDERS.items():
    t = fn()
    TEMPLATES[name] = t
    out(f'data/{MOD}/structure/{name}.nbt', t.to_bytes(), 'wb')

# name: (biomes, spacing, separation, salt, step, adaptation, reward items)
STRUCTS = {
    'tesseract_vault': (['#minecraft:is_taiga', 'minecraft:snowy_plains'], 34, 12, 1177001,
                        'surface_structures', 'beard_thin', ['space_stone']),
    'power_orb_temple': (['#minecraft:is_badlands', 'minecraft:desert'], 34, 12, 1177002,
                         'surface_structures', 'beard_thin', ['power_stone']),
    'aether_chamber': (['minecraft:plains', 'minecraft:desert', 'minecraft:savanna',
                        'minecraft:snowy_plains', '#minecraft:is_forest'], 40, 14, 1177003,
                       'underground_structures', 'none', ['reality_stone']),
    'vormir': (['#minecraft:is_mountain'], 40, 14, 1177004, 'surface_structures', 'none', ['soul_stone']),
    'hydra_outpost': (['#minecraft:is_forest', 'minecraft:plains'], 30, 10, 1177005,
                      'surface_structures', 'beard_thin', ['mind_stone', 'scepter']),
    'sanctum_sanctorum': (['minecraft:plains', 'minecraft:sunflower_plains', 'minecraft:meadow',
                           'minecraft:cherry_grove'], 36, 12, 1177006,
                          'surface_structures', 'beard_thin', ['time_stone']),
}

TREASURE_ENTRIES = [
    {"type": "minecraft:item", "name": "minecraft:diamond", "weight": 4,
     "functions": [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 1, "max": 3}}]},
    {"type": "minecraft:item", "name": "minecraft:gold_block", "weight": 4,
     "functions": [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 1, "max": 4}}]},
    {"type": "minecraft:item", "name": "minecraft:golden_apple", "weight": 3},
    {"type": "minecraft:item", "name": "minecraft:enchanted_golden_apple", "weight": 1}]
TREASURE_POOL = {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 4}, "entries": TREASURE_ENTRIES}

for name, (biomes, spacing, sep, salt, step, adapt, rewards) in STRUCTS.items():
    G = TEMPLATES[name].G
    jout(f'data/{MOD}/tags/worldgen/biome/has_structure/{name}.json', {"values": biomes})
    jout(f'data/{MOD}/worldgen/structure/{name}.json', {
        "type": "minecraft:jigsaw",
        "biomes": f"#{MOD}:has_structure/{name}",
        "step": step,
        "spawn_overrides": {},
        "terrain_adaptation": adapt,
        "start_pool": f"{MOD}:{name}/start",
        "size": 1,
        "start_height": {"absolute": -G},
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "max_distance_from_center": 80,
        "use_expansion_hack": False})
    jout(f'data/{MOD}/worldgen/template_pool/{name}/start.json', {
        "fallback": "minecraft:empty",
        "elements": [{"weight": 1, "element": {
            "element_type": "minecraft:single_pool_element", "location": f"{MOD}:{name}",
            "processors": "minecraft:empty", "projection": "rigid"}}]})
    jout(f'data/{MOD}/worldgen/structure_set/{name}.json', {
        "structures": [{"structure": f"{MOD}:{name}", "weight": 1}],
        "placement": {"type": "minecraft:random_spread", "spacing": spacing, "separation": sep, "salt": salt}})
    pools = [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"{MOD}:{r}"}]} for r in rewards]
    pools.append(TREASURE_POOL)
    jout(f'data/{MOD}/loot_table/chests/{name}.json', {"type": "minecraft:chest", "pools": pools})

# the Stonekeeper's altar on Vormir: treasure only (the Soul Stone is at the bottom of the cliff)
jout(f'data/{MOD}/loot_table/chests/vormir_altar.json', {"type": "minecraft:chest", "pools": [
    {"rolls": {"type": "minecraft:uniform", "min": 3, "max": 5}, "entries": TREASURE_ENTRIES + [
        {"type": "minecraft:item", "name": "minecraft:soul_lantern", "weight": 6},
        {"type": "minecraft:item", "name": "minecraft:netherite_scrap", "weight": 2}]}]})

# ------------------------------------------------------------ mod metadata
out('META-INF/neoforge.mods.toml', '''modLoader="javafml"
loaderVersion="[1,)"
license="MIT"

[[mods]]
modId="infinitygauntlet"
version="1.1.0"
displayName="Infinity Gauntlet"
description=\'\'\'
The Infinity Gauntlet, the six Infinity Stones with their MCU homes (Asgard's vault, Morag, the Aether
shrine, Vormir, a Hydra base and the Sanctum Sanctorum), Loki's Scepter and the Snap.
Data-driven and pack-friendly.
\'\'\'

[[dependencies.infinitygauntlet]]
modId="neoforge"
type="required"
versionRange="[21.1.0,)"
ordering="NONE"
side="BOTH"

[[dependencies.infinitygauntlet]]
modId="minecraft"
type="required"
versionRange="[1.21.1]"
ordering="NONE"
side="BOTH"
''')
print('generated into', RES)
for n, t in TEMPLATES.items():
    print(f'  {n}: {t.size} {t.count()} blocks')
