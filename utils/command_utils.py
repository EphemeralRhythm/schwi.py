import discord
from utils.database import (
    units_collection,
    dead_collection,
    buildings_collection,
    walls_collection,
    commands_collection,
    map_collection,
    unit_queues,
    mines_collection,
)
from utils.pings import get_pings
import utils.data
from utils.units_info import units
from queue import PriorityQueue
import time


def get_direction(dir_x, dir_y):
    if abs(dir_x) > abs(dir_y):
        if dir_x > 0:
            dir = "R"
        else:
            dir = "L"
    else:
        if dir_y > 0:
            dir = "D"
        else:
            dir = "U"

    return dir


def move(f_x: int, f_y: int, unit):
    if unit.get("boat"):
        return
    x, y = unit.get("x"), unit.get("y")
    dir_x = f_x - x
    dir_y = f_y - y

    name = unit.get("name")
    info = units.get(name, {})

    speed = unit.get("speed", info.get("speed"))
    node = utils.data.map_arr[x // 16][y // 16]

    distance = ((f_x - x) ** 2 + (f_y - y) ** 2) ** 0.5
    if distance <= speed:
        if utils.data.map_arr[f_x // 16][f_y // 16] != node:
            return -1
        x, y = f_x, f_y
    else:
        x_step = int((f_x - x) * speed // distance)
        y_step = int((f_y - y) * speed // distance)

        if x + x_step <= 0 or x + x_step >= 6000:
            return -1
        if y + y_step <= 0 or y + y_step >= 6000:
            return -1

        if utils.data.map_arr[(x + x_step) // 16][(y + y_step) // 16] != node:
            return -1
        x += x_step
        y += y_step

    dir = get_direction(dir_x, dir_y)

    update = {
        "$set": {
            "x": x,
            "y": y,
            "direction": dir,
            "state": int(not (x == f_x and y == f_y)),
        }
    }
    units_collection.find_one_and_update({"_id": unit["_id"]}, update)

    if unit["name"] == "Boat" and unit.get("unit"):
        update = {
            "$set": {
                "x": x,
                "y": y - 8,
                "direction": dir,
                "state": 0,
            }
        }

        units_collection.update_one({"_id": unit["unit"]}, update)
    return x == f_x and y == f_y


# PATH FINDING
def heuristic(start: tuple, end: tuple):
    return abs(start[0] - end[0]) + abs(start[1] - end[1])


def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]


def astar(node_x: int, node_y: int, unit):
    x, y = unit.get("x"), unit.get("y")

    start = (x // 16, y // 16)
    open_queue = PriorityQueue()
    open_queue.put((0, start))

    came_from = {}
    g_score = {}
    f_score = {}

    node_type = utils.data.map_arr[x // 16][y // 16]

    g_score[start] = 0
    f_score[start] = heuristic(start, (node_x, node_y))

    open_hash = {start}

    while not open_queue.empty():
        current = open_queue.get()[1]
        x, y = current
        open_hash.remove(current)

        if current == (node_x, node_y):
            return reconstruct_path(came_from, (node_x, node_y))

        dir = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for d in dir:
            n_x = x + d[0]
            n_y = y + d[1]

            if n_x < 0 or n_x >= 375:
                continue
            if n_y < 0 or n_y >= 375:
                continue

            node = utils.data.map_arr[n_x][n_y]
            if node != node_type:
                continue

            temp_g_score = g_score[current] + 1

            if temp_g_score < g_score.get((n_x, n_y), float("inf")):
                came_from[(n_x, n_y)] = current
                g_score[(n_x, n_y)] = temp_g_score
                f_score[(n_x, n_y)] = temp_g_score + heuristic(
                    (n_x, n_y), (node_x, node_y)
                )
                if (n_x, n_y) not in open_hash:
                    open_queue.put((f_score[(n_x, n_y)], (n_x, n_y)))
                    open_hash.add((n_x, n_y))
    return False


def direction_vector(curr, head):
    if curr[0] == head[0]:
        dir_x = 0
    else:
        dir_x = (curr[0] - head[0]) // abs(curr[0] - head[0])

    if curr[1] == head[1]:
        dir_y = 0
    else:
        dir_y = (curr[1] - head[1]) // abs(curr[1] - head[1])

    curr_dir = (dir_x, dir_y)
    return curr_dir


def move_to_path(path):
    if not path:
        return []

    head = path[0]
    end = path[-1]
    print(f"head: {head}, end: {end}")
    if len(path) == 1:
        return [end]

    curr = path[1]
    curr_dir = direction_vector(curr, head)

    points = []
    i = 1
    while curr != end:
        i += 1
        next = path[i]
        temp_dir = direction_vector(next, curr)
        if temp_dir != curr_dir:
            points.append(curr)
            curr_dir = temp_dir
        curr = next

    if not points:
        points = [end]
    elif points[-1] != end:
        points.append(end)
    return points


async def damage(unit, target, client):
    u_name = unit.get("name")
    u_race = unit.get("race")
    u_info = units.get(u_name, {})

    u_attack = unit.get("attack") or u_info.get("attack")
    u_owner = unit.get("owner") or unit["_id"]
    u_pings = get_pings(u_owner)

    target_id = target["_id"]
    t_name = target.get("name")
    t_hp = target.get("hp")
    t_race = target.get("race")
    t_owner = target.get("owner") or target["_id"]
    t_pings = get_pings(t_owner)
    t_hp -= u_attack

    is_building = target.get("type") == "building"

    if is_building:
        t_x, t_y = target["_id"].split("-")
        t_x, t_y = int(t_x) * 16, int(t_y) * 16
    else:
        t_x = target.get("x")
        t_y = target.get("y")

    u_x = unit.get("x")
    u_y = unit.get("y")

    print(f"{u_name} attacks {t_name}")
    dist = abs(u_x - t_x) + abs(u_y - t_y)

    dir_x = t_x - u_x
    dir_y = t_y - u_y

    dir = get_direction(dir_x, dir_y)
    u_recharge = u_info.get("recharge", 0) + 1
    print(f"recharge: {u_recharge}")
    units_collection.update_one(
        {"_id": unit["_id"]},
        {"$set": {"state": -1, "recharge": u_recharge, "direction": dir}},
    )
    u_mention = None
    t_mention = None

    race_roles = {
        "cyan": "&1137742430360317952",
        "red": "&1137742509154521118",
        "lime": "&1137742610417590342",
    }
    if is_building:
        t_owner = race_roles.get(t_race)
        target_id = ""

    u_last_ping = utils.data.ping_times.get(u_owner, 0)
    t_last_ping = utils.data.ping_times.get(t_owner, 0)

    if u_pings.get("Attacking an enemy") and time.time() - u_last_ping > 60 * 20:
        u_mention = f"<@{u_owner}>"
        utils.data.ping_times[u_owner] = time.time()
    if t_pings.get("Getting attacked") and time.time() - t_last_ping > 60 * 20:
        t_mention = f"<@{t_owner}>"
        utils.data.ping_times[t_owner] = time.time()
    if u_name == "Player":
        unit["_id"] = f"<@{unit['_id']}>"

    await log(
        u_race,
        "Attacking!",
        f"<@{u_owner}>"
        + f"{u_name} attacked {t_race} {t_name} dealing "
        + f"{u_attack} points of damage.",
        client=client,
        content=u_mention,
    )
    await log(
        t_race,
        "Warning!",
        f"<@{t_owner}>"
        + f"{t_name} {target_id} is being attacked by {u_race} {u_name}.",
        client=client,
        content=t_mention,
    )
    if not is_building:
        if t_hp <= 0:
            commands_collection.delete_many({"target": target["_id"]})
            commands_collection.delete_many({"unit": target["_id"]})
        if t_hp <= 0 and t_name != "Player":
            units_collection.delete_one({"_id": target["_id"]})
            ping = f"<@{target.get('owner')}>"

            await log(
                u_race,
                "GG!",
                f"{u_name} killed {t_race} {t_name}.",
                client=client,
                content=None,
            )
            await log(
                t_race,
                "Unit Lost",
                f"{t_name} {target_id} was killed by "
                + f"{u_race} {u_name} {unit.get('_id')}",
                content=ping,
                client=client,
            )
            if unit["name"] == "boat":
                if not unit.get("unit"):
                    return

                carried_unit = units_collection.find_one({"_id": unit["unit"]})
                if not carried_unit:
                    return
                if carried_unit["name"] == "Player":
                    dead_collection.insert_one(carried_unit)
                units_collection.delete_one(carried_unit)
                ping = carried_unit.get("owner") or carried_unit["_id"]

                await log(
                    t_race,
                    "Unit Lost",
                    f"{carried_unit['name']} {carried_unit['_id']} drowned",
                    content=ping,
                    client=client,
                )

            return True

        elif t_hp <= 0:
            await log(
                u_race,
                "GG!",
                f"{u_name} killed <@{target_id}>.",
                client=client,
            )
            await log(
                t_race,
                "Unit Lost",
                f'<@{target_id}> was killed by {u_race} {u_name} {unit.get("_id")}',
                client=client,
                content=f"<@{target.get('_id')}>",
            )
            dead_collection.insert_one(target)
            units_collection.delete_one({"_id": target["_id"]})
            return True

        else:
            units_collection.update_one(
                {"_id": target["_id"]}, {"$set": {"hp": t_hp, "heal": 10}}
            )
            temp = utils.data.attacked_from.get(target["_id"])

            if not temp:
                utils.data.attacked_from[target["_id"]] = (unit["_id"], dist)

            elif temp[1] >= dist:
                utils.data.attacked_from[target["_id"]] = (unit["_id"], dist)

    else:
        if t_hp <= 0:
            buildings_collection.delete_one({"_id": target["_id"]})
            unit_queues.delete_many({"building": target["_id"]})

            t_x, t_y = target["_id"].split("-")
            t_x, t_y = int(t_x), int(t_y)

            utils.data.map_objects.pop((t_x, t_y))
            await log(
                u_race,
                "GG!",
                f"{u_name} destroyed {t_race} {t_name}.",
                client=client,
                content=None,
            )
            await log(
                t_race,
                "Unit Lost",
                f"{t_name} {target_id} has been destroyed by "
                + f"{u_race} {u_name} {unit.get('_id')}",
                content=t_mention,
                client=client,
            )

            if target["name"] == "Headquarters":
                map_collection.delete_one({"_id": target["_id"]})
                units_collection.delete_many({"race": target["race"]})
                dead_collection.delete_many({"race": target["race"]})

                await log(
                    u_race,
                    "GG!",
                    f"Team {target['race']} was eliminated.",
                    client=client,
                    content=None,
                )
                await log(
                    t_race,
                    "Game Over",
                    f"Team {target['race']} was eliminated.",
                    content=t_mention,
                    client=client,
                )
        else:
            buildings_collection.update_one(
                {"_id": target["_id"]}, {"$set": {"hp": t_hp}}
            )


async def attack(unit, target_id, client):
    target = units_collection.find_one({"_id": target_id})

    if not target:
        return

    night_debuff = 0 if utils.data.game_time < 180 else 2

    u_name = unit.get("name")
    u_x = unit.get("x")
    u_y = unit.get("y")
    u_race = unit.get("race")
    u_info = units.get(u_name, {})

    u_range = unit.get("range") or u_info.get("range") or 8
    u_range -= night_debuff

    u_owner = unit.get("owner") or unit["_id"]
    u_pings = get_pings(u_owner)

    t_name = target.get("name")
    t_x = target.get("x")
    t_y = target.get("y")
    t_race = target.get("race")

    if unit.get("boat") and u_range <= 16:
        return
    u_node = utils.data.map_arr[u_x // 16][u_y // 16]
    t_node = utils.data.map_arr[t_x // 16][t_y // 16]

    dist = abs(u_x - t_x) + abs(u_y - t_y)
    if u_node == -1:
        u_range += 2 * 16
    if t_node != u_node:
        dist += 16
    print(f"Range: {u_range}, Dist: {dist}")
    if dist > u_range:
        path = astar(t_x // 16, t_y // 16, unit)
        if not path and u_range <= 16:
            u_mention = None
            if u_pings.get("Failing to attack"):
                u_mention = f"<@{u_owner}>"
            commands_collection.delete_many({"unit": unit["_id"]})
            await log(
                u_race,
                "Target Out Of Reach",
                f"<@{u_owner}>\n" + f"{u_name} failed to attack {t_race} {t_name}.",
                client=client,
                content=u_mention,
            )
            return
        elif path:
            if len(path) == 1:
                move(t_x, t_y, unit)
            else:
                points = move_to_path(path)
                node = points[0]
                move(node[0] * 16, node[1] * 16, unit)
        else:
            move(t_x, t_y, unit)
        target = units_collection.find_one({"_id": target["_id"]})
        unit = units_collection.find_one({"_id": unit["_id"]})

        t_x = target.get("x")
        t_y = target.get("y")

        u_x = unit.get("x")
        u_y = unit.get("y")

        dist = abs(u_x - t_x) + abs(u_y - t_y)

        if dist > u_range:
            return

    if unit.get("recharge", 0) != 0:
        return

    if u_name != "Mage":
        await damage(unit, target, client)
    else:
        for enemy in units_collection.find({"race": {"$ne": u_race}}):
            e_x = enemy["x"]
            e_y = enemy["y"]
            if abs(t_x - e_x) + abs(t_y - e_y) > 60:
                continue
            await damage(unit, enemy, client)


async def attack_building(unit, target_id, client):
    target = buildings_collection.find_one({"_id": target_id})

    if not target:
        return

    night_debuff = 0 if utils.data.game_time < 180 else 2

    u_name = unit.get("name")
    u_x = unit.get("x")
    u_y = unit.get("y")
    u_race = unit.get("race")
    u_info = units.get(u_name, {})

    u_range = unit.get("range") or u_info.get("range") or 8
    u_range -= night_debuff

    u_owner = unit.get("owner") or unit["_id"]
    u_pings = get_pings(u_owner)

    t_name = target.get("name")
    t_race = target.get("race")

    t_x, t_y = target["_id"].split("-")
    t_x, t_y = int(t_x) * 16, int(t_y) * 16

    u_node = utils.data.map_arr[u_x // 16][u_y // 16]

    dist = abs(u_x - t_x) + abs(u_y - t_y)
    if u_node == -1:
        u_range += 2 * 16

    if dist > u_range:
        path = astar(t_x // 16, t_y // 16, unit)
        print("Path: ", path)
        if not path and u_range <= 16:
            u_mention = None
            if u_pings.get("Failing to attack"):
                u_mention = f"<@{u_owner}>"
            commands_collection.delete_many({"unit": unit["_id"]})
            await log(
                u_race,
                "Target Out Of Reach",
                f"<@{u_owner}>\n" + f"{u_name} failed to attack {t_race} {t_name}.",
                client=client,
                content=u_mention,
            )
            return
        elif path:
            if len(path) == 1:
                move(t_x, t_y, unit)
            else:
                points = move_to_path(path)
                node = points[0]
                move(node[0] * 16, node[1] * 16, unit)
        else:
            move(t_x, t_y, unit)
        return

    if unit.get("recharge", 0) != 0:
        return

    await damage(unit, target, client)


async def guard(unit, pos, client):
    u_race = unit.get("race")
    query = {"race": {"$ne": unit.get("race")}}
    players = units_collection.find(query)

    x, y, dir = pos

    def locate(target):
        offset = 0
        if u := utils.data.dynamic_fog.get(
            (target.get("x") // 16, target.get("y") // 16)
        ):
            if not u.get(u_race):
                offset += 300
        t_x, t_y = target.get("x"), target.get("y")
        return abs(x - t_x) + abs(y - t_y) + offset

    players = sorted(players, key=lambda enemy: locate(enemy))

    if locate(players[0]) > 100:
        if move(x, y, unit):
            units_collection.update_one(
                {"_id": unit["_id"]}, {"$set": {"direction": dir}}
            )
        return
    print("attacking!")
    await attack(unit, players[0]["_id"], client=client)


def chop(unit, pos: tuple):
    tree = utils.data.map_objects.get((pos[0] // 16, pos[1] // 16))
    if not tree:
        return
    print(tree)
    u_name = unit["name"]
    u_info = units.get(u_name, {})
    u_attack = unit.get("attack") or u_info.get("attack")

    hp = tree.get("hp") - u_attack
    if hp > 0:
        map_collection.update_one({"_id": tree["_id"]}, {"$set": {"hp": hp}})
        tree["hp"] = hp
    else:
        utils.data.map_objects.pop((pos[0] // 16, pos[1] // 16))
        map_collection.delete_one({"_id": tree["_id"]})
        return 1


def gather(command, unit):
    f_x, f_y = command.get("x") * 16, command.get("y") * 16
    x = unit.get("x")
    y = unit.get("y")
    if command.get("state") == "collect":
        if x != f_x or y != f_y:
            path = astar(f_x // 16, f_y // 16, unit)
            if not path:
                commands_collection.delete_many({"unit": unit["_id"]})
                return 1
            else:
                if len(path) == 1:
                    move(f_x, f_y, unit)
                else:
                    points = move_to_path(path)
                    node = points[0]
                    move(node[0] * 16, node[1] * 16, unit)
            return
        else:
            resource_type = "raw_" + str(command.get("type"))
            resource_amount = 10
            unit[resource_type] = unit.get(resource_type, 0) + resource_amount

            x, y = command.get("x"), command.get("y")
            result = mines_collection.update_one(
                {"x": x, "y": y},
                {"$inc": {"cap": -resource_amount}},
            )

            if result.modified_count == 1 and result.raw_result["updatedExisting"]:
                ore = mines_collection.find_one({"x": x, "y": y})
                if ore.get("cap") <= 0:
                    mines_collection.delete_one({"_id": command.get("ore")})
                    commands_collection.delete_one({"_id": command["_id"]})
                    return -1

            units_collection.update_one(
                {"_id": unit["_id"]},
                {"$set": {resource_type: unit[resource_type]}},
            )

            if unit.get(resource_type) >= 100:
                commands_collection.update_one(
                    {"_id": command["_id"]},
                    {"$set": {"state": "deposit"}},
                )

    elif command.get("state") == "deposit":
        query = {"race": unit.get("race"), "name": "Workshop"}
        buildings = buildings_collection.find(query)

        x, y = unit.get("x"), unit.get("y")

        def locate(building):
            xm, ym = building["_id"].split("-")
            xm, ym = int(xm) * 16, int(ym) * 16

            return abs(xm - x) + abs(ym - y)

        buildings = sorted(buildings, key=lambda b: locate(b))
        print(buildings)
        if not buildings:
            commands_collection.delete_one({"_id": command["_id"]})

            return 1

        f_x, f_y = buildings[0]["_id"].split("-")
        f_x, f_y = int(f_x) * 16, int(f_y) * 16

        value = move(f_x, f_y, unit)
        if value:
            resources_type = command.get("type")
            raw_type = "raw_" + str(resources_type)

            buildings_collection.update_one(
                {"_id": buildings[0]["_id"]},
                {"$inc": {resources_type: unit.get(raw_type)}},
            )

            x, y = buildings[0]["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)][resources_type] = buildings[0][
                resources_type
            ] + unit.get(raw_type)

            units_collection.update_one(
                {"_id": unit["_id"]},
                {"$set": {raw_type: 0}},
            )

            commands_collection.update_one(
                {"_id": command["_id"]}, {"$set": {"state": "collect"}}
            )


async def update_command(command, client: discord.Client):
    name = command["command"]
    unit_id = command["unit"]
    filter = {"_id": unit_id}
    unit = units_collection.find_one(filter)
    if not unit:
        commands_collection.delete_one({"_id": command["_id"]})
        return
    u_owner = unit.get("owner") or unit.get("_id")
    u_pings = get_pings(u_owner)

    if name == "move":
        f_x, f_y = command.get("x"), command.get("y")
        value = move(f_x, f_y, unit)
        if value:
            commands_collection.delete_one({"_id": command["_id"]})
            if not unit.get("owner"):
                name = f"<@{unit.get('_id')}>"
            else:
                name = unit.get("_id")
            if value != -1:
                u_mention = None
                if u_pings.get("Reaching destination"):
                    u_mention = f"<@{u_owner}>"

                await log(
                    unit.get("race"),
                    "Destination Reached",
                    f"{unit.get('name')} {name} reached its destination.",
                    client=client,
                    content=u_mention,
                )
            else:
                u_mention = None
                if u_pings.get("Hitting an obstacle"):
                    u_mention = f"<@{u_owner}>"

                await log(
                    unit.get("race"),
                    "Destination Unreachable",
                    f"{unit.get('name')} {name} ran into an obstacle.",
                    client=client,
                    content=u_mention,
                )
    elif name == "attack":
        target_id = command["target"]
        await attack(unit, target_id, client)
    elif name == "battack":
        target_id = command["target"]
        await attack_building(unit, target_id, client)
    elif name == "turn":
        units_collection.update_one(
            {"_id": unit["_id"]}, {"$set": {"direction": command.get("direction")}}
        )
    elif name == "guard":
        x, y = command.get("x"), command.get("y")
        dir = command.get("direction")
        await guard(unit, (x, y, dir), client)
    elif name == "chop":
        x, y = command.get("x"), command.get("y")
        dir = command.get("direction")
        if chop(unit, (x, y)):
            units_collection.update_one({"_id": unit["_id"]}, {"$inc": {"wood": 5}})
            commands_collection.delete_one({"_id": command["_id"]})
            await log(
                unit.get("race"),
                "Command Completed",
                f"{unit['name']} {unit['_id']} chopped {command.get('name')}",
                client=client,
                content=None,
            )

    elif name == "build":
        commands_collection.update_one(
            {"_id": command["_id"]}, {"$set": {"time": command["time"] - 1}}
        )
        if command.get("time") == 0:
            commands_collection.delete_one({"_id": command["_id"]})
            x = command.pop("x") // 16
            y = command.pop("y") // 16

            command["_id"] = f"{x}-{y}"

            keys = ["time", "author", "unit", "command"]
            for k in keys:
                command.pop(k)
            if command.get("type") == "wall":
                walls_collection.insert_one(command)
                utils.data.map_arr[x][y] = -1
            else:
                buildings_collection.insert_one(command)

            utils.data.map_objects[(x, y)] = command

            await log(
                unit.get("race"),
                "Construction Completed",
                f"Worker {unit['_id']} finished building {command.get('name')}",
                client=client,
                content=None,
            )

    elif name == "gather":
        result = gather(command, unit)
        if result == -1:
            await log(
                unit.get("race"),
                "Mine Depleted",
                f"{command['name']} was depleted while {unit['_id']} was mining.",
                client=client,
                content=None,
            )
        elif result == 1:
            await log(
                unit.get("race"),
                "No Workshop Found",
                f"{unit['_id']} stopped mining because it can't reach to a workshop.",
                client=client,
                content=None,
            )


async def log(race: str, title: str, message: str, client, content=None):
    channel_id = 1089906968031924274
    if race == "cyan":
        channel_id = 1138577304369504348
    elif race == "red":
        channel_id = 1138577441376452669
    elif race == "lime":
        channel_id = 1134178075731558450
    else:
        print(f"Invalid race during log. Race: {race}")
    channel = client.get_channel(channel_id)
    embed = discord.Embed(color=discord.Color.from_rgb(201, 0, 118), title=title)
    embed.description = message

    await channel.send(content=content, embed=embed)
