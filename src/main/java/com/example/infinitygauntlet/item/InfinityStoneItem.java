package com.example.infinitygauntlet.item;

import com.example.infinitygauntlet.Config;
import com.example.infinitygauntlet.StoneType;
import com.example.infinitygauntlet.ability.Ability;
import com.example.infinitygauntlet.ability.AbilityManager;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

public class InfinityStoneItem extends Item {
    private final StoneType type;

    public InfinityStoneItem(StoneType type, Properties props) {
        super(props);
        this.type = type;
    }

    public StoneType type() { return type; }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        InteractionHand otherHand = hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND;
        // Let the gauntlet handle socketing if it is in the other hand.
        if (player.getItemInHand(otherHand).getItem() instanceof GauntletItem) return InteractionResultHolder.pass(stack);
        if (!Config.STANDALONE_STONES.get()) return InteractionResultHolder.pass(stack);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);

        ServerPlayer sp = (ServerPlayer) player;
        Ability first = Ability.forStone(type).get(0);
        int cooldown = AbilityManager.run(sp, first);
        if (cooldown < 0) return InteractionResultHolder.fail(stack);
        sp.getCooldowns().addCooldown(this, cooldown * 2);
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public boolean isFoil(ItemStack stack) { return true; }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> tip, TooltipFlag flag) {
        tip.add(Component.translatable("tooltip.infinitygauntlet.lore." + type.id())
                .withStyle(ChatFormatting.ITALIC, ChatFormatting.GRAY));
        for (Ability a : Ability.forStone(type)) {
            tip.add(Component.literal("\u2022 ").withStyle(ChatFormatting.GRAY).append(a.displayName()));
        }
        tip.add(Component.translatable("tooltip.infinitygauntlet.stone_hint").withStyle(ChatFormatting.DARK_GRAY));
    }
}
