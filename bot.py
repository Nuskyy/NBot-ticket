import discord
from discord.ext import commands
import requests
import asyncio
import os
import config

# Configuration
if config.TOKEN is None:
    raise ValueError("Le token du bot n'est pas défini. Veuillez définir la variable d'environnement DISCORD_TOKEN.")




GUILD_ID = config.SERVER_ID  
CHANNEL_ID_INFORMATIONS = config.CHANNEL_ID_INFORMATIONS  
USER_IDS_MP_SERVEUR_DOWN = config.USER_IDS_MP_SERVEUR_DOWN
SERVER_IP = config.SERVER_IP
SERVER_PORT = config.SERVER_PORT
SERVER_STATUS_URL = config.SERVER_STATUS_URL
CONNEXION_FIVEM = config.CONNEXION_FIVEM
prefix = config.prefix
ticket_category_id = config.ticket_category_id 
open_ticket = config.open_ticket
close_ticket = config.close_ticket
AUTHORIZED_ROLES = config.AUTHORIZED_ROLES
WELCOME_CHANNEL_ID = config.WELCOME_CHANNEL_ID 




status1 = config.status1
status2 = config.status2


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=config.prefix, intents=intents)


message_id = None # NE PAS TOUCHER
server_message_id = None  # NE PAS TOUCHER
server_was_online = False  # NE PAS TOUCHER


class ConnectButton(discord.ui.View):
    def __init__(self, connexion_url, status_url ):
        super().__init__()
        self.add_item(discord.ui.Button(label="Se Connecter", url=connexion_url))

        self.add_item(discord.ui.Button(label="Status CFX", url=status_url))

class DownButton(discord.ui.View):
    def __init__(self, status_url ):
        super().__init__()
        self.add_item(discord.ui.Button(label="Status CFX", url=status_url))


        

async def check_server_status():
    global message_id, server_message_id, server_was_online
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID_INFORMATIONS)

    while not bot.is_closed():
        try:
            response = requests.get(f'http://{SERVER_IP}:{SERVER_PORT}/info.json', timeout=5)
            if response.status_code == 200:
                
                if message_id is not None:
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                    message_id = None
                if server_message_id is None or not server_was_online:
                    print("Le serveur est en ligne.")
                    embed = discord.Embed(
                        title="🎉 vLand est maintenant en ligne !",
                        description=f"\n Tous nos services fonctionnent \n ",
                        color=discord.Color.green()
                    )
                    view = ConnectButton(CONNEXION_FIVEM, SERVER_STATUS_URL)
                    
                    message = await channel.send(embed=embed,view= view)
                    server_message_id = message.id
                    server_was_online = True
            else:
                raise Exception("Le serveur est hors ligne.")
        except requests.RequestException:
            if message_id is None:
                embed = discord.Embed(
                    title="⚠️ Nous sommes désolés pour le problème rencontré \n",
                    description=f"Après vérification du serveur vLand il s'est mis hors ligne pour des raisons que je ne peux pas vous communiquer.\n \n J'ai contacté Nuskyy pour le tenir au courant.\n \nMerci pour votre attente.",
                    color=discord.Color.red()
                )
                view = DownButton(SERVER_STATUS_URL)
                message = await channel.send(embed=embed, view=view)
                message_id = message.id
                for user_id in USER_IDS_MP_SERVEUR_DOWN:
                    try:
                        user = await bot.fetch_user(user_id)
                        dm_channel = user.dm_channel
                        if dm_channel is None:
                            dm_channel = await user.create_dm()
            
                        await dm_channel.send(f"⚠️ Le serveur 'vLand' est hors ligne !")
                        print(dm_channel)
                    except discord.errors.HTTPException  as e:
                        print(f"Erreur lors de l'envoi du message à l'utilisateur avec l'ID {user_id}: {e}")
            server_was_online = False
            if server_message_id is not None:
                message = await channel.fetch_message(server_message_id)
                await message.delete()
                server_message_id = None
        
        await asyncio.sleep(1)

async def change_status():
    while not bot.is_closed():
        try:
            guild = bot.get_guild(GUILD_ID)
            activity1 = discord.Activity(name=status1, type=discord.ActivityType.watching)
            await bot.change_presence(status=discord.Status.dnd, activity=activity1)
            await asyncio.sleep(5)  
            
            await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=status2))
            await asyncio.sleep(5)  
            
        except discord.HTTPException as e:
            print(f"Error occurred while changing presence: {e}")
        
@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user.name}')
    bot.loop.create_task(check_server_status())
    if config.change_status_bot == 'on': 
        bot.loop.create_task(change_status())
    else: 
        activity1 = discord.Activity(name=config.status, type=discord.ActivityType.watching)
        await bot.change_presence(status=discord.Status.dnd, activity=activity1)


    
    guild = bot.get_guild(GUILD_ID)

    await bot.tree.sync()

    print("Commandes slash :")
    for command in bot.tree.get_commands():
        print(f"- {command.name}")

    if guild:
        try:
            await bot.tree.sync(guild=guild)
            print("Commandes slash synchronisées avec le serveur.")
        except Exception as e:
            print(f"Erreur lors de la synchronisation des commandes slash : {e}")
    else:
        print("Guilde non trouvée.")

@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        
        guild = bot.get_guild(GUILD_ID)
        category = discord.utils.get(guild.categories, id=ticket_category_id)

        if guild and category:
            existing_channel = discord.utils.get(category.channels, name=f'ticket-de-{message.author.name.lower()}')
            
            if existing_channel:
                await existing_channel.send(f"**{message.author}** : {message.content}")
                if message.attachments:
                    for attachment in message.attachments:
                        await existing_channel.send(attachment.url)
            else:
                new_channel = await guild.create_text_channel(f'ticket-de-{message.author.name}', category=category)
                member = guild.get_member(message.author.id)
                if member:
                    joined_date = member.joined_at.strftime('%d/%m/%Y à %H:%M:%S') 
                
                embed = discord.Embed(
                    title="Guide des réponses !",
                    description=f"\n **{message.author.name}** a rejoind le discord le : **{joined_date}**.\n Pour repondre a l'utilisateur **!reply** <votre message> \n Pour fermer le ticket **!close** ",
                    color=discord.Color.green()
                )
                message2 = await new_channel.send(embed=embed)
                server_message_id = message2.id
                server_was_online = True
                await new_channel.send(f"**{message.author}**: {message.content}")
                if message.author.name == 'so_lis':
                    await message.channel.send('ton ticket est en prioriter ma reine')
                else:
                    await message.channel.send(open_ticket)
                if message.attachments:
                    for attachment in message.attachments:
                        await existing_channel.send(attachment.url)        
    if message.author == bot.user:
        return
    if config.protect =='on':
        if message.author == bot.user:
            return
    
        has_authorized_role = any(role.id in AUTHORIZED_ROLES or role.name in AUTHORIZED_ROLES for role in message.author.roles)

        if "https://discord.gg/" in message.content and not has_authorized_role:
        
            await message.delete()

            await message.author.send(config.protect_message)
    else: 
        print('Mode protect is not active')
    await bot.process_commands(message)




@bot.command()
async def close(ctx):
    if ctx.channel.name.startswith("ticket-de-"):
        owner_name = ctx.channel.name.split("ticket-de-")[1]

        user = discord.utils.get(ctx.guild.members, name=owner_name)

        if user:
            dm_channel = user.dm_channel
            if dm_channel is None:
                dm_channel = await user.create_dm()
                
            await dm_channel.send(close_ticket)
            
            await ctx.send(f"Le ticket sera fermé dans quelques instants...")
            await ctx.channel.delete(reason="Ticket fermé par un staff.")
        else:
            await ctx.send("Utilisateur introuvable.")
    else:
        await ctx.send("Ce ticket ne peut pas être fermé avec cette commande.")

@bot.event
async def on_member_join(member):
    if config.welcome == 'on':
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(f"Bienvenue sur le serveur, {member.mention} ! N'hésite pas à consulter les règles et à te présenter.")
    else:
        print('Welcome message not active')

@bot.command()
async def reply(ctx, *, message_content: str = None):
    if message_content is None:
        await ctx.send("Tu dois fournir un message à répondre. Utilise `!reply <message>`.")
        return
    
    if ctx.channel.name.startswith("ticket-de"):
        owner_name = ctx.channel.name.split("ticket-de-")[1]

        user = discord.utils.get(ctx.guild.members, name=owner_name)

        if user:
            top_role_upper = ctx.author.top_role.name.upper()
            author_name_upper = ctx.author.name.upper()
            
            dm_channel = user.dm_channel
            if dm_channel is None:
                dm_channel = await user.create_dm()
            
            
                
            await dm_channel.send(f"** ({top_role_upper}) {author_name_upper}** : {message_content}")

            await ctx.send(f"** ({top_role_upper}) {author_name_upper}** : {message_content}")
            
            if ctx.message.attachments:
                for attachment in ctx.message.attachments:
                    await dm_channel.send(file=await attachment.to_file())
                    await ctx.send(file=await attachment.to_file())
            
            

            
            await ctx.message.delete()
        else:
            await ctx.send("Utilisateur introuvable.")
            
    else:
        await ctx.send("Cette commande ne peut être utilisée que dans un salon privé.")

@bot.tree.command(name="wl", description="La commande vous donne le rôle permettant de vous connecter au serveur")
async def wl(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name="Whitelist")
    if not role:
        await interaction.response.send_message("Le rôle 'Whitelist' n'a pas été trouvé.", ephemeral=True)
        return

    try:
        await interaction.response.defer(ephemeral=True)

        if role in interaction.user.roles:
            await interaction.followup.send("Vous avez déjà le rôle 'Whitelist'.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.followup.send("Vous avez maintenant accès au serveur!", ephemeral=True)

    except discord.Forbidden:
        await interaction.followup.send("Je n'ai pas la permission de vous donner ce rôle.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(f"Une erreur est survenue : {e}", ephemeral=True)


@bot.tree.command(name="ban", description="Bannir un utilisateur du serveur")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Aucune raison spécifiée"):

    if not any(role.name in AUTHORIZED_ROLES or role.id in AUTHORIZED_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("Vous n'avez pas les permissions nécessaires pour bannir des membres.", ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("Je n'ai pas la permission de bannir des membres.", ephemeral=True)
        return
    
    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f"{user.mention} a été banni pour la raison suivante : {reason}")
    except Exception as e:
        await interaction.response.send_message(f"Une erreur s'est produite : {str(e)}")


@bot.tree.command(name="kick", description="Kick un utilisateur du serveur")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Aucune raison spécifiée"):

    if not any(role.name in AUTHORIZED_ROLES or role.id in AUTHORIZED_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("Vous n'avez pas les permissions nécessaires pour bannir des membres.", ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("Je n'ai pas la permission de bannir des membres.", ephemeral=True)
        return
    
    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"{user.mention} a été kick pour la raison suivante : {reason}")
    except Exception as e:
        await interaction.response.send_message(f"Une erreur s'est produite : {str(e)}")


@bot.tree.command(name="addroles", description="Ajouter un rôle à un utilisateur")
async def ban(interaction: discord.Interaction, user: discord.Member, role: discord.Role):

    if not any(role.name in AUTHORIZED_ROLES or role.id in AUTHORIZED_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("Vous n'avez pas les permissions nécessaires pour bannir des membres.", ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("Je n'ai pas la permission de bannir des membres.", ephemeral=True)
        return
    
    try:
        await user.add_roles(role)
        await interaction.response.send_message(f"Le rôle {role.name} a été ajouté à {user.mention}.")
    except Exception as e:
        await interaction.response.send_message(f"Une erreur s'est produite : {str(e)}")


@bot.tree.command(name="removeroles", description="Retirer un rôle à un utilisateur")
async def ban(interaction: discord.Interaction, user: discord.Member, role: discord.Role):

    if not any(role.name in AUTHORIZED_ROLES or role.id in AUTHORIZED_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("Vous n'avez pas les permissions nécessaires pour bannir des membres.", ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("Je n'ai pas la permission de bannir des membres.", ephemeral=True)
        return
    
    try:
        await user.remove_roles(role)
        await interaction.response.send_message(f"Le rôle {role.name} a été retirer à {user.mention}.")
    except Exception as e:
        await interaction.response.send_message(f"Une erreur s'est produite : {str(e)}")





bot.run(config.TOKEN)
