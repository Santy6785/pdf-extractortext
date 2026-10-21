/**
 * Cliente HTTP para la API del servicio de extracción de PDFs.
 * 
 * Capa Modelo / Red: Aísla completamente el acceso HTTP y el contrato de la API.
 * Cualquier cambio en endpoints, prefijos o códigos de error solo se modifica aquí.
 */

export class ApiError extends Error {
  constructor(message, status = 500, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export class ApiClient {
  /**
   * @param {Object} options
   * @param {string} [options.basePath=''] URL base o prefijo de ruta (e.g. "" para rutas relativas)
   * @param {number} [options.timeoutMs=30000] Tiempo límite de petición en milisegundos
   * @param {number} [options.maxRetries=3] Máximo de reintentos para peticiones idempotentes
   * @param {number} [options.retryBaseDelayMs=300] Demora base en ms para backoff exponencial
   */
  constructor(options = {}) {
    this.basePath = (options.basePath || '').replace(/\/+$/, '');
    this.timeoutMs = options.timeoutMs ?? 30000;
    this.maxRetries = options.maxRetries ?? 3;
    this.retryBaseDelayMs = options.retryBaseDelayMs ?? 300;
  }

  /**
   * Construye la URL combinando basePath y la ruta relativa.
   * @param {string} path 
   * @returns {string}
   */
  _buildUrl(path) {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${this.basePath}${cleanPath}`;
  }

  /**
   * Realiza una petición fetch con timeout mediante AbortController.
   */
  async _fetchWithTimeout(url, options, timeoutMs) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      return response;
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new ApiError(
          'Tiempo de espera agotado al conectar con el servidor.',
          408
        );
      }
      throw new ApiError(
        'Error de conexión con el servidor. Verifique su red e intente nuevamente.',
        0,
        err.message
      );
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Parsea defensivamente la respuesta (tolera JSON, listas Pydantic o texto plano / HTML de proxy).
   */
  async _parseResponseBody(response) {
    const rawText = await response.text();
    if (!rawText || !rawText.trim()) {
      return null;
    }
    try {
      return JSON.parse(rawText);
    } catch {
      // No es JSON (e.g. error HTML generado por Traefik o Nginx)
      return { raw: rawText };
    }
  }

  /**
   * Normaliza los mensajes de error según el contrato de la UI original y la API.
   */
  _normalizeErrorMessage(status, parsedBody) {
    let rawDetail = '';
    if (parsedBody && parsedBody.detail) {
      if (typeof parsedBody.detail === 'string') {
        rawDetail = parsedBody.detail;
      } else if (Array.isArray(parsedBody.detail)) {
        // Errores de validación Pydantic
        rawDetail = parsedBody.detail
          .map((item) => `${item.loc?.join('.') || 'param'}: ${item.msg || 'error'}`)
          .join(', ');
      } else {
        rawDetail = JSON.stringify(parsedBody.detail);
      }
    } else if (parsedBody && parsedBody.raw) {
      rawDetail = parsedBody.raw;
    }

    // Traducción fiel a los mensajes de la UI original
    if (status === 409 || rawDetail.includes('already exists') || rawDetail.includes('mismo checksum')) {
      return 'El archivo ya existe en el sistema.';
    }
    if (rawDetail.includes('PDF') || rawDetail.includes('pdf')) {
      return 'El archivo no es un PDF válido o está corrupto.';
    }
    if (rawDetail.includes('encrypt')) {
      return 'El PDF está encriptado o protegido con contraseña.';
    }
    if (rawDetail.includes('process') || rawDetail.includes('corrupto') || rawDetail.includes('dañado')) {
      return 'No se pudo procesar el PDF. Verifica que no esté dañado.';
    }
    if (status === 400 && rawDetail.includes('tamaño')) {
      return 'El archivo es demasiado grande. Tamaño máximo: 10MB.';
    }
    if (status === 404) {
      return rawDetail || 'Documento no encontrado.';
    }
    if (status === 429) {
      return 'Demasiadas solicitudes. Por favor, espere un momento antes de reintentar.';
    }
    if (status === 502 || status === 503 || status === 504) {
      return 'Servicio temporalmente no disponible. Por favor, reintente en unos instantes.';
    }

    return rawDetail || 'Error al procesar el archivo';
  }

  /**
   * Pausa la ejecución para el backoff exponencial.
   */
  _delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Ejecuta peticiones HTTP gestionando reintentos (solo para métodos idempotentes como GET).
   */
  async _request(method, path, options = {}) {
    const isIdempotentGet = method.toUpperCase() === 'GET';
    const shouldRetry = Boolean(options.allowRetry ?? isIdempotentGet);
    const maxAttempts = shouldRetry ? this.maxRetries : 1;
    const url = this._buildUrl(path);

    let lastError = null;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const fetchOptions = {
          method,
          headers: options.headers || {},
          body: options.body
        };

        const response = await this._fetchWithTimeout(
          url,
          fetchOptions,
          options.timeoutMs ?? this.timeoutMs
        );

        if (response.status === 204) {
          return true;
        }

        const parsedBody = await this._parseResponseBody(response);

        if (!response.ok) {
          const isTransientStatus = [502, 503, 504, 408].includes(response.status);
          const errorMessage = this._normalizeErrorMessage(response.status, parsedBody);
          const error = new ApiError(errorMessage, response.status, parsedBody);

          // Si es reintentable, idempotente y quedan intentos
          if (shouldRetry && isTransientStatus && attempt < maxAttempts) {
            const delayMs = this.retryBaseDelayMs * Math.pow(2, attempt - 1);
            await this._delay(delayMs);
            continue;
          }

          throw error;
        }

        return parsedBody;
      } catch (err) {
        lastError = err;
        // Si el fallo fue de red y es un método idempotente que permite reintentos
        if (shouldRetry && attempt < maxAttempts && (err.status === 0 || [502, 503, 504, 408].includes(err.status))) {
          const delayMs = this.retryBaseDelayMs * Math.pow(2, attempt - 1);
          await this._delay(delayMs);
          continue;
        }
        throw lastError;
      }
    }

    throw lastError;
  }

  /**
   * Subir un documento PDF al backend para extracción síncrona.
   * Endpoint: POST /api/v1/documents/upload
   * NUNCA se reintenta automáticamente para evitar dobles envíos.
   * 
   * @param {File|Blob} file 
   * @returns {Promise<{id: string, checksum: string, extracted_text: string, created_at: string}>}
   */
  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file, file.name || 'document.pdf');

    return this._request('POST', '/api/v1/documents/upload', {
      body: formData,
      allowRetry: false // POST nunca se reintenta automáticamente
    });
  }

  /**
   * Listar documentos paginados.
   * Endpoint: GET /api/v1/documents/?skip=0&limit=20
   * Idempotente: se reintenta con backoff en caso de fallos transitorios.
   */
  async listDocuments({ skip = 0, limit = 20 } = {}) {
    const query = new URLSearchParams();
    if (skip !== undefined) query.set('skip', String(skip));
    if (limit !== undefined) query.set('limit', String(limit));

    const path = `/api/v1/documents/?${query.toString()}`;
    return this._request('GET', path, { allowRetry: true });
  }

  /**
   * Obtener un documento por su identificador.
   * Endpoint: GET /api/v1/documents/{id}
   */
  async getDocument(id) {
    if (!id) throw new ApiError('El identificador de documento es requerido', 400);
    return this._request('GET', `/api/v1/documents/${encodeURIComponent(id)}`, {
      allowRetry: true
    });
  }

  /**
   * Actualizar el texto extraído de un documento existente.
   * Endpoint: PUT /api/v1/documents/{id}
   * No se reintenta automáticamente.
   */
  async updateDocument(id, extractedText) {
    if (!id) throw new ApiError('El identificador de documento es requerido', 400);
    return this._request('PUT', `/api/v1/documents/${encodeURIComponent(id)}`, {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ extracted_text: extractedText }),
      allowRetry: false
    });
  }

  /**
   * Eliminar un documento por su ID.
   * Endpoint: DELETE /api/v1/documents/{id}
   * No se reintenta automáticamente.
   */
  async deleteDocument(id) {
    if (!id) throw new ApiError('El identificador de documento es requerido', 400);
    return this._request('DELETE', `/api/v1/documents/${encodeURIComponent(id)}`, {
      allowRetry: false
    });
  }

  /**
   * Consultar el endpoint de health check del front/proxy.
   * Endpoint: GET /health
   */
  async checkHealth() {
    return this._request('GET', '/health', { allowRetry: true });
  }
}
