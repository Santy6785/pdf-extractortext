import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { validateFile, formatFileSize } from '../../../frontend/js/validator.js';

describe('Validator Unit Tests', () => {
  test('valida correctamente archivo PDF valido', () => {
    const file = {
      name: 'documento.pdf',
      type: 'application/pdf',
      size: 5 * 1024 * 1024
    };
    const result = validateFile(file, 10);
    assert.equal(result.isValid, true);
    assert.equal(result.error, null);
  });

  test('falla si el archivo no tiene extension .pdf ni tipo application/pdf', () => {
    const file = {
      name: 'imagen.png',
      type: 'image/png',
      size: 1024
    };
    const result = validateFile(file, 10);
    assert.equal(result.isValid, false);
    assert.equal(result.error, 'El archivo debe ser un PDF. Formato no válido.');
  });

  test('falla si el archivo supera el limite maximo en MB', () => {
    const file = {
      name: 'pesado.pdf',
      type: 'application/pdf',
      size: 11 * 1024 * 1024
    };
    const result = validateFile(file, 10);
    assert.equal(result.isValid, false);
    assert.equal(result.error, 'El archivo es demasiado grande. Tamaño máximo: 10MB.');
  });

  test('formatFileSize formatea adecuadamente bytes, KB y MB', () => {
    assert.equal(formatFileSize(0), '0 Bytes');
    assert.equal(formatFileSize(1024), '1 KB');
    assert.equal(formatFileSize(1048576), '1 MB');
    assert.equal(formatFileSize(5242880), '5 MB');
  });
});
