# Guía de Contribución

## Estándar de desarrollo: TDD (Red-Green-Refactor)

Toda feature nueva y todo bugfix deben desarrollarse siguiendo el ciclo **TDD real**. No se aceptan PRs que agreguen código de producción sin el test que lo precede.

### 1. Fase Roja (Red)

- Escribe **primero** un test (unitario o de integración) que exprese el nuevo requisito, **antes** de tocar código de producción.
- Ejecuta el test y **verifica que falla**. Un test que nunca falló no demuestra nada.
- La aserción debe representar fielmente el requisito: usa valores esperados literales (ground truth), nunca recalcules el esperado con la misma lógica bajo prueba.
- El test debe apuntar al *seam* correspondiente (ver `docs/CONTEXT.md`).

### 2. Fase Verde (Green)

- Escribe la **implementación mínima** que haga pasar el test. Nada más.
- Sin sobreingeniería anticipada: no agregues abstracciones, opciones ni casos que ningún test exige.
- Ejecuta la suite completa: el nuevo test y todos los anteriores deben pasar.

### 3. Fase Refactor

- Con la suite en verde, limpia: elimina duplicación (DRY), mejora nombres, simplifica estructura (KISS).
- La suite completa debe permanecer **en verde durante todo el refactor**. Si algo se rompe, deshaz el último cambio.

### 4. Compromiso en Git

- Antes de cada commit/PR, ejecuta localmente la suite completa: `pytest`.
- Refleja el ciclo en el historial cuando sea posible: commit del test (rojo) y luego commit de la implementación (verde).
- El CI (GitHub Actions) corre `pytest` en cada PR y push a `main`; un check en rojo bloquea el merge. No uses `--no-verify` ni fuerces merges con tests rotos.

## Reglas adicionales de la suite

- Ningún test unitario toca la red, el disco, MongoDB ni PDFs reales (usa mocks/fakes; ver seam rules en `docs/CONTEXT.md`).
- Los tests de integración viven en `tests/integration/`.
- Los fixtures y helpers compartidos van en `tests/conftest.py` (evita duplicar aserciones entre archivos).
