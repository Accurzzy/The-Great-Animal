import asyncio
import traceback
import logging
import discord
from discord.ext import commands, tasks
from commands.rcon import GameServer
from import_lib import *
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional, Literal
import mysql.connector

# ENV
load_dotenv()

# BOT
TOKEN = os.getenv("TOKEN")
APP_ID = os.getenv("APPLICATION_ID")

# DB
DB_HOST = os.getenv("DATABASE_HOST")
DB_USER = os.getenv("DATABASE_USER")
DB_PW = os.getenv("DATABASE_PW")
DB_NAME = os.getenv("DATABASE_NAME")

# Validate environment variables
required_vars = ["TOKEN", "DATABASE_HOST", "DATABASE_USER", "DATABASE_PW", "DATABASE_NAME"]
for var in required_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

# Setup logging
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')

# Create database connection pool
db = mysql.connector.connect(
    host=DB_HOST, user=DB_USER, password=DB_PW, database=DB_NAME, pool_name="mypool", pool_size=5
)

def get_db_connection():
    return mysql.connector.connect(pool_name="mypool")

# Create 'players' table and ensure columns exist
with db.cursor(dictionary=True) as cursor:
    create_table_query = """
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name TEXT NOT NULL,
        discord_id BIGINT NOT NULL UNIQUE,
        steam_id TEXT DEFAULT NULL,
        bugs_received INTEGER DEFAULT 0,
        bugs INTEGER DEFAULT 0,
        score INTEGER DEFAULT 0,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_query)

    # Check if 'animals' column exists
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'players' AND TABLE_SCHEMA = %s;
    """, (DB_NAME,))
    columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

    if 'animals' not in columns:
        alter_table_query = """
        ALTER TABLE players ADD COLUMN animals TEXT DEFAULT NULL;
        """
        cursor.execute(alter_table_query)

    db.commit()
    print("Players table checked/created, and columns verified.")

# Insert or update player in the database
def insert_or_update_player(name, discord_id, steam_id=None, bugs_received=0, bugs=0, score=0):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # First, check if the player already exists by discord_id
        select_query = "SELECT * FROM players WHERE discord_id = %s"
        cursor.execute(select_query, (discord_id,))
        player = cursor.fetchone()

        if player:
            # If player exists, update the record
            update_query = """
            UPDATE players 
            SET name = %s, steam_id = %s, bugs_received = %s, bugs = %s, score = %s, last_activity = CURRENT_TIMESTAMP
            WHERE discord_id = %s;
            """
            cursor.execute(update_query, (name, steam_id, bugs_received, bugs, score, discord_id))
            print(f"Updated player {name} in the database.")
        else:
            # If player doesn't exist, insert a new record
            insert_query = """
            INSERT INTO players (name, discord_id, steam_id, bugs_received, bugs, score)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (name, discord_id, steam_id, bugs_received, bugs, score))
            print(f"Inserted new player {name} into the database.")

        connection.commit()
    except mysql.connector.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        cursor.close()
        connection.close()

# BOT setup
bot = commands.Bot(command_prefix=["!", "."], help_command=None, intents=discord.Intents.all(), application_id=APP_ID)

_DIR = Path(__file__).parent
COMMANDS_DIR = _DIR / "commands"

async def load():
    # Load the inject cog specifically
    try:
        await bot.load_extension('commands.inject')  # This assumes 'inject.py' is in the 'commands' directory
        print("inject.py loaded successfully!")
    except Exception as e:
        logging.error(f"inject.py could not be loaded. [{e}]")
        print(f'inject.py could not be loaded. [{e}]')

    # Dynamically load other cogs
    for file in COMMANDS_DIR.iterdir():
        if file.suffix == ".py" and file.stem != "inject":  # Skip inject.py since it's already loaded
            filename = file.stem
            try:
                await bot.load_extension(f"commands.{filename}")
                print(f"{filename} loaded successfully!")
            except Exception as e:
                logging.error(f"{filename} could not be loaded. [{e}]")
                print(f'{filename} could not be loaded. [{e}]')

async def update_presence():
    try:
        response = await GameServer(bot).rcon("PlayersCount")
        player_count = response.split(":")[1].strip() if ":" in response else response
        formatted_presence = f"Animalia, Server:The Great Circle | Players Online: {player_count}"

        # Update bot's presence with the formatted string
        await bot.change_presence(activity=discord.Game(name=formatted_presence))
        print('Bot presence updated')
        print(formatted_presence)
    except Exception as e:
        logging.error(f"Failed to update presence: {e}")

async def main():
    await load()
    await bot.start(TOKEN)

@tasks.loop(minutes=5)
async def presence_update_task():
    await update_presence()

# Start the task when the bot is ready
@bot.event
async def on_ready():
    presence_update_task.start()
    print('Bot Online!')

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f"An error occurred in {event}. [{args}, {kwargs}]", exc_info=True)
    print(f'An error occurred in {event}. [{args}, {kwargs}]')

@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Command error: {error}", exc_info=True)
    if isinstance(error, commands.CommandNotFound):
        return

    embed = discord.Embed(
        title="Animalia Survival 🤖",
        description=f"An error occurred while running the command:\n\n{str(error)}",
        color=0xfcff40,
    )
    await ctx.send(embed=embed)
    raise error
    
@bot.command()
@commands.guild_only()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot Shutdown")
        pass
