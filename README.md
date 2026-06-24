# PDF Extractor Text

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0%2B-47A248)](https://mongodb.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> API RESTful para extraer texto de documentos PDF con arquitectura limpia, persistencia en MongoDB y validación de duplicados mediante checksum SHA-256.

## Características Principales

- **Extracción de texto**: Extrae texto de archivos PDF de manera rápida y precisa
- **Procesamiento en memoria**: 100% en memoria, sin archivos temporales en disco
- **Validación de duplicados**: Previene subidas duplicadas usando checksum SHA-256
- **API RESTful completa**: CRUD completo con operaciones de listado, consulta, actualización y eliminación
- **Interfaz web moderna**: UI responsive con drag & drop para subir archivos
- **Arquitectura Limpia**: Separación clara de responsabilidades siguiendo Clean Architecture
- **Dockerización**: Configuración completa con Docker y Docker Compose
- **Tests automatizados**: Tests unitarios y de integración con pytest

## Tecnologías

- **Python 3.11+**: Lenguaje de programación
- **FastAPI**: Framework web de alto rendimiento
- **UV**: Gestor de dependencias y entornos virtuales
- **Pydantic**: Validación de datos y configuración
- **PyPDF**: Extracción de texto de PDFs
- **Motor**: Driver asíncrono para MongoDB
- **MongoDB**: Base de datos NoSQL para persistencia
- **Docker**: Containerización y orquestación
- **Tailwind CSS**: Framework CSS para la interfaz web

## Metodologías y Principios

### Metodologías
- **TDD (Test Driven Development)**: Desarrollo guiado por tests
- **GitHub Flow**: Gestión de código con Git y GitHub
- **12-Factor App**: Aplicación siguiendo los 12 factores

### Principios de Programación
- **KISS** (Keep It Simple, Stupid): Simplicidad en el diseño
- **DRY** (Don't Repeat Yourself): Evitar duplicación de código
- **YAGNI** (You Aren't Gonna Need It): No implementar hasta que sea necesario
- **SOLID**: Principios de diseño orientado a objetos
- **Clean Architecture**: Arquitectura limpia con separación de capas

## Arquitectura

El proyecto sigue **Clean Architecture** con las siguientes capas:

```
┌─────────────────────────────────────────────────────────────┐
│                      API (Adaptadores)                       │
│                 FastAPI Routes & Controllers                 │
├─────────────────────────────────────────────────────────────┤
│                   Application (Casos de Uso)                │
│              Services, DTOs & Business Logic                 │
├─────────────────────────────────────────────────────────────┤
│                      Domain (Entidades)                     │
│              Models, Repositories (interfaces)              │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure (Adaptadores)              │
│         MongoDB Repository, PDF Processing, Config            │
└─────────────────────────────────────────────────────────────┘
```

### Estructura de Directorios

```
pdf-extractortext/
├── app/
│   ├── api/                    # Endpoints HTTP y dependencias
│   ├── application/            # Casos de uso y DTOs
│   ├── domain/                 # Entidades e interfaces
│   ├── infrastructure/         # Implementaciones concretas
│   ├── services/               # Servicios de dominio
│   └── config/                 # Configuración
├── tests/                      # Tests unitarios e integración
├── docker-compose.yml          # Orquestación de servicios
├── Dockerfile                  # Imagen de contenedor
├── pyproject.toml             # Configuración del proyecto
└── README.md                  # Este archivo
```

## Instalación y Configuración

### Prerrequisitos

- Python 3.11 o superior
- Docker y Docker Compose (opcional, recomendado)
- MongoDB (si no usas Docker)

### Opción 1: Usar Docker Compose (Recomendado)

Este proyecto separa la compilación de la imagen (build) de la ejecución (runtime). El archivo `docker-compose.yml` utiliza imágenes versionadas ya compiladas, permitiendo un despliegue más rápido y controlado.

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/pdf-extractortext.git
cd pdf-extractortext

# Configurar las variables de la imagen (ejemplo con GitHub Container Registry)
export API_IMAGE=ghcr.io/tu-usuario/pdf-extractortext-api        # Nombre de la imagen
export API_VERSION=0.1.0                                           # Versión de la imagen

# Iniciar servicios con Docker Compose
docker-compose up -d
```

> 💡 **Nota:** El inicio del proyecto asume que la imagen `${API_IMAGE}:${API_VERSION}` ya existe localmente o en el registro configurado.

La aplicación estará disponible en: http://localhost:8000

### Opción 2: Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/pdf-extractortext.git
cd pdf-extractortext

# Instalar UV si no lo tienes
pip install uv

# Crear entorno virtual e instalar dependencias
uv venv
uv pip install -e ".[dev]"

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración de MongoDB

# Iniciar MongoDB (si no está en Docker)
# mongod --dbpath /path/to/db

# Ejecutar la aplicación
uvicorn app.main:app --reload
```

## Variables de Entorno

Crear un archivo `.env` con las siguientes variables:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=pdf_extractor

# Application Configuration
APP_NAME="PDF Extractor API"
APP_VERSION="0.2.0"
DEBUG=false

# PDF Configuration
MAX_PDF_SIZE_MB=10
```

## Uso

### Interfaz Web

Abrir en navegador: http://localhost:8000

La interfaz permite:
- Subir archivos PDF mediante drag & drop
- Ver el texto extraído en tiempo real
- Copiar el texto al portapapeles
- Descargar el texto como archivo .txt

### API Endpoints

#### Subir un PDF
```bash
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: [archivo.pdf]
```

**Respuesta:**
```json
{
  "id": "...",
  "checksum": "sha256...",
  "extracted_text": "Contenido extraído...",
  "created_at": "2024-01-15T10:30:00"
}
```

#### Listar documentos
```bash
GET /api/v1/documents/?skip=0&limit=20
```

#### Obtener un documento
```bash
GET /api/v1/documents/{document_id}
```

#### Actualizar texto extraído
```bash
PUT /api/v1/documents/{document_id}
Content-Type: application/json

{
  "extracted_text": "Nuevo contenido..."
}
```

#### Eliminar un documento
```bash
DELETE /api/v1/documents/{document_id}
```

#### Health Check
```bash
GET /api/v1/health
```

### Documentación Interactiva

FastAPI genera automáticamente documentación interactiva:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con cobertura
pytest --cov=app --cov-report=html

# Ejecutar solo tests unitarios
pytest tests/unit/

# Ejecutar solo tests de integración
pytest tests/integration/
```

## Desarrollo

### Convenciones de Código

- Seguir PEP 8
- Usar type hints en todas las funciones
- Documentar con docstrings (Google style)
- Mantener cobertura de tests > 80%

## Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## Integrantes del Equipo

Proyecto desarrollado para la materia de Desarrollo de Software:

- **Bardaro Lautaro**
- **Dorado Santiago**
- **Márquez Pablo**
- **Martinez Franco**

---

**Nota**: Este proyecto está en desarrollo activo. Algunas funcionalidades planificadas (como la integración con IA para resúmenes) aún no están implementadas.
