"Cámara del proyecto: lee la imagen, la pone en espejo y cuenta los FPS"
import cv2
import time


class Camara:
    def __init__(self, indice=0, ancho=1280, alto=720):
        self.cap = cv2.VideoCapture(indice, cv2.CAP_DSHOW)   # CAP_DSHOW: en Windows abre más rápido y sin avisos
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)
        self.t_anterior = time.perf_counter()
        self.fps = 0

    def read(self):
        # Devuelve (ok, imagen) igual que cv2.VideoCapture, pero ya en espejo y contando los FPS
        ok, frame = self.cap.read()
        if not ok:
            return False, None

        # Espejo horizontal (para que se vea como un espejo, no como una cámara de seguridad)
        frame = cv2.flip(frame, 1)

        # FPS suavizados: así el número no salta tanto de una imagen a otra
        ahora = time.perf_counter()
        self.fps = 0.9 * self.fps + 0.1 * (1 / max(ahora - self.t_anterior, 1e-6))
        self.t_anterior = ahora
        return True, frame

    def pintar_fps(self, frame):
        # Recuadro blanco con borde negro y los FPS en verde, abajo a la izquierda
        letra, tamano, grosor = cv2.FONT_HERSHEY_SIMPLEX, 1, 2
        (ancho, alto), _ = cv2.getTextSize('FPS: 00', letra, tamano, grosor)
        margen = 10
        x, y = 20, frame.shape[0] - 20 - alto - 2 * margen
        esquina = (x + ancho + 2 * margen, y + alto + 2 * margen)
        cv2.rectangle(frame, (x, y), esquina, (255, 255, 255), -1)   # relleno blanco
        cv2.rectangle(frame, (x, y), esquina, (0, 0, 0), 2)          # borde negro
        cv2.putText(frame, f'FPS: {self.fps:.0f}', (x + margen, y + margen + alto), letra, tamano, (0, 150, 0), grosor)

    def release(self):
        self.cap.release()
