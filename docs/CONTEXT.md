# Contexto Arquitectónico y Seams del Sistema

> **Estado:** Aceptado
> **Fecha:** 2026-09-15
> **Issue relacionado:** #50 — Definir los seams con el equipo y documentarlos
> **Contexto:** Reconstrucción de la suite de tests con TDD real + CI.

## 1. Propósito

Este documento formaliza los **seams** (puntos de costura o desacople arquitectónico) del proyecto
`pdf-extractortext`. Un seam es un lugar del sistema donde el comportamiento puede cambiarse sin
modificar el código que lo usa (en el sentido de *Working Effectively with Legacy Code*, Feathers).

Definir estos seams explícitamente nos permite:

- Escribir tests unitarios rápidos y deterministas (sin MongoDB ni PDFs reales).
- Aplicar TDD de forma disciplinada: cada seam define un contrato testeable antes de la implementación.
- Sustituir implementaciones de infraestructura (motor de PDF, base de datos) por dobles de prueba
  mediante inyección de dependencias.
- Documentar decisiones arquitectónicas auditables para todo el equipo.

La arquitectura sigue **Clean Architecture** / **Hexagonal (Ports & Adapters)**, por lo que los
seams coinciden en gran parte con los puertos definidos entre capas.

## 2. Mapa general de los seams

```
┌────────────────────────────────────────────────────────────┐
│  Seam 1: API HTTP (app/api/routes.py)                      │
│  FastAPI Routes — Presentation Layer                       │
│           │  Depends(get_document_service)                 │
│           ▼                                                │
│  Seam 2: DocumentService (app/application/services/)       │
│  Application / Core Service — orquestación                 │
│      │                  │                    │             │
│      ▼                  ▼                    ▼             │
│  Seam 3: PdfExtractor  Seam 4: ChecksumService            │
│  (app/application/     (app/application/                   │
│   pdf/pdf_extractor.py) services/checksum_service.py)      │
│      │                  │                                  │
│      ▼                  ▼                                  │
│  Infrastructure:      Seam 5: DocumentRepository +         │
│  PypdfPdfExtractor    Database                             │
│  (PyPDF/pdfplumber)   (app/infrastructure/persistence/)    │
│                       MongoDB + Motor                      │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Seam 1 — API HTTP (FastAPI Routes / Presentation Layer)

**Ubicación:** `app/api/routes.py`, `app/api/dependencies.py`

**Responsabilidad**

- Entrada de peticiones HTTP (upload, CRUD, health check).
- Validación de entrada a nivel HTTP: tipo MIME, extensión `.pdf`, tamaño máximo (`validate_pdf_file`, `validate_pdf_size`).
- Serialización/deserialización con Pydantic (`DocumentResponseDTO`, `DocumentListDTO`, `DocumentUpdateDTO`).
- Traducción de resultados y errores de dominio a status codes HTTP:
  - `400` archivo inválido o tamaño excedido
  - `404` documento no encontrado (`DocumentNotFoundError`)
  - `409` checksum duplicado
  - `422` PDF corrupto (`PdfProcessingError`)

**Cómo se desacopla**

La capa HTTP nunca instancia servicios directamente: recibe `DocumentService` y `Database` a través
de `Depends(...)` (`get_document_service`, `get_database`). Esto hace de los endpoints un seam:
en tests se sobreescriben las dependencias con `app.dependency_overrides`.

**Estrategia de testing**

- Tests de contrato HTTP con `TestClient` (FastAPI) o `httpx.AsyncClient` (async).
- Se sobreescribe `get_document_service` con un fake/mock para verificar status codes, payloads y
  cabeceras sin lógica de negocio real.
- Ejemplo:

```python
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_document_service

app.dependency_overrides[get_document_service] = lambda: fake_service
client = TestClient(app)

response = client.post("/api/v1/documents/upload", files={"file": ("doc.pdf", b"%PDF-1.4...", "application/pdf")})
assert response.status_code == 200
```

> Regla: en esta capa se testea el *mapeo* (HTTP ↔ dominio), no la lógica de negocio.

---

## 4. Seam 2 — DocumentService (Application / Core Service)

**Ubicación:** `app/application/services/document_service.py`

**Responsabilidad**

- Orquestación de la lógica de negocio: procesar PDF → validar checksum → persistir.
- Coordinación entre el puerto de extracción (`PdfExtractor`), `ChecksumService` y el
  puerto de persistencia (`DocumentRepository`).
- Operaciones CRUD (`get_all`, `get_by_id`, `update`, `delete`) devolviendo DTOs de aplicación.
- Traducción de fallos técnicos a error de aplicación (`DocumentServiceError`).

**Cómo se desacopla**

Todas sus dependencias se inyectan por constructor:

```python
DocumentService(
    repository: DocumentRepository,        # puerto de persistencia
    pdf_extractor: PdfExtractor = None,    # puerto de extracción
    checksum_service: Optional[ChecksumService] = None,
)
```

Esto convierte al servicio en el seam central del sistema: el núcleo testeable sin HTTP,
sin MongoDB y sin PDFs reales.

**Estrategia de testing**

- Tests unitarios puros: se inyectan dobles (fakes/stubs/mocks) de `DocumentRepository` y
  `PdfExtractor`.
- Se verifican los caminos: extracción OK + checksum único → persistido; checksum duplicado →
  `is_valid=False`; extractor que lanza excepción → `DocumentServiceError`.
- Ejemplo:

```python
class FakeRepository(DocumentRepository):
    def __init__(self): self._docs = {}
    async def insert(self, doc): ...
    # ...

class StubPdfExtractor(PdfExtractor):
    def process_pdf(self, file_bytes):
        return PdfProcessingResult(checksum="abc123", extracted_text="texto de prueba")

service = DocumentService(repository=FakeRepository(), pdf_extractor=StubPdfExtractor())
result = await service.process_and_save(b"%PDF-fake", "test.pdf")
assert result.is_valid
```

---

## 5. Seam 3 — PdfExtractor (Puerto / Interface de extracción)

**Ubicación:** puerto en `app/application/pdf/pdf_extractor.py`; implementación en
`app/infrastructure/pdf/pypdf_extractor.py`

**Responsabilidad**

- Abstraer el motor de extracción de PDFs (PyPDF actualmente; pdfplumber u otro en el futuro).
- Contrato (definido como `Protocol`): `extract_text(bytes) -> str`,
  `extract_metadata(bytes) -> dict`, `process_pdf(bytes) -> PdfProcessingResult`.

**Cómo se desacopla**

La aplicación depende del `Protocol` `PdfExtractor`, no de la implementación concreta
`PypdfPdfExtractor`. Cambiar el motor de extracción solo requiere una nueva clase que cumpla el
protocolo, sin tocar `DocumentService`.

**Estrategia de testing**

- Los tests unitarios de lógica de negocio usan stubs/fakes del protocolo: simulan extracción
  exitosa o error (`PdfProcessingError`) sin leer PDFs reales (rápido y determinista).
- La implementación real (`PypdfPdfExtractor`) se testea aparte con una muestra mínima de PDF real
  (fixture pequeña en `tests/`), aislada en tests de integración/infraestructura.

> Regla: ningún test unitario de `DocumentService` debe cargar un PDF real ni la librería PyPDF.

---

## 6. Seam 4 — ChecksumService (Servicio de hashing)

**Ubicación:** `app/application/services/checksum_service.py`

**Responsabilidad**

- Cálculo del hash SHA-256 de los bytes del archivo (`calculate_checksum`).
- Verificación de unicidad del checksum (`is_checksum_unique`) consultando el repositorio.
- Construcción del documento de dominio validado (`validate_and_create_document` →
  `ChecksumValidationResult`).

**Cómo se desacopla**

- El cálculo del hash es una función pura sobre `bytes`: totalmente independiente del almacenamiento físico.
- La dependencia con persistencia es a través del puerto `DocumentRepository`, inyectado y
  **opcional** (`None` → siempre único), lo que permite testear el hashing sin ninguna base de datos.

**Estrategia de testing**

- Tests unitarios directos sobre vectores conocidos de SHA-256 (entrada → hash esperado).
- Tests de unicidad con un `DocumentRepository` fake: mismo checksum en dos documentos →
  `is_valid=False` con mensaje 409; checksum distinto → `is_valid=True`.
- No requiere fixtures pesados ni infraestructura.

---

## 7. Seam 5 — Database / Repository (Puerto de persistencia)

**Ubicación:** puerto `DocumentRepository` en `app/domain/repositories/document_repository.py`;
implementaciones `MongoRepository` y `Database` en `app/infrastructure/persistence/`

**Responsabilidad**

- Abstracción de todas las operaciones de persistencia: `insert`, `find_by_id`,
  `find_by_checksum`, `find_all`, `update`, `delete`.
- La capa de dominio/aplicación desconoce MongoDB, Motor y la forma de los documentos BSON.

**Cómo se desacopla**

`DocumentRepository` es una clase abstracta (ABC). `MongoRepository` la implementa usando Motor
(async driver de MongoDB). Cualquier test puede sustituirla por un repositorio en memoria.

**Estrategia de testing**

- Tests de lógica pura: repositorio fake en memoria (diccionario de `Document`). Cero I/O.
- Tests del adaptador real (`MongoRepository`): aislados, contra MongoDB de integración
  (Docker Compose / testcontainers) o mockeando la colección de Motor; nunca mezclados con los
  tests unitarios de negocio.
- El endpoint `/health` testea `Database.is_connected()` sobreescribiendo `get_database`.

```python
class InMemoryRepository(DocumentRepository):
    def __init__(self):
        self._store: dict[str, Document] = {}

    async def insert(self, document: Document) -> str:
        doc_id = str(ObjectId())
        document.id = doc_id
        self._store[doc_id] = document
        return doc_id
    # ... resto de operaciones
```

---

## 8. Reglas de la suite de tests respecto a los seams

| Seam | Doble de prueba para unit tests | ¿Infraestructura real en tests? |
|------|--------------------------------|--------------------------------|
| API HTTP | `TestClient` + `dependency_overrides` del servicio | No |
| DocumentService | Fakes/stubs de `DocumentRepository` y `PdfExtractor` | No |
| PdfExtractor | Stub del `Protocol` (en tests de lógica) | Solo en tests del adaptador real |
| ChecksumService | Real (función pura) + repositorio fake | No |
| Repository / Database | `InMemoryRepository` | Solo en tests del adaptador real |

**Acuerdos del equipo:**

1. Toda nueva funcionalidad entra por TDD: test contra el seam correspondiente primero (red),
   implementación mínima después (green), refactor final. La metodología completa del ciclo
   Red-Green-Refactor y sus reglas de compromiso están formalizadas en `CONTRIBUTING.md`.
2. Ningún test unitario toca la red, el disco, MongoDB ni archivos PDF pesados.
3. Las implementaciones de infraestructura se verifican con tests de integración separados
   (`tests/integration/`).
4. Un nuevo seam (ej. cola de mensajes, servicio externo de IA) debe documentarse en este archivo
   antes o junto con su implementación.

## 9. Referencias

- M. Feathers, *Working Effectively with Legacy Code* — concepto de *seam*.
- R. C. Martin, *Clean Architecture*.
- Alistair Cockburn, *Hexagonal Architecture (Ports & Adapters)*.
- Diagramas del proyecto: `docs/diagramas/diagrama_de_clases.puml`, `docs/diagramas/diagrama_de_secuencia.puml`.
