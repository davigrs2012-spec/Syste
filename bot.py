import os, random, asyncio, discord, aiohttp
from discord.ext import commands
from discord import app_commands
from collections import deque, defaultdict, Counter
from datetime import datetime, timezone, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

TOKEN = os.getenv("TOKEN")
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_LOGS = 1559066250410197013
CANAL_ISCA = 1559066250410197013
CANAL_PESCA = 1559446593277796463
CANAL_BOT = 1559447018869358592

CARGOS_LEVEL = {
    1: 1559444021531770993,
    5: 1559444648101945394,
    10: 1559444288859938916,
    15: 1559444486386360320,
    20: 1559444978017505280,
}

BOTS_RESTRITOS = [208583444938057728, 235148962103951360] # Loritta e Carl pra deletar fora do #comandos

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
rep_db = defaultdict(int)
marry_db = {}

lista_de_peixes = [
    {"nome": "Bota Velha", "emoji": "🥾", "raridade": "Lixo", "preco": 2, "xp": 1},
    {"nome": "Sardinha", "emoji": "🐟", "raridade": "Comum", "preco": 10, "xp": 5},
    {"nome": "Tilápia", "emoji": "🐟", "raridade": "Comum", "preco": 15, "xp": 8},
    {"nome": "Baiacu", "emoji": "🐡", "raridade": "Raro", "preco": 50, "xp": 20},
    {"nome": "Tubarão", "emoji": "🦈", "raridade": "Lendário", "preco": 250, "xp": 100},
    {"nome": "Peixe Dourado", "emoji": "🐠", "raridade": "Épico", "preco": 500, "xp": 200},
    {"nome": "Kraken", "emoji": "🦑", "raridade": "MÍTICO", "preco": 1500, "xp": 1000},
]

# GIFS - CLONE DA LORITTA
GIFS = {
    "kiss": ["https://i.pinimg.com/originals/4d/7d/fd/4d7dfdc48c80e8dcfcf06c5307c11fa.gif", "https://media.tenor.com/0p7a5T3b6TAAAAAC/kiss-anime.gif"],
    "hug": ["https://media.tenor.com/kCZj6Xh2aSsAAAAC/anime-hug.gif", "https://media.tenor.com/Cy7R1FMwQyQAAAAC/hug-anime.gif"],
    "slap": ["https://media.tenor.com/Uw1P5v2oD0QAAAAC/anime-slap.gif", "https://media.tenor.com/6B1m0a5t0b0AAAAC/slap-anime.gif"],
    "pat": ["https://media.tenor.com/1R1Q3z3Q3QAAAAC/pat-anime.gif", "https://media.tenor.com/XWQy7Z9v4a0AAAAC/pat-head.gif"],
    "cuddle": ["https://media.tenor.com/7a0a0a0a0a0AAAAC/cuddle-anime.gif"],
}

def is_adm(i): return i.user.guild_permissions.administrator
def check_pesca(i): return i.channel.id == CANAL_PESCA
def check_bot(i): return i.channel.id in [CANAL_PESCA, CANAL_BOT]

def add_xp(uid, amt):
    data = level_db[uid]
    data["xp"] += amt
    old = data["level"]
    data["level"] = data["xp"] // 100 + 1
    return data["level"] > old, data["level"]

async def dar_cargo_level(member, level):
    if not member.guild: return
    for lvl_req, cargo_id in sorted(CARGOS_LEVEL.items()):
        if level >= lvl_req:
            cargo = member.guild.get_role(cargo_id)
            if cargo and cargo not in member.roles:
                try: await member.add_roles(cargo, reason=f"Level {level}")
                except: pass

@bot.event
async def on_ready():
    print(f"🔥 SUPERNOVA LORITTA KILLER ON: {bot.user}")
    synced = await bot.tree.sync()
    print(f"Sync {len(synced)} comandos")

@bot.event
async def on_member_join(member):
    canal_bv = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal_bv:
        try:
            embed = discord.Embed(title="Bem vindo a Seita!", description=f"{member.mention} entrou na Seita do CJ Vascaino!", color=0x00ff00)
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal_bv.send(embed=embed)
            cargo1 = member.guild.get_role(CARGOS_LEVEL[1])
            if cargo1: await member.add_roles(cargo1)
        except: pass
    if not anti_raid_ativado: return
    agora = datetime.now(timezone.utc)
    recent_joins.append(agora)
    while recent_joins and (agora - recent_joins[0]).total_seconds() > 15: recent_joins.popleft()
    canal_log = bot.get_channel(CANAL_LOGS)
    idade = (agora - member.created_at).days
    if idade < 7:
        try: await member.kick(reason=f"Conta nova {idade}d");
            if canal_log: await canal_log.send(f"🚨 KICK: {member} | {idade}d")
        except: pass
        return
    if len(recent_joins) >= 5:
        try: await member.ban(reason="Raid", delete_message_days=1);
            if canal_log: await canal_log.send(f"🔥 RAID: {member} BANIDO")
        except: pass

@bot.event
async def on_message(message):
    # ANTI-LORITTA: Apaga Loritta e Carl fora do #comandos
    if message.author.id in BOTS_RESTRITOS:
        if message.channel.id!= CANAL_BOT:
            try: await message.delete()
            except: pass
            return
    if message.author.bot: return
    if message.guild:
        upou, lvl = add_xp(message.author.id, random.randint(1,3))
        if upou: await dar_cargo_level(message.author, lvl)
    if message.channel.id == CANAL_ISCA:
        if message.guild and message.author.guild_permissions.administrator:
            await bot.process_commands(message); return
        try: await message.delete(); await message.guild.ban(message.author, reason="Isca", delete_message_days=1)
        except: pass
        return
    await bot.process_commands(message)

# ============ MODERAÇÃO ============
@bot.tree.command(name="antiraid", description="Controle anti-raid")
async def antiraid(interaction: discord.Interaction, acao: str):
    if not is_adm(interaction): await interaction.response.send_message("Só ADM!", ephemeral=True); return
    global anti_raid_ativado
    if acao == "on": anti_raid_ativado = True; await interaction.response.send_message("✅ LIGADO", ephemeral=True)
    elif acao == "off": anti_raid_ativado = False; await interaction.response.send_message("❌ DESLIGADO", ephemeral=True)
    else: await interaction.response.send_message(f"Status: {'ON' if anti_raid_ativado else 'OFF'}", ephemeral=True)
@antiraid.autocomplete("acao")
async def ac_auto(interaction, current): return [app_commands.Choice(name=v, value=v) for v in ["on","off","status"] if current.lower() in v]
@bot.tree.command(name="clear", description="Apagar mensagens")
async def clear(interaction: discord.Interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages: await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True); deleted = await interaction.channel.purge(limit=quantidade); await interaction.followup.send(f"Apaguei {len(deleted)}!", ephemeral=True)
@bot.tree.command(name="ban", description="Banir")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"🔨 {membro.mention} BANIDO - {motivo}")
@bot.tree.command(name="kick", description="Kikar")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members: await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.kick(reason=motivo); await interaction.response.send_message(f"👢 {membro.mention} KIKADO")
@bot.tree.command(name="timeout", description="Mutar")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.moderate_members: await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos), reason=motivo); await interaction.response.send_message(f"🔇 {membro.mention} {minutos}min")
@bot.tree.command(name="untimeout", description="Desmutar")
async def untimeout(interaction: discord.Interaction, membro: discord.Member):
    if not interaction.user.guild_permissions.moderate_members: await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.timeout(None); await interaction.response.send_message(f"🔊 {membro.mention} desmutado!")
@bot.tree.command(name="lock", description="Trancar canal")
async def lock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message("🔒 Trancado!")
@bot.tree.command(name="unlock", description="Destrancar")
async def unlock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message("🔓 Destrancado!")
@bot.tree.command(name="warn", description="Avisar usuário")
async def warn(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not interaction.user.guild_permissions.moderate_members: await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    warns_db[membro.id].append(motivo); await interaction.response.send_message(f"⚠️ {membro.mention} avisado: {motivo} | Total warns: {len(warns_db[membro.id])}")

# ============ CLONE LORITTA - SOCIAL ============
async def social_cmd(interaction, membro, tipo, verbo):
    if not check_bot(interaction):
        canal = bot.get_channel(CANAL_BOT); await interaction.response.send_message(f"Usa no {canal.mention}!", ephemeral=True); return
    if membro.id == interaction.user.id:
        await interaction.response.send_message("Tu não pode fazer isso em você mesmo, doido!", ephemeral=True); return
    gif = random.choice(GIFS.get(tipo, GIFS["hug"]))
    embed = discord.Embed(description=f"**{interaction.user.mention} {verbo} {membro.mention}!**", color=0xff69b4)
    embed.set_image(url=gif)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="beijar", description="Beijar alguém - igual Loritta +kiss")
async def beijar(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "kiss", "beijou")
@bot.tree.command(name="abracar", description="Abraçar alguém - igual +hug")
async def abracar(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "hug", "abraçou")
@bot.tree.command(name="tapa", description="Dar tapa - igual +slap")
async def tapa(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "slap", "deu um tapa em")
@bot.tree.command(name="cafune", description="Fazer cafuné")
async def cafune(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "pat", "fez cafuné em")
@bot.tree.command(name="cuddle", description="Aconchegar")
async def cuddle(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "cuddle", "aconchegou")

@bot.tree.command(name="ship", description="Shippar 2 pessoas - igual Loritta")
async def ship(interaction: discord.Interaction, pessoa1: discord.Member, pessoa2: discord.Member = None):
    if not check_bot(interaction):
        canal = bot.get_channel(CANAL_BOT); await interaction.response.send_message(f"Usa no {canal.mention}!", ephemeral=True); return
    pessoa2 = pessoa2 or interaction.user
    perc = random.randint(0,100)
    barra = "█" * (perc//10) + "░" * (10 - perc//10)
    embed = discord.Embed(title="💘 SHIP", description=f"{pessoa1.mention} + {pessoa2.mention}\n{barra} {perc}%\n" + ("💖 ALMAS GÊMEAS!" if perc>80 else "💔 Melhor não..." if perc<30 else "💕 Tem chance!"), color=0xff00ff)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rep", description="Dar rep - igual Loritta")
async def rep(interaction: discord.Interaction, membro: discord.Member):
    if not check_bot(interaction): return
    rep_db[membro.id] += 1
    await interaction.response.send_message(f"⭐ {interaction.user.mention} deu rep para {membro.mention}! Agora tem {rep_db[membro.id]} reps!")

@bot.tree.command(name="avatar", description="Ver avatar - /user avatar da Loritta")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"Avatar de {membro.display_name}", color=0x00ffff)
    embed.set_image(url=membro.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="Info do usuário - /user info da Loritta")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"Info de {membro.display_name}", color=0x0099ff)
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="ID", value=membro.id)
    embed.add_field(name="Entrou em", value=membro.joined_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Conta criada", value=membro.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Level", value=level_db[membro.id]["level"])
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Info do server - /server info")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=g.name, color=0x00ff00)
    if g.icon: embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="Membros", value=g.member_count)
    embed.add_field(name="Criado em", value=g.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Canais", value=len(g.channels))
    await interaction.response.send_message(embed=embed)

# ============ ECONOMIA LORITTA ============
@bot.tree.command(name="pescar", description="Pescar - só no canal de pesca")
async def pescar(interaction: discord.Interaction):
    if not check_pesca(interaction):
        canal = bot.get_channel(CANAL_PESCA); await interaction.response.send_message(f"🎣 Vai no {canal.mention}!", ephemeral=True); return
    peixe = random.choices(lista_de_peixes, weights=[30,25,20,15,7,2,1], k=1)[0]
    inventario_db[interaction.user.id].append(peixe); carteira_db[interaction.user.id] += peixe["preco"]
    upou, lvl = add_xp(interaction.user.id, peixe["xp"]);
    if upou: await dar_cargo_level(interaction.user, lvl)
    cor = {"Lixo": 0x808080, "Comum": 0x00ff00, "Raro": 0x0099ff, "Lendário": 0xffd700, "Épico": 0x9b59b6, "MÍTICO": 0xff0000}[peixe["raridade"]]
    embed = discord.Embed(title="🎣 Você pescou!", description=f"**{peixe['nome']}** {peixe['emoji']}\nRaridade: **{peixe['raridade']}**\nR$ {peixe['preco']} | +{peixe['xp']} XP", color=cor)
    if upou: embed.add_field(name="🆙 LEVEL UP!", value=f"Level {lvl}!", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventario", description="Inventário")
async def inventario(interaction: discord.Interaction):
    if not check_pesca(interaction): await interaction.response.send_message(f"Vai no <#{CANAL_PESCA}>!", ephemeral=True); return
    itens = inventario_db[interaction.user.id]
    if not itens: await interaction.response.send_message("Vazio! /pescar", ephemeral=True); return
    c = Counter([f"{p['emoji']} {p['nome']}" for p in itens]); desc = "\n".join([f"{q}x {nome}" for nome, q in c.items()])
    embed = discord.Embed(title=f"🎒 {interaction.user.display_name}", description=desc[:4000], color=0x0099ff)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="carteira", description="Ver grana - igual /sonhos atm")
async def carteira(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    await interaction.response.send_message(f"💰 {membro.mention} tem **R$ {carteira_db[membro.id]}** e {rep_db[membro.id]} reps")

@bot.tree.command(name="top", description="Ranking - igual /sonhos rank")
async def top(interaction: discord.Interaction):
    ranking = sorted(carteira_db.items(), key=lambda x: x[1], reverse=True)[:10]
    if not ranking: await interaction.response.send_message("Ninguém pescou!", ephemeral=True); return
    desc = ""
    for i, (uid, grana) in enumerate(ranking, 1):
        user = bot.get_user(uid); nome = user.display_name if user else f"ID {uid}"; desc += f"**{i}.** {nome} - R$ {grana}\n"
    await interaction.response.send_message(embed=discord.Embed(title="🏆 Top Ricos", description=desc, color=0xffd700))

@bot.tree.command(name="daily", description="Resgate diário")
async def daily(interaction: discord.Interaction):
    agora = datetime.now(timezone.utc); ultimo = daily_db.get(interaction.user.id)
    if ultimo and (agora - ultimo).total_seconds() < 86400:
        horas = int((86400 - (agora - ultimo).total_seconds()) // 3600); await interaction.response.send_message(f"Já pegou! Volta em {horas}h", ephemeral=True); return
    daily_db[interaction.user.id] = agora; premio = random.randint(50,150); carteira_db[interaction.user.id] += premio
    await interaction.response.send_message(f"🎁 +R$ {premio}!")

@bot.tree.command(name="pay", description="Pagar alguém - igual /sonhos pagar")
async def pay(interaction: discord.Interaction, membro: discord.Member, quantia: int):
    if quantia <=0: await interaction.response.send_message("Valor inválido!", ephemeral=True); return
    if carteira_db[interaction.user.id] < quantia: await interaction.response.send_message("Sem grana!", ephemeral=True); return
    carteira_db[interaction.user.id] -= quantia; carteira_db[membro.id] += quantia
    await interaction.response.send_message(f"💸 {interaction.user.mention} pagou R$ {quantia} para {membro.mention}!")

@bot.tree.command(name="rank", description="Seu level")
async def rank(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user; data = level_db[membro.id]
    embed = discord.Embed(title=f"Level de {membro.display_name}", description=f"Level **{data['level']}**\nXP: {data['xp']} / {data['level']*100}", color=0x9b59b6)
    embed.set_thumbnail(url=membro.display_avatar.url); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="8ball", description="Bola mágica")
async def eightball(interaction: discord.Interaction, pergunta: str):
    respostas = ["Sim", "Não", "Talvez", "Com certeza", "Nem ferrando", "Pergunta pro CJ", "Vasco", "É bait"]; await interaction.response.send_message(f"🎱 {pergunta}\n**{random.choice(respostas)}**")
@bot.tree.command(name="coinflip", description="Cara ou coroa")
async def coinflip(interaction: discord.Interaction): await interaction.response.send_message(f"🪙 **{random.choice(['Cara','Coroa'])}**")
@bot.tree.command(name="roll", description="Rolar dado")
async def roll(interaction: discord.Interaction, lados: int = 6): await interaction.response.send_message(f"🎲 d{lados}: **{random.randint(1,lados)}**")
@bot.tree.command(name="ping", description="Ping")
async def ping(interaction: discord.Interaction): await interaction.response.send_message(f"Pong {round(bot.latency*1000)}ms")

@bot.tree.command(name="ajuda", description="Todos os comandos - Loritta Killer")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="💥 SUPERNOVA - LORITTA KILLER", description="Todos os comandos da Loritta agora são meus!", color=0xff0000)
    embed.add_field(name="💋 Social (igual Loritta)", value="`/beijar` `/abracar` `/tapa` `/cafune` `/cuddle` `/ship` `/rep`", inline=False)
    embed.add_field(name="👤 Discord Info (igual Loritta)", value="`/avatar` `/userinfo` `/serverinfo`", inline=False)
    embed.add_field(name="🎣 Pesca/Economia (igual sonhos)", value="`/pescar` `/inventario` `/carteira` `/top` `/daily` `/pay` `/rank`", inline=False)
    embed.add_field(name="🎲 Diversão", value="`/8ball` `/coinflip` `/roll` `/ping`", inline=False)
    embed.add_field(name="🛡️ ADM", value="`/ban` `/kick` `/timeout` `/warn` `/clear` `/antiraid` `/lock`", inline=False)
    embed.set_footer(text="Loritta e Carl só falam no #comandos, resto eu apago!")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="cj")
async def cj(ctx): await ctx.send(f"{ctx.author.mention} Para de me marcar big smoke~kun")

bot.run(TOKEN)
