from pathlib import Path
import cv2

ARCHIVO = Path(__file__).with_name("record.txt")

def cargar_record():
    if ARCHIVO.exists():
        return int(ARCHIVO.read_text())
    return 0

def actualizar_record(puntos, record):
    if puntos > record:
        record = puntos
        ARCHIVO.write_text(str(record))
    return record

def dibujar_record(frame, record):
    x = frame.shape[1] - 230
    y = 220
    cv2.rectangle(frame, (x, y - 25), (x + 215, y + 15), (255, 255, 255), -1)
    cv2.putText(frame, f"Record: {record}", (x + 10, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)