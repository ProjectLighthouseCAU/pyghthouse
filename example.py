'''
This example should give a simple overview on how to use Pyghthouse.

A generel orientation of what you need:
- Import of pyghthouse
- Creating an instance of Pyghthouse
- Start Pyghthouse routine
- Sending images with either a given callback function or by set_image
- Stop Pyghthouse routine (not needed but recommended)

More examples can be found in the examples folder.
'''

# Optional: This condition only executes if run as a script. 
#           Importing this program won't execute this block.
if __name__ == '__main__':
    
    from pyghthouse import Pyghthouse
    import pyghthouse.utils as utils
    from examples.config import UNAME, TOKEN


    # Create instance of Pyghthouse and start Pyghthouse routine
    username = UNAME
    token = TOKEN
    p = Pyghthouse(username, token)
    p.start()
    
    # The image object is a 3 dimensional list. Each index is accessed via [row][collum][rgb]
    # Create a black image
    img = p.empty_image()

    pos_x = 10
    pos_y = 5

    # The used color is in the RGB format. We use a list where each index represents a color channel.
    # Index 0 for red, 1 for green, 2 for blue. 
    # Each color channel has a size of 1 byte, so values from 0 to 255 can be used.
    color = [100, 124, 24]

    # Set the image with one colored pixel
    img[pos_y][pos_x] = color
    p.set_image(img)

    key = input("Enter 'n' for the next image, enter any other key to skip\n")
    if key.upper() == "N":

        # Our library also have convertors for other color formats. 
        # Now we convert a hsv color to an rgb color
        color = utils.from_hsv(0.5, 1.0, 0.7)
        
        # Set the color of all pixels
        for y in range(14):
            for x in range(28):
                img[y][x] = color
        
        p.set_image(img)
    

    key = input("Enter 'n' for the next animation, enter any other key to skip\n")
    if key.upper() == "N":
        
        color = [255, 255, 255]
        
        # Let 3 white lines appear
        for x in range(28):
            for y in range(3,10,3):
                
                img[y][x] = color
            
            p.set_image(img)
            # set_image overwrites the old image. So to prevent the loss of an image,
            # we wait until the frame has been build
            p.wait()

    
    p.stop()