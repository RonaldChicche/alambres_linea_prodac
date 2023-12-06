import cv2 
import numpy as np

# Functions:
# - Detecting distance between 2 steel bar borders
# - Grinding quality control
# - Obstacle machine area free detector

def measure_welding(img):
    # Cut layer
    # x1, y1, x2, y2 = 725, 450, 1000, 650
    x1, y1, x2, y2 = 775, 450, 960, 650
    img = img[y1:y2, x1:x2]
    img = cv2.resize(img, (500, 400), interpolation=cv2.INTER_AREA)
    # Gray scale layer
    img_ori = img.copy()
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_h, img_w = img.shape
    # print(img_h, img_w)
    # Blur layer
    img_blur = cv2.GaussianBlur(img, (5,5), sigmaX=0, sigmaY=0)
    # Sobel mask
    sobelx = cv2.Sobel(src=img_blur, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=5) # Sobel Edge Detection on the X axis
    sobely = cv2.Sobel(src=img_blur, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=5) # Sobel Edge Detection on the Y axis
    # False edge detector -> No apply in this case
    edge_map = np.hypot(sobelx, sobely)
    edge_map = edge_map / edge_map.max() * 255
    # angle_map = np.arctan2(sobely, sobelx)
    # nms_edge_map = non_maximum_suppression(edge_map, angle_map)
    # Canny detector aplication
    edges = cv2.Canny(image=np.uint8(edge_map), threshold1=180, threshold2=500, L2gradient=False)
    # Morphological closing operation to close the borders of the detected edges
    kernel_size = 5
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    # Get contours
    contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    obj = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Size area discriminator
        if w*h > 200*300: # without resize 80*60
            obj.append([x,y,w,h])
            cv2.rectangle(img_ori, (x, y), (x+w, y+h), (255, 0, 255), 1)
    # print(obj)
    
    if len(obj) == 2:   
        color1 = (255, 255, 0)
        color2 = (0, 255, 0)
        font = cv2.FONT_HERSHEY_SIMPLEX
        # Sort the objects
        if obj[0][0] < obj[1][0]:
            o1 = obj[0][0] + obj[0][2]
            o2 = obj[1][0]
        else:
            o1 = obj[1][0] + obj[1][2]
            o2 = obj[0][0]
        # Line limits
        img_ori = cv2.line(img_ori, (o1, 0), (o1, img_h-1), color=color1, thickness=1)
        img_ori = cv2.line(img_ori, (o2, 0), (o2, img_h-1), color=color2, thickness=1)
        # Draw arrows
        img_ori = cv2.arrowedLine(img_ori, (0, int(img_h/2) - 20), (int(o1), int(img_h/2) - 20), color=color1, thickness=1)
        img_ori = cv2.arrowedLine(img_ori, (int(img_w), int(img_h/2) - 20), (int(o2), int(img_h/2) - 20), color=color2, thickness=1)        
        # Distances -> convert to mm
        dx1 = obj[0][2]
        dx2 = obj[1][2]
        dist = o2 - o1
        # Text
        t1 = f'dx1: {dx1}'
        t2 = f'dx2: {dx2}'
        t3 = f'Dist: {dist}'
        img_ori = cv2.putText(img_ori, t1, (int(img_w/4), int(img_h/2) + 20), font, 0.4, color1, 1, cv2.LINE_AA)
        img_ori = cv2.putText(img_ori, t2, (int(3*img_w/5), int(img_h/2) + 20), font, 0.4, color2, 1, cv2.LINE_AA)
        img_ori = cv2.putText(img_ori, t3, (int(img_w/2) + 30, int(img_h/2) - 40), font, 0.4, (255,0, 255), 1, cv2.LINE_AA)
       
        return img_ori, dist, dx1, dx2
    else:
        print("Low accuracy")
        return img_ori, None, None, None