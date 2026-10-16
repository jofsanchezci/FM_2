# FM didáctica en Wokwi con Arduino UNO

## Abrir el proyecto

1. Visite https://wokwi.com/projects/new/arduino-uno.
2. Sustituya el contenido de `sketch.ino` por el archivo de este paquete.
3. Abra la pestaña `diagram.json` y sustituya su contenido por el archivo del mismo nombre.
4. Inicie la simulación con el botón verde. No requiere librerías adicionales.
5. El Serial Plotter muestra `Mensaje` y `Recuperado`; las trazas Min y Max fijan una referencia visual. Espere unos segundos.
6. Gire el potenciometro para ajustar la desviación. Después de moverlo, espere a que las curvas se estabilicen.

## Qué se simula

Un solo Arduino desempeña dos funciones independientes: el transmisor genera en D9 una onda cuadrada cuya frecuencia varía con un mensaje sinusoidal; el receptor detecta flancos reales en D2, conectado mediante un cable a D9. El receptor calcula el periodo y estima el mensaje. Al retirar el cable D9-D2 se interrumpe la recepción y deja de imprimirse información nueva.

Es un modelo eléctrico de FM a baja frecuencia. No simula antenas, propagación, audio radiado, ni los chips Si4713/Si4703. La señal cuadrada conserva amplitud lógica y cambia su separación temporal; contiene armónicos y no representa una portadora RF sinusoidal pura.

## Parámetros y ecuaciones

| Magnitud | Valor |
|---|---:|
| Frecuencia central FC | 200 Hz |
| Frecuencia del mensaje FM | 0,5 Hz |
| Desviación máxima Δf | Ajustable de 20 a 120 Hz |
| Frecuencia del acumulador de fase | 20 000 muestras/s |
| Frecuencia instantánea | FC + Δf · mensaje |
| Estimación del mensaje | (1 / periodo − FC) / Δf |

La desviación es conocida por ambos roles porque comparten Arduino. Un receptor independiente necesitaría configurar su propia escala de desviación. El filtro de salida es un suavizado de primer orden, por lo que introduce retardo. La cuantización temporal genera pequeñas diferencias entre las curvas.

## Experimentos para clase

1. Potenciómetro al mínimo: frecuencia instantánea entre 180 y 220 Hz. Observe la curva recuperada.
2. Potenciómetro al máximo: frecuencia instantánea entre 80 y 320 Hz. Compare la separación de flancos.
3. Calcule el índice β = Δf / FM en ambos casos.
4. Cambie FM a 1 Hz. Cambie también `2000000UL` por `1000000UL` en el cálculo de `tiempo`, para conservar la continuidad del seno.
5. Retire el cable entre D9 y D2 y explique por qué cesa la información nueva del receptor.

## Analizador lógico

D0 registra la salida FM y D1 la entrada al receptor. Las dos trazas deben coincidir porque el canal es un cable ideal. Al detener la simulación, Wokwi permite obtener la captura VCD y abrirla con PulseView/GTKWave. Verifique que la amplitud lógica no cambia y el periodo sí. El analizador no muestra una sinusoidal analógica.

## Alcance de la validación

Se revisaron la estructura del diagrama y el algoritmo de generación/demodulación. El paquete no se ejecutó dentro de Wokwi ni se compiló con el compilador AVR en el entorno de creación.

Documentación oficial: https://docs.wokwi.com/guides/serial-monitor y https://docs.wokwi.com/guides/logic-analyzer.
