package com.example.infinitygauntlet.item;

import com.example.infinitygauntlet.ability.Ability;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;

/** All gauntlet state lives in the stack's CUSTOM_DATA component. */
public final class GauntletData {
    private GauntletData() {}

    private static CompoundTag tag(ItemStack s) {
        return s.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
    }

    public static int getStones(ItemStack s) { return tag(s).getInt("Stones"); }

    public static void setStones(ItemStack s, int mask) {
        CustomData.update(DataComponents.CUSTOM_DATA, s, t -> t.putInt("Stones", mask));
        sync(s, mask);
    }

    /** The item model switches on custom_model_data (the stone bitmask) to draw the socketed stones. */
    public static void sync(ItemStack s, int mask) {
        CustomModelData current = s.get(DataComponents.CUSTOM_MODEL_DATA);
        if (current == null || current.value() != mask) {
            s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(mask));
        }
    }

    public static int getSelected(ItemStack s) { return tag(s).getInt("Selected"); }

    public static void setSelected(ItemStack s, int index) {
        CustomData.update(DataComponents.CUSTOM_DATA, s, t -> t.putInt("Selected", index));
    }

    public static long getReady(ItemStack s, Ability a) { return tag(s).getLong("Cd_" + a.id()); }

    public static void setReady(ItemStack s, Ability a, long gameTime) {
        CustomData.update(DataComponents.CUSTOM_DATA, s, t -> t.putLong("Cd_" + a.id(), gameTime));
    }
}
