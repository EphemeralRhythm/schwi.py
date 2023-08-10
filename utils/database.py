from pymongo import MongoClient
import os

cluster = MongoClient(
    f"mongodb+srv://{os.getenv('database_key')}.mongodb.net/?retryWrites=true&w=majority"
)

db = cluster["Discord"]

fog_collection = db["Fog"]
units_collection = db["Units"]
commands_collection = db["Commands"]
dead_collection = db["Dead"]
xp_collection = db["xp"]
map_collection = db["Objects"]
walls_collection = db["Walls"]
buildings_collection = db["Buildings"]
pings_collection = db["Pings"]
resources_collection = db["Resources"]
info_collection = db["info"]
unit_queues = db["unit_queues"]
