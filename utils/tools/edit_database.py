from pymongo import MongoClient
import os

cluster = MongoClient(
    f"mongodb+srv://ephemeralrhyhtm:P5gNwZsGY23zJqT@cluster0.npfjeiw.mongodb.net/?retryWrites=true&w=majority"
)

db = cluster["Discord"]

fog_collection = db["Fog"]
units_collection = db["Units"]
commands_collection = db["Commands"]
dead_collection = db["Dead"]
xp_collection = db["xp"]
map_collection = db["Objects"]

# # Query to find documents with image: "DeadTrees2"
# query = {"image": "DeadTrees3"}
#
# # Update the documents to change image: "DeadTrees2" to image: "DeadTree2"
# update = {"$set": {"image": "DeadTree3"}}
# result = map_collection.update_many(query, update)
#
# # Print the number of documents updated
# print(f"Number of documents updated: {result.modified_count}")

result = map_collection.update_many({}, {"$unset": {"x": "", "y": ""}})

# Print the number of documents updated
print(f"Number of documents updated: {result.modified_count}")
