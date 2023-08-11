import utils.database as db

attacked_from = {}
has_attacked = set()  # a set of the units who has attacked another unit

ping_times = {}

map_objects = {}
map_fog = {}
map_walls = {}
dynamic_fog = {}
wheat_fields = []
game_time = 0

for object in db.map_collection.find():
    x, y = object["_id"].split("-")
    x, y = int(x), int(y)

    map_objects[(x, y)] = object

for building in db.buildings_collection.find():
    x, y = building["_id"].split("-")
    x, y = int(x), int(y)

    map_objects[(x, y)] = building

for node in db.fog_collection.find():
    x, y = node["_id"].split("-")
    x, y = int(x), int(y)

    map_fog[(x, y)] = node

with open("map.txt") as f:
    map_arr = eval(f.read())

for wall in db.walls_collection.find():
    x, y = wall["_id"].split("-")
    x, y = int(x), int(y)

    map_objects[(x, y)] = wall
    map_arr[x][y] = -1
print(f"Data initialized: {len(map_arr)}, {len(map_arr[0])}")
