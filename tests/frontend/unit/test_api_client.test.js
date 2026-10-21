import { test, describe, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { ApiClient, ApiError } from '../../../frontend/js/api-client.js';

describe('ApiClient Unit Tests', () => {
  let client;
  let originalFetch;

  beforeEach(() => {
    client = new ApiClient({
      basePath: '',
      timeoutMs: 1000,
      maxRetries: 2,
      retryBaseDelayMs: 10
    });
  });

  test('uploadDocument envia multipart/form-data a /api/v1/documents/upload y retorna datos', async () => {
    const mockResponse = {
      id: 'doc-123',
      checksum: 'sha256-abcdef',
      extracted_text: 'Texto de prueba',
      created_at: '2026-04-27T20:00:00Z'
    };

    let fetchCalledWith = null;
    global.fetch = async (url, options) => {
      fetchCalledWith = { url, options };
      return {
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: async () => JSON.stringify(mockResponse),
        json: async () => mockResponse
      };
    };

    const mockFile = new Blob(['%PDF-1.4 fake content'], { type: 'application/pdf' });
    mockFile.name = 'sample.pdf';

    const result = await client.uploadDocument(mockFile);

    assert.equal(fetchCalledWith.url, '/api/v1/documents/upload');
    assert.equal(fetchCalledWith.options.method, 'POST');
    assert.ok(fetchCalledWith.options.body instanceof FormData);
    assert.deepEqual(result, mockResponse);
  });

  test('uploadDocument mapea error 409 a "El archivo ya existe en el sistema."', async () => {
    global.fetch = async () => ({
      ok: false,
      status: 409,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify({ detail: 'Ya existe un documento con el mismo checksum' })
    });

    const mockFile = new Blob(['duplicate'], { type: 'application/pdf' });
    mockFile.name = 'dup.pdf';

    await assert.rejects(
      async () => client.uploadDocument(mockFile),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 409);
        assert.equal(err.message, 'El archivo ya existe en el sistema.');
        return true;
      }
    );
  });

  test('uploadDocument mapea error 400 por archivo no valido', async () => {
    global.fetch = async () => ({
      ok: false,
      status: 400,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify({ detail: 'El archivo debe ser PDF. Tipo recibido: text/plain' })
    });

    const mockFile = new Blob(['not-a-pdf'], { type: 'text/plain' });
    mockFile.name = 'test.txt';

    await assert.rejects(
      async () => client.uploadDocument(mockFile),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 400);
        assert.equal(err.message, 'El archivo no es un PDF válido o está corrupto.');
        return true;
      }
    );
  });

  test('uploadDocument mapea error por falla de procesamiento', async () => {
    global.fetch = async () => ({
      ok: false,
      status: 422,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify({ detail: 'Failed to process content' })
    });

    const mockFile = new Blob(['corrupt'], { type: 'application/pdf' });
    mockFile.name = 'corrupt.pdf';

    await assert.rejects(
      async () => client.uploadDocument(mockFile),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 422);
        assert.equal(err.message, 'No se pudo procesar el PDF. Verifica que no esté dañado.');
        return true;
      }
    );
  });

  test('uploadDocument maneja respuestas de error no-JSON defensivamente (HTML de proxy)', async () => {
    global.fetch = async () => ({
      ok: false,
      status: 502,
      headers: new Headers({ 'content-type': 'text/html' }),
      text: async () => '<html><body>502 Bad Gateway</body></html>'
    });

    const mockFile = new Blob(['test'], { type: 'application/pdf' });
    mockFile.name = 'test.pdf';

    await assert.rejects(
      async () => client.uploadDocument(mockFile),
      (err) => {
        assert.ok(err instanceof ApiError);
        assert.equal(err.status, 502);
        assert.equal(err.message, 'Servicio temporalmente no disponible. Por favor, reintente en unos instantes.');
        return true;
      }
    );
  });

  test('uploadDocument maneja 429 Rate Limit', async () => {
    global.fetch = async () => ({
      ok: false,
      status: 429,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: async () => 'Too Many Requests'
    });

    const mockFile = new Blob(['test'], { type: 'application/pdf' });
    mockFile.name = 'test.pdf';

    await assert.rejects(
      async () => client.uploadDocument(mockFile),
      (err) => {
        assert.equal(err.status, 429);
        assert.equal(err.message, 'Demasiadas solicitudes. Por favor, espere un momento antes de reintentar.');
        return true;
      }
    );
  });

  test('NUNCA reintenta uploadDocument ante fallo 503 (metodo POST no idempotente)', async () => {
    let callCount = 0;
    global.fetch = async () => {
      callCount++;
      return {
        ok: false,
        status: 503,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => 'Service Unavailable'
      };
    };

    const mockFile = new Blob(['test'], { type: 'application/pdf' });
    mockFile.name = 'test.pdf';

    await assert.rejects(async () => client.uploadDocument(mockFile));
    assert.equal(callCount, 1, 'Upload NO debe reintentarse automaticamente');
  });

  test('NUNCA reintenta deleteDocument ante fallo (metodo DELETE no idempotente en cliente)', async () => {
    let callCount = 0;
    global.fetch = async () => {
      callCount++;
      return {
        ok: false,
        status: 504,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => 'Gateway Timeout'
      };
    };

    await assert.rejects(async () => client.deleteDocument('doc-123'));
    assert.equal(callCount, 1, 'DELETE NO debe reintentarse automaticamente');
  });

  test('listDocuments reintenta automaticamente en GET con backoff ante fallos transitorios 503', async () => {
    let callCount = 0;
    const mockList = [{ id: 'doc-1', checksum: 'abc', created_at: '2026-04-27T00:00:00Z' }];

    global.fetch = async () => {
      callCount++;
      if (callCount < 2) {
        return {
          ok: false,
          status: 503,
          headers: new Headers({ 'content-type': 'text/plain' }),
          text: async () => 'Service Unavailable'
        };
      }
      return {
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: async () => JSON.stringify(mockList),
        json: async () => mockList
      };
    };

    const result = await client.listDocuments({ skip: 0, limit: 10 });
    assert.equal(callCount, 2, 'GET debe haberse reintentado y tenido exito en el 2do intento');
    assert.deepEqual(result, mockList);
  });

  test('getDocument maneja 404 documento no encontrado', async () => {
    global.fetch = async () => ({
      ok: false,
      status: 404,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify({ detail: 'Documento con id doc-999 no encontrado' })
    });

    await assert.rejects(
      async () => client.getDocument('doc-999'),
      (err) => {
        assert.equal(err.status, 404);
        assert.equal(err.message, 'Documento con id doc-999 no encontrado');
        return true;
      }
    );
  });

  test('deleteDocument retorna exito en 204 No Content', async () => {
    global.fetch = async (url, options) => {
      assert.equal(url, '/api/v1/documents/doc-123');
      assert.equal(options.method, 'DELETE');
      return {
        ok: true,
        status: 204,
        headers: new Headers(),
        text: async () => ''
      };
    };

    const res = await client.deleteDocument('doc-123');
    assert.equal(res, true);
  });

  test('parsea defensivamente errores con esquema de lista Pydantic', async () => {
    global.fetch = async () => ({
      ok: false,
      status: 422,
      headers: new Headers({ 'content-type': 'application/json' }),
      text: async () => JSON.stringify({
        detail: [
          { loc: ['body', 'extracted_text'], msg: 'Field required', type: 'missing' }
        ]
      })
    });

    await assert.rejects(
      async () => client.updateDocument('doc-123', null),
      (err) => {
        assert.equal(err.status, 422);
        assert.ok(err.message.includes('Field required') || err.message.includes('extracted_text'));
        return true;
      }
    );
  });

  test('checkHealth llama a /health y retorna estado JSON', async () => {
    global.fetch = async (url) => {
      assert.equal(url, '/health');
      return {
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: async () => JSON.stringify({ status: 'ok', service: 'frontend' }),
        json: async () => ({ status: 'ok', service: 'frontend' })
      };
    };

    const health = await client.checkHealth();
    assert.deepEqual(health, { status: 'ok', service: 'frontend' });
  });
});
