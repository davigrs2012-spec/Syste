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

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATABASE NA MEMÓRIA =================
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

# ================= UTILS =================
def is_adm(interaction):
    return interaction.user.guild_permissions.administrator

def add_xp(user_id, amount):
    data = level_db[user_id]
    data["xp"] += amount
    lvl_antigo = data["level"]
    # 100 xp por level
    data["level"] = data["xp"] // 100 + 1
    return data["level"] > lvl_antigo, data["level"]

# ================= EVENTOS =================
@bot.event
async def on_ready():
    print(f"🔥 SUPERNOVA ON: {bot.user} | Cristino Taruishida no comando")
    try:
        synced = await bot.tree.sync()
        print(f"Sync: {len(synced)} comandos")
    except Exception as e:
        print(f"Erro sync: {e}")

@bot.event
async def on_member_join(member):
    canal_bv = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal_bv:
        try:
            embed = discord.Embed(title="Bem vindo a Seita!", description=f"{member.mention} entrou na Seita do CJ Vascaino!", color=0x00ff00)
            embed.set_thumbnail(url=member.display_avatar.url)
            await canal_bv.send(embed=embed)
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
            if canal_log: await canal_log.send(f"🚨 KICK AUTO: {member} | {idade} dias")
        except: pass
        return
    if len(recent_joins) >= 5:
        try:
            await member.ban(reason="Raid Detectado", delete_message_days=1)
            if canal_log: await canal_log.send(f"🔥 RAID BAN: {member}")
        except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return

    # Level por mensagem
    if message.guild:
        upou, lvl = add_xp(message.author.id, random.randint(1,3))
        if upou and lvl % 5 == 0:
            try:
                await message.channel.send(f"🎉 {message.author.mention} upou pro level **{lvl}**!", delete_after=10)
            except: pass

    # Canal isca
    if message.channel.id == CANAL_ISCA:
        if message.guild and message.author.guild_permissions.administrator:
            await bot.process_commands(message)
            return
        try:
            await message.delete()
            await message.guild.ban(message.author, reason="Caiu na isca", delete_message_days=1)
            log = bot.get_channel(CANAL_LOGS)
            if log: await log.send(f"🪤 ISCA: {message.author} BANIDO")
        except: pass
        return

    await bot.process_commands(message)

# ================= MODERAÇÃO SUPERNOVA =================
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
    await interaction.followup.send(f"Apaguei {len(deleted)} mensagens!", ephemeral=True)

@bot.tree.command(name="ban", description="Banir usuario")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    try:
        await membro.ban(reason=motivo, delete_message_days=1)
        await interaction.response.send_message(f"🔨 {membro.mention} BANIDO - {motivo}")
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

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
    try:
        await membro.timeout(timedelta(minutes=minutos), reason=motivo)
        await interaction.response.send_message(f"🔇 {membro.mention} mutado por {minutos}min - {motivo}")
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="untimeout", description="Desmutar usuario")
async def untimeout(interaction: discord.Interaction, membro: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    await membro.timeout(None)
    await interaction.response.send_message(f"🔊 {membro.mention} desmutado!")

@bot.tree.command(name="warn", description="Dar aviso")
async def warn(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True); return
    warns_db[membro.id].append({"motivo": motivo, "por": interaction.user.id, "data": datetime.now().strftime("%d/%m %H:%M")})
    await interaction.response.send_message(f"⚠️ {membro.mention} avisado: {motivo} | Total: {len(warns_db[membro.id])}")

@bot.tree.command(name="warns", description="Ver avisos de um usuario")
async def warns(interaction: discord.Interaction, membro: discord.Member):
    lista = warns_db[membro.id]
    if not lista:
        await interaction.response.send_message(f"{membro.mention} sem avisos!", ephemeral=True); return
    desc = "\n".join([f"`{w['data']}` - {w['motivo']}" for w in lista[-10:]])
    embed = discord.Embed(title=f"Warns de {membro.display_name}", description=desc, color=0xffa500)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="lock", description="Trancar canal")
async def lock(interaction: discord.Interaction):
    if not is_adm(interaction):
        await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Canal trancado!")

@bot.tree.command(name="unlock", description="Destrancar canal")
async def unlock(interaction: discord.Interaction):
    if not is_adm(interaction):
        await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Canal destrancado!")

@bot.tree.command(name="slowmode", description="Definir modo lento")
async def slowmode(interaction: discord.Interaction, segundos: int):
    if not is_adm(interaction):
        await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.channel.edit(slowmode_delay=segundos)
    await interaction.response.send_message(f"🐢 Slowmode: {segundos}s")

# ================= INFO E UTIL =================
@bot.tree.command(name="ping", description="Ver ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong {round(bot.latency*1000)}ms")

@bot.tree.command(name="userinfo", description="Info do usuario")
async def userinfo(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"Info de {membro.display_name}", color=0x0099ff)
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="ID", value=membro.id)
    embed.add_field(name="Entrou em", value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "N/A")
    embed.add_field(name="Conta criada", value=membro.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Cargos", value=len(membro.roles)-1)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Info do servidor")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = discord.Embed(title=g.name, color=0x00ff00)
    if g.icon: embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="Membros", value=g.member_count)
    embed.add_field(name="Criado em", value=g.created_at.strftime("%d/%m/%Y"))
    embed.add_field(name="Canais", value=len(g.channels))
    embed.add_field(name="Cargos", value=len(g.roles))
    embed.add_field(name="Boost", value=g.premium_subscription_count)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Ver avatar")
async def avatar(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title=f"Avatar de {membro.display_name}", color=0x0099ff)
    embed.set_image(url=membro.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# ================= ECONOMIA E PESCA SUPERNOVA =================
@bot.tree.command(name="pescar", description="Pesque um peixe")
async def pescar(interaction: discord.Interaction):
    peixe = random.choices(lista_de_peixes, weights=[30,25,20,15,7,2,1], k=1)[0]
    inventario_db[interaction.user.id].append(peixe)
    carteira_db[interaction.user.id] += peixe["preco"]
    upou, lvl = add_xp(interaction.user.id, peixe["xp"])

    cor = {"Lixo": 0x808080, "Comum": 0x00ff00, "Raro": 0x0099ff, "Lendário": 0xffd700, "Épico": 0x9b59b6, "MÍTICO": 0xff0000}[peixe["raridade"]]
    embed = discord.Embed(title="🎣 Você pescou!", description=f"**{peixe['nome']}** {peixe['emoji']}\nRaridade: **{peixe['raridade']}**\nValor: R$ {peixe['preco']} | +{peixe['xp']} XP", color=cor)
    embed.set_footer(text=f"Carteira: R$ {carteira_db[interaction.user.id]} | Level: {level_db[interaction.user.id]['level']}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventario", description="Seu inventário")
async def inventario(interaction: discord.Interaction):
    itens = inventario_db[interaction.user.id]
    if not itens:
        await interaction.response.send_message("Inventário vazio! Use /pescar", ephemeral=True); return
    c = Counter([f"{p['emoji']} {p['nome']} - R${p['preco']}" for p in itens])
    desc = "\n".join([f"{q}x {nome}" for nome, q in c.items()])
    embed = discord.Embed(title=f"🎒 {interaction.user.display_name}", description=desc[:4000], color=0x0099ff)
    embed.set_footer(text=f"Carteira: R$ {carteira_db[interaction.user.id]} | Total: {len(itens)} peixes")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="carteira", description="Ver sua grana")
async def carteira(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    embed = discord.Embed(title="💰 Carteira", description=f"{membro.mention} tem **R$ {carteira_db[membro.id]}**", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="top", description="Ranking de pescadores")
async def top(interaction: discord.Interaction):
    ranking = sorted(carteira_db.items(), key=lambda x: x[1], reverse=True)[:10]
    if not ranking:
        await interaction.response.send_message("Ninguém pescou ainda!", ephemeral=True); return
    desc = ""
    for i, (uid, grana) in enumerate(ranking, 1):
        user = bot.get_user(uid)
        nome = user.display_name if user else f"ID {uid}"
        desc += f"**{i}.** {nome} - R$ {grana}\n"
    embed = discord.Embed(title="🏆 Top Pescadores", description=desc, color=0xffd700)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="vender", description="Vender todos os peixes")
async def vender(interaction: discord.Interaction):
    itens = inventario_db[interaction.user.id]
    if not itens:
        await interaction.response.send_message("Nada pra vender!", ephemeral=True); return
    total = sum(p["preco"] for p in itens)
    carteira_db[interaction.user.id] += total
    inventario_db[interaction.user.id].clear()
    await interaction.response.send_message(f"💸 Vendeu {len(itens)} peixes por R$ {total}! Carteira: R$ {carteira_db[interaction.user.id]}")

@bot.tree.command(name="daily", description="Resgate diário")
async def daily(interaction: discord.Interaction):
    agora = datetime.now(timezone.utc)
    ultimo = daily_db.get(interaction.user.id)
    if ultimo and (agora - ultimo).total_seconds() < 86400:
        falta = 86400 - (agora - ultimo).total_seconds()
        horas = int(falta // 3600)
        await interaction.response.send_message(f"Já pegou! Volta em {horas}h", ephemeral=True); return
    daily_db[interaction.user.id] = agora
    premio = random.randint(50, 150)
    carteira_db[interaction.user.id] += premio
    await interaction.response.send_message(f"🎁 Daily: +R$ {premio}! Carteira: R$ {carteira_db[interaction.user.id]}")

@bot.tree.command(name="rank", description="Seu level")
async def rank(interaction: discord.Interaction, membro: discord.Member = None):
    membro = membro or interaction.user
    data = level_db[membro.id]
    embed = discord.Embed(title=f"Level de {membro.display_name}", description=f"Level **{data['level']}**\nXP: {data['xp']} / {data['level']*100}", color=0x9b59b6)
    embed.set_thumbnail(url=membro.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# ================= DIVERSÃO =================
@bot.tree.command(name="8ball", description="Pergunte a bola mágica")
async def eightball(interaction: discord.Interaction, pergunta: str):
    respostas = ["Sim", "Não", "Talvez", "Com certeza", "Nem ferrando", "Pergunta pro CJ", "Vasco", "É bait"]
    await interaction.response.send_message(f"🎱 Pergunta: {pergunta}\nResposta: **{random.choice(respostas)}**")

@bot.tree.command(name="coinflip", description="Cara ou coroa")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.send_message(f"🪙 Caiu: **{random.choice(['Cara','Coroa'])}**")

@bot.tree.command(name="roll", description="Rolar dado")
async def roll(interaction: discord.Interaction, lados: int = 6):
    await interaction.response.send_message(f"🎲 Rolou d{lados}: **{random.randint(1,lados)}**")

@bot.tree.command(name="say", description="Fazer o bot falar (ADM)")
async def say(interaction: discord.Interaction, texto: str):
    if not is_adm(interaction):
        await interaction.response.send_message("Só ADM!", ephemeral=True); return
    await interaction.response.send_message("Enviado!", ephemeral=True)
    await interaction.channel.send(texto)

@bot.tree.command(name="poll", description="Criar enquete")
async def poll(interaction: discord.Interaction, pergunta: str):
    embed = discord.Embed(title="📊 Enquete", description=pergunta, color=0x0099ff)
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@bot.tree.command(name="ajuda", description="Todos os comandos da supernova")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="💥 SUPERNOVA - SEITA DO CJ", description="Bot da Seita - Cristino Taruishida", color=0xff0000)
    embed.add_field(name="🛡️ Moderação", value="`/ban` `/kick` `/timeout` `/untimeout` `/warn` `/warns` `/clear` `/antiraid` `/lock` `/unlock` `/slowmode`", inline=False)
    embed.add_field(name="🎣 Economia", value="`/pescar` `/inventario` `/carteira` `/vender` `/top` `/daily` `/rank`", inline=False)
    embed.add_field(name="📊 Info", value="`/ping` `/userinfo` `/serverinfo` `/avatar`", inline=False)
    embed.add_field(name="🎮 Diversão", value="`/8ball` `/coinflip` `/roll` `/poll` `/say`", inline=False)
    embed.set_footer(text="SUPERNOVA EDITION - Taruishida Cristino")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ================= PREFIXO LEGADO =================
@bot.command(name="cj")
async def cj(ctx):
    await ctx.send(f"{ctx.author.mention} Para de me marcar big smoke~kun")

@bot.command(name="zoeira")
async def zoeira(ctx):
    await ctx.send("Procurou zoeira achou bait, seu miseravel kkkkkkkkkkk")
    await ctx.send("https://cdn.discordapp.com/attachments/743996477227008010/1338093043429150760/meandwho2.gif")

bot.run(TOKEN)
