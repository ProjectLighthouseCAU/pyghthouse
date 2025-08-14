"""TODO: Test methods: __init__
                       set_image
                       _check_size
                       _check_cells
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
        self._check_cells(new_image)
        self._check_values(new_image)

        for y in range(len(self.image)):
            for x in range(len(self.image[0])):
                for rgb in range(self.image[0][0]):
                    
                    self.image[y][x][rgb] = new_image[y][x][rgb]

        return self.image


    def _check_size(self, other: list):

        try:
            other_size = (len(other), len(other[0]), len(other[0][0]))
        
        # Catch objects like [] or 0
        except (IndexError, TypeError):
            raise TypeError(f"Received object with missing dimensions. Require a 3-dimensional list ")
        
        # Raise ValueError on wrong dimension size
        if self.size != other_size:
            raise ValueError(f"The image does not have the correct dimensions. Dimensions should be {self.size} as (y, x, rgb), but received {other_size}")
            
        
    
    def _check_cells(self, other: list):
        
        # Catch objects like [[[0,1,2],[0,1,2,3,4,5],[1]],1]
        # TODO: Decide on either throw error on too large lists or do a warning
        for y in range(self.size[0]):
            try:
                
                if len(other[y]) != self.size[1]:
                    raise IndexError(f"RGB list size shoule be {self.size[1]} but received {len(other[y])} at [{y}]")
            
            except (TypeError):
                raise TypeError(f"Require type 'list' at [{y}], but received object of type '{type(other[y]).__name__}'")
                
            for x in range(self.size[1]):
                try:
                    
                    if len(other[y][x]) != self.size[2]:
                        raise IndexError(f"RGB list size shoule be {self.size[2]} but received {len(other[y][x])} at [{y}][{x}]")
                
                except (TypeError):
                    raise TypeError(f"Require type 'list' at [{y}][{x}], but received object of type '{type(other[y][x]).__name__}'")
        


    def _check_values(self, other: list):
        
        for y in range(self.size[0]):
            for x in range(self.size[1]):
                for rgb in range(self.size[2]):
                    
                    value = other[y][x][rgb]
                    
                    #TODO: Decide on either throw error on wrong type or do a typecast with a warning
                    #TODO: Integrate other numerical types?
                    if not isinstance(value, int):
                        raise TypeError(f"Wrong type at ({y},{x},{rgb}). Type should be 'int' but received '{type(value).__name__}'")
                    
                    #TODO: Decide on either throw error when out of range or change to closest value in range with a warning
                    if int(value) < 0 or int(value) > 255:
                        raise ValueError(f"Received value {value} at ({y},{x},{rgb}) is out of range. Value should be a number between 0 <= value <= 255")


    def get_image_bytes(self):
        
        image_bytes = b''
        
        for y in range(self.size[0]):
            for x in range(self.size[1]):
                
                image_bytes += bytes(self.image[y][x])
        
        return image_bytes
