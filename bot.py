import os, random, discord, asyncio, re
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from collections import defaultdict, deque, Counter
from datetime import datetime, timezone, timedelta
import sys

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

# ================= CANAIS =================
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_ISCA = 1559066250410197013
CANAL_LOGS = 1559066250410197013
CANAL_ANTIRAID = 1559066250410197013
CANAL_REGRAS = 1559756885727383633
CANAL_MIDIA = 1559446593277796463
CANAL_SUGESTAO = 1559066250410197013
CANAL_REPORT = 1559066250410197013

CANAIS_PROTEGIDOS = [CANAL_REGRAS, CANAL_BOAS_VINDAS, CANAL_MIDIA]

BOTS_RESTRITOS = [208583444938057728, 235148962103951360, 155149108183695360]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.presences = True

bot = commands.Bot(command_prefix=["!", "s!", "m!"], intents=intents, help_command=None)

# DB
level = defaultdict(lambda: {"xp": 0, "level": 1, "msgs": 0})
warns = defaultdict(list)
afk = {}
blacklist = set()
whitelist = set()
spam = defaultdict(list)
rapido = defaultdict(lambda: deque(maxlen=10))
anti_link = False
anti_spam = True
anti_raid = True
anti_flood = True
bemvindo_on = True
logs_on = True
entradas = defaultdict(list)
comandos = Counter()

def is_adm(i): return i.user.guild_permissions.administrator
def is_mod(i): return i.user.guild_permissions.moderate_members or is_adm(i)
def level_from_xp(xp): return int((xp / 100) ** 0.5) + 1

# VIEWS
class SugestaoModal(Modal, title="Enviar Sugestão"):
    sugestao = TextInput(label="Sua sugestão", style=discord.TextStyle.paragraph, max_length=1000, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        emb = discord.Embed(title="Nova Sugestão", description=f"**De:** {interaction.user.mention}\n**Sugestão:** {self.sugestao.value}", color=0x2b2d31)
        canal = bot.get_channel(CANAL_SUGESTAO)
        if canal: await canal.send(embed=emb)
        await interaction.response.send_message("Sugestão enviada!", ephemeral=True)

class ReportModal(Modal, title="Reportar"):
    alvo = TextInput(label="ID ou @ do usuário", required=True)
    motivo = TextInput(label="Motivo", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    async def on_submit(self, interaction: discord.Interaction):
        emb = discord.Embed(title="Novo Report", description=f"**Por:** {interaction.user.mention}\n**Alvo:** {self.alvo.value}\n**Motivo:** {self.motivo.value}", color=0xff0000)
        canal = bot.get_channel(CANAL_REPORT)
        if canal: await canal.send(embed=emb)
        await interaction.response.send_message("Report enviado!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"ON {bot.user} | 900+ LINHAS | REGRAS PROTEGIDO")
    try: await bot.tree.sync()
    except: pass

@bot.event
async def on_member_join(member):
    now = datetime.now(timezone.utc)
    entradas[member.guild.id].append(now)
    entradas[member.guild.id] = [t for t in entradas[member.guild.id] if (now-t).total_seconds() < 60]
    if bemvindo_on:
        ch = bot.get_channel(CANAL_BOAS_VINDAS)
        if ch:
            try: await ch.send(f"Boas vindas {member.mention}!!! Espero que goste do servidor viu seu imu tranca rua de tabuape\nDá uma olhada em <#{CANAL_REGRAS}>")
            except: pass
    if anti_raid and len(entradas[member.guild.id]) > 5:
        log = bot.get_channel(CANAL_ANTIRAID)
        if log:
            try: await log.send(f"🚨 Possível raid: {len(entradas[member.guild.id])} entraram em 60s | Último: {member.mention}")
            except: pass

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    if message.channel.id in CANAIS_PROTEGIDOS: return
    if message.channel.id == CANAL_ISCA: return
    if message.content.startswith("!regras") or message.content.startswith("/regras") or message.content.startswith("!ajuda"): return
    if logs_on:
        canal = bot.get_channel(CANAL_LOGS)
        if canal:
            try:
                emb = discord.Embed(title="Mensagem Deletada", description=f"**Autor:** {message.author.mention}\n**Canal:** {message.channel.mention}\n**Conteúdo:** {message.content[:1000]}", color=0xff0000)
                await canal.send(embed=emb)
            except: pass

@bot.event
async def on_message_edit(before, after):
    if before.author.bot: return
    if before.content == after.content: return
    if before.channel.id in CANAIS_PROTEGIDOS: return
    if logs_on:
        canal = bot.get_channel(CANAL_LOGS)
        if canal:
            try:
                emb = discord.Embed(title="Mensagem Editada", description=f"**Autor:** {before.author.mention}\n**Canal:** {before.channel.mention}\n**Antes:** {before.content[:500]}\n**Depois:** {after.content[:500]}", color=0xffa500)
                await canal.send(embed=emb)
            except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id in CANAIS_PROTEGIDOS:
        await bot.process_commands(message)
        return
    if message.author.id in blacklist:
        try: await message.delete()
        except: pass
        return
    if anti_spam and not message.author.guild_permissions.administrator:
        agora = datetime.now(timezone.utc)
        spam[message.author.id].append(agora)
        spam[message.author.id] = [t for t in spam[message.author.id] if (agora-t).total_seconds() < 5]
        if len(spam[message.author.id]) > 5:
            try: await message.author.timeout(timedelta(minutes=5), reason="Anti-spam"); await message.channel.send(f"⏰ {message.author.mention} mutado 5min por spam", delete_after=10); spam[message.author.id]=[]
            except: pass
    if anti_link and not message.author.guild_permissions.administrator:
        if "http://" in message.content or "https://" in message.content or "discord.gg" in message.content:
            try: await message.delete(); await message.channel.send(f"🔗 {message.author.mention} link bloqueado", delete_after=5); return
            except: pass
    if message.mentions:
        for m in message.mentions:
            if m.id in afk:
                try: await message.channel.send(f"💤 {m.display_name} tá AFK: {afk[m.id]}", delete_after=10)
                except: pass
    if message.author.id in afk:
        try: del afk[message.author.id]; await message.channel.send(f"👋 {message.author.mention} voltou do AFK", delete_after=5)
        except: pass
    if message.guild and not message.author.bot:
        data = level[message.author.id]; data["xp"]+=random.randint(5,15); data["msgs"]+=1; data["level"]=level_from_xp(data["xp"])
    if message.channel.id == CANAL_ISCA and not message.author.guild_permissions.administrator:
        if message.author.id not in whitelist:
            try: await message.delete(); await message.guild.ban(message.author, reason="Isca anti-raid", delete_message_days=1)
            except: pass
        return
    await bot.process_commands(message)

# ========== COMANDOS SLASH E PREFIXO ==========
@bot.tree.command(name="regras", description="Ver regras")
async def regras_slash(interaction: discord.Interaction):
    emb = discord.Embed(title="Regras do servidor", description="Pra todo mundo ficar de boa:", color=0x2b2d31)
    emb.add_field(name="1. Respeito", value="Trata todo mundo bem, sem treta.", inline=False)
    emb.add_field(name="2. Sem spam", value="Sem flood ou divulgação sem permissão.", inline=False)
    emb.add_field(name="3. Conteúdo no lugar certo", value="Mídia no canal de mídia.", inline=False)
    emb.add_field(name="4. Isca", value=f"Canal <#{CANAL_ISCA}> é proteção anti-raid, não fala lá.", inline=False)
    await interaction.response.send_message(embed=emb)

@bot.command(name="regras")
async def regras_prefix(ctx):
    emb = discord.Embed(title="Regras do servidor", description="Pra todo mundo ficar de boa:", color=0x2b2d31)
    emb.add_field(name="1. Respeito", value="Trata todo mundo bem, sem treta.", inline=False)
    emb.add_field(name="2. Sem spam", value="Sem flood ou divulgação.", inline=False)
    emb.add_field(name="3. Isca", value=f"<#{CANAL_ISCA}> é proteção anti-raid.", inline=False)
    await ctx.send(embed=emb)

@bot.tree.command(name="clear", description="Limpa mensagens")
async def clear_cmd(interaction: discord.Interaction, quantidade: int):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    d = await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"Limpei {len(d)}", ephemeral=True)

@bot.tree.command(name="ban", description="Banir")
async def ban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Sem motivo"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("Sem permissão", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"{membro.mention} banido. {motivo}")

@bot.tree.command(name="massban", description="Banir vários IDs")
async def massban_cmd(interaction: discord.Interaction, ids: str, motivo: str="Anti-raid"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    lista = [x.strip() for x in ids.split() if x.strip().isdigit()]; banidos=0
    for uid in lista:
        try: user = await bot.fetch_user(int(uid)); await interaction.guild.ban(user, reason=motivo); banidos+=1; await asyncio.sleep(0.5)
        except: pass
    await interaction.followup.send(f"Massban: {banidos}/{len(lista)}")

@bot.tree.command(name="unban", description="Desbanir")
async def unban_cmd(interaction: discord.Interaction, user_id: str):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: user = await bot.fetch_user(int(user_id)); await interaction.guild.unban(user); await interaction.response.send_message(f"{user.mention} desbanido")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="softban", description="Softban limpa msgs")
async def softban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Limpeza"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.guild.unban(membro); await interaction.response.send_message(f"Softban {membro.mention} feito")

@bot.tree.command(name="kick", description="Expulsar")
async def kick_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Sem motivo"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await membro.kick(reason=motivo); await interaction.response.send_message(f"{membro.mention} expulso")

@bot.tree.command(name="timeout", description="Mutar")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int, motivo: str="Mutado"):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos), reason=motivo); await interaction.response.send_message(f"{membro.mention} mutado {minutos}min")

@bot.tree.command(name="untimeout", description="Desmutar")
async def untimeout_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    await membro.timeout(None); await interaction.response.send_message(f"{membro.mention} desmutado")

@bot.tree.command(name="warn", description="Avisar")
async def warn_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    warns[membro.id].append(motivo); await interaction.response.send_message(f"{membro.mention} avisado. {motivo} Total {len(warns[membro.id])}/3")
    if len(warns[membro.id])>=3:
        try: await membro.timeout(timedelta(hours=1), reason="3 warns"); await interaction.followup.send(f"{membro.mention} mutado 1h por 3 avisos")
        except: pass

@bot.tree.command(name="warns", description="Ver avisos")
async def warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    w = warns[membro.id]; await interaction.response.send_message(f"{membro.mention} {len(w)} avisos: {', '.join(w) if w else 'nenhum'}", ephemeral=True)

@bot.tree.command(name="clear_warns", description="Limpar avisos")
async def clear_warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    warns[membro.id]=[]; await interaction.response.send_message(f"Avisos de {membro.mention} limpos")

@bot.tree.command(name="lock", description="Trancar canal")
async def lock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel; await c.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message(f"{c.mention} trancado")

@bot.tree.command(name="unlock", description="Destrancar")
async def unlock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel; await c.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message(f"{c.mention} liberado")

@bot.tree.command(name="lockall", description="Trancar tudo")
async def lockall_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    for c in interaction.guild.text_channels:
        if c.id in CANAIS_PROTEGIDOS: continue
        try: await c.set_permissions(interaction.guild.default_role, send_messages=False); await asyncio.sleep(0.2)
        except: pass
    await interaction.followup.send("Lockdown feito - regras protegido")

@bot.tree.command(name="unlockall", description="Destrancar tudo")
async def unlockall_cmd(interaction: discord.Interaction):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    for c in interaction.guild.text_channels:
        try: await c.set_permissions(interaction.guild.default_role, send_messages=True); await asyncio.sleep(0.2)
        except: pass
    await interaction.followup.send("Todos liberados")

@bot.tree.command(name="slowmode", description="Slowmode")
async def slowmode_cmd(interaction: discord.Interaction, segundos: int):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    await interaction.channel.edit(slowmode_delay=segundos); await interaction.response.send_message(f"Slowmode {segundos}s")

@bot.tree.command(name="nuke", description="Recria canal")
async def nuke_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel; pos = c.position; novo = await c.clone(reason=f"Nuke {interaction.user}"); await novo.edit(position=pos); await c.delete(reason="Nuke"); await novo.send(f"Canal recriado por {interaction.user.mention}")

@bot.tree.command(name="dar_cargo", description="Dar cargo")
async def dar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await membro.add_roles(cargo); await interaction.response.send_message(f"{membro.mention} ganhou {cargo.mention}")

@bot.tree.command(name="tirar_cargo", description="Tirar cargo")
async def tirar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await membro.remove_roles(cargo); await interaction.response.send_message(f"{membro.mention} perdeu {cargo.mention}")

@bot.tree.command(name="cargo_todos", description="Dar cargo pra todos")
async def cargo_todos_cmd(interaction: discord.Interaction, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await interaction.response.defer()
    count=0
    for m in interaction.guild.members:
        if not m.bot and cargo not in m.roles:
            try: await m.add_roles(cargo); count+=1; await asyncio.sleep(0.3)
            except: pass
    await interaction.followup.send(f"Cargo {cargo.mention} dado pra {count} membros")

@bot.tree.command(name="criar_canal", description="Criar canal")
async def criar_canal_cmd(interaction: discord.Interaction, nome: str):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = await interaction.guild.create_text_channel(nome); await interaction.response.send_message(f"Canal {c.mention} criado")

@bot.tree.command(name="deletar_canal", description="Deletar canal")
async def deletar_canal_cmd(interaction: discord.Interaction, canal: discord.TextChannel):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    await canal.delete(reason=f"Deletado por {interaction.user}"); await interaction.response.send_message(f"Canal {canal.name} deletado", ephemeral=True)

@bot.tree.command(name="criar_cargo", description="Criar cargo")
async def criar_cargo_cmd(interaction: discord.Interaction, nome: str, cor: str="2b2d31"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: cor_int = int(cor.replace("#",""), 16); cargo = await interaction.guild.create_role(name=nome, colour=discord.Colour(cor_int)); await interaction.response.send_message(f"Cargo {cargo.mention} criado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="deletar_cargo", description="Deletar cargo")
async def deletar_cargo_cmd(interaction: discord.Interaction, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: await cargo.delete(reason=f"Deletado por {interaction.user}"); await interaction.response.send_message(f"Cargo {cargo.name} deletado")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="blacklist", description="Blacklist")
async def blacklist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    blacklist.add(membro.id); await interaction.response.send_message(f"{membro.mention} blacklist")

@bot.tree.command(name="unblacklist", description="Tirar blacklist")
async def unblacklist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    blacklist.discard(membro.id); await interaction.response.send_message(f"{membro.mention} removido")

@bot.tree.command(name="whitelist", description="Whitelist isca")
async def whitelist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    whitelist.add(membro.id); await interaction.response.send_message(f"{membro.mention} whitelist isca")

@bot.tree.command(name="antilink", description="Anti-link on/off")
async def antilink_cmd(interaction: discord.Interaction, estado: str):
    global anti_link
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    anti_link = estado.lower() == "on"; await interaction.response.send_message(f"Anti-link {'ligado' if anti_link else 'desligado'}")

@bot.tree.command(name="antispam", description="Anti-spam on/off")
async def antispam_cmd(interaction: discord.Interaction, estado: str):
    global anti_spam
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    anti_spam = estado.lower() == "on"; await interaction.response.send_message(f"Anti-spam {'ligado' if anti_spam else 'desligado'}")

@bot.tree.command(name="antiraid", description="Anti-raid on/off")
async def antiraid_cmd(interaction: discord.Interaction, estado: str):
    global anti_raid
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    anti_raid = estado.lower() == "on"; await interaction.response.send_message(f"Anti-raid {'ligado' if anti_raid else 'desligado'}")

@bot.tree.command(name="say", description="Falar como bot")
async def say_cmd(interaction: discord.Interaction, mensagem: str, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    c = canal or interaction.channel; await c.send(mensagem); await interaction.response.send_message("Enviado", ephemeral=True)

@bot.tree.command(name="embed", description="Mandar embed")
async def embed_cmd(interaction: discord.Interaction, titulo: str, descricao: str, cor: str="2b2d31"):
    if not is_adm(interaction): await interaction.response.send_message("Só adm", ephemeral=True); return
    try: cor_int = int(cor.replace("#",""), 16)
    except: cor_int = 0x2b2d31
    emb = discord.Embed(title=titulo, description=descricao, color=cor_int)
    await interaction.channel.send(embed=emb); await interaction.response.send_message("Embed enviado", ephemeral=True)

@bot.tree.command(name="aviso", description="Aviso embed")
async def aviso_cmd(interaction: discord.Interaction, titulo: str, descricao: str):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    emb = discord.Embed(title=titulo, description=descricao, color=0x2b2d31); emb.set_footer(text=f"Por {interaction.user.display_name}"); emb.timestamp = datetime.now(timezone.utc)
    await interaction.channel.send(embed=emb); await interaction.response.send_message("Aviso enviado", ephemeral=True)

@bot.tree.command(name="limpar_user", description="Limpar msgs de um user")
async def limpar_user_cmd(interaction: discord.Interaction, membro: discord.Member, quantidade: int=50):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    def check(m): return m.author.id == membro.id
    deleted = await interaction.channel.purge(limit=quantidade, check=check)
    await interaction.followup.send(f"Limpei {len(deleted)} de {membro.mention}", ephemeral=True)

@bot.tree.command(name="nick", description="Mudar apelido")
async def nick_cmd(interaction: discord.Interaction, membro: discord.Member, apelido: str):
    if not is_mod(interaction): await interaction.response.send_message("Só mod", ephemeral=True); return
    try: await membro.edit(nick=apelido); await interaction.response.send_message(f"Apelido de {membro.mention} mudado pra {apelido}")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

# MEMBROS
@bot.tree.command(name="perfil", description="Ver perfil")
async def perfil_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level[membro.id]
    emb=discord.Embed(title=f"Perfil de {membro.display_name}", color=0x2b2d31); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="Level", value=f"{data['level']} ({data['xp']} XP)"); emb.add_field(name="Msgs", value=data["msgs"])
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="avatar", description="Ver foto")
async def avatar_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; emb = discord.Embed(color=0x2b2d31); emb.set_image(url=membro.display_avatar.url); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="banner", description="Ver banner")
async def banner_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user
    try:
        u = await bot.fetch_user(membro.id)
        if u.banner: emb = discord.Embed(color=0x2b2d31); emb.set_image(url=u.banner.url); await interaction.response.send_message(embed=emb)
        else: await interaction.response.send_message("Sem banner", ephemeral=True)
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="userinfo", description="Info do user")
async def userinfo_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; emb = discord.Embed(title=membro.display_name, color=0x2b2d31); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="ID", value=membro.id); emb.add_field(name="Entrou", value=f"<t:{int(membro.joined_at.timestamp())}:R>" if membro.joined_at else "?")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="serverinfo", description="Info do server")
async def serverinfo_cmd(interaction: discord.Interaction):
    g = interaction.guild; emb = discord.Embed(title=g.name, color=0x2b2d31)
    if g.icon: emb.set_thumbnail(url=g.icon.url)
    emb.add_field(name="Membros", value=g.member_count); emb.add_field(name="Canais", value=len(g.channels)); emb.add_field(name="Criado", value=f"<t:{int(g.created_at.timestamp())}:D>")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="ping", description="Ping")
async def ping_cmd(interaction: discord.Interaction): await interaction.response.send_message(f"Pong {round(bot.latency*1000)}ms")

@bot.tree.command(name="afk", description="Ficar AFK")
async def afk_cmd(interaction: discord.Interaction, motivo: str="AFK"): afk[interaction.user.id]=motivo; await interaction.response.send_message(f"{interaction.user.mention} AFK: {motivo}")

@bot.tree.command(name="rank", description="Ranking")
async def rank_cmd(interaction: discord.Interaction):
    top = sorted(level.items(), key=lambda x: x[1]['xp'], reverse=True)[:10]; desc=""
    for i,(uid,d) in enumerate(top,1):
        m = interaction.guild.get_member(uid); nome = m.display_name if m else f"ID {uid}"; desc+=f"{i}. {nome} - Level {d['level']}\n"
    await interaction.response.send_message(embed=discord.Embed(title="Ranking", description=desc or "Vazio", color=0x2b2d31))

@bot.tree.command(name="top_ativos", description="Top msgs")
async def top_ativos_cmd(interaction: discord.Interaction):
    top = sorted(level.items(), key=lambda x: x[1]['msgs'], reverse=True)[:10]; desc="\n".join([f"{i}. {interaction.guild.get_member(uid).display_name if interaction.guild.get_member(uid) else uid} - {d['msgs']} msgs" for i,(uid,d) in enumerate(top,1)]) or "Vazio"
    await interaction.response.send_message(embed=discord.Embed(title="Top Ativos", description=desc, color=0x2b2d31))

@bot.tree.command(name="sugestao", description="Enviar sugestão")
async def sugestao_cmd(interaction: discord.Interaction): await interaction.response.send_modal(SugestaoModal())

@bot.tree.command(name="report", description="Reportar")
async def report_cmd(interaction: discord.Interaction): await interaction.response.send_modal(ReportModal())

@bot.tree.command(name="enquete", description="Criar enquete")
async def enquete_cmd(interaction: discord.Interaction, pergunta: str, opcao1: str, opcao2: str, opcao3: str=None, opcao4: str=None):
    emb = discord.Embed(title="📊 Enquete", description=pergunta, color=0x2b2d31)
    opcoes = [o for o in [opcao1, opcao2, opcao3, opcao4] if o]
    desc = "\n".join([f"{i+1}. {o}" for i,o in enumerate(opcoes)])
    emb.add_field(name="Opções", value=desc); emb.set_footer(text=f"Por {interaction.user.display_name}")
    await interaction.response.send_message(embed=emb)
    msg = await interaction.original_response()
    emojis = ["1️⃣","2️⃣","3️⃣","4️⃣"]
    for i in range(len(opcoes)):
        try: await msg.add_reaction(emojis[i])
        except: pass

@bot.tree.command(name="ajuda", description="Comandos")
async def ajuda_cmd(interaction: discord.Interaction):
    emb=discord.Embed(title="Comandos", color=0x2b2d31)
    emb.add_field(name="Moderação", value="clear, ban, massban, unban, softban, kick, timeout, untimeout, warn, warns, clear_warns, lock, unlock, lockall, unlockall, slowmode, nuke, dar_cargo, tirar_cargo, cargo_todos, criar_canal, deletar_canal, criar_cargo, deletar_cargo, blacklist, unblacklist, whitelist, antilink, antispam, antiraid, say, embed, aviso, limpar_user, nick", inline=False)
    emb.add_field(name="Membros", value="perfil, avatar, banner, userinfo, serverinfo, ping, afk, rank, top_ativos, regras, ajuda, sugestao, report, enquete", inline=False)
    await interaction.response.send_message(embed=emb, ephemeral=True)

bot.run(TOKEN)
