# Preparación de datos de carbono lábil (POXC)

El código `src/07_prepare_poxc_data.py` prepara los resultados del informe firmado `LAIMEC-042-2026 Resultados carbono lábil-firmado.pdf`, conservado en `raw/pina/PoxC/`.

## Decisiones de preparación

- El PDF es la fuente canónica y no se modifica.
- Sus 12 resultados se transcriben explícitamente en el código porque el informe no contiene una tabla estructurada. El código valida previamente la huella SHA-256 exacta del PDF; si el archivo cambia, el proceso se detiene.
- Los códigos `P01` a `P08` corresponden a las parcelas de Piña de las fincas 1 a 8.
- Los códigos `P01-ND`, `P03-ND`, `P04-ND` y `P05-ND` se vinculan con las parcelas de Bosque de las fincas 1, 3, 4 y 5, respectivamente. La equivalencia queda registrada como criterio de correspondencia; el texto del informe utiliza «no disturbada».
- El método fue realizado por triplicado, pero el PDF publica solamente un resultado final por muestra. Por ello se conserva una observación por parcela y no se crean repeticiones `R`.
- La unidad normalizada es `mg POXC/kg de suelo seco`, de acuerdo con la descripción metodológica del informe.

## Salidas

Todas las salidas se escriben en `processed/poxc_analisis_listo/`:

- `resultados_poxc.csv`: resultado completo con fechas, método y procedencia.
- `auditoria_preparacion.csv`: controles de fuente, correspondencia y cobertura.

Los resúmenes descriptivos y la salida pública se generan después con `src/08_poxc_analysis.py`; no se mezclan con la preparación del informe.

## Ejecución

Desde la raíz del repositorio:

```powershell
python src/07_prepare_poxc_data.py
```

El código utiliza únicamente la biblioteca estándar de Python. Requiere que `processed/diseno_muestreo.csv` exista; este archivo se genera con `src/01_soil_data_pipeline.py`.
