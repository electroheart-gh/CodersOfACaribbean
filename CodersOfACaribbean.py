import sys
import math
import time
from inspect import currentframe
from operator import methodcaller
from operator import attrgetter


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

    def distance_to(self, entity):
        """Returns distance to the entity using cube coordinate system."""
        # return (entity.x - self.x) ** 2 + (entity.y - self.y) ** 2
        # x0, y0, z0 = self.cube()
        # x1, y1, z1 = entity.cube()
        # return max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
        return max(abs(ax[0] - ax[1]) for ax in zip(entity.cube(), self.cube()))

    def cube(self):
        """Returns coordinates by Cube system converted from Offset system for simpler algorithm. """
        cube_x = int(self.x - (self.y - (self.y % 2)) / 2)
        cube_z = int(self.y)
        cube_y = int(-cube_x - cube_z)
        return Cube((cube_x, cube_y, cube_z))


class Entities(list):
    def __init__(self, entity_list=()):
        super().__init__(entity_list)

    def ally(self):
        return Entities([e for e in self if e.owner == 1])  # type: Entities

    def enemy(self):
        return Entities([e for e in self if e.owner != 1])  # type: Entities

    def closest_to(self, entity):
        if len(self):
            return min(self, key=methodcaller("distance_to", entity))
        else:
            return None


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
        else:
            self.turns_to_fire = max(0, ent.turns_to_fire - 1)
            self.turns_to_mine = max(0, ent.turns_to_mine - 1)

        DT.stderr("speed {0}".format(self.speed))

    def next_location(self):
        return self.cube() + Cube().neighbor(self.orientation) * self.speed  # type:Cube


class Ships(Entities):
    pass


class Barrel(Entity):
    def __init__(self, entity_id, x, y, rum):
        super().__init__(entity_id, x, y)
        self.rum = int(rum)


class Barrels(Entities):
    pass


class Cannonball(Entity):
    def __init__(self, entity_id, x, y, shooter, turns_to_impact):
        super().__init__(entity_id, x, y)
        self.shooter = int(shooter)
        self.turns_to_impact = turns_to_impact


class Cannonballs(Entities):
    pass


class Mine(Entity):
    def __init__(self, entity_id, x, y):
        super().__init__(entity_id, x, y)


class Mines(Entities):
    pass


class History(list):
    def last(self, entity_id, turns=-1):
        try:
            for ent in self[turns]:
                if ent.entity_id == entity_id:
                    return ent
            return None
        except IndexError:
            return None


#######################################
# Debugger Instantiation
#######################################
DT = DebugTool()

#######################################
# Initial Input
#######################################

#######################################
# Global Variables for Game
#######################################
turns_to_fire = 2
turns_to_mine = 5

#######################################
# Parameters to be adjusted
#######################################
distance_to_fire = 4

#######################################
# Game Loop
#######################################

entities_in_history = History()


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

    def neighbor(self, orientation):
        neighbors = ((+1, -1, 0), (+1, 0, -1), (0, +1, -1),
                     (-1, +1, 0), (-1, 0, +1), (0, -1, +1))
        return self + Cube(neighbors[orientation])

    def offset(self):
        return int(self[0] + (self[2] - self[2] % 2) / 2), self[2]


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
    for self in ships.ally():  # type: Ship
        # Dodge a mine or a cannonball

        # Check location of next turn
        next_location = self.next_location()
        # Then check following location after the next with WAIT, PORT and STARBOARD move.
        #   if it touches a mine or a cannonball and damage.
        # If wrong, try PORT and STARBOARD move.
        # If everything wrong, select move which takes the least damage.

        # Fire to an enemy ship
        target_ship = ships.enemy().closest_to(self)  # type: Ship
        if target_ship.distance_to(self) <= distance_to_fire and self.turns_to_fire == 0:
            target_cube = target_ship.next_location()  # type: Cube
            command = "FIRE {0} {1}".format(*(target_cube.offset()))
            print(command)
            self.turns_to_fire = turns_to_fire
        # Get a barrel
        else:
            barrel = barrels.closest_to(self)  # type: Barrel
            if barrel is not None:
                command = "MOVE {0} {1}".format(barrel.x, barrel.y)
                print(command)
            else:
                command = "MOVE {0} {1}".format(target_ship.x, target_ship.y)
                print(command)

    entities_in_history.append(ships + barrels + mines)
