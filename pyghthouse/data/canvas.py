from threading import Lock
from numbers import Number

class PyghthouseCanvas:
    
    IMAGE_SHAPE = (14, 28, 3)
    
    def __init__(self, initial_image=None):
        
        self.lock = Lock()
        self.image = [[[0 for k in range(self.IMAGE_SHAPE[2])] for j in range(self.IMAGE_SHAPE[1])] for i in range(self.IMAGE_SHAPE[0])]
        
        if initial_image is not None:
            self.set_image(initial_image)


    def set_image(self, new_image: list) -> True:
        
        self._check_size(new_image)
        self._check_cells(new_image)
        self._check_values(new_image)

        with self.lock:

            for y in range(self.IMAGE_SHAPE[0]):
                for x in range(self.IMAGE_SHAPE[1]):
                    for rgb in range(self.IMAGE_SHAPE[2]):

                        self.image[y][x][rgb] = int(new_image[y][x][rgb])

        return self.image
    

    def get_bytes_image(self):
        
        image_bytes = b''
        
        with self.lock:
        
            for y in range(self.IMAGE_SHAPE[0]):
                for x in range(self.IMAGE_SHAPE[1]):
                    
                    image_bytes += bytes(self.image[y][x])
        
        return image_bytes
    

    def copy_image(self):

        image_copy = [[[0 for k in range(self.IMAGE_SHAPE[2])] for j in range(self.IMAGE_SHAPE[1])] for i in range(self.IMAGE_SHAPE[0])]

        with self.lock:

            for y in range(self.IMAGE_SHAPE[0]):
                for x in range(self.IMAGE_SHAPE[1]):
                    for rgb in range(self.IMAGE_SHAPE[2]):

                        image_copy[y][x][rgb] = self.image[y][x][rgb]

        return image_copy


    def _check_size(self, other: list):

        try:
            other_size = (len(other), len(other[0]), len(other[0][0]))
        
        # Catch objects like [] or 0
        except (IndexError, TypeError):
            raise TypeError(f"Received object with missing dimensions. Require a 3-dimensional list ") from None
        
        # Raise ValueError on wrong dimension size
        if self.IMAGE_SHAPE != other_size:
            raise ValueError(f"The image does not have the correct dimension sizes. Dimensions should be {self.IMAGE_SHAPE} as (row, column, rgb), but received {other_size}")
            
        
    
    def _check_cells(self, other: list):
        
        # Catch objects like [[[0,1,2],[0,1,2,3,4,5],[1]],1]
        for y in range(self.IMAGE_SHAPE[0]):
            try:
                
                if len(other[y]) != self.IMAGE_SHAPE[1]:
                    raise IndexError(f"column-list size should be {self.IMAGE_SHAPE[1]} but received {len(other[y])} at position [{y}]")
            
            except (TypeError):
                raise TypeError(f"Require type 'list' at [{y}], but received object of type '{type(other[y]).__name__}'") from None
                
            for x in range(self.IMAGE_SHAPE[1]):
                try:
                    
                    if len(other[y][x]) != self.IMAGE_SHAPE[2]:
                        raise IndexError(f"RGB-list size should be {self.IMAGE_SHAPE[2]} but received {len(other[y][x])} at position [{y}][{x}]")
                
                except (TypeError):
                    raise TypeError(f"Require type 'list' at [{y}][{x}], but received object of type '{type(other[y][x]).__name__}'") from None
        


    def _check_values(self, other: list):
        
        for y in range(self.IMAGE_SHAPE[0]):
            for x in range(self.IMAGE_SHAPE[1]):
                for rgb in range(self.IMAGE_SHAPE[2]):
                    
                    value = other[y][x][rgb]
                    
                    if not isinstance(value, Number):
                        raise TypeError(f"Wrong type at ({y},{x},{rgb}). Type should be a Number, like 'int', but received '{type(value).__name__}'")
                    
                    if int(value) < 0 or int(value) > 255:
                        raise ValueError(f"Received value {value} at ({y},{x},{rgb}) is out of range. Value should be a number between 0 <= value <= 255")