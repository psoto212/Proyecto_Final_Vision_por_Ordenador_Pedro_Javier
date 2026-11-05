# Calibración de cámara

`calibracion_camara.py` usa el procedimiento del Lab 2 con las fotos de `../Fotos Calibración Camara` y un tablero de 9 × 6 esquinas interiores.

Ejecutar `python calibracion_camara.py`. Muestra K, los coeficientes de distorsión, el error RMS y los extrínsecos [R | t] de cada foto relativos al tablero. Los parámetros quedan en las variables `intrinsics`, `dist_coeffs`, `rvecs`, `tvecs` y `extrinsics`.

Cambiar `length` por el lado real de una casilla en mm para obtener traslaciones en mm. Con `length = 1.0` se expresan en casillas.
