package com.example.infinitygauntlet.ability;

import com.example.infinitygauntlet.Config;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.common.NeoForge;

public final class AbilityManager {
    private AbilityManager() {}

    /**
     * Runs an ability after all checks (config, dimension, event).
     * @return cooldown in ticks if it ran, or -1 if it did not.
     */
    public static int run(ServerPlayer player, Ability ability) {
        if (!ability.isEnabled()) {
            player.displayClientMessage(Component.translatable("message.infinitygauntlet.disabled"), true);
            return -1;
        }
        String dim = player.level().dimension().location().toString();
        if (Config.csv(Config.DISABLED_DIMENSIONS.get()).contains(dim)) {
            player.displayClientMessage(Component.translatable("message.infinitygauntlet.disabled_dimension"), true);
            return -1;
        }
        AbilityUseEvent event = new AbilityUseEvent(player, ability);
        NeoForge.EVENT_BUS.post(event);
        if (event.isCanceled()) return -1;

        if (!ability.execute(player)) {
            player.displayClientMessage(Component.translatable("message.infinitygauntlet.no_effect"), true);
            return -1;
        }
        return ability.cooldownTicks();
    }
}
