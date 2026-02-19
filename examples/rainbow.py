from pyghthouse import Pyghthouse
from pyghthouse.utils import from_hsv
from config import UNAME, TOKEN


def rainbow_generator():
    image = Pyghthouse.empty_image()
    while True:
        for i in range(180):
            for x in range(28):
                for y in range(14):
                    j = x + y*28
                    image[y][x] = from_hsv((i / 180 + j / (14 * 28)) % 1.0, 1.0, 1.0)
            yield image



rainbow = rainbow_generator()


def callback():
    return next(rainbow)


if __name__ == '__main__':
    p = Pyghthouse(UNAME, TOKEN, image_callback=callback)
    print("Starting... use CTRL+C to stop.")
    p.start()
    p.keep_running()