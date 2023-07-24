from typing import Tuple
from collections import deque
from pymongo import UpdateOne

dir_map = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


def circular_search(start: Tuple[int, int], sight: int, race: str):
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

        for d_x, d_y in [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]:
            if d_x >= 0 and d_x < 375 and d_y >= 0 and d_y < 375 and distance < sight:
                queue.append((d_x, d_y, distance + 1))

    return updates


def diverge_search(start: Tuple[int, int], sight: int, race: str, dir: str):
    x, y = start

    updates = []

    for d_x in [-1, 0, 1]:
        for d_y in [-1, 0, 1]:
            filter = {"_id": f"{x + d_x}-{y + d_y}"}
            update = {"$set": {race: 1}}
            updates.append(UpdateOne(filter, update))

    direction = dir_map.get(dir, (0, 0))

    for i in range(1, sight + 1):
        d_x = i * direction[0]
        d_y = i * direction[1]

        for j in range(0, i + 1):
            pr_x = abs(d_y)
            pr_y = abs(d_x)

            for pr_dir in [1, -1]:
                filter = {
                    "_id": f"{x + d_x + j * pr_x * pr_dir}-{y + d_y + j * pr_y * pr_dir}"
                }
                update = {"$set": {race: 1}}
                updates.append(UpdateOne(filter, update))

    return updates
