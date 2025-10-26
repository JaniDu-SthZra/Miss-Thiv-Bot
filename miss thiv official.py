import discord
from discord.ext import commands, tasks
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import os
from dotenv import load_dotenv
import sys
sys.stdout.reconfigure(encoding='utf-8')


load_dotenv()
TOKEN = os.getenv("MISS_THIV_TOKEN")  


WELCOME_CHANNEL_ID = 1340615114159816736
GOODBYE_CHANNEL_ID = 896622074200735765
GUILD_ID = 894062577443815434
ROLE_ID = 1419199510709669938
CHANNEL_ID = 899634880395247666
MESSAGE_ID = 1419208532300926997
SUSER_ID = 719951797023932426
SROLE_ID = 1067405890602418256  
LOG_CHANNEL_ID = 1429044953031512157

arrow = "<a:pink:1420493746759536762>"
cyan_heart = "<a:arrow_heartright:1419889005117571123>"
intro = "<a:fg_bun_love:1419889827423191121>"

RULES_CHANNEL_ID = 894069329967079425 
SELFROLES_CHANNEL_ID = 899634880395247666

BACKGROUND_URL = "https://res.cloudinary.com/dzetdzeld/image/upload/v1758714549/welcome_lduwmx.png"
WELCOME_FONT = "fonts/Poppins-Regular.ttf"  


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
status_toggle = 0
streamer_mode = False   


async def create_welcome_image(member):
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BACKGROUND_URL) as resp:
                bg_bytes = await resp.read()
        base = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
    except Exception:
        base = Image.new("RGBA", (800, 400), (30, 30, 30, 255))

    # Load avatar
    async with aiohttp.ClientSession() as session:
        async with session.get(str(member.display_avatar.url)) as resp:
            avatar_bytes = await resp.read()
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar_size = 180
    avatar = avatar.resize((avatar_size, avatar_size))
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
    avatar.putalpha(mask)
    avatar_position = (base.width // 2 - avatar_size // 2, 50)
    base.paste(avatar, avatar_position, avatar)

    # Draw username
    draw = ImageDraw.Draw(base)
    try:
        font_username = ImageFont.truetype(WELCOME_FONT, 36)
    except OSError:
        font_username = ImageFont.load_default()
    text_username = member.name
    bbox = draw.textbbox((0, 0), text_username, font=font_username)
    text_width = bbox[2] - bbox[0]
    draw.text(
        (base.width // 2 - text_width // 2, avatar_position[1] + avatar_size + 30),
        text_username,
        font=font_username,
        fill=(255, 255, 255, 255),
    )

    img_bytes = io.BytesIO()
    base.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    update_status.start()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        img = await create_welcome_image(member)
        file = discord.File(img, filename="welcome.png")
        rules_ch = bot.get_channel(RULES_CHANNEL_ID)
        selfroles_ch = bot.get_channel(SELFROLES_CHANNEL_ID)
        embed = discord.Embed(
            title=f"{intro} Welcome {member.name}!",
            description=(
                f"{member.mention}, welcome to **{member.guild.name}**\n\n"
                f"Check out the {cyan_heart} {rules_ch.mention if rules_ch else '#rules'} {arrow}\n"
                f"Grab your roles in {cyan_heart} {selfroles_ch.mention if selfroles_ch else '#self-roles'} {arrow}"
            ),
            color=discord.Color.pink()
        )
        embed.set_image(url="attachment://welcome.png")
        await channel.send(embed=embed, file=file)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(GOODBYE_CHANNEL_ID)
    if channel:
        await channel.send(f"{member.name} has left the server. 🥹")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    content = message.content.lower()
    if content in ["hi", "hello"]:
        await message.channel.send(f"Hello lamaya 💗 {message.author.mention}")
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != CHANNEL_ID or payload.message_id != MESSAGE_ID:
        return
    guild = bot.get_guild(payload.guild_id)
    member = payload.member
    if member is None or member.bot:
        return
    role = guild.get_role(ROLE_ID)
    if role:
        await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != CHANNEL_ID or payload.message_id != MESSAGE_ID:
        return
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None:
        member = await guild.fetch_member(payload.user_id)
    role = guild.get_role(ROLE_ID)
    if role:
        await member.remove_roles(role)

@bot.event
async def on_guild_join(guild):
    allowed_servers = [GUILD_ID]
    if guild.id not in allowed_servers:
        await guild.leave()

# ---------------- COMMANDS ----------------
@bot.command()
@commands.has_role("Bot Manager")
async def say(ctx, *, msg):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    await ctx.send(msg)
    
@bot.command()
async def testwelcome(ctx):
    img = await create_welcome_image(ctx.author)
    file = discord.File(img, filename="welcome.png")
    embed = discord.Embed(
        title=f"🎉 Welcome {ctx.author.name}!",
        description=f"{ctx.author.mention}, enjoy your stay at **{ctx.guild.name}**",
        color=discord.Color.gold()
    )
    embed.set_image(url="attachment://welcome.png")
    await ctx.send(embed=embed, file=file)


@tasks.loop(seconds=10)
async def update_status():
    global status_toggle, streamer_mode
    if streamer_mode:  
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    if status_toggle == 0:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Miss Thiv ❤️"))
    elif status_toggle == 1:
        online = idle = dnd = 0
        for member in guild.members:
            if member.bot:
                continue
            if member.status == discord.Status.online:
                online += 1
            elif member.status == discord.Status.idle:
                idle += 1
            elif member.status == discord.Status.dnd:
                dnd += 1
        status_text = f"Online: {online} | Idle: {idle} | DND: {dnd}"
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
    else:
        await bot.change_presence(activity=discord.Game(name="with 💚Miss Thiv fam"))

    status_toggle = (status_toggle + 1) % 3


# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    update_status.start()
    print("Status loop started.")

@bot.event
async def on_member_update(before, after):
    global streamer_mode

    added_roles = [role for role in after.roles if role not in before.roles]
    removed_roles = [role for role in before.roles if role not in after.roles]

    for role in added_roles:
        if role.id == SROLE_ID and after.id == SUSER_ID:
            streamer_mode = True
            activity = discord.Streaming(
                name="On YouTube",
                url="https://www.twitch.tv/channel"
            )
            await bot.change_presence(activity=activity, status=discord.Status.online)
            print(f"Streamer mode ON because {after.name} got {role.name}")

    for role in removed_roles:
        if role.id == SROLE_ID and after.id == SUSER_ID:
            streamer_mode = False
            # Run one cycle of normal status immediately
            guild = bot.get_guild(GUILD_ID)
            if guild:
                global status_toggle
                if status_toggle == 0:
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Miss Thiv ❤️"))
                elif status_toggle == 1:
                    online = idle = dnd = 0
                    for member in guild.members:
                        if member.bot:
                            continue
                        if member.status == discord.Status.online:
                            online += 1
                        elif member.status == discord.Status.idle:
                            idle += 1
                        elif member.status == discord.Status.dnd:
                            dnd += 1
                    status_text = f"Online: {online} | Idle: {idle} | DND: {dnd}"
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
                else:
                    await bot.change_presence(activity=discord.Game(name="with 💚Miss Thiv fam"))
                status_toggle = (status_toggle + 1) % 3
            print(f"Streamer mode OFF because {after.name} lost {role.name}")


bot.run(TOKEN)