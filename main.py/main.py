import discord
import asyncio
import random
import re
import time

from datetime import timedelta
from discord.ext import commands
from discord.ui import View


# =========================
# AYARLAR
# =========================

TOKEN = "YENI_TOKENINI_BURAYA_YAZ"

TICKET_CATEGORY = "Tickets"
STAFF_ROLE = "Yetkili"

WELCOME_CHANNEL = "📥╎hoşgeldi̇n"
GOODBYE_CHANNEL = "📥╎hoşgeldi̇n"

AUTO_ROLE = "· | Member Of Valthera"


# =========================
# BOT
# =========================

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# =========================
# YETKİ KONTROLÜ
# =========================

def is_staff():

    async def predicate(ctx):

        if ctx.author.guild_permissions.administrator:
            return True

        role = discord.utils.get(
            ctx.guild.roles,
            name=STAFF_ROLE
        )

        if role and role in ctx.author.roles:
            return True

        raise commands.CheckFailure(
            "Yetkili rolü veya Administrator gerekli."
        )

    return commands.check(predicate)


# =========================
# BOT AÇILDI
# =========================

@bot.event
async def on_ready():

    print("--------------------------------")
    print(f"{bot.user} aktif!")
    print("Valthera botu çalışıyor!")
    print(f"Sunucu sayısı: {len(bot.guilds)}")
    print("--------------------------------")

    try:
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())
    except Exception as e:
        print(f"View yüklenirken hata: {e}")


# =========================
# ÜYE GİRİNCE
# =========================

@bot.event
async def on_member_join(member):

    role = discord.utils.get(
        member.guild.roles,
        name=AUTO_ROLE
    )

    if role:
        try:
            await member.add_roles(role)
            print(f"{member} kullanıcısına oto rol verildi.")
        except discord.Forbidden:
            print("Oto rol verilemedi!")
    else:
        print(f"'{AUTO_ROLE}' rolü bulunamadı.")

    channel = discord.utils.get(
        member.guild.text_channels,
        name=WELCOME_CHANNEL
    )

    if channel is None:
        print("Hoş geldin kanalı bulunamadı!")
        return

    embed = discord.Embed(
        title="👋 Hoş Geldin!",
        description=(
            f"Sunucumuza hoş geldin {member.mention}! 🎉\n\n"
            f"👥 Seninle birlikte **{member.guild.member_count}** kişi olduk."
        ),
        color=discord.Color.green()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    await channel.send(embed=embed)


# =========================
# ÜYE AYRILINCA
# =========================

@bot.event
async def on_member_remove(member):

    channel = discord.utils.get(
        member.guild.text_channels,
        name=GOODBYE_CHANNEL
    )

    if channel is None:
        print("Güle güle kanalı bulunamadı!")
        return

    await channel.send(
        f"👋 **{member.name}** sunucudan ayrıldı.\n"
        f"👥 Sunucuda artık **{member.guild.member_count}** kişi kaldı."
    )


# =========================================================
# TICKET KAPAT
# =========================================================

class CloseTicketView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ticket Kapat",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                "❌ Bu kanal bir ticket değil.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Ticket kapatılıyor...",
            ephemeral=True
        )

        await asyncio.sleep(2)

        await interaction.channel.delete()


# =========================================================
# TICKET SİSTEMİ
# =========================================================

class TicketView(View):

    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(
        self,
        interaction: discord.Interaction,
        ticket_type: str
    ):

        guild = interaction.guild
        user = interaction.user

        existing_ticket = discord.utils.find(
            lambda channel:
                channel.name == f"ticket-{user.id}",
            guild.text_channels
        )

        if existing_ticket:
            await interaction.response.send_message(
                f"❌ Zaten açık bir ticketın var: "
                f"{existing_ticket.mention}",
                ephemeral=True
            )
            return

        staff_role = discord.utils.get(
            guild.roles,
            name=STAFF_ROLE
        )

        bot_member = guild.me

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),

            bot_member:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

        category = discord.utils.get(
            guild.categories,
            name=TICKET_CATEGORY
        )

        if category is None:
            category = await guild.create_category(
                TICKET_CATEGORY
            )

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites,
            topic=f"{ticket_type} | {user}"
        )

        embed = discord.Embed(
            title=f"🎫 {ticket_type}",
            description=(
                f"Hoş geldin {user.mention}! 👋\n\n"
                f"📌 **Talep türü:** {ticket_type}\n\n"
                "Yetkili ekip en kısa sürede seninle ilgilenecektir.\n\n"
                "🔒 Ticketı kapatmak için aşağıdaki "
                "butona basabilirsin."
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="Valthera Destek Sistemi"
        )

        await channel.send(
            content=user.mention,
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Ticket oluşturuldu: {channel.mention}",
            ephemeral=True
        )

    # =========================
    # EKİP ALIM
    # =========================

    @discord.ui.button(
        label="Ekip Alım",
        emoji="🛡️",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_ekip"
    )
    async def ekip(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.create_ticket(
            interaction,
            "Ekip Alım"
        )

    # =========================
    # ALLY
    # =========================

    @discord.ui.button(
        label="Ally",
        emoji="🤝",
        style=discord.ButtonStyle.success,
        custom_id="ticket_ally"
    )
    async def ally(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.create_ticket(
            interaction,
            "Ally"
        )

    # =========================
    # PARTNERLIK
    # =========================

    @discord.ui.button(
        label="Partnerlık",
        emoji="🔗",
        style=discord.ButtonStyle.success,
        custom_id="ticket_partner"
    )
    async def partner(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.create_ticket(
            interaction,
            "Partnerlık"
        )

    # =========================
    # GENEL DESTEK
    # =========================

    @discord.ui.button(
        label="Genel Destek",
        emoji="🎫",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_destek"
    )
    async def destek(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.create_ticket(
            interaction,
            "Genel Destek"
        )


# =========================================================
# TICKET PANELİ
# =========================================================

@bot.command()
@commands.has_permissions(administrator=True)
async def ticket(ctx):

    embed = discord.Embed(
        title="🎫 Valthera Destek Sistemi",
        description=(
            "Aşağıdaki seçeneklerden sana uygun olanı seçerek "
            "bir ticket oluşturabilirsin.\n\n"

            "🛡️ **Ekip Alım**\n"
            "Ekibe katılmak için ticket oluştur.\n\n"

            "🤝 **Ally**\n"
            "Ally başvuruları için ticket oluştur.\n\n"

            "🔗 **Partnerlık**\n"
            "Partnerlik başvuruları için ticket oluştur.\n\n"

            "🎫 **Genel Destek**\n"
            "Diğer tüm destek talepleri için ticket oluştur."
        ),
        color=discord.Color.blurple()
    )

    embed.set_footer(
        text="Valthera • Destek Sistemi"
    )

    await ctx.send(
        embed=embed,
        view=TicketView()
    )


# =========================================================
# PING
# =========================================================

@bot.command()
async def ping(ctx):

    await ctx.send(
        f"🏓 Pong! {round(bot.latency * 1000)}ms"
    )


# =========================================================
# ÇEKİLİŞ
# =========================================================

def parse_duration(duration):

    match = re.fullmatch(
        r"(\d+)(s|m|h|d)",
        duration.lower()
    )

    if not match:
        return None

    number = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return number

    if unit == "m":
        return number * 60

    if unit == "h":
        return number * 60 * 60

    if unit == "d":
        return number * 60 * 60 * 24

    return None


@bot.command(name="çekiliş")
@is_staff()
async def giveaway(
    ctx,
    duration: str,
    winners: int,
    *,
    prize: str
):

    seconds = parse_duration(duration)

    if seconds is None:
        await ctx.send(
            "❌ Süre yanlış!\n"
            "Örnek: `!çekiliş 10m 1 Discord Nitro`"
        )
        return

    if winners < 1:
        await ctx.send(
            "❌ Kazanan sayısı en az 1 olmalı."
        )
        return

    if winners > 50:
        await ctx.send(
            "❌ En fazla 50 kazanan olabilir."
        )
        return

    embed = discord.Embed(
        title="🎉 ÇEKİLİŞ 🎉",
        description=(
            f"🎁 **Ödül:** {prize}\n\n"
            f"🏆 **Kazanan:** {winners} kişi\n"
            f"⏰ **Süre:** {duration}\n\n"
            "Katılmak için 🎉 emojisine bas!"
        ),
        color=discord.Color.gold()
    )

    embed.set_footer(
        text=f"Başlatan: {ctx.author}"
    )

    message = await ctx.send(
        embed=embed
    )

    await message.add_reaction("🎉")

    await asyncio.sleep(seconds)

    try:

        message = await ctx.channel.fetch_message(
            message.id
        )

        reaction = discord.utils.get(
            message.reactions,
            emoji="🎉"
        )

        if reaction is None:
            await ctx.send(
                "❌ Çekilişe kimse katılmadı."
            )
            return

        users = [
            user async for user in reaction.users()
            if not user.bot
        ]

        if not users:
            await ctx.send(
                "❌ Çekilişe kimse katılmadı."
            )
            return

        selected = random.sample(
            users,
            min(winners, len(users))
        )

        mentions = " ".join(
            user.mention
            for user in selected
        )

        await ctx.send(
            f"🎉 **Çekiliş sona erdi!**\n\n"
            f"🎁 Ödül: **{prize}**\n"
            f"🏆 Kazananlar: {mentions}"
        )

    except discord.NotFound:

        await ctx.send(
            "❌ Çekiliş mesajı bulunamadı."
        )


# =========================================================
# BAN
# =========================================================

@bot.command()
@is_staff()
async def ban(
    ctx,
    member: discord.Member,
    *,
    reason="Sebep belirtilmedi."
):

    if member == ctx.author:
        await ctx.send(
            "❌ Kendini yasaklayamazsın."
        )
        return

    try:

        await member.ban(
            reason=reason
        )

        await ctx.send(
            f"🔨 **{member}** sunucudan yasaklandı.\n"
            f"📝 Sebep: {reason}"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Bu üyeyi yasaklayamıyorum."
        )


# =========================================================
# KICK
# =========================================================

@bot.command()
@is_staff()
async def kick(
    ctx,
    member: discord.Member,
    *,
    reason="Sebep belirtilmedi."
):

    if member == ctx.author:
        await ctx.send(
            "❌ Kendini atamazsın."
        )
        return

    try:

        await member.kick(
            reason=reason
        )

        await ctx.send(
            f"👢 **{member}** sunucudan atıldı.\n"
            f"📝 Sebep: {reason}"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Bu üyeyi atamıyorum."
        )


# =========================================================
# MUTE
# =========================================================

@bot.command()
@is_staff()
async def mute(
    ctx,
    member: discord.Member,
    *,
    reason="Sebep belirtilmedi."
):

    try:

        timeout = (
            discord.utils.utcnow()
            + timedelta(minutes=10)
        )

        await member.timeout(
            timeout,
            reason=reason
        )

        await ctx.send(
            f"🔇 **{member}** 10 dakika susturuldu.\n"
            f"📝 Sebep: {reason}"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Bu üyeyi susturamıyorum."
        )


# =========================================================
# WARN
# =========================================================

warnings = {}


@bot.command()
@is_staff()
async def warn(
    ctx,
    member: discord.Member,
    *,
    reason="Sebep belirtilmedi."
):

    guild_id = ctx.guild.id

    if guild_id not in warnings:
        warnings[guild_id] = {}

    if member.id not in warnings[guild_id]:
        warnings[guild_id][member.id] = []

    warnings[guild_id][member.id].append(
        reason
    )

    count = len(
        warnings[guild_id][member.id]
    )

    await ctx.send(
        f"⚠️ **{member}** uyarıldı.\n"
        f"📝 Sebep: {reason}\n"
        f"⚠️ Toplam uyarı: **{count}**"
    )


# =========================================================
# CLEAR
# =========================================================

@bot.command()
@is_staff()
async def clear(
    ctx,
    amount: int
):

    if amount < 1:
        await ctx.send(
            "❌ En az 1 mesaj silmelisin."
        )
        return

    deleted = await ctx.channel.purge(
        limit=amount + 1
    )

    msg = await ctx.send(
        f"🧹 **{len(deleted) - 1}** mesaj silindi."
    )

    await asyncio.sleep(3)

    await msg.delete()


# =========================================================
# LOCK
# =========================================================

@bot.command()
@is_staff()
async def lock(ctx):

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        send_messages=False
    )

    await ctx.send(
        "🔒 Bu kanal kilitlendi."
    )


# =========================================================
# UNLOCK
# =========================================================

@bot.command()
@is_staff()
async def unlock(ctx):

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        send_messages=None
    )

    await ctx.send(
        "🔓 Bu kanalın kilidi açıldı."
    )


# =========================================================
# HATA MESAJLARI
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CheckFailure
    ):

        await ctx.send(
            "❌ Bu komutu kullanmak için yetkin yok."
        )

    elif isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Eksik bilgi girdin. Komutu doğru kullan."
        )

    elif isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ Üye bulunamadı."
        )

    elif isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Girdiğin değerlerden biri hatalı."
        )

    elif isinstance(
        error,
        commands.CommandNotFound
    ):

        pass

    else:

        print(
            f"Hata: {error}"
        )


# =========================================================
# BOTU BAŞLAT
# =========================================================

if __name__ == "__main__":

    while True:

        try:

            print("Bot başlatılıyor...")

            
        
     
            bot.run(os.environ.get('DISCORD_TOKEN')) 

        except Exception as e:

            print(
                f"❌ Bot kapandı: {e}"
            )

            print(
                "🔄 5 saniye sonra tekrar başlatılıyor..."
            )

            time.sleep(5)