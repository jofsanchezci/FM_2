#!/usr/bin/env python3
"""Simulación de transmisión y recepción de FM analógica (sin hardware).

Instalación: python -m pip install numpy scipy matplotlib
Ejecución:   python simulacion_fm_tx_rx.py
Ejemplos:
  python simulacion_fm_tx_rx.py --snr 5 --desviacion 3000
  python simulacion_fm_tx_rx.py --sin-ruido
  python simulacion_fm_tx_rx.py --no-mostrar --guardar resultado_fm.png

Transmisor: seno real de fase modulada por la integral del mensaje.
Canal: ruido blanco gaussiano aditivo con semilla reproducible.
Receptor: filtro de canal, señal analítica (Hilbert), diferencia de fase,
eliminación de la frecuencia central y filtro paso bajo de salida.
Los filtros de fase cero son un recurso de análisis fuera de línea;
no representan una implementación causal en tiempo real.
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt, hilbert, welch


def simular(fs=200000.0, fc=20000.0, fm=500.0, desviacion=5000.0,
            duracion=0.2, snr_db=15.0, sin_ruido=False, semilla=42):
    """Devuelve señales, estimaciones y métricas, sin abrir ventanas."""
    if not all(np.isfinite(v) and v > 0 for v in
               (fs, fc, fm, desviacion, duracion)):
        raise ValueError('fs, fc, fm, desviacion y duracion deben ser positivos y finitos.')
    if not np.isfinite(snr_db):
        raise ValueError('SNR debe ser finita; use --sin-ruido para un canal ideal.')
    # Carson es una aproximación: se añade margen al filtro de canal.
    semibanda = 1.4 * (desviacion + fm)
    inferior, superior = fc - semibanda, fc + semibanda
    if inferior <= 0 or superior >= fs / 2 or 1.5 * fm >= fs / 2:
        raise ValueError('La banda de canal debe quedar entre 0 y fs/2. '
                         'Aumente fs/fc o reduzca desviacion/fm según corresponda.')
    margen = max(0.01, 5 / fm)
    if duracion <= 4 * margen:
        raise ValueError(f'Use una duración mayor que {4*margen:.3f} s.')
    t = np.arange(int(fs * duracion)) / fs
    mensaje = np.cos(2 * np.pi * fm * t)
    portadora = np.cos(2 * np.pi * fc * t)
    # Integral discreta: cada incremento de fase codifica una muestra.
    fase = 2 * np.pi * fc * t + 2 * np.pi * desviacion * np.cumsum(mensaje) / fs
    transmitida = np.cos(fase)
    rng = np.random.default_rng(semilla)
    potencia_tx = np.mean(transmitida ** 2)
    ruido = np.zeros_like(t) if sin_ruido else rng.normal(
        0, np.sqrt(potencia_tx * 10 ** (-snr_db / 10)), t.size)
    recibida = transmitida + ruido
    filtro_canal = butter(6, [inferior, superior], btype='bandpass', fs=fs, output='sos')
    filtrada = sosfiltfilt(filtro_canal, recibida)
    analitica = hilbert(filtrada)
    # arg(z[n] * conj(z[n-1])) evita un desenrollado global de fase.
    paso_fase = np.angle(analitica[1:] * np.conj(analitica[:-1]))
    frecuencia_rx = np.r_[paso_fase[0], paso_fase] * fs / (2 * np.pi)
    demodulada = (frecuencia_rx - fc) / desviacion
    filtro_audio = butter(6, 1.5 * fm, btype='lowpass', fs=fs, output='sos')
    recuperada = sosfiltfilt(filtro_audio, demodulada)
    # Excluir los extremos: Hilbert y los filtros tienen efectos de borde.
    validas = (t >= margen) & (t < t[-1] - margen)
    error = mensaje[validas] - recuperada[validas]
    mse = np.mean(error ** 2)
    correlacion = np.corrcoef(mensaje[validas], recuperada[validas])[0, 1]
    snr_salida = 10 * np.log10(np.mean(mensaje[validas] ** 2) / max(mse, 1e-30))
    return dict(t=t, mensaje=mensaje, portadora=portadora, transmitida=transmitida,
                recibida=recibida, recuperada=recuperada, validas=validas,
                frecuencia_rx=frecuencia_rx, rmse=np.sqrt(mse),
                correlacion=correlacion, snr_salida=snr_salida,
                fs=fs, fc=fc, fm=fm, desviacion=desviacion, margen=margen)


def graficar(r, titulo_canal):
    t = r['t']
    # Ventana interna para mostrar señales sin transitorios de borde.
    inicio = r['margen'] + 2 / r['fm']
    ventana = (t >= inicio) & (t < inicio + 4 / r['fm'])
    detalle = (t >= inicio) & (t < inicio + 1 / r['fm'])
    fig, axs = plt.subplots(3, 2, figsize=(13, 10), constrained_layout=True)
    fig.suptitle('Sistema FM: transmisor → canal → receptor\n' + titulo_canal)
    ms = t * 1000
    axs[0, 0].plot(ms[ventana], r['mensaje'][ventana])
    axs[0, 0].set_title('Mensaje: coseno de amplitud 1')
    axs[0, 1].plot(ms[detalle], r['portadora'][detalle], label='Portadora', alpha=.6)
    axs[0, 1].plot(ms[detalle], r['transmitida'][detalle], label='FM', alpha=.8)
    axs[0, 1].set_title('Portadora y señal FM transmitida')
    axs[0, 1].legend()
    axs[1, 0].plot(ms[detalle], r['recibida'][detalle], color='tab:orange')
    axs[1, 0].set_title('Señal recibida antes del filtro de canal')
    for clave, etiqueta in [('transmitida', 'Transmitida'), ('recibida', 'Recibida')]:
        f, p = welch(r[clave], fs=r['fs'], nperseg=min(8192, len(t)))
        axs[1, 1].plot(f / 1000, 10 * np.log10(p + 1e-20), label=etiqueta, alpha=.8)
    b = r['desviacion'] + r['fm']
    for borde in [r['fc'] - b, r['fc'] + b]:
        axs[1, 1].axvline(borde / 1000, ls='--', color='gray')
    axs[1, 1].set_xlim(max(0, (r['fc'] - 2*b) / 1000),
                          min(r['fs']/2000, (r['fc'] + 2*b) / 1000))
    axs[1, 1].set_title('Espectro y bordes aproximados de Carson')
    axs[1, 1].set_xlabel('Frecuencia [kHz]')
    axs[1, 1].set_ylabel('Densidad espectral [dB/Hz]')
    axs[1, 1].legend()
    axs[2, 0].plot(ms[ventana], r['mensaje'][ventana], label='Original', lw=2)
    axs[2, 0].plot(ms[ventana], r['recuperada'][ventana], '--', label='Recuperado')
    axs[2, 0].set_title(f"Recuperación: RMSE={r['rmse']:.4f}; r={r['correlacion']:.4f}")
    axs[2, 0].legend()
    axs[2, 1].plot(ms[ventana],
        (r['fc'] + r['desviacion'] * r['mensaje'][ventana]) / 1000,
        label='Frecuencia instantánea ideal', lw=2)
    axs[2, 1].plot(ms[ventana], r['frecuencia_rx'][ventana] / 1000,
                   label='Estimada antes del filtro de salida', alpha=.6)
    axs[2, 1].set_title('Frecuencia instantánea')
    axs[2, 1].set_ylabel('Frecuencia [kHz]')
    axs[2, 1].legend(fontsize=8)
    for i, ax in enumerate(axs.flat):
        ax.grid(alpha=.25)
        if i != 3:
            ax.set_xlabel('Tiempo [ms]')
        if i in (0, 1, 2, 4):
            ax.set_ylabel('Amplitud')
    return fig


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--fs', type=float, default=200000, help='Muestras/s')
    p.add_argument('--fc', type=float, default=20000, help='Frecuencia central en Hz')
    p.add_argument('--fm', type=float, default=500, help='Frecuencia del mensaje en Hz')
    p.add_argument('--desviacion', type=float, default=5000, help='Desviación pico en Hz')
    p.add_argument('--duracion', type=float, default=.2, help='Duración en segundos')
    p.add_argument('--snr', type=float, default=15, help='SNR de entrada en dB, sobre toda la banda muestreada')
    p.add_argument('--semilla', type=int, default=42)
    p.add_argument('--sin-ruido', action='store_true')
    p.add_argument('--guardar', metavar='IMAGEN.png', help='Guardar las gráficas')
    p.add_argument('--no-mostrar', action='store_true', help='Ejecutar sin abrir ventana')
    a = p.parse_args()
    try:
        r = simular(a.fs, a.fc, a.fm, a.desviacion, a.duracion,
                    a.snr, a.sin_ruido, a.semilla)
    except ValueError as exc:
        p.error(str(exc))
    print(f'Índice de modulación β: {a.desviacion/a.fm:.2f}')
    print(f'Ancho de banda de Carson: {2*(a.desviacion+a.fm):.0f} Hz')
    print(f'Frecuencia instantánea ideal: {a.fc-a.desviacion:.0f} a {a.fc+a.desviacion:.0f} Hz')
    print(f"RMSE: {r['rmse']:.5f}; correlación: {r['correlacion']:.5f}")
    print(f"Relación señal/error de salida: {r['snr_salida']:.2f} dB")
    titulo = 'Canal sin ruido' if a.sin_ruido else f'Canal AWGN: SNR de entrada = {a.snr:g} dB'
    fig = graficar(r, titulo)
    if a.guardar:
        fig.savefig(a.guardar, dpi=160)
        print('Gráficas guardadas en:', a.guardar)
    if not a.no_mostrar:
        plt.show()
    plt.close(fig)


if __name__ == '__main__':
    main()
