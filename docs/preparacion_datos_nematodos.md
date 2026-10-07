# Preparación de los datos de nematodos

El libro original se conserva sin modificaciones en `raw/nematodos/`. La entrada canónica del código es `raw/nematodos/nematodos_raw.xlsx`; la copia con el nombre descriptivo recibido se conserva como respaldo de procedencia y no se procesa. La preparación usa las cuatro hojas porque representan capas distintas del proceso, pero evita tratarlas como cuatro bases independientes.

| Hoja | Función | Decisión |
|---|---|---|
| `Nematodos en piña` | Conteos por taxón, parámetros de laboratorio y fórmulas de abundancia | Conservar los conteos y parámetros; recalcular y contrastar la abundancia |
| `NINJA` | Matriz de abundancias suministrada al calculador NINJA | Conservar en `trazabilidad/` para poder reproducir la entrada exacta |
| `INDICES` | Índices y huellas calculados por NINJA | Conservar como resultados derivados, separados de los conteos |
| `NEMATODES` | Clases c-p/p-p, grupo alimenticio y masa por taxón | Conservar como catálogo de rasgos y validar que cubra todos los taxones |

## Decisiones de limpieza

- Las 12 muestras corresponden a parcelas completas: 8 de Piña y 4 de Bosque. Este archivo no contiene repeticiones `R`; no se crean ni se emparejan repeticiones con otros análisis.
- Los identificadores escritos como `PIÑA 1`, `PINA3` o `Bosque1` se normalizan a `Pina_1`, `Pina_3` y `Bosque_1`, y se vinculan con `processed/diseno_muestreo.csv` para obtener la finca y el productor.
- Los 35 taxones coinciden entre la tabla de conteos, la matriz NINJA y el catálogo de rasgos.
- Hay dos conteos vacíos: `Clarkus` en `Bosque_2` y `Bosque_3`. Las fórmulas del libro y la matriz NINJA los tratan como cero. La salida conserva el vacío original, registra por separado el cero usado por la fuente y lo señala en la auditoría; no se convierte silenciosamente en una ausencia observada.
- El parámetro `Vol counted for abundance (of 10 ml)` se conserva, aunque las fórmulas de abundancia del libro no lo utilizan. No se elimina porque puede ser información metodológica y conviene confirmar su función con quien realizó el procedimiento.
- `Vol added for ID` también se conserva. En la fórmula del libro aparece multiplicando y dividiendo, por lo que se cancela algebraicamente; el script reproduce la fórmula tal como está y verifica su coincidencia con `NINJA`.
- El número de la columna `MUESTRA` de `NINJA` se conserva únicamente como orden de carga. La parcela se identifica mediante la columna `ID`.
- El libro no registra la versión del calculador NINJA. Los índices se conservan, pero ese dato queda señalado como metadato faltante.

## Salidas

El script `src/05_prepare_nematode_data.py` crea únicamente archivos bajo `processed/nematodos_analisis_listo/`:

- `abundancia_taxones.csv`: tabla larga de conteos, abundancia absoluta y relativa por parcela y taxón, con celdas de procedencia.
- `parametros_muestras.csv`: parámetros y totales por parcela.
- `rasgos_taxones.csv`: catálogo de rasgos funcionales.
- `indices_ninja.csv`: índices en formato largo.
- `indices_ninja_por_parcela.csv`: vista ancha para revisión o análisis multivariado.
- `trazabilidad/matriz_ninja.csv`: copia tabular de la entrada utilizada por NINJA.
- `auditoria_preparacion.csv`: correspondencias, diferencias numéricas, vacíos y decisiones de tratamiento.

La abundancia se expresa como `individuos/100 cm3 de suelo` porque la hoja está encabezada como “MUESTRAS DE SUELO 100CC”. Esta interpretación debe confirmarse contra el protocolo de laboratorio antes de presentar resultados finales.

## Ejecución

Primero debe existir `processed/diseno_muestreo.csv`, generado por el código `01`. Luego, con el entorno de Python activado:

```powershell
python src/01_soil_data_pipeline.py
python src/05_prepare_nematode_data.py
```

El código `05` requiere `openpyxl`, valida completamente las cuatro hojas antes de escribir las salidas y no modifica el libro original. El análisis descriptivo y los dos CSV públicos se generan después mediante `python src/06_nematode_analysis.py`; la metodología está documentada en [`analisis_nematodos.md`](analisis_nematodos.md).
