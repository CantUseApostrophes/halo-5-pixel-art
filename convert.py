from colors import color_names, colors_rgb
from PIL import Image
import math, ConfigParser, io

# Loads the configuration file
with open("config.ini") as f:
    sample_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.readfp(io.BytesIO(sample_config))

### Options ###
# See config.ini for comments describing each option
input_name = config.get('options', 'input_filename')

output_name = config.get('options', 'output_filename')

instructions_name = config.get('options', 'instructions_filename')

adjust_for_eyes = config.getboolean('options', 'adjust_for_eyes')

resample_mode = config.get('options', 'resample_mode')
if resample_mode.lower() == 'bicubic':
    resample_mode = Image.BICUBIC
elif resample_mode.lower() == 'lanczos':
    resample_mode = Image.LANCZOS
elif resample_mode.lower() == 'bilinear':
    resample_mode = Image.BILINEAR
elif resample_mode.lower() == 'nearest':
    resample_mode = Image.NEAREST

print_info = config.getboolean('options', 'print_info')

native_res = config.getboolean('options', 'native_resolution')

max_resolution = config.getint('options', 'max_resolution')

instructions_mode = config.getint('options', 'instructions_mode')


image = Image.open(input_name)

results = [] # stores a list of colors

target_size = [] # stores the dimensions of the resized image

def printInfo():
    print 'Image dimensions:', image.width, 'x', image.height

    resize_factor = math.sqrt(image.width * image.height / 1600.)
    print 'Resize factor:', resize_factor

    max_width = int(image.width / resize_factor)
    print 'Max width:', max_width

    max_height = int(image.height / resize_factor)
    print 'Max height:', max_height

    print 'Max resolution:', max_width * max_height

def resizeImage():
    global image, target_size

    if native_res:
        resize_factor = 1
    else:
        target_res = max_resolution
        resize_factor = math.sqrt(image.width * image.height / float(target_res))

    target_size = [int(image.width / resize_factor), int(image.height / resize_factor)]

    if print_info:
        printResizeInfo(resize_factor)

    image = image.resize((int(image.size[0]/resize_factor), int(image.size[1]/resize_factor)), resample_mode)

def printResizeInfo(resize_factor):
    print 'Target width:', target_size[0]
    print 'Target height:', target_size[1]
    print 'Actual resolution:', target_size[0] * target_size[1]

def adjustColors():
    global image
    pixel = image.load()
    for j in range(0,image.size[1]):
      for i in range(0,image.size[0]):
          pixel[i,j] = nearestColor(image.getpixel((i,j)))

def nearestColor(rgb1):
    min_dist = 442
    mindex = -1
    for i in range(0, 128):
        rgb2 = colors_rgb[i]
        if adjust_for_eyes:
            # Human eyes are sensitive to some colors more than others
            dist = math.sqrt(((rgb1[0]-rgb2[0])*0.30)**2 + ((rgb1[1]-rgb2[1])*0.59)**2 + ((rgb1[2]-rgb2[2])*0.11)**2)
        else:
            dist = math.sqrt((rgb1[0]-rgb2[0])**2 + (rgb1[1]-rgb2[1])**2 + (rgb1[2]-rgb2[2])**2)
        if dist < min_dist:
            min_dist = dist
            mindex = i
    if instructions_mode == 0 or instructions_mode == 3:
        # Builds list of colors using with names that Halo 5 uses
        results.append(color_names[mindex])
    elif instructions_mode == 1:
        # Adds the index of each color to make it easier to find in horizontal scrolling color picker
        results.append('('+str(mindex+1)+')'+color_names[mindex])
    elif instructions_mode == 2:
        # Adds row and column numbers of each color to make it easier to find in PC color picker menu
        results.append('('+str(mindex/4+1)+','+str(mindex%4+1)+')'+color_names[mindex])
    else:
        results.append([mindex, 1])
    return (colors_rgb[mindex][0], colors_rgb[mindex][1], colors_rgb[mindex][2])

def slimResults():
    global results
    # Inserts 'break' into the list to signify the end of a row
    for i in range(len(results), -1, -1):
        if i % target_size[0] == 0 and i != 0:
            results.insert(i, 'break')
    i = 0
    # Let's say there are 5 reds in a row, this will combine them into 'red x5'
    while i < len(results):
        n = 1
        while i < len(results) - n and results[i] == results[i+n] and results[i+n] != 'break':
            n += 1
        if n > 1:
            results.insert(i, results[i] + ' x' + str(n))
            for j in range(0, n):
                results.pop(i+1)
        i += 1

def slimResults_AHK():
    global results
    # Inserts 'break' into the list to signify the end of a row
    for i in range(len(results), -1, -1):
        if i % target_size[0] == 0 and i != 0:
            results.insert(i, 'break')
    i = 0
    # Let's say there are 6 reds in a row, this will make them into a 4-long block and a 2-long block
    while i < len(results):
        n = 1
        while i < len(results) - n and results[i] == results[i+n] and results[i+n] != 'break':
            n += 1
        if n > 1:
            temp_color = results[i][0]
            index_adjust = 0 # Need to adjust index each loop so that we don't "slim" data more than once
            for j in range(0, n):
                results.pop(i)
            for j in range(0, n/4):
                results.insert(i, [temp_color, 4])
            index_adjust += n/4
            if n%4 == 1:
                results.insert(i+n/4, [temp_color, 1])
                index_adjust += 1
            elif n%4 == 2:
                results.insert(i+n/4, [temp_color, 2])
                index_adjust += 1
            elif n%4 == 3:
                results.insert(i+n/4, [temp_color, 2])
                results.insert(i+n/4+1, [temp_color, 1])
                index_adjust += 2
            i += index_adjust
        else:
            i += 1
    if print_info:
        print 'Object count:', len(results)

def writeInstructions():
    f = open(instructions_name,'w')
    output = ''
    for i in range(0, len(results)):
        if results[i] != 'break':
            output += results[i]
            if i + 1 < len(results) and results[i+1] != 'break':
                output += ' | '
        else:
            output += '\n\n'
    f.write(output)
    f.close()

def generateAHK():
    f = open('build_image.ahk','w')
    row = 0
    col = 0
    coords = [target_size[0]*(-1), 0, target_size[1]*2-250]
    output = '{Escape}::ExitApp\n' # Sets Esc key to terminate script
    # Clicks the plus button, then Primitives, then 2'
    output += 'Click 1750, 40\nSleep 100\nClick 1560, 230\nSleep 100\nClick 1560, 200\nSleep 100\n'
    for i in range(0, len(results)):
        if results[i] == 'break':
            row += 1
            col = 0
        else:
            coords = [target_size[0]*(-1)+col*2, 0, target_size[1]*2-250-row*2]
            if results[i][1] == 1:
                output += 'Click 1560, 240\nSleep 100\n' # Spawn 1-pixel block (2'x2'x2')
                col += 1
            elif results[i][1] == 2:
                output += 'Click 1560, 265\nSleep 100\n' # Spawn 2-pixel block (2'x2'x4')
                col += 2
            elif results[i][1] == 4:
                output += 'Click 1560, 295\nSleep 100\n' # Spawn 4-pixel block (2'x2'x8')
                col += 4
            #Clicks the Object Properties button
            output += 'Click 1850, 40\nSleep 100\n'
            if i == 0:
                output += 'PixelGetColor, color, 1533, 143\nif (color = "0x000000")\n{\n\tClick 1530, 150\n\tSleep 100\n}\n'
            output += 'Loop '+str(23+results[i][0])+' {\n\tClick 1856, 455\n\tSleep 50\n}\n' #
            output += 'Loop '+str(23+results[i][0])+' {\n\tClick 1856, 483\n\tSleep 50\n}\n' # Sets colors
            output += 'Loop '+str(23+results[i][0])+' {\n\tClick 1856, 511\n\tSleep 50\n}\n' #
            output += 'Loop 5 {\n\tClick 1856, 567\n\tSleep 50\n}\n' #
            output += 'Loop 5 {\n\tClick 1856, 595\n\tSleep 50\n}\n' # Sets matte/metallic to 10
            output += 'Loop 5 {\n\tClick 1856, 623\n\tSleep 50\n}\n' #
            output += 'Click 1560, 315\nSleep 100\n' # Click Rotation
            output += 'Click 1830, 207\nSleep 100\n' # Click pitch left arrow
            output += 'Click 1518, 80\nSleep 100\n' # Click the back button
            output += 'Click 1560, 285\nSleep 100\n' # Click Position
            output += 'Click 1813, 177\nSleep 100\n' # Click X field
            output += 'Send ' + str(coords[0]) + '{Enter}\nSleep 100\n' # Enter X coordinates
            output += 'Click 1813, 205\nSleep 100\n' # Click Y field
            output += 'Send ' + str(coords[1]) + '{Enter}\nSleep 100\n' # Enter Y coordinates
            output += 'Click 1813, 233\nSleep 100\n' # Click Z field
            output += 'Send ' + str(coords[2]) + '{Enter}\nSleep 100\n' # Enter Z coordinates
            output += 'Click 1750, 40\nSleep 100\n' # Click plus button
    output += 'Send {Escape}'
    f.write(output)
    f.close()

def main():
    if print_info:
        printInfo()             # Prints info about the max dimensions of the image
    resizeImage()               # Resizes the image and stores the dimensions
    adjustColors()              # Finds the nearest color of each pixel, and creates a list of the color names
    if instructions_mode != 3 and instructions_mode != 4:
        slimResults()           # If there are multiple of the same color in a row, combine into one entry
    if instructions_mode == 4:
        slimResults_AHK()
        generateAHK()
    else:
        writeInstructions()         # Outputs the names of the colors to a text file
    image.save('output.png')
    print 'Image successfully converted.'

main()
