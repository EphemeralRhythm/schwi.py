from PIL import Image, ImageDraw
import utils.data
import time
import utils.database as db


def draw_map(player_post, unit_post, transparent=None):
    size = (6000, 6000)
    new_size = (800, 800)
    x, y = unit_post.get("x"), unit_post.get("y")

    # set constraint for x and y boundaries
    if x < new_size[0] // 2:
        x = new_size[0] // 2
    if x > size[0] - new_size[0] // 2:
        x = size[0] - new_size[0] // 2
    if y < new_size[1] // 2:
        y = new_size[1] // 2
    if y > size[1] - new_size[1] // 2:
        y = size[1] - new_size[1] // 2

    start_time = time.time()
    map_image = Image.open("images/NCNL/map.png")

    end_time_0 = time.time()
    fog_image = Image.new("RGBA", (6000, 6000), (0, 0, 0, 0))
    overlay = ImageDraw.Draw(fog_image)
    race = player_post.get("race")
    offset_size = (64, 64)
    x_bound = (
        x - new_size[0] // 2 - offset_size[0],
        x + new_size[0] // 2 + offset_size[0] + 1,
    )
    y_bound = (
        y - new_size[0] // 2 - offset_size[1],
        y + new_size[1] // 2 + offset_size[1] + 1,
    )
    if player_post.get("race") != "Admin":
        for b_x in range(x_bound[0] // 16, x_bound[1] // 16):
            for b_y in range(y_bound[0] // 16, y_bound[1] // 16):
                post = utils.data.map_fog.get((b_x, b_y))
                dynamic_post = utils.data.dynamic_fog.get(
                    (b_x, b_y), {"cyan": 0, "red": 0, "lime": 0}
                )
                if not post:
                    continue
                if not post.get(race):
                    overlay.rectangle(
                        (
                            b_x * 16,
                            b_y * 16,
                            b_x * 16 + 16,
                            b_y * 16 + 16,
                        ),
                        fill=(0, 0, 0),
                    )
                else:
                    if utils.data.game_time < 180:
                        if not dynamic_post.get(race):
                            overlay.rectangle(
                                (
                                    b_x * 16,
                                    b_y * 16,
                                    b_x * 16 + 16,
                                    b_y * 16 + 16,
                                ),
                                fill=(0, 0, 0, 100),
                            )
                    else:
                        if not dynamic_post.get(race):
                            overlay.rectangle(
                                (
                                    b_x * 16,
                                    b_y * 16,
                                    b_x * 16 + 16,
                                    b_y * 16 + 16,
                                ),
                                fill=(0, 0, 0, 200),
                            )

                        else:
                            overlay.rectangle(
                                (
                                    b_x * 16,
                                    b_y * 16,
                                    b_x * 16 + 16,
                                    b_y * 16 + 16,
                                ),
                                fill=(0, 0, 0, 100),
                            )

    end_time_1 = time.time()
    # draw naval units
    for unit in db.units_collection.find({"type": "naval"}):
        u_x, u_y = unit.get("x"), unit.get("y")
        if (
            u_x < x - new_size[0] // 2 - 32
            or u_x > x + new_size[0] // 2 + 32
            or u_y < y - new_size[1] // 2 - 32
            or u_y > y + new_size[1] // 2 + 32
            and race != "Admin"
        ):
            continue
        states = {-1: "attack", 0: "idle", 1: "move"}
        race = unit.get("race")
        name = unit.get("name")

        if player_post.get("race") != "Admin":
            if u := utils.data.dynamic_fog.get((u_x // 16, u_y // 16)):
                if not u.get(player_post.get("race")):
                    continue
            else:
                continue
        direction = unit.get("direction")

        if name == "Battleship":
            path = f"images/NCNL/Units/{race}/{name}/{direction}.png"
            s = 32
        else:
            path = f"images/NCNL/Units/boats/{direction}.png"
            s = 16

        unit_image = Image.open(path)
        map_image.paste(
            unit_image,
            (
                u_x - s // 2,
                u_y - s // 2,
                u_x + s // 2,
                u_y + s // 2,
            ),
            mask=unit_image,
        )

    # draw map objects
    for b_x in range(x_bound[0] // 16, x_bound[1] // 16):
        for b_y in range(y_bound[0] // 16, y_bound[1] // 16):
            object = utils.data.map_objects.get((b_x, b_y))
            if not object:
                continue

            if u := utils.data.dynamic_fog.get((b_x // 16, b_y // 16)):
                if not u.get(player_post.get("race")):
                    continue
            object_type = object.get("type")
            size = object.get("size", (16, 16))

            if object["name"] == "wheatfield":
                path = f"images/NCNL/Nature/Wheatfield{object['state']}.png"
            elif object_type == "building":
                race = object.get("race", "NPC")

                path = f"images/NCNL/{race}/{object.get('image')}.png"
            elif object_type == "wall":
                path = f"images/NCNL/Walls/{object.get('image')}.png"
            elif object_type == "nature":
                path = f"images/NCNL/Nature/{object.get('image')}.png"
            else:
                path = f"images/NCNL/Other/{object.get('image')}.png"

            image = Image.open(path)
            map_image.paste(
                image,
                (b_x * 16, b_y * 16, b_x * 16 + size[0], b_y * 16 + size[1]),
                mask=image,
            )

    end_time_2 = time.time()
    print("started")
    # draw units
    for unit in db.units_collection.find():
        if unit.get("type") == "naval":
            continue
        u_x, u_y = unit.get("x"), unit.get("y")
        if (
            u_x < x - new_size[0] // 2 - 32
            or u_x > x + new_size[0] // 2 + 32
            or u_y < y - new_size[1] // 2 - 32
            or u_y > y + new_size[1] // 2 + 32
            and player_post.get("race") != "Admin"
        ):
            continue
        states = {-1: "attack", 0: "idle", 1: "move"}
        race = unit.get("race")
        name = unit.get("name")

        if player_post.get("race") != "Admin":
            if u := utils.data.dynamic_fog.get((u_x // 16, u_y // 16)):
                if not u.get(player_post.get("race")):
                    continue
            else:
                continue

        if name == "Player":
            name += "/" + unit.get("class")
        state = states.get(unit.get("state"))
        direction = unit.get("direction")

        s = 32 if name == "Knight" or name == "Battleship" else 16
        path = f"images/NCNL/Units/{race}/{name}/{state}/{direction}.png"

        unit_image = Image.open(path)
        map_image.paste(
            unit_image,
            (
                u_x - s // 2,
                u_y - s // 2,
                u_x + s // 2,
                u_y + s // 2,
            ),
            mask=unit_image,
        )

        if name == "Lancer" and state == "attack":
            dir = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
            offset = dir.get(direction, (0, 0))
            u_x += 16 * offset[0]
            u_y += 16 * offset[1]

            path = f"images/NCNL/Units/{race}/{name}/{state}/{direction}2.png"

            unit_image = Image.open(path)
            map_image.paste(
                unit_image,
                (
                    u_x - s // 2,
                    u_y - s // 2,
                    u_x + s // 2,
                    u_y + s // 2,
                ),
                mask=unit_image,
            )

    path = "images/NCNL/Other/0.png"
    unit_image = Image.open(path)
    u_x, u_y = unit_post.get("x"), unit_post.get("y")
    s = 16
    map_image.paste(
        unit_image,
        (
            u_x - s // 2,
            u_y - s // 2,
            u_x + s // 2,
            u_y + s // 2,
        ),
        mask=unit_image,
    )
    end_time_3 = time.time()
    if transparent:
        return map_image, fog_image
    if player_post.get("race") != "Admin":
        map_image = Image.alpha_composite(map_image, fog_image)

    end_time_4 = time.time()

    # execution_time_0 = end_time_0 - start_time
    # execution_time_1 = end_time_1 - end_time_0
    # execution_time_2 = end_time_2 - end_time_1
    # execution_time_3 = end_time_3 - end_time_2
    # execution_time_4 = end_time_4 - end_time_3

    # print(f"Image.open() Time: {execution_time_0:.6f} seconds")
    # print(f"Fog Time: {execution_time_1:.6f} seconds")
    # print(f"Map Time: {execution_time_2:.6f} seconds")
    # print(f"Units Time: {execution_time_3:.6f} seconds")
    # print(f"Crop Time: {execution_time_4:.6f} seconds")
    print(f"Total Time: {(start_time - end_time_4):.6f} seconds\n")

    return map_image
