
import cv2
import numpy as np
import time

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("No se ha podido abrir la camara")

centro_anterior = None
tiempo_anterior = None

velocidad_suavizada = 0.0
alpha = 0.2

intervalo_actualizacion = 0.2
ultimo_cambio = time.perf_counter()
velocidad_mostrada = 0.0

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

    objeto_detectado = False
    tiempo_actual = time.perf_counter()

    if len(contornos) > 0:
        contorno_mayor = max(contornos, key=cv2.contourArea)

        if cv2.contourArea(contorno_mayor) > 1000:
            objeto_detectado = True

            x, y, w, h = cv2.boundingRect(contorno_mayor)

            centro_x = x + w // 2
            centro_y = y + h // 2

            cv2.circle(
                frame, (centro_x, centro_y),
                5, (0, 0, 255), -1
            )

            cv2.rectangle(
                frame, (x, y),
                (x + w, y + h),
                (0, 255, 0), 2
            )

            if centro_anterior is not None and tiempo_anterior is not None:
                dt = tiempo_actual - tiempo_anterior

                if dt > 0:
                    dx = centro_x - centro_anterior[0]
                    dy = centro_y - centro_anterior[1]

                    distancia = np.sqrt(dx**2 + dy**2)
                    velocidad = distancia / dt

                    velocidad_suavizada = (
                        alpha * velocidad
                        + (1 - alpha) * velocidad_suavizada
                    )

            centro_anterior = (centro_x, centro_y)
            tiempo_anterior = tiempo_actual

    if not objeto_detectado:
        centro_anterior = None
        tiempo_anterior = None
        velocidad_suavizada = 0.0

    if tiempo_actual - ultimo_cambio >= intervalo_actualizacion:
        velocidad_mostrada = velocidad_suavizada
        ultimo_cambio = tiempo_actual

    cv2.rectangle(
        frame,
        (10, 10),
        (320, 55),
        (255, 255, 255),
        -1
    )

    cv2.putText(
        frame,
        f"Velocidad: {velocidad_mostrada:.1f} px/s",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 0),
        2
    )

    cv2.imshow("Proyecto Final Vision por Ordenador", frame)
    cv2.imshow("Mascara azul", mascara)
    cv2.imshow("Azul segmentado", azul_segmentado)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
