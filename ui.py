#!/usr/bin/env python

import pygame

class Bar(object):

    def __init__(self, max_val, color = [95, 135, 240],
        width = 100, height = 20, start_value = 0, pos = (0, 0)):

        self.max_val = max_val
        self.color = color
        self.width = width
        self.height = height
        self.frame_x_border = 10
        self.frame_y_border = 10
        self.pos = pos

        self.cur_value = start_value
        self.target_value = start_value
        self.i = 0

    def draw(self, surf):

        pos = self.pos

        back_w = self.width + 2*self.frame_x_border
        back_h = self.height + 2 * self.frame_y_border
        back = pygame.Surface((back_w, back_h))
        back.fill((105, 85, 50))


        bar = pygame.Surface((self.width, self.height))
        bar.fill((0, 0, 0))

        surf.blit(back, pos)
        surf.blit(bar, (self.frame_x_border+pos[0], self.frame_y_border+pos[1]))

        if self.cur_value > 0:
            prop_full = 1.0*self.cur_value/self.max_val
            bar_value = pygame.Surface((self.width*prop_full, self.height))
            bar_value.fill(self.color)
            if self.cur_value > 6.5:
                bar_value.fill((205, 70, 95))
            off = 0
            surf.blit(bar_value, (pos[0] + off+ self.frame_x_border,
                pos[1]+self.frame_y_border))

        shadow = pygame.Surface((self.width + 2*self.frame_x_border, self.height/2 + self.frame_y_border))
        shadow.fill((255, 255, 255))
        shadow.set_alpha(60)
        surf.blit(shadow, pos)

    def update(self, dt):

        dv = self.target_value - self.cur_value
        self.i += dv*dt

        d = 15.0
        i = 1
        self.cur_value += d*dv*dt + i*self.i*dt

        self.color[0]
