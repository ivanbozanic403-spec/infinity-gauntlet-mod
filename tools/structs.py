"""Structure builders: each function returns a finished Tpl (a Minecraft structure template).

All coordinates are template-local.  Layout rules used everywhere:
  * y == G is the first air layer that sits at ground level when the structure is placed
    (the generator sets start_height = -G),  so the floor you walk on is y == G-1.
  * +z is "south", -z is "north".  Chests face the direction the *front* points.
  * Stairs: `facing` is the direction you walk UP.   Ladders: `facing` is the open side.
"""
import gzip, math, random, struct

MOD = 'infinitygauntlet'


# ------------------------------------------------------------------ NBT writer
def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def T_int(v): return (3, struct.pack('>i', v))
def T_str(s): return (8, w_str(s))


def T_list(items, tid):
    return (9, bytes([tid]) + struct.pack('>i', len(items)) + b''.join(p for _, p in items))


def T_comp(d):
    o = b''
    for k, (i, p) in d.items():
        o += bytes([i]) + w_str(k) + p
    return (10, o + b'\x00')


DATA_VERSION = 3955  # Minecraft 1.21.1


class Tpl:
    def __init__(self, sx, sy, sz, G):
        self.size = (sx, sy, sz)
        self.G = G
        self.blocks = {}

    # -- primitives ------------------------------------------------------
    def inb(self, x, y, z):
        sx, sy, sz = self.size
        return 0 <= x < sx and 0 <= y < sy and 0 <= z < sz

    def set(self, x, y, z, name, props=None, nbt=None, clip=False):
        x, y, z = int(x), int(y), int(z)
        if not self.inb(x, y, z):
            if clip:
                return
            raise ValueError(('out of bounds', x, y, z, self.size, name))
        if ':' not in name:
            name = 'minecraft:' + name
        self.blocks[(x, y, z)] = (name, tuple(sorted((k, str(v)) for k, v in (props or {}).items())), nbt)

    def get(self, x, y, z):
        b = self.blocks.get((x, y, z))
        return b[0].split(':')[1] if b else None

    def fill(self, x1, y1, z1, x2, y2, z2, name, props=None, clip=False):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    n = name(x, y, z) if callable(name) else name
                    if n:
                        self.set(x, y, z, n, props, clip=clip)

    def air(self, x1, y1, z1, x2, y2, z2):
        self.fill(x1, y1, z1, x2, y2, z2, 'air')

    def shell(self, x1, y1, z1, x2, y2, z2, name, props=None):
        """Hollow box (walls, floor and ceiling only)."""
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for z in range(z1, z2 + 1):
                    if x in (x1, x2) or y in (y1, y2) or z in (z1, z2):
                        self.set(x, y, z, name(x, y, z) if callable(name) else name, props)

    # -- round shapes ------------------------------------------------------
    def disc(self, cx, cz, r, y, name, r0=0.0, props=None):
        """Filled circle (or annulus when r0>0) on layer y.  name(x,y,z,d) may return None to skip."""
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if r0 <= d <= r:
                    n = name(x, y, z, d) if callable(name) else name
                    if n:
                        self.set(x, y, z, n, props, clip=True)

    def cyl(self, cx, cz, r, y1, y2, name, r0=0.0):
        for y in range(y1, y2 + 1):
            self.disc(cx, cz, r, y, name, r0)

    def sphere(self, cx, cy, cz, r, name):
        """name(dx,dy,dz,d) -> block or None."""
        for dx in range(-int(r) - 1, int(r) + 2):
            for dy in range(-int(r) - 1, int(r) + 2):
                for dz in range(-int(r) - 1, int(r) + 2):
                    d = math.sqrt(dx * dx + dy * dy + dz * dz)
                    if d <= r:
                        n = name(dx, dy, dz, d)
                        if n:
                            self.set(cx + dx, cy + dy, cz + dz, n, clip=True)

    # -- decorated blocks ----------------------------------------------------
    def stairs(self, x, y, z, mat, facing, half='bottom'):
        self.set(x, y, z, mat + '_stairs', {'facing': facing, 'half': half, 'shape': 'straight'}, clip=True)

    def slab(self, x, y, z, mat, typ='bottom'):
        self.set(x, y, z, mat + '_slab', {'type': typ}, clip=True)

    def chest(self, x, y, z, facing, loot):
        self.set(x, y, z, 'chest', {'facing': facing},
                 {'id': 'minecraft:chest', 'LootTable': f'{MOD}:chests/{loot}'})

    def ladder(self, x, y1, y2, z, facing):
        for y in range(y1, y2 + 1):
            self.set(x, y, z, 'ladder', {'facing': facing})

    def ring_stairs(self, cx, cz, r0, r1, y, mat):
        """Stairs rising toward the centre of a circle."""
        def pick(x, yy, z, d):
            dx, dz = x - cx, z - cz
            if abs(dx) >= abs(dz):
                f = 'east' if dx < 0 else 'west'
            else:
                f = 'south' if dz < 0 else 'north'
            self.set(x, yy, z, mat + '_stairs', {'facing': f, 'half': 'bottom', 'shape': 'straight'}, clip=True)
            return None
        self.disc(cx, cz, r1, y, pick, r0)

    def count(self):
        return len(self.blocks)

    # -- serialisation ---------------------------------------------------------
    def to_bytes(self):
        palette, plist, blist = {}, [], []
        for (x, y, z), (n, pr, nbt) in sorted(self.blocks.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2])):
            key = (n, pr)
            if key not in palette:
                palette[key] = len(plist)
                plist.append(key)
            entry = {'pos': T_list([T_int(x), T_int(y), T_int(z)], 3), 'state': T_int(palette[key])}
            if nbt:
                entry['nbt'] = T_comp({k: T_str(v) for k, v in nbt.items()})
            blist.append(T_comp(entry))
        pal = []
        for n, pr in plist:
            d = {'Name': T_str(n)}
            if pr:
                d['Properties'] = T_comp({k: T_str(v) for k, v in pr})
            pal.append(T_comp(d))
        root = {'size': T_list([T_int(s) for s in self.size], 3), 'entities': T_list([], 0),
                'blocks': T_list(blist, 10), 'palette': T_list(pal, 10), 'DataVersion': T_int(DATA_VERSION)}
        return gzip.compress(bytes([10]) + w_str('') + T_comp(root)[1])


RAINBOW = ['red', 'orange', 'yellow', 'lime', 'light_blue', 'blue', 'purple']
FACE4 = ['north', 'east', 'south', 'west']


# ============================================================================
#  SPACE STONE  -  the Asgardian Vault (Odin's Vault / the Tesseract)
# ============================================================================
def tesseract_vault():
    """Cold-biome hall: a Bifrost bridge leads to a golden vault, the Tesseract floats in a glass cage."""
    t = Tpl(27, 22, 41, G=4)
    r = random.Random(3)
    BR, PB, GD = 'polished_blackstone_bricks', 'polished_blackstone', 'gold_block'
    GB = 'gilded_blackstone'

    # --- foundation and floor
    t.fill(0, 0, 12, 26, 2, 40, BR)
    for x in range(27):
        for z in range(12, 41):
            if 11 <= x <= 15:
                b = 'smooth_quartz'
            elif x in (10, 16):
                b = GD
            else:
                b = PB if (x + z) % 2 == 0 else 'blackstone'
                if r.random() < 0.05:
                    b = GB
            t.set(x, 3, z, b)

    # --- shell: walls
    for y in range(4, 15):
        for x in range(27):
            for z in (12, 40):
                t.set(x, y, z, BR)
        for z in range(12, 41):
            for x in (0, 26):
                t.set(x, y, z, BR)
    t.air(1, 4, 13, 25, 14, 39)
    # side roofs
    t.fill(0, 15, 12, 7, 15, 40, BR)
    t.fill(19, 15, 12, 26, 15, 40, BR)
    t.fill(1, 15, 13, 6, 15, 39, BR)
    t.fill(20, 15, 13, 25, 15, 39, BR)
    # raised nave with clerestory windows
    for x in (7, 19):
        for z in range(12, 41):
            t.set(x, 15, z, BR)
            for y in (16, 17):
                t.set(x, y, z, BR if z % 5 == 0 or z in (12, 40) else 'light_blue_stained_glass')
    for z in (12, 40):
        t.fill(7, 15, z, 19, 17, z, BR)
    t.fill(7, 18, 12, 19, 18, 40, BR)
    t.air(8, 15, 13, 18, 17, 39)
    t.fill(7, 19, 12, 7, 19, 40, GB)
    t.fill(19, 19, 12, 19, 19, 40, GB)
    # oculus above the dais
    t.fill(10, 18, 30, 16, 18, 36, 'light_blue_stained_glass')

    # --- corner spires and trim
    for x, z in ((0, 12), (26, 12), (0, 40), (26, 40)):
        t.fill(x, 3, z, x, 16, z, GD)
        t.fill(x, 17, z, x, 19, z, 'lightning_rod')
    for z in range(13, 40):
        for x in (0, 26):
            t.set(x, 13, z, GB)
    for x in range(1, 26):
        if not 9 <= x <= 17:
            t.set(x, 13, 12, GB)
        t.set(x, 13, 40, GB)
    for x in (4, 22):
        t.fill(x, 4, 12, x, 14, 12, GD)
        t.fill(x, 4, 40, x, 14, 40, GD)

    # --- grand gate (portico + stepped arch)
    t.air(11, 4, 12, 15, 9, 12)
    t.air(12, 10, 12, 14, 11, 12)
    for x in (9, 17):
        t.fill(x, 4, 11, x, 13, 11, 'quartz_pillar', {'axis': 'y'})
        t.set(x, 4, 11, GD)
        t.set(x, 14, 11, GD)
    t.fill(9, 15, 11, 17, 15, 11, GD)
    t.fill(10, 14, 11, 16, 14, 11, 'chiseled_quartz_block')
    for x in range(10, 17):
        t.set(x, 12, 12, 'sea_lantern') if x in (10, 16) else None
    t.set(13, 15, 12, 'sea_lantern')
    for x in (10, 16):
        t.fill(x, 4, 12, x, 11, 12, GD)
    t.stairs(11, 10, 12, 'polished_blackstone_brick', 'east', 'top')
    t.stairs(15, 10, 12, 'polished_blackstone_brick', 'west', 'top')
    t.stairs(12, 12, 12, 'polished_blackstone_brick', 'east', 'top')
    t.stairs(14, 12, 12, 'polished_blackstone_brick', 'west', 'top')

    # --- columns of the arcade
    for z in (15, 20, 25, 30, 35):
        for x in (7, 19):
            t.set(x, 4, z, GD)
            t.fill(x, 5, z, x, 13, z, 'quartz_pillar', {'axis': 'y'})
            t.set(x, 14, z, 'chiseled_quartz_block')
    for x in (7, 19):
        for z in range(13, 40):
            if z % 5 != 0:
                t.set(x, 14, z, BR)

    # --- stained-glass windows in the side walls
    for z0 in (17, 22, 27, 32):
        for x in (0, 26):
            t.fill(x, 6, z0, x, 11, z0 + 1, 'light_blue_stained_glass')
            for zz in (z0 - 1, z0 + 2):
                t.fill(x, 5, zz, x, 12, zz, GB)
            t.fill(x, 5, z0, x, 5, z0 + 1, GB)
            t.fill(x, 12, z0, x, 12, z0 + 1, GB)

    for z in (15, 20, 25, 30, 35):                       # gold inlay strips on the outer walls
        for x in (0, 26):
            t.fill(x, 4, z, x, 12, z, GD)
            t.set(x, 13, z, 'chiseled_quartz_block')

    # --- relic pedestals in the aisles
    relics_l = ['conduit', 'lodestone', 'enchanting_table', 'respawn_anchor']
    relics_r = ['beacon', 'end_portal_frame', 'dragon_head', 'sculk_catalyst']
    for z, rl, rr in zip((17, 22, 27, 32), relics_l, relics_r):
        for x, relic in ((3, rl), (23, rr)):
            t.set(x, 4, z, GD)
            t.set(x, 5, z, relic)
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t.set(x + dx, 4, z + dz, 'polished_blackstone_wall')
            t.set(x, 4, z + 1, 'polished_blackstone_wall')
            t.set(x + (1 if x < 13 else -1), 5, z + 1, 'lantern', {'hanging': 'false'})
            t.set(x, 3, z, 'sea_lantern')

    # --- chandeliers
    for z in (17, 23, 29):
        for x in (12, 14):
            t.fill(x, 15, z, x, 17, z, 'chain')
            t.set(x, 14, z, 'lantern', {'hanging': 'true'})
        t.fill(13, 15, z, 13, 17, z, 'chain')
        t.set(13, 14, z, 'sea_lantern')

    # --- the dais, the Tesseract and its glass cage
    DX, DZ = 13, 33

    def dais1(x, y, z, d):
        return GD if d > 5 else BR
    t.disc(DX, DZ, 6, 4, dais1)
    t.ring_stairs(DX, DZ, 5, 6.9, 4, 'polished_blackstone_brick')
    t.disc(DX, DZ, 4, 5, lambda x, y, z, d: 'smooth_quartz' if d < 3.4 else GD)
    t.disc(DX, DZ, 2, 6, 'chiseled_quartz_block')
    t.set(DX, 7, DZ, GD)
    t.set(DX, 8, DZ, 'end_rod')
    t.fill(DX - 2, 9, DZ - 2, DX + 2, 13, DZ + 2, 'light_blue_stained_glass')
    t.fill(DX - 1, 10, DZ - 1, DX + 1, 12, DZ + 1, 'sea_lantern')
    t.fill(DX - 1, 9, DZ - 1, DX + 1, 9, DZ + 1, 'light_blue_stained_glass')
    t.chest(DX, 6, DZ - 4, 'north', 'tesseract_vault')
    for dx in (-3, 3):
        t.fill(DX + dx, 5, DZ - 3, DX + dx, 6, DZ - 3, 'polished_blackstone_wall')
        t.set(DX + dx, 7, DZ - 3, 'lantern', {'hanging': 'false'})

    # --- BIFROST bridge (rainbow glass over a glowing deck) with pylons and arch
    t.air(8, 4, 0, 18, 12, 11)
    for z in range(0, 12):
        for i, x in enumerate(range(10, 17)):
            t.set(x, 3, z, RAINBOW[i] + '_stained_glass')
            t.set(x, 2, z, 'sea_lantern')
        for x in (9, 17):
            t.set(x, 3, z, GD)
            t.set(x, 2, z, 'polished_blackstone_bricks')
        if z % 3 == 1:
            for x in (9, 17):
                t.fill(x, 4, z, x, 5, z, 'end_rod')
                t.set(x, 6, z, 'sea_lantern')
    for z in (2, 6, 10):
        for x in (9, 17):
            t.fill(x, 0, z, x, 2, z, GD)
    for x in (9, 17):
        t.fill(x, 4, 1, x, 11, 1, 'quartz_pillar', {'axis': 'y'})
        t.set(x, 4, 1, GD)
        t.set(x, 12, 1, GD)
    t.fill(9, 13, 1, 17, 13, 1, GD)
    t.fill(11, 12, 1, 15, 12, 1, 'chiseled_quartz_block')
    t.set(13, 11, 1, 'sea_lantern')
    return t


# ============================================================================
#  POWER STONE  -  the ruined temple on Morag (the Orb)
# ============================================================================
def power_orb_temple():
    """Ruined round temple: broken colonnade, a purple-lit sunken floor and the Orb on its pedestal."""
    t = Tpl(37, 30, 38, G=4)
    r = random.Random(11)
    cx = cz = 18
    RUIN = ['stone_bricks'] * 6 + ['cracked_stone_bricks'] * 3 + ['mossy_stone_bricks', 'deepslate_bricks', 'andesite']

    def ruin(x=0, y=0, z=0, d=0):
        return r.choice(RUIN)

    # --- foundation
    t.disc(cx, cz, 18, 0, ruin)
    for y in (1, 2):
        t.disc(cx, cz, 18, y, lambda x, yy, z, d: r.choice(['cobbled_deepslate', 'stone', 'andesite', 'gravel']))

    # --- floor with a radial pattern
    def floor(x, y, z, d):
        ang = math.atan2(z - cz, x - cx)
        if d <= 2.6:
            return 'amethyst_block'
        if d <= 5.2:
            return 'polished_blackstone'
        if d <= 6.4:
            return 'crying_obsidian'
        if d <= 9.5:
            if abs(math.sin(4 * ang)) < 0.14:
                return 'chiseled_deepslate'
            return 'deepslate_tiles'
        if r.random() < 0.10:
            return r.choice(['gravel', 'coarse_dirt', 'cracked_deepslate_tiles'])
        return r.choice(RUIN)
    t.disc(cx, cz, 16.4, 3, floor)

    # --- the ruined outer wall (gap on the south side for the gate)
    for x in range(37):
        for z in range(38):
            d = math.hypot(x - cx, z - cz)
            if 15.0 <= d <= 16.8:
                ang = math.atan2(z - cz, x - cx)
                if z > cz and abs(x - cx) <= 3.5:
                    continue
                h = int(2 + 8 * abs(math.sin(ang * 3 + 0.6) * math.cos(ang * 2 - 0.4)) + r.randint(0, 3))
                for y in range(4, 4 + h):
                    t.set(x, y, z, r.choice(RUIN))
                if h > 4 and r.random() < 0.5:
                    t.slab(x, 4 + h, z, 'stone_brick')

    # --- gate towers flanking the entrance
    for sx in (-5, 5):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                for y in range(4, 14):
                    t.set(cx + sx + dx, y, cz + 16 + dz, r.choice(RUIN))
        t.stairs(cx + sx, 14, cz + 16, 'stone_brick', 'north')
    for dx in range(-4, 5):
        if r.random() < 0.8:
            t.set(cx + dx, 12, cz + 16, 'stone_bricks')
            if r.random() < 0.6:
                t.set(cx + dx, 13, cz + 16, 'chiseled_stone_bricks')

    # --- broken colonnade: eight pillars with purple bands
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        px, pz = round(cx + 11 * math.cos(a)), round(cz + 11 * math.sin(a))
        h = r.randint(5, 14)
        for dx in range(2):
            for dz in range(2):
                for y in range(4, 4 + h):
                    band = (y - 4) % 4 == 3
                    t.set(px + dx, y, pz + dz, 'chiseled_deepslate' if band else 'deepslate_bricks')
                if h >= 12:
                    t.set(px + dx, 4 + h, pz + dz, 'purpur_slab', {'type': 'bottom'})
        for dx in range(-1, 3):
            for dz in range(-1, 3):
                if r.random() < 0.5 and (dx in (-1, 2) or dz in (-1, 2)):
                    t.set(px + dx, 4, pz + dz, r.choice(['cobblestone', 'andesite', 'cracked_stone_bricks']))
        t.set(px - (1 if px < cx else -2), 4, pz - (1 if pz < cz else -2), 'amethyst_cluster', {'facing': 'up'}) \
            if r.random() < 0.7 else None
    # fallen columns
    for (x0, z0, axis) in ((8, 24, 'x'), (27, 12, 'z')):
        for i in range(6):
            x, z = (x0 + i, z0) if axis == 'x' else (x0, z0 + i)
            t.set(x, 4, z, 'polished_deepslate')

    # --- rubble and amethyst growth on the floor
    for x in range(37):
        for z in range(38):
            d = math.hypot(x - cx, z - cz)
            if 7 <= d <= 14.5 and (x, 4, z) not in t.blocks and r.random() < 0.09:
                roll = r.random()
                if roll < 0.35:
                    t.set(x, 4, z, 'amethyst_cluster', {'facing': 'up'})
                elif roll < 0.7:
                    t.set(x, 4, z, r.choice(['cobblestone', 'andesite', 'gravel']))
                else:
                    t.stairs(x, 4, z, 'stone_brick', r.choice(FACE4))

    # --- raised dais, pedestal and the Orb
    t.disc(cx, cz, 6, 4, 'polished_blackstone_bricks')
    t.ring_stairs(cx, cz, 5.2, 6.9, 4, 'polished_blackstone_brick')
    t.disc(cx, cz, 4, 5, lambda x, y, z, d: 'polished_blackstone' if d > 2.6 else 'chiseled_polished_blackstone')
    t.fill(cx - 1, 6, cz - 1, cx + 1, 6, cz + 1, 'polished_blackstone_bricks')
    t.set(cx, 7, cz, 'chiseled_polished_blackstone')
    t.fill(cx, 8, cz, cx, 8, cz, 'end_rod')

    def orb(dx, dy, dz, d):
        if d <= 1.4:
            return 'amethyst_block'
        if dy == 0 and (dx == 0 or dz == 0) and d > 1.4:
            return 'purple_stained_glass'
        if abs(dy) == 0:
            return 'chiseled_polished_blackstone'
        if abs(dy) >= 2 and d > 2.0:
            return 'iron_block'
        return 'iron_block' if (dx + dy + dz) % 2 == 0 else 'polished_deepslate'
    t.sphere(cx, 11, cz, 2.5, orb)
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        t.set(cx + dx, 6, cz + dz, 'purpur_pillar', {'axis': 'y'})
        t.set(cx + dx, 7, cz + dz, 'amethyst_block')
    t.chest(cx, 6, cz - 4, 'south', 'power_orb_temple')

    # --- the entrance causeway
    for z in range(cz + 17, 38):
        for x in range(cx - 3, cx + 4):
            for y in range(0, 3):
                t.set(x, y, z, 'cobbled_deepslate')
            t.set(x, 3, z, r.choice(['cracked_stone_bricks', 'stone_bricks', 'gravel']
                                    if z > 34 else ['stone_bricks', 'cracked_stone_bricks']))
        for x in (cx - 4, cx + 4):
            if r.random() < 0.75:
                t.set(x, 4, z, 'stone_brick_wall')
            if z % 3 == 0 and r.random() < 0.7:
                t.set(x, 5, z, 'lantern', {'hanging': 'false'})
    return t


# ============================================================================
#  REALITY STONE  -  the Aether chamber (Dark Elf shrine)
# ============================================================================
def aether_chamber():
    """A Dark-Elf shrine on the surface, a 36-block ladder shaft and the crimson vault of the Aether."""
    t = Tpl(25, 50, 25, G=40)
    r = random.Random(5)
    OB, CO = 'obsidian', 'crying_obsidian'
    PX, PZ = 12, 15            # altar centre
    SX, SZ = 12, 5             # shaft centre

    # --- vault shell
    def shell_block(x, y, z):
        return CO if r.random() < 0.16 else OB
    t.fill(0, 0, 0, 24, 14, 24, shell_block)
    t.air(1, 2, 1, 23, 12, 23)

    # floor
    def floor(x, y, z, d):
        if d <= 3:
            return CO
        if d <= 4.2:
            return 'redstone_block'
        if d <= 6.5:
            return 'polished_blackstone'
        if abs(x - PX) == abs(z - PZ) and d < 12:
            return 'red_nether_bricks'
        return 'gilded_blackstone' if r.random() < 0.08 else 'blackstone'
    t.disc(PX, PZ, 18, 1, floor)
    for x in range(25):
        for z in range(25):
            if (x, 1, z) not in t.blocks or x in (0, 24) or z in (0, 24):
                if x in (0, 24) or z in (0, 24):
                    continue
                t.set(x, 1, z, 'blackstone')

    # glowing wall panels
    for x0 in (4, 10, 16):
        for wall in ('n', 's'):
            zz = 0 if wall == 'n' else 24
            for x in range(x0, x0 + 3):
                for y in (5, 6, 7, 8):
                    t.set(x, y, zz, 'shroomlight' if y in (6, 7) else CO)
    for z0 in (6, 12, 18):
        for zz in range(z0, z0 + 3):
            for y in (5, 6, 7, 8):
                t.set(0, y, zz, 'shroomlight' if y in (6, 7) else CO)
                t.set(24, y, zz, 'shroomlight' if y in (6, 7) else CO)

    # pillars
    for (px, pz) in ((5, 10), (19, 10), (5, 15), (19, 15), (5, 20), (19, 20), (9, 21), (15, 21)):
        for y in range(2, 13):
            t.set(px, y, pz, 'red_nether_bricks' if y in (2, 7, 12) else 'polished_blackstone')
        t.set(px, 3, pz, 'chiseled_polished_blackstone')
        t.set(px, 11, pz, CO)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t.set(px + dx, 2, pz + dz, 'polished_blackstone_brick_stairs',
                  {'facing': {(1, 0): 'west', (-1, 0): 'east', (0, 1): 'north', (0, -1): 'south'}[(dx, dz)],
                   'half': 'bottom'})
    # hanging chains with soul lanterns
    for (hx, hz) in ((8, 8), (16, 8), (8, 18), (16, 18), (12, 20), (12, 9)):
        t.fill(hx, 10, hz, hx, 12, hz, 'chain')
        t.set(hx, 9, hz, 'soul_lantern', {'hanging': 'true'})
    # cobwebs in the corners
    for (x, y, z) in ((1, 12, 1), (23, 12, 1), (1, 12, 23), (23, 12, 23), (1, 11, 2), (22, 11, 22), (2, 11, 1)):
        t.set(x, y, z, 'cobweb')

    # --- altar
    t.disc(PX, PZ, 5, 2, lambda x, y, z, d: CO if d > 4 else OB)
    t.disc(PX, PZ, 3.6, 3, lambda x, y, z, d: 'redstone_block' if 2.6 < d else 'polished_blackstone')
    t.ring_stairs(PX, PZ, 4.2, 5.4, 2, 'polished_blackstone_brick')
    t.disc(PX, PZ, 2, 4, CO)
    t.set(PX, 5, PZ, OB)
    t.set(PX, 6, PZ, 'end_rod')
    t.chest(PX, 4, PZ - 3, 'north', 'aether_chamber')
    for dx in (-3, 3):
        t.set(PX + dx, 4, PZ - 2, 'soul_lantern', {'hanging': 'false'})

    # --- the Aether itself: a crimson core with swirling tendrils
    def core(dx, dy, dz, d):
        if d <= 0.9:
            return 'shroomlight'
        if d <= 1.7:
            return 'redstone_block'
        return 'red_stained_glass'
    t.sphere(PX, 9, PZ, 2.2, core)
    for arm in range(4):
        for k in range(14):
            a = arm * math.pi / 2 + k * 0.55
            rad = 2.6 + k * 0.28
            y = 9 + round(2.4 * math.sin(k * 0.5 + arm))
            t.set(PX + round(rad * math.cos(a)), y, PZ + round(rad * math.sin(a)), 'red_stained_glass', clip=True)
    for k in range(10):
        a = r.random() * 6.28
        rad = 3.5 + r.random() * 3
        t.set(PX + round(rad * math.cos(a)), 7 + r.randint(0, 5), PZ + round(rad * math.sin(a)), CO, clip=True)

    # --- ladder shaft (ring walls from vault ceiling to the chimney top)
    t.fill(SX - 2, 13, SZ - 2, SX + 2, 48, SZ + 2, lambda x, y, z: CO if r.random() < 0.1 else 'deepslate_bricks')
    t.air(SX - 1, 13, SZ - 1, SX + 1, 48, SZ + 1)
    for y in range(2, 13):
        t.set(SX, y, SZ - 1, 'polished_blackstone')       # ladder backing hanging below the ceiling
    t.ladder(SX, 2, 41, SZ - 1, 'south')
    for y in range(15, 40, 6):                              # torches in the shaft
        t.set(SX - 1, y, SZ + 1, 'soul_wall_torch', {'facing': 'north'})

    # --- surface pavilion
    def pave(x, y, z):
        return CO if (x + z) % 5 == 0 else ('polished_blackstone_bricks' if (x + z) % 2 == 0 else 'blackstone')
    t.fill(6, 39, 0, 18, 39, 10, pave)
    t.fill(10, 39, 3, 14, 39, 7, 'deepslate_bricks')
    for (px, pz) in ((6, 0), (18, 0), (6, 10), (18, 10)):
        t.fill(px, 40, pz, px, 45, pz, 'polished_blackstone')
        t.set(px, 40, pz, 'chiseled_polished_blackstone')
        t.set(px, 46, pz, 'chiseled_polished_blackstone')
        t.set(px, 47, pz, 'soul_lantern', {'hanging': 'false'})
    for x in range(6, 19):
        for z in (0, 10):
            t.set(x, 46, z, 'polished_blackstone_bricks')
    for z in range(0, 11):
        for x in (6, 18):
            t.set(x, 46, z, 'polished_blackstone_bricks')
    for x in (10, 14):
        for z in (3, 7):
            t.set(x, 49, z, 'soul_lantern', {'hanging': 'false'})
    t.air(SX, 40, SZ + 2, SX, 41, SZ + 2)                  # doorway out of the shaft (south side)
    t.air(SX - 1, 40, SZ + 2, SX + 1, 40, SZ + 2)
    for x in (SX - 1, SX + 1):
        t.stairs(x, 42, SZ + 2, 'polished_blackstone_brick', 'north', 'top')
    return t


# ============================================================================
#  SOUL STONE  -  Vormir: the sacrificial cliff
# ============================================================================
def vormir():
    """A sinkhole-cliff in the mountains: Stonekeeper's altar on the rim, a jump pier over the chasm,
    a pool below and, on a ledge at the bottom, the Soul Stone.  Safe landing in the water (MCU-style)."""
    t = Tpl(41, 36, 57, G=26)
    r = random.Random(77)
    cx = cz = 20
    ROCK = ['blackstone'] * 4 + ['cobbled_deepslate'] * 2 + ['basalt', 'smooth_basalt', 'polished_blackstone']

    def rock(x=0, y=0, z=0, d=0):
        return r.choice(ROCK)

    # --- the chasm: walls, floor, air
    t.cyl(cx, cz, 12.5, 1, 24, rock, r0=9)
    t.cyl(cx, cz, 15.5, 16, 24, rock, r0=12.6)
    t.disc(cx, cz, 12.5, 0, rock)
    t.cyl(cx, cz, 8.99, 5, 25, 'air')
    t.cyl(cx, cz, 8.99, 1, 4, 'blackstone')
    t.cyl(cx, cz, 7.0, 1, 4, 'water')
    for k in range(8):
        a = k * math.pi / 4
        t.set(cx + round(4 * math.cos(a)), 0, cz + round(4 * math.sin(a)), 'shroomlight')
    # keep sky clear above the rim, the pier and the altar
    t.cyl(cx, cz, 15, 26, 32, 'air')
    t.air(16, 26, 35, 24, 31, 56)
    t.air(11, 26, 0, 29, 35, 10)

    # --- the plaza on the rim
    def plaza(x, y, z, d):
        ang = math.atan2(z - cz, x - cx)
        if d > 13.6:
            return 'basalt'
        if abs(math.sin(4 * ang)) < 0.11 and d > 10:
            return 'chiseled_polished_blackstone'
        if r.random() < 0.05:
            return r.choice(['cracked_polished_blackstone_bricks', 'soul_soil', 'gilded_blackstone'])
        return 'polished_blackstone_bricks'
    t.disc(cx, cz, 15, 25, plaza, r0=9)
    for k in range(40):
        a = r.random() * 6.28
        d = 10 + r.random() * 4.5
        x, z = cx + round(d * math.cos(a)), cz + round(d * math.sin(a))
        if t.get(x, 25, z) == 'soul_soil':
            t.set(x, 26, z, 'soul_fire')

    # --- the approach: a long paved path with gate arches and lamp posts
    for z in range(35, 57):
        for x in range(16, 25):
            for y in range(21, 25):
                t.set(x, y, z, 'blackstone')
            if x in (16, 24):
                t.set(x, 25, z, 'chiseled_polished_blackstone')
            else:
                t.set(x, 25, z, 'polished_blackstone_bricks' if (z + x) % 4 else 'polished_blackstone')
    for z in (39, 45, 51):
        for x in (16, 24):
            t.fill(x, 26, z, x, 32, z, 'polished_blackstone_bricks')
            t.set(x, 26, z, 'chiseled_polished_blackstone')
            t.set(x, 32, z, 'chiseled_polished_blackstone')
        t.fill(16, 33, z, 24, 33, z, 'polished_blackstone_bricks')
        t.fill(18, 32, z, 22, 32, z, 'polished_blackstone_bricks') if z == 51 else None
        t.stairs(17, 32, z, 'polished_blackstone_brick', 'east', 'top')
        t.stairs(23, 32, z, 'polished_blackstone_brick', 'west', 'top')
        t.set(20, 32, z, 'chain')
        t.set(20, 31, z, 'soul_lantern', {'hanging': 'true'})
    for z in (36, 42, 48, 54):
        for x in (16, 24):
            t.set(x, 26, z, 'polished_blackstone_brick_wall')
            t.set(x, 27, z, 'soul_lantern', {'hanging': 'false'})

    # --- the jump pier
    for z in range(23, 31):
        for x in range(19, 22):
            t.set(x, 25, z, 'polished_blackstone_bricks')
    for x in (19, 21):
        t.set(x, 26, 23, 'polished_blackstone_brick_wall')
        t.set(x, 27, 23, 'soul_lantern', {'hanging': 'false'})
    t.set(20, 25, 23, 'chiseled_polished_blackstone')

    # --- the Stonekeeper's altar
    t.fill(12, 16, 0, 28, 25, 9, lambda x, y, z: 'blackstone' if (x, y, z) not in t.blocks else None)
    t.fill(13, 26, 1, 27, 26, 8, 'polished_blackstone_bricks')
    t.fill(15, 27, 1, 25, 27, 6, 'polished_blackstone_bricks')
    t.fill(17, 28, 1, 23, 28, 4, 'polished_blackstone_bricks')
    for x in range(14, 27):
        t.stairs(x, 26, 9, 'polished_blackstone_brick', 'north') if 13 <= x <= 27 else None
    for x in range(17, 24):
        t.stairs(x, 27, 7, 'polished_blackstone_brick', 'north')
        t.stairs(x, 28, 5, 'polished_blackstone_brick', 'north')
    # the cloaked figure with a red-skull face
    t.fill(20, 29, 2, 20, 30, 2, 'black_wool')
    t.set(19, 30, 2, 'black_wool')
    t.set(21, 30, 2, 'black_wool')
    t.set(20, 31, 2, 'wither_skeleton_skull', {'rotation': '0'})
    t.fill(20, 29, 1, 20, 30, 1, 'red_wool')
    t.chest(20, 29, 3, 'south', 'vormir_altar')
    for x in (18, 22):
        t.set(x, 29, 3, 'soul_campfire', {'facing': 'south', 'lit': 'true'})
    for x in (16, 24):
        t.fill(x, 26, 2, x, 33, 2, 'polished_blackstone_bricks')
        t.set(x, 33, 2, 'chiseled_polished_blackstone')
        t.set(x, 34, 2, 'soul_lantern', {'hanging': 'false'})
    for dx in (-3, 3):
        t.fill(20 + dx, 29, 2, 20 + dx, 31, 2, 'polished_blackstone_brick_wall')
        t.set(20 + dx, 32, 2, 'soul_lantern', {'hanging': 'false'})

    # --- the ledge at the bottom, the way back up, and the Soul Stone
    for x in range(11, 16):
        for z in range(17, 24):
            if math.hypot(x - cx, z - cz) < 9:
                for y in range(1, 6):
                    t.set(x, y, z, 'blackstone')
                t.set(x, 5, z, 'soul_soil' if (x + z) % 3 == 0 else 'polished_blackstone')
    t.ladder(12, 6, 25, cz, 'east')
    t.chest(14, 6, cz, 'east', 'vormir')
    for z in (17, 23):
        t.set(13, 6, z, 'soul_lantern', {'hanging': 'false'})
    t.set(15, 6, 21, 'soul_campfire', {'facing': 'east', 'lit': 'true'})
    t.set(15, 6, 19, 'soul_campfire', {'facing': 'east', 'lit': 'true'})
    for z in (19, 21):
        t.set(11, 6, z, 'shroomlight')
    return t


# ============================================================================
#  MIND STONE  -  Hydra research outpost (Loki's Scepter)
# ============================================================================
HYDRA_LOGO = [
    "....#######....", "...#########...", "..###########..", "..###########..",
    "..##..###..##..", "..##..###..##..", "..###########..", "...####.####...",
    "....#######....", "....#.#.#.#....", "...##.#.#.##...", "..##..#.#..##..",
    ".##...#.#...##.", ".#...##.##...#.", "##...#...#...##",
]


def hydra_outpost():
    """Walled research base: corner towers, a keep with the Hydra emblem, a lab, and the stone's vault."""
    t = Tpl(33, 26, 33, G=4)
    r = random.Random(9)
    DB, PD, DT = 'deepslate_bricks', 'polished_deepslate', 'deepslate_tiles'
    assert all(len(row) == 15 for row in HYDRA_LOGO)

    # --- foundation and courtyard
    t.fill(0, 0, 0, 32, 2, 32, lambda x, y, z: r.choice(['stone_bricks', 'deepslate_bricks', 'cobbled_deepslate']))
    for x in range(33):
        for z in range(33):
            t.set(x, 3, z, 'stone' if (x + z) % 2 else 'smooth_stone')
    for z in range(23, 33):
        for x in (15, 16, 17):
            t.set(x, 3, z, 'polished_andesite')
    # helipad
    t.fill(2, 3, 24, 10, 3, 32 - 1, 'gray_concrete')
    for x in range(2, 11):
        for z in range(24, 32):
            d = math.hypot(x - 6, z - 28)
            if 3.0 <= d <= 3.9:
                t.set(x, 3, z, 'yellow_concrete')
    for z in range(26, 31):
        t.set(5, 3, z, 'white_concrete')
        t.set(7, 3, z, 'white_concrete')
    t.set(6, 3, 28, 'white_concrete')

    # --- perimeter wall with a crenellated top and a gate on the south side
    for x in range(33):
        for z in range(33):
            if x in (0, 32) or z in (0, 32):
                for y in range(4, 10):
                    t.set(x, y, z, DB)
                t.set(x, 10, z, DT) if (x + z) % 2 == 0 else None
                t.set(x, 7, z, 'blackstone') if y == 7 and (x + z) % 4 == 0 else None
    t.air(14, 4, 32, 18, 8, 32)
    t.fill(14, 8, 32, 18, 8, 32, 'iron_bars')
    for x in (13, 19):
        t.fill(x, 4, 32, x, 9, 32, 'blackstone')
        t.set(x, 10, 32, 'sea_lantern')
    # --- corner towers
    for (ox, oz) in ((0, 0), (28, 0), (0, 28), (28, 28)):
        for y in range(4, 16):
            for x in range(ox, ox + 5):
                for z in range(oz, oz + 5):
                    edge = x in (ox, ox + 4) or z in (oz, oz + 4)
                    t.set(x, y, z, (PD if y % 6 else DT) if edge else 'air')
        for y in (7, 12):
            for (x, z) in ((ox + 2, oz), (ox + 2, oz + 4), (ox, oz + 2), (ox + 4, oz + 2)):
                t.set(x, y, z, 'iron_bars')
        t.fill(ox + 1, 10, oz + 1, ox + 3, 10, oz + 3, 'smooth_stone')
        t.set(ox + 2, 9, oz + 2, 'sea_lantern')
        for k, (w, y) in enumerate(((5, 16), (3, 17))):
            o = (5 - w) // 2
            t.fill(ox + o, y, oz + o, ox + o + w - 1, y, oz + o + w - 1, DT)
        t.set(ox + 2, 18, oz + 2, DT)
        t.fill(ox + 2, 19, oz + 2, ox + 2, 21, oz + 2, 'lightning_rod')

    # --- the keep
    KX0, KX1, KZ0, KZ1 = 9, 23, 6, 22
    for y in range(4, 20):
        for x in range(KX0, KX1 + 1):
            for z in range(KZ0, KZ1 + 1):
                if x in (KX0, KX1) or z in (KZ0, KZ1):
                    t.set(x, y, z, DT if y in (9, 10) else PD)
    t.air(KX0 + 1, 4, KZ0 + 1, KX1 - 1, 19, KZ1 - 1)
    t.fill(KX0, 20, KZ0, KX1, 20, KZ1, DT)
    t.fill(KX0 + 1, 21, KZ0 + 1, KX1 - 1, 21, KZ1 - 1, 'deepslate_tile_slab')
    # blackstone pilasters on the side walls
    for z in range(KZ0, KZ1 + 1, 4):
        for y in range(4, 20):
            t.set(KX0, y, z, 'blackstone')
            t.set(KX1, y, z, 'blackstone')
    # slit windows
    for z in (10, 14, 18):
        for x in (KX0, KX1):
            t.fill(x, 12, z, x, 15, z, 'light_blue_stained_glass')
    # HYDRA emblem on the south face
    for row, line in enumerate(HYDRA_LOGO):
        for col, ch in enumerate(line):
            t.set(KX0 + col, 19 - row, KZ1, 'black_concrete' if ch == '#' else 'red_concrete')
    t.fill(KX0, 4, KZ1, KX1, 4, KZ1, PD)
    t.air(15, 4, KZ1, 17, 6, KZ1)
    for x in (14, 18):
        t.fill(x, 4, KZ1, x, 7, KZ1, 'gray_concrete')
    t.fill(14, 7, KZ1, 18, 7, KZ1, 'gray_concrete')
    t.fill(15, 7, KZ1, 17, 7, KZ1, 'sea_lantern')

    # --- interior floor and lab
    t.fill(KX0 + 1, 3, KZ0 + 1, KX1 - 1, 3, KZ1 - 1,
           lambda x, y, z: 'iron_block' if x in (13, 19) else ('smooth_stone' if (x + z) % 2 else 'stone'))
    # gallery
    for x in range(10, 23):
        for z in range(7, 10):
            t.set(x, 10, z, 'smooth_stone')
    for x in (10, 11):
        for z in range(10, 16):
            t.set(x, 10, z, 'smooth_stone')
    for z in range(10, 16):
        t.set(12, 11, z, 'iron_bars')
    for x in range(12, 23):
        t.set(x, 11, 10, 'iron_bars')
    for i in range(6):                                  # stairs up to the gallery
        t.stairs(11, 4 + i, 21 - i, 'polished_deepslate', 'north')
        for y in range(4, 4 + i):
            t.set(11, y, 21 - i, 'polished_deepslate')
    # hanging lamps
    for (x, z) in ((13, 12), (19, 12), (16, 17), (13, 19), (19, 19)):
        t.fill(x, 16, z, x, 19, z, 'chain')
        t.set(x, 15, z, 'sea_lantern')
    # containment tubes
    for (tx, tz) in ((13, 15), (19, 15)):
        for y in range(4, 9):
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    if (dx, dz) != (0, 0):
                        t.set(tx + dx, y, tz + dz, 'light_blue_stained_glass')
        t.fill(tx - 1, 9, tz - 1, tx + 1, 9, tz + 1, 'iron_block')
        t.fill(tx - 1, 3, tz - 1, tx + 1, 3, tz + 1, 'sea_lantern')
        t.set(tx, 4, tz, 'water')
        t.set(tx, 5, tz, 'water')
    # consoles
    for z in range(9, 20, 2):
        t.set(21, 4, z, 'gray_concrete')
        t.set(21, 5, z, 'lectern', {'facing': 'west'})
        t.fill(22, 6, z, 22, 7, z, 'lime_concrete')
    # --- the vault
    for z in range(7, 12):
        for y in range(4, 10):
            t.set(13, y, z, 'polished_blackstone_bricks')
            t.set(19, y, z, 'polished_blackstone_bricks')
    for x in range(13, 20):
        for y in range(4, 10):
            t.set(x, y, 11, 'polished_blackstone_bricks')
    t.air(14, 4, 7, 18, 9, 10)
    t.air(15, 4, 11, 17, 6, 11)
    for x in (14, 18):
        t.fill(x, 4, 11, x, 7, 11, 'gold_block')
    t.fill(14, 7, 11, 18, 7, 11, 'gold_block')
    t.fill(14, 3, 7, 18, 3, 10, 'polished_blackstone')
    for x in range(14, 19):
        for z in (8, 10):
            t.set(x, 9, z, 'sea_lantern') if (x + z) % 2 == 0 else None
    t.set(16, 4, 9, 'gold_block')
    t.chest(16, 5, 9, 'south', 'hydra_outpost')
    for x in range(15, 18):
        for z in range(8, 11):
            for y in range(5, 8):
                if not (x == 16 and z == 9) and (x in (15, 17) or z in (8, 10) or y == 7):
                    t.set(x, y, z, 'light_blue_stained_glass')
    t.set(16, 6, 9, 'air')
    t.set(16, 7, 9, 'light_blue_stained_glass')
    t.set(16, 8, 9, 'sea_lantern')

    # --- courtyard fittings: lamp posts, crates
    for z in (25, 29):
        for x in (13, 19):
            t.fill(x, 4, z, x, 6, z, 'deepslate_brick_wall')
            t.set(x, 7, z, 'sea_lantern')
    for (x, z) in ((28, 25), (29, 25), (28, 26), (30, 25), (29, 26), (28, 29), (29, 29)):
        t.set(x, 4, z, 'barrel', {'facing': 'up'})
    t.set(28, 5, 25, 'barrel', {'facing': 'up'})
    t.set(29, 5, 25, 'barrel', {'facing': 'up'})
    return t


# ============================================================================
#  TIME STONE  -  the Sanctum Sanctorum (Eye of Agamotto)
# ============================================================================
def sanctum_sanctorum():
    """A brick townhouse with the round Seal window, a tall library hall, a sling-ring portal and
    the Eye of Agamotto on a mezzanine altar."""
    t = Tpl(21, 29, 24, G=4)
    r = random.Random(21)
    X0, X1, Z0, Z1 = 3, 17, 6, 20
    CX = 10

    t.fill(2, 0, 5, 18, 2, 22, 'stone_bricks')
    for x in range(2, 19):
        for z in range(5, 23):
            t.set(x, 3, z, 'dark_oak_planks' if (x + z) % 2 else 'spruce_planks')
    # walls
    for y in range(4, 21):
        for x in range(X0, X1 + 1):
            for z in range(Z0, Z1 + 1):
                if x in (X0, X1) or z in (Z0, Z1):
                    quoin = x in (X0, X1) and z in (Z0, Z1)
                    band = y in (10, 20)
                    t.set(x, y, z, 'stone_bricks' if quoin or band else 'bricks')
    t.air(X0 + 1, 4, Z0 + 1, X1 - 1, 20, Z1 - 1)
    # ceiling and mansard roof
    t.fill(X0, 21, Z0, X1, 21, Z1, 'deepslate_tiles')
    w = 15
    for layer in range(7):
        y = 22 + layer
        o = layer + 1
        x0, x1, z0, z1 = X0 + o, X1 - o, Z0 + o, Z1 - o
        if x1 < x0:
            break
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    if x1 - x0 < 2:
                        t.set(x, y, z, 'deepslate_tiles')
                        continue
                    if z == z1 and x0 < x < x1:
                        f = 'north'
                    elif z == z0 and x0 < x < x1:
                        f = 'south'
                    elif x == x0:
                        f = 'east'
                    else:
                        f = 'west'
                    t.stairs(x, y, z, 'deepslate_tile', f)
                else:
                    t.set(x, y, z, 'deepslate_tiles')
    for (x, z) in ((4, 7), (16, 7)):
        t.fill(x, 22, z, x, 26, z, 'bricks')
        t.set(x, 27, z, 'campfire', {'lit': 'true', 'facing': 'south'})

    # --- facade: round Seal window, door, windows
    cyc = 15
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            d = math.hypot(dx, dy)
            if d > 3.7:
                continue
            if d <= 1.4:
                b = 'yellow_stained_glass'
            elif d <= 2.6:
                b = 'gold_block' if (dx == 0 or dy == 0 or abs(dx) == abs(dy)) else 'orange_stained_glass'
            else:
                b = 'gold_block' if (dx + dy) % 2 == 0 else 'glowstone'
            t.set(CX + dx, cyc + dy, Z1, b)
    t.set(CX, cyc, Z1, 'glowstone')
    for x in (6, 14):
        for y in (5, 6, 7):
            t.set(x, y, Z1, 'glass_pane')
        t.set(x, 8, Z1, 'stone_bricks')
        t.set(x, 4, Z1, 'stone_bricks')
    t.air(CX, 4, Z1, CX, 7, Z1)
    t.set(CX, 4, Z1, 'dark_oak_door', {'facing': 'south', 'half': 'lower', 'hinge': 'left', 'open': 'false'})
    t.set(CX, 5, Z1, 'dark_oak_door', {'facing': 'south', 'half': 'upper', 'hinge': 'left', 'open': 'false'})
    t.set(CX, 6, Z1, 'glass_pane')
    for x in (CX - 1, CX + 1):
        t.fill(x, 4, Z1, x, 7, Z1, 'stone_bricks')
    t.fill(CX - 1, 8, Z1, CX + 1, 8, Z1, 'stone_bricks')
    t.stairs(CX - 2, 8, Z1, 'stone_brick', 'east')
    t.stairs(CX + 2, 8, Z1, 'stone_brick', 'west')
    # stoop with railings and lanterns
    t.fill(7, 3, 21, 13, 3, 23, 'stone_bricks')
    for z in (21, 22, 23):
        for x in (7, 13):
            t.set(x, 4, z, 'iron_bars')
    t.set(7, 5, 21, 'lantern', {'hanging': 'false'})
    t.set(13, 5, 21, 'lantern', {'hanging': 'false'})
    # side windows
    for z in (9, 13, 17):
        for x in (X0, X1):
            for y in (5, 6, 7, 8):
                t.set(x, y, z, 'glass_pane')
            for y in (13, 14, 15, 16, 17):
                t.set(x, y, z, 'glass_pane')
            t.set(x, 9, z, 'stone_bricks')
    # --- ground-floor library hall
    for z in range(8, 19):
        for y in range(4, 9):
            if r.random() < 0.96:
                t.set(X0 + 1, y, z, 'bookshelf')
    for z in range(8, 14):
        for y in range(11, 14):
            t.set(X0 + 1, y, z, 'bookshelf')
    for x in range(CX - 1, CX + 2):
        for z in range(8, 19):
            t.set(x, 4, z, 'red_carpet')
    t.fill(CX - 1, 4, 18, CX + 1, 4, 18, 'red_carpet')
    for (x, z) in ((8, 19), (12, 19)):
        t.set(x, 4, z, 'lectern', {'facing': 'south'})
    for z in (10, 14):
        t.fill(CX, 17, z, CX, 20, z, 'chain')
        t.set(CX, 16, z, 'lantern', {'hanging': 'true'})
    # stairs to the mezzanine (east wall)
    for i in range(6):
        t.stairs(16, 4 + i, 19 - i, 'dark_oak', 'north')
        for y in range(4, 4 + i):
            t.set(16, y, 19 - i, 'dark_oak_planks')
    # mezzanine at the back (z 7..13) with a railing
    for x in range(X0 + 1, X1):
        for z in range(7, 14):
            t.set(x, 10, z, 'dark_oak_planks')
    for x in range(X0 + 2, 16):
        t.set(x, 11, 14, 'dark_oak_fence')
    # the sling-ring portal (free-standing orange ring)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            d = math.hypot(dx, dy)
            if 2.6 <= d <= 3.5:
                t.set(CX + dx, 8 + dy, 16, 'glowstone' if (dx + dy) % 3 == 0 else 'orange_stained_glass', clip=True)
    # --- the Eye of Agamotto
    t.fill(CX - 1, 11, 9, CX + 1, 11, 11, 'emerald_block')
    t.set(CX, 12, 10, 'gold_block')
    t.chest(CX, 13, 10, 'south', 'sanctum_sanctorum')
    for (x, z) in ((CX - 1, 9), (CX + 1, 9), (CX - 1, 11), (CX + 1, 11)):
        t.set(x, 12, z, 'lime_candle', {'candles': '4', 'lit': 'true'})
    for x in (CX - 2, CX + 2):
        t.fill(x, 11, 8, x, 14, 8, 'gold_block')
        t.set(x, 15, 8, 'lantern', {'hanging': 'false'})
    return t
