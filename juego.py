"Parte del juego: caras que aparecen y se pueden golpear"
import cv2
import random
from pathlib import Path
from seguridad import pegar_png
from deteccion_guante import Guante, actualizar_guantes
import time
import math
from rachas import Rachas, es_malo

CARPETA_JUEGO = Path(__file__).resolve().parent / 'imagenes' / 'caras'
ALTO_CARA = 200     # alto en píxeles de cada cara en pantalla

DURACION_JUEGO = 60  # segundos que dura la partida
TIEMPO_FASE = 20     # cada 20 s sale una cara más (1, luego 2, luego 3)

TIEMPO_CARAS = 1.5  # segundos que dura cada tanda de caras
INTENTOS = 20       # colocaciones al azar que probamos para quedarnos con la más separada
VELOCIDAD_GOLPE = 700  # px/s: el guante tiene que ir al menos así de rápido para que cuente como puñetazo

TEXTO_PONERSE = 'PONTE LOS GUANTES!'  # frase de la cuenta atrás (cv2.putText no pinta tildes, ni la ñ, ni ¡ ¿)
TIEMPO_PONERSE = 10                  # segundos de cuenta atrás antes de empezar la partida

def cargar_cara(ruta):
    # Lee el PNG con transparencia y lo deja con ALTO_CARA de alto sin deformarlo
    png = cv2.imread(str(ruta), cv2.IMREAD_UNCHANGED)
    ancho = int(png.shape[1] * ALTO_CARA / png.shape[0])
    return cv2.resize(png, (ancho, ALTO_CARA), interpolation=cv2.INTER_AREA)


# Diccionario de personajes: número -> (cara normal, cara golpeada)
PERSONAJES = {}
TIPO_PERSONAJE = {}
for i, ruta in enumerate(sorted((CARPETA_JUEGO / 'sin_fondo').glob('*.png'))):
    buena = cargar_cara(ruta)
    golpeada = cv2.imread(str(CARPETA_JUEGO / 'paliza' / ruta.name), cv2.IMREAD_UNCHANGED)
    golpeada = cv2.resize(golpeada, (buena.shape[1], buena.shape[0]), interpolation=cv2.INTER_AREA)
    PERSONAJES[i] = (buena, golpeada)
    TIPO_PERSONAJE[i] = es_malo(ruta.stem)

def nuevas_caras(ancho_pantalla, alto_pantalla, n_caras):
    # Dividimos la pantalla en N_CARAS franjas (columnas), una para cada cara: así nunca se pisan
    ancho_franja = ancho_pantalla // n_caras
    personajes = random.sample(list(PERSONAJES), n_caras)

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

def cuenta_atras(cap, guantes):
    # Antes de jugar: TIEMPO_PONERSE segundos con el mensaje para ponerse los guantes y un número que baja.
    # Devuelve False si se pulsa 'q' (no se juega)
    t_inicio = time.perf_counter()
    while True:
        ret, frame = cap.read()
        if not ret:
            return False

        quedan = TIEMPO_PONERSE - (time.perf_counter() - t_inicio)
        if quedan <= 0:
            return True

        # Recuadros de los guantes, para ver que los detecta bien antes de empezar
        actualizar_guantes(frame, guantes)
        for guante in guantes:
            if guante.recuadro is not None:
                x, y, w, h = guante.recuadro
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Mensaje y número de la cuenta atrás, centrados
        letra = cv2.FONT_HERSHEY_SIMPLEX
        (ancho, _), _ = cv2.getTextSize(TEXTO_PONERSE, letra, 2, 5)
        cv2.putText(frame, TEXTO_PONERSE, ((1280 - ancho) // 2, 250), letra, 2, (0, 255, 255), 5)
        numero = str(math.ceil(quedan))
        (ancho, _), _ = cv2.getTextSize(numero, letra, 6, 12)
        cv2.putText(frame, numero, ((1280 - ancho) // 2, 480), letra, 6, (255, 255, 255), 12)

        cap.pintar_fps(frame)
        cv2.imshow('Juego', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False


def jugar(cap):
    # Una partida entera (60 s) usando la cámara que ya está abierta
    guantes = [Guante(), Guante()]
    rachas = Rachas()
    if not cuenta_atras(cap, guantes):
        cv2.destroyWindow('Juego')
        return

    t_juego = time.perf_counter()   # momento en que empieza la partida
    caras = nuevas_caras(1280, 720, 2)
    t_caras = time.perf_counter()   # momento en que salió la tanda actual

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Buscamos los guantes ANTES de pintar las caras (si no, el azul de alguna foto podría confundirlo)
        actualizar_guantes(frame, guantes)

        # Cuánto llevamos de partida; a los 60 s se acaba
        transcurrido = time.perf_counter() - t_juego
        if transcurrido >= DURACION_JUEGO:
            break

        # Cada 20 s sale una cara más: 2, 3 y 4
        n_caras = 2 + int(transcurrido // TIEMPO_FASE)

        # Si la tanda actual lleva 1,5 s en pantalla, sacamos caras nuevas
        if time.perf_counter() - t_caras >= TIEMPO_CARAS:

            for cara in caras:
                if TIPO_PERSONAJE[cara['num']] and not cara['golpeada']:
                    rachas.reiniciar_racha()
                    break

            caras = nuevas_caras(1280, 720, n_caras)
            t_caras = time.perf_counter()

        # Golpe: el recuadro de un guante toca el recuadro (hitbox) de una cara y ese guante va rápido.
        # Basta con que se toquen un poco, no hace falta que el centro del guante caiga dentro
        for guante in guantes:
            if guante.recuadro is None or guante.velocidad <= VELOCIDAD_GOLPE:
                continue
            gx, gy, gw, gh = guante.recuadro
            for cara in caras:
                alto, ancho = PERSONAJES[cara['num']][0].shape[:2]
                se_tocan = (gx < cara['x'] + ancho and cara['x'] < gx + gw and
                            gy < cara['y'] + alto and cara['y'] < gy + gh)
                if se_tocan and not cara['golpeada']:
                    cara['golpeada'] = True

                    if TIPO_PERSONAJE[cara['num']]:
                        rachas.golpe_correcto()
                    else:
                        rachas.golpe_incorrecto()

        # Pintamos cada cara: la golpeada si ya le han dado, la normal si no
        for cara in caras:
            buena, golpeada = PERSONAJES[cara['num']]
            imagen = golpeada if cara['golpeada'] else buena
            pegar_png(frame, imagen, cara['x'], cara['y'])

        cv2.putText(frame, f'Tiempo: {DURACION_JUEGO - transcurrido:.0f}', (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        # Guantes: recuadro verde y velocidad de cada uno (en rojo cuando va lo bastante rápido para golpear)
        for i, guante in enumerate(guantes):
            if guante.recuadro is not None:
                x, y, w, h = guante.recuadro
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame, guante.centro, 6, (0, 0, 255), -1)
            color = (0, 0, 255) if guante.velocidad > VELOCIDAD_GOLPE else (255, 255, 255)
            cv2.putText(frame, f'Guante {i + 1}: {guante.velocidad:.0f} px/s', (20, 100 + 40 * i),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        rachas.dibujar(frame)
        cap.pintar_fps(frame)
        cv2.imshow('Juego', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):    # q: terminar la partida antes
            break

    cv2.destroyWindow('Juego')       # cerramos solo la ventana del juego (la cámara sigue abierta)

# Prueba: solo se ejecuta si lanzas este archivo
if __name__ == '__main__':
    from camara import Camara
    cap = Camara()
    jugar(cap)
    cap.release()
    cv2.destroyAllWindows()