import discord
import asyncio
import os
from discord.ext import commands

from SerrureNDL import *


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="&", intents=discord.Intents.all())
    
    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def on_ready(self) -> None:
        asyncio.create_task(purge_outdated_otp_task())
        print("Connected")
    
async def purge_outdated_otp_task():
    while True:
        status = PurgeOutdatedOTP()
        print(f"Purge des otp : {status}")
        await asyncio.sleep(int(os.getenv("PURGE_FREQ"))) # Purge every hour

bot = Bot()
bot.setup_hook()



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
    if not (Prez_Role in auteur.roles or VicePrez_Role in auteur.roles):
        await interaction.response.send_message("Vous n'avez pas la permission de faire ça. Vous devez être Prez ou VicePrez du lab concerné.", ephemeral=True)
        return
    await pseudo.add_roles(role)
    await pseudo.add_roles(discord.utils.get(interaction.guild.roles, id=int(os.getenv("DISCORD_ROLE_MEMBRE_ID"))))
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
    await interaction.user.send(f"Le code est {code}, il est valide pour {os.getenv('OTP_DURATION')} minutes.")
    await interaction.response.send_message(f"Le code est {code}", ephemeral=True)

@bot.tree.command(name="purge", description="Purge les codes obsolètes - Pas cencé etre utilisé !")
async def purge_outdated(interaction: discord.Interaction):
    admin = discord.utils.get(interaction.guild.roles, name="Admin")
    if not (admin in interaction.user.roles):
        await interaction.response.send_message("Vous n'avez pas la permission de faire ça. Vous devez être Admin.", ephemeral=True)
        return
    status = PurgeOutdatedOTP()
    await interaction.response.send_message(f"{status}", ephemeral=True)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_GARAGEBOT_TOKEN"))
    
