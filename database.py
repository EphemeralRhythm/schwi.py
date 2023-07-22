from pymongo import MongoClient
import os

cluster = MongoClient(
    f"mongodb+srv://{os.getenv('database_key')}.mongodb.net/?retryWrites=true&w=majority"
)

db = cluster["Discord"]

fog_collection = db["Fog"]
buildings_collection = db["Buildings"]
nature_collection = db["Nature"]
mines_collection = db["Mines"]
loot_collection = db["loot"]
units_collection = db["Units"]
commands_collection = db["Commands"]
dead_collection = db["Dead"]
xp_collection = db["xp"]
