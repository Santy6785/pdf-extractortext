/**
 * Capa de Vista (View / DOM Rendering).
 * 
 * Centraliza la manipulación del árbol DOM, aplicando los estilos y animaciones
 * exactamente iguales a la interfaz original.
 */

export class AppView {
  constructor(documentRef = globalThis.document) {
    this.doc = documentRef;
  }

  // Getters para obtener elementos dinámicamente
  get dropZone() { return this.doc.getElementById('dropZone'); }
  get fileInput() { return this.doc.getElementById('fileInput'); }
  get fileInfo() { return this.doc.getElementById('fileInfo'); }
  get fileName() { return this.doc.getElementById('fileName'); }
  get fileSize() { return this.doc.getElementById('fileSize'); }
  get processBtn() { return this.doc.getElementById('processBtn'); }
  get btnText() { return this.doc.getElementById('btnText'); }
  get btnLoader() { return this.doc.getElementById('btnLoader'); }
  get errorMessage() { return this.doc.getElementById('errorMessage'); }
  get errorText() { return this.doc.getElementById('errorText'); }
  get resultsSection() { return this.doc.getElementById('resultsSection'); }
  get checksumValue() { return this.doc.getElementById('checksumValue'); }
  get extractedText() { return this.doc.getElementById('extractedText'); }
  get copyBtn() { return this.doc.getElementById('copyBtn'); }
  get deleteBtn() { return this.doc.getElementById('deleteBtn'); }

  setDragOver(isOver) {
    if (!this.dropZone) return;
    if (isOver) {
      this.dropZone.classList.add('drag-over');
    } else {
      this.dropZone.classList.remove('drag-over');
    }
  }

  showFileInfo(name, formattedSize) {
    if (this.fileName) this.fileName.textContent = name;
    if (this.fileSize) this.fileSize.textContent = formattedSize;
    if (this.fileInfo) this.fileInfo.classList.remove('hidden');
    if (this.processBtn) this.processBtn.disabled = false;
    this.hideResults();
  }

  hideFileInfo() {
    if (this.fileInput) this.fileInput.value = '';
    if (this.fileInfo) this.fileInfo.classList.add('hidden');
    if (this.processBtn) this.processBtn.disabled = true;
    this.hideResults();
  }

  setLoading(isLoading) {
    if (!this.processBtn) return;
    this.processBtn.disabled = isLoading;
    if (isLoading) {
      if (this.btnText) this.btnText.textContent = 'Procesando...';
      if (this.btnLoader) this.btnLoader.classList.remove('hidden');
    } else {
      if (this.btnText) this.btnText.textContent = 'Procesar y Extraer Texto';
      if (this.btnLoader) this.btnLoader.classList.add('hidden');
    }
  }

  showError(message) {
    if (this.errorText) this.errorText.textContent = message;
    if (this.errorMessage) this.errorMessage.classList.remove('hidden');
  }

  hideError() {
    if (this.errorMessage) this.errorMessage.classList.add('hidden');
  }

  showResults(checksum, text) {
    if (this.checksumValue) this.checksumValue.textContent = checksum || '';
    if (this.extractedText) this.extractedText.value = text || '';
    if (this.resultsSection) {
      this.resultsSection.classList.remove('hidden');
      if (typeof this.resultsSection.scrollIntoView === 'function') {
        this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }

  hideResults() {
    if (this.resultsSection) this.resultsSection.classList.add('hidden');
    if (this.checksumValue) this.checksumValue.textContent = '';
    if (this.extractedText) this.extractedText.value = '';
  }

  showCopyFeedback() {
    if (!this.copyBtn) return;
    const originalContent = this.copyBtn.innerHTML;
    this.copyBtn.innerHTML = `
      <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
      </svg>
      Copiado
    `;
    setTimeout(() => {
      if (this.copyBtn) this.copyBtn.innerHTML = originalContent;
    }, 2000);
  }

  downloadText(filename, content) {
    if (!content) return;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = this.doc.createElement('a');
    a.href = url;
    a.download = filename;
    this.doc.body.appendChild(a);
    a.click();
    this.doc.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}
