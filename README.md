# Calibración de cámara

`calibracion_camara.py` usa el procedimiento del Lab 2 con las fotos de `../Fotos Calibracion Camara` y un tablero de 9 × 6 esquinas interiores.

Ejecutar `python calibracion_camara.py`. Muestra K, los coeficientes de distorsión, el error RMS y, si se pide, los extrínsecos [R | t] de cada foto relativos al tablero. Los parámetros quedan en las variables `intrinsics`, `dist_coeffs`, `rvecs`, `tvecs` y `extrinsics`.

`length` es el lado real de una casilla en mm (23), así que las traslaciones salen en mm.
