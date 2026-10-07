# Análisis descriptivo de nematodos

El código `src/06_nematode_analysis.py` utiliza únicamente las salidas validadas por `05_prepare_nematode_data.py`. No vuelve a leer ni modificar el Excel original.

## Contenido del análisis

- Abundancia total y riqueza observada por parcela.
- Los 45 resultados de NINJA, organizados en índices, biomasa y huellas, número de individuos y porcentajes calculados.
- Los parámetros numéricos de conteo e identificación, separados de los resultados biológicos.
- Abundancia y porcentaje de los grupos alimenticios: herbívoros, fungívoros, bacterívoros, depredadores y omnívoros.
- Conteo de identificación, abundancia absoluta y composición porcentual de los 35 taxones.
- Grupo alimenticio, clases c-p y p-p y masa de cada taxón como contexto y en el resumen de taxones.
- Diferencias descriptivas Piña menos Bosque únicamente para las fincas que contienen ambos usos.

No se realizan pruebas inferenciales. Hay una muestra comunitaria por parcela y no existen repeticiones `R` dentro de este análisis. Las parcelas de Piña que no tienen una parcela de Bosque asociada se conservan en los resúmenes generales, pero no se incluyen en las comparaciones pareadas.

Los dos conteos vacíos de `Clarkus` continúan identificados en las tablas preparadas. El análisis utiliza las abundancias NINJA de la fuente, donde esos dos casos fueron tratados como cero; no los presenta como conteos observados.

## Salidas

Las tablas completas se escriben en `processed/nematodos_analisis_listo/resumenes/`:

- `resumen_por_parcela.csv`
- `grupos_funcionales_por_parcela.csv`
- `resumen_taxones.csv`
- `comparaciones_pina_bosque.csv`

La web utiliza `processed/nematodos_analisis_listo/web/resultados_nematodos.csv` para los gráficos y `processed/nematodos_analisis_listo/web/rasgos_taxones.csv` para el catálogo de rasgos. El primer archivo contiene 167 registros por parcela: 2 indicadores generales, 5 parámetros de muestra, los 45 resultados NINJA, 10 resultados de grupos alimenticios y 105 resultados correspondientes a 35 taxones en tres escalas. Los archivos omiten celdas de origen y metadatos internos del laboratorio, que permanecen en las tablas preparadas. Los índices, parámetros técnicos, grupos y taxones se separan en familias para evitar comparaciones improcedentes.

Además de la vista individual, la web ofrece barras apiladas para grupos alimenticios, mapas de calor para taxones y comparaciones pareadas Piña–Bosque para las fincas que contienen ambos usos.

Cuando la hoja fuente solo proporciona una sigla de huella (`CFT`, `EFT`, `SFT`, `HeFT`, `FuFT`, `BaFT` o `PrFT`) y no indica su unidad, la web conserva la sigla y muestra «unidad no indicada en la fuente»; no se asigna una interpretación adicional.

## Ejecución

```powershell
python src/01_soil_data_pipeline.py
python src/05_prepare_nematode_data.py
python src/06_nematode_analysis.py
```

Después de ejecutar `06`, deben añadirse a Git los dos CSV públicos de `processed/nematodos_analisis_listo/web/` para que GitHub Pages pueda leerlos.
