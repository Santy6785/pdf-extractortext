/**
 * Punto de entrada y Bootstrap de la aplicación Front-End.
 * 
 * Orquesta la inyección de dependencias entre:
 * - Model: ApiClient + AppState
 * - View: AppView
 * - Controller: AppController
 */

import { ApiClient } from './api-client.js';
import { AppState } from './state.js';
import { AppView } from './view.js';
import { AppController } from './controller.js';

// Carga de configuración dinámica de tiempo de ejecución
const runtimeConfig = window.__CONFIG__ || {};

const config = {
  apiBasePath: runtimeConfig.API_BASE_PATH ?? '',
  maxUploadMb: Number(runtimeConfig.MAX_UPLOAD_MB) || 10,
  requestTimeoutMs: Number(runtimeConfig.REQUEST_TIMEOUT_MS) || 30000
};

const apiClient = new ApiClient({
  basePath: config.apiBasePath,
  timeoutMs: config.requestTimeoutMs
});

const state = new AppState();
const view = new AppView(document);
const controller = new AppController({
  apiClient,
  state,
  view,
  config
});

// Funciones globales para retrocompatibilidad con los atributos inline del HTML original
window.appController = controller;
window.handleFileSelect = (event) => {
  const file = event.target.files?.[0];
  if (file) controller.handleFileSelected(file);
};
window.clearFile = () => controller.clearFile();
window.processFile = () => controller.processFile();
window.copyText = () => controller.copyText();
window.downloadText = () => controller.downloadText();
window.deleteCurrentDocument = () => controller.deleteCurrentDocument();

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => controller.init());
} else {
  controller.init();
}
