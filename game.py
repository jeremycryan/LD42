#!/usr/bin/env python

import time
import pygame

from map import *
from constants import *
from ui import *
from math import sin
from copy import deepcopy
import sys
import os

#   Pyracy
from camera_tools import Camera
from sprite_tools import *
from particle_tools import *

class Player(object):

    def __init__(self, map, pos = [1, 1], cam = None):
        self.pos = pos

        self.focus_pos = (0, 0)
        self.cam = cam
        self.score = 0
        self.consecutive_rocks = 0
        self.rock_break_sound = pygame.mixer.Sound(p("rock_break.wav"))
        self.rock_break_sound.set_volume(0.2)
        self.dash_sound = pygame.mixer.Sound(p("dash_sound.wav"))
        self.dash_sound.set_volume(0.08)
        self.reset_sound = pygame.mixer.Sound(p("reset.wav"))
        self.reset_sound.set_volume(0.25)
        #while True: pass
        self.milk_sound = pygame.mixer.Sound(p("milk_pickup.wav"))
        self.milk_sound.set_volume(0.07)

        self.zoom_effect_amt = 1.5

        idle_right = SpriteSheet(p('ram_idle_right.png'), (8, 1), 8)
        idle_left = SpriteSheet(p('ram_idle_right.png'), (8, 1), 8)
        idle_left.reverse(1, 0)
        dash_right = SpriteSheet(p('ram_dash_right.png'), (7, 1), 7)
        dash_left = SpriteSheet(p('ram_dash_right.png'), (7, 1), 7)
        dash_left.reverse(1, 0)

        self.sprite = Sprite(fps = 10)
        self.sprite.x_pos = TILE_XOFF + pos[0]*TILE_WIDTH
        self.sprite.y_pos = TILE_YOFF + pos[1]*TILE_HEIGHT
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
        if self.juice > 3:
            self.cam.set_speed(0.2)
            self.cam.zoom_to(self.zoom_effect_amt-0.1)
            self.cam.set_target_zoom(self.zoom_effect_amt)
            self.cam.set_zoom_pid(20, 0.0, 0)

            #self.trail.duration = 0.1
            #self.trail.time = 0
        self.cam.shake(6+self.juice*2)

    def draw(self, screen):

        dash_pos = self.dash_pos()
        xdif = dash_pos[0] - self.pos[0]
        ydif = dash_pos[1] - self.pos[1]

        dash = pygame.Surface((32*abs(xdif)+64, 32*abs(ydif)+64))
        dash.fill((255, 255, 255))
        dash.set_alpha(75)

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

        rat=15
        if self.sprite.active_animation in ["DashLeft","DashRight","DashUp","DashDown"]:
            if self.juice > 2:
                rat = 20
            else:
                rat = 50
        if dt > 0.025:
            rat *= 0.6
        if dt > 0.05:
            rat *= 0.8
        self.sprite.x_pos += xdif*rat*dt
        self.sprite.y_pos += ydif*rat*dt

    def do_dash(self):
        x, y = self.dash_pos(dashing=True)

        if self.juice > 0:
            self.dash_sound.play()
        if self.consecutive_rocks > 0:
            self.rock_break_sound.play()
            self.consecutive_rocks = 0

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
                        self.consecutive_rocks += 100
                        self.score += self.consecutive_rocks


        if self.last_move == "up":
            new_x, new_y = pos[0], pos[1] - 1
            if dashing and self.sprite.active_animation == "IdleRight":
                self.sprite.start_animation("DashRight", "IdleRight")
                self.dash_effect()
            elif dashing:
                self.sprite.start_animation("DashLeft", "IdleLeft")
                self.dash_effect()
        elif self.last_move == "down":
            new_x, new_y = pos[0], pos[1] + 1
            if dashing and self.sprite.active_animation == "IdleRight":
                self.sprite.start_animation("DashRight", "IdleRight")
                self.dash_effect()
            elif dashing:
                self.sprite.start_animation("DashLeft", "IdleLeft")
                self.dash_effect()
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
                            self.rock_effect(spos)
                            self.consecutive_rocks += 100
                            self.score += self.consecutive_rocks

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
                map.remove_milk_at_cell(cur_cell)
                self.pickup_milk()

    def pickup_milk(self):
        self.milk_sound.play()
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
            if ("rock1" in new_cell.contents or "rock2" in new_cell.contents \
                or "rock3" in new_cell.contents) and direction != "dash":
                self.last_move = direction
                return 0

        else:
            self.pos = new_x, new_y
            self.last_move = direction
            return 1


class Game(object):

    def __init__(self):

        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.mus = pygame.mixer.music.load(p("LD42.wav"))
        self.tmus = pygame.mixer.Sound(p("LD42_Title.wav"))
        #pygame.mixer.init()

        self.display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        pygame.display.set_caption("Rampart")
        self.cam = Camera(self.display)
        self.cam.pos = TILE_XOFF + 32*8, TILE_YOFF - 128
        self.cam.set_pan_pid(1, 0, 0)
        self.screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

        #   Game stuff
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)
        self.sky = pygame.image.load(p("backdrop.png"))
        self.title = pygame.image.load("rampart.png")
        title_spritesheet = SpriteSheet("rampart.png", (1, 1), 1)
        self.title_sprite = Sprite()
        self.title_sprite.add_animation({"idle": title_spritesheet})
        self.title_sprite.start_animation("idle")

        self.high_score = 0


        pygame.font.init()
        self.coin_font = pygame.font.SysFont('default', 30)
        self.hs_font = pygame.font.SysFont('default', 50)


        #   Interface
        self.juice_bar = Bar(MAX_JUICE, start_value = 0, width = 140, pos = JUICE_BAR_POS)

        #   SPRITES

        while True:
            self.main()


    def main(self):
        #self.cam.set_target_zoom(2.0)
        #self.cam.set_target_center((0, 0))

        self.map = Map(MAP_WIDTH, MAP_HEIGHT)

        self.player = Player(self.map, [7, 5], cam=self.cam)
        self.player.sprite.start_animation('IdleRight')
        self.since_rock_spawn = 0

        objects_layer_0 = [self.map]
        objects_layer_1 = []
        objects_layer_2 = [self.title_sprite]
        ui = [self.juice_bar]
        layers = [objects_layer_0,
            objects_layer_1,
            objects_layer_2]

        then = time.time()
        time.sleep(0.01)

        self.cam.zoom_to(1.0)

###############################################################
#################### TITLE EFFECT #############################
###############################################################
        self.tmus.set_volume(0.25)
        self.tmus.play(loops=-1)
        while True:
            #   PYGAME EVENTS
            pygame.event.pump()
            events = pygame.event.get(pygame.KEYDOWN)
            quit = pygame.event.get(pygame.QUIT)
            if len(quit):
                pygame.quit()
                sys.exit()
            pygame.event.clear()
            if len(events):
                break

            #   TIME STUFF
            now = time.time()
            dt = now - then
            dt = self.cam.time_step(dt)
            then = now

            self.cam.set_target_center((TILE_XOFF + 32*8,
                TILE_YOFF - 128 + 12*sin(time.time()*2)))
            self.title_sprite.x_pos = TILE_XOFF + 8*32 - self.title.get_width()/2
            self.title_sprite.y_pos = TILE_YOFF -280

            #   DRAW TO SCREEN
            self.screen.fill((0, 0, 0))
            self.display.fill((0, 0, 0))
            self.display.blit(self.sky, (-self.cam.pos[0]*0.5, -self.cam.pos[1]*0.2+40))
            self.screen.set_colorkey((0, 0, 0))


            for layer in layers:
                for item in layer:
                    item.update(dt)
                    item.draw(self.screen)

            hs_text = self.hs_font.render("HIGH SCORE: %s" % self.high_score, 50, (1, 0, 0))
            hs_text = pygame.transform.scale(hs_text, (120, 16))
            self.screen.blit(hs_text, (TILE_XOFF + 8*32 - hs_text.get_width()/2,
                TILE_YOFF - 170))


            text = self.coin_font.render("PRESS ANY KEY TO START", 10,
                (0, 0, 0))
            text = pygame.transform.scale(text, (240, 18))
            if time.time() % 1 < 0.5:
                self.display.blit(text, (DISPLAY_WIDTH/2 - text.get_width()/2,
                    16))




            #       FINAL BLIT FOR NORMAL THINGS
            self.cam.capture(self.screen)

            pygame.display.flip()

        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(loops=999)
        objects_layer_2.append(self.player)
        layers = [objects_layer_0,
            objects_layer_1,
            objects_layer_2]
        self.spawn_milk()
        title_speed = -400
        self.tmus.fadeout(500)

##############################################################
#################### MAIN LOOP ###############################
##############################################################
        while True:

            self.title_sprite.y_pos -= title_speed *dt
            title_speed += 3000*dt
            if self.title_sprite.y_pos < 0 and self.title_sprite in layers[2]:
                layers[2].remove(self.title_sprite)

            #   PYGAME EVENTS
            pygame.event.pump()
            events = pygame.event.get(pygame.KEYDOWN)
            quit = pygame.event.get(pygame.QUIT)
            if len(quit):
                pygame.quit()
                sys.exit()
            pygame.event.clear()

            #   TIME STUFF
            now = time.time()
            dt = now - then
            print("FPS: %s" % (1/dt))
            dt = self.cam.time_step(dt)
            then = now



            #   PLAYER MOVEMENT/UPDATE
            if len(events):
                turnover = self.player.test_movement(events, self.map)
                self.turnover()
                if 114 in [e.key for e in events]:
                    self.player.reset_sound.play()
                    self.high_score = max(self.high_score, self.player.score)
                    pygame.mixer.music.fadeout(1500)
                    break

            self.player.test_pickup(self.map)
            self.juice_bar.target_value = self.player.juice



            #self.cam.set_pan_pid(3, 0.1, -0.3)
            self.cam.set_target_center((self.player.focus_pos[0] + 32,
                self.player.focus_pos[1] + 32))
            #self.cam.set_target_zoom(1.0 - 0.01*self.player.juice)


            #   DRAW TO SCREEN
            self.screen.fill((0, 0, 0))
            self.display.fill((0, 0, 0))
            self.display.blit(self.sky, (-self.cam.pos[0]*0.5, -self.cam.pos[1]*0.2+40))
            self.screen.set_colorkey((0, 0, 0))

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

            #   Coin amt
            ui_back = pygame.Surface((INT_WID, INT_HEI))
            ui_back.set_alpha(100)
            self.display.blit(ui_back, (INT_BORD,
                DISPLAY_HEIGHT - INT_HEI - INT_BORD))
            string = str(self.player.score)
            # digits = 6
            # if len(string) < digits:
            #     plus = "0"*(digits - len(string))
            #     string = plus+string
            text = self.coin_font.render(string, False, (255, 255, 255))
            text.set_alpha(180)
            text_pos = (INT_BORD + INT_WID - text.get_width() - 8,
                DISPLAY_HEIGHT - INT_BORD - INT_HEI + 8)
            self.display.blit(text, text_pos)

            pygame.display.flip()

    def spawn_milk(self):

        num_milk = self.map.get_count("milk")
        while num_milk < 3:
            self.map.spawn_milk()
            num_milk = self.map.get_count("milk")

    def turnover(self):

        self.cam.set_pan_pid(3, 0.1, -0.3)
        self.spawn_milk()

        self.since_rock_spawn += 1
        if self.since_rock_spawn >=4:
            dont = self.player.quarter_positions(self.player.pos)
            try:
                new_rock_x, new_rock_y = self.map.spawn_rock(dont=dont)
            except:
                return
            self.rock_spawn_effect(new_rock_x, new_rock_y)
            self.since_rock_spawn = 0

    def rock_spawn_effect(self, x, y):
        pass


def p(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

if __name__ == '__main__':
    game = Game()
