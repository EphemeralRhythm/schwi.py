import database as db
from fog_of_war import circular_search

locations = [(5, 92), (310, 369), (303, 3)]
races = ["cyan", "red", "lime"]
posts = []

for i in range(3):
    new_arr = circular_search(locations[i], 4, races[i])

    posts.extend(new_arr)
print(posts)
db.fog_collection.bulk_write(posts)
