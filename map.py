##!/usr/bin/env python

import pygame
import random
from game import p
from sprite_tools import *
from constants import *

class Map(object):

    def __init__(self, x_size, y_size):

        self.cells = []

        for y in range(y_size):

            a = [Cell((x, y), ["tile"]) for x in range(x_size)]
            self.cells.append(a)

        print(self)

        self.blank_tile = pygame.image.load(p('map_blank.png'))
        self.gone_tile = pygame.image.load(p('map_gone.png'))
        self.rock = pygame.image.load(p('rock.png'))
        self.milk = pygame.image.load(p('milk.png'))
        self.img_dict = {"tile": self.blank_tile,
            "rock": self.rock, "milk": self.milk}

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
        pass

    def draw(self, screen):

        for cell in self.get_all_cells():
            for item in cell.contents:
                img = self.img_dict[item]
                x = cell.x * TILE_WIDTH + TILE_XOFF
                y = cell.y * TILE_HEIGHT + TILE_YOFF
                screen.blit(img, (x, y))

    def spawn_rock(self):
        cells = self.get_all_empty_cells()
        if len(cells):
            to_spawn = random.choice(cells)
            to_spawn.add("rock")

    def spawn_milk(self):
        cells = self.get_all_empty_cells()
        if len(cells):
            to_spawn = random.choice(cells)
            to_spawn.add("milk")

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
