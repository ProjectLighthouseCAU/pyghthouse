"""TODO: Test methods: __init__
                       set_image
                       _check_size
                       _check_values
                       get_image_bytes
"""
class PyghthouseCanvas:

    def __init__(self, initial_image=None):
        
        self.size = (14,28,3)
        self.image = [[[0] * self.size[2]] * self.size[1]] * self.size[1]
        
        if initial_image != None:
            self.set_image(initial_image)


    def set_image(self, new_image: list) -> True:
        
        self._check_size(new_image)
        self._check_values(new_image)

        for y in range(len(self.image)):
            for x in range(len(self.image[0])):
                for rgb in range(self.image[0][0]):
                    
                    self.image[y][x][rgb] = new_image[y][x][rgb]

        return self.image


    def _check_size(self, other: list):
        #TODO: Catch objects like [[[0,1,2],[0,1,2,3,4,5]]]
        # Catch objects like [0, [], [[1,2,3]]]
        try:
            other_size = (len(other), len(other[0]), len(other[0][0]))
        except (IndexError, TypeError):
            raise TypeError(f"TypeError: Received image with missing dimensions. Are you sure this object is an image?")
        
        # Raise ValueError on wrong dimension size
        if self.size == other_size:
            return True
        else:
            raise ValueError(f"ValueError: The image does not have the correct dimensions. Dimensions should be {self.size} as (y,x,rgb), but received {other_size} ")
        
    
    def _check_values(self, other: list):
        
        for y in range(self.size[0]):
            for x in range(self.size[1]):
                for rgb in range(self.size[2]):
                    
                    value = other[y][x][rgb]
                    
                    #TODO: Decide on either throw error on wrong type or do a typecast with a warning
                    if not isinstance(value, int):
                        raise TypeError(f"TypeError: Wrong type at ({y},{x},{rgb}). Type should be int but received {type(value)}")
                    
                    #TODO: Decide on either throw error on wrong value or change to closest value in bounds with a warning
                    if int(value) < 0 or int(value) > 255:
                        raise ValueError(f"ValueError: The value {value} at ({y},{x},{rgb}) is out of bounds. Value should be a number between 0 <= value <= 255")


    def get_image_bytes(self):
        
        bytes_image = b''
        for y in range(self.size[0]):
            for x in range(self.size[1]):
                bytes_image += bytes(self.image[y][x])
        
        return bytes_image
