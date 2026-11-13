"Bloque de seguridad: contar dedos dentro del recuadro"
import cv2
import numpy as np
import time

# Color de la piel: Usamos la escala YCrCb, que trata la luminancia y el color por separado. Esto hace que sea más fácil separar la piel del fondo.
# (Brillo, Cantidad de rojo, Cantidad de azul)
PIEL_BAJO = np.array([0, 133, 77])
PIEL_ALTO = np.array([255, 173, 127])

# Recuadro donde hay que poner la mano: (x1, y1, x2, y2)
RECUADRO = (850, 150, 1200, 550)

# Secuencia
SECUENCIA = [5, 1, 2, 5]
TIEMPO_MANTENER = 1.5  # segundos

# Lista de seguimiento
memoria = []

def contar_dedos(mascara):
    # 1. La MANO = la mancha blanca más grande. Buscamos los contornos de la máscara y nos quedamos con el más grande.
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contornos) == 0:
        return None, None, None
    
    mano = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(mano) < 3000:          # Umbral: demasiado pequeña para ser una mano
        return None, None, None
    
    solo_mano = np.zeros_like(mascara)  # Transformamos la máscara a una imagen en blanco y negro donde solo está la mano
    cv2.drawContours(solo_mano, [mano], -1, 255, -1)

    # 2. Centro de la palma: Calculamos las distancias con el borde negro más cercano para cada pixel
    distancias = cv2.distanceTransform(solo_mano, cv2.DIST_L2, 5)
    _, radio_palma, _, centro = cv2.minMaxLoc(distancias)   # Calcula distancia y posición del pixel más interior (radio), y del más exterior (lo despreciamos)
    radio = int(1.7 * radio_palma) # Usamos un circulo un poco más mayor que la palma, pero en donde corte los dedos

    # La idea es dibujar un punto por cada grado del circulo: como un reloj con 360 minutos
    # 3. Creación del circulo
    angulos = np.radians(np.arange(360))
    xs = (centro[0] + radio * np.cos(angulos)).astype(int)  # Coordenadas en x
    ys = (centro[1] - radio * np.sin(angulos)).astype(int)  # Coordenadas en y

    # 4. ¿Cada punto del círculo cae en la mano? (los que se salen de la imagen cuentan como negro)
    alto, ancho = mascara.shape
    dentro = (xs >= 0) & (xs < ancho) & (ys >= 0) & (ys < alto)
    blanco = np.zeros(360, dtype=bool)
    blanco[dentro] = solo_mano[ys[dentro], xs[dentro]] > 0

    # 5. No miramos la parte de abajo, que es por donde entra la muñeca
    blanco[225:315] = False

    # 6. Contamos los trozos blancos seguidos (cada uno es un dedo)
    blanco = np.roll(blanco, -270)    # empezamos a recorrer desde abajo
    dedos, largo = 0, 0
    for es_blanco in blanco:
        if es_blanco:
            largo += 1
        else:
            if largo >= 5:            # trozos de menos de 5 grados son ruido
                dedos += 1
            largo = 0
    return dedos, centro, radio

class Contrasena:
    def __init__(self, secuencia):
        self.secuencia = secuencia
        self.memoria=[]
        self.candidato=None
        self.tiempo_inicio=None
        self.mano_fuera=True

    def actualizar(self, dedos):
        ahora = time.perf_counter()

        # 1. Sin mano: apuntamos que ha salido (da permiso para el siguiente número)
        if dedos is None:
            self.mano_fuera = True
            self.candidato = None
            return None

        # 2. Hay mano, pero no la has sacado desde el último número: ignoramos
        if not self.mano_fuera:
            return None

        # 3. Número distinto al de antes: empezamos a contar el segundo desde cero
        if dedos != self.candidato:
            self.candidato = dedos
            self.t_inicio = ahora
            return None

        # 4. Mismo número, pero todavía no ha pasado el segundo
        if ahora - self.t_inicio < TIEMPO_MANTENER:
            return None

        # 5. Número aceptado: a partir de aquí hay que sacar la mano para el siguiente
        self.mano_fuera = False
        self.candidato = None

        if dedos == 0:                                       # puño: se borra todo
            self.memoria = []
            return 'reinicio'

        if dedos == self.secuencia[len(self.memoria)]:       # es el que tocaba
            self.memoria.append(dedos)
            if len(self.memoria) == len(self.secuencia):     # ya están todos
                self.memoria = []
                return 'correcto'
            return 'aceptado'

        self.memoria = []                                    # no es el que tocaba
        return 'fallo'

    def progreso(self):
        # De 0 a 1: cuánto llevas aguantado el número actual (para la barrita)
        if self.candidato is None:
            return 0
        return min((time.perf_counter() - self.t_inicio) / TIEMPO_MANTENER, 1)
        
# Prueba: solo se ejecuta si lanzas este archivo
if __name__ == '__main__':
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    x1, y1, x2, y2 = RECUADRO

    contra = Contrasena(SECUENCIA)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)

        # Solo miramos dentro del recuadro
        trozo = frame[y1:y2, x1:x2]
        ycrcb = cv2.cvtColor(trozo, cv2.COLOR_BGR2YCrCb)
        mascara = cv2.inRange(ycrcb, PIEL_BAJO, PIEL_ALTO)
        nucleo = np.ones((5, 5), np.uint8)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, nucleo)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, nucleo)

        dedos, centro, radio = contar_dedos(mascara)

        resultado = contra.actualizar(dedos)
        if resultado is not None:
            print(resultado, contra.memoria)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
        if dedos is not None:
            cv2.circle(trozo, centro, radio, (0, 255, 255), 2)       # el círculo
            cv2.circle(trozo, centro, 5, (0, 0, 255), -1)            # el centro de la palma
            cv2.putText(frame, str(dedos), (x1, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)

        cv2.imshow('Seguridad', frame)
        cv2.imshow('Mascara recuadro', mascara)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()