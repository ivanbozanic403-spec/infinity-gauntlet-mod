package com.example.infinitygauntlet;

import com.example.infinitygauntlet.item.GauntletData;
import com.example.infinitygauntlet.item.GauntletItem;
import com.example.infinitygauntlet.item.InfinityStoneItem;
import com.example.infinitygauntlet.item.ScepterItem;
import java.util.EnumMap;
import java.util.Map;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(InfinityGauntlet.MODID);
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, InfinityGauntlet.MODID);

    public static final Map<StoneType, DeferredHolder<Item, InfinityStoneItem>> STONES = new EnumMap<>(StoneType.class);

    static {
        for (StoneType type : StoneType.values()) {
            STONES.put(type, ITEMS.register(type.id() + "_stone",
                    () -> new InfinityStoneItem(type, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant())));
        }
    }

    public static final DeferredHolder<Item, GauntletItem> GAUNTLET = ITEMS.register("infinity_gauntlet",
            () -> new GauntletItem(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()));

    public static final DeferredHolder<Item, ScepterItem> SCEPTER = ITEMS.register("scepter",
            () -> new ScepterItem(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()));

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> TAB = TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup." + InfinityGauntlet.MODID))
                    .icon(() -> new ItemStack(GAUNTLET.get()))
                    .displayItems((params, out) -> {
                        out.accept(GAUNTLET.get());
                        ItemStack full = new ItemStack(GAUNTLET.get());
                        GauntletData.setStones(full, StoneType.allMask());
                        out.accept(full);
                        STONES.values().forEach(h -> out.accept(h.get()));
                        out.accept(SCEPTER.get());
                    })
                    .build());

    private ModItems() {}
}
