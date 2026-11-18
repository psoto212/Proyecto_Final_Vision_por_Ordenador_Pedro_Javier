import cv2
import numpy as np
import time
import math

AZUL_MIN = np.array([85, 40, 30], dtype=np.uint8)    # color azul del guante en HSV
AZUL_MAX = np.array([140, 255, 255], dtype=np.uint8)
AREA_MIN = 1000      # manchas azules más pequeñas no cuentan como guante
ALPHA = 0.5          # suavizado de la velocidad (más alto = reacciona antes, pero tiembla más)


def mascara_azul(frame):
    # Blanco donde hay azul, negro en el resto (con erosión y dilatación para quitar puntitos)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mascara = cv2.inRange(hsv, AZUL_MIN, AZUL_MAX)
    kernel = np.ones((5, 5), np.uint8)
    mascara = cv2.erode(mascara, kernel, iterations=1)
    mascara = cv2.dilate(mascara, kernel, iterations=1)
    return mascara


class Guante:
    def __init__(self):
        self.centro_anterior = None   # dónde estaba el guante en la imagen anterior
        self.t_anterior = None        # y en qué momento
        self.velocidad = 0.0          # velocidad suavizada en píxeles por segundo

    def actualizar(self, frame):
        # Busca el guante en la imagen. Devuelve (recuadro, centro, mascara);
        # si no hay guante, recuadro y centro son None. La velocidad queda en self.velocidad
        mascara = mascara_azul(frame)
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ahora = time.perf_counter()

        # Sin guante: olvidamos la posición anterior y la velocidad
        if len(contornos) == 0 or cv2.contourArea(max(contornos, key=cv2.contourArea)) < AREA_MIN:
            self.centro_anterior, self.t_anterior, self.velocidad = None, None, 0.0
            return None, None, mascara

        # El guante es la mancha azul más grande
        x, y, w, h = cv2.boundingRect(max(contornos, key=cv2.contourArea))
        centro = (x + w // 2, y + h // 2)

        # Velocidad = distancia recorrida desde la imagen anterior / tiempo que ha pasado
        if self.centro_anterior is not None:
            dt = ahora - self.t_anterior
            if dt > 0:
                velocidad = math.dist(centro, self.centro_anterior) / dt
                self.velocidad = ALPHA * velocidad + (1 - ALPHA) * self.velocidad

        self.centro_anterior, self.t_anterior = centro, ahora
        return (x, y, w, h), centro, mascara


# Prueba: solo se ejecuta si lanzas este archivo
if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("No se ha podido abrir la camara")

    guante = Guante()
    intervalo_actualizacion = 0.2    # el número de la velocidad se refresca cada 0,2 s para poder leerlo
    ultimo_cambio = time.perf_counter()
    velocidad_mostrada = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        recuadro, centro, mascara = guante.actualizar(frame)
        azul_segmentado = cv2.bitwise_and(frame, frame, mask=mascara)

        if recuadro is not None:
            x, y, w, h = recuadro
            cv2.circle(frame, centro, 5, (0, 0, 255), -1)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if time.perf_counter() - ultimo_cambio >= intervalo_actualizacion:
            velocidad_mostrada = guante.velocidad
            ultimo_cambio = time.perf_counter()

        cv2.rectangle(frame, (10, 10), (320, 55), (255, 255, 255), -1)
        cv2.putText(frame, f"Velocidad: {velocidad_mostrada:.1f} px/s", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        cv2.imshow("Proyecto Final Vision por Ordenador", frame)
        cv2.imshow("Mascara azul", mascara)
        cv2.imshow("Azul segmentado", azul_segmentado)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
