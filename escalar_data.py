import matplotlib.pyplot as plt
import numpy as np


# lista de datos
pixeles = [562, 410, 327, 254, 78]
medida_mm = [10.7, 8.1, 5.9, 5, 1.9]

# inferir la ecuación de la recta f(pixeles) = m * pixeles + b
m, b = np.polyfit(pixeles, medida_mm, 1)
# print equation
print(f"y = {m} * x + {b}")

# graficar los datos
plt.plot(pixeles, medida_mm, 'o', label='Datos')
plt.plot(pixeles, m * np.array(pixeles) + b, label='Ajuste lineal')
plt.xlabel('Pixeles')
plt.ylabel('Medida (mm)')
plt.legend()
plt.show()