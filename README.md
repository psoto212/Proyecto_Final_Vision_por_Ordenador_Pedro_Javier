# ¡Dale al malo! 🥊

Proyecto final de **Visión por Ordenador I** (3º de Ingeniería Matemática, ICAI – Universidad Pontificia Comillas, curso 2026/27).

Es un sistema de visión por ordenador clásica (sin Deep Learning) que solo necesita la webcam del ordenador. Tiene dos partes:

1. **Seguridad:** para entrar hay que meter una contraseña enseñando números con los dedos de la mano.
2. **Juego:** con unos guantes azules hay que darle puñetazos a los "malos" que van apareciendo en pantalla, sin tocar a los "buenos".

---

## Índice

- [Cómo se juega](#cómo-se-juega)
- [Instalación](#instalación)
- [Cómo ejecutarlo](#cómo-ejecutarlo)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Cómo funciona por dentro](#cómo-funciona-por-dentro)
- [Calibración de la cámara](#calibración-de-la-cámara)
- [Parámetros que se pueden cambiar](#parámetros-que-se-pueden-cambiar)
- [Consejos y limitaciones](#consejos-y-limitaciones)
- [Autores](#autores)

---

## Cómo se juega

### 1. Pantalla de seguridad
- A la derecha hay un **recuadro blanco**. Mete la mano dentro (sin guante) y enseña un número con los dedos.
- Cada número hay que **aguantarlo 1 segundo** (se va llenando una barra verde debajo del recuadro).
- La contraseña por defecto es **5 – 1 – 2 – 5**. Debajo del recuadro van saliendo los números que llevas (`5 1 _ _`).
- Si te equivocas, o cierras el **puño**, la secuencia se borra y vuelves a empezar.
- Dos números iguales seguidos: hay que cambiar de número o sacar la mano del recuadro entre uno y otro (sale el aviso `CAMBIA DE NUMERO`).
- Cuando la contraseña es correcta, el **candado** de arriba a la derecha se abre.

Con el candado abierto hay dos opciones:
- **Cambiar la contraseña:** aguanta el puño **5 segundos** (barra naranja) y mete 4 números nuevos. El candado se cierra y hay que entrar con la contraseña nueva. *(La contraseña nueva no se guarda al cerrar el programa.)*
- **Jugar:** pon la mano encima del botón **JUGAR** durante 1 segundo, o haz **clic** en él con el ratón.

### 2. Cuenta atrás
Salen 10 segundos con el mensaje **PONTE LOS GUANTES!** para dar tiempo a ponerse los guantes. Ya se ven los recuadros verdes de los guantes, así se puede comprobar que los detecta bien antes de empezar.

### 3. Partida
- Dura **30 segundos** y van saliendo caras en tandas de **1,5 segundos**.
- Empiezan saliendo 2 caras a la vez, y cada 10 segundos sale una más (2 → 3 → 4).
- **Golpear a un malo:** suma puntos y aumenta la racha.
- **Golpear a un bueno:** resta un punto y la racha vuelve a 0.
- **Dejar escapar a un malo** (que desaparezca sin darle): la racha vuelve a 0.
- Con **5 aciertos seguidos** los puntos valen **x2**, y con **10** valen **x3**.
- Solo cuenta como golpe si el guante va **rápido** (más de 700 píxeles por segundo). Pasar la mano despacio por encima no vale.
- En la parte de abajo del centro hay una **zona de descanso** donde no sale ninguna cara, para dejar las manos quietas sin golpear sin querer.
- Se pueden usar **dos guantes** a la vez.

### 4. Fin de partida
Salen los puntos y el **récord** (la mejor puntuación guardada en el ordenador). Para elegir, pon la mano 1 segundo encima de **VOLVER A JUGAR** o de **SALIR**.

La tecla **`q`** cierra el programa desde la seguridad, la cuenta atrás o el fin de partida. Durante la partida, `q` la termina antes de tiempo y pasa directamente al fin de partida.

---

## Instalación

Hace falta **Python 3.8 o superior** y una webcam.

```bash
git clone https://github.com/psoto212/Proyecto_Final_Vision_por_Ordenador_Pedro_Javier.git
cd Proyecto_Final_Vision_por_Ordenador_Pedro_Javier
pip install -r requirements.txt
```

Las librerías que se usan son solo **OpenCV** (`opencv-python`) y **NumPy**.

> Ojo: tiene que ser `opencv-python` y no `opencv-python-headless`, porque la versión *headless* no puede abrir ventanas.

---

## Cómo ejecutarlo

**Programa completo** (seguridad → juego → fin de partida):

```bash
python main.py
```

**Calibración de la cámara** (solo hace falta hacerla una vez, antes de usar el programa):

```bash
python calibracion/calibracion_camara.py
```

**Probar cada parte por separado:**

```bash
python seguridad.py           # solo la pantalla de la contraseña
python juego.py               # solo una partida
python deteccion_guante.py    # ver la máscara azul y la velocidad de los guantes
```

> El programa está pensado para **Windows** (abre la cámara con `cv2.CAP_DSHOW`) y para una imagen de **1280 x 720**. Si la cámara no es la número 0, se cambia el índice en `camara.py`.

---

## Estructura del repositorio

```
├── main.py                 # Programa principal: une todas las pantallas
├── camara.py               # Lee la cámara, quita la deformación de la lente, espejo y FPS
├── seguridad.py            # Pantalla de seguridad: piel, contar dedos y contraseña
├── juego.py                # Cuenta atrás y partida: caras, golpes y marcador
├── deteccion_guante.py     # Detección de los 2 guantes azules y su velocidad
├── rachas.py               # Puntos, rachas y multiplicadores (qué personajes son malos)
├── record.py               # Guarda y lee el récord en record.txt
├── fin_partida.py          # Pantalla final con los botones de volver a jugar o salir
├── calibracion/
│   ├── calibracion_camara.py      # Calibración offline con el tablero de ajedrez
│   ├── calibracion.npz            # Resultado de la calibración (K y distorsión)
│   ├── fotos_calibracion/         # Las 19 fotos del tablero
│   └── resultados_calibracion/    # Las fotos con las esquinas detectadas dibujadas
├── imagenes/
│   ├── candados/           # Candado abierto y cerrado
│   └── caras/              # Personajes: sin_fondo (normales), paliza (golpeados) y originales
└── requirements.txt
```

---

## Cómo funciona por dentro

### Cámara (`camara.py`)
Todas las pantallas leen la imagen a través de la clase `Camara`, que en cada imagen:
1. **Quita la deformación de la lente** con los datos de la calibración. El "mapa" de corrección se calcula una sola vez al principio (`initUndistortRectifyMap`) y luego en cada imagen solo se aplica con `remap`, que es mucho más rápido que `undistort` (unos 4 ms por imagen).
2. La pone en **espejo**, para que moverse delante de la cámara sea natural.
3. Calcula los **FPS** (suavizados para que no salten) y los pinta abajo a la izquierda en todas las pantallas.

### Seguridad: contar dedos (`seguridad.py`)
1. Solo se mira la imagen **dentro del recuadro**.
2. Se pasa al espacio de color **YCrCb**, que separa el brillo del color, y se buscan los píxeles de color piel con `inRange`. Así funciona mejor con distintas luces que en RGB.
3. Se limpia la máscara con **apertura y cierre** (morfología) para quitar puntitos y rellenar agujeros.
4. La **mano** es la mancha blanca más grande.
5. Con la **transformada de distancia** se encuentra el centro de la palma (el punto más alejado del borde) y su radio.
6. Se dibujan **3 círculos** alrededor de la palma (1,7, 2,0 y 2,3 veces el radio) y se cuentan los trozos blancos que cortan: cada trozo es un dedo. La parte de abajo del círculo (la muñeca) no se cuenta. Nos quedamos con el círculo que más dedos ve, porque cerca de la base los dedos se juntan y más arriba se separan.
7. **Votación:** el número final es el que más se repite en las últimas 10 imágenes, para que no salte de un número a otro.

### Seguridad: la contraseña (clase `Contrasena`)
Es el **decodificador** que memoriza hasta 4 números seguidos. Un número se acepta cuando se aguanta 1 segundo. Si es el que tocaba se guarda, si no se borra todo. El puño también lo borra todo. Con el candado abierto, aguantar el puño 5 segundos pasa al modo de contraseña nueva.

### Juego: detectar y seguir los guantes (`deteccion_guante.py`)
1. Se pasa la imagen a **HSV** y se buscan los píxeles **azules** con `inRange` (pedimos un azul bastante intenso para no confundirlo con cosas azul pálido del fondo).
2. Se limpia con **erosión y dilatación**.
3. Los guantes son las **2 manchas azules más grandes** (con un área mínima). Se rodean con su **recuadro** (*bounding box*), que es el que se ve en pantalla.
4. **Seguimiento:** en cada imagen se compara el centro del recuadro con el de la imagen anterior para calcular la **velocidad** (píxeles por segundo, suavizada). Con dos guantes, el de la izquierda es el guante 1 y el de la derecha el guante 2. Si solo se ve uno, se le asigna al que estaba más cerca.

### Juego: caras y golpes (`juego.py`, `rachas.py`)
- Las caras se cargan una sola vez al principio en un diccionario: número → (cara normal, cara golpeada). Son PNG con transparencia que se pegan encima de la imagen de la cámara.
- Para que **no se pisen**, la pantalla se divide en tantas columnas como caras y cada cara sale en la suya. Se prueban 20 colocaciones al azar y nos quedamos con la que deja las caras **más separadas**. Además, ninguna cara puede salir en la zona de descanso.
- Hay **golpe** cuando el recuadro de un guante toca el recuadro de una cara **y** ese guante va a más de 700 px/s. La cara cambia a su versión golpeada.
- Los guantes se buscan **antes** de pintar las caras, para que el azul de alguna foto no se confunda con un guante.

---

## Calibración de la cámara

La calibración se hace **offline**, antes de ejecutar el programa, con `calibracion/calibracion_camara.py`:
- Tablero de ajedrez de **9 x 6 esquinas interiores** y cuadros de **23 mm**.
- Se buscan las esquinas con `findChessboardCorners`, se afinan con `cornerSubPix` y se calibra con `calibrateCamera`.
- El resultado se guarda en `calibracion/calibracion.npz`, y `camara.py` lo lee al arrancar.

Resultados con nuestra webcam (19 de 19 fotos válidas, imágenes de 1280 x 720):

| Parámetro | Valor |
|---|---|
| Error RMS | **0,747 píxeles** |
| fx, fy | 1012,8 · 1009,9 |
| cx, cy | 604,7 · 330,9 |
| Distorsión (k1, k2, p1, p2, k3) | 0,166 · −0,870 · −0,007 · −0,007 · 1,817 |

Al corregir la deformación, los bordes de la imagen salen un poco curvados con negro alrededor. Es normal: son las zonas donde la cámara no tiene información después de "enderezar" la imagen.

Si se usa otra cámara, hay que hacer fotos nuevas del tablero, ponerlas en `calibracion/fotos_calibracion/` y volver a ejecutar la calibración.

---

## Parámetros que se pueden cambiar

Están todos arriba del todo de cada archivo, en mayúsculas:

| Archivo | Parámetro | Para qué sirve |
|---|---|---|
| `seguridad.py` | `SECUENCIA` | Contraseña inicial (por defecto `[5, 1, 2, 5]`) |
| `seguridad.py` | `RECUADRO` | Dónde está el recuadro de la mano |
| `seguridad.py` | `PIEL_BAJO`, `PIEL_ALTO` | Color de la piel en YCrCb |
| `seguridad.py` | `TIEMPO_MANTENER`, `TIEMPO_CAMBIO` | Segundos para aceptar un número y para cambiar la contraseña |
| `juego.py` | `DURACION_JUEGO`, `TIEMPO_FASE`, `TIEMPO_CARAS` | Duración de la partida, cada cuánto sale una cara más y cuánto dura cada tanda |
| `juego.py` | `VELOCIDAD_GOLPE` | Lo rápido que tiene que ir el guante para que cuente como golpe |
| `juego.py` | `TEXTO_PONERSE`, `TIEMPO_PONERSE` | Frase y duración de la cuenta atrás |
| `juego.py` | `ZONA_DESCANSO` | Zona donde no salen caras |
| `deteccion_guante.py` | `AZUL_MIN`, `AZUL_MAX` | Color azul del guante en HSV |
| `rachas.py` | `PERSONAJES_MALOS`, `RACHA_X2`, `RACHA_X3` | Qué personajes son malos y con cuántos aciertos sube el multiplicador |

> `cv2.putText` no sabe pintar tildes, ñ ni los signos `¡ ¿`, así que los textos de la pantalla van sin ellos.

---

## Consejos y limitaciones

- **Luz:** con poca luz se pierden trozos de los dedos y la cámara baja sola los FPS. Funciona mucho mejor con buena luz.
- **Fondo:** para la contraseña, conviene que detrás de la mano no haya nada de color parecido a la piel (madera, paredes beige, la cara). Para el juego, que no haya cosas azules intensas detrás.
- **Dedos:** hay que abrirlos un poco. Si están completamente pegados, se ven como un solo trozo y no se pueden separar.
- **Puñetazos:** la velocidad se mide en el plano de la imagen, así que un puñetazo directo hacia la cámara casi no se detecta. Hay que golpear de lado o de arriba abajo.
- **Dos guantes:** si se cruzan los brazos, los guantes se pueden "intercambiar" un momento y la velocidad da un salto.

---

## Autores

- **Pedro** – [psoto212](https://github.com/psoto212)
- **Javier Arraiza** – [javier13arraiza](https://github.com/javier13arraiza)

Universidad Pontificia Comillas, ICAI – Visión por Ordenador I, grupo A.

Durante el desarrollo hemos usado un asistente de IA (Claude) como apoyo para resolver dudas, revisar código y redactar parte de la documentación.
