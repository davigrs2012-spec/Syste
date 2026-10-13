import os, random, asyncio, discord
from discord.ext import commands
from discord import app_commands
from collections import deque, defaultdict, Counter
from datetime import datetime, timezone, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# ================= CONFIG DA SEITA =================
TOKEN = os.getenv("TOKEN")
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_LOGS = 1559066250410197013
CANAL_ISCA = 1559066250410197013
CANAL_PESCA = 1559446593277796463
CANAL_BOT = 1559447018869358592

# CARGOS POR LEVEL
CARGOS_LEVEL = {
    1: 1559444021531770993,
    5: 1559444648101945394,
    10: 1559444288859938916,
    15: 1559444486386360320,
    20: 1559444978017505280,
}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

anti_raid_ativado = True
recent_joins = deque()
inventario_db = defaultdict(list)
carteira_db = defaultdict(int)
level_db = defaultdict(lambda: {"xp": 0, "level": 1})
warns_db = defaultdict(list)
daily_db = {}

lista_de_peixes = [
    {"nome": "Bota Velha", "emoji": "🥾", "raridade": "Lixo", "preco": 2, "xp": 1},
    {"nome": "Sardinha", "emoji": "🐟", "raridade": "Comum", "preco": 10, "xp": 5},
    {"nome": "Tilápia", "emoji": "🐟", "raridade": "Comum", "preco": 15, "xp": 8},
    {"nome": "Baiacu", "emoji": "🐡", "raridade": "Raro", "preco": 50, "xp": 20},
    {"nome": "Tubarão", "emoji": "🦈", "raridade": "Lendário", "preco": 250, "xp": 100},
    {"nome": "Peixe Dourado", "emoji": "🐠", "raridade": "Épico", "preco": 500, "xp": 200},
    {"nome": "Kraken", "emoji": "🦑", "raridade": "MÍTICO", "preco": 1500, "xp": 1000},
]

def is_adm(interaction):
    return interaction.user.guild_permissions.administrator

def add_xp(user_id, amount):
    data = level_db[user_id]
    data["xp"] += amount
    lvl_antigo = data["level"]
    data["level"] = data["xp"] // 100 + 1
    return data["level"] > lvl_antigo, data["level"]

async def dar_cargo_level(member, level):
    if not member.guild: return
    for lvl_req, cargo_id in sorted(CARGOS_LEVEL.items()):
        if level >= lvl_req:
            cargo = member.guild.get_role(cargo_id)
            if cargo and cargo not in member.roles:
                try:
                    await member.add_roles(cargo, reason=f"Level {level}")
                except: pass

def check_canal_pesca(interaction):
    if interaction.channel.id!= CANAL_PESCA:
        return False
    return True

def check_canal_bot(interaction):
    # Libera se for no canal de pesca OU no canal de bot
    if interaction.channel.id in [CANAL_PESCA, CANAL_BOT]:
        return True
    return False

@bot.event
async def on_ready():
    print(f"🔥 SUPERNOVA ON: {bot.user}")
    synced = await bot.tree.sync()
    print(f"Sync: {len(synced)} comandos")

@bot.event
async def on_member_join(member):
    canal_bv = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal_bv:
        try:
            embed = discord.Embed(title="Bem vindo a Seita!", description=f"{member.mention} entrou na Seita do CJ Vascaino!", color=0x00ff00)
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal_bv.send(embed=embed)
            cargo1 = member.guild.get_role(CARGOS_LEVEL[1])
            if cargo1:
                await member.add_roles(cargo1)
        except: pass
    if not anti_raid_ativado: return
    agora = datetime.now(timezone.utc)
    recent_joins.append(agora)
    while recent_joins and (agora - recent_joins[0]).total_seconds() > 15:
        recent_joins.popleft()
    canal_log = bot.get_channel(CANAL_LOGS)
    idade = (agora - member.created_at).days
    if idade < 7:
        try:
            await member.kick(reason=f"Conta nova {idade}d")
            if canal_log: await canal_log.send(f"🚨 KICK: {member} | {idade}d")
        except: pass
        return
    if len(recent_joins) >= 5:
        try:
            await member.ban(reason="Raid", delete_message_days=1)
            if canal_log: await canal_log.send(f"🔥 RAID: {member} BANIDO")
        except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.guild:
        upou, lvl = add_xp(message.author.id, random.randint(1,3))
        if upou:
            try:
                await dar_cargo_level(message.author, lvl)
                if lvl in CARGOS_LEVEL:
                    await message.channel.send(f"🎉 {message.author.mention} upou pro level **{lvl}** e ganhou cargo!", delete_after=15)
            except: pass
    if message.channel.id == CANAL_ISCA:
        if message.guild and message.author.guild_permissions.administrator:
            await bot.process_commands(message)
            return
        try:
            await message.delete()
            await message.guild.ban(message.author, reason="Isca", delete_message_days=1)
        except: pass
        return
    await bot.process_commands(message)

# ================= MODERAÇÃO =================
@bot.tree.command(name="antiraid", description="Controle do anti-raid")
async def antiraid(interaction: discord.Interaction, acao: str):
    if not is_adm(interaction):
        await interaction.response.send_message("Só ADM!", ephemeral=True); return
    global anti_raid_ativado
    if acao == "on": anti_raid_ativado = True; await interaction.response.send_message("✅ ANTI-RAID LIGADO", ephemeral=True)
    elif acao == "off": anti_raid_ativado = False; await interaction.response.send_message("❌ ANTI-RAID DESLIGADO", ephemeral=True)
    else: await interaction.response.send_message(f"Status: {'ON' if anti_raid_ativado else 'OFF'}", ephemeral=True)

@antiraid.autocomplete("acao")
async def ac_auto(interaction, current):
    return [app_commands.Choice(name=v, value=v) for v in ["on","off","status"] if current.lower() in v]

@bot.tree.command(name="clear", description="Apagar mensagens")
async def clear(interaction: discord.Interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"Apaguei {len(deleted)}!", ephemeral=True)

@bot.tree.command(name="ban", description="Banir usuario")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1)
    await interaction.response.send_message(f"🔨 {membro.mention} BANIDO - {motivo}")

@bot.tree.command(name="kick", description="Kikar usuario")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.kick(reason=motivo)
    await interaction.response.send_message(f"👢 {membro.mention} KIKADO - {motivo}")

@bot.tree.command(name="timeout", description="Mutar usuario por tempo")
async def timeout(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos), reason=motivo)
    await interaction.response.send_message(f"🔇 {membro.mention} mutado {minutos}min")

@bot.tree.command(name="untimeout", description="Desmutar usuario")
async def untimeout(interaction: discord.Interaction, membro: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.timeout(None)
    await interaction.response.send_message(f"🔊 {membro.mention} desmutado!")

@bot.tree.command(name="lock", description="Trancar canal")
async def lock(interaction: discord.Interaction):
    if not is_adm(interaction):
        await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Trancado!")

@bot.tree.command(name="unlock", description="Destrancar canal")
async def unlock(interaction: discord.Interaction):
    if not is_adm(interaction):
        await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Destrancado!")

@bot.tree.command(name="ping", description="Ver ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong {round(bot.latency*1000)}ms")

# ================= PESCA - SÓ NO CANAL DE PESCA =================
@bot.tree.command(name="pescar", description="Pesque um peixe - só no canal de pesca")
async def pescar(interaction: discord.Interaction):
    if not check_canal_pesca(interaction):
        canal = bot.get_channel(CANAL_PESCA)
        await interaction.response.send_message(f"🎣 Vai pescar no {canal.mention}!", ephemeral=True)
        return
    peixe = random.choices(lista_de_peixes, weights=[30,25,20,15,7,2,1], k=1)[0]
    inventario_db[interaction.user.id].append(peixe)
    carteira_db[interaction.user.id] += peixe["preco"]
    upou, lvl = add_xp(interaction.user.id, peixe["xp"])
    if upou:
        await dar_cargo_level(interaction.user, lvl)
    cor = {"Lixo": 0x808080, "Comum": 0x00ff00, "Raro": 0x0099ff, "Lendário": 0xffd700, "Épico": 0x9b59b6, "MÍTICO": 0xff0000}[peixe["raridade"]]
    embed = discord.Embed(title="🎣 Você pescou!", description=f"**{peixe['nome']}** {peixe['emoji']}\nRaridade: **{peixe['raridade']}**\nR$ {peixe['preco']} | +{peixe['xp']} XP", color=cor)
    embed.set_footer(text=f"Carteira: R$ {carteira_db[interaction.user.id]} | Level: {level_db[interaction.user.id]['level']}")
    if upou:
        embed.add_field(name="🆙 LEVEL UP!", value=f"Level {lvl}!", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventario", description="Seu inventário - só na pesca")
async def inventario(interaction: discord.Interaction):
    if not check_canal_pesca(interaction):
        canal = bot.get_channel(CANAL_PESCA)
        await interaction.response.send_message(f"Veja seu inventário no {canal.mention}!", ephemeral=True)
        return
    itens = inventario_db[interaction.user.id]
    if not itens:
        await interaction.response.send_message("Vazio! Use /pescar", ephemeral=True); return
    c = Counter([f"{p['emoji']} {p['nome']}" for p in itens])
    desc = "\n".join([f"{q}x {nome}" for nome, q in c.items()])
    embed = discord.Embed(title=f"🎒 {interaction.user.display_name}", description=desc[:4000], color=0x0099ff)
    embed.set_footer(text=f"Carteira: R$ {carteira_db[interaction.user.id]}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="carteira", description="Ver grana")
async def carteira(interaction: discord.Interaction, membro: discord.Member = None):
    if not check_canal_bot(interaction):
        canal = bot.get_channel(CANAL_BOT)
        await interaction.response.send_message(f"Use comandos no {canal.mention}!", ephemeral=True)
        return
    membro = membro or interaction.user
    await interaction.response.send_message(f"💰 {membro.mention} tem **R$ {carteira_db[membro.id]}**")

@bot.tree.command(name="top", description="Ranking")
async def top(interaction: discord.Interaction):
    if not check_canal_bot(interaction):
        canal = bot.get_channel(CANAL_BOT)
        await interaction.response.send_message(f"Veja o top no {canal.mention}!", ephemeral=True)
        return
    ranking = sorted(carteira_db.items(), key=lambda x: x[1], reverse=True)[:10]
    if not ranking:
        await interaction.response.send_message("Ninguém pescou!", ephemeral=True); return
    desc = ""
    for i, (uid, grana) in enumerate(ranking, 1):
        user = bot.get_user(uid)
        nome = user.display_name if user else f"ID {uid}"
        desc += f"**{i}.** {nome} - R$ {grana}\n"
    embed = discord.Embed(title="🏆 Top Pescadores", description=desc, color=0xffd700)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vender", description="Vender peixes - só na pesca")
async def vender(interaction: discord.Interaction):
    if not check_canal_pesca(interaction):
        canal = bot.get_channel(CANAL_PESCA)
        await interaction.response.send_message(f"Vende no {canal.mention}!", ephemeral=True)
        return
    itens = inventario_db[interaction.user.id]
    if not itens:
        await interaction.response.send_message("Nada pra vender!", ephemeral=True); return
    total = sum(p["preco"] for p in itens)
    carteira_db[interaction.user.id] += total
    inventario_db[interaction.user.id].clear()
    await interaction.response.send_message(f"💸 Vendeu {len(itens)} por R$ {total}!")

@bot.tree.command(name="daily", description="Resgate diário - só na pesca")
async def daily(interaction: discord.Interaction):
    if not check_canal_pesca(interaction):
        canal = bot.get_channel(CANAL_PESCA)
        await interaction.response.send_message(f"Pega daily no {canal.mention}!", ephemeral=True)
        return
    agora = datetime.now(timezone.utc)
    ultimo = daily_db.get(interaction.user.id)
    if ultimo and (agora - ultimo).total_seconds() < 86400:
        horas = int((86400 - (agora - ultimo).total_seconds()) // 3600)
        await interaction.response.send_message(f"Já pegou! Volta em {horas}h", ephemeral=True); return
    daily_db[interaction.user.id] = agora
    premio = random.randint(50, 150)
    carteira_db[interaction.user.id] += premio
    await interaction.response.send_message(f"🎁 +R$ {premio}!")

@bot.tree.command(name="rank", description="Seu level")
async def rank(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    data = level_db[membro.id]
    embed = discord.Embed(title=f"Level de {membro.display_name}", description=f"Level **{data['level']}**\nXP: {data['xp']} / {data['level']*100}", color=0x9b59b6)
    embed.set_thumbnail(url=membro.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="8ball", description="Bola mágica - só no bot")
async def eightball(interaction: discord.Interaction, pergunta: str):
    if not check_canal_bot(interaction):
        canal = bot.get_channel(CANAL_BOT)
        await interaction.response.send_message(f"Usa no {canal.mention}!", ephemeral=True)
        return
    respostas = ["Sim", "Não", "Talvez", "Com certeza", "Nem ferrando", "Pergunta pro CJ", "Vasco", "É bait"]
    await interaction.response.send_message(f"🎱 {pergunta}\n**{random.choice(respostas)}**")

@bot.tree.command(name="coinflip", description="Cara ou coroa - só no bot")
async def coinflip(interaction: discord.Interaction):
    if not check_canal_bot(interaction):
        canal = bot.get_channel(CANAL_BOT)
        await interaction.response.send_message(f"Usa no {canal.mention}!", ephemeral=True)
        return
    await interaction.response.send_message(f"🪙 **{random.choice(['Cara','Coroa'])}**")

@bot.tree.command(name="roll", description="Rolar dado - só no bot")
async def roll(interaction: discord.Interaction, lados: int = 6):
    if not check_canal_bot(interaction):
        canal = bot.get_channel(CANAL_BOT)
        await interaction.response.send_message(f"Usa no {canal.mention}!", ephemeral=True)
        return
    await interaction.response.send_message(f"🎲 d{lados}: **{random.randint(1,lados)}**")

@bot.tree.command(name="ajuda", description="Todos os comandos")
async def ajuda(interaction: discord.Interaction):
    canal_pesca = bot.get_channel(CANAL_PESCA)
    canal_bot = bot.get_channel(CANAL_BOT)
    embed = discord.Embed(title="💥 SUPERNOVA - SEITA DO CJ", color=0xff0000)
    embed.add_field(name=f"🎣 Pesca - Só no {canal_pesca.name if canal_pesca else 'pesca'}", value="`/pescar` `/inventario` `/vender` `/daily`", inline=False)
    embed.add_field(name=f"🤖 Bot - Só no {canal_bot.name if canal_bot else 'bot'}", value="`/carteira` `/top` `/8ball` `/coinflip` `/roll` `/rank`", inline=False)
    embed.add_field(name="🛡️ ADM", value="`/ban` `/kick` `/timeout` `/clear` `/antiraid` `/lock` `/unlock`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="All commands")
async def help_en(interaction: discord.Interaction):
    await ajuda.callback(interaction)

@bot.command(name="cj")
async def cj(ctx):
    await ctx.send(f"{ctx.author.mention} Para de me marcar big smoke~kun")

bot.run(TOKEN)
