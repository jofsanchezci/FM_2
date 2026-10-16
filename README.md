# Simulación de transmisión y recepción FM en Python

Este proyecto permite estudiar un sistema de comunicaciones de modulación en frecuencia (FM): genera un mensaje, lo transmite mediante una portadora, añade ruido y recupera el mensaje en el receptor. Incluye seis gráficas y métricas para evaluar la recuperación.

El archivo principal es `simulacion_fm_tx_rx.py`. La simulación es numérica y no requiere Arduino, GNU Radio ni equipos de radio.

## 1. Instalación

Necesita Python 3 con NumPy, SciPy y Matplotlib:

```bash
python3 -m pip install numpy scipy matplotlib
```

Si utiliza un entorno virtual en macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install numpy scipy matplotlib
```

En Windows puede utilizar `python` en lugar de `python3`. Para activar el entorno desde PowerShell, ejecute `.venv\Scripts\Activate.ps1`.

## 2. Ejecución

Abra una terminal en la carpeta del programa y ejecute:

```bash
python3 simulacion_fm_tx_rx.py
```

El programa imprime los parámetros y las métricas en la terminal y abre una ventana con las gráficas. Para consultar las opciones:

```bash
python3 simulacion_fm_tx_rx.py --help
```

### Ejemplos

```bash
# Comparar con un canal ideal
python3 simulacion_fm_tx_rx.py --sin-ruido

# Aumentar el ruido: una SNR menor implica más ruido
python3 simulacion_fm_tx_rx.py --snr 5

# Cambiar la desviación y la frecuencia del mensaje
python3 simulacion_fm_tx_rx.py --desviacion 3000 --fm 1000

# Guardar la figura y mostrarla
python3 simulacion_fm_tx_rx.py --guardar resultado_fm.png

# Guardar la figura sin abrir una ventana
python3 simulacion_fm_tx_rx.py --no-mostrar --guardar resultado_fm.png
```

En servidores sin interfaz gráfica puede seleccionar un backend no interactivo, por ejemplo en macOS/Linux:

```bash
MPLBACKEND=Agg python3 simulacion_fm_tx_rx.py --no-mostrar --guardar resultado_fm.png
```

## 3. Parámetros disponibles

| Opción | Valor inicial | Significado |
|---|---:|---|
| `--fs` | 200000 | Frecuencia de muestreo, muestras/s |
| `--fc` | 20000 | Frecuencia central de la portadora, Hz |
| `--fm` | 500 | Frecuencia del mensaje sinusoidal, Hz |
| `--desviacion` | 5000 | Desviación máxima de frecuencia, Hz |
| `--duracion` | 0.2 | Duración simulada, segundos |
| `--snr` | 15 | Relación señal/ruido de entrada, dB |
| `--semilla` | 42 | Semilla del generador de ruido |
| `--sin-ruido` | Desactivada | Utiliza un canal ideal, sin ruido aditivo |
| `--guardar` | Sin archivo | Ruta de la imagen que se desea guardar |
| `--no-mostrar` | Desactivada | Evita abrir la ventana de las gráficas |

La amplitud del mensaje y de la portadora es 1. La semilla permite repetir una prueba con la misma realización de ruido.

## 4. Fundamento del transmisor

El mensaje es un coseno:

$m(t)=\cos(2\pi f_m t)$

La frecuencia instantánea ideal es:

$f_i(t)=f_c+\Delta f\,m(t)$


La señal transmitida se obtiene integrando el mensaje en la fase:

$s(t)=\cos\left(2\pi f_c t+2\pi\Delta f\int_0^t m(\tau)\,d\tau\right)$

En el código, `np.cumsum(mensaje) / fs` aproxima esa integral. La amplitud de la portadora permanece constante; la separación entre sus ciclos cambia con el mensaje.

Para un tono, el índice de modulación y la aproximación de Carson son:

$\beta=\frac{\Delta f}{f_m},\qquad B\approx2(\Delta f+f_m)$

Con los valores iniciales, β = 10 y B ≈ 11 000 Hz. La frecuencia instantánea varía entre 15 y 25 kHz. Los bordes aproximados de Carson están en 14,5 y 25,5 kHz: el intervalo de frecuencia instantánea y el ancho de banda espectral son magnitudes diferentes.

## 5. Canal con ruido

El canal se modela mediante:

$r(t)=s(t)+n(t)$

donde `n(t)` es ruido blanco gaussiano aditivo (AWGN). El programa calcula la potencia media de la señal y determina la varianza del ruido mediante:

$P_n=P_s\,10^{-\mathrm{SNR}_{dB}/10}$

La SNR configurada corresponde a toda la banda muestreada, antes del filtro de canal. No representa directamente la SNR del mensaje recuperado. Los filtros del receptor eliminan parte del ruido añadido.

## 6. Funcionamiento del receptor

1. **Filtro de canal.** Selecciona la banda alrededor de la portadora mediante un filtro Butterworth. Sus límites son `fc ± 1.4 × (desviacion + fm)`; el factor 1,4 añade margen a la estimación de Carson.
2. **Señal analítica.** La transformada de Hilbert genera una representación compleja a partir de la señal real filtrada.
3. **Diferencia de fase.** Se calcula el argumento de `z[n] × conjugado(z[n−1])`. Al multiplicarlo por `fs / (2π)` se estima la frecuencia instantánea.
4. **Recuperación del mensaje.** Se resta `fc` y se divide por `desviacion`:

$\hat m[n]=\frac{\hat f_i[n]-f_c}{\Delta f}$

5. **Filtro de salida.** Un filtro paso bajo con frecuencia de corte `1.5 × fm` reduce el ruido de alta frecuencia en el mensaje recuperado.

El receptor conoce la frecuencia central y la desviación empleadas por el transmisor. No incluye adquisición de frecuencia ni seguimiento mediante PLL.

## 7. Cómo interpretar las gráficas

| Gráfica | Qué permite observar |
|---|---|
| Mensaje | La señal sinusoidal que se desea comunicar |
| Portadora y FM transmitida | Los cambios en la separación temporal de los ciclos |
| Señal recibida | El efecto del ruido antes del filtro de canal |
| Espectro | Bandas laterales, piso de ruido y bordes aproximados de Carson |
| Original y recuperado | La calidad de la recuperación mediante la superposición de curvas |
| Frecuencia instantánea | La comparación entre la frecuencia ideal y la estimada antes del filtro de salida |

El espectro se estima mediante el método de Welch. Las líneas de Carson son referencias aproximadas, no límites exactos: pueden existir componentes espectrales fuera de ellas.

Las gráficas temporales muestran ventanas cortas internas del registro, para apreciar los ciclos y evitar los efectos de borde.

## 8. Métricas impresas

Las métricas excluyen un margen en ambos extremos de la señal para reducir la influencia de los transitorios del filtrado y de Hilbert.

- **RMSE:** raíz del error cuadrático medio entre el mensaje original y el recuperado. Un valor menor indica una recuperación más precisa.
- **Correlación:** mide la asociación lineal entre las señales. Un valor cercano a 1 indica que sus formas son similares, pero no garantiza por sí solo que tengan la misma amplitud.
- **Relación señal/error de salida:** compara la potencia del mensaje con la potencia del error total de recuperación. Incluye ruido, distorsión y errores numéricos; no mide exclusivamente ruido aleatorio.

La relación señal/error se calcula como:

$10\log_{10}\left(\frac{\operatorname{media}(m^2)}{\operatorname{media}((m-\hat m)^2)}\right)$

## 9. Organización del código

| Función | Responsabilidad |
|---|---|
| `simular(...)` | Generar señales, transmitir, añadir ruido, demodular y calcular métricas |
| `graficar(r, titulo_canal)` | Construir la figura con las seis gráficas |
| `main()` | Leer opciones, ejecutar la simulación e imprimir/guardar los resultados |

También puede importar el simulador desde otro programa:

```python
from simulacion_fm_tx_rx import simular

for snr in [0, 5, 10, 15, 20]:
    resultado = simular(snr_db=snr, semilla=42)
    print(snr, resultado['rmse'], resultado['correlacion'])
```

Para un análisis estadístico del desempeño, repita cada condición con varias semillas y compare promedios, no solo una realización del ruido.

## 10. Restricciones del modelo

- Se utiliza un mensaje de un solo tono. Para voz o varios tonos deben revisarse el ancho de banda del mensaje y el filtro de salida.
- Los filtros se aplican con `sosfiltfilt`, hacia adelante y hacia atrás. Esto permite un análisis de fase cero fuera de línea, pero no representa un receptor causal en tiempo real.
- El espectro ideal de FM no tiene un límite finito exacto. Las validaciones de muestreo usan una banda práctica con margen, no una garantía matemática de ausencia total de aliasing.
- Se requiere `fc − 1.4 × (desviacion + fm) > 0` y `fc + 1.4 × (desviacion + fm) < fs/2`.
- La duración debe superar `4 × max(0.01, 5/fm)` segundos. Con los valores iniciales, debe ser mayor que 0,04 s.
- Con ruido intenso pueden aparecer errores grandes en la estimación de fase y degradarse la recepción.
- No se modelan antenas, pérdidas de propagación, interferencias de otras emisoras ni amplificadores de RF.

## 11. Actividad sugerida

1. Ejecute el canal sin ruido y registre RMSE y correlación.
2. Compare SNR de 20, 10, 5 y 0 dB, manteniendo los demás parámetros.
3. Compare desviaciones de 1000, 3000 y 5000 Hz. Calcule β y el ancho de banda de Carson en cada caso.
4. Duplique la frecuencia del mensaje conservando la desviación y explique los cambios en β y en el espectro.
5. Entregue una tabla de parámetros y métricas, las gráficas seleccionadas y una explicación del compromiso entre ruido, desviación y ancho de banda.
