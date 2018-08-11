#!/usr/bin/env python

import time
import pygame

from map import *
from constants import *



#   Pyracy
from camera_tools import *
from sprite_tools import *
from particle_tools import *

class Player(object):

    def __init__(self, pos = [2, 2]):
        self.pos = pos

        idle = SpriteSheet(p('player_idle.png'), (4, 1), 5)

        self.sprite = Sprite(fps = 8)
        self.sprite.add_animation({'Idle': idle})

        self.key_dict = {'up': 273,
            'down': 274,
            'left': 276,
            'right': 275}

        self.last_move = "rest"
        self.juice = 0

    def draw(self, screen):
        self.sprite.draw(screen)

    def update(self, dt):
        self.sprite.update(dt)
        self.update_movement(dt)

    def update_movement(self, dt):

        target_x = self.pos[0] * TILE_WIDTH + TILE_XOFF
        target_y = self.pos[1] * TILE_HEIGHT + TILE_YOFF


        self.sprite.x_pos = target_x
        self.sprite.y_pos = target_y

    def test_movement(self, events, map):

        keydowns = [event.key for event in events]
        for direction in self.key_dict:
            if self.key_dict[direction] in keydowns:
                self.apply_movement(direction, map)

    def apply_movement(self, direction, map):

        if direction == "up":
            new_x, new_y = self.pos[0], self.pos[1] - 1
        elif direction == "down":
            new_x, new_y = self.pos[0], self.pos[1] + 1
        elif direction == "left":
            new_x, new_y = self.pos[0] - 1, self.pos[1]
        elif direction == "right":
            new_x, new_y = self.pos[0] + 1, self.pos[1]
        else:
            new_x, new_y = self.pos[0], self.pos[1]

        if new_x < 0 or new_y < 0 or \
            new_x > MAP_WIDTH - 1 or new_y > MAP_HEIGHT - 1:
            #self.last_move = "rest"
            return 0

        new_cell = map.get_cell(new_x, new_y)
        if "rock" in new_cell.contents:
            return 0

        else:
            self.pos = new_x, new_y
            self.last_move = direction
            return 1


class Game(object):

    def __init__(self):
        pygame.init()

        self.display = pygame.display.set_mode((640, 480))
        self.cam = Camera(self.display)
        self.screen = pygame.Surface((640, 480))

        #   Game stuff
        self.map = Map(16, 12)


        #   SPRITES


        self.main()


    def main(self):
        #self.cam.set_target_zoom(2.0)
        #self.cam.set_target_center((0, 0))

        self.player = Player([2, 2])
        self.player.sprite.start_animation('Idle')

        self.map = Map(MAP_WIDTH, MAP_HEIGHT)

        objects_layer_0 = [self.map]
        objects_layer_1 = []
        objects_layer_2 = [self.player]
        layers = [objects_layer_0, objects_layer_1, objects_layer_2]

        then = time.time()
        time.sleep(0.01)

        self.cam.set_target_zoom(1.5)

        self.map.spawn_rock()

        while True:

            #   PYGAME EVENTS
            pygame.event.pump()
            events = pygame.event.get(pygame.KEYDOWN)

            #   TIME STUFF
            now = time.time()
            dt = now - then
            dt = self.cam.time_step(dt)
            then = now

            #   PLAYER MOVEMENT
            if len(events):
                self.player.test_movement(events, self.map)
                print([i.key for i in events])

            #   DROPPING THINGS
            self.spawn_items()

            self.cam.set_target_center([self.player.sprite.x_pos,
                self.player.sprite.y_pos])


            #   DRAW TO SCREEN
            self.screen.fill((50, 50, 50))

            for layer in layers:
                for item in layer:
                    item.update(dt)
                    item.draw(self.screen)

            self.cam.capture(self.screen)
            pygame.display.flip()

    def spawn_items(self):

        num_milk = self.map.get_count("milk")
        if num_milk < 1:
            self.map.spawn_milk()


def p(path):

    return path

if __name__ == '__main__':
    game = Game()
