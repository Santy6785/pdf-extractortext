"""
Tests unitarios para MongoDocumentRepository.
Utilizan mocks para no requerir conexión a base de datos real.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId


@pytest.fixture
def mock_motor_collection():
    """Fixture que crea un mock de colección MongoDB con motor."""
    collection = MagicMock()
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock()
    collection.find = MagicMock()
    collection.delete_one = AsyncMock()
    return collection


@pytest.mark.asyncio
async def test_mongo_repository_insert(mock_motor_collection):
    """Test que inserta un documento en MongoDB."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    # Configurar mock
    inserted_id = ObjectId()
    mock_motor_collection.insert_one.return_value = MagicMock(inserted_id=inserted_id)

    repository = MongoDocumentRepository(mock_motor_collection)

    document = Document(
        checksum="abc123",
        extracted_text="contenido del documento",
        created_at=datetime.now(),
        id=None
    )

    result = await repository.insert(document)

    mock_motor_collection.insert_one.assert_called_once()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mongo_repository_find_by_checksum(mock_motor_collection):
    """Test que busca documento por checksum."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    
    # Simular documento encontrado (solo checksum, extracted_text, created_at)
    mock_doc = {
        "_id": ObjectId(),
        "checksum": "target-checksum",
        "extracted_text": "texto extraído del documento",
        "created_at": datetime.now()
    }
    mock_motor_collection.find_one.return_value = mock_doc
    
    repository = MongoDocumentRepository(mock_motor_collection)
    
    result = await repository.find_by_checksum("target-checksum")
    
    mock_motor_collection.find_one.assert_called_once_with({"checksum": "target-checksum"})
    assert result is not None
    assert result.checksum == "target-checksum"
    assert result.extracted_text == "texto extraído del documento"


@pytest.mark.asyncio
async def test_mongo_repository_find_by_checksum_not_found(mock_motor_collection):
    """Test que retorna None cuando el checksum no existe."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    
    mock_motor_collection.find_one.return_value = None
    
    repository = MongoDocumentRepository(mock_motor_collection)
    
    result = await repository.find_by_checksum("non-existent")
    
    assert result is None


@pytest.mark.asyncio
async def test_mongo_repository_find_by_id(mock_motor_collection):
    """Test que busca documento por ID."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    
    doc_id = str(ObjectId())
    mock_doc = {
        "_id": ObjectId(doc_id),
        "checksum": "cs123",
        "extracted_text": "contenido encontrado",
        "created_at": datetime.now()
    }
    mock_motor_collection.find_one.return_value = mock_doc
    
    repository = MongoDocumentRepository(mock_motor_collection)
    
    result = await repository.find_by_id(doc_id)
    
    assert result is not None
    assert result.id == doc_id
    assert result.checksum == "cs123"


@pytest.mark.asyncio
async def test_mongo_repository_delete():
    """Test que elimina un documento."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    
    # Crear mock de colección
    collection = MagicMock()
    delete_result = MagicMock()
    delete_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=delete_result)
    
    repository = MongoDocumentRepository(collection)
    
    # Usar un ObjectId válido
    doc_id = str(ObjectId())
    result = await repository.delete(doc_id)
    
    assert result is True


@pytest.mark.asyncio
async def test_mongo_repository_delete_not_found(mock_motor_collection):
    """Test que retorna False al eliminar documento inexistente."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    
    mock_motor_collection.delete_one.return_value = MagicMock(deleted_count=0)
    
    repository = MongoDocumentRepository(mock_motor_collection)
    
    result = await repository.delete("non-existent")
    
    assert result is False


@pytest.mark.asyncio
async def test_mongo_repository_find_all(mock_motor_collection):
    """Test que lista todos los documentos con paginación."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository

    # Simular cursor con documentos (solo campos requeridos)
    mock_docs = [
        {
            "_id": ObjectId(),
            "checksum": "cs1",
            "extracted_text": "texto1",
            "created_at": datetime.now()
        },
        {
            "_id": ObjectId(),
            "checksum": "cs2",
            "extracted_text": "texto2",
            "created_at": datetime.now()
        }
    ]

    mock_cursor = MagicMock()
    mock_cursor.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=mock_docs)
    mock_motor_collection.find.return_value = mock_cursor

    repository = MongoDocumentRepository(mock_motor_collection)

    result = await repository.find_all(limit=20)

    assert len(result) == 2
    assert all(doc.checksum in ["cs1", "cs2"] for doc in result)
    # Verify pagination
    mock_motor_collection.find.return_value.skip.assert_called_once_with(0)
    mock_cursor.skip.return_value.limit.assert_called_once_with(20)


@pytest.mark.asyncio
async def test_mongo_repository_find_all_with_pagination(mock_motor_collection):
    """Test que lista documentos con paginación personalizada."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository

    mock_docs = [
        {
            "_id": ObjectId(),
            "checksum": "cs3",
            "extracted_text": "texto3",
            "created_at": datetime.now()
        }
    ]

    mock_cursor = MagicMock()
    mock_cursor.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=mock_docs)
    mock_motor_collection.find.return_value = mock_cursor

    repository = MongoDocumentRepository(mock_motor_collection)

    result = await repository.find_all(skip=5, limit=10)

    assert len(result) == 1
    mock_motor_collection.find.return_value.skip.assert_called_once_with(5)
    mock_cursor.skip.return_value.limit.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_mongo_repository_handles_bson_objectid():
    """Test que maneja correctamente ObjectId de BSON."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from bson import ObjectId
    
    collection = MagicMock()
    object_id = ObjectId()
    
    mock_doc = {
        "_id": object_id,
        "checksum": "abc",
        "extracted_text": "text",
        "created_at": datetime.now()
    }
    collection.find_one = AsyncMock(return_value=mock_doc)
    
    repository = MongoDocumentRepository(collection)
    result = await repository.find_by_id(str(object_id))
    
    assert result.id == str(object_id)


@pytest.mark.asyncio
async def test_mongo_repository_schema_fields():
    """Test que el documento tiene solo los campos requeridos (checksum, extracted_text, created_at)."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    collection = MagicMock()

    doc = Document(
        checksum="test-checksum",
        extracted_text="texto del documento",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        id=None
    )

    inserted_id = ObjectId()
    insert_result = MagicMock()
    insert_result.inserted_id = inserted_id
    collection.insert_one = AsyncMock(return_value=insert_result)

    repository = MongoDocumentRepository(collection)
    await repository.insert(doc)

    # Verificar que se llamó a insert_one
    assert collection.insert_one.called

    # Obtener el diccionario pasado a insert_one
    call_args = collection.insert_one.call_args[0][0]

    # Verificar campos del esquema
    assert "checksum" in call_args
    assert "extracted_text" in call_args
    assert "created_at" in call_args

    # Verificar que NO tiene campos no deseados
    assert "filename" not in call_args
    assert "page_dimensions" not in call_args


@pytest.mark.asyncio
async def test_mongo_repository_update_success():
    """Test que actualiza un documento existente."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    collection = MagicMock()
    update_result = MagicMock()
    update_result.matched_count = 1
    collection.update_one = AsyncMock(return_value=update_result)

    repository = MongoDocumentRepository(collection)

    doc_id = str(ObjectId())
    document = Document(
        checksum="updated-checksum",
        extracted_text="updated text",
        created_at=datetime.now(),
        id=doc_id
    )

    result = await repository.update(doc_id, document)

    assert result is True
    collection.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_mongo_repository_update_not_found():
    """Test que retorna False al actualizar documento inexistente."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    collection = MagicMock()
    update_result = MagicMock()
    update_result.matched_count = 0
    collection.update_one = AsyncMock(return_value=update_result)

    repository = MongoDocumentRepository(collection)

    doc_id = str(ObjectId())
    document = Document(
        checksum="check",
        extracted_text="text",
        created_at=datetime.now(),
        id=doc_id
    )

    result = await repository.update(doc_id, document)

    assert result is False


@pytest.mark.asyncio
async def test_mongo_repository_find_by_id_invalid_objectid():
    """Test que retorna None ante ObjectIds invalidos sin consultar la coleccion."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository

    collection = MagicMock()
    collection.find_one = AsyncMock(return_value={"unexpected": "doc"})

    repository = MongoDocumentRepository(collection)

    assert await repository.find_by_id("id-invalido") is None
    assert await repository.find_by_id("123") is None
    assert await repository.find_by_id("..no-es-oid..") is None
    collection.find_one.assert_not_called()


@pytest.mark.asyncio
async def test_mongo_repository_find_by_id_propagates_nothing_on_db_error():
    """Test que errores de la coleccion en find_by_id devuelven None."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository

    collection = MagicMock()
    collection.find_one = AsyncMock(side_effect=ConnectionError("mongo caido"))

    repository = MongoDocumentRepository(collection)

    result = await repository.find_by_id(str(ObjectId()))

    assert result is None


@pytest.mark.asyncio
async def test_mongo_repository_insert_does_not_include_id_for_new_document():
    """Test que insertar un documento nuevo no incluye el campo _id."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    collection = MagicMock()
    collection.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId())
    )

    repository = MongoDocumentRepository(collection)

    document = Document(
        checksum="new-doc",
        extracted_text="texto nuevo",
        created_at=datetime.now(),
        id=None
    )

    await repository.insert(document)

    inserted = collection.insert_one.call_args[0][0]
    assert "_id" not in inserted


@pytest.mark.asyncio
async def test_mongo_repository_insert_includes_id_when_present():
    """Test que insertar un documento con id lo incluye como ObjectId."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    collection = MagicMock()
    doc_id = str(ObjectId())
    collection.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=ObjectId(doc_id))
    )

    repository = MongoDocumentRepository(collection)

    document = Document(
        checksum="with-id",
        extracted_text="texto",
        created_at=datetime.now(),
        id=doc_id
    )

    await repository.insert(document)

    inserted = collection.insert_one.call_args[0][0]
    assert inserted["_id"] == ObjectId(doc_id)


@pytest.mark.asyncio
async def test_mongo_repository_update_uses_id_filter_and_set_operator():
    """Test que update filtra por _id y usa el operador $set sin enviar _id."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    collection = MagicMock()
    collection.update_one = AsyncMock(return_value=MagicMock(matched_count=1))

    repository = MongoDocumentRepository(collection)

    doc_id = str(ObjectId())
    document = Document(
        checksum="cs-upd",
        extracted_text="texto actualizado",
        created_at=datetime.now(),
        id=doc_id
    )

    result = await repository.update(doc_id, document)

    assert result is True
    filt, update = collection.update_one.call_args[0]
    assert filt == {"_id": ObjectId(doc_id)}
    assert set(update.keys()) == {"$set"}
    assert "_id" not in update["$set"]
    assert update["$set"]["checksum"] == "cs-upd"
    assert update["$set"]["extracted_text"] == "texto actualizado"


@pytest.mark.asyncio
async def test_mongo_repository_update_invalid_objectid_returns_false():
    """Test que update con un id invalido retorna False sin tocar la coleccion."""
    from app.infrastructure.persistence.mongo_repository import MongoDocumentRepository
    from app.domain.models.document import Document

    collection = MagicMock()
    collection.update_one = AsyncMock()

    repository = MongoDocumentRepository(collection)

    document = Document(
        checksum="cs",
        extracted_text="texto",
        created_at=datetime.now()
    )

    assert await repository.update("id-invalido", document) is False
    assert await repository.update("123", document) is False
    collection.update_one.assert_not_called()
