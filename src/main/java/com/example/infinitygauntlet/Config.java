package com.example.infinitygauntlet;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import net.neoforged.neoforge.common.ModConfigSpec;

/** Everything a modpack author is likely to want to tune lives here. */
public final class Config {
    private static final ModConfigSpec.Builder B = new ModConfigSpec.Builder();

    public static final ModConfigSpec.DoubleValue DAMAGE_MULTIPLIER = B
            .comment("Multiplier applied to all damage dealt by gauntlet abilities.")
            .defineInRange("damageMultiplier", 1.0, 0.0, 100.0);

    public static final ModConfigSpec.DoubleValue COOLDOWN_MULTIPLIER = B
            .comment("Multiplier applied to all ability cooldowns. 0.5 = twice as fast, 2.0 = twice as slow.")
            .defineInRange("cooldownMultiplier", 1.0, 0.0, 100.0);

    public static final ModConfigSpec.BooleanValue STANDALONE_STONES = B
            .comment("If true, a stone used on its own (outside the gauntlet) casts its first ability at double cooldown.")
            .define("standaloneStones", true);

    public static final ModConfigSpec.DoubleValue SNAP_FRACTION = B
            .comment("Fraction of hostile mobs in range removed by the Snap.")
            .defineInRange("snapFraction", 0.5, 0.0, 1.0);

    public static final ModConfigSpec.BooleanValue SNAP_PASSIVE = B
            .comment("If true, the Snap also dusts passive creatures (never tamed or name-tagged ones).")
            .define("snapAffectsPassive", false);

    public static final ModConfigSpec.IntValue SNAP_RADIUS = B
            .comment("Radius in blocks affected by the Snap.")
            .defineInRange("snapRadius", 48, 4, 256);

    public static final ModConfigSpec.DoubleValue SNAP_HEALTH_COST = B
            .comment("Health the wielder loses when snapping (never drops below half a heart).")
            .defineInRange("snapHealthCost", 10.0, 0.0, 1000.0);

    public static final ModConfigSpec.ConfigValue<String> DISABLED_ABILITIES = B
            .comment("Comma separated ability ids to disable, e.g. \"snap,home_warp,transmute\".")
            .define("disabledAbilities", "");

    public static final ModConfigSpec.ConfigValue<String> DISABLED_DIMENSIONS = B
            .comment("Comma separated dimension ids where abilities are disabled, e.g. \"minecraft:the_end,mypack:arena\".")
            .define("disabledDimensions", "");

    public static final ModConfigSpec SPEC = B.build();

    private Config() {}

    public static List<String> csv(String s) {
        return Arrays.stream(s.split(","))
                .map(x -> x.trim().toLowerCase(Locale.ROOT))
                .filter(x -> !x.isEmpty())
                .toList();
    }
}
