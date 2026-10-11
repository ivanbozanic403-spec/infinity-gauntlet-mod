package com.example.infinitygauntlet;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import com.example.infinitygauntlet.ability.TimeTracker;

@Mod(InfinityGauntlet.MODID)
public class InfinityGauntlet {
    public static final String MODID = "infinitygauntlet";

    public InfinityGauntlet(IEventBus modBus, ModContainer container) {
        ModItems.ITEMS.register(modBus);
        ModItems.TABS.register(modBus);
        container.registerConfig(ModConfig.Type.COMMON, Config.SPEC);
        NeoForge.EVENT_BUS.addListener((PlayerTickEvent.Post e) -> TimeTracker.onPlayerTick(e));
        NeoForge.EVENT_BUS.addListener((PlayerEvent.PlayerLoggedOutEvent e) -> TimeTracker.onLogout(e));
    }
}
