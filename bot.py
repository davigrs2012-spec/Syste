import os, random, asyncio, discord, re, math, json
from discord.ext import commands
from discord import app_commands
from collections import deque, defaultdict
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
    10: 1559444021531770993,
    20: 1559444648101945394,
    30: 1559444288859938916,
    40: 1559444486386360320,
    50: 1559444978017505280,
}
BOTS_RESTRITOS = [208583444938057728, 235148962103951360]
DB_FILE = "database.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix=["!", "cj!"], intents=intents, help_command=None)

# DBs MEMORIA
inventario_db = defaultdict(list)
carteira_db = defaultdict(int)
banco_db = defaultdict(int)
level_db = defaultdict(lambda: {"xp": 0, "level": 1, "messages": 0})
warns_db = defaultdict(list)
daily_db = {}
rep_db = defaultdict(int)
rep_cooldown = {}
marry_db = {}
afk_db = {}
recent_joins = deque()
pesca_evento_ativo = False
pesca_evento_fim = None
proxima_pesca_mitica = False
pesca_buff_admins = {}
pesca_cooldown = {}

# ===== SISTEMA DE SAVE QUE TU PEDIU =====
def salvar_db():
    try:
        dados = {
            "inventario": {str(k): v for k, v in inventario_db.items()},
            "carteira": dict(carteira_db),
            "banco": dict(banco_db),
            "level": {str(k): v for k, v in level_db.items()},
            "rep": dict(rep_db),
            "daily": {str(k): v.isoformat() if isinstance(v, datetime) else str(v) for k, v in daily_db.items()},
            "marry": {str(k): v for k, v in marry_db.items()},
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False)
    except Exception as e:
        print(f"Erro salvar: {e}")

def carregar_db():
    if not os.path.exists(DB_FILE):
        print("Sem database.json, criando novo")
        return
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for k, v in dados.get("inventario", {}).items():
            inventario_db[int(k)] = v
        for k, v in dados.get("carteira", {}).items():
            carteira_db[int(k)] = v
        for k, v in dados.get("banco", {}).items():
            banco_db[int(k)] = v
        for k, v in dados.get("level", {}).items():
            level_db[int(k)] = v
        for k, v in dados.get("rep", {}).items():
            rep_db[int(k)] = v
        for k, v in dados.get("daily", {}).items():
            try: daily_db[int(k)] = datetime.fromisoformat(v)
            except: pass
        for k, v in dados.get("marry", {}).items():
            marry_db[int(k)] = v
        print(f"DB CARREGADO: {len(level_db)} usuarios, {sum(len(v) for v in inventario_db.values())} peixes")
    except Exception as e:
        print(f"Erro carregar DB: {e}")

async def auto_save():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(300) # 5 min
        salvar_db()
        print("Auto-save feito")

peixes = [
    {"nome": "Bota Velha", "emoji": "🥾", "rar": "Lixo", "preco": 2, "xp": 1, "cor": 0x808080},
    {"nome": "Sardinha", "emoji": "🐟", "rar": "Comum", "preco": 10, "xp": 5, "cor": 0x2ecc71},
    {"nome": "Baiacu", "emoji": "🐡", "rar": "Raro", "preco": 50, "xp": 20, "cor": 0x3498db},
    {"nome": "Tubarao", "emoji": "🦈", "rar": "Lendario", "preco": 250, "xp": 100, "cor": 0xf1c40f},
    {"nome": "Kraken", "emoji": "🦑", "rar": "MITICO", "preco": 2000, "xp": 1000, "cor": 0xe74c3c},
    {"nome": "MEGALODON", "emoji": "🦈", "rar": "MITICO", "preco": 5000, "xp": 3000, "cor": 0xff0000},
]

FRASES_CJ = ["Para de me marcar big smoke~kun 😒","Vai pescar que tu ganha mais, fraco 🎣","Seita do CJ não tem tempo pra loritta 💅","Quem dorme de touca é o Vasco 🤣","Fala tu, Cristino mandou avisar que tu é cria da Seita 🔥","Pesca um Kraken e para de chorar 😭🦑"]
FRASES_LACRE = ["Quem tem CJ tem tudo, quem tem Loritta tem lag 💅","Seita do CJ não pede, conquista 🔥","Level 50 na Seita é mais raro que Kraken 🦑","Cristino criou, CJ executa, Seita domina 👑"]

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
    if new > old: salvar_db()
    return new > old, old, new

async def dar_cargo_level(member, level):
    if not member.guild: return
    for lvl_req, cargo_id in sorted(CARGOS_LEVEL.items()):
        if level >= lvl_req:
            cargo = member.guild.get_role(cargo_id)
            if cargo and cargo not in member.roles:
                try:
                    await member.add_roles(cargo, reason=f"Level {level}")
                    ch = bot.get_channel(CANAL_BOT)
                    if ch: await ch.send(f"🎉 {member.mention} pegou {cargo.mention} no level {level}!")
                except: pass

@bot.event
async def on_ready():
    carregar_db()
    print(f"CJ FINAL COM SAVE ON: {bot.user}")
    await bot.tree.sync()
    bot.loop.create_task(auto_save())

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(CANAL_BOAS_VINDAS)
    if ch:
        try:
            emb = discord.Embed(title="Bem vindo a Seita!", description=f"{member.mention} entrou! Somos {member.guild.member_count}! Vai no <#{CANAL_BOT}> e digita /seita", color=0x00ff00)
            emb.set_thumbnail(url=member.display_avatar.url)
            await ch.send(embed=emb)
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
    for m in message.mentions:
        if m.id in afk_db:
            try: await message.reply(f"{m.display_name} AFK: {afk_db[m.id][0]}", delete_after=8)
            except: pass
    if message.guild and not message.author.bot:
        upou, old, new = add_xp(message.author.id, random.randint(5, 12))
        if upou: await dar_cargo_level(message.author, new)
    if message.channel.id == CANAL_ISCA and not message.author.guild_permissions.administrator:
        try: await message.delete(); await message.guild.ban(message.author, reason="Isca", delete_message_days=1)
        except: pass
        return
    await bot.process_commands(message)

# ADM MOD
@bot.tree.command(name="clear", description="[ADM] Limpar")
async def clear(interaction: discord.Interaction, quantidade: int):
    if not is_mod(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True); d = await interaction.channel.purge(limit=quantidade); await interaction.followup.send(f"Apaguei {len(d)}!", ephemeral=True)
@bot.tree.command(name="ban", description="[ADM] Banir")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str="Sem motivo"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("So ADM!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"{membro.mention} banido!")
@bot.tree.command(name="kick", description="[ADM] Kikar")
async def kick(interaction: discord.Interaction, membro: discord.Member):
    if not interaction.user.guild_permissions.kick_members: await interaction.response.send_message("So ADM!", ephemeral=True); return
    await membro.kick(); await interaction.response.send_message(f"{membro.mention} kikado!")
@bot.tree.command(name="timeout", description="[ADM] Mutar")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int):
    if not is_mod(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos)); await interaction.response.send_message(f"{membro.mention} mutado {minutos}min")
@bot.tree.command(name="warn", description="[ADM] Warn")
async def warn(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not is_mod(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    warns_db[membro.id].append(motivo); await interaction.response.send_message(f"{membro.mention} warn {len(warns_db[membro.id])}/3")
@bot.tree.command(name="lock", description="[ADM] Trancar")
async def lock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message("Trancado!")
@bot.tree.command(name="unlock", description="[ADM] Destrancar")
async def unlock(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message("Destrancado!")
@bot.tree.command(name="anuncio", description="[ADM] Anuncio")
async def anuncio(interaction: discord.Interaction, titulo: str, descricao: str, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    c = canal or interaction.channel; emb = discord.Embed(title=titulo, description=descricao, color=0xff0000); await c.send(embed=emb); await interaction.response.send_message("Enviado!", ephemeral=True)
@bot.tree.command(name="falar_como_cj", description="[ADM] Falar como CJ")
async def falar_como_cj(interaction: discord.Interaction, mensagem: str, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    c = canal or interaction.channel
    try:
        webhook = await c.create_webhook(name="CJ")
        await webhook.send(content=mensagem, username="CJ", avatar_url=bot.user.display_avatar.url)
        await webhook.delete()
        await interaction.response.send_message("Enviado!", ephemeral=True)
    except Exception as e: await interaction.response.send_message(f"Erro: {e}", ephemeral=True)
@bot.tree.command(name="fake_ban", description="[ADM] Fake ban")
async def fake_ban(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    await interaction.response.send_message(f"🔨 {membro.mention} foi banido!")
    await asyncio.sleep(3); await interaction.followup.send(f"Brincadeira {membro.mention}, continua na Seita 😏")

# ADM CHEATS
@bot.tree.command(name="pescar_cheat", description="[ADM CHEAT] Forcar peixe")
async def pescar_cheat(interaction: discord.Interaction, peixe_nome: str, membro: discord.Member=None):
    if not is_adm(interaction): await interaction.response.send_message("So ADM cheat!", ephemeral=True); return
    alvo = membro or interaction.user
    achado = next((p for p in peixes if peixe_nome.lower() in p["nome"].lower()), None)
    if not achado: await interaction.response.send_message(f"Opcoes: {', '.join([p['nome'] for p in peixes])}", ephemeral=True); return
    inventario_db[alvo.id].append(achado); carteira_db[alvo.id]+=achado["preco"]; salvar_db()
    await interaction.response.send_message(f"CHEAT: {alvo.mention} ganhou {achado['nome']}!", ephemeral=True)
    if membro:
        canal = bot.get_channel(CANAL_PESCA)
        if canal: await canal.send(f"{alvo.mention} pescou {achado['emoji']} **{achado['nome']}**! 🦑")
@pescar_cheat.autocomplete("peixe_nome")
async def peixe_auto(interaction, current): return [app_commands.Choice(name=p["nome"], value=p["nome"]) for p in peixes if current.lower() in p["nome"].lower()][:25]
@bot.tree.command(name="dar_grana", description="[ADM CHEAT] Dar grana")
async def dar_grana(interaction: discord.Interaction, membro: discord.Member, quantia: int):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    carteira_db[membro.id]+=quantia; salvar_db(); await interaction.response.send_message(f"{membro.mention} recebeu R$ {quantia}!", ephemeral=True)
@bot.tree.command(name="set_level", description="[ADM CHEAT] Setar level")
async def set_level(interaction: discord.Interaction, membro: discord.Member, level: int):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    xp = xp_para_level(level); level_db[membro.id]["xp"]=xp; level_db[membro.id]["level"]=level; await dar_cargo_level(membro, level); salvar_db(); await interaction.response.send_message(f"{membro.mention} level {level}!", ephemeral=True)
@bot.tree.command(name="spawn_mitico", description="[ADM CHEAT] Proxima pesca mitica")
async def spawn_mitico(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    global proxima_pesca_mitica; proxima_pesca_mitica=True; await interaction.response.send_message("Kraken spawnado!", ephemeral=True)
    canal = bot.get_channel(CANAL_PESCA)
    if canal: await canal.send("🌊 **KRAKEN AVISTADO!** Proxima pesca sera MITICA! 🦑")
@bot.tree.command(name="pesca_evento", description="[ADM CHEAT] Evento 10min")
async def pesca_evento(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("So ADM!", ephemeral=True); return
    global pesca_evento_ativo, pesca_evento_fim; pesca_evento_ativo=True; pesca_evento_fim=datetime.now(timezone.utc)+timedelta(minutes=10)
    await interaction.response.send_message("Evento 10min!", ephemeral=True)
    canal = bot.get_channel(CANAL_PESCA)
    if canal: await canal.send(embed=discord.Embed(title="🎉 EVENTO PESCA 3X!", description="10min chance 3x Lendario!", color=0xffd700))

# MEMBROS SEITA CRISTINO
@bot.tree.command(name="seita", description="[MEMBROS] Juramento")
async def seita(interaction: discord.Interaction):
    emb = discord.Embed(title="👁️ JURAMENTO DA SEITA DO CJ", description="Eu juro:\n🔥 Nunca usar Loritta\n🎣 Pescar todo dia\n💀 Proteger a isca\n🏴‍☠️ Cristino é o mestre", color=0x000000)
    await interaction.response.send_message(embed=emb)
@bot.tree.command(name="vasco", description="[MEMBROS] Vasco")
async def vasco(interaction: discord.Interaction):
    await interaction.response.send_message("**VASCÃO!** 🖤🤍 O time da Seita!")
@bot.tree.command(name="cj_fala", description="[MEMBROS] CJ fala")
async def cj_fala(interaction: discord.Interaction):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    await interaction.response.send_message(random.choice(FRASES_CJ))
@bot.tree.command(name="lacrar", description="[MEMBROS] Lacrar")
async def lacrar(interaction: discord.Interaction):
    await interaction.response.send_message(f"💅 {random.choice(FRASES_LACRE)}")
@bot.tree.command(name="roleta", description="[MEMBROS] Roleta russa")
async def roleta(interaction: discord.Interaction):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    await interaction.response.send_message(f"{interaction.user.mention} girou... 🎲")
    await asyncio.sleep(2)
    if random.randint(1,6)==1:
        try: await interaction.user.timeout(timedelta(minutes=2)); await interaction.followup.send(f"💥 {interaction.user.mention} mutado 2min!")
        except: await interaction.followup.send("Era pra mutar mas deu erro!")
    else: await interaction.followup.send(f"😎 {interaction.user.mention} se salvou!")
@bot.tree.command(name="x1", description="[MEMBROS] X1")
async def x1(interaction: discord.Interaction, membro: discord.Member):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    vencedor = random.choice([interaction.user, membro]); await interaction.response.send_message(f"⚔️ {interaction.user.mention} vs {membro.mention}\nVencedor: **{vencedor.mention}**!")
@bot.tree.command(name="clima", description="[MEMBROS] Clima")
async def clima(interaction: discord.Interaction):
    g = interaction.guild; total = sum(len(v) for v in inventario_db.values())
    emb = discord.Embed(title="🌤️ Clima Seita", description=f"Membros: {g.member_count}\nPeixes pescados: {total}\nEvento: {'ATIVO 🔥' if pesca_evento_ativo else 'Inativo'}\nChefe: Cristino 👑", color=0x00ffff)
    await interaction.response.send_message(embed=emb)

# MEMBROS NORMAL
@bot.tree.command(name="pescar", description="[MEMBROS] Pescar")
async def pescar(interaction: discord.Interaction):
    if interaction.channel.id!=CANAL_PESCA: await interaction.response.send_message(f"Pesca so no <#{CANAL_PESCA}>!", ephemeral=True); return
    ultimo=pesca_cooldown.get(interaction.user.id); agora=datetime.now(timezone.utc)
    if ultimo and (agora-ultimo).total_seconds()<3: await interaction.response.send_message("Cooldown 3s!", ephemeral=True); return
    pesca_cooldown[interaction.user.id]=agora
    global proxima_pesca_mitica, pesca_evento_ativo, pesca_evento_fim
    if pesca_evento_ativo and pesca_evento_fim and agora>pesca_evento_fim: pesca_evento_ativo=False
    await interaction.response.defer(); await asyncio.sleep(1)
    if proxima_pesca_mitica: peixe=random.choice([p for p in peixes if p["rar"]=="MITICO"]); proxima_pesca_mitica=False
    elif pesca_evento_ativo: peixe=random.choices(peixes, weights=[5,5,10,10,30,30,20,20,20,15,5], k=1)[0]
    else: peixe=random.choices(peixes, weights=[30,25,20,15,8,4,2,1,0.5,0.5,0.2], k=1)[0]
    inventario_db[interaction.user.id].append(peixe); carteira_db[interaction.user.id]+=peixe["preco"]
    upou, old, new = add_xp(interaction.user.id, peixe["xp"])
    if upou: await dar_cargo_level(interaction.user, new)
    salvar_db()
    emb=discord.Embed(title="🎣 Pescou!", description=f"{peixe['emoji']} **{peixe['nome']}**\nRar: **{peixe['rar']}**\nR$ {peixe['preco']} +{peixe['xp']} XP", color=peixe["cor"])
    if upou: emb.add_field(name="LEVEL UP!", value=f"{old} -> {new}!")
    await interaction.followup.send(embed=emb)

@bot.tree.command(name="carteira", description="[MEMBROS] Carteira")
async def carteira(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; await interaction.response.send_message(f"💰 {membro.mention} Mao R$ {carteira_db[membro.id]} Banco R$ {banco_db[membro.id]}")
@bot.tree.command(name="daily", description="[MEMBROS] Daily")
async def daily(interaction: discord.Interaction):
    if not check_bot(interaction): await interaction.response.send_message(f"Use no <#{CANAL_BOT}>!", ephemeral=True); return
    agora=datetime.now(timezone.utc); ultimo=daily_db.get(interaction.user.id)
    if ultimo and (agora-ultimo).total_seconds()<86400: await interaction.response.send_message("Ja pegou!", ephemeral=True); return
    daily_db[interaction.user.id]=agora; premio=random.randint(150,400); carteira_db[interaction.user.id]+=premio; salvar_db(); await interaction.response.send_message(f"🎁 +R$ {premio}!")
@bot.tree.command(name="rank", description="[MEMBROS] Rank")
async def rank(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level_db[membro.id]; xp=data["xp"]; lvl=data["level"]
    xp_prox=xp_para_level(lvl+1); xp_base=xp_para_level(lvl); prog=xp-xp_base; total=xp_prox-xp_base
    perc=int(prog/total*100) if total>0 else 100; barra="█"*(perc//10)+"░"*(10-perc//10)
    emb=discord.Embed(title=f"Level {membro.display_name}", description=f"Level {lvl}\n{barra} {perc}%\n{prog}/{total} XP pro {lvl+1}\nFalta: {xp_prox-xp} XP", color=0x9b59b6); await interaction.response.send_message(embed=emb)
@bot.tree.command(name="xp", description="[MEMBROS] Tabela")
async def xp_table(interaction: discord.Interaction):
    desc="**CARGOS:**\nLevel 10=Cargo1\nLevel 20=Cargo2\nLevel 30=Cargo3\nLevel 40=Cargo4\nLevel 50=Cargo5\n\n"
    desc+="\n".join([f"Level {lvl}: {xp_para_level(lvl)} XP" for lvl in [10,20,30,40,50]])
    await interaction.response.send_message(embed=discord.Embed(title="Tabela", description=desc, color=0x3498db))
@bot.tree.command(name="perfil", description="[MEMBROS] Perfil")
async def perfil(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level_db[membro.id]; lvl=data["level"]
    emb=discord.Embed(title=f"Perfil {membro.display_name}", color=membro.color or 0x00ffff)
    emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="Level", value=f"{lvl} - {data['xp']} XP", inline=False)
    emb.add_field(name="Carteira", value=f"{carteira_db[membro.id]}", inline=True)
    emb.add_field(name="Reps", value=rep_db[membro.id], inline=True)
    await interaction.response.send_message(embed=emb)
@bot.tree.command(name="ajuda", description="Menu final")
async def ajuda(interaction: discord.Interaction):
    emb=discord.Embed(title="🤖 CJ Bot - FINAL COM SAVE", description="Nunca mais perde dados!", color=0x00ff00)
    emb.add_field(name="👑 ADM", value="/ban /kick /timeout /clear /warn /lock /unlock /anuncio /falar_como_cj /fake_ban", inline=False)
    emb.add_field(name="🎣 ADM CHEATS", value="/pescar_cheat /dar_grana /set_level /spawn_mitico /pesca_evento", inline=False)
    emb.add_field(name="👁️ SEITA", value="/seita /vasco /cj_fala /lacrar /roleta /x1 /clima", inline=False)
    emb.add_field(name="🎣 MEMBROS", value="/pescar /carteira /daily /rank /xp /perfil", inline=False)
    emb.add_field(name="💾 SAVE", value="Salva auto a cada 5min em database.json - nao perde mais!", inline=False)
    await interaction.response.send_message(embed=emb, ephemeral=True)

@bot.command(name="cj")
async def cj_cmd(ctx): await ctx.send(f"{ctx.author.mention} Usa /ajuda no <#{CANAL_BOT}>!")

bot.run(TOKEN)
