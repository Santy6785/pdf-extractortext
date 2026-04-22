"""
Adaptadores de API - Endpoints HTTP.
Arquitectura Limpia: Esta capa es el adaptador primario que recibe
peticiones externas y las convierte en llamadas al dominio.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from APP.services.pdf_service import PdfService, PdfProcessingError


router = APIRouter(prefix="/api/v1", tags=["documents"])


def validate_pdf_file(file: UploadFile) -> None:
    """
    Valida que el archivo sea un PDF.
    
    Args:
        file: Archivo subido
        
    Raises:
        HTTPException: 400 si el archivo no es PDF
    """
    # Validar por content_type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"El archivo debe ser PDF. Tipo recibido: {file.content_type}"
        )
    
    # Validar por extensión
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe tener extensión .pdf"
        )


@router.post("/documents/")
async def upload_document(file: UploadFile = File(...)) -> dict:
    """
    Endpoint para subir y procesar un documento PDF.
    
    - Valida que sea PDF
    - Procesa 100% en memoria (sin guardar en disco)
    - Extrae texto y dimensiones
    - Calcula checksum SHA-256
    
    Returns:
        JSON con: nombre_archivo, checksum, dimensiones_paginas, texto_extraido
        
    Raises:
        HTTPException: 400 si no es PDF, 422 si está corrupto/encriptado
    """
    # 1. Validación de tipo de archivo
    validate_pdf_file(file)
    
    # 2. Leer archivo completamente en memoria (bytes)
    file_bytes = await file.read()
    
    # 3. Delegar al servicio de dominio
    pdf_service = PdfService()
    
    try:
        result = pdf_service.process_pdf(file_bytes, file.filename)
    except PdfProcessingError as e:
        # Convertir error de dominio a HTTP 422
        raise HTTPException(
            status_code=422,
            detail=f"No se pudo procesar el PDF: {str(e)}"
        )
    
    # 4. Retornar respuesta
    return {
        "nombre_archivo": result.nombre_archivo,
        "checksum": result.checksum,
        "dimensiones_paginas": result.dimensiones_paginas,
        "texto_extraido": result.texto_extraido
    }
