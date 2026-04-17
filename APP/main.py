from fastapi import FastAPI, UploadFile, File
from converter import extraer_texto_pdf
from file_manager import guardar_txt

app = FastAPI()


@app.get("/")
def inicio():
    return {"mensaje": "API funcionando"}


@app.post("/upload")
async def subir_pdf(file: UploadFile = File(...)):
    try:
        # Extraer texto
        texto = extraer_texto_pdf(file.file)

        if not texto:
            return {"error": "No se pudo extraer texto"}

        # Guardar en txt (temporal, para pruebas)
        guardar_txt(texto, "resultado.txt")

        return {
            "mensaje": "Archivo procesado correctamente",
            "preview": texto[:200]  # solo una parte
        }

    except Exception as e:
        return {"error": str(e)}