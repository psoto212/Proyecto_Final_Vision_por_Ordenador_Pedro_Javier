import cv2
import numpy as np
from pathlib import Path

## CARGAMOS LAS IMÁGENES Y DEFINIMOS LOS PARÁMETROS DE LA CALIBRACIÓN
base_dir = Path(__file__).resolve().parent
imgs_path = sorted((base_dir.parent / 'Fotos Calibracion Camara').glob('*.jpg'))
chessboard_shape = (9, 6)  # Esquinas interiores de nuestro tablero.
length = 23  # Longitud de cada cuadro del tablero en milímetros.

def get_chessboard_points(chessboard_shape, dx, dy):
    cols, rows = chessboard_shape
    points = []
    for y in range(rows):
        for x in range(cols):
            points.append([x * dx, y * dy, 0])
    return np.array(points, dtype=np.float32)

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
valid_corners = []
valid_chessboard_points = []
valid_paths = []
image_size = None
detecciones_dir = base_dir / 'resultados_calibracion' / 'detecciones'
detecciones_dir.mkdir(parents=True, exist_ok=True)

for path in imgs_path:

    img = cv2.imread(str(path))
    if img is None:
        print(f'No se pudo cargar {path.name}')
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    size = (gray.shape[1], gray.shape[0])
    if image_size is not None and size != image_size:
        raise ValueError('Todas las fotos deben tener la misma resolución.')

    res, corner = cv2.findChessboardCorners(gray, chessboard_shape)
    if res:
        refined = cv2.cornerSubPix(gray, corner, (5, 5), (-1, -1), criteria)
        valid_corners.append(refined)
        valid_chessboard_points.append(
            get_chessboard_points(chessboard_shape, length, length)
        )
        valid_paths.append(path)
        image_size = size
        # Guardamos la foto con las esquinas detectadas dibujadas.
        cv2.drawChessboardCorners(img, chessboard_shape, refined, res)
        cv2.imwrite(str(detecciones_dir / path.name), img)
    else:
        print(f'No se ha detectado el tablero en {path.name}')

if len(valid_corners) < 3:
    raise ValueError('Se necesitan al menos 3 fotos con el tablero detectado.')

rms, intrinsics, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    valid_chessboard_points, valid_corners, image_size, None, None
)

#PARA GUARDAR LOS PARÁMETROS DE CALIBRACIÓN EN UN ARCHIVO .npz, Y NO TENER QUE CALIBRAR CADA VEZ QUE EJECUTEMOS EL PROGRAMA
np.savez(base_dir / 'calibracion.npz', K=intrinsics, dist=dist_coeffs)

# Extrínsecos [R | t], uno por foto, relativos al tablero.
extrinsics = [
    np.hstack((cv2.Rodrigues(rvec)[0], tvec))
    for rvec, tvec in zip(rvecs, tvecs)
]

print(f'Fotos válidas: {len(valid_corners)} de {len(imgs_path)}')
print('\nIntrínsecos (K):\n', intrinsics)
print('\nCoeficientes de distorsión:\n', dist_coeffs)
print('\nError RMS:', rms)

bool_extinse = input('¿Desea imprimir los extrínsecos? (s/n): ')
if bool_extinse.lower() == 's':
    for path, extrinsic in zip(valid_paths, extrinsics):
        print(f'Extrínsecos {path.name}:\n', extrinsic)
