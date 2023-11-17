import numpy as np

from config import UNAME, TOKEN
from pyghthouse import Pyghthouse


def image_gen():
    image = np.zeros((14, 28, 3))
    yield image.tolist()
    while True:
        for x in range(14):
            for y in range(28):
                for j in range(3):
                    image[x, y, j] = 255
                    yield image.tolist()
        for y in range(28):
            for x in range(14):
                for j in range(3):
                    image[x, y, j] = 0
                    yield image.tolist()


g = image_gen()

if __name__ == '__main__':
    p = Pyghthouse(UNAME, TOKEN, image_callback=g.__next__, frame_rate=60)
    print("Starting... use CTRL+C to stop.")
    p.start()
