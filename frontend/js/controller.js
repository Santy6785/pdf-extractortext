/**
 * Capa de Controlador (Controller / Application Use Cases).
 * 
 * Orquesta los eventos del usuario, las validaciones de cliente,
 * la sincronización del estado y la interacción con el cliente de API.
 */

import { validateFile, formatFileSize } from './validator.js';

export class AppController {
  /**
   * @param {Object} params
   * @param {import('./api-client.js').ApiClient} params.apiClient
   * @param {import('./state.js').AppState} params.state
   * @param {import('./view.js').AppView} params.view
   * @param {Object} [params.config]
   * @param {number} [params.config.maxUploadMb=10]
   */
  constructor({ apiClient, state, view, config = {} }) {
    this.apiClient = apiClient;
    this.state = state;
    this.view = view;
    this.maxUploadMb = config.maxUploadMb || 10;
  }

  /**
   * Inicializa los manejadores de eventos en el DOM.
   */
  init() {
    const { dropZone, fileInput, processBtn, copyBtn, deleteBtn } = this.view;

    if (dropZone) {
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        this.view.setDragOver(true);
      });

      dropZone.addEventListener('dragleave', () => {
        this.view.setDragOver(false);
      });

      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        this.view.setDragOver(false);
        const files = e.dataTransfer?.files;
        if (files && files.length > 0) {
          this.handleFileSelected(files[0]);
        }
      });

      dropZone.addEventListener('click', (e) => {
        // Evitar que el clic en el fileInput vuelva a disparar el evento del contenedor
        if (e.target !== fileInput && fileInput) {
          fileInput.click();
        }
      });
    }

    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files && files.length > 0) {
          this.handleFileSelected(files[0]);
        }
      });
    }

    if (processBtn) {
      processBtn.addEventListener('click', () => {
        this.processFile();
      });
    }

    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        this.copyText();
      });
    }

    if (deleteBtn) {
      deleteBtn.addEventListener('click', () => {
        this.deleteCurrentDocument();
      });
    }
  }

  /**
   * Valida y establece el archivo seleccionado.
   * @param {File} file 
   */
  handleFileSelected(file) {
    this.view.hideError();

    const validation = validateFile(file, this.maxUploadMb);
    if (!validation.isValid) {
      this.view.showError(validation.error);
      return;
    }

    this.state.setFile(file);
    const formattedSize = formatFileSize(file.size);
    this.view.showFileInfo(file.name, formattedSize);
  }

  /**
   * Limpia el archivo seleccionado y restablece la vista.
   */
  clearFile() {
    this.state.clearFile();
    this.view.hideFileInfo();
    this.view.hideError();
  }

  /**
   * Sube y procesa el archivo PDF seleccionado de forma síncrona.
   */
  async processFile() {
    if (this.state.isLoading) {
      return; // Prevenir doble clic / envío simultáneo
    }

    if (!this.state.selectedFile) {
      this.view.showError('Por favor selecciona un archivo PDF primero.');
      return;
    }

    this.state.setLoading(true);
    this.view.setLoading(true);
    this.view.hideError();
    this.view.hideResults();

    try {
      const data = await this.apiClient.uploadDocument(this.state.selectedFile);

      this.state.setResults({
        id: data.id,
        checksum: data.checksum,
        extractedText: data.extracted_text
      });

      this.view.showResults(data.checksum, data.extracted_text);
    } catch (err) {
      console.error('Error al procesar el archivo:', err);
      const message = err.message || 'Error al procesar el archivo';
      this.state.setError(message);
      this.view.showError(message);
    } finally {
      this.state.setLoading(false);
      this.view.setLoading(false);
    }
  }

  /**
   * Elimina el documento actualmente procesado en la base de datos.
   */
  async deleteCurrentDocument() {
    if (this.state.isLoading || !this.state.documentId) {
      return;
    }

    const docId = this.state.documentId;
    this.state.setLoading(true);
    this.view.setLoading(true);
    this.view.hideError();

    try {
      await this.apiClient.deleteDocument(docId);
      this.clearFile();
    } catch (err) {
      console.error('Error al eliminar documento:', err);
      this.view.showError(err.message || 'Error al eliminar el documento');
    } finally {
      this.state.setLoading(false);
      this.view.setLoading(false);
    }
  }

  /**
   * Copia el texto extraído al portapapeles con feedback temporal.
   */
  async copyText() {
    const text = this.state.extractedText;
    if (!text) return;

    try {
      if (globalThis.navigator?.clipboard?.writeText) {
        await globalThis.navigator.clipboard.writeText(text);
        this.view.showCopyFeedback();
      } else {
        throw new Error('Clipboard API no disponible');
      }
    } catch (err) {
      console.error('Error al copiar:', err);
      this.view.showError('No se pudo copiar al portapapeles.');
    }
  }

  /**
   * Descarga el texto extraído en formato .txt
   */
  downloadText() {
    const text = this.state.extractedText;
    if (!text) return;

    const baseName = this.state.selectedFile
      ? this.state.selectedFile.name.replace(/\.pdf$/i, '')
      : 'documento';
    const filename = `${baseName}.txt`;

    this.view.downloadText(filename, text);
  }
}
