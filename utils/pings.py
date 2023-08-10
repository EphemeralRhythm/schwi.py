from utils.database import pings_collection


def get_pings(id) -> dict:
    player_post = pings_collection.find_one({"_id": id})
    if not player_post:
        player_post = {
            "_id": id,
            "Reaching destination": True,
            "Hitting an obstacle": True,
            "Attacking an enemy": True,
            "Getting attacked": True,
            "Failing to attack": True,
        }
        pings_collection.insert_one(player_post)
    return player_post
