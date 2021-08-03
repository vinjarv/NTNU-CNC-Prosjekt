import cv2
import numpy as np
import svgwrite as svg

# noinspection PyPep8Naming
def stackImages(scale, imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape [:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None,scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        ver = hor
    return ver

frameWidth = 640
frameHeight = 480
paused = False

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("Error opening video")

cap.set(3, frameWidth)
cap.set(4, frameHeight)


def empty(a):
    pass


cv2.namedWindow("Output", flags=cv2.WINDOW_AUTOSIZE)


# Using 'value' pointer is unsafe and deprecated. Use NULL as value pointer. To fetch trackbar value setup callback
# This is a bug from OpenCV, pay no attention to it.

print("Press P for Pause\nPress Q for quit\nPress S for Save and Quit")
while True:
    # If not paused - get next
    if not paused:
        ret, frame = cap.read()
    #for tape 6.10, 500, 128
    # for plate 1.26, 500, 128
    Contrast = 6.10
    Brightness = 500
    Threshold_1 = 128

    effect = frame.copy()
    effect = cv2.cvtColor(effect, cv2.COLOR_BGR2HSV)
    effect[:, :, 2] = np.clip(Contrast * effect[:, :, 2] + Brightness, 0, 255)
    effect = cv2.cvtColor(effect, cv2.COLOR_HSV2BGR)

    img_gray = cv2.cvtColor(effect, cv2.COLOR_BGR2GRAY)

    ret, thresh = cv2.threshold(img_gray, Threshold_1, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)

    image_copy = effect.copy()
    blank_image = np.zeros((frameHeight, frameWidth, 3), np.uint8)
    new_contour = []
    for i in range(len(hierarchy[0])):
        if hierarchy[0][i][3] != -1:
            new_contour.append(contours[i])
    contours = new_contour


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
                x.append(cnt[i][0][0])
                y.append(cnt[i][0][1])
        print("Saving image...")
        cv2.imwrite("Saved_img/test_img.png", imgStack)
        file_cont = open("./test.txt", "w+")
        print("Saving Contours...")
        for i in range(len(x)):
            line = str(x[i]) + "," + str(y[i]) + "\n"
            file_cont.writelines(line)
        file_cont.close()
        sheet = svg.Drawing('sheet.svg')
        for cnt in contours:
            for i in range(len(cnt)-1):
                sheet.add(sheet.line((int(cnt[i][0][0]), int(cnt[i][0][1])), (int(cnt[i+1][0][0]), int(cnt[i+1][0][1])), stroke=svg.rgb(0, 0, 0, '%')))
            sheet.add(sheet.line((int(cnt[0][0][0]), int(cnt[0][0][1])), (int(cnt[-1][0][0]), int(cnt[-1][0][1])), stroke=svg.rgb(0, 0, 0, '%')))
        sheet.save()

        print("Quitting...")
        break
    elif key_press & 0xFF == ord('q') or key_press == 27:
        print("Quitting...")
        break
    elif key_press & 0xFF == ord("p"):
        paused = not paused
cap.release()
cv2.destroyAllWindows()
