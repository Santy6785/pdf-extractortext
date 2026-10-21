# Contrato de API (OpenAPI / FastAPI) - Microservicio Backend

> **Fuente de verdad:** OpenAPI 3.1.0 generado automáticamente desde `app/main.py` y `app/api/routes.py` (inspección de código y exportación `docs/openapi.json`).  
> **Versión de la API:** 0.2.0  
> **Prefijo global:** `/api/v1`  
> **Mapeo Traefik / Origen:** Peticiones relativas del navegador dirigidas a `/api/v1/...` son enrutadas a la API backend sin `StripPrefix`.

---

## 1. Resumen de Endpoints del Backend

| Método | Ruta | Estado / Consumo Front | Descripción |
|---|---|---|---|
| `POST` | `/api/v1/documents/upload` | **Activo** | Subida y extracción síncrona de PDF, validación de SHA-256 y persistencia en MongoDB. |
| `POST` | `/api/v1/documents/` | **Obsoleto / Deprecated** | Endpoint legacy que retornaba `text/plain` (.txt). El front actual **NO** lo utiliza. |
| `GET` | `/api/v1/documents/` | Disponible (CRUD) | Listado paginado de documentos almacenados. |
| `GET` | `/api/v1/documents/{document_id}` | Disponible (CRUD) | Detalle de un documento por ID. |
| `PUT` | `/api/v1/documents/{document_id}` | Disponible (CRUD) | Actualización del texto extraído de un documento. |
| `DELETE` | `/api/v1/documents/{document_id}` | Disponible (CRUD) | Eliminación de un documento por ID. |
| `GET` | `/api/v1/health` | Backend Health | Estado de la API y verificación de conexión a MongoDB. |

---

## 2. Especificación Detallada de Contratos

### 2.1 `POST /api/v1/documents/upload` (Subida de PDF)
- **Propósito:** Endpoint principal de ingesta. Procesa el archivo en memoria (sin almacenar temporalmente en disco), calcula checksum SHA-256, comprueba duplicados, extrae texto y almacena en MongoDB.
- **Content-Type Request:** `multipart/form-data`
- **Request Body (Form Data):**
  - `file`: Binario del archivo (`application/pdf`, extensión obligatoria `.pdf`, tamaño máximo definido en configuración, por defecto 10 MB).
- **Respuestas:**
  - **`200 OK`**:
    - **Content-Type:** `application/json`
    - **Schema (`DocumentResponseDTO`):**
      ```json
      {
        "id": "string",
        "checksum": "string (sha256 hex)",
        "extracted_text": "string",
        "created_at": "string (ISO 8601 date-time)"
      }
      ```
  - **`400 Bad Request`**:
    - Validación de tipo MIME: `{"detail": "El archivo debe ser PDF. Tipo recibido: <mime>"}`
    - Validación de extensión: `{"detail": "El archivo debe tener extension .pdf"}`
    - Validación de tamaño: `{"detail": "El archivo excede el tamaño máximo permitido de 10MB"}`
  - **`409 Conflict`**:
    - Documento duplicado (mismo checksum SHA-256 existente en base de datos):
      `{"detail": "Ya existe un documento con el mismo checksum"}`
  - **`422 Unprocessable Entity`**:
    - Fallo al leer o parsear PDF corrupto / protegido:
      `{"detail": "No se pudo procesar el PDF: <mensaje_error>"}`
    - Error de validación de esquema FastAPI / Pydantic:
      `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`

---

### 2.2 `POST /api/v1/documents/` (Legacy / Deprecated)
- **Estado:** Marcado explícitamente como `deprecated: true`.
- **Content-Type Request:** `multipart/form-data` con campo `file`.
- **Respuesta 200:** `text/plain` con encabezado `Content-Disposition: attachment; filename="<nombre>.txt"`.
- **Análisis de consumo:** El frontend original del monolito (`APP/api/static/index.html`) utilizaba esta ruta y calculaba el checksum en el cliente. En la versión actual bajo migración (`frontend/index.html`), este endpoint fue sustituido por `/api/v1/documents/upload`. **El frontend actual NO lo consume.**

---

### 2.3 `GET /api/v1/documents/` (Listado Paginado)
- **Propósito:** Obtener lista resumida de documentos ordenados / paginados.
- **Query Parameters:**
  - `skip` (opcional, entero, `ge=0`, default: `0`): Número de documentos a omitir.
  - `limit` (opcional, entero, `ge=1`, `le=100`, default: según `Settings.default_page_size` = `20`): Cantidad máxima a retornar.
- **Respuestas:**
  - **`200 OK`**:
    - **Content-Type:** `application/json`
    - **Schema:** Array de `DocumentListDTO`:
      ```json
      [
        {
          "id": "string",
          "checksum": "string",
          "created_at": "string (ISO 8601 date-time)"
        }
      ]
      ```
  - **`422 Unprocessable Entity`**: Si los parámetros no cumplen restricciones (e.g. `limit=0` o `skip=-1`). Retorna lista `detail` de validación Pydantic.

---

### 2.4 `GET /api/v1/documents/{document_id}` (Detalle de Documento)
- **Propósito:** Consultar el contenido íntegro y metadatos de un documento por su identificador.
- **Path Parameters:**
  - `document_id` (string, obligatorio): ID del documento (ObjectId string).
- **Respuestas:**
  - **`200 OK`**: `DocumentResponseDTO` (`{ "id", "checksum", "extracted_text", "created_at" }`).
  - **`404 Not Found`**: `{"detail": "Documento con id <document_id> no encontrado"}`.
  - **`422 Unprocessable Entity`**: Si el formato de parámetros de ruta no es válido.

---

### 2.5 `PUT /api/v1/documents/{document_id}` (Actualización de Texto Extraído)
- **Propósito:** Modificar el texto extraído asociado a un documento.
- **Path Parameters:**
  - `document_id` (string, obligatorio).
- **Content-Type Request:** `application/json`
- **Request Body (`DocumentUpdateDTO`):**
  ```json
  {
    "extracted_text": "string (obligatorio)"
  }
  ```
- **Respuestas:**
  - **`200 OK`**: `DocumentResponseDTO` con el texto actualizado.
  - **`404 Not Found`**: `{"detail": "Documento con id <document_id> no encontrado"}`.
  - **`422 Unprocessable Entity`**: Si falta `extracted_text` o el tipo no es string.

---

### 2.6 `DELETE /api/v1/documents/{document_id}` (Eliminación)
- **Propósito:** Eliminar físicamente el documento de la base de datos MongoDB.
- **Path Parameters:**
  - `document_id` (string, obligatorio).
- **Respuestas:**
  - **`204 No Content`**: Eliminado exitosamente (cuerpo vacío).
  - **`404 Not Found`**: `{"detail": "Documento con id <document_id> no encontrado"}`.

---

### 2.7 `GET /api/v1/health` (Health Check del Backend)
- **Propósito:** Verificación de disponibilidad de la API y conectividad con MongoDB.
- **Respuestas:**
  - **`200 OK`**:
    ```json
    {
      "status": "healthy",
      "database": "connected",
      "version": "0.2.0"
    }
    ```
  - **`503 Service Unavailable`**:
    ```json
    {
      "status": "unhealthy",
      "database": "disconnected",
      "version": "0.2.0"
    }
    ```
    o `{ "status": "unhealthy", "error": "...", "version": "0.2.0" }`.

---

## 3. Códigos de Estado y Manejo Defensivo en el Cliente

| Código HTTP | Causa | Formato Payload Backend | Acción en Cliente Front |
|---|---|---|---|
| `200` | Operación exitosa (Upload, List, Get, Update). | JSON estructurado | Procesar datos y actualizar vista. |
| `204` | Eliminación exitosa (Delete). | Sin contenido | Notificar éxito y limpiar/actualizar vista. |
| `400` | Archivo no PDF, extensión errónea o tamaño > 10MB. | JSON: `{"detail": "..."}` | Mostrar mensaje específico al usuario. |
| `404` | Documento no existe en MongoDB. | JSON: `{"detail": "Documento con id ... no encontrado"}` | Mostrar aviso de no encontrado. |
| `409` | Checksum SHA-256 duplicado. | JSON: `{"detail": "Ya existe un documento con el mismo checksum"}` | Mostrar mensaje de duplicado en UI. |
| `422` | PDF ilegible/corrupto o error de esquema Pydantic. | JSON: `{"detail": "..."}` o `{"detail": [...]}` | Parsear defensivamente (string o array de errores) y presentar mensaje legible. |
| `429` | Rate limit Traefik excedido. | Texto o JSON de proxy | Notificar límite alcanzado y ofrecer reintento manual. |
| `502 / 503 / 504` | Backend caído / circuito abierto Traefik / gateway timeout. | HTML/texto de Traefik o Nginx | No romper UI; mostrar error de servicio no disponible y habilitar reintento manual. |
| `Timeout / Red` | Petición abortada o fallo de red. | Excepción TypeError/DOMException | Notificar fallo de conexión/timeout y reintentar sólo si es GET. |
