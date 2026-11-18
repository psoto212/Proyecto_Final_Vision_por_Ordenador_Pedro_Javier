"Programa principal: primero la seguridad y, al pulsar JUGAR, el juego"
import cv2
from seguridad import Contrasena, SECUENCIA, pantalla_seguridad
from juego import jugar

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# La contraseña se crea una sola vez: si la cambias, se mantiene entre partidas
contra = Contrasena(SECUENCIA)

# Seguridad -> (pulsas JUGAR) -> juego -> vuelta a seguridad ... hasta pulsar 'q' en seguridad
while pantalla_seguridad(cap, contra):
    jugar(cap)

cap.release()
cv2.destroyAllWindows()
