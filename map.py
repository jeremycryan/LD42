##!/usr/bin/env python

import pygame
import random
#from game import p
from sprite_tools import *
from constants import *
from copy import deepcopy

class Map(object):

    def __init__(self, x_size, y_size):

        self.cells = []

        for y in range(y_size):

            a = [Cell((x, y), ["tile"]) for x in range(x_size)]
            self.cells.append(a)


        self.blank_tile = pygame.image.load(p('map_blank.png'))
        self.blank_tile = pygame.transform.scale(self.blank_tile,
            (TILE_WIDTH, TILE_HEIGHT))
        self.gone_tile = pygame.image.load(p('map_gone.png'))
        self.rock1 = pygame.image.load(p('rock1.png'))
        self.rock2 = pygame.image.load(p('rock2.png'))
        self.rock3 = pygame.image.load(p('rock3.png'))
        milk_spawn = SpriteSheet("milk_spawn.png", (12, 1), 12)
        milk_static = SpriteSheet("milk.png", (1, 1), 1)
        self.milk_sprite = Sprite(fps=8)
        self.milk_sprite.add_animation({"Spawn": milk_spawn,
                                        "Static": milk_static})
        self.milks = []

        self.img_dict = {"tile": self.blank_tile,
            "rock1": self.rock1, "milk": None, "rock2": self.rock2,
            "rock3": self.rock3}
        self.bkgnd = pygame.image.load(p("arena.png"))
        self.bkgnd.set_colorkey((0, 0, 0))


    def get_cell(self, x, y):
        return self.cells[y][x]

    def get_count(self, item):
        n = 0
        for cell in self.get_all_cells():
            n += cell.contents.count(item)
        return n

    def get_all_cells(self):

        cells = []
        for row in self.cells:
            for item in row:
                cells.append(item)

        return cells

    def get_all_empty_cells(self):
        empty_cells = []
        for cell in self.get_all_cells():
            if cell.is_empty():
                empty_cells.append(cell)
        return empty_cells

    def update(self, dt):
        for milk in self.milks:
            milk.update(dt)
        pass

    def draw(self, screen):
        screen.blit(self.bkgnd, (0, 200))
        for cell in self.get_all_cells():
            for item in cell.contents:
                if item == "milk":
                    continue
                img = self.img_dict[item]
                x = cell.x * TILE_WIDTH + TILE_XOFF
                y = cell.y * TILE_HEIGHT + TILE_YOFF
                if item in ["rock1", "rock2", "rock3"]:
                    y += ROCK_Y_OFFSET
                if item == "tile":
                    continue
                screen.blit(img, (x, y))
        for milk in self.milks:
            milk.draw(screen)

    def remove_milk_at_cell(self, cell):
        for milk in self.milks:
            if (milk.x_pos-TILE_XOFF)/TILE_WIDTH == cell.x:
                if (milk.y_pos+32-TILE_YOFF)/TILE_HEIGHT == cell.y:
                    self.milks.remove(milk)
                    return

    def spawn_rock(self, dont = -1):
        cells = self.get_all_empty_cells()
        if len(cells) < 6:
            return None
        if len(cells):
            to_spawn = random.choice(cells)
            while (to_spawn.x, to_spawn.y) in dont:
                to_spawn = random.choice(cells)
            to_spawn.add(random.choice(ROCKS))
        return to_spawn.x, to_spawn.y

    def spawn_milk(self):
        cells = self.get_all_empty_cells()
        if len(cells):
            to_spawn = random.choice(cells)
            to_spawn.add("milk")

        milk_spawn = SpriteSheet("milk_spawn.png", (12, 1), 12)
        milk_static = SpriteSheet("milk.png", (1, 1), 1)
        milk = Sprite(fps=8)
        milk.add_animation({"Spawn": milk_spawn,
                                        "Static": milk_static})
        #milk = deepcopy(self.milk_sprite)
        milk.start_animation("Spawn", "Static")
        milk.x_pos = to_spawn.x*TILE_WIDTH + TILE_XOFF
        milk.y_pos = to_spawn.y*TILE_WIDTH + TILE_YOFF - 32
        self.milks.append(milk)

    def __repr__(self):
        s = ""
        for i in self.cells:
            s += str(i) + "\n"
        return s

class Cell(object):

    def __init__(self, pos, contents = "tile"):
        self.contents = contents
        self.x = pos[0]
        self.y = pos[1]

    def __repr__(self):
        return str(self.contents)

    def add(self, items):

        self.contents.append(items)

    def remove(self, x, y, item):
        """ returns true if removed successfully"""

        if item == "all":
            if self.contents == []:
                return 0
            self.contents = []
            return 1

        else:
            if item in self.contents:
                while item in self.contents:
                    self.contents.remove(item)
                return 1
            else:
                return 0

    def is_empty(self):
        if len(self.contents) > 1:
            return False
        return True

def p(path):

    return path


if __name__ == '__main__':
    pygame.init()
    a = Map(6, 4)
    print(a)
    print(a.get_all_cells())
    b = pygame.display.set_mode((640, 480))
    a.draw(b)
    pygame.display.flip()
    while True:
        pass
