package com.example.infinitygauntlet.ability;

import com.example.infinitygauntlet.Config;
import com.example.infinitygauntlet.InfinityGauntlet;
import com.example.infinitygauntlet.StoneType;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

public enum Ability {
    // Power
    POWER_BLAST(StoneType.POWER, 100, AbilityEffects::powerBlast),
    SMITE(StoneType.POWER, 80, AbilityEffects::smite),
    TITAN_LEAP(StoneType.POWER, 80, AbilityEffects::titanLeap),
    POWER_BEAM(StoneType.POWER, 140, AbilityEffects::powerBeam),
    // Space
    BLINK(StoneType.SPACE, 40, AbilityEffects::blink),
    GRAVITY_WELL(StoneType.SPACE, 160, AbilityEffects::gravityWell),
    HOME_WARP(StoneType.SPACE, 1200, AbilityEffects::homeWarp),
    // Reality
    TRANSMUTE(StoneType.REALITY, 400, AbilityEffects::transmute),
    REALITY_WARP(StoneType.REALITY, 300, AbilityEffects::realityWarp),
    REALITY_FEAST(StoneType.REALITY, 600, AbilityEffects::realityFeast),
    // Soul
    SOUL_HEAL(StoneType.SOUL, 400, AbilityEffects::soulHeal),
    SOUL_DRAIN(StoneType.SOUL, 120, AbilityEffects::soulDrain),
    SOUL_WARD(StoneType.SOUL, 900, AbilityEffects::soulWard),
    // Time
    TIME_FREEZE(StoneType.TIME, 600, AbilityEffects::timeFreeze),
    TIME_SURGE(StoneType.TIME, 900, AbilityEffects::timeSurge),
    CHRONO_BLOOM(StoneType.TIME, 200, AbilityEffects::chronoBloom),
    TIME_REWIND(StoneType.TIME, 1200, AbilityEffects::timeRewind),
    // Mind
    MIND_CONTROL(StoneType.MIND, 300, AbilityEffects::mindControl),
    TELEPATHY(StoneType.MIND, 600, AbilityEffects::telepathy),
    PACIFY(StoneType.MIND, 400, AbilityEffects::pacify),
    // Needs all six stones
    SNAP(null, 6000, AbilityEffects::snap);

    @FunctionalInterface
    interface Executor {
        boolean run(ServerLevel level, ServerPlayer player);
    }

    public final StoneType stone;
    private final int baseCooldown;
    private final Executor executor;

    Ability(StoneType stone, int baseCooldown, Executor executor) {
        this.stone = stone;
        this.baseCooldown = baseCooldown;
        this.executor = executor;
    }

    public String id() {
        return name().toLowerCase(Locale.ROOT);
    }

    public Component displayName() {
        return Component.translatable("ability." + InfinityGauntlet.MODID + "." + id());
    }

    public boolean isEnabled() {
        return !Config.csv(Config.DISABLED_ABILITIES.get()).contains(id());
    }

    public int cooldownTicks() {
        return Math.max(1, (int) Math.round(baseCooldown * Config.COOLDOWN_MULTIPLIER.get()));
    }

    public boolean execute(ServerPlayer player) {
        return executor.run(player.serverLevel(), player);
    }

    /** Abilities usable with the given stone bitmask, in a stable order. */
    public static List<Ability> available(int mask) {
        List<Ability> list = new ArrayList<>();
        for (Ability a : values()) {
            if (a.stone == null) {
                if (mask == StoneType.allMask()) list.add(a);
            } else if ((mask & a.stone.bit()) != 0) {
                list.add(a);
            }
        }
        return list;
    }

    public static List<Ability> forStone(StoneType type) {
        List<Ability> list = new ArrayList<>();
        for (Ability a : values()) if (a.stone == type) list.add(a);
        return list;
    }
}
