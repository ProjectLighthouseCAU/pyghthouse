from random import random

import numpy as np
from PIL import Image, ImageDraw

from pyghthouse.utils import from_hsv
from pyghthouse import Pyghthouse

from config import UNAME, TOKEN

SPEED_FACTOR = 0.02
COLOR_SPEED = 0.01


class BouncyPoint:

    def __init__(self):
        self.x = random()
        self.y = random()
        self.vx = SPEED_FACTOR * (random() + 0.5)
        self.vy = SPEED_FACTOR * (random() + 0.5)

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.x < 0:
            self.vx *= -1
            self.x *= -1
        elif self.x > 1:
            self.vx *= -1
            self.x = 2 - self.x
        if self.y < 0:
            self.vy *= -1
            self.y *= -1
        elif self.y > 1:
            self.vy *= -1
            self.y = 2 - self.y


class ImageMaker:

    def __init__(self):
        self.p1 = BouncyPoint()
        self.p2 = BouncyPoint()
        self.img = Image.new('RGB', (280, 140))
        self.draw = ImageDraw.Draw(self.img)
        self.hue = 0.0

    def callback(self):
        self.p1.update()
        self.p2.update()
        self.hue += COLOR_SPEED
        self.draw.line([(self.p1.x * 280, self.p1.y * 140), (self.p2.x * 280, self.p2.y * 140)], width=10,
                       fill=tuple(from_hsv(self.hue, 1, 1)))
        output = self.img.copy()
        output.thumbnail((28, 14))
        return np.asarray(output).tolist()


if __name__ == '__main__':
    i = ImageMaker()
    p = Pyghthouse(UNAME, TOKEN, image_callback=i.callback, frame_rate=60)
    p.start()
