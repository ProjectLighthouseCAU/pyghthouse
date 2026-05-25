from pyghthouse import Pyghthouse, VerbosityLevel
from config import UNAME, TOKEN
from time import sleep


def main_loop():
    p = Pyghthouse(UNAME, TOKEN, frame_rate=60)
    p.start()
    
    img = p.empty_image()
    while True:
        for y in range(14):
            for x in range(28):
                img[y][x] = (255, 255, 255)
                p.set_image(img)
                p.wait()
        
        sleep(1)

        for y in range(13, -1, -1):
            for x in range(27, -1, -1):
                img[y][x] = [0,0,0]
                p.set_image(img)
                # We skip frames here, but our frame_rate is high enough to hide it
                sleep(0.01)


if __name__ == '__main__':
    main_loop()