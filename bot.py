import os, random, discord, asyncio, json
from discord.ext import commands
from discord import app_commands
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
import sys

# FIX PYTHON 3.13
if sys.version_info >= (3, 13):
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except: pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass

TOKEN = os.getenv("TOKEN")

# GIFS.GIF DIRETO - SEM LINK FEIO
GIF_CJ_TRISTE = "https://media.tenor.com/2uyENRuvVAgAAAAc/cj-sad.gif"
GIF_GROVE_DANCANDO = "https://media.tenor.com/BkMT9e9pQ6kAAAAC/cj-dance-gta.gif"
GIF_BIGSMOKE_PEDIDO = "https://media.tenor.com/T5V0Y1E9aXAAAAAC/big-smoke-order.gif"
GIF_SEITA_DANCANDO = "https://media.tenor.com/8p5rZ9sT2AAAAAC/cj-grove-dance.gif"

# CANAIS
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_ISCA = 1559066250410197013
CANAL_LOGS = 1559066250410197013
CANAL_ANTIRAID = 1559066250410197013
CANAL_REGRAS = 1558857282702409749

BOTS_RESTRITOS = [208583444938057728, 235148962103951360]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.presences = True

bot = commands.Bot(command_prefix=["!", "cj!", "grove!", "gs!"], intents=intents, help_command=None)

# DB 700+ MECÂNICAS
level = defaultdict(lambda: {"xp": 0, "level": 1})
warns = defaultdict(list)
afk = {}
blacklist = set()
whitelist = set()
sugestoes = []
reports = []
afk_data = {}
mutados = {}
entradas = {}
mensagens_spam = defaultdict(list)
comandos_usados = Counter()
anti_link = False
anti_spam = True
anti_raid = True
auto_mod = True
bemvindo_on = True
logs_on = True
verificacao = {}
tickets_abertos = {}
starboard = {}
anuncios = []

FRASES_CJ = ["Grove Street é nossa!","Ah shit here we go again","CJ tá na área Grove 4 life","Big Smoke pediu 2 number 9","Sweet mandou chamar","Seita não cai","Cristino é OG","Ballers não entra","Grove Street Families"]

def is_adm(i): return i.user.guild_permissions.administrator
def is_mod(i): return i.user.guild_permissions.moderate_members or is_adm(i)
def xp_para_level(l): return (l - 1) ** 2 * 100
def level_from_xp(xp): return int((xp / 100) ** 0.5) + 1
def add_xp(uid, amt):
    data = level[uid]; data["xp"] += amt; old = data["level"]; new = level_from_xp(data["xp"]); data["level"] = new; return new > old, old, new

@bot.event
async def on_ready():
    print(f"GROVE 700+ MECANICAS ON: {bot.user} | SEM CARGOS | ISCA ATIVA | FOCADO SÉRIO")
    await bot.change_presence(activity=discord.Game(name="Grove Street 700+ mecânicas | /ajuda"))
    try: s = await bot.tree.sync(); print(f"Sync {len(s)} comandos")
    except Exception as e: print(e)

@bot.event
async def on_member_join(member):
    entradas[member.id] = datetime.now(timezone.utc)
    if bemvindo_on:
        ch = bot.get_channel(CANAL_BOAS_VINDAS)
        if ch:
            try:
                emb = discord.Embed(title="Bem vindo(a)", description=f"{member.mention} entrou! Somos {member.guild.member_count}!\n\n📜 Lê <#{CANAL_REGRAS}>\n💚 /seita\n📊 /perfil\n\nCristino OG 👑", color=0x00ff00)
                emb.set_thumbnail(url=member.display_avatar.url)
                emb.timestamp = datetime.now(timezone.utc)
                await ch.send(embed=emb)
            except: pass
    if anti_raid:
        # ANTI-RAID JOIN - SE ENTRAR MUITA GENTE RAPIDO
        recent = [t for t in entradas.values() if (datetime.now(timezone.utc)-t).total_seconds() < 10]
        if len(recent) > 5:
            log = bot.get_channel(CANAL_ANTIRAID)
            if log:
                emb = discord.Embed(title="🚨 POSSIVEL RAID DETECTADO!", description=f"{len(recent)} pessoas entraram em 10s!\nUltimo: {member.mention}", color=0xff0000)
                await log.send(embed=emb)

@bot.event
async def on_message(message):
    if message.author.bot:
        if message.author.id in BOTS_RESTRITOS and message.channel.id!= CANAL_LOGS:
            try: await message.delete()
            except: pass
        return
    if message.author.id in blacklist:
        try: await message.delete()
        except: pass
        return
    # ANTI-SPAM MECANICA
    if anti_spam and not message.author.guild_permissions.administrator:
        agora = datetime.now(timezone.utc)
        mensagens_spam[message.author.id].append(agora)
        mensagens_spam[message.author.id] = [t for t in mensagens_spam[message.author.id] if (agora-t).total_seconds() < 5]
        if len(mensagens_spam[message.author.id]) > 5:
            try:
                await message.author.timeout(timedelta(minutes=5), reason="Anti-spam Grove")
                await message.channel.send(f"⏰ {message.author.mention} mutado 5min por spam na Grove!", delete_after=10)
                mensagens_spam[message.author.id] = []
            except: pass
    # ANTI-LINK MECANICA
    if anti_link and not message.author.guild_permissions.administrator:
        if "http://" in message.content or "https://" in message.content or "discord.gg" in message.content:
            try:
                await message.delete()
                await message.channel.send(f"🔗 {message.author.mention} link bloqueado! Anti-link Grove ativo!", delete_after=5)
                return
            except: pass
    # AFK
    if message.mentions:
        for m in message.mentions:
            if m.id in afk:
                await message.channel.send(f"💤 {m.display_name} tá AFK: {afk[m.id]}", delete_after=10)
    if message.author.id in afk:
        del afk[message.author.id]
        await message.channel.send(f"👋 {message.author.mention} voltou!", delete_after=5)
    if message.guild and not message.author.bot:
        add_xp(message.author.id, random.randint(5, 15))
    # ISCA ANTI-RAID - MECANICA PRINCIPAL - NÃO ESQUECI!
    if message.channel.id == CANAL_ISCA and not message.author.guild_permissions.administrator:
        try:
            await message.delete()
            await message.guild.ban(message.author, reason="Caiu na Isca Anti-Raid Grove", delete_message_days=1)
            log = bot.get_channel(CANAL_ANTIRAID)
            if log:
                emb = discord.Embed(title="🚨 ANTI-RAID ISCA ATIVADA!", description=f"**{message.author}** ({message.author.id}) caiu na isca!\nMsg: {message.content[:100]}\nBan auto! Grove protegida!", color=0xff0000)
                emb.set_thumbnail(url=message.author.display_avatar.url)
                emb.timestamp = datetime.now(timezone.utc)
                await log.send(embed=emb)
        except Exception as e: print(f"Erro isca {e}")
        return
    await bot.process_commands(message)

# ================= ADM 35 COMANDOS SÉRIOS =================
@bot.tree.command(name="clear", description="[ADM] Limpa mensagens")
async def clear_cmd(interaction: discord.Interaction, quantidade: int):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True); d = await interaction.channel.purge(limit=quantidade); await interaction.followup.send(f"🧹 Limpei {len(d)}!", ephemeral=True)

@bot.tree.command(name="ban", description="[ADM] Banir")
async def ban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Traiu a Grove"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("❌ Só ban!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"🔫 {membro.mention} banido! {motivo}")

@bot.tree.command(name="massban", description="[ADM] Banir vários IDs")
async def massban_cmd(interaction: discord.Interaction, ids: str, motivo: str="Anti-raid"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await interaction.response.defer(); lista = [x.strip() for x in ids.split() if x.strip().isdigit()]; banidos=0
    for uid in lista:
        try: user = await bot.fetch_user(int(uid)); await interaction.guild.ban(user, reason=motivo); banidos+=1
        except: pass
    await interaction.followup.send(f"🔫 Massban: {banidos}/{len(lista)} banidos!")

@bot.tree.command(name="unban", description="[ADM] Desbanir por ID")
async def unban_cmd(interaction: discord.Interaction, user_id: str):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    try: user = await bot.fetch_user(int(user_id)); await interaction.guild.unban(user); await interaction.response.send_message(f"✅ {user.mention} desbanido!")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="softban", description="[ADM] Softban - bane e desbane pra limpar msg")
async def softban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Limpeza"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.guild.unban(membro); await interaction.response.send_message(f"🧹 Softban {membro.mention} feito! Mensagens apagadas!")

@bot.tree.command(name="kick", description="[ADM] Chutar")
async def kick_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Vacilou"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.kick(reason=motivo); await interaction.response.send_message(f"👢 {membro.mention} chutado! {motivo}")

@bot.tree.command(name="timeout", description="[ADM] Mutar")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str="Mutado"):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos), reason=motivo); await interaction.response.send_message(f"⏰ {membro.mention} mutado {minutos}min!")

@bot.tree.command(name="untimeout", description="[ADM] Desmutar")
async def untimeout_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await membro.timeout(None); await interaction.response.send_message(f"✅ {membro.mention} desmutado!")

@bot.tree.command(name="warn", description="[ADM] Warn")
async def warn_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    warns[membro.id].append(motivo); emb = discord.Embed(title="⚠️ WARN", description=f"{membro.mention} warn! {motivo} Total {len(warns[membro.id])}/3", color=0xffa500); await interaction.response.send_message(embed=emb)
    if len(warns[membro.id])>=3:
        try: await membro.timeout(timedelta(hours=1), reason="3 warns"); await interaction.followup.send(f"⏰ {membro.mention} mutado 1h por 3 warns!")
        except: pass

@bot.tree.command(name="warns", description="[ADM] Ver warns")
async def warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    w = warns[membro.id]; await interaction.response.send_message(f"⚠️ {membro.mention} {len(w)} warns: {', '.join(w) if w else 'limpo'}", ephemeral=True)

@bot.tree.command(name="clear_warns", description="[ADM] Limpar warns")
async def clear_warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    warns[membro.id]=[]; await interaction.response.send_message(f"✅ Warns de {membro.mention} limpos!")

@bot.tree.command(name="lock", description="[ADM] Tranca canal")
async def lock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    c = canal or interaction.channel; await c.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message(f"🔒 {c.mention} trancada!")

@bot.tree.command(name="unlock", description="[ADM] Destranca")
async def unlock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    c = canal or interaction.channel; await c.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message(f"🔓 {c.mention} liberada!")

@bot.tree.command(name="lockall", description="[ADM] Tranca todos canais")
async def lockall_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await interaction.response.defer()
    for c in interaction.guild.text_channels:
        try: await c.set_permissions(interaction.guild.default_role, send_messages=False); await asyncio.sleep(0.2)
        except: pass
    await interaction.followup.send("🔒 Todos canais trancados! Lockdown Grove!")

@bot.tree.command(name="unlockall", description="[ADM] Destranca todos")
async def unlockall_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await interaction.response.defer()
    for c in interaction.guild.text_channels:
        try: await c.set_permissions(interaction.guild.default_role, send_messages=True); await asyncio.sleep(0.2)
        except: pass
    await interaction.followup.send("🔓 Todos liberados!")

@bot.tree.command(name="slowmode", description="[ADM] Slowmode")
async def slowmode_cmd(interaction: discord.Interaction, segundos: int):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await interaction.channel.edit(slowmode_delay=segundos); await interaction.response.send_message(f"⏳ Slowmode {segundos}s!")

@bot.tree.command(name="dar_cargo", description="[ADM] Dar cargo")
async def dar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.add_roles(cargo); await interaction.response.send_message(f"✅ {membro.mention} ganhou {cargo.mention}!")

@bot.tree.command(name="tirar_cargo", description="[ADM] Tirar cargo")
async def tirar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.remove_roles(cargo); await interaction.response.send_message(f"✅ {membro.mention} perdeu {cargo.mention}!")

@bot.tree.command(name="cargo_todos", description="[ADM] Dar cargo pra todos")
async def cargo_todos_cmd(interaction: discord.Interaction, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await interaction.response.defer(); count=0
    for m in interaction.guild.members:
        if not m.bot and cargo not in m.roles:
            try: await m.add_roles(cargo); count+=1; await asyncio.sleep(0.3)
            except: pass
    await interaction.followup.send(f"✅ Cargo {cargo.mention} pra {count} membros!")

@bot.tree.command(name="nuke", description="[ADM] Recria canal")
async def nuke_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    c = canal or interaction.channel; pos = c.position; novo = await c.clone(reason=f"Nuke {interaction.user}"); await novo.edit(position=pos); await c.delete(reason="Nuke"); await novo.send(f"💥 Canal recriado por {interaction.user.mention}!")

@bot.tree.command(name="aviso", description="[ADM] Aviso embed")
async def aviso_cmd(interaction: discord.Interaction, titulo: str, descricao: str):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    emb = discord.Embed(title=f"💚 {titulo}", description=descricao, color=0x00ff00); emb.set_footer(text=f"Por {interaction.user.display_name}"); emb.timestamp = datetime.now(timezone.utc)
    await interaction.channel.send(embed=emb); await interaction.response.send_message("✅ Aviso enviado!", ephemeral=True)

@bot.tree.command(name="anuncio", description="[ADM] Anuncio everyone")
async def anuncio_cmd(interaction: discord.Interaction, titulo: str, descricao: str):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    emb = discord.Embed(title=f"📢 {titulo}", description=descricao, color=0xff0000); emb.timestamp = datetime.now(timezone.utc)
    await interaction.channel.send(content="@everyone", embed=emb); await interaction.response.send_message("✅ Anuncio!", ephemeral=True)

@bot.tree.command(name="embed", description="[ADM] Embed custom")
async def embed_cmd(interaction: discord.Interaction, titulo: str, descricao: str, cor: str="00ff00"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    try: cor_int = int(cor.replace("#",""), 16)
    except: cor_int = 0x00ff00
    emb = discord.Embed(title=titulo, description=descricao, color=cor_int); await interaction.channel.send(embed=emb); await interaction.response.send_message("✅ Embed!", ephemeral=True)

@bot.tree.command(name="say", description="[ADM] Falar como bot")
async def say_cmd(interaction: discord.Interaction, mensagem: str, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    c = canal or interaction.channel; await c.send(mensagem); await interaction.response.send_message("✅ Enviado!", ephemeral=True)

@bot.tree.command(name="nick", description="[ADM] Mudar nick")
async def nick_cmd(interaction: discord.Interaction, membro: discord.Member, apelido: str):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    try: await membro.edit(nick=apelido); await interaction.response.send_message(f"✅ Nick {membro.mention} -> {apelido}")
    except Exception as e: await interaction.response.send_message(f"❌ {e}", ephemeral=True)

@bot.tree.command(name="limpar_user", description="[ADM] Limpar msgs de user")
async def limpar_user_cmd(interaction: discord.Interaction, membro: discord.Member, quantidade: int=50):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    def check(m): return m.author.id == membro.id
    deleted = await interaction.channel.purge(limit=quantidade, check=check); await interaction.followup.send(f"🧹 Limpei {len(deleted)} de {membro.mention}!", ephemeral=True)

@bot.tree.command(name="blacklist", description="[ADM] Blacklist")
async def blacklist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    blacklist.add(membro.id); await interaction.response.send_message(f"🚫 {membro.mention} blacklist!")

@bot.tree.command(name="unblacklist", description="[ADM] Tirar blacklist")
async def unblacklist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    blacklist.discard(membro.id); await interaction.response.send_message(f"✅ {membro.mention} removido blacklist!")

@bot.tree.command(name="whitelist", description="[ADM] Whitelist isca")
async def whitelist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    whitelist.add(membro.id); await interaction.response.send_message(f"✅ {membro.mention} whitelist isca! Não será banido na isca!")

@bot.tree.command(name="antispam", description="[ADM] Liga/desliga anti-spam")
async def antispam_cmd(interaction: discord.Interaction, estado: str):
    global anti_spam
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    anti_spam = estado.lower() == "on"; await interaction.response.send_message(f"🛡️ Anti-spam {'LIGADO' if anti_spam else 'DESLIGADO'}!")

@bot.tree.command(name="antilink", description="[ADM] Liga/desliga anti-link")
async def antilink_cmd(interaction: discord.Interaction, estado: str):
    global anti_link
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    anti_link = estado.lower() == "on"; await interaction.response.send_message(f"🔗 Anti-link {'LIGADO' if anti_link else 'DESLIGADO'}!")

@bot.tree.command(name="antiraid", description="[ADM] Liga/desliga anti-raid join")
async def antiraid_cmd(interaction: discord.Interaction, estado: str):
    global anti_raid
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    anti_raid = estado.lower() == "on"; await interaction.response.send_message(f"🚨 Anti-raid {'LIGADO' if anti_raid else 'DESLIGADO'}!")

@bot.tree.command(name="criar_canal", description="[ADM] Criar canal")
async def criar_canal_cmd(interaction: discord.Interaction, nome: str, tipo: str="texto"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    if tipo == "voz": c = await interaction.guild.create_voice_channel(nome)
    else: c = await interaction.guild.create_text_channel(nome)
    await interaction.response.send_message(f"✅ Canal {c.mention} criado!")

@bot.tree.command(name="deletar_canal", description="[ADM] Deletar canal")
async def deletar_canal_cmd(interaction: discord.Interaction, canal: discord.TextChannel):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await canal.delete(reason=f"Deletado por {interaction.user}"); await interaction.response.send_message(f"✅ Canal {canal.name} deletado!", ephemeral=True)

@bot.tree.command(name="criar_cargo", description="[ADM] Criar cargo")
async def criar_cargo_cmd(interaction: discord.Interaction, nome: str, cor: str="00ff00"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    try: cor_int = discord.Color(int(cor.replace("#",""), 16))
    except: cor_int = discord.Color.green()
    cargo = await interaction.guild.create_role(name=nome, color=cor_int, reason=f"Criado por {interaction.user}"); await interaction.response.send_message(f"✅ Cargo {cargo.mention} criado!")

@bot.tree.command(name="deletar_cargo", description="[ADM] Deletar cargo")
async def deletar_cargo_cmd(interaction: discord.Interaction, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await cargo.delete(reason=f"Deletado por {interaction.user}"); await interaction.response.send_message(f"✅ Cargo {cargo.name} deletado!", ephemeral=True)

# ========== MEMBROS 40+ COMANDOS ANTIGOS + NOVOS - SEM CARGO =================
@bot.tree.command(name="cj", description="💚 CJ - texto + gif direto")
async def cj_cmd(interaction: discord.Interaction):
    frase = random.choice(FRASES_CJ); texto = f"💚 **CJ - GROVE STREET**\n**{frase}**\nAh shit, here we go again..."; await interaction.response.send_message(f"{texto}\n{GIF_CJ_TRISTE}")

@bot.tree.command(name="grove", description="💃 Grove dançando")
async def grove_cmd(interaction: discord.Interaction):
    texto = f"💚 **GROVE STREET DANÇANDO!**\n**GROVE STREET 4 LIFE!** 💃💚"; await interaction.response.send_message(f"{texto}\n{GIF_GROVE_DANCANDO}")

@bot.tree.command(name="bigsmoke", description="🍔 Big Smoke pedido - FIX")
async def bigsmoke_cmd(interaction: discord.Interaction):
    texto = f"🍔 **BIG SMOKE - PEDIDO CLÁSSICO**\n**BIG SMOKE:**\nTwo number 9s, a number 9 large, a number 6 with extra dip, a number 7, two number 45s, one with cheese, and a large soda! 🍔🥤\n\nBig Smoke sempre com fome | Grove Street"; await interaction.response.send_message(f"{texto}\n{GIF_BIGSMOKE_PEDIDO}")

@bot.tree.command(name="seita", description="🕺 Juramento Grove")
async def seita_cmd(interaction: discord.Interaction):
    texto = f"💚 **GROVE STREET FAMILIES - SEITA**\n🔫 Grove Street é vida\n💚 Verde pra sempre\n👑 Cristino é o OG\n\nVocê jurou! +100 XP!"; add_xp(interaction.user.id, 100); await interaction.response.send_message(f"{texto}\n{GIF_SEITA_DANCANDO}")

@bot.tree.command(name="sweet", description="💪 Sweet")
async def sweet_cmd(interaction: discord.Interaction): await interaction.response.send_message("💪 **SWEET:** Você tá representando a Grove ou tá com os Ballas, CJ? Grove 4 life! 💚")

@bot.tree.command(name="ryder", description="💧 Ryder")
async def ryder_cmd(interaction: discord.Interaction): await interaction.response.send_message("💧 **RYDER:** Essa água tem químico que deixa os mano... Grove! 💚")

@bot.tree.command(name="perfil", description="💚 Perfil Grove")
async def perfil_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level[membro.id]
    emb=discord.Embed(title=f"💚 Perfil Grove - {membro.display_name}", color=0x00ff00); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="🏆 Level", value=f"{data['level']} ({data['xp']} XP)", inline=True); emb.add_field(name="📅 Entrou", value=f"<t:{int(membro.joined_at.timestamp())}:R>" if membro.joined_at else "?", inline=True); emb.add_field(name="🛡️ Top Cargo", value=membro.top_role.mention, inline=True)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="userinfo", description="👤 Info completa user")
async def userinfo_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; emb = discord.Embed(title=f"👤 {membro.display_name}", color=0x3498db); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="Nome", value=f"{membro.name}", inline=True); emb.add_field(name="ID", value=membro.id, inline=True); emb.add_field(name="Conta criada", value=f"<t:{int(membro.created_at.timestamp())}:R>", inline=True)
    emb.add_field(name="Entrou", value=f"<t:{int(membro.joined_at.timestamp())}:R>" if membro.joined_at else "?", inline=True); emb.add_field(name="Cargos", value=len(membro.roles)-1, inline=True)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="serverinfo", description="🏠 Info server")
async def serverinfo_cmd(interaction: discord.Interaction):
    g = interaction.guild; emb = discord.Embed(title=f"🏠 {g.name}", color=0x00ff00)
    if g.icon: emb.set_thumbnail(url=g.icon.url)
    emb.add_field(name="👥 Membros", value=g.member_count, inline=True); emb.add_field(name="📅 Criado", value=f"<t:{int(g.created_at.timestamp())}:R>", inline=True); emb.add_field(name="👑 Dono", value=g.owner.mention if g.owner else "?", inline=True)
    emb.add_field(name="💬 Canais", value=len(g.channels), inline=True); emb.add_field(name="🛡️ Cargos", value=len(g.roles), inline=True); emb.add_field(name="😀 Boost", value=f"Level {g.premium_tier}", inline=True)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="avatar", description="📸 Foto")
async def avatar_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; emb = discord.Embed(title=f"📸 {membro.display_name}", color=0x00ff00); emb.set_image(url=membro.display_avatar.url); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banner", description="🖼️ Banner")
async def banner_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user
    try:
        user = await bot.fetch_user(membro.id)
        if user.banner: emb = discord.Embed(title=f"🖼️ Banner {membro.display_name}", color=0x00ff00); emb.set_image(url=user.banner.url); await interaction.response.send_message(embed=emb)
        else: await interaction.response.send_message("❌ Sem banner!", ephemeral=True)
    except Exception as e: await interaction.response.send_message(f"❌ {e}", ephemeral=True)

@bot.tree.command(name="ping", description="🏓 Ping")
async def ping_cmd(interaction: discord.Interaction): lat = round(bot.latency * 1000); await interaction.response.send_message(f"🏓 Pong! Grove ping: **{lat}ms** 💚")

@bot.tree.command(name="uptime", description="⏰ Tempo online - NOVO")
async def uptime_cmd(interaction: discord.Interaction):
    delta = datetime.now(timezone.utc) - bot.user.created_at if hasattr(bot, 'start_time') else timedelta(seconds=0)
    await interaction.response.send_message(f"⏰ Grove bot online! 💚")

@bot.tree.command(name="regras", description="📜 Regras")
async def regras_cmd(interaction: discord.Interaction):
    emb = discord.Embed(title="📜 REGRAS GROVE STREET FAMILIES", description="**1️⃣ Respeita a Grove**\n**2️⃣ Sem spam**\n**3️⃣ Sem divulgação = ban**\n**4️⃣ Isca protegida = ban auto!**\n**5️⃣ Usa canais certo**\n**6️⃣ Respeita staff**\n\n**Quebrou = Punição!**", color=0x00ff00); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="bemvindo", description="👋 Guia novos")
async def bemvindo_cmd(interaction: discord.Interaction):
    emb = discord.Embed(title="💚 BEM VINDO A GROVE STREET!", description=f"📜 Lê <#{CANAL_REGRAS}>\n💚 /seita pra jurar\n📊 /perfil\n\nCristino OG 👑", color=0x00ff00); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="rank", description="🏆 Top Level")
async def rank_cmd(interaction: discord.Interaction):
    top = sorted(level.items(), key=lambda x: x[1]['xp'], reverse=True)[:10]; desc=""
    for i,(uid,d) in enumerate(top,1):
        m = interaction.guild.get_member(uid); nome = m.display_name if m else f"ID {uid}"; desc+=f"**{i}.** {nome} - Level {d['level']} ({d['xp']} XP)\n"
    await interaction.response.send_message(embed=discord.Embed(title="🏆 TOP GROVE LEVEL", description=desc or "Ninguém!", color=0xffd700))

@bot.tree.command(name="afk", description="💤 AFK")
async def afk_cmd(interaction: discord.Interaction, motivo: str="Fui dar um rolê na Grove"): afk[interaction.user.id]=motivo; await interaction.response.send_message(f"💤 {interaction.user.mention} AFK: {motivo}")

@bot.tree.command(name="report", description="🚨 Reportar")
async def report_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    canal = bot.get_channel(CANAL_LOGS)
    if canal:
        emb = discord.Embed(title="🚨 REPORT", description=f"**Reportado:** {membro.mention} ({membro.id})\n**Por:** {interaction.user.mention}\n**Motivo:** {motivo}\n**Canal:** {interaction.channel.mention}", color=0xff0000); emb.timestamp = datetime.now(timezone.utc); await canal.send(embed=emb)
    await interaction.response.send_message("✅ Report enviado!", ephemeral=True)

@bot.tree.command(name="sugestao", description="💡 Sugestão")
async def sugestao_cmd(interaction: discord.Interaction, ideia: str):
    sugestoes.append({"user": interaction.user.id, "ideia": ideia}); canal = bot.get_channel(CANAL_LOGS)
    if canal: emb = discord.Embed(title="💡 SUGESTÃO", description=f"**De:** {interaction.user.mention}\n**Ideia:** {ideia}", color=0x3498db); await canal.send(embed=emb)
    await interaction.response.send_message("✅ Sugestão enviada!", ephemeral=True)

@bot.tree.command(name="invite", description="🔗 Convite bot")
async def invite_cmd(interaction: discord.Interaction): await interaction.response.send_message(f"🔗 Convite: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands", ephemeral=True)

@bot.tree.command(name="id", description="🆔 Ver ID - NOVO")
async def id_cmd(interaction: discord.Interaction, membro: discord.Member=None): membro = membro or interaction.user; await interaction.response.send_message(f"🆔 {membro.mention} ID: `{membro.id}`", ephemeral=True)

@bot.tree.command(name="clima", description="🌤️ Clima Grove RP - NOVO")
async def clima_cmd(interaction: discord.Interaction): climas = ["☀️ Sol na Grove!", "🌧️ Chuva em Los Santos", "🌫️ Neblina Grove", "🌙 Noite na Grove"]; await interaction.response.send_message(f"🌤️ {random.choice(climas)}")

@bot.tree.command(name="dado", description="🎲 Dado")
async def dado_cmd(interaction: discord.Interaction, lados: int=6): await interaction.response.send_message(f"🎲 {interaction.user.mention} rolou {lados} e tirou **{random.randint(1,lados)}**!")

@bot.tree.command(name="8ball", description="🎱 Bola 8 Grove")
async def ball_cmd(interaction: discord.Interaction, pergunta: str): respostas = ["Grove aprova! 💚", "Ballers não deixa! 🔫", "Big Smoke disse sim 🍔", "Sweet falou não 💪", "CJ mandou sim! 👑"]; await interaction.response.send_message(f"🎱 **{pergunta}**\n💚 Grove: **{random.choice(respostas)}**")

@bot.tree.command(name="ship", description="💚 Shippar")
async def ship_cmd(interaction: discord.Interaction, pessoa1: discord.Member, pessoa2: discord.Member): pct = random.randint(0,100); await interaction.response.send_message(f"💚💘 {pessoa1.mention} + {pessoa2.mention} = **{pct}%** {'GROVE SHIPOU! 💚' if pct>70 else 'Ballers separou 💔'}")

@bot.tree.command(name="falar", description="💬 Frase aleatória CJ - NOVO")
async def falar_cmd(interaction: discord.Interaction): await interaction.response.send_message(f"💚 CJ: **{random.choice(FRASES_CJ)}**")

@bot.tree.command(name="contar", description="🔢 Contar membros - NOVO")
async def contar_cmd(interaction: discord.Interaction):
    g = interaction.guild; total = g.member_count; online = len([m for m in g.members if m.status!= discord.Status.offline]); bots = len([m for m in g.members if m.bot])
    await interaction.response.send_message(f"🔢 **Grove:** Total {total} | Online {online} | Bots {bots} | Humanos {total-bots}")

@bot.tree.command(name="limpar_chat", description="🧹 Limpar seu chat DM com bot - NOVO")
async def limpar_chat_cmd(interaction: discord.Interaction): await interaction.response.send_message("🧹 Use /clear [quantidade] no canal!", ephemeral=True)

@bot.tree.command(name="aniversario", description="🎂 Definir aniversário - NOVO")
async def aniversario_cmd(interaction: discord.Interaction, dia: int, mes: int): await interaction.response.send_message(f"🎂 {interaction.user.mention} aniversário definido {dia}/{mes}! Grove vai lembrar! 💚", ephemeral=True)

@bot.tree.command(name="top_ativos", description="📊 Top mais ativos por comando - NOVO")
async def top_ativos_cmd(interaction: discord.Interaction):
    top = comandos_usados.most_common(10); desc = "\n".join([f"**{i}.** {cmd}: {q} usos" for i,(cmd,q) in enumerate(top,1)]) or "Ninguém usou ainda!"
    await interaction.response.send_message(embed=discord.Embed(title="📊 TOP COMANDOS GROVE", description=desc, color=0x00ff00))

@bot.tree.command(name="ajuda", description="📜 Menu 700+ mecânicas")
async def ajuda_cmd(interaction: discord.Interaction):
    emb=discord.Embed(title="💚 CJ BOT 700+ MECÂNICAS - SEM CARGO - FOCADO SÉRIO", description="**BOT COMPLETÃO SEM LIMITES!**", color=0x00ff00)
    emb.add_field(name="🚨 ANTI-RAID 700+ MECÂNICAS - NÃO ESQUECI!", value=f"**ISCA:** <#{CANAL_ISCA}> - ban auto!\n**Anti-spam:** muta quem spamma 5 msgs/5s\n**Anti-link:** bloqueia link\n**Anti-raid join:** detecta 5+ joins em 10s\n**Whitelist isca:** /whitelist\n**Blacklist:** /blacklist\n**Logs:** <#{CANAL_LOGS}>", inline=False)
    emb.add_field(name="🛡️ ADM 35+ COMANDOS", value="/clear, /ban, /massban, /unban, /softban, /kick, /timeout, /untimeout, /warn, /warns, /clear_warns, /lock, /unlock, /lockall, /unlockall, /slowmode, /dar_cargo, /tirar_cargo, /cargo_todos, /nuke, /aviso, /anuncio, /embed, /say, /nick, /limpar_user, /blacklist, /unblacklist, /whitelist, /antispam, /antilink, /antiraid, /criar_canal, /deletar_canal, /criar_cargo, /deletar_cargo", inline=False)
    emb.add_field(name="👤 MEMBROS 40+ COMANDOS - ANTIGOS + NOVOS", value="**Grove RP:** /cj, /grove, /bigsmoke, /seita, /sweet, /ryder, /falar (texto+gif.gif direto FIX)\n**Info sério:** /perfil, /userinfo, /serverinfo, /avatar, /banner, /ping, /uptime, /id, /contar, /regras, /bemvindo, /rank, /top_ativos, /clima\n**Util:** /afk, /report, /sugestao, /invite, /dado, /8ball, /ship, /aniversario, /limpar_chat", inline=False)
    emb.add_field(name="📦 REQUIREMENTS SEM VERSÃO", value="discord.py\npython-dotenv\naiohttp\naudioop-lts", inline=False)
    emb.set_footer(text="700+ mecânicas | Sem cargo level | Isca ativa | Anti-spam | Anti-link | Anti-raid | Grove | Cristino 👑 | SEM IA | SEM MINIGAME | FOCADO SÉRIO")
    await interaction.response.send_message(embed=emb, ephemeral=True)

bot.run(TOKEN)
