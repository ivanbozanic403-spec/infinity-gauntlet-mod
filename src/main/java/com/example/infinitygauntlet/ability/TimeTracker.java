package com.example.infinitygauntlet.ability;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** Keeps a rolling ten-second history of each player so Time Rewind has somewhere to go back to. */
public final class TimeTracker {
    public record Snapshot(ResourceKey<Level> dim, Vec3 pos, float yRot, float xRot, float health) {}

    private static final int INTERVAL_TICKS = 10;
    private static final int MAX_SNAPSHOTS = 20;
    private static final Map<UUID, ArrayDeque<Snapshot>> HISTORY = new HashMap<>();

    private TimeTracker() {}

    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer p)) return;
        if (!p.isAlive() || p.tickCount % INTERVAL_TICKS != 0) return;
        ArrayDeque<Snapshot> q = HISTORY.computeIfAbsent(p.getUUID(), k -> new ArrayDeque<>());
        q.addLast(new Snapshot(p.level().dimension(), p.position(), p.getYRot(), p.getXRot(), p.getHealth()));
        while (q.size() > MAX_SNAPSHOTS) q.removeFirst();
    }

    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        HISTORY.remove(event.getEntity().getUUID());
    }

    /** The oldest remembered state (about ten seconds ago), or null if there is none yet. */
    public static Snapshot oldest(ServerPlayer p) {
        ArrayDeque<Snapshot> q = HISTORY.get(p.getUUID());
        return q == null ? null : q.peekFirst();
    }

    public static void reset(ServerPlayer p) {
        HISTORY.remove(p.getUUID());
    }
}
