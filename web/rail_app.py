def ajustar_rail_soldadura(longitud_actual_alambre):
    # Condición para determinar el signo del ajuste en la estación de soldadura
    if longitud_actual_alambre < 270:
        ajuste = abs(longitud_actual_alambre - 270)
        print(f"Ajuste positivo en riel de soldadura: {ajuste} cm")
        return ajuste
    else:
        ajuste = -abs(longitud_actual_alambre - 270)
        print(f"Ajuste negativo en riel de soldadura: {ajuste} cm")
        return ajuste

def ajustar_rail_recocido(longitud_actual_alambre):
    # Condición para determinar el signo del ajuste en la estación de recocido
    if longitud_actual_alambre < 270:
        ajuste = -abs(longitud_actual_alambre - 270)
        print(f"Ajuste negativo en riel de recocido: {ajuste} cm")
        return ajuste
    else:
        ajuste = abs(longitud_actual_alambre - 270)
        print(f"Ajuste positivo en riel de recocido: {ajuste} cm")
        return ajuste

def estado_esmerilado():
    # Simulación del estado de la estación de esmerilado
    print("Esmerilado estatico")

# Longitudes de los alambres
longitud_alambre1 = 272  # entre soldadora y esmeriladora 
longitud_alambre2 = 272  # estre esmeril y recocido

# Carrera de las estaciones
carrera_estacion = 120  # 1.2 metros

# Ajustes en la estación de soldadura
ajuste_soldadura = ajustar_rail_soldadura(longitud_alambre1)

# Estado de esmerilado
estado_esmerilado()

# Ajustes en la estación de recocido
ajuste_recocido = ajustar_rail_recocido(longitud_alambre2)

# Determinar cuál de los ajustes es mayor y restarlo a la carrera restante
mayor_ajuste = max(abs(ajuste_soldadura), abs(ajuste_recocido))
carrera_restante = carrera_estacion - mayor_ajuste
print(f"Carrera restante del riel lineal: {carrera_restante} cm")

# Calcular la velocidad necesaria para realizar la carrera restante en 60 segundos
tiempo_objetivo = 60  # en segundos
velocidad_necesaria = carrera_restante / tiempo_objetivo
print(f"Velocidad necesaria para realizar la carrera en {tiempo_objetivo} segundos: {velocidad_necesaria} cm/s")