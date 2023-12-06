import cv2 
import numpy as np

# Functions:
# - Detecting distance between 2 steel bar borders
# - Grinding quality control
# - Obstacle machine area free detector

def measure_welding(img):
    """ Esta funcion recibe imagenes de 1080x1920, detecta los bordes de las barras de acero y mide la distancia entre ellas.
        - Codigos de error:
            0: No hay error
            1: Imagen en formato incorrecto
            2: Fallo en la deteccion de bordes
            3: mala deteccion
    """
    err = 0
    # Check image size and rgb chanel
    if img.shape != (1080, 1920, 3):
        print("Image size error")
        err = 1
        return img, 0, 0, 0, err
    # Cut, resize layer
    x1, y1, x2, y2 = 830, 500, 1030, 700
    img = img[y1:y2, x1:x2]
    img = cv2.resize(img, (800, 750), interpolation=cv2.INTER_AREA)
    # Gray mask layer
    img_ori = img.copy()
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_h, img_w = img.shape
    # print(img_h, img_w)
    # Blur layer
    img_blur = cv2.medianBlur(img, 17)
    # Sobel mask
    sobelx = cv2.Sobel(src=img_blur, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=9) # Sobel Edge Detection on the X axis
    sobely = cv2.Sobel(src=img_blur, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=9) # Sobel Edge Detection on the Y axis
    # False edge detector -> No apply in this case
    edge_map = np.hypot(sobelx, sobely)
    edge_map = edge_map / edge_map.max() * 255
    # Canny detector aplication
    edges = cv2.Canny(image=np.uint8(edge_map), threshold1=85, threshold2=450)
    # Morphological closing operation to close the borders of the detected edges
    kernel_size = 5
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    # Get contours
    contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [(x, y, w, h) for contour in contours for x, y, w, h in [cv2.boundingRect(contour)]]
    obj = sorted(rects, key=lambda x: x[2]*x[3], reverse=True)[:2]
    
    for rect in rects:
        x, y, w, h = rect
        if rect in obj:
            cv2.rectangle(img_ori, (x, y), (x+w, y+h), (255, 0, 255), 2)
    # print(obj)
    
    if len(obj) != 2:  
        print("Low accuracy")
        err = 2
        return img_ori, 0, 0, 0, err

    
    # Sort the objects
    if obj[0][0] < obj[1][0]:
        o1 = obj[0][0] + obj[0][2]
        o2 = obj[1][0]
    else:
        o1 = obj[1][0] + obj[1][2]
        o2 = obj[0][0]

    # Distances -> convert to mm
    dx1 = obj[0][2]
    dx2 = obj[1][2]
    dist = o2 - o1
    dist_mm = round(0.0245924 * dist + 1.03627584, 2)

    if obj[0][2] * obj[0][3] < 7000 or obj[1][2] * obj[1][3] < 7000:
        print("Low accuracy 3")
        return img_ori, 0, 0, 0, 3
    
    
    if obj[0][0] + dist + obj[1][2]> img_w:
        print("Low accuracy 4")
        return img_ori, 0, 0, 0, 3

    # if dx1 + dx2 > img_w:
    #     print("Low accuracy 5")
    #     return img_ori, 0, 0, 3

    color1 = (255, 255, 0)
    color2 = (0, 255, 0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    # Line limits
    img_ori = cv2.line(img_ori, (o1, 0), (o1, img_h-1), color=color1, thickness=1)
    img_ori = cv2.line(img_ori, (o2, 0), (o2, img_h-1), color=color2, thickness=1)
    # Draw arrows
    img_ori = cv2.arrowedLine(img_ori, (0, int(img_h/2) - 20), (int(o1), int(img_h/2) - 20), color=color1, thickness=1)
    img_ori = cv2.arrowedLine(img_ori, (int(img_w), int(img_h/2) - 20), (int(o2), int(img_h/2) - 20), color=color2, thickness=1)        
    
    # Text
    t1 = f'dx1: {dx1}'
    t2 = f'dx2: {dx2}'
    t3 = f'Dist: {dist_mm} mm, {dist} px'
    img_ori = cv2.putText(img_ori, t1, (int(img_w/4), int(img_h/2) + 20), font, 0.4, color1, 1, cv2.LINE_AA)
    img_ori = cv2.putText(img_ori, t2, (int(3*img_w/5), int(img_h/2) + 20), font, 0.4, color2, 1, cv2.LINE_AA)
    img_ori = cv2.putText(img_ori, t3, (int(img_w/2) + 30, int(img_h/2) - 40), font, 0.4, (255,0, 255), 1, cv2.LINE_AA)
    
    return img_ori, dist_mm, dx1, dx2, err
    
def get_best_blob(blobs):
    if blobs:
        # Calcular el área de cada contorno
        areas = [cv2.contourArea(blob) for blob in blobs]
        # Encontrar el índice del contorno con el área más grande
        best_blob_index = np.argmax(areas)
        # Devolver el contorno con el área más grande
        return blobs[best_blob_index]
    else:
        # Si no hay contornos, devolver None
        return None

def measure_tail(img):
    """ Esta funcion recibe imagenes de 1080x1920, detecta la cola del alambre y mide su longitud respecto de un punto de referencia.
        - Codigos de error:
            0: No hay error
            1: Imagen en formato incorrecto
            2: Fallo en la deteccion de bordes
    """
    err = 0
    # Check image size and rgb chanel
    if img.shape != (1080, 1920, 3):
        print("Image size error")
        err = 1
        return img, 0, err

    # Capa  de corte: extraccion de area de interes950:1050
    img = img[310:560, 300:1400]   
    img = cv2.resize(img, (0, 0), fx=1, fy=3)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Extract wire region
    _ , thresh = cv2.threshold(gray,70,250,cv2.THRESH_BINARY_INV)
    
    # morphology kernel
    kernel = np.array((
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
            ), dtype="int")

    dy = cv2.Sobel(thresh, cv2.CV_32F, 0, 1, ksize=21)
    dy = dy * dy
    cv2.normalize(dy, dy, norm_type=cv2.NORM_MINMAX, alpha=255)
    dy = dy.astype('uint8')

    _, mid = cv2.threshold(dy, 0.2 * 255, 255, cv2.THRESH_BINARY)
    
    mid[0:250, :] = 0
    mid[550:, :] = 0

    mid_temp = cv2.dilate(mid, kernel, iterations=7)
    mid = cv2.erode(mid_temp, kernel, iterations=7)

    mid_blobs, _ = cv2.findContours(mid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_mid = get_best_blob(mid_blobs)

    if best_mid is None:
        err = 2
        return img, 0, err

    img_contour = img.copy()
    x, y, w, h = cv2.boundingRect(best_mid)
    cv2.rectangle(img_contour, (x, y), (x+w, y+h), (255, 0, 255), 2)
    # draw a vertical line given a x position
    x_line = 1075
    cv2.line(img_contour, (x_line, 0), (x_line, img.shape[0]), (0, 255, 0), 2)
    pixel_length = x_line - x

    # check if x is out of range
    if x > 1000:
        err = 2
        return img_contour, -1, err
    elif x + w < 1000:
        err = 3
        return img_contour, -1, err

    # tail_length = 0.05699 * pixel_length - 2.947
    tail_length = 0.03837315 * pixel_length +  0.43820662
    tail_length = tail_length * 10
    tail_length = round(tail_length, 1)

    # put pixel length on image
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img_contour, f'{tail_length}', (50, 50), font, 1, (0, 0, 255), 2, cv2.LINE_AA)

    return img_contour, tail_length, err