import cv2
import numpy as np
import svgwrite as svg


# function for creating stacked images in one display window
def stackImages(scale, img_array):
    rows = len(img_array)
    cols = len(img_array[0])
    rowsAvailable = isinstance(img_array[0], list)
    width = img_array[0][0].shape[1]
    height = img_array[0][0].shape[0]
    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                if img_array[x][y].shape[:2] == img_array[0][0].shape[:2]:
                    img_array[x][y] = cv2.resize(img_array[x][y], (0, 0), None, scale, scale)
                else:
                    img_array[x][y] = cv2.resize(img_array[x][y], (img_array[0][0].shape[1], img_array[0][0].shape[0]),
                                                 None, scale, scale)
                if len(img_array[x][y].shape) == 2: img_array[x][y] = cv2.cvtColor(img_array[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank] * rows
        hor_con = [imageBlank] * rows
        for x in range(0, rows):
            hor[x] = np.hstack(img_array[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if img_array[x].shape[:2] == img_array[0].shape[:2]:
                img_array[x] = cv2.resize(img_array[x], (0, 0), None, scale, scale)
            else:
                img_array[x] = cv2.resize(img_array[x], (img_array[0].shape[1], img_array[0].shape[0]), None, scale,
                                          scale)
            if len(img_array[x].shape) == 2: img_array[x] = cv2.cvtColor(img_array[x], cv2.COLOR_GRAY2BGR)
        hor = np.hstack(img_array)
        ver = hor
    return ver


# old function for transformation, new to come
"""def transform_pixel_to_mm(dist_px):
    x1 = 47
    x2 = 566
    y1 = 0
    y2 = 1000
    a = (y1 - y2) / (x1 - x2)
    b = int(y2 - a * x2)
    dist_mm = round(a * dist_px + b)
    return dist_mm


def flip_x_axis(y_coord_cam):
    x1 = 0
    x2 = 1000
    y1 = 1000
    y2 = 0
    a = (y1 - y2) / (x1 - x2)
    b = y2 - a * x2
    new_x_coord = round(a * y_coord_cam + b)
    return new_x_coord


def flip_y_axis(x_coord_cam):
    x1 = 0
    x2 = 1500
    y1 = 0
    y2 = 1500
    a = (y1 - y2) / (x1 - x2)
    b = y2 - a * x2
    new_y_coord = round(a * x_coord_cam + b)
    return new_y_coord"""


# New transformation function for camera to cnc coordinates
def transformation(point, transform_matrix):
    world_point = cv2.perspectiveTransform(point, transform_matrix)
    return world_point


def transformation_matrix_calculation():
    # coordinate of reference points in camera coordinates
    camera_points = np.array([[, ], [, ], [, ], [, ], [, ], [, ], [, ], [, ], [, ], [, ]])
    # coordinates of matching points in cnc coordinates
    cnc_points = np.array([[, ], [, ], [, ], [, ], [, ], [, ], [, ], [, ], [, ], [, ]])
    h, status = cv2.findHomography(camera_points, cnc_points)
    return h

# sets size of display window
frameWidth = 640
frameHeight = 480
paused = False
# Asks whether user wants to calibrate video settings or not
calibrate = input('Do you want to calibrate? y/n ')

# Starts video capture with camera 0
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error opening video")
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)
cap.set(3, frameWidth)
cap.set(4, frameHeight)
h_matrix = transformation_matrix_calculation()


def empty(a):
    pass


cv2.namedWindow("Output", flags=cv2.WINDOW_AUTOSIZE)

# sets baseline settings that work okay for current set up
Contrast = 1
Brightness = 75
Threshold_1 = 171

if calibrate == 'y':
    cv2.createTrackbar("Contrast", "Output", Contrast * 100, 1000, empty)
    cv2.createTrackbar("Brightness", "Output", Brightness * 100, 10000, empty)
    cv2.createTrackbar("Threshold1", "Output", Threshold_1, 255, empty)

print("Press P for Pause\nPress Q for quit\nPress S for Save and export")
while True:

    if not paused:
        ret, frame = cap.read()

    if calibrate == 'y':
        Contrast = float(cv2.getTrackbarPos("Contrast", "Output") / 100)
        Brightness = float(cv2.getTrackbarPos("Brightness", "Output") / 100)
        Threshold_1 = cv2.getTrackbarPos("Threshold1", "Output")

    # applies the Contrast, Brightness and Threshold settings to the image
    effect = frame.copy()
    effect = cv2.cvtColor(effect, cv2.COLOR_BGR2HSV)
    effect[:, :, 2] = np.clip(Contrast * effect[:, :, 2] + Brightness, 0, 255)
    effect = cv2.cvtColor(effect, cv2.COLOR_HSV2BGR)

    img_gray = cv2.cvtColor(effect, cv2.COLOR_BGR2GRAY)

    ret, thresh = cv2.threshold(img_gray, Threshold_1, 255, cv2.THRESH_BINARY)
    # gathers contours and draws them on both a blank image and over the capture video
    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)

    image_copy = effect.copy()
    blank_image = np.zeros((frameHeight, frameWidth, 3), np.uint8)

    cv2.drawContours(image=image_copy, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2,
                     lineType=cv2.LINE_AA)

    cv2.drawContours(image=blank_image, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2,
                     lineType=cv2.LINE_AA)

    imgStack = stackImages(0.65, ([frame, blank_image],
                                  [thresh, image_copy]))
    cv2.imshow("Output", imgStack)
    key_press = cv2.waitKey(1)
    if key_press & 0xFF == ord('s'):
        # Make the coordinate arrays
        cx_data = []
        cy_data = []
        x = []
        y = []
        sheet = svg.Drawing('sheet.svg')
        # this for loop iterates through all the contour elements found by openCV
        for cnt in contours:
            M = cv2.moments(cnt)
            # Finds the centers of all contour objects
            if M['m00'] is None or M['m00'] == 0:
                cx = 1
                cy = 1
            else:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
            cx_data.append(cx)
            cy_data.append(cy)
            # Separates out all the x and y coordinates of the contour edges
            for i in range(len(cnt)):
                point = transformation(cnt[i], h_matrix)
                x.append(point[0])
                y.append(point[1])

            # uncomment if you want to write contour coordinates to a text file
            """file_cont = open("./test.txt", "w+")
            for i in range(len(x)):
                line = str(x[i]) + "," + str(y[i]) + "\n"
                file_cont.writelines(line)
            file_cont.close()"""

            for i in range(len(cnt)-1):
                sheet.add(sheet.line((x[i],y[i]),(x[i+1],y[i+1]), stroke=svg.rgb(0, 0, 0, '%')))
            sheet.add(sheet.line((x[0], y[0]), (x[-1], y[-1]), stroke=svg.rgb(0, 0, 0, '%')))
        print("Saving Contours...")
        print("Saving image...")
        cv2.imwrite("Saved_img/test_img.png", imgStack)


        # Creates the SVG file using the old transform to real world coordinates
        """sheet = svg.Drawing('sheet.svg')
        for cnt in contours:
            for i in range(len(cnt) - 1):
                sheet.add(sheet.line(
                    (
                    flip_x_axis(transform_pixel_to_mm(cnt[i][0][1])), flip_y_axis(transform_pixel_to_mm(cnt[i][0][0]))),
                    (
                        flip_x_axis(transform_pixel_to_mm(cnt[i + 1][0][1])),
                        flip_y_axis(transform_pixel_to_mm((cnt[i + 1][0][0])))), stroke=svg.rgb(0, 0, 0, '%')))
            sheet.add(sheet.line(
                (flip_x_axis(transform_pixel_to_mm(cnt[0][0][1])), flip_y_axis(transform_pixel_to_mm(cnt[0][0][0]))), (
                    flip_x_axis(transform_pixel_to_mm(cnt[-1][0][1])),
                    flip_y_axis(transform_pixel_to_mm((cnt[-1][0][0])))), stroke=svg.rgb(0, 0, 0, '%')))"""
        sheet.save()


    elif key_press & 0xFF == ord('q') or key_press == 27:
        print("Quitting...")
        break
    elif key_press & 0xFF == ord("p"):
        paused = not paused

cap.release()
cv2.destroyAllWindows()
