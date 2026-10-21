import { test, describe, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { AppState } from '../../../frontend/js/state.js';

describe('AppState Unit Tests', () => {
  let state;

  beforeEach(() => {
    state = new AppState();
  });

  test('estado inicial tiene valores por defecto correctos', () => {
    assert.equal(state.selectedFile, null);
    assert.equal(state.extractedText, '');
    assert.equal(state.checksum, '');
    assert.equal(state.documentId, null);
    assert.equal(state.isLoading, false);
    assert.equal(state.errorMessage, null);
    assert.equal(state.hasResults, false);
  });

  test('setFile actualiza selectedFile y notifica suscriptores', () => {
    let notified = false;
    state.subscribe(() => {
      notified = true;
    });

    const file = { name: 'doc.pdf', size: 1024 };
    state.setFile(file);

    assert.equal(state.selectedFile, file);
    assert.equal(notified, true);
    assert.equal(state.errorMessage, null);
  });

  test('clearFile reinicia selectedFile y resultados', () => {
    state.setFile({ name: 'doc.pdf' });
    state.setResults({ id: '1', checksum: 'abc', extractedText: 'text' });

    state.clearFile();

    assert.equal(state.selectedFile, null);
    assert.equal(state.hasResults, false);
    assert.equal(state.documentId, null);
  });

  test('setLoading conmuta bandera isLoading', () => {
    state.setLoading(true);
    assert.equal(state.isLoading, true);
    state.setLoading(false);
    assert.equal(state.isLoading, false);
  });

  test('setError y clearError actualizan errorMessage', () => {
    state.setError('Error fatal');
    assert.equal(state.errorMessage, 'Error fatal');
    state.clearError();
    assert.equal(state.errorMessage, null);
  });

  test('setResults almacena los datos extraidos y activa hasResults', () => {
    state.setResults({
      id: 'doc-999',
      checksum: 'sha256-hash',
      extractedText: 'Hola mundo'
    });

    assert.equal(state.hasResults, true);
    assert.equal(state.documentId, 'doc-999');
    assert.equal(state.checksum, 'sha256-hash');
    assert.equal(state.extractedText, 'Hola mundo');
  });
});
