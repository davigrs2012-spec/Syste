import os, random, asyncio, discord, json, re
from discord.ext import commands
from discord import app_commands
from collections import deque, defaultdict, Counter
from datetime import datetime, timezone, timedelta
import math

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
CARGOS_LEVEL = {1: 1559444021531770993, 5: 1559444648101945394, 10: 1559444288859938916, 15: 1559444486386360320, 20: 1559444978017505280}
BOTS_RESTRITOS = [208583444938057728, 235148962103951360]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix=["!", "cj!"], intents=intents, help_command=None)

inventario_db = defaultdict(list)
carteira_db = defaultdict(int)
banco_db = defaultdict(int)
level_db = defaultdict(lambda: {"xp": 0, "level": 1, "messages": 0})
warns_db = defaultdict(list)
daily_db = {}
work_db = {}
rep_db = defaultdict(int)
rep_cooldown = {}
marry_db = {}
afk_db = {}
anti_raid_ativado = True
recent_joins = deque()
auto_role = None
links_bloqueados = False

lista_de_peixes = [
    {"nome": "Bota Velha", "emoji": "🥾", "raridade": "Lixo", "preco": 2, "xp": 1},
    {"nome": "Sardinha", "emoji": "🐟", "raridade": "Comum", "preco": 10, "xp": 5},
    {"nome": "Baiacu", "emoji": "🐡", "raridade": "Raro", "preco": 50, "xp": 20},
    {"nome": "Tubarao", "emoji": "🦈", "raridade": "Lendario", "preco": 250, "xp": 100},
    {"nome": "Peixe Dourado", "emoji": "🐠", "raridade": "Epico", "preco": 500, "xp": 200},
    {"nome": "Kraken", "emoji": "🦑", "raridade": "MITICO", "preco": 1500, "xp": 1000},
]

GIFS = {
    "kiss": ["https://media.tenor.com/F02Ep3U2j0kAAAAC/anime-kiss.gif"],
    "hug": ["https://media.tenor.com/kCZj6Xh2aSsAAAAC/anime-hug.gif"],
    "slap": ["https://media.tenor.com/Uw1P5v2oD0QAAAAC/anime-slap.gif"],
    "pat": ["https://media.tenor.com/2uyENRuvV-0AAAAC/anime-head-pat.gif"],
    "punch": ["https://media.tenor.com/sV_My3vGgnYAAAAC/anime-punch.gif"],
    "dance": ["https://media.tenor.com/2uyENRuvV-0AAAAC/anime-dance.gif"],
}

def is_adm(i): return i.user.guild_permissions.administrator
def check_pesca(i): return i.channel.id == CANAL_PESCA
def check_bot(i): return i.channel.id in [CANAL_PESCA, CANAL_BOT]
def add_xp(uid, amt):
    data = level_db[uid]
    data["xp"] += amt
    data["messages"] += 1
    old = data["level"]
    new_level = int(math.sqrt(data["xp"] / 10)) + 1
    data["level"] = new_level
    return new_level > old, new_level

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
    print(f"SUPERNOVA CJ V3 ON: {bot.user} - FAZ TUDO")
    synced = await bot.tree.sync()
    print(f"Sync {len(synced)} comandos")

@bot.event
async def on_member_join(member):
    canal_bv = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal_bv:
        try:
            embed = discord.Embed(title="BEM VINDO A SEITA DO CJ!", description=f"{member.mention} entrou! Somos {member.guild.member_count} malucos! Vai em <#{CANAL_BOT}>!", color=0x00ff00)
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal_bv.send(embed=embed)
            cargo1 = member.guild.get_role(CARGOS_LEVEL[1])
            if cargo1: await member.add_roles(cargo1)
        except: pass
    if not anti_raid_ativado: return
    agora = datetime.now(timezone.utc)
    recent_joins.append(agora)
    while recent_joins and (agora - recent_joins[0]).total_seconds() > 15: recent_joins.popleft()
    idade = (agora - member.created_at).days
    if idade < 7:
        try: await member.kick(reason=f"Conta nova {idade}d")
        except: pass
        return
    if len(recent_joins) >= 5:
        try: await member.ban(reason="Raid", delete_message_days=1)
        except: pass

@bot.event
async def on_message(message):
    if message.author.bot:
        if message.author.id in BOTS_RESTRITOS:
            if message.channel.id!= CANAL_BOT:
                try: await message.delete()
                except: pass
        return
    if message.author.id in afk_db:
        del afk_db[message.author.id]
        try: await message.channel.send(f"Bem vindo de volta {message.author.mention}!", delete_after=5)
        except: pass
    for mention in message.mentions:
        if mention.id in afk_db:
            motivo, tempo = afk_db[mention.id]
            try: await message.reply(f"{mention.display_name} ta AFK: {motivo}", delete_after=10)
            except: pass
    if message.guild and not message.author.bot:
        upou, lvl = add_xp(message.author.id, random.randint(2,5))
        if upou: await dar_cargo_level(message.author, lvl)
    if message.channel.id == CANAL_ISCA:
        if message.guild and message.author.guild_permissions.administrator:
            await bot.process_commands(message); return
        try: await message.delete(); await message.guild.ban(message.author, reason="Isca", delete_message_days=1)
        except: pass
        return
    if links_bloqueados and message.guild and not message.author.guild_permissions.manage_messages:
        if re.search(r"https?://|discord.gg", message.content):
            try: await message.delete(); return
            except: pass
    await bot.process_commands(message)

# MODERACAO
@bot.tree.command(name="clear", description="Limpar mensagens")
async def clear(interaction: discord.Interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages: await interaction.response.send_message("Sem permissao!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True); deleted = await interaction.channel.purge(limit=quantidade); await interaction.followup.send(f"Apaguei {len(deleted)}!", ephemeral=True)
@bot.tree.command(name="ban", description="Banir")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("Sem permissao!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"{membro.mention} BANIDO - {motivo}")
@bot.tree.command(name="kick", description="Kikar")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members: await interaction.response.send_message("Sem permissao!", ephemeral=True); return
    await membro.kick(reason=motivo); await interaction.response.send_message(f"{membro.mention} KIKADO")
@bot.tree.command(name="timeout", description="Mutar")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.moderate_members: await interaction.response.send_message("Sem permissao!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos), reason=motivo); await interaction.response.send_message(f"{membro.mention} mutado {minutos}min")
@bot.tree.command(name="untimeout", description="Desmutar")
async def untimeout(interaction: discord.Interaction, membro: discord.Member):
    if not interaction.user.guild_permissions.moderate_members: await interaction.response.send_message("Sem permissao!", ephemeral=True); return
    await membro.timeout(None); await interaction.response.send_message(f"{membro.mention} desmutado!")
@bot.tree.command(name="warn", description="Dar warn")
async def warn(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not interaction.user.guild_permissions.moderate_members: await interaction.response.send_message("Sem permissao!", ephemeral=True); return
    warns_db[membro.id].append(motivo); total = len(warns_db[membro.id]); await interaction.response.send_message(f"{membro.mention} warn {total}/3: {motivo}")
    if total >= 3:
        try: await membro.ban(reason="3 warns", delete_message_days=1); await interaction.followup.send(f"{membro.mention} banido por 3 warns!")
        except: pass
@bot.tree.command(name="lock", description="Trancar canal")
async def lock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message("Trancado!")
@bot.tree.command(name="unlock", description="Destrancar")
async def unlock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message("Destrancado!")
@bot.tree.command(name="poll", description="Enquete")
async def poll(interaction: discord.Interaction, pergunta: str, opcao1: str, opcao2: str):
    embed = discord.Embed(title=f"Enquete: {pergunta}", description=f"1️⃣ {opcao1}\n2️⃣ {opcao2}", color=0x00ffff); await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response(); await msg.add_reaction("1️⃣"); await msg.add_reaction("2️⃣")

# SOCIAL CLONE LORITTA
async def social_cmd(interaction, membro, tipo, verbo):
    if not check_bot(interaction): canal = bot.get_channel(CANAL_BOT); await interaction.response.send_message(f"Usa no {canal.mention}!", ephemeral=True); return
    if membro.id == interaction.user.id: await interaction.response.send_message("Nao pode em voce mesmo!", ephemeral=True); return
    gif = random.choice(GIFS.get(tipo, GIFS["hug"])); embed = discord.Embed(description=f"**{interaction.user.mention} {verbo} {membro.mention}!**", color=0xff69b4); embed.set_image(url=gif); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="beijar", description="Beijar - clone Loritta")
async def beijar(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "kiss", "beijou")
@bot.tree.command(name="abracar", description="Abracar")
async def abracar(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "hug", "abracou")
@bot.tree.command(name="tapa", description="Tapa")
async def tapa(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "slap", "deu tapa em")
@bot.tree.command(name="cafune", description="Cafune")
async def cafune(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "pat", "fez cafune em")
@bot.tree.command(name="soco", description="Soco")
async def soco(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "punch", "deu socao em")
@bot.tree.command(name="dancar", description="Dancar")
async def dancar(interaction: discord.Interaction, membro: discord.Member): await social_cmd(interaction, membro, "dance", "dancou com")

@bot.tree.command(name="ship", description="Shippar")
async def ship(interaction: discord.Interaction, pessoa1: discord.Member, pessoa2: discord.Member = None):
    pessoa2 = pessoa2 or interaction.user; perc = random.randint(0,100); barra = "█" * (perc//10) + "░" * (10 - perc//10)
    embed = discord.Embed(title="💘 SHIP", description=f"{pessoa1.mention} + {pessoa2.mention}\n{barra} {perc}%", color=0xff00ff); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="casar", description="Casar")
async def casar(interaction: discord.Interaction, membro: discord.Member):
    marry_db[interaction.user.id] = membro.id; marry_db[membro.id] = interaction.user.id; await interaction.response.send_message(f"💒 {interaction.user.mention} e {membro.mention} casaram!")
@bot.tree.command(name="divorciar", description="Divorciar")
async def divorciar(interaction: discord.Interaction):
    if interaction.user.id not in marry_db: await interaction.response.send_message("Nem ta casado!", ephemeral=True); return
    conj = marry_db[interaction.user.id]; del marry_db[interaction.user.id];
    if conj in marry_db: del marry_db[conj]
    await interaction.response.send_message("Divorciou!")

@bot.tree.command(name="rep", description="Dar rep - Loritta")
async def rep(interaction: discord.Interaction, membro: discord.Member):
    agora = datetime.now(timezone.utc); ultimo = rep_cooldown.get(interaction.user.id)
    if ultimo and (agora - ultimo).total_seconds() < 3600: await interaction.response.send_message("Espera 1h!", ephemeral=True); return
    rep_cooldown[interaction.user.id] = agora; rep_db[membro.id] += 1; await interaction.response.send_message(f"⭐ {interaction.user.mention} deu rep pra {membro.mention}! Total {rep_db[membro.id]}")

@bot.tree.command(name="afk", description="Ficar AFK - Loritta")
async def afk(interaction: discord.Interaction, motivo: str = "AFK"):
    afk_db[interaction.user.id] = (motivo, datetime.now(timezone.utc)); await interaction.response.send_message(f"{interaction.user.mention} AFK: {motivo}")

# ECONOMIA
@bot.tree.command(name="pescar", description="Pescar - pesca")
async def pescar(interaction: discord.Interaction):
    if not check_pesca(interaction): canal = bot.get_channel(CANAL_PESCA); await interaction.response.send_message(f"Pesca so no {canal.mention}!", ephemeral=True); return
    peixe = random.choices(lista_de_peixes, weights=[30,25,15,10,5,1], k=1)[0]; inventario_db[interaction.user.id].append(peixe); carteira_db[interaction.user.id] += peixe["preco"]
    embed = discord.Embed(title="🎣 Pescou!", description=f"{peixe['nome']} R$ {peixe['preco']}", color=0x00ff00); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="carteira", description="Ver grana - atm")
async def carteira(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user; await interaction.response.send_message(f"💰 {membro.mention} tem R$ {carteira_db[membro.id]} e {rep_db[membro.id]} reps")

@bot.tree.command(name="daily", description="Daily - Loritta")
async def daily(interaction: discord.Interaction):
    agora = datetime.now(timezone.utc); ultimo = daily_db.get(interaction.user.id)
    if ultimo and (agora - ultimo).total_seconds() < 86400: await interaction.response.send_message("Ja pegou daily!", ephemeral=True); return
    daily_db[interaction.user.id] = agora; premio = random.randint(100,300); carteira_db[interaction.user.id] += premio; await interaction.response.send_message(f"🎁 +R$ {premio}!")

@bot.tree.command(name="pay", description="Pagar - sonhos pagar")
async def pay(interaction: discord.Interaction, membro: discord.Member, quantia: int):
    if carteira_db[interaction.user.id] < quantia: await interaction.response.send_message("Sem grana!", ephemeral=True); return
    carteira_db[interaction.user.id] -= quantia; carteira_db[membro.id] += quantia; await interaction.response.send_message(f"{interaction.user.mention} pagou R$ {quantia} pra {membro.mention}!")

@bot.tree.command(name="top", description="Top ricos - rank")
async def top(interaction: discord.Interaction):
    ranking = sorted(carteira_db.items(), key=lambda x: x[1], reverse=True)[:10]; desc = "\n".join([f"{i+1}. <@{uid}> - R$ {grana}" for i, (uid, grana) in enumerate(ranking)])
    await interaction.response.send_message(embed=discord.Embed(title="🏆 Top Ricos", description=desc, color=0xffd700))

@bot.tree.command(name="slots", description="Caca niquel - Loritta")
async def slots(interaction: discord.Interaction, aposta: int):
    if carteira_db[interaction.user.id] < aposta: await interaction.response.send_message("Sem grana!", ephemeral=True); return
    emojis = ["🍒","🍋","🍊","🍇","💎","7️⃣"]; r = [random.choice(emojis) for _ in range(3)]; resultado = " | ".join(r)
    if r[0]==r[1]==r[2]: premio = aposta*5; carteira_db[interaction.user.id] += premio; await interaction.response.send_message(f"{resultado}\nJACKPOT! +R$ {premio}!")
    else: carteira_db[interaction.user.id] -= aposta; await interaction.response.send_message(f"{resultado}\nPerdeu R$ {aposta}!")

# UTILS
@bot.tree.command(name="avatar", description="Avatar - Loritta")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user; embed = discord.Embed(title=f"Avatar {membro.display_name}"); embed.set_image(url=membro.display_avatar.url); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="Userinfo - Loritta")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user; embed = discord.Embed(title=f"Info {membro.display_name}"); embed.add_field(name="ID", value=membro.id); embed.add_field(name="Level", value=level_db[membro.id]["level"]); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Serverinfo - Loritta")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild; embed = discord.Embed(title=g.name); embed.add_field(name="Membros", value=g.member_count); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rank", description="Rank level")
async def rank(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user; data = level_db[membro.id]; embed = discord.Embed(title=f"Level {membro.display_name}", description=f"Level {data['level']} XP {data['xp']}"); await interaction.response.send_message(embed=embed)

@bot.tree.command(name="8ball", description="Bola 8")
async def eightball(interaction: discord.Interaction, pergunta: str):
    respostas = ["Sim", "Nao", "Talvez", "Com certeza", "Vasco"]; await interaction.response.send_message(f"{pergunta} = {random.choice(respostas)}")

@bot.tree.command(name="ping", description="Ping")
async def ping(interaction: discord.Interaction): await interaction.response.send_message(f"Pong {round(bot.latency*1000)}ms")

@bot.tree.command(name="ajuda", description="Ajuda FAZ TUDO")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 CJ FAZ TUDO V3 - TCHAU LORITTA!", description="Pode banir a Loritta agora!", color=0xff0000)
    embed.add_field(name="💋 Social", value="/beijar /abracar /tapa /cafune /soco /dancar /ship /casar /divorciar /rep /afk", inline=False)
    embed.add_field(name="🎣 Economia", value="/pescar /carteira /daily /pay /top /slots /rank", inline=False)
    embed.add_field(name="👤 Utils", value="/avatar /userinfo /serverinfo /perfil /8ball /poll", inline=False)
    embed.add_field(name="🛡️ ADM", value="/ban /kick /timeout /clear /lock /warn", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="cj")
async def cj_cmd(ctx): await ctx.send(f"{ctx.author.mention} Vai usar /ajuda no <#{CANAL_BOT}>!")

bot.run(TOKEN)
