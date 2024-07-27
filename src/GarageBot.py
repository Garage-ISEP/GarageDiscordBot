import discord
import asyncio
import os
import pytz
from discord.ext import commands

from SerrureNDL import *

paris_timezone = pytz.timezone('Europe/Paris')

class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="&&", intents=discord.Intents.all())
    
    async def on_ready(self) -> None:
        await self.tree.sync()
        asyncio.create_task(purge_outdated_otp_task())
        asyncio.create_task(manage_log_task())

        activity = discord.Activity(type=discord.ActivityType.playing, name="Aider les garagistes")
        await self.change_presence(activity=activity)
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
            file_size = os.path.getsize(log_file_path) #return the size in bytes
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

@bot.tree.command(name="code_ndl", description="Genere un code pour le local de NDL valide 1h")
async def code_ndl(interaction: discord.Interaction):
    codeRole = discord.utils.get(interaction.guild.roles, id=int(os.getenv("DISCORD_ROLE_CODE_ID")))
    if not (codeRole in interaction.user.roles):
        await interaction.response.send_message("Vous n'avez pas la permission de faire ça. Demandez à un Admin.", ephemeral=True)
        return
    
    name = interaction.user.name
    for k in range(3): # Add salt to the name to avoid conflict
        name += str(random.randint(1,9))

    code = AddOTP_D(name, int(os.getenv("OTP_DURATION")))
    with open("./log/CodeLog.txt", "a") as f:
        #append a log line as csv, with time, name, pseudo, id, code, valid time
        f.write(f"{datetime.now(paris_timezone)},{interaction.user.display_name},{interaction.user.name},{interaction.user.id},{code},{os.getenv('OTP_DURATION')}\n")

    await interaction.user.send(f"Le code est {code}, il est valide pour {os.getenv('OTP_DURATION')} minutes.")
    await interaction.response.send_message(f"Le code est {code}", ephemeral=True)

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
    bot.run(os.getenv("DISCORD_GARAGEBOT_TOKEN"))
    
