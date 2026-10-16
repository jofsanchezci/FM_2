# Simulación de transmisión y recepción PM en Python

El archivo `simulacion_pm_tx_rx.py` modela un sistema de modulación de fase (PM) con transmisor, canal con ruido y receptor coherente. Permite comparar el mensaje original y el recuperado, observar la fase y el espectro, y evaluar el desempeño mediante métricas.

## 1. Instalación y ejecución

Requiere Python 3 y las bibliotecas NumPy, SciPy y Matplotlib:

```bash
python3 -m pip install numpy scipy matplotlib
python3 simulacion_pm_tx_rx.py
```

Ejecute los comandos desde la carpeta del script. En Windows puede usar `python` en lugar de `python3`.

Para consultar la ayuda:

```bash
python3 simulacion_pm_tx_rx.py --help
```

### Ejemplos

```bash
# Canal sin ruido
python3 simulacion_pm_tx_rx.py --sin-ruido

# Aumentar el índice de modulación
python3 simulacion_pm_tx_rx.py --beta 3

# Aumentar el ruido: una SNR menor implica más ruido
python3 simulacion_pm_tx_rx.py --snr 5

# Cambiar la frecuencia del mensaje y el índice PM
python3 simulacion_pm_tx_rx.py --fm 1000 --beta 2

# Guardar las gráficas
python3 simulacion_pm_tx_rx.py --guardar resultado_pm.png

# Guardar sin abrir la ventana
python3 simulacion_pm_tx_rx.py --no-mostrar --guardar resultado_pm.png
```

En un servidor sin interfaz gráfica, puede seleccionar un backend no interactivo. Por ejemplo, en macOS/Linux:

```bash
MPLBACKEND=Agg python3 simulacion_pm_tx_rx.py --no-mostrar --guardar resultado_pm.png
```

## 2. Parámetros

| Opción | Valor inicial | Descripción |
|---|---:|---|
| `--fs` | 200000 | Frecuencia de muestreo, muestras/s |
| `--fc` | 20000 | Frecuencia de la portadora, Hz |
| `--fm` | 500 | Frecuencia del mensaje, Hz |
| `--beta` | 1.5 | Índice PM, cuyo valor numérico coincide con la desviación pico de fase en radianes |
| `--duracion` | 0.2 | Duración total, incluido el preámbulo, segundos |
| `--snr` | 15 | SNR de entrada antes del filtrado, dB |
| `--semilla` | 42 | Semilla para reproducir el ruido |
| `--sin-ruido` | Desactivada | Elimina el ruido del canal |
| `--guardar` | Sin archivo | Ruta de la figura que se desea guardar |
| `--no-mostrar` | Desactivada | Evita abrir la ventana de las gráficas |

El mensaje tiene amplitud 1. La envolvente compleja transmitida también tiene magnitud 1.

## 3. Representación compleja I/Q

El programa representa la señal mediante un número complejo:

\[
s(t)=e^{j[2\pi f_c t+\beta m(t)]}.
\]

Su parte real, I, corresponde al coseno modulado, y su parte imaginaria, Q, al seno en cuadratura. El receptor dispone de ambas componentes. En un equipo físico, una etapa de recepción I/Q permitiría obtener esa representación.

La gráfica temporal del canal muestra únicamente la parte real, mientras que el procesamiento utiliza la señal compleja completa.

## 4. Mensaje y transmisor PM

El registro comienza con un **preámbulo sin mensaje**. Después, el mensaje es:

\[
m(t)=\sin(2\pi f_m(t-T_p)),\qquad t\geq T_p,
\]

donde `Tp` es la duración del preámbulo. Durante el preámbulo, `m(t) = 0` y el transmisor sigue enviando la portadora.

La desviación de fase sigue directamente al mensaje:

\[
\phi_m(t)=\beta m(t).
\]

Para un mensaje de amplitud `Am` y una sensibilidad `kp` en radianes por unidad de amplitud, el índice es `β = kp × Am`. En este programa se configura β directamente.

En el tramo sinusoidal, la frecuencia instantánea ideal es:

\[
f_i(t)=f_c+\beta f_m\cos(2\pi f_m(t-T_p)).
\]

Por tanto:

\[
\Delta f=\beta f_m,\qquad B_{Carson}\approx2f_m(\beta+1).
\]

Con los valores iniciales:

- Desviación pico de fase: 1,5 rad.
- Desviación pico de frecuencia: 750 Hz.
- Frecuencia instantánea: de 19 250 a 20 750 Hz.
- Ancho de banda aproximado de Carson: 2500 Hz.

Carson describe una ocupación espectral aproximada para el tono. El inicio del mensaje introduce un transitorio adicional y la señal PM ideal puede tener componentes fuera de esos bordes.

## 5. Canal con ruido

El canal suma ruido blanco gaussiano complejo:

\[
r(t)=s(t)+n_I(t)+j n_Q(t).
\]

Las componentes I y Q del ruido son independientes y tienen la misma varianza. Como la potencia de la señal compleja es 1, el código utiliza:

\[
\sigma=\sqrt{\frac{10^{-SNR_{dB}/10}}{2}}.
\]

La potencia total esperada del ruido complejo es `2 × sigma²`. La SNR configurada corresponde a toda la banda muestreada, antes del filtro del receptor.

## 6. Receptor coherente

El receptor realiza los siguientes pasos:

1. **Conversión a banda base:** multiplica la señal recibida por `exp(-j × 2π × fc × t)`, usando un oscilador local ideal con la frecuencia correcta.
2. **Filtrado de canal:** aplica un filtro Butterworth paso bajo con frecuencia de corte `1.4 × (beta + 1) × fm`. El margen permite conservar las componentes significativas de PM.
3. **Extracción de fase:** `np.angle()` obtiene la fase principal y `np.unwrap()` corrige los saltos de representación de 2π.
4. **Referencia de fase:** calcula la fase media durante una parte interna del preámbulo y la resta del registro.
5. **Demodulación:** divide la fase corregida por β para recuperar el mensaje.
6. **Filtrado del mensaje:** aplica un filtro paso bajo con frecuencia de corte `1.5 × fm` para reducir el ruido de salida.

El receptor conoce la frecuencia central, el índice PM y la posición del preámbulo. No implementa una búsqueda de frecuencia, un PLL ni detección automática del inicio de la transmisión.

### Duración del preámbulo

El código calcula:

```python
margen = max(0.005, 5 / fm)
preambulo = 4 * margen
```

Con `fm = 500 Hz`, el margen es 10 ms y el preámbulo dura 40 ms. La estimación de referencia utiliza el intervalo de 10 a 30 ms.

## 7. Gráficas

| Gráfica | Interpretación |
|---|---|
| Mensaje original | Señal sinusoidal que se desea transmitir |
| Señales en el canal | Parte real de la señal PM transmitida y recibida con ruido |
| Desviación de fase | Comparación entre la fase ideal del mensaje y la estimada por el receptor |
| Espectro | Densidad espectral de potencia de transmisión y recepción, con referencias de Carson |
| Recuperación | Superposición del mensaje original y el recuperado |
| Frecuencia instantánea ideal | Variación de frecuencia producida por la derivada del mensaje |

El espectro se estima con Welch utilizando la señal compleja y un espectro bilateral. La figura muestra la región alrededor de la portadora. Las ventanas temporales presentan un tramo interno posterior al preámbulo.

## 8. Métricas

El programa imprime:

- **RMSE:** raíz del error cuadrático medio entre el mensaje original y el recuperado. Un valor menor indica menor error.
- **Correlación:** asociación lineal entre las señales. Un valor cercano a 1 indica formas similares, pero por sí solo no garantiza amplitudes iguales.
- **Relación señal/error de salida:** potencia media del mensaje dividida por la potencia media del error, expresada en dB. Incluye ruido, distorsión y errores numéricos.

Las métricas se calculan después del preámbulo, excluyendo márgenes para reducir el efecto de los transitorios. Por ello, la SNR de entrada y la relación señal/error de salida son medidas diferentes.

## 9. Organización del código

| Función | Responsabilidad |
|---|---|
| `simular(...)` | Generar señales, añadir ruido, recuperar el mensaje y calcular métricas |
| `graficar(r, canal)` | Crear la figura con seis gráficas |
| `main()` | Leer los argumentos y ejecutar el programa |

Puede reutilizar el simulador desde otro script ubicado en la misma carpeta:

```python
from simulacion_pm_tx_rx import simular

for snr in [0, 5, 10, 15, 20]:
    resultado = simular(snr_db=snr, beta=1.5, semilla=42)
    print(snr, resultado['rmse'], resultado['correlacion'])
```

Para estudiar tendencias de desempeño, repita cada condición con varias semillas y promedie los resultados. Una sola realización no permite establecer el comportamiento estadístico completo.

## 10. Restricciones y supuestos

- Es una simulación fuera de línea, sin hardware ni transmisión de RF.
- Los filtros usan `sosfiltfilt`, que procesa hacia adelante y hacia atrás. Este análisis de fase cero requiere el registro completo y no representa filtrado causal en tiempo real.
- El receptor tiene una referencia ideal de frecuencia. Un sistema físico necesita sincronización.
- El índice β debe ser positivo. Con β muy pequeño, dividir por β amplifica las perturbaciones de fase en el mensaje estimado.
- El ruido intenso puede provocar errores de desenrollado de fase y pérdidas de ciclos, con degradación importante de la recuperación.
- Los parámetros deben satisfacer `fc − banda > 0` y `fc + banda < fs/2`, donde `banda = 1.4 × (beta + 1) × fm`. Esta validación utiliza una banda práctica, ya que el espectro ideal de PM no tiene soporte finito exacto.
- La duración debe ser mayor que `9 × margen`. Con los valores iniciales, debe superar 0,09 s.
- El filtro del mensaje está diseñado para un solo tono. Para voz o señales de varios tonos se deben revisar el mensaje, su ancho de banda y los filtros.
- No se modelan pérdidas de propagación, desvanecimiento, interferencias de otras transmisiones ni errores del oscilador local.

## 11. Actividad sugerida para clase

1. Ejecute el canal ideal y registre las métricas.
2. Compare β de 0,5, 1,5 y 3 manteniendo `fm = 500 Hz`. Calcule la desviación de frecuencia y Carson.
3. Duplique `fm` manteniendo β. Explique por qué aumenta la desviación de frecuencia aunque la desviación de fase permanezca constante.
4. Compare SNR de 20, 10, 5 y 0 dB con los demás parámetros fijos.
5. Entregue una tabla de parámetros y métricas, gráficas seleccionadas y una explicación de la diferencia entre PM y FM.

**Idea central:** en PM, la fase sigue al mensaje y la desviación de frecuencia sigue a su derivada.
