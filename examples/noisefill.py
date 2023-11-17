import numpy as np
from random import random

from config import UNAME, TOKEN
from pyghthouse import Pyghthouse


def image_gen():
    image = np.zeros((14, 28, 3))
    yield image.tolist()
    while True:
        for y in range(28):
            for j in range(3):
                image[0, y, j] = int(random() * 255)
            yield image.tolist()
        image = np.roll(image, 1, 0)
        image *= 0.85
        yield image.tolist()


g = image_gen()

if __name__ == '__main__':
    p = Pyghthouse(UNAME, TOKEN, image_callback=g.__next__, frame_rate=60)
    print("Starting... use CTRL+C to stop.")
    p.start()
