import os
import random
import discord
from openai import OpenAI
from discord.ext import commands
from discord import app_commands
from collections import deque
from datetime import datetime, timezone
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

TOKEN = os.getenv("TOKEN")
CANAL_BOAS_VINDAS = 1558857282702409749
CANAL_LOGS = 1559066250410197013
CANAL_ISCA = 1559066250410197013

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

anti_raid_ativado = True
recent_joins = deque()

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    synced = await bot.tree.sync()
    print(f"Sync: {len(synced)} comandos -> {[c.name for c in synced]}")

@bot.tree.command(name="antiraid", description="Controle do anti-raid")
async def antiraid(interaction: discord.Interaction, acao: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Só ADM!", ephemeral=True)
        return
    global anti_raid_ativado
    if acao == "on":
        anti_raid_ativado = True
        await interaction.response.send_message("✅ ANTI-RAID LIGADO", ephemeral=True)
    elif acao == "off":
        anti_raid_ativado = False
        await interaction.response.send_message("❌ ANTI-RAID DESLIGADO", ephemeral=True)
    else:
        await interaction.response.send_message(f"Status: {'ON' if anti_raid_ativado else 'OFF'}", ephemeral=True)

@antiraid.autocomplete("acao")
async def ac_auto(interaction, current):
    return [app_commands.Choice(name=v, value=v) for v in ["on","off","status"] if current.lower() in v]

@bot.tree.command(name="ping", description="Ver o ping do bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong {round(bot.latency*1000)}ms")

@bot.tree.command(name="clear", description="Apagar mensagens")
async def clear(interaction: discord.Interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=quantidade)
    await interaction.followup.send(f"Apaguei {quantidade}", ephemeral=True)

@bot.tree.command(name="ban", description="Banir usuario")
async def ban(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    await membro.ban(reason=motivo, delete_message_days=1)
    await interaction.response.send_message(f"{membro.mention} BANIDO - {motivo}")
    # LOG PRO PAINEL
    with open("/home/Cristino/bot.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%d/%m %H:%M')}] BAN - {membro} foi banido por {interaction.user} | Motivo: {motivo}\n")

@bot.tree.command(name="kick", description="Kikar usuario")
async def kick(interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    await membro.kick(reason=motivo)
    await interaction.response.send_message(f"{membro.mention} KIKADO - {motivo}")
    # LOG PRO PAINEL
    with open("/home/Cristino/bot.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%d/%m %H:%M')}] KICK - {membro} foi kickado por {interaction.user} | Motivo: {motivo}\n")

@bot.command(name="cj")
async def cj(ctx):
    await ctx.send(f"{ctx.author.mention} Para de me marcar big smoke~kun")

@bot.command(name="zoeira")
async def zoeira(ctx):
    await ctx.send("Procurou zoeira achou bait, seu miseravel kkkkkkkkkkk")
    await ctx.send("https://cdn.discordapp.com/attachments/743996477227008010/1338093043429150760/meandwho2.gif?ex=6aceaf82&is=6acd5e02&hm=50f2e27aa6f11fe20ba07e8225f43f871d45595fb9d82a8e14e7e73fcac7df10")

@bot.event
async def on_member_join(member):
    canal_bv = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal_bv:
        try: await canal_bv.send(f"Boas vindas a Seita Do CJ Vascaino Baiano {member.mention}! ")
             await canal_bv.send(f"https://klipy.com/gifs/cj-and-sweet-cj-gta-sa")
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
            if canal_log: await canal_log.send(f"🚨 KICK: {member} | {idade} dias")
        except: pass
        return
    if len(recent_joins) >= 5:
        try:
            await member.ban(reason="Raid", delete_message_days=1)
            if canal_log: await canal_log.send(f"🔥 RAID: {member} BANIDO")
        except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == CANAL_ISCA:
        if message.author.guild_permissions.administrator:
            await bot.process_commands(message)
            return
        try:
            await message.delete()
            await message.guild.ban(message.author, reason="Isca", delete_message_days=1)
        except: pass
        return
    await bot.process_commands(message)
    
import random
from collections import defaultdict

inventario_db = defaultdict(list)
carteira_db = defaultdict(int)

lista_de_peixes = [
    {"nome": "Bota Velha", "emoji": "🥾", "raridade": "Lixo", "preco": 2},
    {"nome": "Sardinha", "emoji": "🐟", "raridade": "Comum", "preco": 10},
    {"nome": "Tilápia", "emoji": "🐟", "raridade": "Comum", "preco": 15},
    {"nome": "Baiacu", "emoji": "🐡", "raridade": "Raro", "preco": 50},
    {"nome": "Tubarão", "emoji": "🦈", "raridade": "Lendário", "preco": 250},
]

@bot.tree.command(name="pescar", description="Pesque um peixe e ganhe dinheiro")
async def pescar(interaction: discord.Interaction):
    peixe = random.choice(lista_de_peixes)
    inventario_db[interaction.user.id].append(peixe)
    carteira_db[interaction.user.id] += peixe["preco"]
    embed = discord.Embed(title="🎣 Você pescou!", description=f"Você pescou um **{peixe['nome']}** {peixe['emoji']}!\nRaridade: {peixe['raridade']}\nValor: R$ {peixe['preco']}", color=0x00ff00)
    embed.set_footer(text=f"Carteira: R$ {carteira_db[interaction.user.id]}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventario", description="Veja seu inventário de pesca")
async def inventario(interaction: discord.Interaction):
    itens = inventario_db[interaction.user.id]
    if not itens:
        await interaction.response.send_message("Inventário vazio. Use /pescar!", ephemeral=True)
        return
    from collections import Counter
    c = Counter([f"{p['emoji']} {p['nome']}" for p in itens])
    desc = "\n".join([f"{q}x {nome}" for nome, q in c.items()])
    embed = discord.Embed(title=f"🎒 Inventário de {interaction.user.display_name}", description=desc, color=0x0099ff)
    embed.set_footer(text=f"Carteira: R$ {carteira_db[interaction.user.id]}")
    await interaction.response.send_message(embed=embed)
    
import os
client_ia = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


@bot.tree.command(name="ia", description="Pergunte qualquer coisa pra IA")
async def ia(interaction: discord.Interaction, pergunta: str):
    await interaction.response.defer() # pensa

    try:
        resposta = client_ia.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "voce e o CJ, seja gangstar e legal no server do..."},
                {"role": "user", "content": pergunta}
            ]
        )
        texto = resposta.choices[0].message.content
        await interaction.followup.send(f"**Você:** {pergunta}\n**IA:** {texto}")
    except Exception as e:
        await interaction.followup.send(f"Erro na IA: {e}")

    
@bot.command()
async def desligar(ctx):
    if ctx.author.id != 1461916890854068309: return
    await bot.change_presence(status=discord.Status.invisible)
    await ctx.send("Fingi que desliguei 😴")

@bot.command()
async def ligar(ctx):
    if ctx.author.id != 1461916890854068309: return
    await bot.change_presence(status=discord.Status.online)
    await ctx.send("Voltei, seu miserável aff")
    
bot.run(TOKEN)

