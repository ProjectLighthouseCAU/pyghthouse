from typing import Union, Iterable
# import numpy as np
class PyghthouseCanvas:

    VALID_IMAGE_TYPE = Union[Iterable, int]
    IMAGE_SHAPE = (14, 28, 3)

    def __init__(self, initial_image=None):
        self.image = self.init_image_array()
        if initial_image is None:
            self.image[:][:][0] = 255
        else:
            self.set_image(initial_image)

    def flatten_list(self,element):
        if(type(element)==list):
            result = []
            for element in element:
                result.extend(self.flatten_list(element))
            return result
        else:
            return [element]


    def init_image_array(self,number_cb=lambda: 0):
        list = []
        for x in range(self.IMAGE_SHAPE[0]):
            list_y = []
            for y in range(self.IMAGE_SHAPE[1]):
                list_rgb = []
                for rgb in range(self.IMAGE_SHAPE[2]):
                    list_rgb.append(int(number_cb()))
                list_y.append(list_rgb)
            list.append(list_y)
        return list
    
    def new_image_to_image_array(self,new_image: VALID_IMAGE_TYPE) -> list:
        if(type(new_image)==int):
            if(0<=new_image<=255):
                return self.init_image_array(lambda: new_image)
            else:
                raise ValueError("Color must be 0<=color<=255")
        # if(type(new_image)==list):
        #     if (len(new_image)!=self.IMAGE_SHAPE[0]):
        #                 raise ValueError("Invalid shape")
        #     for x in range(len(new_image)):
        #         if (len(new_image[x])!=self.IMAGE_SHAPE[1]):
        #                 raise ValueError("Invalid shape.")
        #         for y in range(len(new_image[x])):
        #             if (len(new_image[x][y])!=self.IMAGE_SHAPE[2]):
        #                 raise ValueError("Invalid shape.")
        #             for rgb in range(len(new_image[x][y])):
        #                 if(not(isinstance(new_image[x][y][rgb],int))):
        #                     # try to parse all values as int here
        #                     new_image[x][y][rgb] = int(new_image[x][y][rgb])
        #                 if(not (0<=new_image[x][y][rgb]<=255)):
        #                     raise ValueError(f"Pixel at {x},{y} has invalid color code.")
        #     return new_image
        if(type(new_image)==list):
            try:
                flat = self.flatten_list(new_image)
                result = self.init_image_array(lambda: int(flat.pop(0)))
                if len(flat) != 0:
                    raise ValueError("Input too large")
                return result
            except IndexError:
                raise ValueError("Wrong length of Iterable")
        raise ValueError("Invalid input. Must be int or list")

    def set_image(self, new_image: VALID_IMAGE_TYPE) -> list:
        try:
            self.image = self.new_image_to_image_array(new_image)
        except ValueError as e:
            raise ValueError(f"{e}. Most likely, your image does not have the correct dimensions.") from None

        return self.image

    def get_image_bytes(self)->bytes:
        b_array = bytearray()
        for x in range(self.IMAGE_SHAPE[0]):
            for y in range(self.IMAGE_SHAPE[1]):
                for rgb in range(self.IMAGE_SHAPE[2]):
                    b_array.append(self.image[x][y][rgb])
        return b_array
