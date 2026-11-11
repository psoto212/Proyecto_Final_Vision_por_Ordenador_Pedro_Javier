
import cv2
import numpy as np

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("No se ha podido abrir la camara")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    azul_min = np.array([85, 40, 30], dtype=np.uint8)
    azul_max = np.array([140, 255, 255], dtype=np.uint8)

    mascara = cv2.inRange(hsv, azul_min, azul_max)
    kernel = np.ones((5, 5), np.uint8)

    mascara = cv2.erode(mascara, kernel, iterations=1)
    mascara = cv2.dilate(mascara, kernel, iterations=1)

    azul_segmentado = cv2.bitwise_and(
        frame, frame, mask=mascara
    )

    contornos, _ = cv2.findContours(
        mascara,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contornos) > 0:
        contorno_mayor = max(contornos, key=cv2.contourArea)

        if cv2.contourArea(contorno_mayor) > 1000:
            x, y, w, h = cv2.boundingRect(contorno_mayor)

            # Dibujamos el recuadro
            cv2.rectangle(
                frame, (x, y), (x+w, y+h), (0, 255, 0), 2
            )

    cv2.imshow("Proyecto Final Vision por Ordenador", frame)
    cv2.imshow("Mascara azul", mascara)
    cv2.imshow("Azul segmentado", azul_segmentado)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
