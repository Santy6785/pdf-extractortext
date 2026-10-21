/**
 * Validaciones en cliente y formateo de archivos.
 * Mantiene intactos los textos literales y comportamientos del front original.
 */

export function validateFile(file, maxUploadMb = 10) {
  if (!file) {
    return {
      isValid: false,
      error: 'Por favor selecciona un archivo PDF primero.'
    };
  }

  // Validar tipo de archivo (MIME o extension)
  const isPdfMime = file.type === 'application/pdf';
  const hasPdfExtension = Boolean(file.name && file.name.toLowerCase().endsWith('.pdf'));

  if (!isPdfMime && !hasPdfExtension) {
    return {
      isValid: false,
      error: 'El archivo debe ser un PDF. Formato no válido.'
    };
  }

  // Validar tamaño maximo (en bytes)
  const maxSizeBytes = maxUploadMb * 1024 * 1024;
  if (file.size > maxSizeBytes) {
    return {
      isValid: false,
      error: `El archivo es demasiado grande. Tamaño máximo: ${maxUploadMb}MB.`
    };
  }

  return {
    isValid: true,
    error: null
  };
}

export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
