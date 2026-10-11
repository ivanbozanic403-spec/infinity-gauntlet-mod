package com.example.infinitygauntlet.ability;

import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.Event;
import net.neoforged.bus.api.ICancellableEvent;

/**
 * Posted on NeoForge.EVENT_BUS (server side) before any ability runs.
 * Cancel it from another mod / KubeJS-style integration to block the ability.
 */
public class AbilityUseEvent extends Event implements ICancellableEvent {
    private final ServerPlayer player;
    private final Ability ability;

    public AbilityUseEvent(ServerPlayer player, Ability ability) {
        this.player = player;
        this.ability = ability;
    }

    public ServerPlayer getPlayer() { return player; }
    public Ability getAbility() { return ability; }
}
