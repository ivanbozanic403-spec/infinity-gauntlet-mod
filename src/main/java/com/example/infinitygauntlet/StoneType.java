package com.example.infinitygauntlet;

import java.util.Locale;
import net.minecraft.network.chat.Component;

public enum StoneType {
    POWER(0xA020F0),
    SPACE(0x2D6BFF),
    REALITY(0xE02020),
    SOUL(0xFF9A1F),
    TIME(0x28D048),
    MIND(0xFFE030);

    public final int color;

    StoneType(int color) {
        this.color = color;
    }

    public String id() {
        return name().toLowerCase(Locale.ROOT);
    }

    public int bit() {
        return 1 << ordinal();
    }

    public static int allMask() {
        return (1 << values().length) - 1;
    }

    public Component displayName() {
        return Component.translatable("item." + InfinityGauntlet.MODID + "." + id() + "_stone")
                .withStyle(s -> s.withColor(color));
    }
}
