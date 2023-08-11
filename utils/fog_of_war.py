from typing import Tuple
from collections import deque
from pymongo import UpdateOne

dir_map = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


def circular_search(start: Tuple[int, int], sight: int, race: str, dynamic_fog: dict):
    queue = deque([(start[0], start[1], 0)])
    visited = set()
    updates = []

    while queue:
        x, y, distance = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))

        filter = {"_id": f"{x}-{y}"}
        update = {"$set": {race: 1}}
        updates.append(UpdateOne(filter, update))

        post = dynamic_fog.get((x, y), {"cyan": 0, "red": 0, "lime": 0})
        post[race] = 1
        dynamic_fog[(x, y)] = post

        for d_x, d_y in [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]:
            if d_x >= 0 and d_x < 375 and d_y >= 0 and d_y < 375 and distance < sight:
                queue.append((d_x, d_y, distance + 1))

    return updates, dynamic_fog


def diverge_search(
    start: Tuple[int, int],
    sight: int,
    race: str,
    dir: str,
    dynamic_fog: dict,
    map_fog: dict,
):
    x, y = start

    updates = []

    for d_x in [-1, 0, 1]:
        for d_y in [-1, 0, 1]:
            filter = {"_id": f"{x + d_x}-{y + d_y}"}
            update = {"$set": {race: 1}}
            updates.append(UpdateOne(filter, update))

            post = dynamic_fog.get((x + d_x, y + d_y), {"cyan": 0, "red": 0, "lime": 0})
            post[race] = 1
            dynamic_fog[(x + d_x, y + d_y)] = post

            post = map_fog.get((x + d_x, y + d_y), {"cyan": 0, "red": 0, "lime": 0})
            post[race] = 1
            map_fog[(x + d_x, y + d_y)] = post
    direction = dir_map.get(dir, (0, 0))

    for i in range(sight):
        d_x = i * direction[0]
        d_y = i * direction[1]

        for j in range(i + 3):
            pr_x = abs(direction[1])
            pr_y = abs(direction[0])

            for pr_dir in [1, -1]:
                curr_x = x + d_x + j * pr_x * pr_dir
                curr_y = y + d_y + j * pr_y * pr_dir
                filter = {"_id": f"{curr_x}-{curr_y}"}
                update = {"$set": {race: 1}}
                updates.append(UpdateOne(filter, update))

                post = dynamic_fog.get(
                    (curr_x, curr_y), {"cyan": 0, "red": 0, "lime": 0}
                )
                post[race] = 1
                dynamic_fog[(curr_x, curr_y)] = post

                post = map_fog.get((curr_x, curr_y), {"cyan": 0, "red": 0, "lime": 0})
                post[race] = 1
                map_fog[(curr_x, curr_y)] = post

    return updates
