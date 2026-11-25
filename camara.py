"Cámara del proyecto: lee la imagen, quita la deformación de la lente, la pone en espejo y cuenta los FPS"
import cv2
import numpy as np
import time
from pathlib import Path

# Datos de la calibración (los guarda calibracion_camara.py, que se ejecuta antes, offline)
CALIBRACION = Path(__file__).resolve().parent / 'calibracion.npz'


class Camara:
    def __init__(self, indice=0, ancho=1280, alto=720):
        self.cap = cv2.VideoCapture(indice, cv2.CAP_DSHOW)   # CAP_DSHOW: en Windows abre más rápido y sin avisos
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)

        # Preparamos una sola vez el "mapa" que dice a dónde va cada píxel para quitar la deformación.
        # Así, en cada imagen solo hay que aplicar el mapa (remap), que es mucho más rápido que cv2.undistort
        datos = np.load(CALIBRACION)
        self.map_x, self.map_y = cv2.initUndistortRectifyMap(datos['K'], datos['dist'], None, datos['K'],
                                                             (ancho, alto), cv2.CV_16SC2)
        self.t_anterior = time.perf_counter()
        self.fps = 0

    def read(self):
        # Devuelve (ok, imagen) igual que cv2.VideoCapture, pero ya sin deformación, en espejo y contando los FPS
        ok, frame = self.cap.read()
        if not ok:
            return False, None

        # Quitamos la deformación de la lente (antes del espejo, porque se calibró sin espejo)
        frame = cv2.remap(frame, self.map_x, self.map_y, cv2.INTER_LINEAR)

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
        texto = f'FPS: {self.fps:.0f}'
        (ancho, alto), _ = cv2.getTextSize(texto, letra, tamano, grosor)
        margen = 10
        x, y = 20, frame.shape[0] - 20 - alto - 2 * margen
        esquina = (x + ancho + 2 * margen, y + alto + 2 * margen)
        cv2.rectangle(frame, (x, y), esquina, (255, 255, 255), -1)   # relleno blanco
        cv2.rectangle(frame, (x, y), esquina, (0, 0, 0), 2)          # borde negro
        cv2.putText(frame, texto, (x + margen, y + margen + alto), letra, tamano, (0, 150, 0), grosor)

    def release(self):
        self.cap.release()
