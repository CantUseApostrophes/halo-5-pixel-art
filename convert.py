from colors import color_names, colors_rgb
from PIL import Image
import math

fname = 'manning.png'

image = Image.open(fname)

results = []

target_size = []

# Options
adjust_for_eyes = True # Adjusts color matching algorithm to make them look closer according to human eye

resample_mode = Image.NEAREST # BICUBIC, LANCZOS, BILINEAR, NEAREST

max_resolution = 500

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

    target_res = max_resolution

    resize_factor = math.sqrt(image.width * image.height / float(target_res))

    target_size = [int(image.width / resize_factor), int(image.height / resize_factor)]

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
            dist = math.sqrt(((rgb1[0]-rgb2[0])*0.30)**2 + ((rgb1[1]-rgb2[1])*0.59)**2 + ((rgb1[2]-rgb2[2])*0.11)**2)
        else:
            dist = math.sqrt((rgb1[0]-rgb2[0])**2 + (rgb1[1]-rgb2[1])**2 + (rgb1[2]-rgb2[2])**2)
        if dist < min_dist:
            min_dist = dist
            mindex = i
    results.append(color_names[mindex])
    return (colors_rgb[mindex][0], colors_rgb[mindex][1], colors_rgb[mindex][2])

def slimResults():
    global results
    i = 0
    for i in range(len(results), -1, -1):
        if i % target_size[0] == 0 and i != 0:
            results.insert(i, 'break')
    while i < len(results):
        n = 1
        while i < len(results) - n and results[i] == results[i+n] and results[i+n] != 'break':
            n += 1
        if n > 1:
            results.insert(i, results[i] + ' x' + str(n))
            for j in range(0, n):
                results.pop(i+1)
        i += 1

def writeInstructions():
    f = open('Instructions.txt','w')
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

def main():
    #printInfo()            # Prints info about the max dimensions of the image
    resizeImage()           # Resizes the image and stores the dimensions
    adjustColors()          # Finds the nearest color of each pixel, and creates a list of the color names
    slimResults()           # If there are multiple of the same color in a row, combine into one entry
    writeInstructions()     # Outputs the names of the colors to a text file

main()

image.save('output.png')
