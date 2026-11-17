"Bloque de seguridad: contar dedos dentro del recuadro"
import cv2
import numpy as np
import time
from pathlib import Path
from collections import deque

# Color de la piel: Usamos la escala YCrCb, que trata la luminancia y el color por separado. Esto hace que sea más fácil separar la piel del fondo.
# (Brillo, Cantidad de rojo, Cantidad de azul)
PIEL_BAJO = np.array([0, 133, 77])
PIEL_ALTO = np.array([255, 173, 127])

# Recuadro donde hay que poner la mano: (x1, y1, x2, y2)
RECUADRO = (850, 150, 1200, 550)

# Secuencia
SECUENCIA = [5, 1, 2, 5]
TIEMPO_MANTENER = 1  # segundos
TIEMPO_CAMBIO = 5    # segundos de puño (con el candado abierto) para poner una contraseña nueva
N_VOTOS = 10         # imágenes que se usan para votar el número de dedos (quita los saltos sueltos)

BOTON = (80, 400, 380, 560)   # x1, y1, x2, y2 del botón JUGAR (a la izquierda, lejos de la cara)
TIEMPO_BOTON = 1              # segundos con la mano encima para pulsarlo

# Imágenes de los candados (se cargan una sola vez al arrancar)
CARPETA_ASSETS = Path(__file__).resolve().parent / 'assets'


def cargar_png(nombre, alto):
    # Lee el PNG con su transparencia y lo reduce a 'alto' píxeles sin deformarlo
    png = cv2.imread(str(CARPETA_ASSETS / nombre), cv2.IMREAD_UNCHANGED)
    ancho = int(png.shape[1] * alto / png.shape[0])
    return cv2.resize(png, (ancho, alto), interpolation=cv2.INTER_AREA)

def pegar_png(fondo, png, x, y):
    # Pega el PNG en el fondo con su esquina de arriba a la izquierda en (x, y), respetando la transparencia
    h, w = png.shape[:2]
    zona = fondo[y:y + h, x:x + w]
    alfa = png[:, :, 3:] / 255.0
    zona[:] = (png[:, :, :3] * alfa + zona * (1 - alfa)).astype(np.uint8)

CANDADO_CERRADO = cargar_png('candado_cerrado.png', 120)
CANDADO_ABIERTO = cargar_png('candado_abierto.png', 120)

def contar_dedos(mascara):
    # 1. La MANO = la mancha blanca más grande. Buscamos los contornos de la máscara y nos quedamos con el más grande.
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contornos) == 0:
        return None, None, None
    
    mano = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(mano) < 3000:          # Umbral: demasiado pequeña para ser una mano
        return None, None, None
    if cv2.contourArea(mano) > 0.9 * mascara.size:   # casi todo el recuadro es "piel": no es una mano (fondo o luz)
        return None, None, None

    solo_mano = np.zeros_like(mascara)  # Transformamos la máscara a una imagen en blanco y negro donde solo está la mano
    cv2.drawContours(solo_mano, [mano], -1, 255, -1)

    # 2. Centro de la palma: Calculamos las distancias con el borde negro más cercano para cada pixel
    distancias = cv2.distanceTransform(solo_mano, cv2.DIST_L2, 5)
    _, radio_palma, _, centro = cv2.minMaxLoc(distancias)   # Calcula distancia y posición del pixel más interior (radio), y del más exterior (lo despreciamos)
    # Miramos con 3 círculos de distinto tamaño y nos quedamos con el que más dedos ve
    # (cerca de la base los dedos se tocan; más arriba se separan)
    mejor_dedos, mejor_radio = 0, int(1.7 * radio_palma)
    for factor in (1.7, 2.0, 2.3):
        radio = int(factor * radio_palma)

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

        if dedos > mejor_dedos:
            mejor_dedos, mejor_radio = dedos, radio

    return mejor_dedos, centro, mejor_radio

class Contrasena:
    def __init__(self, secuencia):
        self.secuencia = secuencia
        self.memoria = []            # números metidos bien (o los de la contraseña nueva)
        self.candidato = None        # número que estás aguantando
        self.t_inicio = 0            # desde cuándo lo aguantas
        self.ultimo = None           # último número aceptado (el siguiente tiene que ser distinto)
        self.desbloqueado = False    # ¿se ha metido bien la contraseña?
        self.modo = 'comprobar'      # 'comprobar' = meter la contraseña, 'nueva' = poner una nueva
        self.t_puno = None           # desde cuándo tienes el puño cerrado

    def actualizar(self, dedos):
        ahora = time.perf_counter()

        # 1. Sin mano: olvidamos el número que aguantabas y el último aceptado
        if dedos is None:
            self.ultimo = None
            self.candidato = None
            self.t_puno = None
            return None

        # Puño largo: con el candado abierto, 5 s de puño pasan al modo de contraseña nueva
        if dedos == 0:
            if self.t_puno is None:
                self.t_puno = ahora
            elif self.desbloqueado and self.modo == 'comprobar' and ahora - self.t_puno >= TIEMPO_CAMBIO:
                self.modo = 'nueva'
                self.memoria = []
                return 'nueva'
        else:
            self.t_puno = None

        # 2. Hay mano, pero los dedos son los mismos que antes: ignoramos
        if dedos == self.ultimo:
            self.candidato = None
            return None

        # 3. Número distinto al de antes: empezamos a contar el segundo desde cero
        if dedos != self.candidato:
            self.candidato = dedos
            self.t_inicio = ahora
            return None

        # 4. Mismo número, pero todavía no ha pasado el segundo
        if ahora - self.t_inicio < TIEMPO_MANTENER:
            return None

        # 5. Número aceptado: el siguiente tiene que ser distinto (o sacar la mano)
        self.ultimo = dedos
        self.candidato = None

        if dedos == 0:                                       # puño: se borra todo
            self.memoria = []
            return 'reinicio'

        # Modo contraseña nueva: guardamos los números hasta tener 4
        if self.modo == 'nueva':
            self.memoria.append(dedos)
            if len(self.memoria) == 4:
                self.secuencia = self.memoria
                self.memoria = []
                self.modo = 'comprobar'
                self.desbloqueado = False                    # se cierra para probar la nueva
                return 'cambiada'
            return 'aceptado'

        # Modo comprobar: ¿es el que tocaba?
        if dedos == self.secuencia[len(self.memoria)]:
            self.memoria.append(dedos)
            if len(self.memoria) == len(self.secuencia):     # ya están todos
                self.memoria = []
                self.desbloqueado = True
                return 'correcto'
            return 'aceptado'

        self.memoria = []                                    # no es el que tocaba
        return 'fallo'

    def progreso(self):
        # De 0 a 1: cuánto llevas aguantado el número actual (para la barrita)
        if self.candidato is None:
            return 0
        return min((time.perf_counter() - self.t_inicio) / TIEMPO_MANTENER, 1)

    def progreso_puno(self):
        # De 0 a 1: cuánto llevas de puño para cambiar la contraseña (solo con el candado abierto)
        if self.t_puno is None or not self.desbloqueado or self.modo != 'comprobar':
            return 0
        return min((time.perf_counter() - self.t_puno) / TIEMPO_CAMBIO, 1)
        
# Prueba: solo se ejecuta si lanzas este archivo
if __name__ == '__main__':
    from juego import jugar

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    x1, y1, x2, y2 = RECUADRO

    contra = Contrasena(SECUENCIA)
    mensaje, t_mensaje = '', 0        # último aviso (ACEPTADO, FALLO...) y cuándo salió
    votos = deque(maxlen=N_VOTOS)     # conteos de las últimas imágenes (los más viejos se van solos)
    
    t_boton = None                    # desde cuándo tienes la mano encima del botón

    clic = False                      # ¿se ha hecho clic en el botón?

    def raton(evento, x, y, flags, param):
        # OpenCV llama a esta función cada vez que haces algo con el ratón en la ventana
        global clic
        bx1, by1, bx2, by2 = BOTON
        if evento == cv2.EVENT_LBUTTONDOWN and bx1 <= x <= bx2 and by1 <= y <= by2:
            clic = True               # clic izquierdo dentro del botón

    cv2.namedWindow('Seguridad')
    cv2.setMouseCallback('Seguridad', raton)
    
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

        # Votación: nos quedamos con el número que más se repite en las últimas imágenes
        votos.append(dedos)
        dedos = max(set(votos), key=votos.count)

        resultado = contra.actualizar(dedos)
        if resultado is not None:
            print(resultado, contra.memoria, contra.secuencia)
            mensaje, t_mensaje = resultado.upper(), time.perf_counter()

        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
        if dedos is not None and centro is not None:
            cv2.circle(trozo, centro, radio, (0, 255, 255), 2)       # el círculo
            cv2.circle(trozo, centro, 5, (0, 0, 255), -1)            # el centro de la palma
            cv2.putText(frame, str(dedos), (x1, y1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)

        # Barrita debajo del recuadro: verde mientras aguantas un número, naranja mientras aguantas el puño para cambiar
        if contra.progreso_puno() > 0:
            lleno, color = int((x2 - x1) * contra.progreso_puno()), (0, 140, 255)
        else:
            lleno, color = int((x2 - x1) * contra.progreso()), (0, 255, 0)
        cv2.rectangle(frame, (x1, y2 + 15), (x1 + lleno, y2 + 40), color, -1)
        cv2.rectangle(frame, (x1, y2 + 15), (x2, y2 + 40), (255, 255, 255), 2)

        # Números metidos hasta ahora, en grande (por ejemplo: 5 1 _ _)
        huecos = [str(n) for n in contra.memoria] + ['_'] * (4 - len(contra.memoria))
        cv2.putText(frame, ' '.join(huecos), (x1, y2 + 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)

        # Aviso: el último resultado durante 1 s; si no, lo que toca hacer
        if time.perf_counter() - t_mensaje < 1:
            aviso = mensaje
        elif dedos is not None and dedos == contra.ultimo and dedos != 0:
            aviso = 'CAMBIA DE NUMERO'
        elif contra.modo == 'nueva':
            aviso = 'NUEVA CONTRASENA'
        elif contra.desbloqueado:
            aviso = 'PUNO 5 s: CAMBIAR'
        else:
            aviso = ''
        cv2.putText(frame, aviso, (x1, y2 + 150), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)

        # Candado arriba a la derecha: cerrado hasta meter bien la contraseña
        if contra.desbloqueado:
            pegar_png(frame, CANDADO_ABIERTO, 1140, 15)
        else:
            pegar_png(frame, CANDADO_CERRADO, 1140, 15)

        # Botón JUGAR: solo con el candado abierto (y si no estás poniendo una contraseña nueva)
        if contra.desbloqueado and contra.modo == 'comprobar':
            bx1, by1, bx2, by2 = BOTON
            zona = cv2.cvtColor(frame[by1:by2, bx1:bx2], cv2.COLOR_BGR2YCrCb)
            piel = cv2.inRange(zona, PIEL_BAJO, PIEL_ALTO)
            tapado = cv2.countNonZero(piel) / piel.size > 0.4   # ¿la mano tapa casi medio botón?

            if not tapado:
                t_boton = None
            elif t_boton is None:
                t_boton = time.perf_counter()

            # Se pulsa si llevas 1 s con la mano encima O si has hecho clic con el ratón
            mano_lista = t_boton is not None and time.perf_counter() - t_boton >= TIEMPO_BOTON
            if mano_lista or clic:
                cv2.destroyAllWindows()         # quitamos las ventanas de seguridad
                jugar(cap)                      # aquí se juega la partida entera (60 s)
                contra.desbloqueado = False     # al volver, el candado está cerrado otra vez
                t_boton, clic = None, False
                votos.clear()
                cv2.namedWindow('Seguridad')                # la ventana se borró: la creamos otra vez
                cv2.setMouseCallback('Seguridad', raton)    # y volvemos a escuchar el ratón
                continue

            # Dibujo del botón: se va rellenando de verde desde abajo mientras tienes la mano encima
            lleno = 0 if t_boton is None else min((time.perf_counter() - t_boton) / TIEMPO_BOTON, 1)
            cv2.rectangle(frame, (bx1, by2 - int((by2 - by1) * lleno)), (bx2, by2), (0, 200, 0), -1)
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), (255, 255, 255), 3)
            cv2.putText(frame, 'JUGAR', (bx1 + 50, by1 + 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
        else:
            t_boton, clic = None, False         # con el candado cerrado, los clics no cuentan

        cv2.imshow('Seguridad', frame)
        cv2.imshow('Mascara recuadro', mascara)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()