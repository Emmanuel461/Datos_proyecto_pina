# Preparación de los datos químicos

El resultado **`<1` mg/L de fósforo se conserva como un dato censurado por la izquierda**: su concentración está por debajo de 1 mg/L. No se sustituye por cero, 0,5 ni 1. El reporte no permite identificar ese umbral específicamente como límite de detección o de cuantificación; se denomina **límite reportado**.

## Fuente y trazabilidad

Se utiliza [el reporte químico original](../processed/quimico_all_pina/quimico_all.xlsx), hoja `26-05166 - 26-05177`, reporte 99442. El archivo ordenado estaba bloqueado para lectura durante esta preparación. Los originales no se modifican.

Hay 12 muestras de laboratorio, una por parcela, y 16 variables (192 resultados). Este archivo no contiene resultados químicos separados por repetición o submuestra; permite caracterizar cada parcela, pero no calcular su variación química interna mediante boxplots.

Los nombres entre paréntesis se conservan únicamente dentro de `id_usuario_original`; no se convierten en una asignación de productor ni se utilizan para emparejar parcelas.

| Parcela | ID laboratorio | Resultado de P | Celda original |
|---|---|---|---|
| Bosque 1 | S-26-05174 | <1 mg/L | L27 |
| Bosque 2 | S-26-05175 | <1 mg/L | L28 |
| Bosque 4 | S-26-05177 | <1 mg/L | L30 |

Para Piña 5, tanto la captura del archivo ordenado como el reporte original (celda L23) muestran **P = 1 mg/L**. El CSV preparado conserva ese valor.

## Archivos preparados

Ejecutar desde la raíz: `.venv/Scripts/python.exe src/04_prepare_chemical_data.py`.

- [Resultados con trazabilidad](../processed/quimico_analisis_listo/resultados_quimicos.csv): una fila por muestra y variable, con unidad, resultado original, valor numérico, operador, límite, estado y celda de procedencia.
- [Resultados no cuantificados](../processed/quimico_analisis_listo/resultados_no_cuantificados.csv): permite revisar censurados y faltantes por separado.
- [Vista por parcela](../processed/quimico_analisis_listo/quimica_por_parcela.csv): conserva `<1` para lectura en Excel.

Para `<1`, `valor` queda vacío, `operador` es `<`, `limite_reportado` es 1 y `estado` es `censurado`. El vacío de `valor` **no significa que falte la muestra**: siempre debe consultarse `estado`. Para una medición de 1, `valor` es 1 y `operador` es `=`. Un resultado no reconocido detiene la preparación para impedir conversiones silenciosas.

## Uso en el análisis exploratorio

Los tres censurados representan el 25 % de las muestras y el 75 % de las muestras de bosque para P. Calcular la media de bosque omitiéndolos dejaría únicamente Bosque 3 y daría una descripción incompleta. Tampoco corresponde introducir 0,5 como si fuera una medición: cualquier sustitución debe ser un escenario explícito de sensibilidad. La [guía de la EPA sobre datos ambientales](https://www.epa.gov/n-steps-online/data-considerations) describe la necesidad de considerar la censura en el análisis.

En las gráficas, representar estos resultados con un símbolo distinto situado en el límite, etiquetado `<1`; esa posición indica el umbral y no una concentración medida. Mantener los valores cuantificados de 1 mg/L visualmente diferenciados. No calcular diferencias exactas ni cocientes usando el límite en lugar del resultado censurado.

Como descripción sin imputación, suponiendo concentraciones no negativas, los cuatro bosques tienen una media de P en **[0,25; 1) mg/L**: tres valores en [0; 1) y uno reportado como 1. Este es un intervalo de valores compatibles con el reporte, no un intervalo de confianza. Las ocho parcelas de piña tienen una media de **1,75 mg/L** según el reporte original, incluida Piña 5 = 1. Estos resúmenes son descriptivos y todavía no constituyen una comparación experimental entre pares de parcelas.
