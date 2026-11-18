import cv2

RACHA_X2 = 5
RACHA_X3 = 10

PUNTOS_ACIERTO = 1
PUNTOS_ERROR = -1

PERSONAJES_MALOS = [
    "abalos",
    "darth_vader",
    "hitler",
    "ladron",
    "ogro",
    "rata",
    "sanchez",
    "voldemort"
]

def es_malo(nombre):
    return nombre in PERSONAJES_MALOS


class Rachas:

    def __init__(self):
        self.puntuacion = 0
        self.racha = 0
        self.multiplicador = 1
        self.racha_maxima = 0

    def actualizar_multiplicador(self):
        if self.racha >= RACHA_X3:
            self.multiplicador = 3

        elif self.racha >= RACHA_X2:
            self.multiplicador = 2

        else:
            self.multiplicador = 1

    def golpe_correcto(self):
        self.racha += 1

        self.actualizar_multiplicador()

        self.puntuacion += PUNTOS_ACIERTO * self.multiplicador

        self.racha_maxima = max(self.racha_maxima, self.racha)

    def golpe_incorrecto(self):
        self.puntuacion += PUNTOS_ERROR
        self.reiniciar_racha()

    def reiniciar_racha(self):
        self.racha = 0
        self.multiplicador = 1        


    def dibujar(self, frame):
        ancho = frame.shape[1]

        x = ancho - 230
        y = 15

        cv2.rectangle(frame, (x, y), (x+215, y+70),
                      (255, 255, 255), -1)

        cv2.rectangle(frame, (x, y), (x+215, y+70),
                      (0, 0, 0), 2)

        cv2.putText(frame, f'Puntos: {self.puntuacion}',
                    (x+10, y+27),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 0, 0), 2)

        cv2.putText(frame, f'Racha: {self.racha} | x{self.multiplicador}',
                    (x+10, y+55),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 0), 2)
if __name__ == "__main__":
    rachas = Rachas()

    for i in range(12):
        rachas.golpe_correcto()

        print(f"Puntos: {rachas.puntuacion} | "
              f"Racha: {rachas.racha} | "
              f"x{rachas.multiplicador}")

    print("\nGolpe incorrecto:")
    rachas.golpe_incorrecto()
    print(rachas.puntuacion, rachas.racha, rachas.multiplicador)

    print("\nDejamos escapar a un malo:")
    rachas.golpe_correcto()
    rachas.reiniciar_racha()
    print(rachas.puntuacion, rachas.racha, rachas.multiplicador)