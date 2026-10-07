# Salud del suelo: datos y explorador

El sitio interactivo está en [`docs/index.html`](docs/index.html). La portada ofrece los módulos de análisis físico, químico, nematodos y carbono lábil (POXC).

- [Abrir el explorador interactivo](docs/index.html)
- [Abrir GitHub Pages](https://emmanuel461.github.io/Datos/)

## Organización

```text
raw/                              Fuentes originales y ficha de fincas
src/                              Scripts 01 a 08 de preparación, validación y análisis
processed/
  fisico_all_pina/                 Excel físico consolidado (entrada)
  quimico_all_pina/                Excel químico consolidado (entrada)
  diseno_muestreo.csv              Diseño compartido, generado por 01
  auditoria_preparacion.csv        Auditoría física, generada por 01
  duplicados_consolidados.csv      Registro de duplicados, generado por 01
  analisis_listo/                  Tablas físicas preparadas por 01
    web/                          CSV públicos físicos, generados por 01
    resumenes/                    Seis tablas del análisis físico, generadas por 03
  quimico_analisis_listo/          Tablas químicas preparadas por 04
    web/                          CSV público químico, generado por 04
  nematodos_analisis_listo/        Tablas de nematodos preparadas por 05
    trazabilidad/                 Matriz exacta utilizada como entrada de NINJA
    resumenes/                    Tablas descriptivas generadas por 06
    web/                          Resultados y catálogo público de nematodos generados por 06
  poxc_analisis_listo/             Carbono lábil preparado por 07
    resumenes/                    Resúmenes descriptivos generados por 08
    web/                          CSV público de POXC generado por 08
docs/                             Web, documentación e informes
  figuras/agronomico/             Figuras de los informes, generadas por 03
  figuras/historico/              Figuras anteriores, conservadas como referencia
index.html                        Redirección a docs/index.html
```

Los datos numéricos generados van en `processed/`, nunca en `docs/data/` ni en `docs/tablas/`. Los informes Markdown y sus figuras se mantienen en `docs/`. No editar manualmente los CSV generados: corregir la fuente o el script y volver a ejecutarlo.

## Flujo de ejecución

Ejecutar desde la carpeta `Datos`, con el entorno de Python del proyecto activado. Se necesitan `pandas`, `openpyxl`, `numpy` y `matplotlib`. Los Excel de entrada deben existir previamente; estos scripts no los consolidan ni los modifican.

| Script | Entrada | Salida / función |
|---|---|---|
| `01_soil_data_pipeline.py` | `processed/fisico_all_pina/Fisico_all_sorted.xlsx` y `raw/pina/PIÑA FINCAS PRODUCTORAS .xlsx` | Tablas físicas, CSV públicos, diseño y auditoría |
| `03_exploratory_analysis.py` | Tablas, diseño y auditoría generados por `01` | Tablas en `processed/analisis_listo/resumenes/`; informes y figuras en `docs/` |
| `04_prepare_chemical_data.py` | `processed/quimico_all_pina/quimico_all.xlsx` y diseño generado por `01` | Resultados químicos con trazabilidad, resultados no cuantificados, vista por parcela y CSV público |
| `05_prepare_nematode_data.py` | `raw/nematodos/nematodos_raw.xlsx` y diseño generado por `01` | Abundancias, parámetros, rasgos, índices NINJA y auditoría en `processed/nematodos_analisis_listo/` |
| `06_nematode_analysis.py` | Tablas validadas generadas por `05` | Resúmenes descriptivos y dos CSV públicos para el módulo de nematodos |
| `07_prepare_poxc_data.py` | Informe firmado de `raw/pina/PoxC/` y diseño generado por `01` | Resultado de carbono lábil con trazabilidad y auditoría |
| `08_poxc_analysis.py` | Resultado validado generado por `07` | Resumen por tratamiento, comparaciones dentro de finca y CSV público para POXC |
| `02_test_soil_pipeline.py` | Código y fuentes físicas | Validaciones del flujo físico; conserva su ubicación en src/ |

Para actualizar los cuatro módulos de la web:

```powershell
python src/01_soil_data_pipeline.py
python src/04_prepare_chemical_data.py
python src/05_prepare_nematode_data.py
python src/06_nematode_analysis.py
python src/07_prepare_poxc_data.py
python src/08_poxc_analysis.py
```

Para actualizar también el informe físico y sus figuras, después de `01`:

```powershell
python src/03_exploratory_analysis.py
```

`03` y `04` no dependen entre sí. Si cambia la ficha de fincas, repetir `01` y luego `04` para actualizar ambos módulos. **R significa repetición dentro de una parcela y un análisis**; el mismo número R en análisis distintos no identifica necesariamente la misma muestra.

Los datos de nematodos tampoco contienen repeticiones `R`: hay una muestra comunitaria por parcela. Después de ejecutar `01`, se preparan por separado con:

```powershell
python src/05_prepare_nematode_data.py
python src/06_nematode_analysis.py
```

Las decisiones sobre sus cuatro hojas y los campos conservados están documentadas en [`docs/preparacion_datos_nematodos.md`](docs/preparacion_datos_nematodos.md). El análisis y las variables publicadas se describen en [`docs/analisis_nematodos.md`](docs/analisis_nematodos.md).

El informe de carbono lábil se prepara y analiza por separado con:

```powershell
python src/07_prepare_poxc_data.py
python src/08_poxc_analysis.py
```

La transcripción controlada y la correspondencia de las muestras no disturbadas están documentadas en [`docs/preparacion_datos_poxc.md`](docs/preparacion_datos_poxc.md). Los resúmenes y comparaciones se describen en [`docs/analisis_poxc.md`](docs/analisis_poxc.md).

Se conservan los nombres y la ubicación de los scripts originales en `src/`. Las validaciones de `02` se pueden ejecutar por separado:

```powershell
python src/02_test_soil_pipeline.py
```

## Publicación y vista local

Mantener en Git los siete CSV públicos de las subcarpetas `web/` de los análisis físico, químico, nematodos y POXC, además de los archivos de la web. `.gitignore` excluye los demás CSV y los archivos originales; los enlaces de los informes a esos archivos son para uso local.

La estructura actual requiere publicar la raíz del repositorio (`/ (root)`) en GitHub Pages, no solo `/docs`: la web lee los CSV mediante rutas `../processed/.../web/`. El `index.html` de la raíz es una redirección necesaria, no una segunda web.

Para abrirla localmente, sin usar `file://`:

```powershell
python -m http.server 8000
```

Abrir <http://localhost:8000/>.

## Conservación y limpieza

Las seis tablas antes ubicadas en `docs/tablas/` están en `processed/analisis_listo/resumenes/`, sin recalcular sus valores. Tanto el informe existente como el script `03` utilizan esa ubicación; no se conservan copias duplicadas en `docs/`.

Las tres figuras anteriores `*_por_zona.png` se conservan en `docs/figuras/historico/`; las actuales están en `docs/figuras/agronomico/`. Los originales y los Excel consolidados se conservan sin cambios. Las cachés `.pyc` se retiraron del árbol de trabajo y `.gitignore` evita añadirlas de nuevo; Python puede regenerarlas cuando se ejecuten los scripts.
