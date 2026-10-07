# Análisis descriptivo de carbono lábil (POXC)

El código `src/08_poxc_analysis.py` lee exclusivamente `processed/poxc_analisis_listo/resultados_poxc.csv`, generado y validado por `07_prepare_poxc_data.py`. No vuelve a leer ni interpretar el PDF.

## Alcance

- Resume por separado las ocho parcelas de Piña y las cuatro parcelas de Bosque mediante número de parcelas, media, mediana, mínimo y máximo.
- Compara Piña y Bosque únicamente dentro de las fincas 1, 3, 4 y 5, que contienen ambos usos.
- Calcula la diferencia descriptiva `POXC Piña − POXC Bosque` para cada una de esas cuatro fincas.
- No realiza pruebas inferenciales debido al tamaño y al diseño de los datos.
- No crea repeticiones `R`: el triplicado descrito por el laboratorio forma parte del procedimiento analítico y el informe publica un único resultado final por parcela.

## Salidas

El código escribe dentro de `processed/poxc_analisis_listo/`:

- `resumenes/resumen_por_tratamiento.csv`
- `resumenes/comparaciones_pina_bosque.csv`
- `web/resultados_poxc.csv`

El CSV de `web/` conserva la misma estructura básica de resultados de laboratorio utilizada por el módulo químico, pero POXC permanece como un análisis y una fuente independientes. La portada de la web lo presenta como un módulo sencillo con filtros por tratamiento y finca, gráfico descriptivo, disponibilidad por parcela y exportación CSV.

## Ejecución

Desde la raíz del repositorio y después de ejecutar `07`:

```powershell
python src/08_poxc_analysis.py
```

El código utiliza únicamente la biblioteca estándar de Python.
