"Generacion del esqueleto del programa"
import cv2
import numpy as np
from pathlib import Path
import time

#IMPORTAMOS LOS DATOS DE CALIBRACION (ruta relativa a este archivo, así funciona desde cualquier carpeta)
datos = np.load(Path(__file__).resolve().parent / 'resultados_calibracion' / 'calibracion.npz')
K, dist = datos['K'], datos['dist']


def main(camera_index=0, width=1280, height=720):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # Use CAP_DSHOW for Windows to avoid warning messages
    if not cap.isOpened():
        print(f"Could not open the camera (index {camera_index}).")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Preparamos una sola vez el "mapa" que dice a dónde va cada píxel para quitar la deformación.
    map_x, map_y = cv2.initUndistortRectifyMap(K, dist, None, K, (width, height), cv2.CV_16SC2)

    window_name = "Live Camera - press 'q' to quit"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # resizable window

    t_anterior = time.perf_counter()    #Da la hora en segundos con decimales, de alta precisión
    fps = 0

    # Control de estado: en qué pantalla estamos. Puede ser 'seguridad', 'juego' o 'resultado'
    estado = "seguridad"

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("No frame received (the camera may have been disconnected).")
                break

            # Quitamos la deformación de la lente (antes del espejo, porque se calibró sin espejo)
            frame = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)

            # Espejo horizontal (para que se vea como un espejo, no como una cámara de seguridad)
            frame = cv2.flip(frame, 1)

            # Calculamos los FPS para imprimirlos por pantalla
            t_ahora = time.perf_counter()
            fps = 0.9 * fps + 0.1 * (1 / (t_ahora - t_anterior))
            t_anterior = t_ahora

            texto = f'FPS: {fps:.0f}'
            letra, tamano, grosor = cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3
            (ancho, alto), _ = cv2.getTextSize('FPS: 00', letra, tamano, grosor)
            x, y, margen = 20, 20, 12
            esquina = (x + ancho + 2 * margen, y + alto + 2 * margen)

            cv2.rectangle(frame, (x, y), esquina, (255, 255, 255), -1)   # relleno blanco
            cv2.rectangle(frame, (x, y), esquina, (0, 0, 0), 3)          # borde negro
            cv2.putText(frame, texto, (x + margen, y + margen + alto), letra, tamano, (0, 150, 0), grosor)

            # Imprime en pantalla según el estado de juego
            if estado == 'seguridad':
                texto = "PANTALLA DE SEGURIDAD: Introduce la contraseña"
            elif estado == "juego":
                texto = "PANTALLA DE JUEGO: Bienvenido al juego"
            elif estado == "resultado":
                texto = "PANTALLA DE RESULTADO:"

            cv2.putText(frame, texto, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.putText(frame, 'n: siguiente pantalla   q: salir', (20, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Display the frame
            cv2.imshow(window_name, frame)

            # Wait 1 ms for a key; exit with 'q' or ESC
            key = cv2.waitKey(1) & 0xFF

            # Máquina de estados
            # Con la tecla 'n' pasamos a la siguiente pantalla
            if key == ord('n'):
                if estado == 'seguridad':
                    estado = 'juego'
                elif estado == 'juego':
                    estado = 'resultado'
                elif estado == 'resultado':
                    estado = 'seguridad'

            elif key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    
    main(camera_index=0, width=1280, height=720)