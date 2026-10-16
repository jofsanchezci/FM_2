from scipy import signal
import numpy as np
import matplotlib.pyplot as plt

fs = 1000
t = np.arange(0, 1, 1/fs)
x = np.sin(2 * np.pi * 50 * t) + 0.5 * np.random.randn(len(t))

# Filtro Butterworth pasa-bajos a 100 Hz
b, a = signal.butter(4, 100 / (fs / 2), btype="low")
y = signal.filtfilt(b, a, x)
plt.plot(x,'r--')
plt.plot(y,'b--')
plt.grid()
plt.show()