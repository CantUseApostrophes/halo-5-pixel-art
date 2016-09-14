from colors import color_names, colors_rgb, colors_hex
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
    global image, results
    pixel = image.load()
    for j in range(0,image.size[1]):
        results.append([])
        for i in range(0,image.size[0]):
            pixel[i,j] = nearestColor(image.getpixel((i,j)), j)

def nearestColor(rgb1, row):
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
        results[row].append(color_names[mindex])
    elif instructions_mode == 1:
        # Adds the index of each color to make it easier to find in horizontal scrolling color picker
        results[row].append('('+str(mindex+1)+')'+color_names[mindex])
    elif instructions_mode == 2:
        # Adds row and column numbers of each color to make it easier to find in PC color picker menu
        results[row].append('('+str(mindex/4+1)+','+str(mindex%4+1)+')'+color_names[mindex])
    else:
        results[row].append([mindex, 1])
    return (colors_rgb[mindex][0], colors_rgb[mindex][1], colors_rgb[mindex][2])

def slimResults():
    global results
    # Let's say there are 5 reds in a row, this will combine them into 'red x5'
    for row in results:
        j = 0
        while j < len(row):
            n = 1
            while j < len(row) - n and row[j] == row[j+n]:
                n += 1
            if n > 1:
                temp_val = row[j]
                for k in range(0, n):
                    row.pop(j)
                row.insert(j, temp_val + ' x' + str(n))
            j += 1


def slimResults_AHK():
    global results
    # Let's say there are 6 reds in a row, this will make them into a 4-long block and a 2-long block
    for row in results:
        i = 0
        while i < len(row):
            n = 1
            while i < len(row) - n and row[i] == row[i+n]:
                n += 1
            if n > 1:
                temp_color = row[i][0]
                index_adjust = 0 # Need to adjust index each loop so that we don't "slim" data more than once
                for j in range(0, n):
                    row.pop(i)
                for j in range(0, n/4):
                    row.insert(i, [temp_color, 4])
                index_adjust += n/4
                if n%4 == 1:
                    row.insert(i+n/4, [temp_color, 1])
                    index_adjust += 1
                elif n%4 == 2:
                    row.insert(i+n/4, [temp_color, 2])
                    index_adjust += 1
                elif n%4 == 3:
                    row.insert(i+n/4, [temp_color, 2])
                    row.insert(i+n/4+1, [temp_color, 1])
                    index_adjust += 2
                i += index_adjust
            else:
                i += 1
    if print_info:
        count = 0
        for row in results:
            count += len(row)
        print 'Object count:', count

def writeInstructions():
    f = open(instructions_name,'w')
    output = ''
    for row in results:
        for i in range(0, len(row)):
            output += row[i]
            if i + 1 < len(row):
                output += ' | '
        output += '\n\n'
    f.write(output)
    f.close()

def generateAHK():
    f = open('build_image.ahk','w')
    row_ = 0
    col = 0
    with open ("ahk_functions", "r") as funcs:
        output = funcs.read()
    for row in results:
        for i in range(0, len(row)):
            coords = [target_size[0]*(-1)+col*2, 0, target_size[1]*2-250-row_*2]
            output += 'clickPlus()\n'
            output += 'checkPlusMenu()\n'
            output += 'clickBlock'+str(row[i][1])+'()\n'
            col += row[i][1]
            output += 'clickProperties()\n'
            for j in ['Primary', 'Secondary', 'Tertiary']:
                output += 'click'+j+'()\n'
                output += 'clickColorArrow()\n'
                n = row[i][0]
                colorCoords = [1189 + (n%4)*74, 112 + (n/4)*36]
                label = 'Label_'+str(row_)+'_'+str(col)+'_'+j
                output += label + ':\n'
                if n < 40:
                    output += 'clickColor('+str(colorCoords[0])+', '+str(colorCoords[1])+', '+colors_hex[n]+', '+j+', '+label+')\n'
                else:
                    output += 'dragBar('+str(n/4-9)+')\n'
                    output += 'clickColor('+str(colorCoords[0])+', 443, '+colors_hex[n]+', '+j+', '+label+')\n'
            output += 'clickRotation()\n'
            output += 'clickField1()\n'
            output += 'input(0)\n'
            output += 'clickField2()\n'
            output += 'input(-90)\n'
            output += 'clickField3()\n'
            output += 'input(0)\n'
            output += 'clickArrowToPosition()\n'
            output += 'clickField1()\n'
            output += 'input('+str(coords[0])+')\n'
            output += 'clickField2()\n'
            output += 'input(0)\n'
            output += 'clickField3()\n'
            output += 'input('+str(coords[2])+')\n'
        row_ += 1
        col = 0
    output += 'MsgBox % FormatSeconds((A_TickCount-StartTime)/1000)\n'
    output += 'Escape::ExitApp\n' # Sets Esc key to terminate script
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
