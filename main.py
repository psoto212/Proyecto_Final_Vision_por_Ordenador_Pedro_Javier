"Programa principal: primero la seguridad y, al pulsar JUGAR, el juego"
import cv2
from camara import Camara
from seguridad import Contrasena, SECUENCIA, pantalla_seguridad
from juego import jugar

# La cámara ya da la imagen en espejo y cuenta los FPS (se pintan en cada pantalla)
cap = Camara()

# La contraseña se crea una sola vez: si la cambias, se mantiene entre partidas
contra = Contrasena(SECUENCIA)

# Seguridad -> (pulsas JUGAR) -> juego -> vuelta a seguridad ... hasta pulsar 'q' en seguridad
while pantalla_seguridad(cap, contra):
    jugar(cap)

cap.release()
cv2.destroyAllWindows()
