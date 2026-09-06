import os

def archivo_existe(ruta):
    return os.path.exists(ruta)

def guardar_txt(texto, nombre_archivo):
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(texto)