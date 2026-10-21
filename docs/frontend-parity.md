# Inventario de Paridad de Front-end y Decisiones Arquitectónicas

> Documento de control de fidelidad visual y funcional respecto a la interfaz original del monolito (`APP/api/static/index.html`), comparación con la base inicial (`frontend/index.html`) y especificación de decisiones técnicas para el microservicio de front-end.

---

## 1. Inventario Exhaustivo de la UI Original

### 1.1 Estructura y Secciones
1. **Barra de Navegación (`<nav>`)**:
   - Fondo blanco, borde inferior sutil (`border-gray-200`), sombra suave (`shadow-sm`).
   - Icono vectorial SVG de documento en color índigo (`text-indigo-600`).
   - Título de aplicación: `Extractor de Documentos PDF` (fuente `Inter`, peso `bold`, color `text-gray-900`, tamaño `text-xl`).
   - Enlace a documentación: `Documentación API` (`text-gray-600 hover:text-indigo-600 transition-colors`).
2. **Encabezado Principal (`<header>` / Hero)**:
   - Título principal `<h1>`: `Extrae texto de tus PDFs` (`text-4xl font-bold text-gray-900 mb-4`).
   - Subtítulo explicativo `<p>`: `Sube tu archivo PDF y obtén el texto extraído al instante. Procesamiento seguro, rápido y 100% en memoria.` (`text-lg text-gray-600 max-w-2xl mx-auto`).
3. **Tarjeta de Subida (`bg-white rounded-2xl shadow-lg p-8 mb-8`)**:
   - **Zona Drag & Drop (`#dropZone`)**: Borde discontinuo SVG personalizado índigo (`#6366F1`), bordes redondeados (`rounded-2xl`), padding generoso (`p-12`), cursor interactivo (`cursor-pointer`).
     - Icono de subida en la nube (`h-16 w-16 text-indigo-400`).
     - Título: `Arrastra y suelta tu PDF aquí` (`text-xl font-semibold text-gray-900 mb-2`).
     - Indicación secundaria: `o haz clic para seleccionar un archivo` (`text-gray-500 mb-4`).
     - Restricción de formato y peso: `Solo archivos PDF (máximo 10MB)` (`text-sm text-gray-400`).
     - Input oculto: `<input type="file" id="fileInput" accept=".pdf" class="hidden">`.
   - **Indicador de Archivo Seleccionado (`#fileInfo`, oculto por defecto)**:
     - Contenedor con fondo azulino (`bg-indigo-50 border border-indigo-200 rounded-lg p-4`).
     - Icono de documento en índigo (`h-8 w-8 text-indigo-600`).
     - Nombre del archivo (`#fileName`, `font-medium text-gray-900`).
     - Tamaño formateado (`#fileSize`, `text-sm text-gray-500`).
     - Botón de limpieza/cancelación (`X`, `hover:text-red-500`).
   - **Botón de Acción Principal (`#processBtn`)**:
     - Botón de ancho completo (`w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-lg shadow-md disabled:bg-gray-300 disabled:cursor-not-allowed`).
     - Texto en reposo: `Procesar y Extraer Texto`.
     - Texto durante procesamiento: `Procesando...`.
     - Spinner de carga: `.loader` CSS circular con animación de giro continua.
   - **Bloque de Mensaje de Error (`#errorMessage`, oculto por defecto)**:
     - Fondo rojizo (`bg-red-50 border border-red-200 rounded-lg p-4`).
     - Icono de advertencia circular SVG (`text-red-500`).
     - Texto de error dinámico (`#errorText`, `text-red-700 font-medium`).
4. **Sección de Resultados (`#resultsSection`, oculta por defecto, animación `fade-in`)**:
   - **Tarjeta de Verificación (`Verificación`)**:
     - Icono de check verde en recuadro (`bg-green-100 text-green-600`).
     - Label: `Checksum (SHA-256)`.
     - Valor del Checksum (`#checksumValue`): tipografía monoespaciada, fondo gris, `break-all`.
     - Label: `Estado`.
     - Badge de estado: `Procesado correctamente` (`bg-green-100 text-green-800 rounded-full text-xs font-medium`).
   - **Tarjeta de Texto Extraído (`Texto Extraído`)**:
     - Icono de documento índigo.
     - Botón `Copiar`: icono SVG de portapapeles; conmuta temporalmente a icono de check + `Copiado` durante 2 segundos.
     - Textarea de solo lectura (`#extractedText`): `w-full h-64 p-4 bg-gray-50 border border-gray-200 text-gray-700 text-sm font-mono leading-relaxed resize-none`.
     - Botón `Descargar .txt`: color carbón (`bg-gray-900 hover:bg-gray-800 text-white font-medium py-2 px-4 rounded-lg`).
     - Botón `Eliminar documento`: opción para retirar el documento persistido.
5. **Sección de Características (Features Grid)**:
   - 3 columnas (`md:grid-cols-3`):
     - **Rápido**: `Procesamiento en segundos sin esperas innecesarias` (Icono rayo).
     - **Seguro**: `Procesamiento 100% en memoria, sin almacenar archivos` (Icono escudo/candado).
     - **Preciso**: `Extracción de texto fiel al documento original` (Icono check).
6. **Pie de Página (`<footer>`)**:
   - Texto centrado: `Extractor de Documentos PDF - Desarrollado con FastAPI y Arquitectura Limpia` (`text-center text-gray-500 text-sm`).

---

### 1.2 Estados de la Interfaz

| Estado | Elementos Afectados | Apariencia / Comportamiento |
|---|---|---|
| **Vacío (Inicial)** | `#dropZone` visible, `#fileInfo` oculto, `#processBtn` deshabilitado, `#errorMessage` oculto, `#resultsSection` oculto. | Zona de arrastre interactiva lista para recibir un archivo. |
| **Arrastrando (Drag-over)** | `#dropZone` | Clase `.drag-over` aplicada: fondo tintado `rgba(99, 102, 241, 0.1)`, escalado sutil `transform: scale(1.02)`. |
| **Archivo Seleccionado** | `#dropZone` visible, `#fileInfo` visible con nombre y tamaño legible (KB/MB), `#processBtn` habilitado (`disabled=false`). | Muestra detalles del archivo y permite pulsar el botón de procesar. |
| **Cargando (In Progress)** | `#processBtn` deshabilitado (`disabled=true`), `#btnText` cambia a `Procesando...`, `#btnLoader` visible, zona de arrastre bloqueada. | Indica que la petición HTTP multipart síncrona está en vuelo. Evita doble clic. |
| **Éxito (Procesado)** | `#resultsSection` visible con animación `.fade-in`, scroll suave hacia resultados. Checksum y texto extraído cargados. `#errorMessage` oculto. | Permite copiar al portapapeles y descargar el archivo `.txt`. |
| **Error (Validación o Servidor)**| `#errorMessage` visible con texto rojo específico, `#btnLoader` oculto, botón restablecido. | Permite corregir o reintentar sin romper el layout. |
| **Duplicado (Conflicto 409)** | `#errorMessage` visible con texto literal: `El archivo ya existe en el sistema.` | El backend detectó checksum idéntico previamente guardado en MongoDB. |

---

### 1.3 Validaciones en Cliente

1. **Tipo de Archivo:**
   - Condición: `file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')`
   - Mensaje literal: `El archivo debe ser un PDF. Formato no válido.`
2. **Tamaño Máximo:**
   - Condición: `file.size > 10 * 1024 * 1024` (10 MB, configurable en runtime vía `window.__CONFIG__.MAX_UPLOAD_MB`).
   - Mensaje literal: `El archivo es demasiado grande. Tamaño máximo: 10MB.`
3. **Intento de procesamiento sin archivo:**
   - Mensaje literal: `Por favor selecciona un archivo PDF primero.`

---

### 1.4 Mensajes Literales de Error y Traducción

| Condición detectada / Error devuelto | Mensaje visual mostrado al usuario |
|---|---|
| Archivo no es PDF (cliente) | `El archivo debe ser un PDF. Formato no válido.` |
| Tamaño > 10MB (cliente) | `El archivo es demasiado grande. Tamaño máximo: 10MB.` |
| Sin archivo seleccionado | `Por favor selecciona un archivo PDF primero.` |
| Error contiene substring `'PDF'` | `El archivo no es un PDF válido o está corrupto.` |
| Error contiene substring `'encrypt'` | `El PDF está encriptado o protegido con contraseña.` |
| Error contiene substring `'process'` | `No se pudo procesar el PDF. Verifica que no esté dañado.` |
| Error contiene substring `'already exists'` o código 409 | `El archivo ya existe en el sistema.` |
| Error de portapapeles | `No se pudo copiar al portapapeles.` |
| Errores de infraestructura (502 / 503 / 504) | `Servicio temporalmente no disponible. Por favor, reintente en unos instantes.` |
| Límite de peticiones (429) | `Demasiadas solicitudes. Por favor, espere un momento antes de reintentar.` |
| Timeout / Red inalcanzable | `Error de conexión con el servidor. Verifique su red e intente nuevamente.` |

---

## 2. Tabla de Llamadas HTTP del Front Original vs. Migrado

| Front | Método | Ruta | Payload | Respuesta Esperada | Códigos Manejados | Mensaje Mostrado |
|---|---|---|---|---|---|---|
| **Original Monolito** | `POST` | `/api/v1/documents/` | `multipart/form-data` con `file` | `text/plain` (.txt con texto plano). Checksum calculado con Web Crypto API en cliente. | 200, 400, 409, 422, 500 | Mensajes traducidos según substring del error. |
| **Base Inicial Migración** | `POST` | `https://extract.universidad.localhost/api/v1/documents/upload` | `multipart/form-data` con `file` | `application/json` (`DocumentResponseDTO` con `id`, `checksum`, `extracted_text`, `created_at`). | 200, 400, 409, 422, error genérico | Misma traducción de errores, extrayendo `data.checksum` y `data.extracted_text`. |
| **Microservicio Front Final** | `POST` | `/api/v1/documents/upload` (ruta relativa mediante proxy Traefik / Nginx) | `multipart/form-data` con `file` | `application/json` (`DocumentResponseDTO`). Checksum y texto extraído provistos por backend. | 200, 400, 404, 409, 422, 429, 502, 503, 504, Timeout | Mapeo idéntico de mensajes de negocio + mensajes claros y reintentables ante fallos de proxy / resiliencia. |
| **Microservicio Front Final (CRUD / Delete)** | `DELETE` | `/api/v1/documents/{id}` | Vacío | `204 No Content` | 204, 404, 502, 503, 504 | Elimina documento procesado para restablecer flujo de prueba de duplicados. |
| **Microservicio Front (Health)** | `GET` | `/health` | Vacío | `200 OK` `{"status":"ok","service":"frontend"}` | 200 | Endpoint estático servido por Nginx para Docker y Traefik health checks. |

---

## 3. Matriz de Paridad y Verificación Detallada

Leyenda:
- ✔ **Idéntico**: Comportamiento, estilo o texto 100% equivalente al monolito original.
- ⚠ **Desviación justificada**: Mejora técnica requerida por la arquitectura de microservicios / resiliencia (documentada).
- ✖ **Pendiente**: Tareas pendientes (Cero ítems pendientes).

| Componente / Característica | Estado | Justificación / Observación |
|---|---|---|
| **Tipografía Inter y paleta Tailwind** | ✔ Idéntico | Misma fuente Google Fonts `Inter` y clases CSS Tailwind oficiales. |
| **Borde punteado SVG y estilo .drag-zone** | ✔ Idéntico | Mismo patrón SVG codificado en base64 y animación de foco. |
| **Animación .loader de procesamiento** | ✔ Idéntico | Spinner circular CSS idéntico con rotación de 1 segundo. |
| **Animación .fade-in de resultados** | ✔ Idéntico | Transición de 0.5s con desplazamiento en Y idéntico. |
| **Barra de navegación con logo y texto** | ✔ Idéntico | `Extractor de Documentos PDF` con icono SVG idéntico. |
| **Enlace a documentación API** | ✔ Idéntico | Enlace relativo `/docs` configurable. |
| **Encabezado principal (Hero y subtítulo)** | ✔ Idéntico | `Extrae texto de tus PDFs` y bajada explicativa textual idéntica. |
| **Textos de la zona de arrastre** | ✔ Idéntico | `Arrastra y suelta tu PDF aquí`, `o haz clic para seleccionar un archivo`, `Solo archivos PDF (máximo 10MB)`. |
| **Visualización de archivo seleccionado** | ✔ Idéntico | Nombre de archivo, tamaño formateado (KB/MB) y botón `X`. |
| **Botón de procesamiento** | ✔ Idéntico | `Procesar y Extraer Texto` conmuta a `Procesando...` con `.loader`. |
| **Prevención de doble clic (Double submit)** | ⚠ Desviación justificada | Deshabilita explícitamente el botón y zona mientras `state.isLoading == true`. |
| **Mensajes de validación en cliente** | ✔ Idéntico | Textos literales exactos para no-PDF, tamaño excedido y archivo ausente. |
| **Mensajes de error del backend (400, 409, 422)** | ✔ Idéntico | Mapeo exacto a `El archivo no es un PDF válido...`, `El PDF está encriptado...`, `El archivo ya existe en el sistema.`, etc. |
| **Tarjeta de Verificación (Checksum SHA-256)** | ✔ Idéntico | Muestra SHA-256 del backend y badge `Procesado correctamente`. |
| **Tarjeta de Texto Extraído** | ✔ Idéntico | Textarea de solo lectura con estilos mono y leading-relaxed. |
| **Acción Copiar con feedback temporal** | ✔ Idéntico | Copia al portapapeles y conmuta a check verde + `Copiado` durante 2s. |
| **Acción Descargar .txt** | ✔ Idéntico | Descarga archivo `<nombre>.txt` mediante Blob en memoria. |
| **Acción Eliminar documento procesado** | ⚠ Desviación justificada | Botón discreto añadido para permitir el flujo de verificación E2E `Upload -> 409 Duplicate -> Delete`. |
| **Sección Características (Rápido, Seguro, Preciso)** | ✔ Idéntico | Las 3 tarjetas de pie de página idénticas. |
| **Pie de página (Footer)** | ✔ Idéntico | Texto centrado idéntico. |
| **Rutas relativas sin hosts hardcodeados** | ⚠ Desviación justificada | Eliminado host hardcodeado `https://extract.universidad.localhost`. Se usan rutas relativas `/api/v1/...`. |
| **Separación MVC en JavaScript** | ⚠ Desviación justificada | Model (`api-client.js`, `state.js`), View (`view.js`), Controller (`controller.js`). |
| **Configuración en runtime sin rebuild** | ⚠ Desviación justificada | Nginx ejecuta `envsubst` sobre `config.template.js` para producir `config.js`. |
| **Manejo de códigos Traefik (429, 502, 503, 504)** | ⚠ Desviación justificada | Mensajes amigables y reintentos automáticos con backoff SOLO para GET. |
| **Parseo defensivo de errores** | ⚠ Desviación justificada | Tolera respuestas JSON de FastAPI (string o lista de validación) y HTML de proxy. |
| **Endpoint /health estático en Nginx** | ⚠ Desviación justificada | Retorna `{"status":"ok","service":"frontend"}` con código 200 para Docker y Traefik. |
| **Logs JSON en Nginx sin datos sensibles** | ⚠ Desviación justificada | Registra método, ruta, código, latencia y tamaño; prohíbe contenidos o textos de PDFs. |
| **Parada ordenada por SIGQUIT** | ⚠ Desviación justificada | Permite que Nginx termine conexiones en vuelo antes del apagado. |

**Total de ítems pendientes (✖): 0**

---

## 4. Decisiones Técnicas y DevOps

1. **Separación MVC en JavaScript Moderno:**
   - **`api-client.js` (Model / Network Layer):** Único punto de contacto HTTP. Soporta `uploadDocument`, `listDocuments`, `getDocument`, `updateDocument`, `deleteDocument`, `checkHealth`. Implementa timeouts con `AbortController`, backoff exponencial en peticiones `GET`, parseo defensivo y normalización de errores.
   - **`state.js` (Model / State):** Contenedor observable de estado reactivo.
   - **`view.js` (View Layer):** Manipulación exclusiva del DOM, renderizado de badges, actualización de textos literales y animaciones.
   - **`controller.js` (Controller Layer):** Orquestación de eventos y casos de uso.
2. **Configuración en Runtime con Nginx (`config.js` y `envsubst`):**
   - Nginx ejecuta `/docker-entrypoint.d/40-generate-config.sh` que genera `/usr/share/nginx/html/config.js` a partir de `config.template.js` usando variables de entorno:
     - `API_BASE_PATH` (default: `""` para rutas relativas `/api/v1/...`).
     - `MAX_UPLOAD_MB` (default: `10`).
     - `REQUEST_TIMEOUT_MS` (default: `30000`).
3. **Observabilidad del Microservicio Front:**
   - La especificación de microservicios prevé `/health`, `/trace`, métricas y `/pause|/resume|/shutdown`. En el backend FastAPI están resueltas; en el microservicio de front-end estático (Nginx), se implementa un endpoint `/health` estático de alta eficiencia que retorna `200 OK` con JSON `{"status":"ok","service":"frontend"}`. Las trazas y métricas se manejan en Traefik y backend. El apagado seguro se gestiona mediante la señal `SIGQUIT` en Nginx con `stop_grace_period: 10s`.
4. **Logs JSON Estructurados:**
   - `nginx.conf` formatea los logs de acceso en JSON estándar hacia `/dev/stdout` y errores hacia `/dev/stderr`. No se registran datos sensibles.
5. **Consul:**
   - El repositorio actual no contiene infraestructura de Consul. Se documenta como pendiente la integración de registro en Service Mesh / Consul si se incorpora a nivel general en la infraestructura.
