#!/usr/bin/env python

import time
import pygame

from map import *
from constants import *
from ui import *



#   Pyracy
from camera_tools import *
from sprite_tools import *
from particle_tools import *

class Player(object):

    def __init__(self, map, pos = [2, 2]):
        self.pos = pos
        self.focus_pos = (0, 0)

        idle = SpriteSheet(p('player_idle.png'), (4, 1), 5)

        self.sprite = Sprite(fps = 8)
        self.sprite.add_animation({'Idle': idle})

        self.key_dict = {'up': 273,
            'down': 274,
            'left': 276,
            'right': 275,
            'dash': 32}

        self.last_move = "rest"
        self.juice = 0
        self.max_juice = MAX_JUICE

        self.map = map

    def draw(self, screen):
        self.sprite.draw(screen)

        dash = pygame.Surface((32, 32))
        dash.fill((255, 255, 255))
        dash.set_alpha(100)
        dash_pos = self.dash_pos()
        x = dash_pos[0] * TILE_WIDTH + TILE_XOFF
        y = dash_pos[1] * TILE_HEIGHT + TILE_YOFF

        ctdn = 0.8  #   "Centeredness" on player over shadow
        actdn = 1 - ctdn
        self.focus_pos = [actdn*x+ctdn*self.sprite.x_pos,
                        actdn*y+ctdn*self.sprite.y_pos]

        screen.blit(dash, (x, y))

    def update(self, dt):
        self.sprite.update(dt)
        self.update_movement(dt)

    def update_movement(self, dt):

        target_x = self.pos[0] * TILE_WIDTH + TILE_XOFF
        target_y = self.pos[1] * TILE_HEIGHT + TILE_YOFF


        self.sprite.x_pos = target_x
        self.sprite.y_pos = target_y

    def do_dash(self):
        x, y = self.dash_pos(dashing=True)
        self.juice = 0
        return x, y

    def dash_pos(self, dashing=False):

        dash_cell = self.dash_pos_recurse(self.pos, self.juice, dashing=dashing)
        return dash_cell

    def dash_pos_recurse(self, pos, dist, dashing=False):

        if pos[0] < 0 or pos[1] < 0 or \
            pos[0] > MAP_WIDTH - 1 or pos[1] > MAP_HEIGHT - 1:
            return 0

        cur_cell = self.map.get_cell(pos[0], pos[1])
        if dist == 0:
            if "rock" in cur_cell.contents:
                return 0
            return pos

        if dashing:
            if "rock" in cur_cell.contents:
                cur_cell.contents.remove("rock")
                print("REMOVE ROCK")

        if self.last_move == "up":
            new_x, new_y = pos[0], pos[1] - 1
        elif self.last_move == "down":
            new_x, new_y = pos[0], pos[1] + 1
        elif self.last_move == "left":
            new_x, new_y = pos[0] - 1, pos[1]
        elif self.last_move == "right":
            new_x, new_y = pos[0] + 1, pos[1]
        else:
            return pos

        ans = self.dash_pos_recurse((new_x, new_y), dist - 1, dashing=dashing)
        if ans != 0:
            return ans
        else:
            cur_cell = self.map.get_cell(pos[0], pos[1])
            if "rock" not in cur_cell.contents:
                return pos
            return 0

    def test_pickup(self, map):
        cur_cell = map.get_cell(self.pos[0], self.pos[1])
        if "milk" in cur_cell.contents:
            cur_cell.contents.remove("milk")
            self.pickup_milk()

    def pickup_milk(self):
        self.juice = min(self.juice + 1, self.max_juice)

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
        elif direction == "dash":
            new_x, new_y = self.do_dash()
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
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)

        #   Interface
        self.juice_bar = Bar(MAX_JUICE, start_value = 0, pos = JUICE_BAR_POS)

        #   SPRITES


        self.main()


    def main(self):
        #self.cam.set_target_zoom(2.0)
        #self.cam.set_target_center((0, 0))

        self.player = Player(self.map, [2, 2])
        self.player.sprite.start_animation('Idle')

        objects_layer_0 = [self.map]
        objects_layer_1 = []
        objects_layer_2 = [self.player]
        ui = [self.juice_bar]
        layers = [objects_layer_0,
            objects_layer_1,
            objects_layer_2]

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

            #   PLAYER MOVEMENT/UPDATE
            if len(events):
                self.player.test_movement(events, self.map)
                print([i.key for i in events])
            self.player.test_pickup(self.map)
            self.juice_bar.cur_value = self.player.juice

            #   DROPPING THINGS
            self.spawn_items()


            self.cam.set_pan_pid(3, 0.1, -0.3)
            self.cam.set_target_center(self.player.focus_pos)
            self.cam.set_target_zoom(1.5 - 0.01*self.player.juice)


            #   DRAW TO SCREEN
            self.screen.fill((50, 50, 50))

            for layer in layers:
                for item in layer:
                    item.update(dt)
                    item.draw(self.screen)

            #       FINAL BLIT FOR NORMAL THINGS
            self.cam.capture(self.screen)

            #       UI
            for item in ui:
                item.update(dt)
                item.draw(self.display)

            pygame.display.flip()

    def spawn_items(self):

        num_milk = self.map.get_count("milk")
        if num_milk < 1:
            self.map.spawn_milk()


def p(path):

    return path

if __name__ == '__main__':
    game = Game()
