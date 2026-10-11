package com.example.infinitygauntlet.item;

import com.example.infinitygauntlet.StoneType;
import com.example.infinitygauntlet.ability.Ability;
import com.example.infinitygauntlet.ability.AbilityManager;
import com.example.infinitygauntlet.ability.Sfx;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

public class GauntletItem extends Item {
    public GauntletItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        InteractionHand otherHand = hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND;
        ItemStack other = player.getItemInHand(otherHand);
        int mask = GauntletData.getStones(stack);
        if (!level.isClientSide) GauntletData.sync(stack, mask);

        // Socket a stone held in the other hand.
        if (other.getItem() instanceof InfinityStoneItem stone && (mask & stone.type().bit()) == 0) {
            if (!level.isClientSide) {
                other.shrink(1);
                GauntletData.setStones(stack, mask | stone.type().bit());
                Sfx.play(level, player.position(), SoundEvents.AMETHYST_BLOCK_RESONATE);
                player.displayClientMessage(
                        Component.translatable("message.infinitygauntlet.inserted", stone.type().displayName()), true);
            }
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }

        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);

        ServerPlayer sp = (ServerPlayer) player;
        List<Ability> available = Ability.available(mask);
        if (available.isEmpty()) {
            sp.displayClientMessage(Component.translatable("message.infinitygauntlet.no_stones"), true);
            return InteractionResultHolder.fail(stack);
        }
        int selected = Math.floorMod(GauntletData.getSelected(stack), available.size());

        // Sneak + use cycles the selected ability.
        if (sp.isShiftKeyDown()) {
            selected = (selected + 1) % available.size();
            GauntletData.setSelected(stack, selected);
            sp.displayClientMessage(Component.translatable("message.infinitygauntlet.selected",
                    available.get(selected).displayName()), true);
            return InteractionResultHolder.consume(stack);
        }

        Ability ability = available.get(selected);
        long now = level.getGameTime();
        long ready = GauntletData.getReady(stack, ability);
        if (ready > now) {
            sp.displayClientMessage(Component.translatable("message.infinitygauntlet.cooldown",
                    ability.displayName(), (ready - now + 19) / 20), true);
            return InteractionResultHolder.fail(stack);
        }

        int cooldown = AbilityManager.run(sp, ability);
        if (cooldown < 0) return InteractionResultHolder.fail(stack);
        GauntletData.setReady(stack, ability, now + cooldown);
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public boolean shouldCauseReequipAnimation(ItemStack oldStack, ItemStack newStack, boolean slotChanged) {
        return slotChanged; // cooldown/selection changes shouldn't bounce the item
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return GauntletData.getStones(stack) == StoneType.allMask();
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> tip, TooltipFlag flag) {
        int mask = GauntletData.getStones(stack);
        for (StoneType t : StoneType.values()) {
            boolean has = (mask & t.bit()) != 0;
            tip.add(Component.literal(has ? "\u25C6 " : "\u25C7 ").withStyle(ChatFormatting.GRAY).append(t.displayName()));
        }
        List<Ability> available = Ability.available(mask);
        if (!available.isEmpty()) {
            Ability sel = available.get(Math.floorMod(GauntletData.getSelected(stack), available.size()));
            tip.add(Component.translatable("tooltip.infinitygauntlet.selected", sel.displayName())
                    .withStyle(ChatFormatting.AQUA));
        }
        tip.add(Component.translatable("tooltip.infinitygauntlet.gauntlet_hint").withStyle(ChatFormatting.DARK_GRAY));
    }
}
