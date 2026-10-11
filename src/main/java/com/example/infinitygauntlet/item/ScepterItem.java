package com.example.infinitygauntlet.item;

import com.example.infinitygauntlet.ability.AbilityEffects;
import com.example.infinitygauntlet.ability.Sfx;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

/** Right-click a creature to bend it to your will. Works without the Mind Stone. */
public class ScepterItem extends Item {
    public ScepterItem(Properties props) {
        super(props);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) return InteractionResultHolder.sidedSuccess(stack, true);

        ServerPlayer sp = (ServerPlayer) player;
        ServerLevel sl = sp.serverLevel();
        LivingEntity target = AbilityEffects.findTarget(sp, 32);
        if (target == null) return InteractionResultHolder.fail(stack);

        if (target instanceof Mob mob) {
            List<LivingEntity> nearby = sl.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(16),
                    e -> e != sp && e instanceof Enemy);
            LivingEntity other = AbilityEffects.nearestOther(mob, nearby, 16);
            if (other != null) mob.setTarget(other);
            mob.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 300, 1));
        } else {
            target.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 200, 0));
            target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 100, 2));
        }
        target.addEffect(new MobEffectInstance(MobEffects.GLOWING, 300, 0));
        sl.sendParticles(ParticleTypes.ENCHANT, target.getX(), target.getY() + 1.5, target.getZ(), 30, 0.4, 0.4, 0.4, 0.05);
        Sfx.play(sl, sp.position(), SoundEvents.EVOKER_CAST_SPELL);
        sp.getCooldowns().addCooldown(this, 60);
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public boolean isFoil(ItemStack stack) { return true; }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> tip, TooltipFlag flag) {
        tip.add(Component.translatable("tooltip.infinitygauntlet.scepter").withStyle(ChatFormatting.GRAY));
    }
}
