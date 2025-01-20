import os
import json
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration using environment variables
config = {
    "user": os.getenv("DATABASE_USER"),
    "password": os.getenv("DATABASE_PW"),
    "host": os.getenv("DATABASE_HOST"),
    "database": os.getenv("DATABASE_NAME"),
}

# Animals data
animals = {
    "Buffalo": {"price": 25000, "image": "", "slot": "1", "quantity": 0, "gender": ""},
    "Crocodille": {"price": 25000, "image": "", "slot": "2", "quantity": 0, "gender": ""},
    "Eagle": {"price": 3000, "image": "", "slot": "3", "quantity": 0, "gender": ""},
    "Elephant": {"price": 25000, "image": "", "slot": "4", "quantity": 0, "gender": ""},
    "Gazelle": {"price": 20000, "image": "", "slot": "5", "quantity": 0, "gender": ""},
    "Giraffe": {"price": 20000, "image": "", "slot": "6", "quantity": 0, "gender": ""},
    "Hare": {"price": 100000, "image": "", "slot": "7", "quantity": 0, "gender": ""},
    "Hippopotamus": {"price": 20000, "image": "", "slot": "8", "quantity": 0, "gender": ""},
    "Hyena": {"price": 15000, "image": "", "slot": "9", "quantity": 0, "gender": ""},
    "Kudu": {"price": 15000, "image": "", "slot": "10", "quantity": 0, "gender": ""},
    "Leopard": {"price": 20000, "image": "", "slot": "11", "quantity": 0, "gender": ""},
    "Lion": {"price": 30000, "image": "", "slot": "12", "quantity": 0, "gender": ""},
    "Lionness": {"price": 25000, "image": "", "slot": "12", "quantity": 0, "gender": ""},
    "Meerkat": {"price": 6000, "image": "", "slot": "6", "quantity": 0, "gender": ""},
    "Rhinoceros": {"price": 20000, "image": "", "slot": "6", "quantity": 0, "gender": ""},
    "Shoebill": {"price": 6000, "image": "", "slot": "7", "quantity": 0, "gender": ""},
    "Vulture": {"price": 3000, "image": "", "slot": "8", "quantity": 0, "gender": ""},
    "Warthog": {"price": 20000, "image": "", "slot": "9", "quantity": 0, "gender": ""},
    "Wildebeast": {"price": 50000, "image": "", "slot": "10", "quantity": 0, "gender": ""},
    "WildDog": {"price": 20000, "image": "", "slot": "11", "quantity": 0, "gender": ""},
    "Zebra": {"price": 15000, "image": "", "slot": "12", "quantity": 0, "gender": ""},
}

# Object hook for custom JSON decoding
def object_hook(d):
    for key, value in d.items():
        if isinstance(value, list):
            d[key] = tuple(value)
    return d

# Connect to the database and perform a query
def get_player_data(discord_id):
    try:
        with mysql.connector.connect(**config) as db:
            with db.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM players WHERE discord_id = %s", (discord_id,))
                result = cursor.fetchone()

                if result is None:
                    return None

                last_work_time = result.get("last_work_time", datetime.min)
                voice_start_time = result.get("voice_start_time", datetime.min)
                last_voice_time = result.get("last_voice_time", datetime.min)

                # Safely get the 'animals' key, using an empty dictionary if it's missing
                player_animals = result.get("animals", {})

                player_data = {
                    "steam_id": result["steam_id"],
                    "discord_id": result["discord_id"],
                    "bugs": result["bugs"],
                    "animals": player_animals,
                    "last_work_time": last_work_time,
                    "voice_start_time": voice_start_time,
                    "last_voice_time": last_voice_time,
                }

                print(f"DEBUG: {discord_id} has {player_data['bugs']} bugs.")
                return player_data

    except mysql.connector.Error as e:
        print(f"DEBUG: Error during database query: {e}")
        return None

# Save player data into the database
def save_player_data(discord_id, player_data):
    try:
        with mysql.connector.connect(**config) as db:
            with db.cursor() as cursor:
                cursor.execute(
                    "UPDATE players SET bugs = %s, animals = %s, last_work_time = %s, voice_start_time = %s, last_voice_time = %s WHERE discord_id = %s",
                    (
                        player_data["bugs"],
                        json.dumps(player_data["animals"]),  # Ensure animals are serialized as JSON
                        player_data["last_work_time"],
                        player_data.get("voice_start_time", None),
                        player_data.get("last_voice_time", None),
                        discord_id,
                    ),
                )
                db.commit()

                print(f"DEBUG: User {discord_id} data saved to the database")

    except mysql.connector.Error as e:
        print(f"DEBUG: Error during database update: {e}")

# Clear the player's animal data
def clear_player_animals(discord_id):
    try:
        with mysql.connector.connect(**config) as db:
            with db.cursor() as cursor:
                cursor.execute("UPDATE players SET animals = '{}' WHERE discord_id = %s", (discord_id,))
                db.commit()

        return True
    except mysql.connector.Error as e:
        print(f"DEBUG: Error during clearing animals: {e}")
        return False

# Retrieve player's animal data
def get_player_animals(discord_id):
    try:
        with mysql.connector.connect(**config) as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT animals FROM players WHERE discord_id = %s", (discord_id,))
                player_data = cursor.fetchone()

                if player_data is None or player_data[0] is None:
                    return {}

                try:
                    player_animals = json.loads(player_data[0], object_hook=object_hook)
                except json.decoder.JSONDecodeError as e:
                    print(f"DEBUG: JSON decode error: {e}")
                    player_animals = {}

        return player_animals
    except mysql.connector.Error as e:
        print(f"DEBUG: Error during retrieving animals: {e}")
        return {}

# Check if the player is in the correct channel for the animal shop
def in_animal_shop(ctx):
    return ctx.channel.id == int(os.getenv("BOT_CHANNEL"))

# Check if the player is in the correct channel for the OG channel
def in_og_chan(ctx):
    return ctx.channel.id == int(os.getenv("VIP_CHANNEL"))
