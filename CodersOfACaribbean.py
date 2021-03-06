import sys
import time
from inspect import currentframe


class DebugTool:
    def __init__(self):
        try:
            self.fd = open(r"input.txt")
        except (ImportError, OSError):
            self.debug_mode = False
        else:
            import matplotlib.pyplot as plt
            self.plt = plt
            self.fg = None
            self.ax = None
            self.debug_mode = True

    def input(self):
        if self.debug_mode:
            data = self.fd.readline()
        else:
            data = input()
        print(data, file=sys.stderr, flush=True)
        return data

    def start_timer(self):
        self.timer = time.time()

    def elapsed_time(self):
        end_time = time.time()
        interval = end_time - self.timer
        self.stderr(interval * 1000, "m sec")

    @staticmethod
    def stderr(*args):
        cf = currentframe()
        print(*args, "@" + str(cf.f_back.f_lineno), file=sys.stderr, flush=True)

    def plot_vector_clock(self, vct, clr="b", txt=""):
        # todo: refactor in OO style
        self.plt.plot((0, vct[0]), (0, vct[1]), color=clr)
        self.plt.text(vct[0], vct[1], txt)


class Entity:
    def __init__(self, entity_id, x, y):
        self.entity_id = int(entity_id)
        self.x = int(x)
        self.y = int(y)

    def distance_to(self, entity_or_cubegrid):
        """Return distance to the entity using cube coordinate system."""
        if isinstance(entity_or_cubegrid, Entity):
            cubegrid = entity_or_cubegrid.cube()
        else:
            cubegrid = entity_or_cubegrid
        return max(abs(ax[0] - ax[1]) for ax in zip(cubegrid, self.cube()))

    def cube(self):
        """Return coordinates by Cube system converted from Offset system for simpler algorithm. """
        cube_x = int(self.x - (self.y - (self.y % 2)) / 2)
        cube_z = int(self.y)
        cube_y = int(-cube_x - cube_z)
        return Cube((cube_x, cube_y, cube_z))  # type: Cube


class Entities(list):
    def __init__(self, entity_list=()):
        super().__init__(entity_list)

    def ally(self):
        class_name = type(self)
        return class_name([e for e in self if e.owner == 1])  # type: class_name

    def enemy(self):
        class_name = type(self)
        return class_name([e for e in self if e.owner != 1])  # type: class_name

    def closest_to(self, entity_or_cubegrid):
        return min(self, key=lambda x: x.distance_to(entity_or_cubegrid))  # type: type(self)


class Ship(Entity):
    def __init__(self, entity_id, x, y, orientation, speed, rum, owner):
        super().__init__(entity_id, x, y)
        self.orientation = int(orientation)
        self.speed = int(speed)
        self.rum = int(rum)
        self.owner = int(owner)

        ent = entities_in_history.last(self.entity_id)
        if ent is None:
            self.turns_to_fire = 0
            self.turns_to_mine = 0
            self.turns_halted = 0
        else:
            self.turns_to_fire = max(0, ent.turns_to_fire - 1)
            self.turns_to_mine = max(0, ent.turns_to_mine - 1)
            self.turns_halted = ent.turns_halted

    def next_location(self):
        return self.cube().neighbor(self.orientation, self.speed)  # type:Cube

    def predict_command(self, command):
        """Call 'predict' by 'command' and return the value  with the 'command' value."""

        if command == "WAIT":
            return self.predict(0, 0) + (1, command)

        elif command == "PORT":
            return self.predict(1, 0) + (10, command)

        elif command == "STARBOARD":
            return self.predict(-1, 0) + (10, command)

        elif command == "FASTER":
            return self.predict(0, 1) + (100, command)

        elif command == "SLOWER":
            return self.predict(0, -1) + (0, command)

    def predict(self, turning, speed):
        """Return a tuple of values predicted for the next two turns with specified controlling values.

        Note that the prediction is made assuming the command for the second turn as "WAIT".

        The arguments are:
          turning -- specify 1 to turn 60 degree left, -1 to turn 60 degree right.
          speed -- specify 1 to speed up, -1 to speed down.

        The return values are:
          <Damage Control>
          rum -- increase/decrease of rum

          <Targeting>
          closeness_barrel -- negative value of distance from the closest barrel
          closeness_toughest_enemy -- negative value of distance from the toughest enemy, if NO_BARREL_ACTION true

          <Avoiding>
          remoteness_edge -- distance from the edge of map (Check only if so close to the dislikes)
          remoteness_mine -- distance from the closest mine (Check only if so close to the dislikes)
          remoteness_enemy -- distance from the closest enemy ship, if NO_BARREL_ACTION true

          <Mobility Control>
          speed of the ship -- speed after the second turn

          If NO_BARREL_ACTION is true, change the priority after no barrels left in the map so as to
          rush the toughest enemy or run away from enemies according to quantity of rum left on ships."""

        # <Damage Control>
        # rum -- increase/decrease of rum
        # 1st turn
        current_location = self.cube()
        current_orientation = self.orientation
        current_speed = self.speed

        # Decrease rum
        rum = -1

        # Change speed
        current_speed = min(2, max(0, current_speed + speed))
        # Move Forward with collision check
        temp_location = current_location.neighbor(current_orientation, current_speed)  # type: Cube
        x, y = temp_location.offset()
        if 0 <= x <= MAP_WIDTH and 0 <= y <= MAP_HEIGHT:
            current_location = temp_location
        else:
            if current_speed == 2:
                temp_location = self.cube().neighbor(current_orientation, 1)  # type: Cube
                if 0 <= x <= MAP_WIDTH and 0 <= y <= MAP_HEIGHT:
                    current_location = temp_location
            current_speed = 0
        current_ship_occupation = self.ship_occupation(current_location, current_orientation)
        # Initialize record of ship_occupation
        ship_occupation_set = set(current_ship_occupation)
        # Turn Ship
        current_orientation = (self.orientation + turning) % 6
        current_ship_occupation = self.ship_occupation(current_location, current_orientation)
        # Record additional ship_occupation
        ship_occupation_set |= set(current_ship_occupation)
        # Check impact of a cannonball
        # todo: Check explosion of mines by cannonballs
        rum -= cannonballs.impact_at(current_ship_occupation, 1)

        # 2nd turn
        # Decrease rum
        rum -= 1
        # Move forward with collision check (No change of speed and orientation)
        temp_location = current_location.neighbor(current_orientation, current_speed)  # type: Cube
        x, y = temp_location.offset()
        if 0 <= x <= MAP_WIDTH and 0 <= y <= MAP_HEIGHT:
            current_location = temp_location
        else:
            if current_speed == 2:
                temp_location = self.cube().neighbor(current_orientation, 1)  # type: Cube
                if 0 <= x <= MAP_WIDTH and 0 <= y <= MAP_HEIGHT:
                    current_location = temp_location
            current_speed = 0
        current_ship_occupation = self.ship_occupation(current_location, current_orientation)
        # Record additional ship_occupation
        ship_occupation_set |= set(current_ship_occupation)
        # Check impact of a cannonball
        # todo: Check explosion of mines by cannonballs
        rum -= cannonballs.impact_at(current_ship_occupation, 2)
        # Check touching a mine and getting a barrel with ship_occupation_set
        for loc in ship_occupation_set:
            rum += barrels.rum_at(loc)
            rum -= mines.exist_at(loc)

        # <Targeting>
        # closeness_barrel -- negative value of distance from the closest barrel
        bow = current_location.neighbor(current_orientation)
        if barrels is None or len(barrels) == 0:
            closeness_barrel = - NOT_FOUND
            # closeness_barrel = closeness_barrel, - NOT_FOUND
        else:
            closeness_barrel = -barrels.closest_to(bow).distance_to(bow)
            # closeness_barrel = closeness_barrel, -barrels.closest_to(current_location).distance_to(current_location)

        # closeness_toughest_enemy -- negative value of distance from the toughest enemy
        if NO_BARREL_ACTION and ships.toughest().owner == 1:
            closeness_toughest_enemy = -NOT_FOUND
            # closeness_toughest_enemy = closeness_toughest_enemy, -NOT_FOUND
        else:
            closeness_toughest_enemy = -ships.enemy().toughest().distance_to(bow)
            # closeness_toughest_enemy = closeness_toughest_enemy, \
            #    -ships.enemy().toughest().distance_to(current_location)

        # <Avoiding>
        # remoteness_edge -- distance from the edge of map
        bow = current_location.neighbor(current_orientation).offset()
        remoteness_edge = min(bow[0], MAP_WIDTH - bow[0], bow[1], MAP_HEIGHT - bow[1])
        if remoteness_edge > DISTANCE_TO_CHECK_EDGE:
            remoteness_edge = NOT_FOUND

        # remoteness_mine -- distance from the closest mine
        if mines is None or len(mines) == 0:
            remoteness_mine = NOT_FOUND
        else:
            remoteness_mine = mines.closest_to(current_location).distance_to(current_location)
        if remoteness_mine > DISTANCE_TO_CHECK_MINE:
            remoteness_mine = NOT_FOUND

        # remoteness_enemy -- distance from the closest enemy ship
        if NO_BARREL_ACTION and ships.toughest().owner == 1:
            remoteness_enemy = ships.enemy().closest_to(current_location).distance_to(current_location)
        else:
            remoteness_enemy = NOT_FOUND

        # return result of evaluation
        return rum, (closeness_barrel, closeness_toughest_enemy), (
            remoteness_edge, remoteness_mine, remoteness_enemy), current_speed

    @staticmethod
    def ship_occupation(location, orientation):
        return location, location.neighbor(orientation), location.neighbor(orientation, -1)  # type: tuple[Cube]


class Ships(Entities):
    def toughest(self):
        return max(self, key=lambda x: x.rum)


class Barrel(Entity):
    def __init__(self, entity_id, x, y, rum):
        super().__init__(entity_id, x, y)
        self.rum = int(rum)


class Barrels(Entities):
    def rum_at(self, cube_location):
        for barrel in self:  # type: Barrel
            if barrel.cube() == cube_location:
                return barrel.rum
        return 0


class Cannonball(Entity):
    def __init__(self, entity_id, x, y, shooter, turns_to_impact):
        super().__init__(entity_id, x, y)
        self.shooter = int(shooter)
        self.turns_to_impact = int(turns_to_impact)


class Cannonballs(Entities):
    def impact_at(self, current_ship_occupation, turns_to_impact):
        """Return damage of the ship occupying grids specified at turns_to_impact.

        current_ship_occupation -- a tuple consists of grids in cube system for center, bow and stern of the ship"""

        # Center
        damage = 0
        target = current_ship_occupation[0]
        for cannonball in self:  # type: Cannonball
            if cannonball.cube() == target and cannonball.turns_to_impact == turns_to_impact:
                damage += CANNON_HIGH_DAMAGE

        # Bow and stern
        for target in current_ship_occupation[1:3]:
            for cannonball in self:  # type: Cannonball
                if cannonball.cube() == target and cannonball.turns_to_impact == turns_to_impact:
                    damage += CANNON_LOW_DAMAGE

        return damage


class Mine(Entity):
    def __init__(self, entity_id, x, y):
        super().__init__(entity_id, x, y)


class Mines(Entities):
    def exist_at(self, cube_location):
        for mine in self:  # type: Mine
            if mine.cube() == cube_location:
                return MINE_HIGH_DAMAGE
        return 0


class Cube(tuple):
    def __new__(cls, value=(0, 0, 0)):
        return super().__new__(cls, value)

    def __add__(self, cube):
        return Cube(m + n for m, n in zip(self, cube))

    def __neg__(self):
        return Cube([-n for n in self])

    def __sub__(self, cube):
        return self.__add__(-cube)

    def __mul__(self, n):
        return Cube([m * n for m in self])

    def neighbor(self, orientation, grids=1):
        neighbors = ((+1, -1, 0), (+1, 0, -1), (0, +1, -1),
                     (-1, +1, 0), (-1, 0, +1), (0, -1, +1))
        return self + Cube(neighbors[orientation]) * grids  # type: Cube

    def offset(self):
        return int(self[0] + (self[2] - self[2] % 2) / 2), self[2]


class History(list):
    def last(self, entity_id, turns=-1):
        if len(self) != 0:
            for ent in self[turns]:
                if ent.entity_id == entity_id:
                    return ent  # type: Entity


#######################################
# Debugger Instantiation
#######################################
DT = DebugTool()

#######################################
# Constant Values
#######################################
COOLDOWN_CANNON = 2
COOLDOWN_MINE = 5
STEERING_COMMAND = ("WAIT", "PORT", "STARBOARD", "FASTER", "SLOWER")
MAP_WIDTH = 23
MAP_HEIGHT = 21
CANNON_HIGH_DAMAGE = 50
CANNON_LOW_DAMAGE = 25
MINE_HIGH_DAMAGE = 25
MINE_LOW_DAMAGE = 10
NOT_FOUND = 99

#######################################
# Parameters to be adjusted
#######################################
DISTANCE_TO_FIRE = 4
DISTANCE_TO_CHECK_MINE = 4
DISTANCE_TO_CHECK_EDGE = 4
AUTO_MOVE = False
FORCE_FASTER = True
NO_BARREL_ACTION = True
# MANUAL_MOVE = True

#######################################
# Initialization
#######################################
entities_in_history = History()

#######################################
# Game Loop
#######################################
while True:
    # Initialize for turn
    ships = Ships()
    barrels = Barrels()
    cannonballs = Cannonballs()
    mines = Mines()

    # Input for turn
    my_ship_count = int(DT.input())  # the number of remaining ships
    entity_count = int(DT.input())  # the number of entities (e.g. ships, mines or cannonballs)
    for i in range(entity_count):
        entity_id, entity_type, x, y, arg_1, arg_2, arg_3, arg_4 = DT.input().split()
        if entity_type == "SHIP":
            ships.append(Ship(entity_id, x, y, arg_1, arg_2, arg_3, arg_4))
        if entity_type == "BARREL":
            barrels.append(Barrel(entity_id, x, y, arg_1))
        if entity_type == "CANNONBALL":
            cannonballs.append(Cannonball(entity_id, x, y, arg_1, arg_2))
        if entity_type == "MINE":
            mines.append(Mine(entity_id, x, y))

    # Command for my ships
    for s in ships.ally():  # type: Ship
        if AUTO_MOVE:
            # Dodge a mine or a cannonball

            # Check location of next turn
            next_location = s.next_location()
            # Then check following location after the next with WAIT, PORT and STARBOARD move.

            following_location = next_location + Cube().neighbor(s.orientation) * s.speed  # type:Cube
            #   if it touches a mine or a cannonball and damage.
            # If wrong, try PORT and STARBOARD move.
            # If everything wrong, select move which takes the least damage.

            # Fire to an enemy ship
            target_ship = ships.enemy().closest_to(s)  # type: Ship
            if target_ship.distance_to(s) <= DISTANCE_TO_FIRE and s.turns_to_fire == 0:
                target_cube = target_ship.next_location()  # type: Cube
                command = "FIRE {0} {1}".format(*(target_cube.offset()))
                s.turns_to_fire = COOLDOWN_CANNON
            # Get a barrel
            else:
                if barrels:
                    barrel = barrels.closest_to(s)  # type: Barrel
                    command = "MOVE {0} {1}".format(barrel.x, barrel.y)
                else:
                    command = "MOVE {0} {1}".format(target_ship.x, target_ship.y)
        else:
            # Compare value of each action Wt, Pt, St, Sl, Ft
            # value = (more rum, closer to barrel, further from mine/map edge, more speed, command)
            if s.speed == 0:
                s.turns_halted += 1
            else:
                s.turns_halted = 0

            values = [s.predict_command(com) for com in STEERING_COMMAND]
            DT.stderr(values)
            # If halted for a while and no damage, move forcibly
            if FORCE_FASTER and s.turns_halted > 3 and values[3][0] >= -2:
                command = "FASTER"
            else:
                # Otherwise, choose the action with highest value
                command = max(values)[-1]

            # If WAIT does not lost rum by mine or cannonball, enable to fire(mine)
            if values[0][0] >= -2:
                # ToDo: refine conditions to fire
                target_ship = ships.enemy().closest_to(s)  # type: Ship
                if target_ship.distance_to(s) <= DISTANCE_TO_FIRE and s.turns_to_fire == 0:
                    # ToDo: improve aiming algorithm and create method
                    target_cube = target_ship.next_location()  # type: Cube
                    command = "FIRE {0} {1}".format(*(target_cube.offset()))
                    s.turns_to_fire = COOLDOWN_CANNON

        # Execute the command
        print(command)

    entities_in_history.append(ships + barrels + mines)
