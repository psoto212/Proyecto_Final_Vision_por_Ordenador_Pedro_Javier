
"Programa principal: seguridad, juego y pantalla final"

import cv2
from camara import Camara
from seguridad import Contrasena, SECUENCIA, pantalla_seguridad
from juego import jugar
from fin_partida import fin_partida
from record import cargar_record

cap = Camara()
contra = Contrasena(SECUENCIA)

continuar = True

while continuar and pantalla_seguridad(cap, contra):

    while continuar:
        puntos = jugar(cap)

        if puntos is None:
            continuar = False
            break

        record = cargar_record()

        if not fin_partida(cap, puntos, record):
            continuar = False

cap.release()
cv2.destroyAllWindows()
