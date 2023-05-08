from pymongo import MongoClient
import os

cluster = MongoClient(f"mongodb+srv://{os.getenv('database_key')}.mongodb.net/?retryWrites=true&w=majority")

db = cluster['Discord']

fog_collection = db['Fog']
buildings_collection = db['Buildings']
units_collection = db['Units']
commands_collection = db['Commands']
info_collection = db['Info']
resources_collection = db['resources']
dead_collection = db['Dead']
xp_collection = db["xp"]
units_queue = db["Units_Queue"]
buildings_queue = db["Buildings_Queue"]
ores_collection = db["Raw"]