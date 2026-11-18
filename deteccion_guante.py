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
        self.recuadro = None          # (x, y, w, h) del guante, o None si no se ve
        self.centro = None            # centro del recuadro
        self.centro_anterior = None   # dónde estaba el guante en la imagen anterior
        self.t_anterior = None        # y en qué momento
        self.velocidad = 0.0          # velocidad suavizada en píxeles por segundo

    def actualizar(self, recuadro):
        # Recibe el recuadro de este guante en la imagen actual (o None si no se ve) y calcula su velocidad
        ahora = time.perf_counter()

        # Sin guante: olvidamos la posición anterior y la velocidad
        if recuadro is None:
            self.recuadro, self.centro = None, None
            self.centro_anterior, self.t_anterior, self.velocidad = None, None, 0.0
            return

        x, y, w, h = recuadro
        self.recuadro = recuadro
        self.centro = (x + w // 2, y + h // 2)

        # Velocidad = distancia recorrida desde la imagen anterior / tiempo que ha pasado
        if self.centro_anterior is not None:
            dt = ahora - self.t_anterior
            if dt > 0:
                velocidad = math.dist(self.centro, self.centro_anterior) / dt
                self.velocidad = ALPHA * velocidad + (1 - ALPHA) * self.velocidad

        self.centro_anterior, self.t_anterior = self.centro, ahora


def actualizar_guantes(frame, guantes):
    # Busca hasta 2 guantes (las 2 manchas azules más grandes) y actualiza cada uno. Devuelve la máscara
    mascara = mascara_azul(frame)
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contornos = [c for c in contornos if cv2.contourArea(c) >= AREA_MIN]
    contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:2]
    recuadros = sorted([cv2.boundingRect(c) for c in contornos])   # ordenados de izquierda a derecha

    if len(recuadros) == 2:
        # Dos guantes: el de la izquierda es guantes[0] y el de la derecha guantes[1]
        guantes[0].actualizar(recuadros[0])
        guantes[1].actualizar(recuadros[1])
    elif len(recuadros) == 1:
        # Un solo guante: se lo damos al que estaba más cerca en la imagen anterior (para no estropear su velocidad)
        x, y, w, h = recuadros[0]
        centro = (x + w // 2, y + h // 2)
        distancias = [math.dist(centro, g.centro_anterior) if g.centro_anterior else 10**9 for g in guantes]
        cerca = 0 if distancias[0] <= distancias[1] else 1
        guantes[cerca].actualizar(recuadros[0])
        guantes[1 - cerca].actualizar(None)
    else:
        guantes[0].actualizar(None)
        guantes[1].actualizar(None)

    return mascara


# Prueba: solo se ejecuta si lanzas este archivo
if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("No se ha podido abrir la camara")

    guantes = [Guante(), Guante()]
    intervalo_actualizacion = 0.2    # los números de la velocidad se refrescan cada 0,2 s para poder leerlos
    ultimo_cambio = time.perf_counter()
    velocidades_mostradas = [0.0, 0.0]

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        mascara = actualizar_guantes(frame, guantes)
        azul_segmentado = cv2.bitwise_and(frame, frame, mask=mascara)

        for guante in guantes:
            if guante.recuadro is not None:
                x, y, w, h = guante.recuadro
                cv2.circle(frame, guante.centro, 5, (0, 0, 255), -1)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if time.perf_counter() - ultimo_cambio >= intervalo_actualizacion:
            velocidades_mostradas = [g.velocidad for g in guantes]
            ultimo_cambio = time.perf_counter()

        cv2.rectangle(frame, (10, 10), (420, 90), (255, 255, 255), -1)
        for i, v in enumerate(velocidades_mostradas):
            cv2.putText(frame, f"Guante {i + 1}: {v:.1f} px/s", (20, 40 + 35 * i),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        cv2.imshow("Proyecto Final Vision por Ordenador", frame)
        cv2.imshow("Mascara azul", mascara)
        cv2.imshow("Azul segmentado", azul_segmentado)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
