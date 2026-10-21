/**
 * Gestión del Estado de la Aplicación (Model / State).
 * 
 * Centraliza las variables reactivas de la UI y notifica a los suscriptores ante cualquier cambio.
 */

export class AppState {
  constructor() {
    this.selectedFile = null;
    this.extractedText = '';
    this.checksum = '';
    this.documentId = null;
    this.isLoading = false;
    this.errorMessage = null;
    this._listeners = new Set();
  }

  get hasResults() {
    return Boolean(this.extractedText || this.checksum);
  }

  subscribe(listener) {
    this._listeners.add(listener);
    return () => this._listeners.delete(listener);
  }

  _notify() {
    for (const listener of this._listeners) {
      try {
        listener(this);
      } catch (err) {
        console.error('Error en listener de estado:', err);
      }
    }
  }

  setFile(file) {
    this.selectedFile = file;
    this.errorMessage = null;
    this._notify();
  }

  clearFile() {
    this.selectedFile = null;
    this.extractedText = '';
    this.checksum = '';
    this.documentId = null;
    this.errorMessage = null;
    this._notify();
  }

  setLoading(isLoading) {
    this.isLoading = Boolean(isLoading);
    this._notify();
  }

  setError(message) {
    this.errorMessage = message;
    this._notify();
  }

  clearError() {
    this.errorMessage = null;
    this._notify();
  }

  setResults({ id = null, checksum = '', extractedText = '' } = {}) {
    this.documentId = id;
    this.checksum = checksum;
    this.extractedText = extractedText;
    this.errorMessage = null;
    this._notify();
  }

  clearResults() {
    this.extractedText = '';
    this.checksum = '';
    this.documentId = null;
    this._notify();
  }

  reset() {
    this.selectedFile = null;
    this.extractedText = '';
    this.checksum = '';
    this.documentId = null;
    this.isLoading = false;
    this.errorMessage = null;
    this._notify();
  }
}
