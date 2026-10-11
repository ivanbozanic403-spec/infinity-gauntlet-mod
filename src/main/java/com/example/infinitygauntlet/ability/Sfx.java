package com.example.infinitygauntlet.ability;

import net.minecraft.core.Holder;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** Overloads so callers can pass either a SoundEvent or a Holder<SoundEvent>. */
public final class Sfx {
    private Sfx() {}

    public static void play(Level level, Vec3 pos, SoundEvent sound) {
        level.playSound(null, pos.x, pos.y, pos.z, sound, SoundSource.PLAYERS, 1.0f, 1.0f);
    }

    public static void play(Level level, Vec3 pos, Holder<SoundEvent> sound) {
        play(level, pos, sound.value());
    }
}
