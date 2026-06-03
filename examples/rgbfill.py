import numpy as np

from config import UNAME, TOKEN
from pyghthouse import Pyghthouse


def image_gen():
    image = np.zeros((14, 28, 3))
    yield image
    while True:
        for y in range(14):
            for x in range(28):
                for j in range(3):
                    image[y, x, j] = 255
                    yield image
        for x in range(28):
            for y in range(14):
                for j in range(3):
                    image[y, x, j] = 0
                    yield image


g = image_gen()

if __name__ == '__main__':
    p = Pyghthouse(UNAME, TOKEN, image_callback=g.__next__, frame_rate=60)
    print("Starting... use CTRL+C to stop.")
    p.start()
    p.keep_running()