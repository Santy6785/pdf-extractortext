from converter import pdf_a_word, word_a_pdf
from file_manager import archivo_existe

def main():
    print("1: PDF a Word")
    print("2: Word a PDF")

    opcion = input("Elegí una opción: ")

    origen = input("Ruta del archivo de entrada: ")
    destino = input("Ruta del archivo de salida: ")

    if not archivo_existe(origen):
        print("El archivo no existe.")
        return

    if opcion == "1":
        ok = pdf_a_word(origen, destino)
    elif opcion == "2":
        ok = word_a_pdf(origen, destino)
    else:
        print("Opción inválida")
        return

    if ok:
        print("Conversión exitosa")
    else:
        print("Falló la conversión")


if __name__ == "__main__":
    main()