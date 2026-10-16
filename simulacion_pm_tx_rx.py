#!/usr/bin/env python3
"""Transmisión y recepción PM en representación compleja I/Q.

Instalar: python3 -m pip install numpy scipy matplotlib
Ejecutar: python3 simulacion_pm_tx_rx.py
Opciones: --beta 2 --fm 1000 --snr 10 --guardar resultado.png
Canal ideal: --sin-ruido
Sin ventana: --no-mostrar --guardar resultado.png

Se usa una referencia coherente de frecuencia y un preámbulo de fase conocida.
Los filtros de fase cero permiten análisis fuera de línea, no tiempo real.
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfiltfilt, welch


def simular(fs=200000., fc=20000., fm=500., beta=1.5, duracion=.2,
            snr_db=15., sin_ruido=False, semilla=42):
    """Devuelve señales y métricas. beta es la desviación pico en radianes."""
    if not all(np.isfinite(v) and v > 0 for v in (fs, fc, fm, beta, duracion)):
        raise ValueError('fs, fc, fm, beta y duracion deben ser positivos y finitos.')
    if not np.isfinite(snr_db):
        raise ValueError('SNR debe ser finita. Use --sin-ruido para el canal ideal.')
    banda = 1.4 * (beta + 1) * fm
    if fc - banda <= 0 or fc + banda >= fs/2:
        raise ValueError('La banda práctica fc ± 1.4*(beta+1)*fm debe quedar entre 0 y fs/2.')
    margen = max(.005, 5/fm)
    preambulo = 4*margen
    if duracion <= preambulo + 5*margen:
        raise ValueError(f'Use --duracion mayor que {preambulo+5*margen:.3f} s.')
    t = np.arange(int(fs*duracion))/fs
    # Preámbulo sin mensaje: proporciona una referencia de fase conocida.
    mensaje = np.where(t < preambulo, 0., np.sin(2*np.pi*fm*(t-preambulo)))
    fase_mensaje = beta*mensaje
    tx = np.exp(1j*(2*np.pi*fc*t + fase_mensaje))
    rng = np.random.default_rng(semilla)
    if sin_ruido:
        ruido = np.zeros(t.size, dtype=complex)
    else:
        # Potencia total compleja del ruido = 10^(-SNR/10), potencia TX = 1.
        sigma = np.sqrt(10**(-snr_db/10)/2)
        ruido = sigma*(rng.normal(size=t.size)+1j*rng.normal(size=t.size))
    rx = tx+ruido
    # Conversión coherente a banda base con oscilador local ideal.
    base = rx*np.exp(-1j*2*np.pi*fc*t)
    filtro_canal = butter(6, banda, fs=fs, output='sos')
    base_filtrada = sosfiltfilt(filtro_canal, base)
    fase_rx = np.unwrap(np.angle(base_filtrada))
    entrenamiento = (t >= margen) & (t < preambulo-margen)
    # Corrige la referencia constante, incluida la rama de 2*pi del unwrap.
    fase_rx -= np.mean(fase_rx[entrenamiento])
    cruda = fase_rx/beta
    filtro_mensaje = butter(6, 1.5*fm, fs=fs, output='sos')
    recuperada = sosfiltfilt(filtro_mensaje, cruda)
    validas = (t > preambulo+2*margen) & (t < t[-1]-margen)
    error = mensaje[validas]-recuperada[validas]
    rmse = np.sqrt(np.mean(error**2))
    correlacion = np.corrcoef(mensaje[validas], recuperada[validas])[0, 1]
    relacion = 10*np.log10(np.mean(mensaje[validas]**2)/max(rmse**2, 1e-30))
    fi_ideal = np.where(t < preambulo, fc,
                       fc+beta*fm*np.cos(2*np.pi*fm*(t-preambulo)))
    return dict(t=t, mensaje=mensaje, tx=tx, rx=rx, fase=fase_mensaje,
                fase_rx=fase_rx, recuperada=recuperada, validas=validas,
                fi=fi_ideal, fs=fs, fc=fc, fm=fm, beta=beta,
                margen=margen, preambulo=preambulo, rmse=rmse,
                correlacion=correlacion, relacion=relacion)


def graficar(r, canal):
    t=r['t']; inicio=r['preambulo']+2*r['margen']
    v=(t>inicio)&(t<inicio+4/r['fm'])
    d=(t>inicio)&(t<inicio+1/r['fm'])
    ms=t*1000
    fig, ax=plt.subplots(3, 2, figsize=(13, 10), constrained_layout=True)
    fig.suptitle('Sistema PM: transmisión, canal y recepción coherente\n'+canal)
    ax[0,0].plot(ms[v],r['mensaje'][v]); ax[0,0].set_title('Mensaje original')
    ax[0,1].plot(ms[d],r['tx'].real[d],label='PM transmitida (I)')
    ax[0,1].plot(ms[d],r['rx'].real[d],alpha=.55,label='Recibida (I)')
    ax[0,1].set_title('Señales en el canal'); ax[0,1].legend()
    ax[1,0].plot(ms[v],r['fase'][v],label='Ideal')
    ax[1,0].plot(ms[v],r['fase_rx'][v],alpha=.7,label='Estimada')
    ax[1,0].set_title('Desviación de fase [rad]'); ax[1,0].legend()
    for clave, etiqueta in [('tx','Transmitida'),('rx','Recibida')]:
        f,p=welch(r[clave],fs=r['fs'],nperseg=min(8192,len(t)),return_onesided=False)
        idx=np.argsort(f)
        ax[1,1].plot(f[idx]/1000,10*np.log10(p[idx]+1e-20),label=etiqueta,alpha=.8)
    b=(r['beta']+1)*r['fm']
    for borde in [r['fc']-b,r['fc']+b]: ax[1,1].axvline(borde/1000,color='gray',ls='--')
    ax[1,1].set_xlim((r['fc']-2*b)/1000,(r['fc']+2*b)/1000)
    ax[1,1].set_title('Espectro y referencia de Carson')
    ax[1,1].set_xlabel('Frecuencia [kHz]'); ax[1,1].set_ylabel('PSD [dB/Hz]');ax[1,1].legend()
    ax[2,0].plot(ms[v],r['mensaje'][v],label='Original',lw=2)
    ax[2,0].plot(ms[v],r['recuperada'][v],'--',label='Recuperado')
    ax[2,0].set_title(f"Recuperación: RMSE={r['rmse']:.4f}");ax[2,0].legend()
    ax[2,1].plot(ms[v],r['fi'][v]/1000,color='tab:purple')
    ax[2,1].set_title('Frecuencia instantánea ideal [kHz]')
    for i,a in enumerate(ax.flat):
        a.grid(alpha=.25)
        if i!=3:a.set_xlabel('Tiempo [ms]')
    return fig


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    for nombre,valor in [('fs',200000),('fc',20000),('fm',500),('beta',1.5),('duracion',.2),('snr',15)]:
        p.add_argument('--'+nombre,type=float,default=valor)
    p.add_argument('--semilla',type=int,default=42)
    p.add_argument('--sin-ruido',action='store_true')
    p.add_argument('--no-mostrar',action='store_true')
    p.add_argument('--guardar',metavar='IMAGEN.png')
    a=p.parse_args()
    try:r=simular(a.fs,a.fc,a.fm,a.beta,a.duracion,a.snr,a.sin_ruido,a.semilla)
    except ValueError as exc:p.error(str(exc))
    print(f'Índice PM y desviación de fase: {a.beta:g} rad')
    print(f'Desviación de frecuencia: {a.beta*a.fm:g} Hz')
    print(f'Carson: {2*(a.beta+1)*a.fm:g} Hz')
    print(f"RMSE: {r['rmse']:.5f}; correlación: {r['correlacion']:.5f}")
    print(f"Relación señal/error de salida: {r['relacion']:.2f} dB")
    fig=graficar(r,'Sin ruido' if a.sin_ruido else f'SNR de entrada: {a.snr:g} dB')
    if a.guardar:fig.savefig(a.guardar,dpi=160)
    if not a.no_mostrar:plt.show()
    plt.close(fig)


if __name__=='__main__':main()
