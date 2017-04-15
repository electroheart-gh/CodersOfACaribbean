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
        # ToDo: refine for hex map
        return (entity.x - self.x) ** 2 + (entity.y - self.y) ** 2


class Ship(Entity):
    def __init__(self, entity_id, x, y, orientation, speed, rum, owner):
        super().__init__(entity_id, x, y)
        self.orientation = int(orientation)
        self.speed = int(speed)
        self.rum = int(rum)
        self.owner = int(owner)


class Ships(list):
    def ally(self):
        return [e for e in self if e.owner == 1]  # type: Ships


class Barrel(Entity):
    def __init__(self, entity_id, x, y, rum)
        super().__init__(entity_id, x, y)
        self.rum = int(rum)


class Barrels(list):
    pass


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

#######################################
# Parameters to be adjusted
#######################################

#######################################
# Game Loop
#######################################
while True:
    # Initialize for turn
    ships = Ships()
    barrels = Barrels()

    # Input for turn
    my_ship_count = int(input())  # the number of remaining ships
    entity_count = int(input())  # the number of entities (e.g. ships, mines or cannonballs)
    for i in range(entity_count):
        entity_id, entity_type, x, y, arg_1, arg_2, arg_3, arg_4 = DT.input().split()
        if entity_type == "SHIP":
            ships.append(Ship(entity_id, x, y, arg_1, arg_2, arg_3, arg_4))
        if entity_type == "BARREL":
            barrels.append(Barrel(entity_id, x, y, arg_1))

    # Command for my ships
    for i in range(my_ship_count):
        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr)

        # Any valid action, such as "WAIT" or "MOVE x y"

        print("MOVE 11 10")
