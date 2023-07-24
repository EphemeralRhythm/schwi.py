import utils.database as db

map_objects = {}
map_fog = {}

for object in db.map_collection.find():
    x, y = object["_id"].split("-")
    x, y = int(x), int(y)

    map_objects[(x, y)] = object

for node in db.fog_collection.find():
    x, y = node["_id"].split("-")
    x, y = int(x), int(y)

    map_fog[(x, y)] = node
