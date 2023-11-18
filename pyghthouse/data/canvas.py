from typing import Union, Iterable


class PyghthouseCanvas:
    VALID_IMAGE_TYPE = Union[Iterable, int]
    IMAGE_SHAPE = (14, 28, 3)

    def __init__(self, initial_image=None):
        self.image = self.init_image_array()
        if initial_image is None:
            self.image[:][:][0] = 255
        else:
            self.set_image(initial_image)

    """
    Flattens the list. Works for nested lists too.
    """

    def flatten_list(self, element):
        if type(element) == list:
            result = []
            for element in element:
                result.extend(self.flatten_list(element))
            return result
        else:
            return [element]

    """
    Creates a nested list in the shape of IMAGE_SHAPE. 
    number_cb: function
        A function that returns an integer (or to integer castable) element.
    """

    def init_image_array(self, number_cb=lambda: 0):
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

    """
    Parses user input to image data.
    new_image: int | list
        If int provided, sets all values to this number. Must be between 0 and 255.
        If list provided, it must contain exactly as many elements as the image needs values,
            but it may be nested in any way.
    """

    def new_image_to_image_array(self, new_image: VALID_IMAGE_TYPE) -> list[int]:
        if isinstance(new_image, int):
            if 0 <= new_image <= 255:
                return self.init_image_array(lambda: new_image)
            else:
                raise ValueError("Color must be 0<=color<=255")

        if isinstance(new_image, list):
            try:
                flat = self.flatten_list(new_image)
                result = self.init_image_array(lambda: int(flat.pop(0)))
                if len(flat) != 0:
                    raise ValueError("Input too large")
                return result
            except IndexError:
                raise ValueError("Wrong length of Iterable")
        raise ValueError("Invalid input. Must be int or list")

    """
    Sets the new image.
    """

    def set_image(self, new_image: VALID_IMAGE_TYPE) -> list:
        try:
            self.image = self.new_image_to_image_array(new_image)
        except ValueError as e:
            raise ValueError(
                f"{e}. Most likely, your image does not have the correct dimensions."
            ) from None

        return self.image

    """
    Transforms the image to byte values.
    """

    def get_image_bytes(self) -> bytes:
        b_array = bytearray()
        for x in range(self.IMAGE_SHAPE[0]):
            for y in range(self.IMAGE_SHAPE[1]):
                for rgb in range(self.IMAGE_SHAPE[2]):
                    b_array.append(self.image[x][y][rgb])
        return b_array
