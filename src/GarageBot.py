import discord
import asyncio
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import pytz
from discord.ext import commands

from SerrureNDL import *

paris_timezone = pytz.timezone('Europe/Paris')

# --- Healthcheck HTTP server ---

bot_ready = False

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" and bot_ready:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"not ready")

    def log_message(self, format, *args):
        pass  # Silence request logs

def start_healthcheck_server():
    port = int(os.getenv("HEALTHCHECK_PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Healthcheck server started on port {port}")

# --- Bot ---

class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="&&", intents=discord.Intents.all())
    
    async def on_ready(self) -> None:
        global bot_ready
        bot_ready = True
        await self.tree.sync()
        asyncio.create_task(purge_outdated_otp_task())
        asyncio.create_task(manage_log_task())

        print("Connected")
    
async def purge_outdated_otp_task():
    while True:
        status = PurgeOutdatedOTP()
        print(f"Purge des otp : {status}")
        await asyncio.sleep(int(os.getenv("PURGE_FREQ"))) # Purge every hour


async def manage_log_task():
    log_file_path = "./log/CodeLog.txt"
    while True:
        if os.path.exists(log_file_path):
            file_size = os.path.getsize(log_file_path)
            if file_size >= 20*1024*1024: #20 MB
                archive_name = 'CodeLog-Archive-{}.bak'.format(datetime.now().strftime('%Y-%m-%d'))
                archive_path = f"./log/{archive_name}"
                os.rename(log_file_path, archive_path)
                with open(log_file_path, 'w') as new_log_file:
                    print("new log file created")
        await asyncio.sleep(24*3600) # everyday


bot = Bot()

@bot.tree.command(name="owner", description="Donne le pseudo du propriétaire du serveur")
async def owner_command(interaction: discord.Interaction):
    owner = bot.get_user(int(interaction.guild.owner.id))
    await interaction.response.send_message(f"{owner} est le propriétaire du serveur", ephemeral=True)


@bot.tree.command(name="ping", description="Donne le ping du bot")
async def ping_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)


@bot.tree.command(name="add_member", description="Ajoute un membre dans le lab")
async def addMember_command(interaction: discord.Interaction, pseudo: discord.User, role: discord.Role):
    auteur = interaction.user
    Prez_Role = discord.utils.get(interaction.guild.roles, name=f"Prez - {role.name}")
    VicePrez_Role = discord.utils.get(interaction.guild.roles, name=f"VicePrez - {role.name}")
    Admin_Role = discord.utils.get(interaction.guild.roles, id=int(os.getenv("DISCORD_ROLE_ADMIN_ID")))
    if not (Prez_Role in auteur.roles or VicePrez_Role in auteur.roles or Admin_Role in auteur.roles):
        await interaction.response.send_message("Vous n'avez pas la permission de faire ça. Vous devez être Prez ou VicePrez du lab concerné.", ephemeral=True)
        return
    await pseudo.add_roles(role)
    await pseudo.add_roles(discord.utils.get(interaction.guild.roles, id=int(os.getenv("DISCORD_ROLE_MEMBRE_ID"))))
    await interaction.response.send_message("Done !", ephemeral=True)

@bot.tree.command(name="remove_member", description="Retire un membre du lab")
async def removeMember_command(interaction: discord.Interaction, pseudo: discord.User, role: discord.Role):
    auteur = interaction.user
    Prez_Role = discord.utils.get(interaction.guild.roles, name=f"Prez - {role.name}")
    VicePrez_Role = discord.utils.get(interaction.guild.roles, name=f"VicePrez - {role.name}")
    Admin_Role = discord.utils.get(interaction.guild.roles, id=int(os.getenv("DISCORD_ROLE_ADMIN_ID")))
    if not (Prez_Role in auteur.roles or VicePrez_Role in auteur.roles or Admin_Role in auteur.roles):
        await interaction.response.send_message("Vous n'avez pas la permission de faire ça. Vous devez être Prez ou VicePrez du lab concerné.", ephemeral=True)
        return
    await pseudo.remove_roles(role)
    await interaction.response.send_message("Done !", ephemeral=True)

@bot.tree.command(name="code_ndl", description="Génère un code pour le local NDL (durée custom pour les admins)")
async def code_ndl(interaction: discord.Interaction, duree: int = None):
    codeRole = discord.utils.get(interaction.guild.roles, id=int(os.getenv("DISCORD_ROLE_CODE_ID")))
    adminRole = discord.utils.get(interaction.guild.roles, id=int(os.getenv("DISCORD_ROLE_ADMIN_ID")))
    is_admin = adminRole in interaction.user.roles

    if not (codeRole in interaction.user.roles or is_admin):
        await interaction.response.send_message("Vous n'avez pas la permission de faire ça. Demandez à un Admin.", ephemeral=True)
        return

    if duree is not None and not is_admin:
        await interaction.response.send_message("Seuls les admins peuvent spécifier une durée custom.", ephemeral=True)
        return

    otp_duration = duree if (duree is not None and is_admin) else int(os.getenv("OTP_DURATION"))

    name = interaction.user.name
    for k in range(3): # Add salt to the name to avoid conflict
        name += str(random.randint(1,9))

    code = AddOTP_D(name, otp_duration)
    with open("./log/CodeLog.txt", "a") as f:
        f.write(f"{datetime.now(paris_timezone)},{interaction.user.display_name},{interaction.user.name},{interaction.user.id},{code},{otp_duration}\n")

    await interaction.user.send(f"Le code est {code}, il est valide pour {otp_duration} minutes.")
    await interaction.response.send_message(f"Le code est {code}, valide {otp_duration} min.", ephemeral=True)

#Purge les codes obsolètes - Pas cencé etre utilisé - Debug
@bot.command(name="purge")
async def purge_outdated(ctx):
    admin = discord.utils.get(ctx.guild.roles, id=int(os.getenv("DISCORD_ROLE_ADMIN_ID")))
    if not (admin in ctx.author.roles):
        await ctx.send("Vous n'avez pas la permission de faire ça. Vous devez être Admin.", ephemeral=True)
        return
    status = PurgeOutdatedOTP()
    await ctx.send(f"{status}", ephemeral=True)

@bot.command(name="getlog")
async def get_log(ctx):
    admin = discord.utils.get(ctx.guild.roles, id=int(os.getenv("DISCORD_ROLE_ADMIN_ID")))
    if not (admin in ctx.author.roles):
        await ctx.send("Vous n'avez pas la permission de faire ça. Vous devez être Admin.", ephemeral=True)
        return
    try:
        with open('./log/CodeLog.txt', 'rb') as fp:
            file = discord.File(fp, 'CodeLog.txt')
            await ctx.author.send(file=file)
    except discord.HTTPException as e:
        if e.code == 413:
            await ctx.send("Le fichier est trop volumineux pour être envoyé.", ephemeral=True)
        else:
            await ctx.send("Une erreur s'est produite lors de l'envoi du fichier. Veuillez réessayer.", ephemeral=True)
    except FileNotFoundError:
        await ctx.send("Aucune log", ephemeral=True)

@bot.command(name="forcesync")
async def force_sync(ctx):
    admin = discord.utils.get(ctx.guild.roles, id=int(os.getenv("DISCORD_ROLE_ADMIN_ID")))
    if not (admin in ctx.author.roles):
        await ctx.send("Vous n'avez pas la permission de faire ça. Vous devez être Admin.", ephemeral=True)
        return
    await bot.tree.sync()
    await ctx.send("Done !", ephemeral=True)

if __name__ == "__main__":
    start_healthcheck_server()
    bot.run(os.getenv("DISCORD_GARAGEBOT_TOKEN"))