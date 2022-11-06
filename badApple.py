from re import A
import cv2 as cv
import numpy as np
import math
import os


def outline(imgName):
    img = cv.imread(imgName)

    imgGray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    thresh, imgBinary = cv.threshold(imgGray, 240, 255, cv.THRESH_BINARY)

    contours, hierarchy = cv.findContours(
        imgBinary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    imgWidth = len(img[0])
    imgHeight = len(img)

    out = np.zeros((imgHeight, imgWidth, 3), dtype=np.uint8)

    cv.drawContours(out, contours, -1, (0, 255, 0), 1)
    cv.drawContours(img, contours, -1, (0, 255, 0), 1)

    cv.imwrite("out.jpg", out)

    # cv.imshow('img', out)

    im2 = cv.imread("out.jpg")
    cropped = im2[1:imgHeight-1, 1:imgWidth-1]

    # cv.imshow('img', cropped)

    cv.imwrite('out.jpg', cropped)

    # cv.imshow('img', img)
    # cv.waitKey(0)

    w = imgWidth
    h = imgHeight

    return contours, w, h


def contoursToSvg(contours, w, h, index):
    with open("svgs\\frame{index}.svg".format(index=index), "w+") as f:
        # f.write(f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">')

        for c in contours:
            f.write('<path d="M')
            for i in range(len(c)):
                x, y = c[i][0]
                f.write(f"{x} {y} ")
            f.write('" style="stroke:pink"/>')
        f.write("</svg>")


def svgToGcode(w, h, index):
    totalExtrude = 0
    with open("svgs\\frame{index}.svg".format(index=index), "r") as f:
        svg = f.read()

    numPaths = svg.count("<path")
    if (numPaths == 0):
        return
    # print(numPaths)

    layerHeight = 0.2
    nozzleDiameter = 0.4
    unitMaterial = (nozzleDiameter/2)**2 * math.pi * layerHeight
    filamentDiameter = 1.75
    filamentArea = (filamentDiameter/2)**2 * math.pi
    unitFilLength = unitMaterial/filamentArea
    with open("gcodes\\gcodeFrame{index}.gcode".format(index=index), "w+") as f:
        startingCode = ["M82 ;Absolute extrusion mode",
                        "BADAPPLE_START BED_TEMP=65 EXTRUDER_TEMP=175", "G0 X100 Y100 Z0.2\n"]
        f.write("\n".join(startingCode))
        curX = 100
        curY = 100
        for i in range(0, numPaths):
            cutString = svg[svg.find("M")+1:svg.find(' "')]
            svg = svg[svg.find(' "')+1:]
            # print(cutString)
            # print("\n")
            valList = cutString.split(" ")
            for j in range(0, len(valList), 2):
                x = int(valList[j])
                y = int(valList[j+1])

                # Scale x and y to print bed using new_value = ( (old_value - old_min) / (old_max - old_min) ) * (new_max - new_min) + new_min
                x = ((float(x) - 0) / (float(w) - 0)) * (200 - 20) + 20
                y = ((float(y) - 0) / (float(h) - 0)) * (200 - 20) + 20
                x = round(x, 2)
                y = round(y, 2)
                # flip y axis bc for some reason its upside down, then translate it back up to the print bed
                y = (y*-1)+220
                #print("totalExtrude = {totalExtrude}".format(totalExtrude = totalExtrude))
                moveLength = math.sqrt(abs((x-curX)**2 + (y-curY)**2))
                amountToExtrude = moveLength * unitFilLength
                amountToExtrude = round(amountToExtrude, 5)
                amountToExtrude = round(amountToExtrude*1.1, 5)

                #print("amtToExtrude = {amountToExtrude}".format(amountToExtrude = amountToExtrude))
                if (j == 0):
                    f.write(f"G0 X{x} Y{y}\n")
                    # print(j)
                else:
                    totalExtrude += amountToExtrude
                    totalExtrude = round(totalExtrude, 5)
                    f.write(
                        f"G1 X{x} Y{y} E{totalExtrude}; amountToExtrude={amountToExtrude}\n")
                curX = x
                curY = y
        f.write("END_PRINT\n")


def main():

    for index in range(1, 6573):
        index = str(index)
        while (len(index) != 4):
            index = "0" + index
        contours, w, h = outline(
            "frames\BadApple (8-29-2022 10-26-14 PM)\BadApple {index}.jpg".format(index=index))
        index = int(index)
        contoursToSvg(contours, w, h, index)
        svgToGcode(w, h, index)
        os.remove("svgs\\frame{index}.svg".format(index=index))
        print(index)
    print("done")


main()
