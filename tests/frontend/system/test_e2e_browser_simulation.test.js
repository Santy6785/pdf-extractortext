import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { ApiClient } from '../../../frontend/js/api-client.js';
import { AppState } from '../../../frontend/js/state.js';
import { AppController } from '../../../frontend/js/controller.js';

describe('E2E Frontend System Flow Simulation (Upload -> Results -> 409 Duplicate -> Delete)', () => {
  test('Flujo completo de usuario en la UI', async () => {
    // 1. Simular base de datos / servidor backend
    const database = new Map();
    let isServerDown = false;

    const mockFetch = async (url, options) => {
      if (isServerDown) {
        return {
          ok: false,
          status: 503,
          headers: new Headers({ 'content-type': 'text/plain' }),
          text: async () => 'Service Unavailable'
        };
      }

      if (url.endsWith('/health') && options.method === 'GET') {
        return {
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          text: async () => JSON.stringify({ status: 'ok', service: 'frontend' }),
          json: async () => ({ status: 'ok', service: 'frontend' })
        };
      }

      if (url.endsWith('/api/v1/documents/upload') && options.method === 'POST') {
        const checksum = 'sha256-mock-e2e-hash';
        if (database.has(checksum)) {
          return {
            ok: false,
            status: 409,
            headers: new Headers({ 'content-type': 'application/json' }),
            text: async () => JSON.stringify({ detail: 'Ya existe un documento con el mismo checksum' })
          };
        }

        const doc = {
          id: 'doc-e2e-42',
          checksum,
          extracted_text: 'Contenido extraído del archivo de prueba E2E.',
          created_at: new Date().toISOString()
        };
        database.set(checksum, doc);
        return {
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          text: async () => JSON.stringify(doc),
          json: async () => doc
        };
      }

      if (url.includes('/api/v1/documents/') && options.method === 'DELETE') {
        const id = url.split('/').pop();
        for (const [checksum, doc] of database.entries()) {
          if (doc.id === id) {
            database.delete(checksum);
            return {
              ok: true,
              status: 204,
              headers: new Headers(),
              text: async () => ''
            };
          }
        }
        return {
          ok: false,
          status: 404,
          headers: new Headers({ 'content-type': 'application/json' }),
          text: async () => JSON.stringify({ detail: 'Documento no encontrado' })
        };
      }

      return {
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: async () => JSON.stringify({ detail: 'Not Found' })
      };
    };

    global.fetch = mockFetch;

    // 2. Configurar MVC de la UI
    const apiClient = new ApiClient({ basePath: '' });
    const state = new AppState();
    const ui = {
      fileInfoVisible: false,
      fileNameText: '',
      fileSizeText: '',
      processDisabled: true,
      btnText: 'Procesar y Extraer Texto',
      loaderHidden: true,
      errorMessage: null,
      resultsVisible: false,
      checksumText: '',
      extractedText: '',
      copyFeedback: false,
      downloadTriggered: null
    };

    const mockView = {
      showFileInfo: (name, size) => {
        ui.fileInfoVisible = true;
        ui.fileNameText = name;
        ui.fileSizeText = size;
        ui.processDisabled = false;
        ui.resultsVisible = false;
      },
      hideFileInfo: () => {
        ui.fileInfoVisible = false;
        ui.processDisabled = true;
        ui.resultsVisible = false;
      },
      setLoading: (loading) => {
        ui.processDisabled = loading;
        ui.btnText = loading ? 'Procesando...' : 'Procesar y Extraer Texto';
        ui.loaderHidden = !loading;
      },
      showError: (msg) => { ui.errorMessage = msg; },
      hideError: () => { ui.errorMessage = null; },
      showResults: (chk, txt) => {
        ui.resultsVisible = true;
        ui.checksumText = chk;
        ui.extractedText = txt;
      },
      hideResults: () => {
        ui.resultsVisible = false;
        ui.checksumText = '';
        ui.extractedText = '';
      },
      showCopyFeedback: () => { ui.copyFeedback = true; },
      downloadText: (name, content) => { ui.downloadTriggered = { name, content }; }
    };

    const controller = new AppController({
      apiClient,
      state,
      view: mockView,
      config: { maxUploadMb: 10 }
    });

    // Paso A: Verificar Health Check del front
    const health = await apiClient.checkHealth();
    assert.deepEqual(health, { status: 'ok', service: 'frontend' });

    // Paso B: Usuario selecciona archivo PDF
    const testPdf = new Blob(['%PDF-1.4 test bytes'], { type: 'application/pdf' });
    testPdf.name = 'sample.pdf';

    controller.handleFileSelected(testPdf);
    assert.equal(ui.fileInfoVisible, true);
    assert.equal(ui.fileNameText, 'sample.pdf');
    assert.equal(ui.processDisabled, false);

    // Paso C: Usuario hace clic en "Procesar y Extraer Texto"
    await controller.processFile();
    assert.equal(ui.resultsVisible, true);
    assert.equal(ui.checksumText, 'sha256-mock-e2e-hash');
    assert.equal(ui.extractedText, 'Contenido extraído del archivo de prueba E2E.');
    assert.equal(state.documentId, 'doc-e2e-42');
    assert.equal(ui.errorMessage, null);

    // Paso D: Usuario intenta subir el mismo archivo nuevamente -> 409 Conflict
    controller.handleFileSelected(testPdf);
    await controller.processFile();
    assert.equal(ui.errorMessage, 'El archivo ya existe en el sistema.');
    assert.equal(ui.resultsVisible, false);

    // Paso E: Usuario elimina el documento del sistema
    state.setResults({
      id: 'doc-e2e-42',
      checksum: 'sha256-mock-e2e-hash',
      extractedText: 'Contenido extraído'
    });
    await controller.deleteCurrentDocument();
    assert.equal(state.documentId, null);
    assert.equal(database.size, 0, 'La base de datos debe estar vacía tras la eliminación');

    // Paso F: Usuario vuelve a seleccionar y procesar el archivo -> Éxito total
    controller.handleFileSelected(testPdf);
    await controller.processFile();
    assert.equal(ui.resultsVisible, true);
    assert.equal(ui.checksumText, 'sha256-mock-e2e-hash');
    assert.equal(ui.errorMessage, null);
  });
});
