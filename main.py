import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_GUILD_ID = 1328638885659545682  # ここにギルドIDを入れてください

notify_settings = {}
notification_channels = {}

@bot.event
async def on_ready():
    guild = discord.Object(id=TARGET_GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"{bot.user} でログインしました！")

def is_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.manage_guild

@bot.tree.command(name="join_notify", description="入室通知をON/OFF切り替えます", guild=discord.Object(id=TARGET_GUILD_ID))
@app_commands.describe(mode="on または off を指定してください")
async def notify(interaction: discord.Interaction, mode: str):
    if interaction.guild_id != TARGET_GUILD_ID:
        return

    if not is_admin(interaction):
        await interaction.response.send_message("❌ 管理者権限が必要です。", ephemeral=True)
        return

    mode = mode.lower()
    if mode == "on":
        if interaction.guild_id not in notification_channels:
            await interaction.response.send_message("⚠️ 先に /setchannel で通知チャンネルを設定してください。", ephemeral=True)
            return
        notify_settings[interaction.guild_id] = True
        await interaction.response.send_message("✅ 入室通知をONにしました。", ephemeral=True)
    elif mode == "off":
        notify_settings[interaction.guild_id] = False
        await interaction.response.send_message("🚫 入室通知をOFFにしました。", ephemeral=True)
    else:
        await interaction.response.send_message("❌ 'on' または 'off' を指定してください。", ephemeral=True)


@bot.tree.command(name="setchannel", description="通知メッセージを送るチャンネルを設定します", guild=discord.Object(id=TARGET_GUILD_ID))
@app_commands.describe(channel="通知チャンネルを選択してください")
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.guild_id != TARGET_GUILD_ID:
        return

    if not is_admin(interaction):
        await interaction.response.send_message("❌ 管理者権限が必要です。", ephemeral=True)
        return

    notification_channels[interaction.guild_id] = channel.id
    await interaction.response.send_message(f"✅ 通知チャンネルを {channel.mention} に設定しました。", ephemeral=True)


def get_account_age_days(user: discord.User) -> int:
    now = datetime.now(timezone.utc)  # ここを修正
    created_at = user.created_at
    return (now - created_at).days

@bot.event
async def on_member_join(member):
    if member.guild.id != TARGET_GUILD_ID:
        return
    if not notify_settings.get(member.guild.id, False):
        return
    channel_id = notification_channels.get(member.guild.id)
    if not channel_id:
        return
    channel = member.guild.get_channel(channel_id)
    if not channel:
        return

    days = get_account_age_days(member)
    embed = discord.Embed(
        title="メンバーが参加しました！",
        description=f"{member.mention} さんがサーバーに参加しました！",
        color=discord.Color.green()
    )
    embed.add_field(name="ユーザーID", value=str(member.id), inline=True)
    embed.add_field(name="アカウント作成日数", value=f"{days} 日前", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="入室通知")

    await channel.send(embed=embed)

from datetime import datetime, timezone  # 既に読み込んでいる場合は不要

leave_notify_settings = {}

@bot.tree.command(name="leave_notify", description="退出通知をON/OFF切り替えます", guild=discord.Object(id=TARGET_GUILD_ID))
@app_commands.describe(mode="on または off を指定してください")
async def leave_notify(interaction: discord.Interaction, mode: str):
    if interaction.guild_id != TARGET_GUILD_ID:
        return

    if not is_admin(interaction):
        await interaction.response.send_message("❌ 管理者権限が必要です。", ephemeral=True)
        return

    mode = mode.lower()
    if mode == "on":
        if interaction.guild_id not in notification_channels:
            await interaction.response.send_message("⚠️ 先に /setchannel で通知チャンネルを設定してください。", ephemeral=True)
            return
        leave_notify_settings[interaction.guild_id] = True
        await interaction.response.send_message("✅ 退出通知をONにしました。", ephemeral=True)
    elif mode == "off":
        leave_notify_settings[interaction.guild_id] = False
        await interaction.response.send_message("🚫 退出通知をOFFにしました。", ephemeral=True)
    else:
        await interaction.response.send_message("❌ 'on' または 'off' を指定してください。", ephemeral=True)

@bot.event
async def on_member_remove(member):
    if member.guild.id != TARGET_GUILD_ID:
        return
    if not leave_notify_settings.get(member.guild.id, False):  # ここだけ変更
        return
    channel_id = notification_channels.get(member.guild.id)
    if not channel_id:
        return
    channel = member.guild.get_channel(channel_id)
    if not channel:
        return

    now = datetime.now(timezone.utc).astimezone()
    timestamp_str = now.strftime("%Y/%m/%d %H:%M:%S")

    embed = discord.Embed(
        title="メンバーが退出しました",
        description=f"{member.name}#{member.discriminator} さんがサーバーを退出しました。",
        color=discord.Color.red()
    )
    embed.add_field(name="退出時刻", value=timestamp_str, inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="退出通知")

    await channel.send(embed=embed)


bot.run(TOKEN)
