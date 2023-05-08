import discord
from utils import *

size = (5000, 3000)
sq_size = 20
map = {}
rows = size[1]//sq_size
cols = size[0]//sq_size
bin_grid = [[0 for i in range(cols)] for j in range(rows)]
graph_grid = []

with open("map.txt") as f:
    string = f.read()
map_grid = string.split(" ")
n = 250 # number of nodes in one row

for point in fog_collection.find():
    row,col = eval(point["_id"])
    fog = [point.get("Elf"), point.get("Ex-Machina"), point.get("Dwarf")]
    map[(row, col)] = (int(map_grid[n * row + col]), fog)

print("Map Initialized")
print("bin_rows:", len(bin_grid), "bin_cols", len(bin_grid[0]))
for r in range(rows):
    for c in range(cols):
        if not map.get((r, c)):
            print(r, c)
        if map.get((r, c))[0] == 1:
            bin_grid[r][c] = 1
        
graph_grid = make_grid(rows,cols)
for r in graph_grid:
    for node in r:
            node.update_neighbors(graph_grid, bin_grid)

print(len(graph_grid), len(graph_grid[0]))
print("Grids Initialized")


class Unit_Select(discord.ui.Select):
    def __init__(self, author, unit):
        self.author = author
        self.unit = unit
        options=[
            discord.SelectOption(label="Move",emoji="<:location:1065283234834940044>",description=f"Move this unit on the map."),
            discord.SelectOption(label="Attack (Unit)",emoji="<:crosshair:1065283238618214410>",description=f"Attack an enemy unit."),
            discord.SelectOption(label="Attack (Building)",emoji="<:crosshair:1065283238618214410>",description=f"Attack an enemy building."),
            discord.SelectOption(label="Structure",emoji="<:gears:1068824355687112756>", description="Interact with near buildings."),
            discord.SelectOption(label="Guard",emoji="⚔️", description="Attack any enemy units that come within field of view.")
            ]

        if self.unit["name"] in ["Elven Builder", "Ex-Machina Zeichen", "Dwarven Craftsman"]:
            options.append(discord.SelectOption(label="Build",emoji="<:tool:1070299017587732501>", description="Construct new buildings."))
            options.append(discord.SelectOption(label="Gather",emoji="<:pickaxe:1101437961414905898>", description="Gather resources from the map."))

        # if self.unit.get("_id") == 1058691794361122886:
        #     options.append(discord.SelectOption(label="Hack",emoji="<:crosshair:1065283238618214410>", description="Top Secret."))
        super().__init__(placeholder="Select your command",max_values=1,min_values=1,options=options)
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Interaction failed. The command author is not the same as the interaction author.")
            return
        
        if self.values[0] == "Guard":
            
            x,y = eval(self.unit.get("loc"))
            command = {
                    "author": self.author.id,
                    "unit": self.unit.get("_id"),
                    "command": "guard",
                    "loc": f"({x},{y})"
                }
            commands_collection.insert_one(command)
                
            await interaction.channel.send(f"Command added to queue!")
        if self.values[0] == "Move" or self.values[0] == "Attack (Unit)" or self.values[0] == "Attack (Building)":
            if self.values[0] == "Move":
                await interaction.response.send_message("Enter the distance vector x y")
            elif self.values[0] == "Attack (Unit)" or "Attack (Building)":
                await interaction.response.send_message("Enter the distance vector x y for the target.")

            def check(m):
                return m.channel == interaction.channel and m.author == self.author
            try:
                vector = await interaction.client.wait_for('message', check = check, timeout = 30)
            except asyncio.TimeoutError:
                return  
            
            if len(vector.content.split(" ")) != 2:
                await interaction.channel.send("Invalid Vector Format")
                return
            x, y = vector.content.split(" ")
            try:
                x, y = int(x), int(y)
            except:
                await interaction.channel.send("Invalid Vector Format")
                return

            i_x, i_y = eval(self.unit.get("loc"))

            if i_x + x >= 5000 or i_y + y >= 3000 or i_x + x < 0 or i_y + y < 0:
                await interaction.channel.send("Destination is unreachable.")
                return

            if self.values[0] == "Attack (Unit)":
                if abs(x) + abs(y) > 500:
                    await interaction.channel.send("Target is too far.")
                    return
            if not self.unit.get("name") in flying_units:
                
                path = find_path(graph_grid,start= graph_grid[i_y//20][i_x//20],end= graph_grid[(y+i_y)//20][(x+i_x)//20])
         
                if not path:
                    await interaction.channel.send("Destination is unreachable.")
                    return
            if self.values[0] == "Move":
                command = {
                    "author": self.author.id,
                    "unit": self.unit.get("_id"),
                    "command": "move",
                    "loc": f"({i_x + x},{i_y + y})"
                }
                commands_collection.insert_one(command)
                
                await interaction.channel.send(f"Command added to queue!")

            elif self.values[0] == "Attack (Unit)":
                
                query = {"race": {"$ne": self.unit.get("race")}}
                players = units_collection.find(query)
                def locate(unit):
                    loc_x, loc_y = eval(unit.get("loc"))
                    return abs(i_x + x - loc_x) + abs(i_y + y - loc_y)
                players = sorted(players, key=lambda enemy: locate(enemy))
                
                if locate(players[0]) > 200:
                    await interaction.channel.send("No target found in the specified location.")
                    return
                message = await interaction.channel.send(f"Found {players[0].get('name')}. React with ✅ to confirm the command")
                await message.add_reaction('✅')
                
                def check_reaction(reaction, user):
                    return  str(reaction.emoji) == '✅' and user == self.author
                timed_out = False
                try:
                    reaction = await interaction.client.wait_for('reaction_add', check = check_reaction, timeout = 10)
                except asyncio.TimeoutError:
                    timed_out = True
                if not timed_out:
                    command = {
                    "author": self.author.id,
                    "unit": self.unit.get("_id"),
                    "command": "attack",
                    "target": players[0]["_id"]
                    }
                    commands_collection.insert_one(command)
                    await interaction.channel.send(f"Command added to queue!")

            elif self.values[0] == "Attack (Building)":
                query = {"race": {"$ne": self.unit.get("race")}}
                buildings = buildings_collection.find(query)
                def locate(unit):
                    arr = unit.get("loc")
                    loc_x, loc_y = (arr[0] + arr[2])//2, (arr[1] + arr[3])//2
                    return abs(i_x + x - loc_x) + abs(i_y + y - loc_y)
                players = sorted(buildings, key=lambda enemy: locate(enemy))
                
                if locate(players[0]) > 200:
                    await interaction.channel.send("No target found in the specified location.")
                    return
                message = await interaction.channel.send(f"Found {players[0].get('name')}. React with ✅ to confirm the command")
                await message.add_reaction('✅')
                
                def check_reaction(reaction, user):
                    return  str(reaction.emoji) == '✅' and user == self.author
                timed_out = False
                try:
                    reaction = await interaction.client.wait_for('reaction_add', check = check_reaction, timeout = 10)
                except asyncio.TimeoutError:
                    timed_out = True
                if not timed_out:
                    command = {
                    "author": self.author.id,
                    "unit": self.unit.get("_id"),
                    "command": "battack",
                    "target": players[0]["_id"]
                    }
                    commands_collection.insert_one(command)
                    await interaction.channel.send(f"Command added to queue!")       
                
        elif self.values[0] == "Structure":
            query = {"race": self.unit.get("race")}
            buildings = buildings_collection.find(query)
            
            x, y = eval(self.unit.get("loc"))
            def locate(building):
                x1, y1, x2, y2 = building.get("loc")
                xm = (x1 + x2)/2
                ym = (y1 + y2)/2
                return abs(xm - x) + abs(ym - y)
            buildings = sorted(buildings, key=lambda b: locate(b))

            if locate(buildings[0]) > 300:
                await interaction.response.send_message("No nearby buildings found.")
                return
            view = BuildView(author= self.author, building = buildings[0])    
            await interaction.response.send_message(content= f"{buildings[0].get('name')}", view = view)

        elif self.values[0] == "Build":
            view = constructView(author = self.author, unit = self.unit)
            await interaction.response.send_message(view=view)

        elif self.values[0] == "Gather":
            query = {"race": self.unit.get("race")}
            ores = ores_collection.find()
            
            x, y = eval(self.unit.get("loc"))
            def locate(building):
                xm = building.get("x") * 20
                ym = building.get("y") * 20
                
                return abs(xm - x) + abs(ym - y)
            ores = sorted(ores, key=lambda b: locate(b))

            if locate(ores[0]) > 100:
                await interaction.response.send_message("No nearby ores found.")
                return
            
            message = await interaction.channel.send(f"Found {ores[0].get('type')} ore. Amount available: {ores[0].get('amount')}\nReact with ✅ to confirm the command.")
            await message.add_reaction('✅')
            
            def check_reaction(reaction, user):
                return  str(reaction.emoji) == '✅' and user == self.author
            timed_out = False
            try:
                reaction = await interaction.client.wait_for('reaction_add', check = check_reaction, timeout = 10)
            except asyncio.TimeoutError:
                timed_out = True
            if not timed_out:
                command = {
                    "author": self.author.id,
                    "unit": self.unit.get("_id"),
                    "command": "gather",
                    "ore": ores[0]["_id"],
                    "type": ores[0].get("type"),
                    "state": "collect",
                    "x": ores[0].get("x"),
                    "y": ores[0].get("y")
                }
                commands_collection.insert_one(command)
                await interaction.channel.send(f"Command added to queue!") 
        
        elif self.values[0] == "Hack":
            await interaction.response.send_message("Enter the distance vector x y for the target.")

            def check(m):
                return m.channel == interaction.channel and m.author == self.author
            try:
                vector = await interaction.client.wait_for('message', check = check, timeout = 30)
            except asyncio.TimeoutError:
                return  
            
            if len(vector.content.split(" ")) != 2:
                await interaction.channel.send("Invalid Vector Format")
                return
            x, y = vector.content.split(" ")
            try:
                x, y = int(x), int(y)
            except:
                await interaction.channel.send("Invalid Vector Format")
                return

            i_x, i_y = eval(self.unit.get("loc"))

            if i_x + x >= 5000 or i_y + y >= 3000 or i_x + x < 0 or i_y + y < 0:
                await interaction.channel.send("Destination is unreachable.")
                return

            
            if abs(x) + abs(y) > 500:
                await interaction.channel.send("Target is too far.")
                return
            
            query = {"race": {"$ne": self.unit.get("race")}}
            players = units_collection.find(query)
            def locate(unit):
                loc_x, loc_y = eval(unit.get("loc"))
                return abs(i_x + x - loc_x) + abs(i_y + y - loc_y)
            players = sorted(players, key=lambda enemy: locate(enemy))
            
            if locate(players[0]) > 200:
                await interaction.channel.send("No target found in the specified location.")
                return
            message = await interaction.channel.send(f"Found {players[0].get('name')}. React with ✅ to confirm the command")
            await message.add_reaction('✅')
            
            def check_reaction(reaction, user):
                return  str(reaction.emoji) == '✅' and user == self.author
            timed_out = False
            try:
                reaction = await interaction.client.wait_for('reaction_add', check = check_reaction, timeout = 10)
            except asyncio.TimeoutError:
                timed_out = True
            if not timed_out:

                target = players[0]
                if target.get("owner"):
                    units_collection.update_one({"_id": target.get("_id")}, {"$set": {"owner": 1058691794361122886, "race": "Elf"}})

                else:
                    dead_collection.insert_one(target)
                    units_collection.delete_one({"_id": target["_id"]})
                    target.pop("_id")
                    target["owner"] = 1058691794361122886
                    target["race"] = "Elf"
                    
                    units_collection.insert_one(target)
                await interaction.channel.send(f"Success! {target.get('_id')}")


class construct_Select(discord.ui.Select):
    def __init__(self, author, unit):
        self.author = author
        self.unit = unit
        options = []

        if self.unit.get("race") == 'Elf':
            buildings = ["Elven Barracks", "Elven Magic Academy", "Elven Magic Research Facility"]      
        elif self.unit.get("race") == 'Dwarf':
            buildings = ["Dwarven Barracks", "Dwarven Arcane Forge", "Dwarven Development Facility"]  
        elif self.unit.get("race") == 'Ex-Machina':
            buildings = ["Ex-Machina War Factory", "Ex-Machina Machine Assembly", "Ex-Machina Research Labs"]
        
        buildings.append("Resources Facility")
        for build in buildings:
            gold, iron, crystal, mithril = construction_costs.get(build)
            cost_string = ""
            
            cost_string += f"Gold: {gold} "
            cost_string += f",Iron: {iron} "
            cost_string += f",Crystal: {crystal} "
            cost_string += f",Mithril: {mithril} "

            options.append(discord.SelectOption(label=build, description=cost_string))
 
        super().__init__(placeholder="Select the building",max_values=1,min_values=1,options=options)
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Interaction failed. The command author is not the same as the interaction author.")
            return
        cost = construction_costs.get(self.values[0])
        player_post = resources_collection.find_one({"_id": self.author.id})
        inventory = [player_post.get("gold"), player_post.get("iron"), player_post.get("crystal"), player_post.get("mithril")] 
        
        for index, building_cost in enumerate(cost):
            if building_cost > inventory[index]:
                await interaction.response.send_message("Insufficient resources.")
                return

        x, y = eval(self.unit.get("loc"))
        s = buildings_info.get(self.values[0])[2]

        x,y = (x// 20) * 20, (y//20) * 20

        node = map.get((s + y//20 ,s + x//20))
        if not node:
            await interaction.response.send_message("Cannot build here.")
            return
        
        if not node[0]:
            await interaction.response.send_message("Cannot build here.")
            return
        
        
        rect1 = (x, y, s*20 + x, s*20 + y)

        for build in buildings_collection.find():
            loc_arr = build.get("loc")
            rect2 = (loc_arr[0], loc_arr[1], loc_arr[2], loc_arr[3])

            if overlap( rect1, rect2):
                await interaction.response.send_message("Cannot build here. The builder location is too close to another building.")
                return
        resources = ["gold", "iron", "crystal", "mithril"]
        filter = {"_id": self.author.id}

        for index, currency in enumerate(inventory):
            currency -= cost[index]

            update = {"$set": {resources[index]: currency}}
            result = resources_collection.update_one(filter, update)
        
        command = {
            "author": self.author.id,
            "unit": self.unit.get("_id"),
            "command": "build",
            "name": self.values[0],
            "max_hp": buildings_info.get(self.values[0])[1],
            "hp": buildings_info.get(self.values[0])[1],
            "race": self.unit.get("race"),
            "loc": rect1,
            "time": buildings_info.get(self.values[0])[0] * GAME_SPEED * 24 * 30
        }
        
        result = commands_collection.insert_one(command)
        await interaction.response.send_message("Command added to queue!")

class Building_Select(discord.ui.Select):
    def __init__(self, author, building):
        self.author = author
        self.building = building
        options = []
        troops = []
        if building.get("name") == "Elven Headquarters":
            troops = ["Elven Builder"]
        elif building.get("name") == "Elven Barracks":
            troops = ["Elven Ranger", "Elven Archer", "Elven Warship"]
        elif building.get("name") == "Elven Magic Academy":
            troops = ["Elven Mage", "Elven Summoner"]
        elif building.get("name") == "Elven Magic Research Facility":
            pass

        elif building.get("name") == "Ex-Machina Headquarters":
            troops = ["Ex-Machina Zeichen"]
        elif building.get("name") == "Ex-Machina War Factory":
            troops = ["Ex-Machina Prüfer","Ex-Machina Angriff", "Ex-Machina Seher"]
        elif building.get("name") == "Ex-Machina Machine Assembly":
            troops = ["Ex-Machina Kämpfer", "Ex-Machina Schwer"]
        elif building.get("name") == "Ex-Machina Research Labs":
            pass

        elif building.get("name") == "Dwarven Headquarters":
            troops = ["Dwarven Craftsman"]
        elif building.get("name") == "Dwarven Barracks":
            troops = ["Dwarven Scout", "Dwarven Demolitionist", "Dwarven Subterrane"]
        elif building.get("name") == "Dwarven Arcane Forge":
            troops = ["Dwarven Combatant", "Dwarven Golem"]
        elif building.get("name") == "Dwarven Development Facility":
            pass

        
        for troop in troops:
            gold, iron, crystal, mithril = production_costs.get(troop)
            cost_string = ""
            if gold:
                cost_string += f"Gold: {gold} "
            if iron:
                cost_string += f"Iron: {iron} "
            if crystal:
                cost_string += f"Crystal: {crystal} "
            if mithril:
                cost_string += f"Mithril: {mithril} "

            options.append(discord.SelectOption(label="Train " + troop, description= cost_string))
        
        
        if self.building.get("name") == "Resources Facility":
            for type in ["gold", "iron", "mithril", "crystal"]:
                options.append(discord.SelectOption(label="Withdraw " + type, description= self.building.get(type, 0)))
        
        super().__init__(placeholder="Select your command",max_values=1,min_values=1,options=options)
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Interaction failed. The command author is not the same as the interaction author.")
            return      

        player_post = resources_collection.find_one({"_id": self.author.id})
        if self.values[0].startswith("Train"):
            unit_name = self.values[0].split("Train ")[1]

            inventory = [player_post.get("gold"), player_post.get("iron"), player_post.get("crystal"), player_post.get("mithril")] 
            cost =    production_costs.get(unit_name)

            for index, currency in enumerate(inventory):
                if currency < cost[index]:
                    await interaction.response.send_message("Insufficient resources.")
                    return

            filter = {"building": self.building["_id"]}
            unit_in_queue = units_queue.find_one(filter)
            
            if unit_in_queue:
                await interaction.response.send_message("This building already has a unit in queue.")
                return
            
            resources = ["gold", "iron", "crystal", "mithril"]
            filter = {"_id": self.author.id}
            for index, currency in enumerate(inventory):
                currency -= cost[index]

                update = {"$set": {resources[index]: currency}}
                result = resources_collection.update_one(filter, update)

            count_post = info_collection.find_one({"_id": "Count"})
            count = count_post.get("count")
            info_collection.update_one({"_id": "Count"}, {"$set": {"count": count + 1}})

            loc_arr = self.building.get("loc")
            loc_x = (loc_arr[0] + loc_arr[2]) //2
            loc_y = (loc_arr[1] + loc_arr[3]) //2
            
            info_post = info_collection.find_one({"_id": unit_name})
            unit_post = {
                "_id": count,
                "hp": info_post.get("hp"),
                "name": unit_name,
                "race": self.building["race"],
                "loc": f"({loc_x}, {loc_y})",
                "owner": self.author.id,
                "building": self.building["_id"],
                "time": int(unit_training_time.get(unit_name) * GAME_SPEED * 24 * 30)
            }
            
            units_queue.insert_one(unit_post)
            await interaction.response.send_message(f"Unit added to queue! Ticks Remaining: {unit_post.get('time')}")
            
        elif self.values[0].startswith("Withdraw"):
            type = self.values[0].split("Withdraw ")[1]
            amount = self.building.get(type)

            if not amount:
                await interaction.response.send_message("There's nothing to withdraw.")
                return
            
            resources_collection.update_one(
                    {"_id": self.author.id},
                    {"$inc": {type: amount}},
            )

            buildings_collection.update_one(
                {"_id": self.building["_id"]},
                {"$set": {type: 0}},
            )
            await interaction.response.send_message(f"Withdrew {amount} {type} from the resources facility.")
            
class SelectView(discord.ui.View):
    def __init__(self, author, unit, *, timeout = 20):
        super().__init__(timeout=timeout)
        self.add_item(Unit_Select(author = author, unit = unit))

class constructView(discord.ui.View):
    def __init__(self, author, unit, *, timeout = 20):
        super().__init__(timeout=timeout)
        self.add_item(construct_Select(author = author, unit = unit))

class BuildView(discord.ui.View):
    def __init__(self, author, building, *, timeout = 20):
        super().__init__(timeout=timeout)
        self.add_item(Building_Select(author = author, building = building))
