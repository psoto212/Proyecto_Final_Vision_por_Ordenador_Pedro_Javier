
import cv2
import time
from seguridad import PIEL_BAJO, PIEL_ALTO

TIEMPO_BOTON = 1

BOTON_JUGAR = (100, 400, 550, 550)
BOTON_SALIR = (730, 400, 1180, 550)


def fin_partida(cap, puntos, record):
    t_jugar = None
    t_salir = None

    while True:
        ret, frame = cap.read()
        if not ret:
            return False

        # Detectamos la mano antes de dibujar los botones
        def mano_encima(boton):
            x1, y1, x2, y2 = boton
            zona = frame[y1:y2, x1:x2]
            ycrcb = cv2.cvtColor(zona, cv2.COLOR_BGR2YCrCb)
            piel = cv2.inRange(ycrcb, PIEL_BAJO, PIEL_ALTO)
            return cv2.countNonZero(piel) / piel.size > 0.4

        ahora = time.perf_counter()

        if mano_encima(BOTON_JUGAR):
            if t_jugar is None:
                t_jugar = ahora
        else:
            t_jugar = None

        if mano_encima(BOTON_SALIR):
            if t_salir is None:
                t_salir = ahora
        else:
            t_salir = None

        # Elegir manteniendo la mano un segundo
        if t_jugar is not None and ahora - t_jugar >= TIEMPO_BOTON:
            cv2.destroyWindow('Fin de partida')
            return True

        if t_salir is not None and ahora - t_salir >= TIEMPO_BOTON:
            cv2.destroyWindow('Fin de partida')
            return False

        # Oscurecer el fondo
        frame = cv2.addWeighted(
            frame, 0.35,
            frame * 0, 0.65, 0
        )

        cv2.putText(frame, 'FIN DE PARTIDA', (345, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)

        cv2.putText(frame, f'Puntos: {puntos}', (455, 245),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)

        cv2.putText(frame, f'Record: {record}', (455, 315),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)

        # Botones con barra de progreso
        for boton, texto, inicio in [
            (BOTON_JUGAR, 'VOLVER A JUGAR', t_jugar),
            (BOTON_SALIR, 'SALIR', t_salir)
        ]:
            x1, y1, x2, y2 = boton

            progreso = 0 if inicio is None else min(
                (ahora - inicio) / TIEMPO_BOTON, 1
            )

            alto = int((y2 - y1) * progreso)

            cv2.rectangle(frame, (x1, y2 - alto),
                          (x2, y2), (0, 180, 0), -1)

            cv2.rectangle(frame, (x1, y1), (x2, y2),
                          (255, 255, 255), 3)

            (ancho, _), _ = cv2.getTextSize(
                texto, cv2.FONT_HERSHEY_SIMPLEX, 1, 2
            )

            cv2.putText(
                frame, texto,
                (x1 + (x2 - x1 - ancho) // 2, y1 + 90),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 255, 255), 2
            )

        cap.pintar_fps(frame)
        cv2.imshow('Fin de partida', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyWindow('Fin de partida')
            return False
