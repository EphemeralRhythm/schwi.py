import database as db

arr = []
for x in range(375):
    for y in range(375):
        post = {"_id": f"{x}-{y}", "cyan": 0, "red": 0, "lime": 0}

        arr.append(post)
print(".")
db.fog_collection.insert_many(arr)
