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

    def __init__(self, map, pos = [2, 2], cam = None):
        self.pos = pos
        self.focus_pos = (0, 0)
        self.cam = cam

        self.zoom_effect_amt = 1.5

        idle_right = SpriteSheet(p('ram_idle_right.png'), (8, 1), 8)
        idle_left = SpriteSheet(p('ram_idle_right.png'), (8, 1), 8)
        idle_left.reverse(1, 0)
        dash_right = SpriteSheet(p('ram_dash_right.png'), (7, 1), 7)
        dash_left = SpriteSheet(p('ram_dash_right.png'), (7, 1), 7)
        dash_left.reverse(1, 0)

        self.sprite = Sprite(fps = 10)
        self.sprite.add_animation({'IdleRight': idle_right,
                                    'IdleLeft': idle_left,
                                    'DashRight': dash_right,
                                    'DashLeft': dash_left})

        self.key_dict = {'up': 273,
            'down': 274,
            'left': 276,
            'right': 275,
            'dash': 32}

        self.last_move = "rest"
        self.juice = 0
        self.max_juice = MAX_JUICE

        self.map = map

        self.rock_bit_1 = Particle(path='square', width = 5, height = 5, color = (45, 55, 20))
        self.rock_bit_2 = Particle(path= 'square', width = 7, height = 7, color = (145, 125, 60))
        self.rock_bit_3 = Particle(path = 'square', width = 4, height = 4, color = (110, 110, 106))
        rocks = [self.rock_bit_1, self.rock_bit_2, self.rock_bit_3]
        self.rock_burst = ParticleEffect(pos = (300, 300), width = 32, height = 32)
        for i, item in enumerate(rocks):
            item.apply_behavior(LinearMotionEffect(direction = -0.25*i, init_speed = 200, accel = 50))
            item.apply_behavior(OpacityEffect(decay = 5))
            self.rock_burst.add_particle_type(item, 0.006)

        self.spark = Particle(path = 'square', width = 5, height = 5, color = (255, 255, 255))
        self.trail = ParticleEffect(pos = (0, 0, 0), width = 32, height = 32)
        self.spark.apply_behavior(OpacityEffect(decay = 1.5))
        self.trail.add_particle_type(self.spark, 0.001)
        self.trail.duration = 0.0001
        #self.rock_effect((TILE_XOFF, TILE_YOFF))
        self.particles = [self.trail]

        self.player_surf = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

    def rock_effect(self, pos):
        p = self.rock_burst.copy()
        p.duration = 0.1
        p.pos = pos
        self.particles.append(p)

    def dash_effect(self):
        #return
        if self.juice > 2:
            self.cam.set_speed(0.2)
            self.cam.zoom_to(self.zoom_effect_amt-0.1)
            self.cam.set_target_zoom(self.zoom_effect_amt)
            self.cam.set_zoom_pid(20, 0.0, 0)

            #self.trail.duration = 0.1
            #self.trail.time = 0

    def draw(self, screen):

        dash_pos = self.dash_pos()
        xdif = dash_pos[0] - self.pos[0]
        ydif = dash_pos[1] - self.pos[1]

        dash = pygame.Surface((32*abs(xdif)+64, 32*abs(ydif)+64))
        dash.fill((255, 255, 255))
        dash.set_alpha(100)

        x = dash_pos[0] * TILE_WIDTH + TILE_XOFF
        y = dash_pos[1] * TILE_HEIGHT + TILE_YOFF

        ctdn = 0.8  #   "Centeredness" on player over shadow
        actdn = 1 - ctdn
        self.focus_pos = [actdn*x+ctdn*self.sprite.x_pos,
                        actdn*y+ctdn*(self.sprite.y_pos - PLAYER_Y_OFFSET)]

        if xdif > 0:
            x = self.sprite.target_x_pos
        if ydif > 0:
            y = self.sprite.target_y_pos - PLAYER_Y_OFFSET
        screen.blit(dash, (x, y))
        self.sprite.draw(screen)

        for p in self.particles:
            p.draw(screen)

    def quarter_positions(self, pos):
        xoff = [0, 1]
        yoff = [0, 1]
        poses = []
        for x in xoff:
            for y in yoff:
                poses.append((pos[0]+x, pos[1]+y))
        return poses

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.sprite.update(dt)
        self.update_movement(dt)

        if self.cam.zoom > self.zoom_effect_amt - 0.000001:
            self.cam.set_target_zoom(1.0)
            self.cam.set_zoom_pid(3, 1, 0.2)
            self.cam.set_speed(1.0)

        self.trail.pos = (self.sprite.x_pos + TILE_WIDTH,
            self.sprite.y_pos - PLAYER_Y_OFFSET + TILE_HEIGHT)

    def update_movement(self, dt):

        target_x = self.pos[0] * TILE_WIDTH + TILE_XOFF
        target_y = self.pos[1] * TILE_HEIGHT + TILE_YOFF


        self.sprite.target_x_pos = target_x
        self.sprite.target_y_pos = target_y + PLAYER_Y_OFFSET

        xdif = self.sprite.target_x_pos - self.sprite.x_pos
        ydif = self.sprite.target_y_pos - self.sprite.y_pos

        rat=20
        if self.sprite.active_animation in ["DashLeft","DashRight","DashUp","DashDown"]:
            if self.juice > 2:
                rat = 20
            else:
                rat = 50
        self.sprite.x_pos += xdif*rat*dt
        self.sprite.y_pos += ydif*rat*dt

    def do_dash(self):
        x, y = self.dash_pos(dashing=True)

        # if self.juice >= 5:
        #     for xoff in [-1, 0, 1]:
        #         for yoff in [-1, 0, 1]:
        #             check_pos = self.pos[0] + xoff, self.pos[1] + yoff
        #             self.dash_pos_recurse(check_pos, self.juice, dashing=True)


        self.juice = 0
        return x, y

    def dash_pos(self, dashing=False):

        dash_cell = self.dash_pos_recurse(self.pos, self.juice, dashing=dashing)
        return dash_cell

    def dash_pos_recurse(self, pos, dist, dashing=False):

        for qpos in self.quarter_positions(pos):
            if qpos[0] < 0 or qpos[1] < 0 or \
                qpos[0] > MAP_WIDTH - 1 or qpos[1] > MAP_HEIGHT - 1:
                return 0

        if dist == 0:
            return pos

        for qpos in self.quarter_positions((pos[0], pos[1])):
            cur_cell = self.map.get_cell(qpos[0], qpos[1])
            if dashing:
                for item in BREAKABLE:
                    if item in cur_cell.contents:
                        cur_cell.contents.remove(item)


        if self.last_move == "up":
            new_x, new_y = pos[0], pos[1] - 1
        elif self.last_move == "down":
            new_x, new_y = pos[0], pos[1] + 1
        elif self.last_move == "left":
            new_x, new_y = pos[0] - 1, pos[1]
            if dashing:
                self.sprite.start_animation("DashLeft", "IdleLeft")
                self.dash_effect()
        elif self.last_move == "right":
            new_x, new_y = pos[0] + 1, pos[1]
            if dashing:
                self.sprite.start_animation("DashRight", "IdleRight")
                self.dash_effect()
        else:
            return pos

        for qpos in self.quarter_positions((new_x, new_y)):
            if 0 <= qpos[0] and qpos[0] <= MAP_WIDTH-1 and \
                0 <= qpos[1] and qpos[1] <= MAP_HEIGHT-1:
                cur_cell = self.map.get_cell(qpos[0], qpos[1])
                if dashing:
                    for item in BREAKABLE:
                        if item in cur_cell.contents:
                            cur_cell.contents.remove(item)
                            spos = (qpos[0] * TILE_WIDTH + TILE_XOFF,
                                qpos[1] * TILE_HEIGHT + TILE_YOFF)
                            print(spos)
                            self.rock_effect(spos)

        ans = self.dash_pos_recurse((new_x, new_y), dist - 1, dashing=dashing)
        if ans != 0:
            return ans
        else:
            return pos

    def test_pickup(self, map):
        for qpos in self.quarter_positions(self.pos):
            cur_cell = map.get_cell(qpos[0], qpos[1])
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
                return True
        return False

    def apply_movement(self, direction, map):


        if direction == "up":
            new_x, new_y = self.pos[0], self.pos[1] - 1
        elif direction == "down":
            new_x, new_y = self.pos[0], self.pos[1] + 1
        elif direction == "left":
            new_x, new_y = self.pos[0] - 1, self.pos[1]
            self.sprite.start_animation('IdleLeft')
        elif direction == "right":
            new_x, new_y = self.pos[0] + 1, self.pos[1]
            self.sprite.start_animation('IdleRight')
        elif direction == "dash":
            new_x, new_y = self.do_dash()
        else:
            new_x, new_y = self.pos[0], self.pos[1]

        for qpos in self.quarter_positions((new_x, new_y)):

            if qpos[0] < 0 or qpos[1] < 0 or \
                qpos[0] > MAP_WIDTH - 1 or qpos[1]> MAP_HEIGHT - 1:
                self.last_move = direction
                return 0

            new_cell = map.get_cell(qpos[0], qpos[1])
            if "rock" in new_cell.contents and direction != "dash":
                self.last_move = direction
                return 0

        else:
            self.pos = new_x, new_y
            self.last_move = direction
            return 1


class Game(object):

    def __init__(self):
        pygame.init()

        self.display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.cam = Camera(self.display)
        self.screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

        #   Game stuff
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)

        #   Interface
        self.juice_bar = Bar(MAX_JUICE, start_value = 0, pos = JUICE_BAR_POS)

        #   SPRITES


        self.main()


    def main(self):
        #self.cam.set_target_zoom(2.0)
        #self.cam.set_target_center((0, 0))

        self.player = Player(self.map, [2, 2], cam=self.cam)
        self.player.sprite.start_animation('IdleRight')
        self.since_rock_spawn = 0
        self.spawn_milk()

        objects_layer_0 = [self.map]
        objects_layer_1 = []
        objects_layer_2 = [self.player]
        ui = [self.juice_bar]
        layers = [objects_layer_0,
            objects_layer_1,
            objects_layer_2]

        then = time.time()
        time.sleep(0.01)

        self.cam.zoom_to(1.0)

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
                turnover = self.player.test_movement(events, self.map)
                self.turnover()
                print([i.key for i in events])
            self.player.test_pickup(self.map)
            self.juice_bar.cur_value = self.player.juice



            self.cam.set_pan_pid(3, 0.1, -0.3)
            self.cam.set_target_center(self.player.focus_pos)
            #self.cam.set_target_zoom(1.0 - 0.01*self.player.juice)


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

    def spawn_milk(self):

        num_milk = self.map.get_count("milk")
        while num_milk < 3:
            self.map.spawn_milk()
            num_milk = self.map.get_count("milk")

    def turnover(self):

        self.spawn_milk()

        self.since_rock_spawn += 1
        if self.since_rock_spawn >=3:
            dont = self.player.quarter_positions(self.player.pos)
            self.map.spawn_rock(dont=dont)
            self.since_rock_spawn = 0


def p(path):

    return path

if __name__ == '__main__':
    game = Game()
