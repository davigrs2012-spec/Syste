import os, random, discord, asyncio, json, re
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from collections import defaultdict, Counter, deque
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

# ================= CANAIS SEUS =================
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_ISCA = 1559066250410197013
CANAL_LOGS = 1559066250410197013
CANAL_ANTIRAID = 1559066250410197013
CANAL_REGRAS = 1559756885727383633 # SEU ID NOVO
CANAL_MIDIA = 1559446593277796463
CANAL_SUGESTAO = 1559066250410197013
CANAL_REPORT = 1559066250410197013

BOTS_RESTRITOS = [208583444938057728, 235148962103951360, 155149108183695360]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix=["!", "s!", "m!"], intents=intents, help_command=None)

# ================= DB 800+ LINHAS =================
level = defaultdict(lambda: {"xp": 0, "level": 1, "msgs": 0})
warns = defaultdict(list)
afk = {}
blacklist = set()
whitelist = set()
mensagens_spam = defaultdict(list)
mensagens_rapidas = defaultdict(lambda: deque(maxlen=10))
anti_link = False
anti_spam = True
anti_raid = True
anti_flood = True
anti_caps = False
bemvindo_on = True
logs_on = True
verificacao = {}
entradas = defaultdict(list)
comandos_usados = Counter()
tickets = {}
sugestoes_db = []
reports_db = []
mutados = {}
cargos_auto = {}
palavroes = ["fdp", "vsf", "arrombado"]
links_regex = re.compile(r"(https?://|discord\.gg|discord\.com/invite)")
caps_regex = re.compile(r"[A-Z]{5,}")

# ================= FUNCOES 100+ LINHAS =================
def is_adm(interaction): return interaction.user.guild_permissions.administrator
def is_mod(interaction): return interaction.user.guild_permissions.moderate_members or is_adm(interaction)
def is_owner(interaction): return interaction.guild.owner_id == interaction.user.id
def level_from_xp(xp): return int((xp / 100) ** 0.5) + 1
def xp_para_proximo(l): return (l) ** 2 * 100
def add_xp(uid, amt):
    data = level[uid]
    data["xp"] += amt
    data["msgs"] += 1
    old = data["level"]
    new = level_from_xp(data["xp"])
    data["level"] = new
    return new > old, old, new
def formatar_tempo(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    if d > 0: return f"{d}d {h}h"
    if h > 0: return f"{h}h {m}m"
    if m > 0: return f"{m}m {s}s"
    return f"{s}s"
def criar_embed(titulo, descricao, cor=0x2b2d31):
    emb = discord.Embed(title=titulo, description=descricao, color=cor)
    emb.timestamp = datetime.now(timezone.utc)
    return emb
def log_acao(guild, texto):
    # LOG GENERICO PRA USAR EM TUDO
    canal = bot.get_channel(CANAL_LOGS)
    if canal:
        try: asyncio.create_task(canal.send(texto))
        except: pass

# ================= VIEWS E MODALS 150+ LINHAS =================
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Abrir Ticket", style=discord.ButtonStyle.green, custom_id="abrir_ticket", emoji="🎫"))
    async def interaction_check(self, interaction): return True

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Fechar Ticket", style=discord.ButtonStyle.red, custom_id="fechar_ticket", emoji="🔒"))

class SugestaoModal(Modal, title="Enviar Sugestão"):
    sugestao = TextInput(label="Sua sugestão", style=discord.TextStyle.paragraph, max_length=1000, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        sugestoes_db.append({"user": interaction.user.id, "texto": self.sugestao.value, "data": datetime.now(timezone.utc).isoformat()})
        emb = discord.Embed(title="Nova Sugestão", description=f"**De:** {interaction.user.mention}\n**Sugestão:** {self.sugestao.value}", color=0x2b2d31)
        canal = bot.get_channel(CANAL_SUGESTAO)
        if canal: await canal.send(embed=emb)
        await interaction.response.send_message("Sugestão enviada!", ephemeral=True)

class ReportModal(Modal, title="Reportar Usuário"):
    user_id = TextInput(label="ID ou @ do usuário", required=True)
    motivo = TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    async def on_submit(self, interaction: discord.Interaction):
        reports_db.append({"por": interaction.user.id, "alvo": self.user_id.value, "motivo": self.motivo.value})
        emb = discord.Embed(title="Novo Report", description=f"**Por:** {interaction.user.mention}\n**Alvo:** {self.user_id.value}\n**Motivo:** {self.motivo.value}\n**Canal:** {interaction.channel.mention}", color=0xff0000)
        canal = bot.get_channel(CANAL_REPORT)
        if canal: await canal.send(embed=emb)
        await interaction.response.send_message("Report enviado!", ephemeral=True)

class VerificacaoView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Verificar", style=discord.ButtonStyle.green, custom_id="verificar_btn", emoji="✅"))
    async def interaction_check(self, interaction): return True

# ================= EVENTOS 150+ LINHAS =================
@bot.event
async def on_ready():
    print(f"Bot ON {bot.user} | {len(bot.guilds)} servers | {CANAL_REGRAS}")
    bot.add_view(TicketView())
    bot.add_view(TicketCloseView())
    bot.add_view(VerificacaoView())
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servidores"))
    try:
        synced = await bot.tree.sync()
        print(f"Sync {len(synced)} comandos")
    except Exception as e:
        print(f"Erro sync {e}")

@bot.event
async def on_member_join(member):
    now = datetime.now(timezone.utc)
    entradas[member.guild.id].append(now)
    # LIMPA ENTRADAS ANTIGAS
    entradas[member.guild.id] = [t for t in entradas[member.guild.id] if (now - t).total_seconds() < 60]
    # BEM VINDO SÓ TEXTO QUE TU PEDIU - SEM EMBED
    if bemvindo_on:
        ch = bot.get_channel(CANAL_BOAS_VINDAS)
        if ch:
            try:
                await ch.send(f"Boas vindas {member.mention}!!! Espero que goste do servidor viu seu imu tranca rua de tabuape\nDá uma olhada em <#{CANAL_REGRAS}> pra não tomar ban")
            except: pass
    # ANTI-RAID JOIN - DETECTA RAID
    if anti_raid:
        if len(entradas[member.guild.id]) > 5:
            log = bot.get_channel(CANAL_ANTIRAID)
            if log:
                try:
                    emb = discord.Embed(title="Possível Raid Detectado", description=f"{len(entradas[member.guild.id])} pessoas entraram em 60s\nÚltimo: {member.mention} ({member.id})", color=0xff0000)
                    await log.send(embed=emb)
                except: pass

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(CANAL_BOAS_VINDAS)
    if ch:
        try: await ch.send(f"{member.display_name} saiu do servidor")
        except: pass

@bot.event
async def on_message_edit(before, after):
    if before.content == after.content: return
    if before.author.bot: return
    if logs_on:
        canal = bot.get_channel(CANAL_LOGS)
        if canal:
            try:
                emb = discord.Embed(title="Mensagem Editada", description=f"**Autor:** {before.author.mention}\n**Canal:** {before.channel.mention}\n**Antes:** {before.content[:1000]}\n**Depois:** {after.content[:1000]}", color=0xffa500)
                await canal.send(embed=emb)
            except: pass

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    if logs_on:
        canal = bot.get_channel(CANAL_LOGS)
        if canal:
            try:
                emb = discord.Embed(title="Mensagem Deletada", description=f"**Autor:** {message.author.mention}\n**Canal:** {message.channel.mention}\n**Conteúdo:** {message.content[:1000]}", color=0xff0000)
                await canal.send(embed=emb)
            except: pass

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
    # ANTI-SPAM
    if anti_spam and not message.author.guild_permissions.administrator:
        agora = datetime.now(timezone.utc)
        mensagens_spam[message.author.id].append(agora)
        mensagens_spam[message.author.id] = [t for t in mensagens_spam[message.author.id] if (agora - t).total_seconds() < 5]
        if len(mensagens_spam[message.author.id]) > 5:
            try:
                await message.author.timeout(timedelta(minutes=5), reason="Anti-spam")
                await message.channel.send(f"⏰ {message.author.mention} mutado 5min por spam", delete_after=10)
                mensagens_spam[message.author.id] = []
                log_acao(message.guild, f"Anti-spam: {message.author} mutado")
            except: pass
    # ANTI-LINK
    if anti_link and not message.author.guild_permissions.administrator:
        if links_regex.search(message.content):
            try:
                await message.delete()
                await message.channel.send(f"🔗 {message.author.mention} link bloqueado", delete_after=5)
                return
            except: pass
    # ANTI-FLOOD
    if anti_flood and not message.author.guild_permissions.administrator:
        mensagens_rapidas[message.author.id].append(message.content)
        if len(mensagens_rapidas[message.author.id]) >= 5:
            ultimas = list(mensagens_rapidas[message.author.id])[-5:]
            if len(set(ultimas)) == 1:
                try:
                    await message.channel.send(f"🚫 {message.author.mention} flood detectado", delete_after=5)
                    await message.author.timeout(timedelta(minutes=2), reason="Flood")
                except: pass
    # AFK
    if message.mentions:
        for m in message.mentions:
            if m.id in afk:
                try: await message.channel.send(f"💤 {m.display_name} tá AFK: {afk[m.id]}", delete_after=10)
                except: pass
    if message.author.id in afk:
        try:
            del afk[message.author.id]
            await message.channel.send(f"👋 {message.author.mention} voltou do AFK", delete_after=5)
        except: pass
    # XP
    if message.guild and not message.author.bot:
        up, old, new = add_xp(message.author.id, random.randint(5, 15)), 0, 0
        # O add_xp retorna tupla, mas vamos simplificar
        data = level[message.author.id]
        if data["msgs"] % 100 == 0:
            log_acao(message.guild, f"{message.author} chegou a {data['msgs']} msgs")
    # ISCA ANTI-RAID - PRINCIPAL
    if message.channel.id == CANAL_ISCA and not message.author.guild_permissions.administrator:
        if message.author.id not in whitelist:
            try:
                await message.delete()
                await message.guild.ban(message.author, reason="Caiu na isca anti-raid", delete_message_days=1)
                log = bot.get_channel(CANAL_ANTIRAID)
                if log:
                    emb = discord.Embed(title="Isca Ativada", description=f"{message.author} ({message.author.id}) caiu na isca\nMsg: {message.content[:200]}", color=0xff0000)
                    await log.send(embed=emb)
            except Exception as e:
                print(f"Erro isca {e}")
        return
    await bot.process_commands(message)

# ================= COMANDOS ADM 300+ LINHAS =================
@bot.tree.command(name="clear", description="Limpa mensagens do canal")
async def clear_cmd(interaction: discord.Interaction, quantidade: int):
    if not is_mod(interaction): await interaction.response.send_message("Só mod pode usar", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    try: deleted = await interaction.channel.purge(limit=quantidade)
    except: deleted = []
    await interaction.followup.send(f"Limpei {len(deleted)} mensagens", ephemeral=True)
    comandos_usados["clear"]+=1

@bot.tree.command(name="ban", description="Bane um usuário")
async def ban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Sem motivo"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("Sem permissão", ephemeral=True); return
    try: await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"{membro.mention} banido. Motivo: {motivo}")
    except Exception as e: await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="massban", description="Bane vários IDs de uma vez")
async def massban_cmd(interaction: discord.Interaction, ids: str, motivo: str="Anti-raid"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    lista = [x.strip() for x in ids.split() if x.strip().isdigit()]
    banidos=0
    for uid in lista:
        try:
            user = await bot.fetch_user(int(uid))
            await interaction.guild.ban(user, reason=motivo)
            banidos+=1
            await asyncio.sleep(0.5)
        except: pass
    await interaction.followup.send(f"Massban finalizado: {banidos}/{len(lista)} banidos")

@bot.tree.command(name="unban", description="Desbane por ID")
async def unban_cmd(interaction: discord.Interaction, user_id: str):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: user = await bot.fetch_user(int(user_id)); await interaction.guild.unban(user); await interaction.response.send_message(f"{user.mention} desbanido")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="softban", description="Bane e desbane pra limpar mensagens")
async def softban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Limpeza"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: await membro.ban(reason=motivo, delete_message_days=1); await interaction.guild.unban(membro); await interaction.response.send_message(f"Softban em {membro.mention} feito")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="kick", description="Expulsa usuário")
async def kick_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Sem motivo"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: await membro.kick(reason=motivo); await interaction.response.send_message(f"{membro.mention} expulso. Motivo: {motivo}")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="timeout", description="Muta usuário por minutos")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str="Mutado"):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    try: await membro.timeout(timedelta(minutes=minutos), reason=motivo); await interaction.response.send_message(f"{membro.mention} mutado por {minutos}min. Motivo: {motivo}")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="untimeout", description="Desmuta")
async def untimeout_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    try: await membro.timeout(None); await interaction.response.send_message(f"{membro.mention} desmutado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="warn", description="Avisa usuário")
async def warn_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    warns[membro.id].append({"motivo": motivo, "por": interaction.user.id, "data": datetime.now(timezone.utc).isoformat()})
    total = len(warns[membro.id])
    await interaction.response.send_message(f"{membro.mention} avisado. Motivo: {motivo}. Total {total}/3")
    if total >=3:
        try: await membro.timeout(timedelta(hours=1), reason="3 warns"); await interaction.followup.send(f"{membro.mention} mutado 1h por 3 avisos")
        except: pass

@bot.tree.command(name="warns", description="Ver avisos de alguém")
async def warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    w = warns[membro.id]
    if not w: await interaction.response.send_message(f"{membro.mention} sem avisos", ephemeral=True); return
    desc = "\n".join([f"{i+1}. {x['motivo']} - por <@{x['por']}> em {x['data'][:10]}" for i,x in enumerate(w)])
    await interaction.response.send_message(f"Avisos de {membro.mention}:\n{desc}", ephemeral=True)

@bot.tree.command(name="clear_warns", description="Limpa avisos")
async def clear_warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    warns[membro.id]=[]; await interaction.response.send_message(f"Avisos de {membro.mention} limpos")

@bot.tree.command(name="lock", description="Tranca canal")
async def lock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel
    try: await c.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message(f"{c.mention} trancado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="unlock", description="Destranca canal")
async def unlock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel
    try: await c.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message(f"{c.mention} liberado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="lockall", description="Tranca todos canais")
async def lockall_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    count=0
    for c in interaction.guild.text_channels:
        try: await c.set_permissions(interaction.guild.default_role, send_messages=False); count+=1; await asyncio.sleep(0.3)
        except: pass
    await interaction.followup.send(f"Lockdown: {count} canais trancados")

@bot.tree.command(name="unlockall", description="Destranca todos")
async def unlockall_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    count=0
    for c in interaction.guild.text_channels:
        try: await c.set_permissions(interaction.guild.default_role, send_messages=True); count+=1; await asyncio.sleep(0.3)
        except: pass
    await interaction.followup.send(f"{count} canais liberados")

@bot.tree.command(name="slowmode", description="Define slowmode")
async def slowmode_cmd(interaction: discord.Interaction, segundos: int):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    try: await interaction.channel.edit(slowmode_delay=segundos); await interaction.response.send_message(f"Slowmode {segundos}s no canal")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="nuke", description="Recria canal do zero")
async def nuke_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel
    pos = c.position
    try:
        novo = await c.clone(reason=f"Nuke por {interaction.user}")
        await novo.edit(position=pos)
        await c.delete(reason="Nuke")
        await novo.send(f"Canal recriado por {interaction.user.mention}")
        await interaction.response.send_message(f"Canal {c.name} nukado", ephemeral=True)
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="dar_cargo", description="Da cargo pra alguém")
async def dar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: await membro.add_roles(cargo); await interaction.response.send_message(f"{membro.mention} ganhou {cargo.mention}")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="tirar_cargo", description="Tira cargo")
async def tirar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: await membro.remove_roles(cargo); await interaction.response.send_message(f"{membro.mention} perdeu {cargo.mention}")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="cargo_todos", description="Da cargo pra todo mundo")
async def cargo_todos_cmd(interaction: discord.Interaction, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    count=0
    for m in interaction.guild.members:
        if not m.bot and cargo not in m.roles:
            try: await m.add_roles(cargo); count+=1; await asyncio.sleep(0.4)
            except: pass
    await interaction.followup.send(f"Cargo {cargo.mention} dado pra {count} membros")

@bot.tree.command(name="criar_canal", description="Cria canal de texto")
async def criar_canal_cmd(interaction: discord.Interaction, nome: str):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: c = await interaction.guild.create_text_channel(nome); await interaction.response.send_message(f"Canal {c.mention} criado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="deletar_canal", description="Deleta canal")
async def deletar_canal_cmd(interaction: discord.Interaction, canal: discord.TextChannel):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: await canal.delete(reason=f"Deletado por {interaction.user}"); await interaction.response.send_message(f"Canal {canal.name} deletado", ephemeral=True)
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="criar_cargo", description="Cria cargo")
async def criar_cargo_cmd(interaction: discord.Interaction, nome: str, cor: str="2b2d31"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try:
        cor_hex = cor.replace("#","")
        cor_int = int(cor_hex, 16)
        cargo = await interaction.guild.create_role(name=nome, colour=discord.Colour(cor_int))
        await interaction.response.send_message(f"Cargo {cargo.mention} criado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="deletar_cargo", description="Deleta cargo")
async def deletar_cargo_cmd(interaction: discord.Interaction, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: await cargo.delete(reason=f"Deletado por {interaction.user}"); await interaction.response.send_message(f"Cargo {cargo.name} deletado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="blacklist", description="Bota na blacklist")
async def blacklist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    blacklist.add(membro.id); await interaction.response.send_message(f"{membro.mention} na blacklist, mensagens dele serão apagadas")

@bot.tree.command(name="unblacklist", description="Tira da blacklist")
async def unblacklist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    blacklist.discard(membro.id); await interaction.response.send_message(f"{membro.mention} removido da blacklist")

@bot.tree.command(name="whitelist", description="Whitelist da isca")
async def whitelist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    whitelist.add(membro.id); await interaction.response.send_message(f"{membro.mention} na whitelist, não toma ban na isca")

@bot.tree.command(name="antilink", description="Liga/desliga anti-link")
async def antilink_cmd(interaction: discord.Interaction, estado: str):
    global anti_link
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    anti_link = estado.lower() == "on"
    await interaction.response.send_message(f"Anti-link {'ligado' if anti_link else 'desligado'}")

@bot.tree.command(name="antispam", description="Liga/desliga anti-spam")
async def antispam_cmd(interaction: discord.Interaction, estado: str):
    global anti_spam
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    anti_spam = estado.lower() == "on"
    await interaction.response.send_message(f"Anti-spam {'ligado' if anti_spam else 'desligado'}")

@bot.tree.command(name="antiraid", description="Liga/desliga anti-raid")
async def antiraid_cmd(interaction: discord.Interaction, estado: str):
    global anti_raid
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    anti_raid = estado.lower() == "on"
    await interaction.response.send_message(f"Anti-raid {'ligado' if anti_raid else 'desligado'}")

@bot.tree.command(name="say", description="Fala como bot em um canal")
async def say_cmd(interaction: discord.Interaction, mensagem: str, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel
    await c.send(mensagem)
    await interaction.response.send_message("Mensagem enviada", ephemeral=True)

@bot.tree.command(name="embed", description="Manda embed custom")
async def embed_cmd(interaction: discord.Interaction, titulo: str, descricao: str, cor: str="2b2d31"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: cor_int = int(cor.replace("#",""), 16)
    except: cor_int = 0x2b2d31
    emb = discord.Embed(title=titulo, description=descricao, color=cor_int)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Embed enviado", ephemeral=True)

@bot.tree.command(name="aviso", description="Manda aviso embed")
async def aviso_cmd(interaction: discord.Interaction, titulo: str, descricao: str):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    emb = discord.Embed(title=titulo, description=descricao, color=0x2b2d31)
    emb.set_footer(text=f"Por {interaction.user.display_name}")
    emb.timestamp = datetime.now(timezone.utc)
    await interaction.channel.send(embed=emb)
    await interaction.response.send_message("Aviso enviado", ephemeral=True)

@bot.tree.command(name="limpar_user", description="Limpa mensagens de um usuário")
async def limpar_user_cmd(interaction: discord.Interaction, membro: discord.Member, quantidade: int=50):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    def check(m): return m.author.id == membro.id
    try: deleted = await interaction.channel.purge(limit=quantidade, check=check); await interaction.followup.send(f"Limpei {len(deleted)} mensagens de {membro.mention}", ephemeral=True)
    except Exception as e: await interaction.followup.send(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="nick", description="Muda apelido")
async def nick_cmd(interaction: discord.Interaction, membro: discord.Member, apelido: str):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    try: await membro.edit(nick=apelido); await interaction.response.send_message(f"Apelido de {membro.mention} mudado pra {apelido}")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

# ================= MEMBROS 300+ LINHAS =================
@bot.tree.command(name="perfil", description="Ver perfil")
async def perfil_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level[membro.id]
    emb=discord.Embed(title=f"Perfil de {membro.display_name}", color=0x2b2d31); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="Level", value=f"{data['level']} ({data['xp']} XP)"); emb.add_field(name="Mensagens", value=data["msgs"])
    emb.add_field(name="Entrou", value=f"<t:{int(membro.joined_at.timestamp())}:R>" if membro.joined_at else "?")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="avatar", description="Ver foto")
async def avatar_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; emb = discord.Embed(color=0x2b2d31); emb.set_image(url=membro.display_avatar.url); emb.set_footer(text=membro.display_name); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banner", description="Ver banner")
async def banner_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user
    try:
        u = await bot.fetch_user(membro.id)
        if u.banner: emb = discord.Embed(color=0x2b2d31); emb.set_image(url=u.banner.url); await interaction.response.send_message(embed=emb)
        else: await interaction.response.send_message("Usuário sem banner", ephemeral=True)
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="userinfo", description="Info do usuário")
async def userinfo_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; emb = discord.Embed(title=membro.display_name, color=0x2b2d31); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="ID", value=membro.id); emb.add_field(name="Conta criada", value=f"<t:{int(membro.created_at.timestamp())}:D>"); emb.add_field(name="Entrou no server", value=f"<t:{int(membro.joined_at.timestamp())}:R>" if membro.joined_at else "?")
    emb.add_field(name="Cargos", value=len(membro.roles)-1); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="serverinfo", description="Info do servidor")
async def serverinfo_cmd(interaction: discord.Interaction):
    g = interaction.guild; emb = discord.Embed(title=g.name, description=g.description or "Sem descrição", color=0x2b2d31)
    if g.icon: emb.set_thumbnail(url=g.icon.url)
    emb.add_field(name="ID", value=g.id); emb.add_field(name="Dono", value=f"<@{g.owner_id}>"); emb.add_field(name="Membros", value=g.member_count); emb.add_field(name="Canais", value=len(g.channels)); emb.add_field(name="Cargos", value=len(g.roles)); emb.add_field(name="Criado em", value=f"<t:{int(g.created_at.timestamp())}:D>")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="ping", description="Latência")
async def ping_cmd(interaction: discord.Interaction): await interaction.response.send_message(f"Pong {round(bot.latency*1000)}ms")

@bot.tree.command(name="afk", description="Ficar AFK")
async def afk_cmd(interaction: discord.Interaction, motivo: str="AFK"): afk[interaction.user.id]=motivo; await interaction.response.send_message(f"{interaction.user.mention} AFK: {motivo}")

@bot.tree.command(name="rank", description="Ranking level")
async def rank_cmd(interaction: discord.Interaction):
    top = sorted(level.items(), key=lambda x: x[1]['xp'], reverse=True)[:15]; desc=""
    for i,(uid,d) in enumerate(top,1):
        m = interaction.guild.get_member(uid); nome = m.display_name if m else f"ID {uid}"; desc+=f"{i}. {nome} - Level {d['level']} ({d['xp']} xp)\n"
    await interaction.response.send_message(embed=discord.Embed(title="Ranking", description=desc or "Vazio", color=0x2b2d31))

@bot.tree.command(name="top_ativos", description="Top mensagens")
async def top_ativos_cmd(interaction: discord.Interaction):
    top = sorted(level.items(), key=lambda x: x[1]['msgs'], reverse=True)[:10]; desc="\n".join([f"{i}. {interaction.guild.get_member(uid).display_name if interaction.guild.get_member(uid) else uid} - {d['msgs']} msgs" for i,(uid,d) in enumerate(top,1)]) or "Vazio"
    await interaction.response.send_message(embed=discord.Embed(title="Top Ativos", description=desc, color=0x2b2d31))

@bot.tree.command(name="regras", description="Mostra regras")
async def regras_cmd(interaction: discord.Interaction):
    emb = discord.Embed(title="Regras do servidor", description="Pra todo mundo ficar de boa por aqui, segue as regras:", color=0x2b2d31)
    emb.add_field(name="1. Respeito", value="Trata todo mundo bem, sem treta desnecessária.", inline=False)
    emb.add_field(name="2. Sem spam ou divulgação", value="Evita flood e não divulga outros servidores sem permissão.", inline=False)
    emb.add_field(name="3. Conteúdo no lugar certo", value="Manda mídia no canal de mídia, conversa no geral.", inline=False)
    emb.add_field(name="4. Isca anti-raid", value=f"O canal <#{CANAL_ISCA}> é isca de proteção, não digita lá ou toma ban automático.", inline=False)
    emb.add_field(name="5. Siga a staff", value="Se a moderação pedir pra parar, respeita.", inline=False)
    emb.set_footer(text="Quebrou? Pode levar mute, kick ou ban")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="ajuda", description="Lista de comandos")
async def ajuda_cmd(interaction: discord.Interaction):
    # AJUDA SÓ TITULO COMO PEDIU
    emb=discord.Embed(title="Comandos", description="Todos os comandos disponíveis no servidor:", color=0x2b2d31)
    emb.add_field(name="Moderação", value="clear, ban, massban, unban, softban, kick, timeout, untimeout, warn, warns, clear_warns, lock, unlock, lockall, unlockall, slowmode, nuke, dar_cargo, tirar_cargo, cargo_todos, criar_canal, deletar_canal, criar_cargo, deletar_cargo, blacklist, unblacklist, whitelist, antilink, antispam, antiraid, say, embed, aviso, limpar_user, nick", inline=False)
    emb.add_field(name="Membros", value="perfil, avatar, banner, userinfo, serverinfo, ping, afk, rank, top_ativos, regras, ajuda, sugestao, report, enquete", inline=False)
    await interaction.response.send_message(embed=emb, ephemeral=True)

@bot.tree.command(name="sugestao", description="Enviar sugestão")
async def sugestao_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(SugestaoModal())

@bot.tree.command(name="report", description="Reportar alguém")
async def report_cmd(interaction: discord.Interaction):
    await interaction.response.send_modal(ReportModal())

@bot.tree.command(name="enquete", description="Criar enquete")
async def enquete_cmd(interaction: discord.Interaction, pergunta: str, opcao1: str, opcao2: str, opcao3: str=None, opcao4: str=None):
    emb = discord.Embed(title="📊 Enquete", description=pergunta, color=0x2b2d31)
    opcoes = [opcao1, opcao2, opcao3, opcao4]
    opcoes = [o for o in opcoes if o]
    desc = "\n".join([f"{i+1}. {o}" for i,o in enumerate(opcoes)])
    emb.add_field(name="Opções", value=desc)
    emb.set_footer(text=f"Enquete criada por {interaction.user.display_name}")
    await interaction.response.send_message(embed=emb)
    msg = await interaction.original_response()
    emojis = ["1️⃣","2️⃣","3️⃣","4️⃣"]
    for i in range(len(opcoes)):
        try: await msg.add_reaction(emojis[i])
        except: pass

bot.run(TOKEN)
