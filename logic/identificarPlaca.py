import cv2
import pytesseract
import re
#para esto debes descargar tesseract  y colocar la ruta de descarga
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Jesus Petro Ramos\Desktop\TODO LO RELACIONADO A DESARROLLO DE SOFTWARE\Registro_vehicular_UTB-main\tesseract\tesseract.exe'

def idPlaca (carpeta,archivo):
    placa = []
    #print (carpeta+"/"+archivo)
    image = cv2.imread(carpeta+"/"+archivo, 1)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.blur(gray, (3, 3))
    canny = cv2.Canny(gray, 150, 200)
    canny = cv2.dilate(canny, None, iterations=1)

    cnts, _ = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        epsilon = 0.09 * cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, epsilon, True)
        if len(approx) == 4 and area > 9000:
            #print('area= ', area)
            aspect_ratio = float(w) / h
            if aspect_ratio > 2.0:
                placa = gray[y:y + h, x:x + w]
                text = pytesseract.image_to_string(placa, config='--psm 11')
                print('text= ', text)
                cv2.imshow('placa', placa)
                cv2.moveWindow('placa', 780, 10)
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 3)
                cv2.putText(image, text, (x - 20, y - 10), 1, 2.2, (0, 255, 0), 3)
                return text



