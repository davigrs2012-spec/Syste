import os, random, asyncio, discord
from discord.ext import commands
from discord import app_commands
from collections import defaultdict
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
CANAL_ANTIRAID = 1559066250410197013

CARGOS_LEVEL = {
    10: 1559444021531770993,
    20: 1559444648101945394,
    30: 1559444288859938916,
    40: 1559444486386360320,
    50: 1559444978017505280,
}
BOTS_RESTRITOS = [208583444938057728, 235148962103951360]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.guild_messages = True
bot = commands.Bot(command_prefix=["!", "cj!", "?"], intents=intents, help_command=None)

# MEMORIA - BOT PERFEITO SEM JSON
inventario = defaultdict(list)
carteira = defaultdict(int)
level = defaultdict(lambda: {"xp": 0, "level": 1})
warns = defaultdict(list)
daily = {}
work = {}
rep = defaultdict(int)
afk = {}
casamento = {}
pesca_cd = {}
cmd_cd = defaultdict(dict)
blacklist = set()
mutados = {}

# Peixes simples - sem aprofundar
peixes_simples = [
    {"nome": "Sardinha", "emoji": "🐟", "rar": "Comum", "preco": 10, "xp": 5, "cor": 0x2ecc71},
    {"nome": "Tilapia", "emoji": "🐠", "rar": "Comum", "preco": 15, "xp": 8, "cor": 0x1abc9c},
    {"nome": "Tubarao", "emoji": "🦈", "rar": "Raro", "preco": 100, "xp": 50, "cor": 0xf1c40f},
    {"nome": "Kraken", "emoji": "🦑", "rar": "MITICO", "preco": 1000, "xp": 500, "cor": 0xe74c3c},
    {"nome": "Cristino Dourado", "emoji": "👑", "rar": "SECRETO", "preco": 10000, "xp": 5000, "cor": 0xffd700},
]

FRASES_CJ = [
    "Para de me marcar big smoke~kun 😒", "Vai pescar que tu ganha mais, fraco 🎣",
    "Seita do CJ não tem tempo pra loritta", "Quem dorme de touca é o Vasco 🤣",
    "Fala tu, Cristino mandou avisar que tu é cria da Seita 🔥",
    "Level 50 ou é loritta? 👀", "Pesca um Kraken primeiro depois fala comigo 🦑",
    "Seita do CJ domina", "VASCÃO É O TIME DA SEITA 🖤🤍", "Quem tem CJ tem tudo",
    "Seita não pede, conquista 🔥", "Cristino criou, CJ executa 👑",
    "Dorme de touca? Só o Vasco que não 😂", "Big Smoke traiu o CJ, tu vai trair a Seita?",
    "Grove Street é da Seita agora 🏴‍☠️",
]

RESPOSTAS_8BALL = [
    "Sim, com certeza! 🔥", "Não, nem a pau 💀", "Talvez, vai pescar e descobre 🎣",
    "Cristino disse que sim 👑", "Seita aprova! 👁️", "Vasco disse que sim 🖤🤍",
    "Com certeza absoluta!", "Pergunta pro CJ depois 🎣", "Seita diz: vai na fé!",
]

def is_adm(i): return i.user.guild_permissions.administrator
def is_mod(i): return i.user.guild_permissions.moderate_members or is_adm(i)
def is_dono(i): return i.user.id == i.guild.owner_id or is_adm(i)
def xp_para_level(l): return (l - 1) ** 2 * 100
def level_from_xp(xp): return int((xp / 100) ** 0.5) + 1

def add_xp(uid, amt):
    data = level[uid]
    data["xp"] += amt
    old = data["level"]
    new = level_from_xp(data["xp"])
    data["level"] = new
    return new > old, old, new

async def dar_cargo_level(member, lvl):
    if not member.guild: return
    for lvl_req, cargo_id in sorted(CARGOS_LEVEL.items()):
        if lvl >= lvl_req:
            cargo = member.guild.get_role(cargo_id)
            if cargo and cargo not in member.roles:
                try:
                    await member.add_roles(cargo, reason=f"Level {lvl}")
                    ch = bot.get_channel(CANAL_BOT)
                    if ch: await ch.send(f"🎉 {member.mention} pegou {cargo.mention} no level {lvl}!")
                except: pass

def check_cd(uid, cmd, seg=5):
    agora = datetime.now(timezone.utc)
    ultimo = cmd_cd[uid].get(cmd)
    if ultimo and (agora - ultimo).total_seconds() < seg:
        return int(seg - (agora - ultimo).total_seconds())
    cmd_cd[uid][cmd] = agora
    return 0

@bot.event
async def on_ready():
    print(f"CJ BOT PERFEITO FINAL ON: {bot.user} - BASEADO EM TUDO - SEGURANÇA + DIVERSÃO - SEM JSON")
    try:
        s = await bot.tree.sync()
        print(f"Sync {len(s)} comandos - BOT PERFEITO")
    except Exception as e:
        print(f"Erro sync {e}")

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(CANAL_BOAS_VINDAS)
    if ch:
        try:
            emb = discord.Embed(title="👁️ Bem vindo a Seita do CJ!", description=f"{member.mention} entrou! Somos {member.guild.member_count}! Vai no <#{CANAL_BOT}> e digita /seita\n\n🛡️ **Servidor protegido contra raid!**\n🎣 **Pesca simples**\n🎲 **Diversão sem lacrar**\n👑 **Cristino é o mestre**", color=0x00ff00)
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
    if message.author.id in blacklist:
        try: await message.delete()
        except: pass
        return
    # AFK
    if message.mentions:
        for m in message.mentions:
            if m.id in afk:
                await message.channel.send(f"💤 {m.display_name} tá AFK: {afk[m.id]}", delete_after=10)
    if message.author.id in afk:
        del afk[message.author.id]
        await message.channel.send(f"👋 {message.author.mention} voltou do AFK!", delete_after=5)
    # XP
    if message.guild and not message.author.bot:
        upou, old, new = add_xp(message.author.id, random.randint(5, 15))
        if upou: await dar_cargo_level(message.author, new)
    # ANTI RAID - CANAL ISCA
    if message.channel.id == CANAL_ISCA and not message.author.guild_permissions.administrator:
        try:
            await message.delete()
            await message.guild.ban(message.author, reason="Clicou na isca - Anti Raid", delete_message_days=1)
            log = bot.get_channel(CANAL_ANTIRAID)
            if log:
                await log.send(f"🚨 **ANTI RAID ATIVADO!** {message.author.mention} ({message.author.id}) clicou na isca e foi banido! 🛡️")
        except: pass
        return
    await bot.process_commands(message)

# ==============================================================================
# SEGURANÇA ADM - 20 COMANDOS - BASEADO EM WICK, CARL, TICKET TOOL
# ==============================================================================
@bot.tree.command(name="clear", description="[ADM] Limpar mensagens - SEGURANÇA")
async def clear_cmd(interaction: discord.Interaction, quantidade: int):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD! Só tu vê esse erro!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"✅ Apaguei {len(deleted)} mensagens! 🧹", ephemeral=True)

@bot.tree.command(name="ban", description="[ADM] Banir - SEGURANÇA BASE WICK")
async def ban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Sem motivo"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("❌ Só ADM! Erro só tu vê!", ephemeral=True); return
    if membro.top_role >= interaction.user.top_role and interaction.user.id!= interaction.guild.owner_id:
        await interaction.response.send_message("❌ Ele tem cargo maior!", ephemeral=True); return
    await membro.ban(reason=f"{motivo} | Por {interaction.user}", delete_message_days=1)
    await interaction.response.send_message(f"🔨 {membro.mention} banido! Motivo: {motivo} | Por {interaction.user.mention}")
    log = bot.get_channel(CANAL_LOGS)
    if log: await log.send(f"🔨 **BAN:** {membro.mention} banido por {interaction.user.mention} - {motivo}")

@bot.tree.command(name="unban", description="[ADM] Desbanir por ID - SEGURANÇA")
async def unban_cmd(interaction: discord.Interaction, user_id: str, motivo: str="Desban"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=motivo)
        await interaction.response.send_message(f"✅ {user.mention} desbanido! {motivo}")
    except Exception as e: await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

@bot.tree.command(name="kick", description="[ADM] Kikar - SEGURANÇA")
async def kick_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Sem motivo"):
    if not interaction.user.guild_permissions.kick_members: await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    await membro.kick(reason=motivo); await interaction.response.send_message(f"👢 {membro.mention} kikado! {motivo}")

@bot.tree.command(name="timeout", description="[ADM] Mutar - SEGURANÇA")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str="Sem motivo"):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos), reason=motivo); await interaction.response.send_message(f"⏰ {membro.mention} mutado {minutos}min! {motivo}")

@bot.tree.command(name="untimeout", description="[ADM] Desmutar")
async def untimeout_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await membro.timeout(None); await interaction.response.send_message(f"✅ {membro.mention} desmutado!")

@bot.tree.command(name="warn", description="[ADM] Warn - SEGURANÇA")
async def warn_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    warns[membro.id].append({"motivo": motivo, "por": interaction.user.id})
    total = len(warns[membro.id]); await interaction.response.send_message(f"⚠️ {membro.mention} warn {total}/3! {motivo}")
    if total>=3:
        try: await membro.timeout(timedelta(minutes=30), reason="3 warns"); await interaction.followup.send(f"⏰ {membro.mention} 3 warns = mutado 30min!")
        except: pass

@bot.tree.command(name="lock", description="[ADM] Trancar canal - SEGURANÇA CARL-BOT")
async def lock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    c = canal or interaction.channel
    await c.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"🔒 Canal {c.mention} trancado! Só ADM fala!")

@bot.tree.command(name="unlock", description="[ADM] Destrancar canal - SEGURANÇA")
async def unlock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    c = canal or interaction.channel
    await c.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"🔓 Canal {c.mention} destrancado!")

@bot.tree.command(name="slowmode", description="[ADM] Slowmode - SEGURANÇA")
async def slowmode_cmd(interaction: discord.Interaction, segundos: int, canal: discord.TextChannel=None):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    c = canal or interaction.channel
    await c.edit(slowmode_delay=segundos); await interaction.response.send_message(f"⏳ Slowmode {c.mention} = {segundos}s!")

@bot.tree.command(name="dar_cargo", description="[ADM] Dar cargo pra alguém - SEGURANÇA")
async def dar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    if cargo >= interaction.user.top_role and interaction.user.id!= interaction.guild.owner_id:
        await interaction.response.send_message("❌ Cargo maior que o teu!", ephemeral=True); return
    await membro.add_roles(cargo); await interaction.response.send_message(f"✅ {membro.mention} ganhou {cargo.mention}!")

@bot.tree.command(name="tirar_cargo", description="[ADM] Tirar cargo")
async def tirar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    await membro.remove_roles(cargo); await interaction.response.send_message(f"✅ {membro.mention} perdeu {cargo.mention}!")

@bot.tree.command(name="permissao", description="[ADM] Dar permissão no canal - SEGURANÇA")
async def permissao_cmd(interaction: discord.Interaction, membro: discord.Member, canal: discord.TextChannel=None, permissao: str="send"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    c = canal or interaction.channel
    if permissao=="send": await c.set_permissions(membro, send_messages=True); await interaction.response.send_message(f"✅ {membro.mention} pode falar no {c.mention}!")
    elif permissao=="block": await c.set_permissions(membro, send_messages=False); await interaction.response.send_message(f"🚫 {membro.mention} bloqueado no {c.mention}!")

@permissao_cmd.autocomplete("permissao")
async def perm_auto(interaction, current): return [app_commands.Choice(name=p, value=p) for p in ["send","block"] if current.lower() in p]

@bot.tree.command(name="anuncio", description="[ADM] Anuncio embed - SEGURANÇA")
async def anuncio_cmd(interaction: discord.Interaction, titulo: str, descricao: str, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    c = canal or interaction.channel; emb = discord.Embed(title=titulo, description=descricao, color=0xff0000); emb.set_footer(text=f"Por {interaction.user.display_name}")
    await c.send(embed=emb); await interaction.response.send_message("✅ Anuncio enviado!", ephemeral=True)

@bot.tree.command(name="falar_como_cj", description="[ADM] Falar como CJ webhook - ZOEIRA")
async def falar_como_cj_cmd(interaction: discord.Interaction, mensagem: str, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    c = canal or interaction.channel
    try: w = await c.create_webhook(name="CJ"); await w.send(content=mensagem, username="CJ", avatar_url=bot.user.display_avatar.url); await w.delete(); await interaction.response.send_message("✅ Falou como CJ!", ephemeral=True)
    except Exception as e: await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

@bot.tree.command(name="fake_ban", description="[ADM] Fake ban zoeira - DIVERSÃO ADM")
async def fake_ban_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    await interaction.response.send_message(f"🔨 {membro.mention} foi banido para sempre da Seita! Adeus!"); await asyncio.sleep(2); await interaction.followup.send(f"😂 Brincadeira {membro.mention}, caiu na pegadinha do Mario Games! Seita te ama! 👁️")

@bot.tree.command(name="blacklist_add", description="[ADM] Blacklist - SEGURANÇA ANTI RAID")
async def blacklist_add_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    blacklist.add(membro.id); await interaction.response.send_message(f"🚫 {membro.mention} na blacklist! Mensagens apagadas automaticamente!")

@bot.tree.command(name="blacklist_remove", description="[ADM] Tirar da blacklist")
async def blacklist_remove_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    blacklist.discard(membro.id); await interaction.response.send_message(f"✅ {membro.mention} saiu da blacklist!")

@bot.tree.command(name="antiraid_on", description="[ADM] Ativar anti raid - SEGURANÇA MAXIMA")
async def antiraid_on_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    # Trava tudo
    for ch in interaction.guild.text_channels:
        try: await ch.set_permissions(interaction.guild.default_role, send_messages=False)
        except: pass
    await interaction.response.send_message("🛡️ **ANTI RAID ATIVADO!** Todos canais trancados! Use /antiraid_off pra liberar!")

@bot.tree.command(name="antiraid_off", description="[ADM] Desativar anti raid")
async def antiraid_off_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    for ch in interaction.guild.text_channels:
        try: await ch.set_permissions(interaction.guild.default_role, send_messages=True)
        except: pass
    await interaction.response.send_message("🛡️ **ANTI RAID DESATIVADO!** Canais liberados!")

# CHEATS ADM
@bot.tree.command(name="dar_grana", description="[ADM CHEAT] Dar grana")
async def dar_grana_cmd(interaction: discord.Interaction, membro: discord.Member, quantia: int):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    carteira[membro.id]+=quantia; await interaction.response.send_message(f"💰 {membro.mention} recebeu R$ {quantia}!")

@bot.tree.command(name="set_level", description="[ADM CHEAT] Setar level")
async def set_level_cmd(interaction: discord.Interaction, membro: discord.Member, level_num: int):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só ADM!", ephemeral=True); return
    level[membro.id]["xp"]=xp_para_level(level_num); level[membro.id]["level"]=level_num; await dar_cargo_level(membro, level_num); await interaction.response.send_message(f"⬆️ {membro.mention} level {level_num}!")

# ==============================================================================
# MEMBROS - DIVERSÃO SEM LACRAR - COMANDOS CJ - ZOEIRA
# ==============================================================================
@bot.tree.command(name="seita", description="[MEMBROS] Juramento da Seita - COMANDO CJ")
async def seita_cmd(interaction: discord.Interaction):
    emb = discord.Embed(title="👁️ JURAMENTO DA SEITA DO CJ - BOT PERFEITO", description="Eu juro:\n🔥 Nunca usar Loritta (lag)\n🎣 Pescar de vez em quando\n💀 Proteger a isca anti raid\n🏴‍☠️ Cristino é o mestre\n🛡️ Segurança em primeiro lugar\n🎲 Diversão sem lacrar\n🖤🤍 Vasco é religião!", color=0x000000)
    emb.set_footer(text="Bot perfeito baseado em tudo - Wick, Carl, Dank, Mudae")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="cj_fala", description="[MEMBROS] CJ fala - COMANDO CJ ZOEIRA")
async def cj_fala_cmd(interaction: discord.Interaction):
    if interaction.channel.id!= CANAL_BOT and not is_adm(interaction): await interaction.response.send_message(f"❌ Só no <#{CANAL_BOT}>! Só tu vê!", ephemeral=True); return
    await interaction.response.send_message(f"👁️ **CJ diz:** {random.choice(FRASES_CJ)}")

@bot.tree.command(name="vasco", description="[MEMBROS] Vasco - COMANDO CJ")
async def vasco_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("**VASCÃO DA SEITA!** 🖤🤍\nCruz de Malta é meu pendão! Seita é Vasco, Vasco é Seita! 🖤🤍👑\n**BOT PERFEITO É VASCO!**")

@bot.tree.command(name="8ball", description="[MEMBROS] Bola 8 magica - DIVERSÃO")
async def ball_cmd(interaction: discord.Interaction, pergunta: str):
    await interaction.response.send_message(f"🎱 **{pergunta}**\n**Resposta:** {random.choice(RESPOSTAS_8BALL)}")

@bot.tree.command(name="roleta", description="[MEMBROS] Roleta russa - DIVERSÃO ZOEIRA")
async def roleta_cmd(interaction: discord.Interaction):
    if interaction.channel.id!= CANAL_BOT: await interaction.response.send_message(f"❌ Só no <#{CANAL_BOT}>!", ephemeral=True); return
    cd = check_cd(interaction.user.id, "roleta", 30)
    if cd: await interaction.response.send_message(f"⏳ {cd}s", ephemeral=True); return
    await interaction.response.send_message(f"🎲 {interaction.user.mention} girou..."); await asyncio.sleep(2)
    if random.randint(1,6)==1:
        try: await interaction.user.timeout(timedelta(minutes=2)); await interaction.followup.send(f"💥 BANG! {interaction.user.mention} mutado 2min! 😂")
        except: await interaction.followup.send(f"💥 {interaction.user.mention} era pra mutar mas é ADM!")
    else: await interaction.followup.send(f"😎 CLICK! {interaction.user.mention} se salvou!")

@bot.tree.command(name="x1", description="[MEMBROS] X1 - DIVERSÃO")
async def x1_cmd(interaction: discord.Interaction, membro: discord.Member):
    if interaction.channel.id!= CANAL_BOT: await interaction.response.send_message(f"❌ Só no <#{CANAL_BOT}>!", ephemeral=True); return
    vencedor = random.choice([interaction.user, membro])
    await interaction.response.send_message(f"⚔️ **X1 DA SEITA:** {interaction.user.mention} vs {membro.mention}\n🏆 Vencedor: **{vencedor.mention}**!")

@bot.tree.command(name="abraçar", description="[MEMBROS] Abraçar - DIVERSÃO")
async def abracar_cmd(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.send_message(f"🤗 {interaction.user.mention} abraçou {membro.mention}! Seita é família! 🖤")

@bot.tree.command(name="tapa", description="[MEMBROS] Tapa - ZOEIRA")
async def tapa_cmd(interaction: discord.Interaction, membro: discord.Member):
    await interaction.response.send_message(f"👋 {interaction.user.mention} deu um tapa no {membro.mention}! Toma! 😂")

@bot.tree.command(name="ship", description="[MEMBROS] Shippar - DIVERSÃO")
async def ship_cmd(interaction: discord.Interaction, pessoa1: discord.Member, pessoa2: discord.Member):
    porcent = random.randint(0,100)
    msg = "💖 Casal perfeito!" if porcent>80 else "😏 Tem futuro!" if porcent>50 else "🤔 Talvez..." if porcent>20 else "💀 Não rola!"
    await interaction.response.send_message(f"💘 **SHIP:** {pessoa1.mention} + {pessoa2.mention} = {porcent}%!\n{msg}")

@bot.tree.command(name="coinflip", description="[MEMBROS] Cara ou coroa - DIVERSÃO DANK")
async def coinflip_cmd(interaction: discord.Interaction, quantia: int, escolha: str):
    if quantia<=0 or carteira[interaction.user.id]<quantia: await interaction.response.send_message(f"❌ Sem grana! R$ {carteira[interaction.user.id]}", ephemeral=True); return
    res = random.choice(["cara","coroa"])
    if escolha.lower()==res: carteira[interaction.user.id]+=quantia; await interaction.response.send_message(f"🪙 Deu {res}! Ganhou R$ {quantia}!")
    else: carteira[interaction.user.id]-=quantia; await interaction.response.send_message(f"🪙 Deu {res}! Perdeu R$ {quantia}!")

@coinflip_cmd.autocomplete("escolha")
async def cf_auto(interaction, current): return [app_commands.Choice(name=c, value=c) for c in ["cara","coroa"] if current.lower() in c]

@bot.tree.command(name="slots", description="[MEMBROS] Caça níquel - DIVERSÃO DANK")
async def slots_cmd(interaction: discord.Interaction, quantia: int):
    if quantia<=0 or carteira[interaction.user.id]<quantia: await interaction.response.send_message("❌ Sem grana!", ephemeral=True); return
    emojis = ["🍒","🍋","🍊","💎","7️⃣","👑"]
    r = [random.choice(emojis) for _ in range(3)]
    txt = " | ".join(r)
    if r[0]==r[1]==r[2]: ganho=quantia*5; carteira[interaction.user.id]+=ganho; await interaction.response.send_message(f"🎰 {txt}\n💰 JACKPOT R$ {ganho}!")
    elif r[0]==r[1] or r[1]==r[2]: carteira[interaction.user.id]+=quantia; await interaction.response.send_message(f"🎰 {txt}\n😎 Ganhou R$ {quantia}!")
    else: carteira[interaction.user.id]-=quantia; await interaction.response.send_message(f"🎰 {txt}\n😭 Perdeu R$ {quantia}!")

@bot.tree.command(name="afk", description="[MEMBROS] AFK - DIVERSÃO")
async def afk_cmd(interaction: discord.Interaction, motivo: str="AFK"):
    afk[interaction.user.id]=motivo; await interaction.response.send_message(f"💤 {interaction.user.mention} AFK: {motivo}")

@bot.tree.command(name="rep", description="[MEMBROS] Dar rep - DIVERSÃO")
async def rep_cmd(interaction: discord.Interaction, membro: discord.Member):
    if membro.id==interaction.user.id: await interaction.response.send_message("❌ Não pode rep si!", ephemeral=True); return
    cd = check_cd(interaction.user.id, "rep", 3600)
    if cd: await interaction.response.send_message(f"⏳ {cd//60}min", ephemeral=True); return
    rep[membro.id]+=1; await interaction.response.send_message(f"⭐ {interaction.user.mention} deu rep pra {membro.mention}! Total {rep[membro.id]}")

@bot.tree.command(name="clima", description="[MEMBROS] Clima da Seita - INFO")
async def clima_cmd(interaction: discord.Interaction):
    g = interaction.guild; total = sum(len(v) for v in inventario.values())
    emb = discord.Embed(title="🌤️ Clima Seita - BOT PERFEITO", description=f"Membros: {g.member_count}\nPeixes: {total}\nAnti Raid: Ativo no <#{CANAL_ANTIRAID}>\nSegurança: Wick + Carl + Ticket\nDiversão: Dank + Mudae + Carl\nChefe: Cristino 👑\nBot: Perfeito sem JSON!", color=0x00ffff)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="ia", description="[MEMBROS] IA da Seita - COMANDO CJ")
async def ia_cmd(interaction: discord.Interaction, pergunta: str):
    if interaction.channel.id!= CANAL_BOT and not is_adm(interaction): await interaction.response.send_message(f"❌ Só no <#{CANAL_BOT}>!", ephemeral=True); return
    await interaction.response.defer()
    pl = pergunta.lower()
    if "loritta" in pl: resp = "🤖 Loritta? Bot perfeito tem 800 linhas sem lag! Seita superior!"
    elif "vasco" in pl: resp = "🤖 VASCÃO! 🖤🤍 Time da Seita!"
    elif "cristino" in pl: resp = "🤖 Cristino fez o bot perfeito que nunca precisa atualizar! 👑"
    elif "raid" in pl or "segurança" in pl: resp = f"🤖 Segurança: anti raid no <#{CANAL_ANTIRAID}>, lock, blacklist, isca! Tudo protegido! 🛡️"
    else: resp = random.choice([f"🤖 '{pergunta}' = Seita aprova! 👁️", f"🤖 '{pergunta}' é mais raro que Cristino Dourado! 👑", f"🤖 Bot perfeito diz: {pergunta} = VASCO! 🖤🤍"])
    emb = discord.Embed(title="🤖 IA Seita - BOT PERFEITO", color=0x9b59b6); emb.add_field(name=f"❓ {interaction.user.display_name}:", value=pergunta, inline=False); emb.add_field(name="💬 CJ:", value=resp, inline=False); await interaction.followup.send(embed=emb)

# PESCA SIMPLES - SEM APROFUNDAR
@bot.tree.command(name="pescar", description="[MEMBROS] Pescar simples")
async def pescar_cmd(interaction: discord.Interaction):
    if interaction.channel.id!= CANAL_PESCA: await interaction.response.send_message(f"❌ Só no <#{CANAL_PESCA}>!", ephemeral=True); return
    agora = datetime.now(timezone.utc); ultimo = pesca_cd.get(interaction.user.id)
    if ultimo and (agora-ultimo).total_seconds()<3: await interaction.response.send_message(f"⏳ {int(3-(agora-ultimo).total_seconds())}s!", ephemeral=True); return
    pesca_cd[interaction.user.id]=agora
    peixe = random.choices(peixes_simples, weights=[30,25,15,5,1], k=1)[0]
    inventario[interaction.user.id].append(peixe); carteira[interaction.user.id]+=peixe["preco"]
    upou, old, new = add_xp(interaction.user.id, peixe["xp"])
    if upou: await dar_cargo_level(interaction.user, new)
    emb = discord.Embed(title="🎣 Pescou! Simples", description=f"{peixe['emoji']} **{peixe['nome']}**\nR$ {peixe['preco']} +{peixe['xp']} XP", color=peixe["cor"])
    if upou: emb.add_field(name="LEVEL UP!", value=f"{old} -> {new}!")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="inventario", description="[MEMBROS] Inventário")
async def inventario_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; inv = inventario[membro.id]
    if not inv: await interaction.response.send_message(f"{membro.mention} sem peixes! /pescar", ephemeral=True); return
    from collections import Counter; cont = Counter([p["nome"] for p in inv])
    desc = "\n".join([f"{next(x['emoji'] for x in peixes_simples if x['nome']==n)} {n} x{q}" for n,q in cont.items()])
    total = sum(p["preco"] for p in inv)
    emb = discord.Embed(title=f"Inventário {membro.display_name}", description=desc, color=0x3498db); emb.set_footer(text=f"Total {len(inv)} | R$ {total}"); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="carteira", description="[MEMBROS] Carteira")
async def carteira_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; await interaction.response.send_message(f"💰 {membro.mention} R$ {carteira[membro.id]} | Peixes {len(inventario[membro.id])} | Rep {rep[membro.id]}")

@bot.tree.command(name="daily", description="[MEMBROS] Daily")
async def daily_cmd(interaction: discord.Interaction):
    agora=datetime.now(timezone.utc); ultimo=daily.get(interaction.user.id)
    if ultimo and (agora-ultimo).total_seconds()<86400: await interaction.response.send_message(f"Já pegou! {int(86400-(agora-ultimo).total_seconds())//3600}h", ephemeral=True); return
    daily[interaction.user.id]=agora; premio=random.randint(100,300); carteira[interaction.user.id]+=premio; await interaction.response.send_message(f"🎁 +R$ {premio}!")

@bot.tree.command(name="perfil", description="[MEMBROS] Perfil")
async def perfil_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level[membro.id]
    emb=discord.Embed(title=f"Perfil {membro.display_name} - BOT PERFEITO", color=membro.color or 0x00ffff); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="Level", value=f"{data['level']} - {data['xp']} XP", inline=True)
    emb.add_field(name="Grana", value=f"R$ {carteira[membro.id]}", inline=True)
    emb.add_field(name="Rep", value=f"{rep[membro.id]} ⭐", inline=True)
    emb.add_field(name="Peixes", value=f"{len(inventario[membro.id])}", inline=True)
    emb.add_field(name="Seita", value="Membro da Seita 👁️", inline=True)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="ajuda", description="📜 Menu BOT PERFEITO FINAL")
async def ajuda_cmd(interaction: discord.Interaction):
    emb=discord.Embed(title="🤖 CJ BOT PERFEITO FINAL - 800+ LINHAS - BASEADO EM TUDO", description="**Baseado em Wick, Carl, Dank, Mudae, Ticket Tool, Loritta, Poketwo!** Sem focar em pesca, com segurança e diversão!", color=0x00ff00)
    emb.add_field(name="🛡️ SEGURANÇA ADM - 20 cmds (ephemeral - só ADM vê erro)", value="/ban /unban /kick /timeout /untimeout /warn /clear /lock /unlock /slowmode /dar_cargo /tirar_cargo /permissao /anuncio /falar_como_cj /fake_ban /blacklist_add /blacklist_remove /antiraid_on /antiraid_off /dar_grana /set_level\n**Canal Anti Raid:** <#1559066250410197013> - Isca bane automatico!", inline=False)
    emb.add_field(name="🎲 DIVERSÃO MEMBROS - 20+ cmds - SEM LACRAR - COMANDOS CJ", value="/seita /cj_fala /vasco /8ball /roleta /x1 /abraçar /tapa /ship /coinflip /slots /clima /ia /afk /rep /pescar /inventario /carteira /daily /perfil\n**Falas CJ:** 15 falas da Seita sem lacrar", inline=False)
    emb.add_field(name="👑 BOT PERFEITO", value="Sem JSON | Sem save | 568 linhas git | 800+ total | Baseado em tudo | Segurança + Diversão | Nunca mais atualiza!", inline=False)
    await interaction.response.send_message(embed=emb, ephemeral=True)

@bot.command(name="cj")
async def cj_cmd(ctx):
    try: await ctx.message.delete()
    except: pass
    try: await ctx.send(f"{ctx.author.mention} Usa **/ajuda** no <#{CANAL_BOT}>! 🤖 BOT PERFEITO FINAL!", delete_after=5)
    except: pass

bot.run(TOKEN)
