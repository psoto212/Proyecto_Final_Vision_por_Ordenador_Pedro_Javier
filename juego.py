"Parte del juego: caras que aparecen y se pueden golpear"
import cv2
import random
from pathlib import Path
from seguridad import pegar_png
import time
import math

CARPETA_JUEGO = Path(__file__).resolve().parent / 'fotos_juego'
ALTO_CARA = 200     # alto en píxeles de cada cara en pantalla
N_CARAS = 3         # cuántas caras salen a la vez
TIEMPO_CARAS = 1.5  # segundos que dura cada tanda de caras
INTENTOS = 20       # colocaciones al azar que probamos para quedarnos con la más separada

def cargar_cara(ruta):
    # Lee el PNG con transparencia y lo deja con ALTO_CARA de alto sin deformarlo
    png = cv2.imread(str(ruta), cv2.IMREAD_UNCHANGED)
    ancho = int(png.shape[1] * ALTO_CARA / png.shape[0])
    return cv2.resize(png, (ancho, ALTO_CARA), interpolation=cv2.INTER_AREA)


# Diccionario de personajes: número -> (cara normal, cara golpeada)
PERSONAJES = {}
for i, ruta in enumerate(sorted((CARPETA_JUEGO / 'sin_fondo').glob('*.png'))):
    buena = cargar_cara(ruta)
    golpeada = cv2.imread(str(CARPETA_JUEGO / 'paliza' / ruta.name), cv2.IMREAD_UNCHANGED)
    golpeada = cv2.resize(golpeada, (buena.shape[1], buena.shape[0]), interpolation=cv2.INTER_AREA)
    PERSONAJES[i] = (buena, golpeada)

def nuevas_caras(ancho_pantalla, alto_pantalla):
    # Dividimos la pantalla en N_CARAS franjas (columnas), una para cada cara: así nunca se pisan
    ancho_franja = ancho_pantalla // N_CARAS
    personajes = random.sample(list(PERSONAJES), N_CARAS)

    # Probamos varias colocaciones al azar y nos quedamos con la que deja las caras más separadas
    mejor_caras, mejor_distancia = None, -1
    for _ in range(INTENTOS):
        caras = []
        for franja, num in enumerate(personajes):
            ancho_cara = PERSONAJES[num][0].shape[1]
            x = franja * ancho_franja + random.randint(0, ancho_franja - ancho_cara)
            y = random.randint(0, alto_pantalla - ALTO_CARA)
            caras.append({'num': num, 'x': x, 'y': y, 'golpeada': False})

        # Distancia entre las dos caras más cercanas de esta colocación
        distancia = 10**9
        for i in range(len(caras)):
            for j in range(i + 1, len(caras)):
                d = math.dist((caras[i]['x'], caras[i]['y']), (caras[j]['x'], caras[j]['y']))
                distancia = min(distancia, d)

        # Si esta colocación las deja más separadas que la mejor hasta ahora, nos la quedamos
        if distancia > mejor_distancia:
            mejor_caras, mejor_distancia = caras, distancia

    return mejor_caras

if __name__ == '__main__':
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    caras = nuevas_caras(1280, 720)
    t_caras = time.perf_counter()   # momento en que salió la tanda actual

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        # Si la tanda actual lleva 1,5 s en pantalla, sacamos caras nuevas
        if time.perf_counter() - t_caras >= TIEMPO_CARAS:
            caras = nuevas_caras(1280, 720)
            t_caras = time.perf_counter()

        # Pintamos cada cara: la golpeada si ya le han dado, la normal si no
        for cara in caras:
            buena, golpeada = PERSONAJES[cara['num']]
            imagen = golpeada if cara['golpeada'] else buena
            pegar_png(frame, imagen, cara['x'], cara['y'])

        cv2.imshow('Juego', frame)
        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord(' '):        # ESPACIO: caras y sitios nuevos
            caras = nuevas_caras(1280, 720)
        elif tecla == 13:            # ENTER: las caras pasan a golpeadas
            for cara in caras:
                cara['golpeada'] = True
        elif tecla == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()