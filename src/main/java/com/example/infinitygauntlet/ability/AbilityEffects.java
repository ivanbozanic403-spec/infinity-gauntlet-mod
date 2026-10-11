package com.example.infinitygauntlet.ability;

import com.example.infinitygauntlet.Config;
import com.example.infinitygauntlet.ModTags;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.Sheep;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/** Server-side implementations of every ability. Each returns true if it did something. */
public final class AbilityEffects {
    private AbilityEffects() {}

    // ---------------------------------------------------------------- helpers

    private static float dmg(double base) {
        return (float) (base * Config.DAMAGE_MULTIPLIER.get());
    }

    private static List<LivingEntity> around(ServerPlayer p, double r) {
        return p.level().getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(r),
                e -> e != p && e.isAlive() && !e.isSpectator() && e.distanceToSqr(p) <= r * r);
    }

    private static boolean immune(LivingEntity e) {
        return e.getType().is(ModTags.SNAP_IMMUNE);
    }

    private static void fx(ServerLevel l, ParticleOptions type, double x, double y, double z, int n, double spread) {
        l.sendParticles(type, x, y, z, n, spread, spread, spread, 0.02);
    }

    private static void effect(LivingEntity e, Holder<MobEffect> effect, int ticks, int amp) {
        e.addEffect(new MobEffectInstance(effect, ticks, amp));
    }

    /** Living entity under the crosshair, or null. */
    public static LivingEntity findTarget(ServerPlayer p, double range) {
        Vec3 eye = p.getEyePosition();
        Vec3 look = p.getLookAngle();
        Vec3 end = eye.add(look.scale(range));
        AABB box = p.getBoundingBox().expandTowards(look.scale(range)).inflate(1.0);
        EntityHitResult hit = ProjectileUtil.getEntityHitResult(p.level(), p, eye, end, box,
                x -> x instanceof LivingEntity && x.isAlive() && !x.isSpectator() && x != p);
        return (hit != null && hit.getEntity() instanceof LivingEntity le) ? le : null;
    }

    public static LivingEntity nearestOther(Mob self, List<? extends LivingEntity> pool, double maxDist) {
        LivingEntity best = null;
        double bestD = maxDist * maxDist;
        for (LivingEntity c : pool) {
            if (c == self || !c.isAlive()) continue;
            double d = c.distanceToSqr(self);
            if (d < bestD) {
                bestD = d;
                best = c;
            }
        }
        return best;
    }

    // ------------------------------------------------------------------ POWER

    static boolean powerBlast(ServerLevel level, ServerPlayer p) {
        for (LivingEntity e : around(p, 8)) {
            e.hurt(level.damageSources().playerAttack(p), dmg(14));
            Vec3 away = e.position().subtract(p.position());
            away = away.lengthSqr() < 1.0E-4 ? new Vec3(0, 0, 1) : away.normalize();
            e.push(away.x * 1.5, 0.6, away.z * 1.5);
            e.hurtMarked = true;
        }
        fx(level, ParticleTypes.EXPLOSION_EMITTER, p.getX(), p.getY() + 1, p.getZ(), 1, 0);
        Sfx.play(level, p.position(), SoundEvents.GENERIC_EXPLODE);
        return true;
    }

    static boolean smite(ServerLevel level, ServerPlayer p) {
        Vec3 loc = p.pick(64, 1.0f, false).getLocation();
        LivingEntity target = findTarget(p, 64);
        if (target != null) loc = target.position();
        LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(level);
        if (bolt == null) return false;
        bolt.moveTo(loc);
        bolt.setCause(p);
        level.addFreshEntity(bolt);
        return true;
    }

    static boolean titanLeap(ServerLevel level, ServerPlayer p) {
        Vec3 look = p.getLookAngle();
        p.setDeltaMovement(look.x * 2.0, 1.0, look.z * 2.0);
        p.hurtMarked = true;
        effect(p, MobEffects.SLOW_FALLING, 200, 0);
        fx(level, ParticleTypes.CLOUD, p.getX(), p.getY(), p.getZ(), 20, 0.4);
        Sfx.play(level, p.position(), SoundEvents.WITHER_SHOOT);
        return true;
    }

    /** Piercing beam of raw power (Ronan / Thanos style). Never breaks blocks. */
    static boolean powerBeam(ServerLevel level, ServerPlayer p) {
        Vec3 eye = p.getEyePosition();
        Vec3 look = p.getLookAngle();
        HitResult hit = p.pick(40, 1.0f, false);
        double len = hit.getType() == HitResult.Type.MISS ? 40 : eye.distanceTo(hit.getLocation());
        Vec3 end = eye.add(look.scale(len));
        AABB box = new AABB(eye, end).inflate(1.5);
        for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box,
                x -> x != p && x.isAlive() && !x.isSpectator())) {
            if (e.getBoundingBox().inflate(0.6).clip(eye, end).isPresent()) {
                e.hurt(level.damageSources().playerAttack(p), dmg(16));
                e.setRemainingFireTicks(80);
            }
        }
        int step = 0;
        for (double d = 1.0; d <= len; d += 0.6, step++) {
            Vec3 pt = eye.add(look.scale(d));
            level.sendParticles(ParticleTypes.DRAGON_BREATH, pt.x, pt.y, pt.z, 2, 0.05, 0.05, 0.05, 0.0);
            if (step % 3 == 0) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, pt.x, pt.y, pt.z, 1, 0.1, 0.1, 0.1, 0.0);
            }
        }
        fx(level, ParticleTypes.EXPLOSION_EMITTER, end.x, end.y, end.z, 1, 0);
        Sfx.play(level, p.position(), SoundEvents.WARDEN_SONIC_BOOM);
        return true;
    }

    // ------------------------------------------------------------------ SPACE

    static boolean blink(ServerLevel level, ServerPlayer p) {
        Vec3 eye = p.getEyePosition();
        Vec3 look = p.getLookAngle();
        HitResult hit = p.pick(48, 1.0f, false);
        double dist = hit.getType() == HitResult.Type.MISS ? 48 : eye.distanceTo(hit.getLocation());
        for (double d = dist; d >= 1.0; d -= 0.5) {
            Vec3 point = eye.add(look.scale(d));
            double dx = point.x - p.getX();
            double dy = point.y - p.getEyeY();
            double dz = point.z - p.getZ();
            if (level.noCollision(p, p.getBoundingBox().move(dx, dy, dz))) {
                fx(level, ParticleTypes.PORTAL, p.getX(), p.getY() + 1, p.getZ(), 40, 0.5);
                p.connection.teleport(p.getX() + dx, p.getY() + dy, p.getZ() + dz, p.getYRot(), p.getXRot());
                p.fallDistance = 0;
                fx(level, ParticleTypes.PORTAL, p.getX(), p.getY() + 1, p.getZ(), 40, 0.5);
                Sfx.play(level, p.position(), SoundEvents.ENDERMAN_TELEPORT);
                return true;
            }
        }
        return false;
    }

    static boolean gravityWell(ServerLevel level, ServerPlayer p) {
        List<LivingEntity> list = around(p, 16);
        for (LivingEntity e : list) {
            Vec3 pull = p.position().add(0, 1, 0).subtract(e.position());
            if (pull.lengthSqr() < 1.0E-4) continue;
            e.setDeltaMovement(pull.normalize().scale(1.1));
            e.hurtMarked = true;
            fx(level, ParticleTypes.PORTAL, e.getX(), e.getY() + 1, e.getZ(), 10, 0.3);
        }
        Sfx.play(level, p.position(), SoundEvents.BEACON_ACTIVATE);
        return !list.isEmpty();
    }

    static boolean homeWarp(ServerLevel level, ServerPlayer p) {
        ServerLevel target = level;
        BlockPos pos = p.getRespawnPosition();
        if (pos == null) {
            target = level.getServer().overworld();
            pos = target.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, target.getSharedSpawnPos());
        } else {
            ResourceKey<Level> dim = p.getRespawnDimension();
            ServerLevel t = level.getServer().getLevel(dim);
            if (t != null) target = t;
            pos = pos.above();
        }
        fx(level, ParticleTypes.PORTAL, p.getX(), p.getY() + 1, p.getZ(), 60, 0.6);
        p.teleportTo(target, pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, p.getYRot(), p.getXRot());
        p.fallDistance = 0;
        Sfx.play(target, p.position(), SoundEvents.ENDERMAN_TELEPORT);
        return true;
    }

    // ---------------------------------------------------------------- REALITY

    private static final Map<Block, Block> TRANSMUTE = Map.ofEntries(
            Map.entry(Blocks.STONE, Blocks.DIAMOND_ORE),
            Map.entry(Blocks.DEEPSLATE, Blocks.DEEPSLATE_DIAMOND_ORE),
            Map.entry(Blocks.NETHERRACK, Blocks.NETHER_GOLD_ORE),
            Map.entry(Blocks.COBBLESTONE, Blocks.STONE),
            Map.entry(Blocks.DIRT, Blocks.GRASS_BLOCK),
            Map.entry(Blocks.SAND, Blocks.GLASS),
            Map.entry(Blocks.GRAVEL, Blocks.IRON_ORE),
            Map.entry(Blocks.OAK_LOG, Blocks.DARK_OAK_LOG));

    private static BlockState transmuted(BlockState s) {
        if (s.is(Blocks.LAVA) && s.getFluidState().isSource()) return Blocks.OBSIDIAN.defaultBlockState();
        if (s.is(Blocks.WATER) && s.getFluidState().isSource()) return Blocks.ICE.defaultBlockState();
        Block b = TRANSMUTE.get(s.getBlock());
        return b == null ? null : b.defaultBlockState();
    }

    static boolean transmute(ServerLevel level, ServerPlayer p) {
        HitResult hit = p.pick(8, 1.0f, false);
        if (!(hit instanceof BlockHitResult bhr) || bhr.getType() == HitResult.Type.MISS) return false;
        BlockPos c = bhr.getBlockPos();
        int n = 0;
        for (BlockPos pos : BlockPos.betweenClosed(c.offset(-1, -1, -1), c.offset(1, 1, 1))) {
            BlockState result = transmuted(level.getBlockState(pos));
            if (result != null) {
                level.setBlockAndUpdate(pos, result);
                fx(level, ParticleTypes.WITCH, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 8, 0.4);
                n++;
            }
        }
        if (n > 0) Sfx.play(level, p.position(), SoundEvents.ENCHANTMENT_TABLE_USE);
        return n > 0;
    }

    static boolean realityWarp(ServerLevel level, ServerPlayer p) {
        int n = 0;
        for (LivingEntity e : around(p, 10)) {
            if (!(e instanceof Enemy) || immune(e)) continue;
            Sheep sheep = EntityType.SHEEP.create(level);
            if (sheep == null) continue;
            sheep.moveTo(e.getX(), e.getY(), e.getZ(), e.getYRot(), 0);
            sheep.setColor(DyeColor.byId(level.random.nextInt(16)));
            level.addFreshEntity(sheep);
            fx(level, ParticleTypes.WITCH, e.getX(), e.getY() + 1, e.getZ(), 25, 0.5);
            e.discard();
            n++;
        }
        if (n > 0) Sfx.play(level, p.position(), SoundEvents.EVOKER_CAST_SPELL);
        return n > 0;
    }

    static boolean realityFeast(ServerLevel level, ServerPlayer p) {
        p.getFoodData().setFoodLevel(20);
        p.getFoodData().setSaturation(20.0f);
        effect(p, MobEffects.REGENERATION, 100, 1);
        fx(level, ParticleTypes.HAPPY_VILLAGER, p.getX(), p.getY() + 1, p.getZ(), 20, 0.5);
        Sfx.play(level, p.position(), SoundEvents.PLAYER_BURP);
        return true;
    }

    // ------------------------------------------------------------------- SOUL

    static boolean soulHeal(ServerLevel level, ServerPlayer p) {
        p.setHealth(p.getMaxHealth());
        for (MobEffectInstance inst : new ArrayList<>(p.getActiveEffects())) {
            if (inst.getEffect().value().getCategory() == MobEffectCategory.HARMFUL) {
                p.removeEffect(inst.getEffect());
            }
        }
        for (LivingEntity e : around(p, 8)) {
            if (e instanceof Player) e.heal(10.0f);
        }
        fx(level, ParticleTypes.HEART, p.getX(), p.getY() + 1.5, p.getZ(), 12, 0.6);
        Sfx.play(level, p.position(), SoundEvents.TOTEM_USE);
        return true;
    }

    static boolean soulDrain(ServerLevel level, ServerPlayer p) {
        float total = 0;
        boolean any = false;
        for (LivingEntity e : around(p, 10)) {
            if (e instanceof Player) continue;
            e.hurt(level.damageSources().playerAttack(p), dmg(6));
            total += dmg(6);
            any = true;
            fx(level, ParticleTypes.SOUL, e.getX(), e.getY() + 1, e.getZ(), 10, 0.4);
        }
        if (any) {
            p.heal(total * 0.5f);
            Sfx.play(level, p.position(), SoundEvents.SOUL_ESCAPE);
        }
        return any;
    }

    static boolean soulWard(ServerLevel level, ServerPlayer p) {
        effect(p, MobEffects.ABSORPTION, 1200, 4);
        effect(p, MobEffects.DAMAGE_RESISTANCE, 600, 1);
        effect(p, MobEffects.FIRE_RESISTANCE, 600, 0);
        fx(level, ParticleTypes.SOUL, p.getX(), p.getY() + 1, p.getZ(), 30, 0.7);
        Sfx.play(level, p.position(), SoundEvents.BEACON_POWER_SELECT);
        return true;
    }

    // ------------------------------------------------------------------- TIME

    static boolean timeFreeze(ServerLevel level, ServerPlayer p) {
        List<LivingEntity> list = around(p, 20);
        for (LivingEntity e : list) {
            effect(e, MobEffects.MOVEMENT_SLOWDOWN, 100, 9);
            effect(e, MobEffects.WEAKNESS, 100, 9);
            fx(level, ParticleTypes.END_ROD, e.getX(), e.getY() + 1, e.getZ(), 6, 0.3);
        }
        Sfx.play(level, p.position(), SoundEvents.BEACON_DEACTIVATE);
        return !list.isEmpty();
    }

    static boolean timeSurge(ServerLevel level, ServerPlayer p) {
        effect(p, MobEffects.MOVEMENT_SPEED, 300, 3);
        effect(p, MobEffects.DIG_SPEED, 300, 3);
        effect(p, MobEffects.DAMAGE_BOOST, 300, 1);
        fx(level, ParticleTypes.ELECTRIC_SPARK, p.getX(), p.getY() + 1, p.getZ(), 30, 0.5);
        Sfx.play(level, p.position(), SoundEvents.BEACON_ACTIVATE);
        return true;
    }

    static boolean chronoBloom(ServerLevel level, ServerPlayer p) {
        BlockPos origin = p.blockPosition();
        int grown = 0;
        outer:
        for (int dx = -8; dx <= 8; dx++) {
            for (int dy = -4; dy <= 4; dy++) {
                for (int dz = -8; dz <= 8; dz++) {
                    BlockPos pos = origin.offset(dx, dy, dz);
                    BlockState state = level.getBlockState(pos);
                    if (state.getBlock() instanceof BonemealableBlock bb && bb.isValidBonemealTarget(level, pos, state)) {
                        bb.performBonemeal(level, level.random, pos, state);
                        fx(level, ParticleTypes.HAPPY_VILLAGER, pos.getX() + 0.5, pos.getY() + 0.8, pos.getZ() + 0.5, 4, 0.3);
                        if (++grown >= 300) break outer;
                    }
                }
            }
        }
        if (grown > 0) Sfx.play(level, p.position(), SoundEvents.BONE_MEAL_USE);
        return grown > 0;
    }

    /** Rewinds the wielder to where (and how healthy) they were about ten seconds ago. */
    static boolean timeRewind(ServerLevel level, ServerPlayer p) {
        TimeTracker.Snapshot s = TimeTracker.oldest(p);
        if (s == null) return false;
        ServerLevel target = level.getServer().getLevel(s.dim());
        if (target == null) return false;
        boolean sameSpot = target == level && s.pos().distanceToSqr(p.position()) < 2.25;
        if (sameSpot && s.health() <= p.getHealth()) return false;
        fx(level, ParticleTypes.REVERSE_PORTAL, p.getX(), p.getY() + 1, p.getZ(), 50, 0.5);
        p.teleportTo(target, s.pos().x, s.pos().y, s.pos().z, s.yRot(), s.xRot());
        p.fallDistance = 0;
        p.clearFire();
        if (s.health() > p.getHealth()) p.setHealth(Math.min(p.getMaxHealth(), s.health()));
        TimeTracker.reset(p);
        fx(target, ParticleTypes.REVERSE_PORTAL, p.getX(), p.getY() + 1, p.getZ(), 50, 0.5);
        Sfx.play(target, p.position(), SoundEvents.BEACON_DEACTIVATE);
        return true;
    }

    // ------------------------------------------------------------------- MIND

    static boolean mindControl(ServerLevel level, ServerPlayer p) {
        List<Mob> hostile = new ArrayList<>();
        for (LivingEntity e : around(p, 24)) {
            if (e instanceof Mob m && e instanceof Enemy) hostile.add(m);
        }
        int n = 0;
        for (Mob m : hostile) {
            LivingEntity other = nearestOther(m, hostile, 16);
            if (other == null) continue;
            m.setTarget(other);
            effect(m, MobEffects.GLOWING, 200, 0);
            fx(level, ParticleTypes.ENCHANT, m.getX(), m.getY() + 1.5, m.getZ(), 15, 0.4);
            n++;
        }
        if (n > 0) Sfx.play(level, p.position(), SoundEvents.EVOKER_PREPARE_SUMMON);
        return n > 0;
    }

    static boolean telepathy(ServerLevel level, ServerPlayer p) {
        for (LivingEntity e : around(p, 64)) effect(e, MobEffects.GLOWING, 300, 0);
        effect(p, MobEffects.NIGHT_VISION, 300, 0);
        Sfx.play(level, p.position(), SoundEvents.ENCHANTMENT_TABLE_USE);
        return true;
    }

    static boolean pacify(ServerLevel level, ServerPlayer p) {
        int n = 0;
        for (LivingEntity e : around(p, 24)) {
            if (e instanceof Mob m && e instanceof Enemy) {
                m.setTarget(null);
                m.setLastHurtByMob(null);
                m.getNavigation().stop();
                effect(m, MobEffects.WEAKNESS, 200, 1);
                fx(level, ParticleTypes.HAPPY_VILLAGER, m.getX(), m.getY() + 1.5, m.getZ(), 8, 0.4);
                n++;
            }
        }
        return n > 0;
    }

    // ------------------------------------------------------------------- SNAP

    static boolean snap(ServerLevel level, ServerPlayer p) {
        List<LivingEntity> targets = new ArrayList<>();
        for (LivingEntity e : around(p, Config.SNAP_RADIUS.get())) {
            boolean hostile = e instanceof Enemy;
            boolean passive = Config.SNAP_PASSIVE.get() && e instanceof Mob && !hostile && !e.hasCustomName()
                    && !(e instanceof TamableAnimal pet && pet.isTame());
            if ((hostile || passive) && !immune(e)) targets.add(e);
        }
        if (targets.isEmpty()) return false;
        Collections.shuffle(targets, new Random(level.random.nextLong()));
        int kills = (int) Math.ceil(targets.size() * Config.SNAP_FRACTION.get());
        for (int i = 0; i < kills && i < targets.size(); i++) {
            LivingEntity e = targets.get(i);
            fx(level, ParticleTypes.ASH, e.getX(), e.getY() + 1, e.getZ(), 60, 0.6);
            fx(level, ParticleTypes.POOF, e.getX(), e.getY() + 1, e.getZ(), 10, 0.4);
            e.hurt(level.damageSources().playerAttack(p), 10000.0f);
            if (e.isAlive()) e.kill();
        }
        float cost = Config.SNAP_HEALTH_COST.get().floatValue();
        p.setHealth(Math.max(1.0f, p.getHealth() - cost));
        Sfx.play(level, p.position(), SoundEvents.LIGHTNING_BOLT_THUNDER);
        p.displayClientMessage(Component.translatable("message.infinitygauntlet.snap", kills), true);
        return true;
    }
}
