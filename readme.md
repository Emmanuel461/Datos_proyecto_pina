# Salud del suelo: datos y explorador

El sitio interactivo está en [`docs/index.html`](docs/index.html). La portada ofrece los módulos de análisis físico y químico.

## Preparar los datos y actualizar el sitio

El flujo usa los scripts de preparación que ya pertenecen al proyecto:

1. Ejecuta `python src/01_soil_data_pipeline.py`. Genera las tablas físicas en `processed/analisis_listo/` y los CSV reducidos para la web en `processed/analisis_listo/web/`.
2. Ejecuta `python src/04_prepare_chemical_data.py`. Genera las tablas químicas en `processed/quimico_analisis_listo/` y el CSV reducido para la web en `processed/quimico_analisis_listo/web/`. Este paso usa el diseño de fincas que produjo el proceso físico.

Las exportaciones de la web contienen tratamiento, finca, parcela, resultados necesarios para los gráficos y el nombre del productor según la ficha de fincas (`productor_finca`). Este nombre se vincula por finca y se muestra en el selector y en la referencia desplegable de ambos módulos. Omiten identificadores de laboratorio, identificadores originales de muestra y celdas de procedencia. Los resultados reportados como límites se conservan sin sustituirlos por valores estimados.

Después de actualizar el código, vuelve a ejecutar `01` y `04` para incorporar los nombres de los productores a los CSV públicos. Las exportaciones anteriores siguen permitiendo graficar, pero no contienen esos nombres.

## Publicar en GitHub Pages

En **Settings → Pages → Build and deployment → Deploy from a branch**, selecciona la rama principal y la carpeta **`/ (root)`**. El archivo `index.html` de la raíz dirige al explorador en `docs/`, que lee los CSV públicos dentro de `processed/`. Incluye en el repositorio los CSV generados en ambas subcarpetas `web/`; las tablas completas y los originales siguen excluidos. Publicar únicamente `/docs` no permite acceder a `processed/`.

Para revisar la web localmente, sirve la raíz del repositorio (por ejemplo, con `python -m http.server`) y abre la dirección local del servidor. Ejecuta primero los procesos de preparación para generar los CSV públicos.

No abras `index.html` con doble clic: el navegador bloquea las solicitudes de CSV desde `file://` y puede mostrar `Failed to fetch`. Desde la carpeta `Datos`, ejecuta `python -m http.server 8000`, deja esa terminal abierta y entra en `http://localhost:8000/`. Servir únicamente la carpeta `docs/` tampoco permite leer `processed/`.

El proceso `04` genera solo el CSV químico. Los tres CSV públicos físicos requieren ejecutar el proceso `01`; deben existir en `processed/analisis_listo/web/` antes de abrir ese módulo.

- [Abrir el explorador interactivo](docs/index.html)
- [Abrir GitHub Pages](https://emmanuel461.github.io/Datos/)
