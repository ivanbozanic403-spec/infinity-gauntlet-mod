package com.example.infinitygauntlet;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EntityType;

public final class ModTags {
    /** Entities listed here can never be removed by the Snap. Other mods/datapacks can add their bosses. */
    public static final TagKey<EntityType<?>> SNAP_IMMUNE = TagKey.create(
            Registries.ENTITY_TYPE, ResourceLocation.fromNamespaceAndPath(InfinityGauntlet.MODID, "snap_immune"));

    private ModTags() {}
}
