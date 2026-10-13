import os, random, asyncio, discord, re, math
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

# CONFIG SEITA DO CJ
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_SAIDA = 1558857282702409749
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
BOTS_RESTRITOS = [208583444938057728, 235148962103951360]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix=["!", "cj!"], intents=intents, help_command=None)

# DBs
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
links_bloqueados = False
auto_role_id = None

peixes = [
    {"nome": "Bota Velha", "emoji": "🥾", "rar": "Lixo", "preco": 2, "xp": 1, "cor": 0x808080},
    {"nome": "Sardinha", "emoji": "🐟", "rar": "Comum", "preco": 10, "xp": 5, "cor": 0x2ecc71},
    {"nome": "Baiacu", "emoji": "🐡", "rar": "Raro", "preco": 50, "xp": 20, "cor": 0x3498db},
    {"nome": "Tubarao", "emoji": "🦈", "rar": "Lendario", "preco": 250, "xp": 100, "cor": 0xf1c40f},
    {"nome": "Kraken", "emoji": "🦑", "rar": "MITICO", "preco": 2000, "xp": 1000, "cor": 0xe74c3c},
]

GIFS = {
    "kiss": "https://media.tenor.com/F02Ep3U2j0kAAAAC/anime-kiss.gif",
    "hug": "https://media.tenor.com/kCZj6Xh2aSsAAAAC/anime-hug.gif",
    "slap": "https://media.tenor.com/Uw1P5v2oD0QAAAAC/anime-slap.gif",
    "pat": "https://media.tenor.com/2uyENRuvV-0AAAAC/anime-head-pat.gif",
    "punch": "https://media.tenor.com/sV_My3vGgnYAAAAC/anime-punch.gif",
    "dance": "https://media.tenor.com/2uyENRuvV-0AAAAC/anime-dance.gif",
    "cuddle": "https://media.tenor.com/7a0a0a0a0a0AAAAC/cuddle-anime.gif",
}

def is_adm(i): return i.user.guild_permissions.administrator
def is_mod(i): return i.user.guild_permissions.moderate_members or is_adm(i)
def check_bot(i): return i.channel.id in [CANAL_BOT, CANAL_PESCA]
def xp_para_level(level): return (level - 1) ** 2 * 100
def level_from_xp(xp): return int(math.sqrt(xp / 100)) + 1
def add_xp(uid, amt):
    data = level_db[uid]
    data["xp"] += amt
    data["messages"] += 1
    old = data["level"]
    new = level_from_xp(data["xp"])
    data["level"] = new
    return new > old, old, new

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
    print(f"CJ FINAL ON: {bot.user}")
    await bot.tree.sync()

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(CANAL_BOAS_VINDAS)
    if ch:
        try:
            emb = discord.Embed(title="Bem vindo a Seita!", description=f"{member.mention} entrou! Somos {member.guild.member_count}! Vai no <#{CANAL_BOT}>!", color=0x00ff00)
            emb.set_thumbnail(url=member.display_avatar.url)
            await ch.send(embed=emb)
            cargo1 = member.guild.get_role(CARGOS_LEVEL[1])
            if cargo1: await member.add_roles(cargo1)
        except: pass
    agora = datetime.now(timezone.utc)
    recent_joins.append(agora)
    while recent_joins and (agora - recent_joins[0]).total_seconds() > 15: recent_joins.popleft()
    if (agora - member.created_at).days < 3:
        try: await member.kick(reason="Conta nova")
        except: pass

@bot.event
async def on_message(message):
    if message.author.bot:
        if message.author.id in BOTS_RESTRITOS and message.channel.id!= CANAL_BOT:
            try: await message.delete()
            except: pass
        return
    if message.author.id in afk_db:
        del afk_db[message.author.id]
        try: await message.channel.send(f"Bem vindo de volta {message.author.mention}!", delete_after=5)
        except: pass
    for m in message.mentions:
        if m.id in afk_db:
            try: await message.reply(f"{m.display_name} ta AFK: {afk_db[m.id][0]}", delete_after=8)
            except: pass
    if message.guild and not message.author.bot:
        upou, old, new = add_xp(message.author.id, random.randint(5, 12))
        if upou: await dar_cargo_level(message.author, new)
    if message.channel.id == CANAL_ISCA:
        if message.author.guild_permissions.administrator:
            await bot.process_commands(message)
            return
        try:
            await message.delete()
            await message.guild.ban(message.author, reason="Isca", delete_message_days=1)
        except: pass
        return
    if links_bloqueados and message.guild and not message.author.guild_permissions.manage_messages:
        if re.search(r"https?://|discord.gg", message.content):
            try: await message.delete(); return
            except: pass
    await bot.process_commands(message)

# ADM
@bot.tree.command(name="clear", description="[ADM] Limpar")
async def clear(interaction: discord.Interaction, quantidade: int):
    if not is_mod(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True); d = await interaction.channel.purge(limit=quantidade); await interaction.followup.send(f"Apaguei {len(d)}!", ephemeral=True)

@bot.tree.command(name="ban", description="[ADM] Banir")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("So ADM!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"{membro.mention} banido!")

@bot.tree.command(name="unban", description="[ADM] Desbanir ID")
async def unban(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("So ADM!", ephemeral=True); return
    u = await bot.fetch_user(int(user_id)); await interaction.guild.unban(u); await interaction.response.send_message(f"{u.mention} desbanido!")

@bot.tree.command(name="kick", description="[ADM] Kikar")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members: await interaction.response.send_message("So ADM!", ephemeral=True); return
    await membro.kick(reason=motivo); await interaction.response.send_message(f"{membro.mention} kikado!")

@bot.tree.command(name="timeout", description="[ADM] Mutar")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int):
    if not is_mod(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos)); await interaction.response.send_message(f"{membro.mention} mutado {minutos}min")

@bot.tree.command(name="untimeout", description="[ADM] Desmutar")
async def untimeout(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await membro.timeout(None); await interaction.response.send_message(f"{membro.mention} desmutado!")

@bot.tree.command(name="warn", description="[ADM] Warn")
async def warn(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not is_mod(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    warns_db[membro.id].append(motivo); await interaction.response.send_message(f"{membro.mention} warn {len(warns_db[membro.id])}/3: {motivo}")
    if len(warns_db[membro.id]) >= 3:
        try: await membro.ban(reason="3 warns", delete_message_days=1)
        except: pass

@bot.tree.command(name="lock", description="[ADM] Trancar")
async def lock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message("Trancado!")

@bot.tree.command(name="unlock", description="[ADM] Destrancar")
async def unlock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message("Destrancado!")

@bot.tree.command(name="slowmode", description="[ADM] Slowmode")
async def slowmode(interaction: discord.Interaction, segundos: int):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.channel.edit(slowmode_delay=segundos); await interaction.response.send_message(f"Slowmode {segundos}s!")

@bot.tree.command(name="nuke", description="[ADM] Nukar canal")
async def nuke(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.response.defer(); ch = interaction.channel; new = await ch.clone(); await new.edit(position=ch.position); await ch.delete(); await new.send(f"Nukado por {interaction.user.mention} 💥")

@bot.tree.command(name="antilink", description="[ADM] Antilink on/off")
async def antilink(interaction: discord.Interaction, acao: str):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    global links_bloqueados; links_bloqueados = (acao == "on"); await interaction.response.send_message(f"Antilink {acao}!")
@antilink.autocomplete("acao")
async def al_auto(interaction, current): return [app_commands.Choice(name=v, value=v) for v in ["on","off"] if current in v]

@bot.tree.command(name="anuncio", description="[ADM] Anuncio")
async def anuncio(interaction: discord.Interaction, titulo: str, descricao: str, canal: discord.TextChannel = None):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    c = canal or interaction.channel; emb = discord.Embed(title=titulo, description=descricao, color=0xff0000); await c.send(embed=emb); await interaction.response.send_message("Enviado!", ephemeral=True)

@bot.tree.command(name="poll", description="[ADM] Enquete")
async def poll(interaction: discord.Interaction, pergunta: str, opcao1: str, opcao2: str):
    emb = discord.Embed(title=f"📊 {pergunta}", description=f"1️⃣ {opcao1}\n2️⃣ {opcao2}", color=0x00ffff); await interaction.response.send_message(embed=emb); m = await interaction.original_response(); await m.add_reaction("1️⃣"); await m.add_reaction("2️⃣")

# MEMBROS
async def social(interaction, membro, tipo, verbo):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    if membro.id == interaction.user.id: await interaction.response.send_message("Nao pode em voce mesmo!", ephemeral=True); return
    emb = discord.Embed(description=f"**{interaction.user.mention} {verbo} {membro.mention}!**", color=0xff69b4); emb.set_image(url=GIFS[tipo]); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="beijar", description="[MEMBROS] Beijar")
async def beijar(interaction: discord.Interaction, membro: discord.Member): await social(interaction, membro, "kiss", "beijou")
@bot.tree.command(name="abracar", description="[MEMBROS] Abracar")
async def abracar(interaction: discord.Interaction, membro: discord.Member): await social(interaction, membro, "hug", "abracou")
@bot.tree.command(name="tapa", description="[MEMBROS] Tapa")
async def tapa(interaction: discord.Interaction, membro: discord.Member): await social(interaction, membro, "slap", "deu tapa em")
@bot.tree.command(name="cafune", description="[MEMBROS] Cafune")
async def cafune(interaction: discord.Interaction, membro: discord.Member): await social(interaction, membro, "pat", "fez cafune em")
@bot.tree.command(name="ship", description="[MEMBROS] Shippar")
async def ship(interaction: discord.Interaction, pessoa1: discord.Member, pessoa2: discord.Member = None):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    pessoa2 = pessoa2 or interaction.user; perc = random.randint(0,100); barra = "█"*(perc//10)+"░"*(10-perc//10); await interaction.response.send_message(embed=discord.Embed(title="SHIP", description=f"{pessoa1.mention} + {pessoa2.mention}\n{barra} {perc}%", color=0xff00ff))
@bot.tree.command(name="casar", description="[MEMBROS] Casar")
async def casar(interaction: discord.Interaction, membro: discord.Member):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    marry_db[interaction.user.id]=membro.id; marry_db[membro.id]=interaction.user.id; await interaction.response.send_message(f"💒 {interaction.user.mention} e {membro.mention} casaram!")
@bot.tree.command(name="rep", description="[MEMBROS] Rep")
async def rep(interaction: discord.Interaction, membro: discord.Member):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    agora = datetime.now(timezone.utc); ultimo = rep_cooldown.get(interaction.user.id)
    if ultimo and (agora-ultimo).total_seconds()<3600: await interaction.response.send_message("Espera 1h!", ephemeral=True); return
    rep_cooldown[interaction.user.id]=agora; rep_db[membro.id]+=1; await interaction.response.send_message(f"⭐ {interaction.user.mention} deu rep pra {membro.mention}! Total {rep_db[membro.id]}")
@bot.tree.command(name="afk", description="[MEMBROS] AFK")
async def afk(interaction: discord.Interaction, motivo: str="AFK"):
    afk_db[interaction.user.id]=(motivo, datetime.now(timezone.utc)); await interaction.response.send_message(f"{interaction.user.mention} AFK: {motivo}")
@bot.tree.command(name="pescar", description="[MEMBROS] Pescar")
async def pescar(interaction: discord.Interaction):
    if interaction.channel.id!=CANAL_PESCA: await interaction.response.send_message(f"Pesca so no <#{CANAL_PESCA}>!", ephemeral=True); return
    p = random.choices(peixes, weights=[30,25,20,15,10], k=1)[0]; inventario_db[interaction.user.id].append(p); carteira_db[interaction.user.id]+=p["preco"]
    upou, old, new = add_xp(interaction.user.id, p["xp"])
    if upou: await dar_cargo_level(interaction.user, new)
    emb = discord.Embed(title="🎣 Pescou!", description=f"{p['emoji']} {p['nome']} R$ {p['preco']} +{p['xp']} XP", color=p["cor"])
    if upou: emb.add_field(name="LEVEL UP!", value=f"{old} -> {new}!")
    await interaction.response.send_message(embed=emb)
@bot.tree.command(name="carteira", description="[MEMBROS] Carteira")
async def carteira(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; await interaction.response.send_message(f"💰 {membro.mention} Mao R$ {carteira_db[membro.id]} Banco R$ {banco_db[membro.id]}")
@bot.tree.command(name="daily", description="[MEMBROS] Daily")
async def daily(interaction: discord.Interaction):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    agora=datetime.now(timezone.utc); ultimo=daily_db.get(interaction.user.id)
    if ultimo and (agora-ultimo).total_seconds()<86400: await interaction.response.send_message("Ja pegou daily!", ephemeral=True); return
    daily_db[interaction.user.id]=agora; premio=random.randint(150,400); carteira_db[interaction.user.id]+=premio; await interaction.response.send_message(f"🎁 +R$ {premio}!")
@bot.tree.command(name="pay", description="[MEMBROS] Pay")
async def pay(interaction: discord.Interaction, membro: discord.Member, quantia: int):
    if carteira_db[interaction.user.id]<quantia: await interaction.response.send_message("Sem grana!", ephemeral=True); return
    carteira_db[interaction.user.id]-=quantia; carteira_db[membro.id]+=quantia; await interaction.response.send_message(f"{interaction.user.mention} pagou R$ {quantia} pra {membro.mention}!")
@bot.tree.command(name="slots", description="[MEMBROS] Slots")
async def slots(interaction: discord.Interaction, aposta: int):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    if carteira_db[interaction.user.id]<aposta: await interaction.response.send_message("Sem grana!", ephemeral=True); return
    emojis=["🍒","🍋","🍊","🍇","💎","7️⃣"]; r=[random.choice(emojis) for _ in range(3)]; res=" | ".join(r)
    if r[0]==r[1]==r[2]: premio=aposta*5; carteira_db[interaction.user.id]+=premio; await interaction.response.send_message(f"{res}\nJACKPOT +R$ {premio}!")
    else: carteira_db[interaction.user.id]-=aposta; await interaction.response.send_message(f"{res}\nPerdeu R$ {aposta}!")
@bot.tree.command(name="top", description="[MEMBROS] Top ricos")
async def top(interaction: discord.Interaction):
    ranking=sorted(carteira_db.items(), key=lambda x: x[1]+banco_db[x[0]], reverse=True)[:10]
    desc="\n".join([f"{i+1}. <@{uid}> - R$ {grana+banco_db[uid]}" for i,(uid,grana) in enumerate(ranking)]) or "Vazio"
    await interaction.response.send_message(embed=discord.Embed(title="Top Ricos", description=desc, color=0xf1c40f))

@bot.tree.command(name="perfil", description="[MEMBROS] Perfil completo")
async def perfil(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level_db[membro.id]; xp=data["xp"]; lvl=data["level"]
    xp_prox=xp_para_level(lvl+1); xp_base=xp_para_level(lvl); prog=xp-xp_base; total=xp_prox-xp_base
    perc=int(prog/total*100) if total>0 else 100; barra="█"*(perc//10)+"░"*(10-perc//10)
    casado=f"<@{marry_db[membro.id]}>" if membro.id in marry_db else "Solteiro"
    emb=discord.Embed(title=f"Perfil {membro.display_name}", color=membro.color or 0x00ffff)
    emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="Level", value=f"{lvl} {barra} {perc}%\n{prog}/{total} XP", inline=False)
    emb.add_field(name="Carteira", value=f"Mao {carteira_db[membro.id]} | Banco {banco_db[membro.id]}", inline=True)
    emb.add_field(name="Reps", value=rep_db[membro.id], inline=True)
    emb.add_field(name="Casado", value=casado, inline=True)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="rank", description="[MEMBROS] Rank com XP")
async def rank(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level_db[membro.id]; xp=data["xp"]; lvl=data["level"]
    xp_prox=xp_para_level(lvl+1); xp_base=xp_para_level(lvl); prog=xp-xp_base; total=xp_prox-xp_base
    perc=int(prog/total*100) if total>0 else 100; barra="█"*(perc//10)+"░"*(10-perc//10)
    emb=discord.Embed(title=f"Level {membro.display_name}", description=f"Level {lvl}\n{barra} {perc}%\n{prog}/{total} XP pro {lvl+1}\nTotal: {xp} XP\nFalta: {xp_prox-xp} XP", color=0x9b59b6)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="xp", description="[MEMBROS] Tabela XP")
async def xp_table(interaction: discord.Interaction):
    desc="\n".join([f"Level {lvl}: {xp_para_level(lvl)} XP" for lvl in [1,2,3,4,5,10,15,20,30,50]])
    desc+="\n\nMsg = 5-12 XP | Pesca = 1-1000 XP"
    await interaction.response.send_message(embed=discord.Embed(title="Tabela XP", description=desc, color=0x3498db))

@bot.tree.command(name="avatar", description="[MEMBROS] Avatar")
async def avatar(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; emb=discord.Embed(title=f"Avatar {membro.display_name}"); emb.set_image(url=membro.display_avatar.url); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="userinfo", description="[MEMBROS] Userinfo")
async def userinfo(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level_db[membro.id]
    emb=discord.Embed(title=f"Info {membro.display_name}"); emb.add_field(name="ID", value=membro.id); emb.add_field(name="Level", value=f"{data['level']} | {data['xp']} XP"); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="serverinfo", description="[MEMBROS] Serverinfo")
async def serverinfo(interaction: discord.Interaction):
    g=interaction.guild; emb=discord.Embed(title=g.name); emb.add_field(name="Membros", value=g.member_count); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="8ball", description="[MEMBROS] 8ball")
async def eightball(interaction: discord.Interaction, pergunta: str):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    await interaction.response.send_message(f"{pergunta} = {random.choice(['Sim','Nao','Talvez'])}")

@bot.tree.command(name="ajuda", description="Ajuda completa")
async def ajuda(interaction: discord.Interaction):
    emb=discord.Embed(title="CJ Bot - Menu Completo", description="Bonito e organizado!", color=0x00ff00)
    emb.add_field(name="👑 ADM", value="/ban /unban /kick /timeout /untimeout /clear /warn /lock /unlock /slowmode /nuke /antilink /anuncio /poll", inline=False)
    emb.add_field(name="👥 MEMBROS Diversao (so #comandos)", value="/beijar /abracar /tapa /cafune /ship /casar /rep /afk /8ball", inline=False)
    emb.add_field(name="🎣 MEMBROS Economia", value="/pescar /inventario /vender /carteira /daily /pay /slots /top", inline=False)
    emb.add_field(name="📊 MEMBROS Info", value="/perfil /rank /xp /top /avatar /userinfo /serverinfo", inline=False)
    emb.add_field(name="💡 XP", value=f"Msg 5-12 XP | Level 10: {xp_para_level(10)} XP | /xp pra tabela", inline=False)
    await interaction.response.send_message(embed=emb, ephemeral=True)

@bot.command(name="cj")
async def cj_cmd(ctx): await ctx.send(f"{ctx.author.mention} Usa /ajuda no <#{CANAL_BOT}>!")

bot.run(TOKEN)
