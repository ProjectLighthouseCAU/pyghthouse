from pyghthouse import Pyghthouse
from pyghthouse.utils import from_hsv
from config import UNAME, TOKEN
import numpy as np


def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = (np.arctan2(y, x) / np.pi) / 2
    return rho, phi


def circle_generator():
    image = np.zeros((14, 28, 3))
    while True:
        for i in range(180):
            for x in range(28):
                for y in range(14):
                    rho, phi = cart2pol(x / 28 - 0.5, y / 14 - 0.5)
                    image[y, x, :] = from_hsv((phi + i / 180) % 1.0, 1-rho, i / 90 if i < 91 else 1 - (i - 90) / 90)
            yield image.tolist()


circle = circle_generator()


def callback():
    return next(circle)


if __name__ == '__main__':
    p = Pyghthouse(UNAME, TOKEN, image_callback=callback)
    print("Starting... use CTRL+C to stop.")
    p.start()
