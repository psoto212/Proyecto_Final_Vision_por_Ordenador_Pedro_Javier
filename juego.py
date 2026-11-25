
"Parte del juego: caras que aparecen y se pueden golpear"

import cv2
import random
from pathlib import Path
from seguridad import pegar_png
from deteccion_guante import Guante, actualizar_guantes
from rachas import Rachas, es_malo
from record import cargar_record, actualizar_record
import time
import math

CARPETA_JUEGO = Path(__file__).resolve().parent / 'imagenes' / 'caras'
ALTO_CARA = 200

DURACION_JUEGO = 60
TIEMPO_FASE = 20
TIEMPO_CARAS = 1.5
INTENTOS = 20
VELOCIDAD_GOLPE = 700

TEXTO_PONERSE = 'PONTE LOS GUANTES!'
TIEMPO_PONERSE = 10


def cargar_cara(ruta):
    png = cv2.imread(str(ruta), cv2.IMREAD_UNCHANGED)

    if png is None:
        raise FileNotFoundError(f'No se pudo cargar la imagen: {ruta}')

    ancho = int(png.shape[1] * ALTO_CARA / png.shape[0])
    return cv2.resize(
        png, (ancho, ALTO_CARA),
        interpolation=cv2.INTER_AREA
    )


PERSONAJES = {}
TIPO_PERSONAJE = {}

for i, ruta in enumerate(sorted((CARPETA_JUEGO / 'sin_fondo').glob('*.png'))):
    buena = cargar_cara(ruta)

    ruta_golpeada = CARPETA_JUEGO / 'paliza' / ruta.name
    golpeada = cv2.imread(str(ruta_golpeada), cv2.IMREAD_UNCHANGED)

    if golpeada is None:
        raise FileNotFoundError(
            f'No se pudo cargar la imagen golpeada: {ruta_golpeada}'
        )

    golpeada = cv2.resize(
        golpeada,
        (buena.shape[1], buena.shape[0]),
        interpolation=cv2.INTER_AREA
    )

    PERSONAJES[i] = (buena, golpeada)
    TIPO_PERSONAJE[i] = es_malo(ruta.stem)


def nuevas_caras(ancho_pantalla, alto_pantalla, n_caras):
    ancho_franja = ancho_pantalla // n_caras
    personajes = random.sample(list(PERSONAJES), n_caras)

    mejor_caras, mejor_distancia = [], -1

    for _ in range(INTENTOS):
        caras = []

        for franja, num in enumerate(personajes):
            ancho_cara = PERSONAJES[num][0].shape[1]

            x = franja * ancho_franja + random.randint(
                0, ancho_franja - ancho_cara
            )

            y = random.randint(0, alto_pantalla - ALTO_CARA)

            caras.append({
                'num': num,
                'x': x,
                'y': y,
                'golpeada': False
            })

        distancia = 10**9

        for i in range(len(caras)):
            for j in range(i + 1, len(caras)):
                d = math.dist(
                    (caras[i]['x'], caras[i]['y']),
                    (caras[j]['x'], caras[j]['y'])
                )
                distancia = min(distancia, d)

        if distancia > mejor_distancia:
            mejor_caras, mejor_distancia = caras, distancia

    return mejor_caras


def cuenta_atras(cap, guantes):
    t_inicio = time.perf_counter()

    while True:
        ret, frame = cap.read()

        if not ret:
            return False

        quedan = TIEMPO_PONERSE - (time.perf_counter() - t_inicio)

        if quedan <= 0:
            return True

        actualizar_guantes(frame, guantes)

        for guante in guantes:
            if guante.recuadro is not None:
                x, y, w, h = guante.recuadro

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0), 2
                )

        letra = cv2.FONT_HERSHEY_SIMPLEX

        (ancho, _), _ = cv2.getTextSize(
            TEXTO_PONERSE, letra, 2, 5
        )

        cv2.putText(
            frame, TEXTO_PONERSE,
            ((1280 - ancho) // 2, 250),
            letra, 2, (0, 255, 255), 5
        )

        numero = str(math.ceil(quedan))

        (ancho, _), _ = cv2.getTextSize(
            numero, letra, 6, 12
        )

        cv2.putText(
            frame, numero,
            ((1280 - ancho) // 2, 480),
            letra, 6, (255, 255, 255), 12
        )

        cap.pintar_fps(frame)
        cv2.imshow('Juego', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            return False


def jugar(cap):
    guantes = [Guante(), Guante()]
    rachas = Rachas()

    # Cargar el record guardado en el ordenador
    record = cargar_record()

    if not cuenta_atras(cap, guantes):
        cv2.destroyWindow('Juego')
        return

    t_juego = time.perf_counter()
    caras = nuevas_caras(1280, 720, 2)
    t_caras = time.perf_counter()

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        actualizar_guantes(frame, guantes)

        transcurrido = time.perf_counter() - t_juego

        if transcurrido >= DURACION_JUEGO:
            break

        n_caras = 2 + int(transcurrido // TIEMPO_FASE)

        # Cambiar las caras cada 1,5 segundos
        if time.perf_counter() - t_caras >= TIEMPO_CARAS:

            # Perder la racha si escapa un malo
            for cara in caras:
                if TIPO_PERSONAJE[cara['num']] and not cara['golpeada']:
                    rachas.reiniciar_racha()
                    break

            caras = nuevas_caras(1280, 720, n_caras)
            t_caras = time.perf_counter()

        # Detectar golpes con ambos guantes
        for guante in guantes:
            if guante.recuadro is None or guante.velocidad <= VELOCIDAD_GOLPE:
                continue

            gx, gy, gw, gh = guante.recuadro

            for cara in caras:
                alto, ancho = PERSONAJES[cara['num']][0].shape[:2]

                se_tocan = (
                    gx < cara['x'] + ancho
                    and cara['x'] < gx + gw
                    and gy < cara['y'] + alto
                    and cara['y'] < gy + gh
                )

                if se_tocan and not cara['golpeada']:
                    cara['golpeada'] = True

                    if TIPO_PERSONAJE[cara['num']]:
                        rachas.golpe_correcto()
                    else:
                        rachas.golpe_incorrecto()

        # Mostrar las caras
        for cara in caras:
            buena, golpeada = PERSONAJES[cara['num']]
            imagen = golpeada if cara['golpeada'] else buena
            pegar_png(frame, imagen, cara['x'], cara['y'])

        # Tiempo restante
        cv2.putText(
            frame,
            f'Tiempo: {DURACION_JUEGO - transcurrido:.0f}',
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2, (0, 0, 255), 3
        )

        # Mostrar guantes y velocidades
        for i, guante in enumerate(guantes):
            if guante.recuadro is not None:
                x, y, w, h = guante.recuadro

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0), 2
                )

                if guante.centro is not None:
                    cv2.circle(
                        frame,
                        guante.centro,
                        6,
                        (0, 0, 255),
                        -1
                    )

            color = (
                (0, 0, 255)
                if guante.velocidad > VELOCIDAD_GOLPE
                else (255, 255, 255)
            )

            cv2.putText(
                frame,
                f'Guante {i + 1}: {guante.velocidad:.0f} px/s',
                (20, 100 + 40 * i),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9, color, 2
            )

        # Puntuacion y rachas
        rachas.dibujar(frame)

        # Actualizar record historico
        record = actualizar_record(rachas.puntuacion, record)

        # Dibujar record debajo del marcador
        x = frame.shape[1] - 230
        y = 95

        cv2.rectangle(
            frame,
            (x, y),
            (x + 215, y + 45),
            (255, 255, 255),
            -1
        )

        cv2.rectangle(
            frame,
            (x, y),
            (x + 215, y + 45),
            (0, 0, 0),
            2
        )

        cv2.putText(
            frame,
            f'Record: {record}',
            (x + 10, y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            2
        )

        cap.pintar_fps(frame)
        cv2.imshow('Juego', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyWindow('Juego')


if __name__ == '__main__':
    from camara import Camara

    cap = Camara()
    jugar(cap)
    cap.release()
    cv2.destroyAllWindows()
