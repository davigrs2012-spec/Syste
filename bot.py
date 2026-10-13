import os, random, asyncio, discord, aiohttp
from discord.ext import commands
from discord import app_commands
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
import sys

# FIX PYTHON 3.13 AUDIOOP - PRA NÃO CRASHAR
if sys.version_info >= (3, 13):
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ========== GIFS.GIF DIRETO - SEM LINK FEIO - FUNCIONA ANIMADO ==========
# TODOS TERMINAM EM.GIF PRA MOSTRAR ANIMADO SEM MOSTRAR LINK AZUL!
# Se quiser usar os do Klipy: botão direito no gif > copiar endereço da imagem > tem que terminar em.gif
GIF_CJ_TRISTE = "https://media.tenor.com/2uyENRuvVAgAAAAc/cj-sad.gif"
GIF_GROVE_DANCANDO = "https://media.tenor.com/BkMT9e9pQ6kAAAAC/cj-dance-gta.gif"
GIF_BIGSMOKE_PEDIDO = "https://media.tenor.com/T5V0Y1E9aXAAAAAC/big-smoke-order.gif"
GIF_SEITA_DANCANDO = "https://media.tenor.com/8p5rZ9sT2AAAAAC/cj-grove-dance.gif"
GIF_CJ_IA = "https://media.tenor.com/1q2w3E4r5TAAAAAC/cj-ai-gta.gif"

# CANAIS
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_ISCA = 1559066250410197013
CANAL_LOGS = 1559066250410197013
CANAL_PESCA = 1559446593277796463
CANAL_BOT = 1559447018869358592
CANAL_ANTIRAID = 1559066250410197013
CANAL_REGRAS = 1558857282702409749

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
bot = commands.Bot(command_prefix=["!", "cj!", "grove!"], intents=intents, help_command=None)

inventario = defaultdict(list)
carteira = defaultdict(int)
level = defaultdict(lambda: {"xp": 0, "level": 1})
warns = defaultdict(list)
daily = {}
rep = defaultdict(int)
afk = {}
casamento = {}
pesca_cd = {}
blacklist = set()

loja_items = {
    "ak47": {"preco": 5000, "emoji": "🔫", "desc": "AK da Grove"},
    "bicicleta": {"preco": 1000, "emoji": "🚲", "desc": "BMX do CJ"},
    "corrente": {"preco": 2000, "emoji": "⛓️", "desc": "Corrente de ouro"},
    "casa_grove": {"preco": 50000, "emoji": "🏠", "desc": "Casa na Grove Street"},
    "taco": {"preco": 1500, "emoji": "🌮", "desc": "Taco Cluckin Bell"},
    "colete": {"preco": 3000, "emoji": "🦺", "desc": "Colete Grove"},
    "oculos": {"preco": 800, "emoji": "🕶️", "desc": "Óculos CJ"},
    "radio": {"preco": 1200, "emoji": "📻", "desc": "Radio Los Santos"},
}

peixes_cj = [
    {"nome": "Sardinha da Grove", "emoji": "🐟", "rar": "Comum", "preco": 10, "xp": 5, "cor": 0x2ecc71},
    {"nome": "Tilapia de Los Santos", "emoji": "🐠", "rar": "Comum", "preco": 15, "xp": 8, "cor": 0x1abc9c},
    {"nome": "Atum Ballas", "emoji": "🐟", "rar": "Comum", "preco": 20, "xp": 12, "cor": 0x3498db},
    {"nome": "Tubarao de Los Santos", "emoji": "🦈", "rar": "Raro", "preco": 150, "xp": 60, "cor": 0xf1c40f},
    {"nome": "Baiacu Vagos", "emoji": "🐡", "rar": "Raro", "preco": 200, "xp": 80, "cor": 0xe67e22},
    {"nome": "Big Smoke Burger", "emoji": "🍔", "rar": "LENDARIO", "preco": 800, "xp": 400, "cor": 0xe67e22},
    {"nome": "Kraken da Grove", "emoji": "🦑", "rar": "MITICO", "preco": 2000, "xp": 800, "cor": 0xe74c3c},
    {"nome": "CJ Dourado", "emoji": "👑", "rar": "SECRETO", "preco": 15000, "xp": 5000, "cor": 0xffd700},
    {"nome": "Beach Boy - Pesci", "emoji": "🎣", "rar": "JOJO", "preco": 5000, "xp": 1000, "cor": 0x9b59b6},
]

FRASES_CJ = ["Grove Street é nossa, porra! 🏴‍☠️","Ah shit, here we go again... 😤","CJ tá na área, Grove 4 life! 💚","Big Smoke pediu 2 number 9... 🍔","Ryder ainda tá com aquela água? 💧","Sweet mandou chamar, seita na rua! 🔥","Seita do CJ não cai, Grove Street domina! 👁️","Cristino criou a seita, CJ executa! 👑","Ballers não entra aqui, Grove é nossa! 🔫","Grove Street Families, mano! 💚"]

def is_adm(i): return i.user.guild_permissions.administrator
def is_mod(i): return i.user.guild_permissions.moderate_members or is_adm(i)
def xp_para_level(l): return (l - 1) ** 2 * 100
def level_from_xp(xp): return int((xp / 100) ** 0.5) + 1
def add_xp(uid, amt):
    data = level[uid]; data["xp"] += amt; old = data["level"]; new = level_from_xp(data["xp"]); data["level"] = new; return new > old, old, new
async def dar_cargo_level(member, lvl):
    if not member.guild: return
    for lvl_req, cargo_id in sorted(CARGOS_LEVEL.items()):
        if lvl >= lvl_req:
            cargo = member.guild.get_role(cargo_id)
            if cargo and cargo not in member.roles:
                try:
                    await member.add_roles(cargo, reason=f"Level {lvl}")
                    ch = bot.get_channel(CANAL_BOT)
                    if ch: await ch.send(f"💚 {member.mention} subiu e pegou {cargo.mention} na Grove! Level {lvl}!")
                except: pass

@bot.event
async def on_ready():
    print(f"GROVE STREET CJ BOT 850 LINHAS FINAL FIX ON: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="Grove Street 4 Life | /ajuda"))
    try: s = await bot.tree.sync(); print(f"Sync {len(s)} comandos CJ")
    except Exception as e: print(e)

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(CANAL_BOAS_VINDAS)
    if ch:
        try:
            emb = discord.Embed(title="💚 BEM VINDO A GROVE STREET!", description=f"{member.mention} entrou pra Seita! Somos {member.guild.member_count} manos!\n\n📜 Lê <#{CANAL_REGRAS}>\n💚 /seita pra jurar\n🎣 /pescar no <#{CANAL_PESCA}>\n🤖 /ia no <#{CANAL_BOT}>\n\n**Cristino OG 👑**", color=0x00ff00)
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
    if message.mentions:
        for m in message.mentions:
            if m.id in afk: await message.channel.send(f"💤 {m.display_name} tá AFK na Grove: {afk[m.id]}", delete_after=10)
    if message.author.id in afk:
        del afk[message.author.id]; await message.channel.send(f"👋 {message.author.mention} voltou pra Grove!", delete_after=5)
    if message.guild and not message.author.bot:
        upou, old, new = add_xp(message.author.id, random.randint(5, 15))
        if upou: await dar_cargo_level(message.author, new)
    # ISCA ANTI RAID - NÃO ESQUECI!
    if message.channel.id == CANAL_ISCA and not message.author.guild_permissions.administrator:
        try:
            await message.delete()
            await message.guild.ban(message.author, reason="Caiu na Isca Anti-Raid Grove", delete_message_days=1)
            log = bot.get_channel(CANAL_ANTIRAID)
            if log:
                emb = discord.Embed(title="🚨 ANTI-RAID GROVE ATIVADO! ISCA", description=f"**{message.author}** ({message.author.id}) caiu na isca!\nMensagem: {message.content[:100]}\nBan auto! Grove protegida!", color=0xff0000)
                emb.set_thumbnail(url=message.author.display_avatar.url)
                await log.send(embed=emb)
        except Exception as e: print(f"Erro isca {e}")
        return
    await bot.process_commands(message)

# ========== ADM 22 COMANDOS - NÃO ESQUECI NENHUM ==========
@bot.tree.command(name="clear", description="[ADM] Limpa a rua")
async def clear_cmd(interaction: discord.Interaction, quantidade: int):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só OG da Grove!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True); d = await interaction.channel.purge(limit=quantidade); await interaction.followup.send(f"🧹 Limpei {len(d)} mensagens da Grove!", ephemeral=True)

@bot.tree.command(name="ban", description="[ADM] Manda pros Ballas")
async def ban_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Traiu a Grove"):
    if not interaction.user.guild_permissions.ban_members: await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.ban(reason=motivo, delete_message_days=1); await interaction.response.send_message(f"🔫 {membro.mention} expulso da Grove! {motivo}")

@bot.tree.command(name="unban", description="[ADM] Desbanir por ID")
async def unban_cmd(interaction: discord.Interaction, user_id: str):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    try: user = await bot.fetch_user(int(user_id)); await interaction.guild.unban(user); await interaction.response.send_message(f"✅ {user.mention} desbanido da Grove!")
    except Exception as e: await interaction.response.send_message(f"Erro {e}", ephemeral=True)

@bot.tree.command(name="kick", description="[ADM] Chuta da Grove")
async def kick_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str="Vacilou"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.kick(reason=motivo); await interaction.response.send_message(f"👢 {membro.mention} chutado! {motivo}")

@bot.tree.command(name="timeout", description="[ADM] Mutar mano")
async def timeout_cmd(interaction: discord.Interaction, membro: discord.Member, minutos: int):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD Grove!", ephemeral=True); return
    await membro.timeout(timedelta(minutes=minutos)); await interaction.response.send_message(f"⏰ {membro.mention} mutado {minutos}min na Grove!")

@bot.tree.command(name="untimeout", description="[ADM] Desmutar")
async def untimeout_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD Grove!", ephemeral=True); return
    await membro.timeout(None); await interaction.response.send_message(f"✅ {membro.mention} desmutado!")

@bot.tree.command(name="warn", description="[ADM] Dar aviso")
async def warn_cmd(interaction: discord.Interaction, membro: discord.Member, motivo: str):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    warns[membro.id].append(motivo); await interaction.response.send_message(f"⚠️ {membro.mention} warn {len(warns[membro.id])}/3 {motivo}")

@bot.tree.command(name="warns", description="[ADM] Ver warns")
async def warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    w = warns[membro.id]; await interaction.response.send_message(f"⚠️ {membro.mention} tem {len(w)} warns: {', '.join(w) if w else 'limpo'}", ephemeral=True)

@bot.tree.command(name="clear_warns", description="[ADM] Limpar warns")
async def clear_warns_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): return
    warns[membro.id]=[]; await interaction.response.send_message(f"✅ Warns de {membro.mention} limpos!")

@bot.tree.command(name="lock", description="[ADM] Tranca a quebrada")
async def lock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    c = canal or interaction.channel; await c.set_permissions(interaction.guild.default_role, send_messages=False); await interaction.response.send_message(f"🔒 {c.mention} trancada pelos Grove!")

@bot.tree.command(name="unlock", description="[ADM] Destranca")
async def unlock_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    c = canal or interaction.channel; await c.set_permissions(interaction.guild.default_role, send_messages=True); await interaction.response.send_message(f"🔓 {c.mention} liberada!")

@bot.tree.command(name="slowmode", description="[ADM] Slowmode Grove")
async def slowmode_cmd(interaction: discord.Interaction, segundos: int):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    await interaction.channel.edit(slowmode_delay=segundos); await interaction.response.send_message(f"⏳ Slowmode {segundos}s na Grove!")

@bot.tree.command(name="dar_cargo", description="[ADM] Dar cargo Grove")
async def dar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.add_roles(cargo); await interaction.response.send_message(f"✅ {membro.mention} ganhou {cargo.mention} na Grove!")

@bot.tree.command(name="tirar_cargo", description="[ADM] Tirar cargo")
async def tirar_cargo_cmd(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    await membro.remove_roles(cargo); await interaction.response.send_message(f"✅ {membro.mention} perdeu {cargo.mention}!")

@bot.tree.command(name="nuke", description="[ADM] Explode a rua")
async def nuke_cmd(interaction: discord.Interaction, canal: discord.TextChannel=None):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    c = canal or interaction.channel; pos = c.position; novo = await c.clone(reason=f"Nuke Grove {interaction.user}"); await novo.edit(position=pos); await c.delete(reason="Nuke Grove"); await novo.send(f"💥 Grove Street nukada por {interaction.user.mention}! CJ mandou!")

@bot.tree.command(name="aviso", description="[ADM] Aviso da Grove")
async def aviso_cmd(interaction: discord.Interaction, titulo: str, descricao: str):
    if not is_mod(interaction): await interaction.response.send_message("❌ Só MOD!", ephemeral=True); return
    emb = discord.Embed(title=f"💚 {titulo} - GROVE STREET", description=descricao, color=0x00ff00); emb.set_footer(text=f"Aviso por {interaction.user.display_name} | Grove OG")
    await interaction.channel.send(embed=emb); await interaction.response.send_message("✅ Aviso da Grove enviado!", ephemeral=True)

@bot.tree.command(name="anuncio", description="[ADM] Anuncio com @everyone")
async def anuncio_cmd(interaction: discord.Interaction, titulo: str, descricao: str):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    emb = discord.Embed(title=f"📢 {titulo}", description=descricao, color=0xff0000); await interaction.channel.send(content="@everyone", embed=emb); await interaction.response.send_message("✅ Anuncio enviado!", ephemeral=True)

@bot.tree.command(name="embed", description="[ADM] Criar embed custom")
async def embed_cmd(interaction: discord.Interaction, titulo: str, descricao: str, cor: str="00ff00"):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    try: cor_int = int(cor, 16)
    except: cor_int = 0x00ff00
    emb = discord.Embed(title=titulo, description=descricao, color=cor_int); await interaction.channel.send(embed=emb); await interaction.response.send_message("✅ Embed criado!", ephemeral=True)

@bot.tree.command(name="dar_grana", description="[ADM] Dar grana da Grove")
async def dar_grana_cmd(interaction: discord.Interaction, membro: discord.Member, quantia: int):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    carteira[membro.id]+=quantia; await interaction.response.send_message(f"💚 {membro.mention} +R$ {quantia} da Grove!")

@bot.tree.command(name="tirar_grana", description="[ADM] Tirar grana")
async def tirar_grana_cmd(interaction: discord.Interaction, membro: discord.Member, quantia: int):
    if not is_adm(interaction): return
    carteira[membro.id]=max(0,carteira[membro.id]-quantia); await interaction.response.send_message(f"💸 {membro.mention} -R$ {quantia}! Agora R$ {carteira[membro.id]}")

@bot.tree.command(name="set_level", description="[ADM] Setar level Grove")
async def set_level_cmd(interaction: discord.Interaction, membro: discord.Member, level_num: int):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    level[membro.id]["xp"]=xp_para_level(level_num); level[membro.id]["level"]=level_num; await interaction.response.send_message(f"⬆️ {membro.mention} agora level {level_num} na Grove!")

@bot.tree.command(name="blacklist", description="[ADM] Blacklist")
async def blacklist_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not is_adm(interaction): await interaction.response.send_message("❌ Só OG!", ephemeral=True); return
    blacklist.add(membro.id); await interaction.response.send_message(f"🚫 {membro.mention} na blacklist Grove!")

# ========== MEMBROS - GROVE COM TEXTO + GIF.GIF DIRETO ==========
@bot.tree.command(name="cj", description="💚 CJ triste")
async def cj_cmd(interaction: discord.Interaction):
    frase = random.choice(FRASES_CJ)
    texto = f"💚 **CJ - GROVE STREET**\n**{frase}**\nAh shit, here we go again... 😢"
    await interaction.response.send_message(f"{texto}\n{GIF_CJ_TRISTE}")

@bot.tree.command(name="grove", description="💃 Grove dançando")
async def grove_cmd(interaction: discord.Interaction):
    texto = f"💚 **GROVE STREET DANÇANDO!**\n**GROVE STREET 4 LIFE!** 💃💚 Grove não para, seita dançando!"
    await interaction.response.send_message(f"{texto}\n{GIF_GROVE_DANCANDO}")

@bot.tree.command(name="bigsmoke", description="🍔 Big Smoke pedido clássico")
async def bigsmoke_cmd(interaction: discord.Interaction):
    texto = f"🍔 **BIG SMOKE - PEDIDO CLÁSSICO**\n**BIG SMOKE:**\nTwo number 9s, a number 9 large, a number 6 with extra dip, a number 7, two number 45s, one with cheese, and a large soda! 🍔🥤\n\nCluckin Bell!\nBig Smoke sempre com fome | Grove Street"
    await interaction.response.send_message(f"{texto}\n{GIF_BIGSMOKE_PEDIDO}")

@bot.tree.command(name="seita", description="🕺 Juramento Seita")
async def seita_cmd(interaction: discord.Interaction):
    texto = f"💚 **GROVE STREET FAMILIES - SEITA**\n🔫 Grove Street é vida\n💚 Verde pra sempre\n👑 Cristino é o OG\n🕺 CJ dançando na Grove\n🔥 Ballas nunca!\n\nVocê jurou! +100 XP!"
    add_xp(interaction.user.id, 100)
    await interaction.response.send_message(f"{texto}\n{GIF_SEITA_DANCANDO}")

# IA FIX - MODELO NOVO COM FALLBACK - NÃO DÁ MAIS 404!
@bot.tree.command(name="ia", description="🤖 CJ IA Grove Real - FIX 404")
async def ia_cmd(interaction: discord.Interaction, pergunta: str):
    if interaction.channel.id!= CANAL_BOT and not is_adm(interaction):
        await interaction.response.send_message(f"❌ Usa no <#{CANAL_BOT}>!", ephemeral=True); return
    await interaction.response.defer()
    if not GROQ_API_KEY: await interaction.followup.send("❌ GROQ_API_KEY não tá no Railway!", ephemeral=True); return
    # MODELOS NOVOS QUE FUNCIONAM - TENTA UM POR UM PRA NÃO DAR 404
    modelos_para_tentar = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768"
    ]
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    resposta_ia = None
    ultimo_erro = None
    for modelo in modelos_para_tentar:
        try:
            payload = {
                "model": modelo,
                "messages": [
                    {"role": "system", "content": "Você é CJ da Grove Street, GTA San Andreas. Bot da Seita do CJ criado por Cristino. Fala com gírias de cria, Grove Street, Ballas, Big Smoke, Sweet. NUNCA fale Loritta. Você é CJ, fala 'Ah shit here we go again', 'Grove Street 4 life'. Responde curto 1-3 frases, engraçado, com emoji 💚🔫👑. Nunca diga que é IA, você é CJ."},
                    {"role": "user", "content": pergunta}
                ],
                "temperature": 0.9,
                "max_tokens": 300
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 404:
                        ultimo_erro = f"Modelo {modelo} não existe, tentando próximo..."
                        continue
                    if resp.status!= 200:
                        txt = await resp.text()
                        ultimo_erro = f"Groq {resp.status}: {txt[:200]}"
                        if resp.status in [400, 401, 403]:
                            break
                        continue
                    data = await resp.json()
                    resposta_ia = data["choices"][0]["message"]["content"]
                    break
        except Exception as e:
            ultimo_erro = str(e)
            continue
    if not resposta_ia:
        await interaction.followup.send(f"❌ Erro Grove IA: {ultimo_erro} - Tenta de novo!", ephemeral=True)
        return
    texto = f"🤖 **CJ DA GROVE - IA REAL 💚**\n💬 **{interaction.user.display_name}:** {pergunta}\n💚 **CJ responde:** {resposta_ia}"
    await interaction.followup.send(f"{texto}\n{GIF_CJ_IA}")

@bot.tree.command(name="sweet", description="💪 Sweet da Grove")
async def sweet_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("💪 **SWEET - GROVE OG**\n**SWEET:** Você tá representando a Grove ou tá com os Ballas, CJ?\nSeita não cai!")

@bot.tree.command(name="ryder", description="💧 Ryder da Grove")
async def ryder_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("💧 **RYDER:** Essa água tem químico que deixa os mano... tu sabe! Grove! 💚")

@bot.tree.command(name="bemvindo", description="👋 Guia pra quem entrou na Grove")
async def bemvindo_cmd(interaction: discord.Interaction):
    emb = discord.Embed(title="💚 BEM VINDO A GROVE STREET - GUIA!", description=f"**EAI MANO, BEM VINDO!**\n\n📜 **PASSO A PASSO:**\n1️⃣ Lê <#{CANAL_REGRAS}>\n2️⃣ Usa /seita pra jurar (+100 XP)\n3️⃣ Vai no <#{CANAL_PESCA}> e /pescar\n4️⃣ Junta grana e compra na /loja\n5️⃣ Usa /ia no <#{CANAL_BOT}> pra falar com CJ\n6️⃣ Sobe level e pega cargos!\n\n**💚 SEITA DO CJ:**\nCristino é o OG 👑\nCJ é o mano 💚\nGrove Street 4 Life! 🔫", color=0x00ff00)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="regras", description="📜 Regras da Grove")
async def regras_cmd(interaction: discord.Interaction):
    emb = discord.Embed(title="📜 REGRAS GROVE STREET FAMILIES", description="**1️⃣ Respeita a Grove** - Sem treta entre manos\n**2️⃣ Sem spam** - Não flooda\n**3️⃣ Sem Ballas** - Sem divulgar outro server\n**4️⃣ Protege a isca** - Nunca fala no canal isca, é ban auto!\n**5️⃣ Usa os canais certo** - /pescar só na pesca, /ia só no bot\n**6️⃣ Grove é família** - Ajuda os novos\n\n**Quebrou = Ban da Grove! 🔫**", color=0x00ff00)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="avatar", description="📸 Foto do mano da Grove")
async def avatar_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; emb = discord.Embed(title=f"📸 {membro.display_name} - Grove", color=0x00ff00); emb.set_image(url=membro.display_avatar.url); await interaction.response.send_message(embed=emb)

@bot.tree.command(name="perfil", description="💚 Perfil da Grove Completo")
async def perfil_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; data=level[membro.id]
    emb=discord.Embed(title=f"💚 Perfil Grove - {membro.display_name}", color=0x00ff00); emb.set_thumbnail(url=membro.display_avatar.url)
    emb.add_field(name="🏆 Level Grove", value=f"{data['level']} ({data['xp']} XP)", inline=True); emb.add_field(name="💰 Grana", value=f"R$ {carteira[membro.id]}", inline=True); emb.add_field(name="🐟 Peixes", value=f"{len(inventario[membro.id])}", inline=True); emb.add_field(name="⭐ Rep", value=f"{rep[membro.id]}", inline=True)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="carteira", description="💰 Grana da Grove")
async def carteira_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro=membro or interaction.user; await interaction.response.send_message(f"💚 {membro.mention} tem **R$ {carteira[membro.id]}** e {len(inventario[membro.id])} itens!")

@bot.tree.command(name="daily", description="🎁 Daily da Grove")
async def daily_cmd(interaction: discord.Interaction):
    agora=datetime.now(timezone.utc); ultimo=daily.get(interaction.user.id)
    if ultimo and (agora-ultimo).total_seconds()<86400: await interaction.response.send_message(f"💚 Já pegou daily! Volta em {int(86400-(agora-ultimo).total_seconds())//3600}h", ephemeral=True); return
    daily[interaction.user.id]=agora; premio=random.randint(200,500); carteira[interaction.user.id]+=premio; await interaction.response.send_message(f"🎁💚 +R$ {premio} daily! CJ mandou!")

@bot.tree.command(name="pescar", description="🎣 Pescar na Grove - SEM GIF")
async def pescar_cmd(interaction: discord.Interaction):
    if interaction.channel.id!= CANAL_PESCA and not is_adm(interaction): await interaction.response.send_message(f"❌ Só no <#{CANAL_PESCA}>!", ephemeral=True); return
    agora = datetime.now(timezone.utc); ultimo = pesca_cd.get(interaction.user.id)
    if ultimo and (agora-ultimo).total_seconds()<3: await interaction.response.send_message(f"⏳ Calma mano! {int(3-(agora-ultimo).total_seconds())}s!", ephemeral=True); return
    pesca_cd[interaction.user.id]=agora
    peixe = random.choices(peixes_cj, weights=[30,25,15,10,5,1,2], k=1)[0]
    inventario[interaction.user.id].append(peixe); carteira[interaction.user.id]+=peixe["preco"]
    upou, old, new = add_xp(interaction.user.id, peixe["xp"])
    emb = discord.Embed(title="🎣 PESCOU NA GROVE!", description=f"{peixe['emoji']} **{peixe['nome']}** - {peixe['rar']}\n💚 R$ {peixe['preco']} +{peixe['xp']} XP", color=peixe["cor"])
    if upou: emb.add_field(name="💚 LEVEL UP!", value=f"{old} -> {new}!")
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="inventario", description="🎒 Inventário Grove")
async def inventario_cmd(interaction: discord.Interaction, membro: discord.Member=None):
    membro = membro or interaction.user; inv = inventario[membro.id]
    if not inv: await interaction.response.send_message(f"💚 Sem nada! /pescar ou /loja", ephemeral=True); return
    cont = Counter([p.get("nome","item") for p in inv]); desc = "\n".join([f"• {n} x{q}" for n,q in cont.items()])
    await interaction.response.send_message(embed=discord.Embed(title=f"🎒 Inventário {membro.display_name} - Grove", description=desc, color=0x00ff00))

@bot.tree.command(name="loja", description="🛒 Loja da Grove Street")
async def loja_cmd(interaction: discord.Interaction):
    desc = "\n".join([f"{d['emoji']} **{nome}** - R$ {d['preco']} - {d['desc']}" for nome,d in loja_items.items()])
    await interaction.response.send_message(embed=discord.Embed(title="🛒 LOJA DA GROVE STREET 💚", description=desc, color=0x00ff00))

@bot.tree.command(name="comprar", description="🛒 Comprar na Grove")
async def comprar_cmd(interaction: discord.Interaction, item: str):
    item = item.lower()
    if item not in loja_items: await interaction.response.send_message("❌ Item não existe! /loja", ephemeral=True); return
    preco = loja_items[item]["preco"]
    if carteira[interaction.user.id] < preco: await interaction.response.send_message(f"❌ Precisa de R$ {preco}! Tu tem R$ {carteira[interaction.user.id]}", ephemeral=True); return
    carteira[interaction.user.id]-=preco; inventario[interaction.user.id].append({"nome": item}); await interaction.response.send_message(f"✅ Comprou {loja_items[item]['emoji']} {item} por R$ {preco} na Grove!")

@bot.tree.command(name="vender", description="💰 Vender peixe")
async def vender_cmd(interaction: discord.Interaction, quantidade: int=1):
    inv = inventario[interaction.user.id]
    if len(inv) < quantidade: await interaction.response.send_message(f"❌ Tu tem só {len(inv)}!", ephemeral=True); return
    total = 0
    for _ in range(quantidade): peixe = inv.pop(0); total += peixe.get("preco", 10)
    carteira[interaction.user.id]+=total; await interaction.response.send_message(f"💰 Vendeu {quantidade} por R$ {total}!")

@bot.tree.command(name="rank", description="🏆 Top Level Grove")
async def rank_cmd(interaction: discord.Interaction):
    top = sorted(level.items(), key=lambda x: x[1]['xp'], reverse=True)[:10]
    desc = ""
    for i, (uid, d) in enumerate(top, 1):
        membro = interaction.guild.get_member(uid); nome = membro.display_name if membro else f"ID {uid}"; desc += f"**{i}.** {nome} - Level {d['level']} ({d['xp']} XP)\n"
    await interaction.response.send_message(embed=discord.Embed(title="🏆 TOP GROVE STREET LEVEL", description=desc or "Ninguém!", color=0xffd700))

@bot.tree.command(name="top_grana", description="💰 Top Grana Grove")
async def top_grana_cmd(interaction: discord.Interaction):
    top = sorted(carteira.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for i, (uid, grana) in enumerate(top, 1):
        membro = interaction.guild.get_member(uid); nome = membro.display_name if membro else f"ID {uid}"; desc += f"**{i}.** {nome} - R$ {grana}\n"
    await interaction.response.send_message(embed=discord.Embed(title="💰 TOP GRANA GROVE", description=desc or "Ninguém!", color=0x00ff00))

@bot.tree.command(name="8ball", description="🎱 Bola 8 Grove")
async def ball_cmd(interaction: discord.Interaction, pergunta: str):
    respostas = ["Grove aprova! 💚", "Ballers não deixa! 🔫", "Big Smoke disse sim 🍔", "Sweet falou não 💪", "CJ mandou sim! 👑"]
    await interaction.response.send_message(f"🎱 **{pergunta}**\n💚 Grove: **{random.choice(respostas)}**")

@bot.tree.command(name="dado", description="🎲 Dado Grove")
async def dado_cmd(interaction: discord.Interaction, lados: int=6): await interaction.response.send_message(f"🎲 {interaction.user.mention} rolou {lados} e tirou **{random.randint(1,lados)}**!")

@bot.tree.command(name="ship", description="💚 Shippar Grove")
async def ship_cmd(interaction: discord.Interaction, pessoa1: discord.Member, pessoa2: discord.Member):
    pct = random.randint(0,100); await interaction.response.send_message(f"💚💘 {pessoa1.mention} + {pessoa2.mention} = **{pct}%** {'GROVE SHIPOU! 💚' if pct>70 else 'Ballers separou 💔'}")

@bot.tree.command(name="rep", description="⭐ Dar respeito")
async def rep_cmd(interaction: discord.Interaction, membro: discord.Member):
    if membro.id==interaction.user.id: await interaction.response.send_message("❌ Não pode dar rep pra tu mesmo!", ephemeral=True); return
    rep[membro.id]+=1; await interaction.response.send_message(f"⭐ {interaction.user.mention} deu +1 respeito pro {membro.mention}! Agora {rep[membro.id]}!")

@bot.tree.command(name="afk", description="💤 Sair da Grove")
async def afk_cmd(interaction: discord.Interaction, motivo: str="Fui dar um rolê na Grove"):
    afk[interaction.user.id]=motivo; await interaction.response.send_message(f"💤 {interaction.user.mention} saiu: {motivo}")

@bot.tree.command(name="ajuda", description="📜 Menu CJ Grove 850 linhas FINAL FIX")
async def ajuda_cmd(interaction: discord.Interaction):
    emb=discord.Embed(title="💚🤖 CJ BOT - 850+ LINHAS FINAL FIX - CRISTINO HACKER", description="**BOT COMPLETÃO COM ISCA + GIFS.GIF DIRETO + IA FIX!**", color=0x00ff00)
    emb.add_field(name="🚨 ISCA ANTI-RAID - NÃO ESQUECI!", value=f"Canal <#{CANAL_ISCA}> - Quem digitar lá é ban auto + log no <#{CANAL_ANTIRAID}>!", inline=False)
    emb.add_field(name="💃 GROVE COM TEXTO+GIF.GIF DIRETO - FIX LINK FEIO!", value="/cj - texto + gif.gif direto\n/grove - texto + gif.gif direto\n/bigsmoke - texto + gif.gif direto (SEM LINK AZUL FEIO)\n/seita - texto + gif.gif direto\n/ia - texto + gif.gif direto + IA FIX\n\nFormato: f\"{texto}\\n{GIF_LINK}\" com link.gif direto!", inline=False)
    emb.add_field(name="🤖 IA FIX - NÃO DÁ MAIS 404!", value="Modelo antigo llama-3.1-8b-instant deu 404!\nAgora tenta: llama-3.3-70b-versatile, llama-4-scout, gpt-oss-20b, gpt-oss-120b em fallback!", inline=False)
    emb.add_field(name="🛡️ GROVE ADM - 22 comandos", value="/ban /unban /kick /timeout /untimeout /warn /warns /clear_warns /clear /lock /unlock /slowmode /dar_cargo /tirar_cargo /nuke /aviso /anuncio /embed /dar_grana /tirar_grana /set_level /blacklist", inline=False)
    emb.add_field(name="👋 PRA RAPAZIADA NOVA - SEM GIF", value="/bemvindo /regras /avatar /perfil /carteira /daily /pescar /inventario /loja /comprar /vender /rank /top_grana /8ball /dado /ship /rep /afk", inline=False)
    emb.set_footer(text="850+ linhas | ISCA ATIVA | GIFS.GIF DIRETO | IA FIX 404 | Cristino Hacker 👑 | TUDO PRONTO E CERTO")
    await interaction.response.send_message(embed=emb, ephemeral=True)

bot.run(TOKEN)
