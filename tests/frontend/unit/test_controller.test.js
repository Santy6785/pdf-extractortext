import { test, describe, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { AppController } from '../../../frontend/js/controller.js';
import { AppState } from '../../../frontend/js/state.js';

describe('AppController Unit Tests', () => {
  let controller;
  let state;
  let mockApiClient;
  let mockView;

  beforeEach(() => {
    state = new AppState();
    mockApiClient = {
      uploadDocument: async () => {},
      deleteDocument: async () => {},
      listDocuments: async () => [],
      getDocument: async () => {}
    };
    mockView = {
      showFileInfo: () => {},
      hideFileInfo: () => {},
      setLoading: () => {},
      showError: () => {},
      hideError: () => {},
      showResults: () => {},
      hideResults: () => {},
      showCopyFeedback: () => {},
      downloadText: () => {}
    };
    controller = new AppController({
      apiClient: mockApiClient,
      state,
      view: mockView,
      config: { maxUploadMb: 10 }
    });
  });

  test('handleFileSelected rechaza archivo que no es PDF y muestra error', () => {
    let errorMessage = '';
    mockView.showError = (msg) => { errorMessage = msg; };

    const invalidFile = { name: 'notas.txt', type: 'text/plain', size: 100 };
    controller.handleFileSelected(invalidFile);

    assert.equal(errorMessage, 'El archivo debe ser un PDF. Formato no válido.');
    assert.equal(state.selectedFile, null);
  });

  test('handleFileSelected acepta PDF valido y actualiza vista y estado', () => {
    let fileInfoShown = null;
    mockView.showFileInfo = (name, size) => { fileInfoShown = { name, size }; };

    const validPdf = { name: 'informe.pdf', type: 'application/pdf', size: 2048 };
    controller.handleFileSelected(validPdf);

    assert.equal(state.selectedFile, validPdf);
    assert.deepEqual(fileInfoShown, { name: 'informe.pdf', size: '2 KB' });
  });

  test('processFile sube el archivo, guarda id y muestra resultados', async () => {
    const mockPdf = { name: 'reporte.pdf', type: 'application/pdf', size: 1024 };
    state.setFile(mockPdf);

    const apiResponse = {
      id: 'doc-456',
      checksum: 'sha256-112233',
      extracted_text: 'Contenido extraído del reporte',
      created_at: '2026-04-27T12:00:00Z'
    };
    mockApiClient.uploadDocument = async () => apiResponse;

    let shownResults = null;
    mockView.showResults = (checksum, text) => {
      shownResults = { checksum, text };
    };

    await controller.processFile();

    assert.equal(state.documentId, 'doc-456');
    assert.equal(state.checksum, 'sha256-112233');
    assert.equal(state.extractedText, 'Contenido extraído del reporte');
    assert.deepEqual(shownResults, {
      checksum: 'sha256-112233',
      text: 'Contenido extraído del reporte'
    });
  });

  test('processFile previene doble click mientras carga (isLoading = true)', async () => {
    let calls = 0;
    mockApiClient.uploadDocument = async () => {
      calls++;
      return { id: '1', checksum: 'a', extracted_text: 'b' };
    };

    state.setFile({ name: 'doc.pdf', type: 'application/pdf', size: 100 });
    state.setLoading(true);

    await controller.processFile();
    assert.equal(calls, 0, 'No debe invocar uploadDocument si ya esta cargando');
  });

  test('deleteCurrentDocument llama a deleteDocument con documentId y limpia estado', async () => {
    state.setResults({ id: 'doc-777', checksum: 'hash', extractedText: 'text' });
    let deletedId = null;
    mockApiClient.deleteDocument = async (id) => {
      deletedId = id;
      return true;
    };

    await controller.deleteCurrentDocument();

    assert.equal(deletedId, 'doc-777');
    assert.equal(state.documentId, null);
    assert.equal(state.hasResults, false);
  });
});
