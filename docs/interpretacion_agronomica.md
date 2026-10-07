# Interpretación agronómica del análisis exploratorio

Lectura de los resultados disponibles al 18 de septiembre de 2026.

Este documento interpreta la caracterización de las **12 parcelas: cuatro de Bosque y ocho de Piña**. Se asume la coherencia metodológica del muestreo, según lo establecido para el estudio. Las repeticiones R son submuestras dentro de cada parcela: ocho para densidad y porosidad y tres para retención de humedad, textura y estabilidad de agregados.

Los valores proceden del resumen por parcela, las observaciones individuales y las comparaciones dentro de finca, enlazados en la sección «Archivos y reproducción» del [informe exploratorio](analisis_exploratorio.md). Al volver a ejecutar `03_exploratory_analysis.py`, esas tablas se guardan en `processed/analisis_listo/resumenes/`. Los gráficos están en el mismo informe y el detalle de cada parcela en las [fichas individuales](caracterizacion_parcelas.md).

Las expresiones «mayor», «menor» y «más variable» se refieren a estas parcelas y a los indicadores medidos. La interpretación es descriptiva; las diferencias no se presentan como resultados de pruebas de significancia.

## 1. Qué muestran los indicadores en conjunto

El resultado principal es la existencia de **perfiles físicos distintos entre parcelas**, incluso dentro del mismo uso del suelo. Una parcela puede combinar estabilidad de agregados relativamente alta con menor agua útil, o menor densidad aparente con una retención de agua inferior a otra parcela. Conviene interpretar conjuntamente el nivel de cada indicador y su dispersión.

La densidad aparente expresa masa de suelo seco por volumen, mientras que la porosidad representa la proporción de espacio poroso. La estabilidad de agregados describe la resistencia de la agregación frente a fuerzas que desintegran la estructura. Son propiedades relacionadas, pero cada una describe un aspecto físico diferente. [NC State Extension: salud física del suelo](https://soilmanagement.ces.ncsu.edu/soil-health/soil-physical-health/).

En esta base, la porosidad se calcula como `100 × (1 − densidad aparente / densidad de partículas)`. Por ello, densidad y porosidad deben leerse juntas: la segunda no constituye una evidencia independiente de las densidades. La densidad de partículas media varía entre **2,43 y 2,71 g/cm³**; conservar ese valor propio de cada parcela evita interpretar la porosidad como si todas tuvieran idéntica densidad de partículas.

El agua útil corresponde a la diferencia entre la humedad gravimétrica a 0,33 bar y a 15 bar. Se mantiene en **porcentaje gravimétrico**, equivalente a gramos de agua por 100 gramos de suelo seco. Aquí describe el intervalo de agua retenida entre ambas presiones; no se expresa como milímetros de agua almacenada en el perfil.

## 2. Caracterización de las parcelas de Bosque

La tabla presenta medias de parcela. La última columna interpreta su perfil dentro del conjunto de bosques.

| Parcela | Densidad aparente (g/cm³) | Porosidad (%) | Agua útil (% gravimétrico) | Estabilidad de agregados (%) | Lectura del perfil |
| --- | --- | --- | --- | --- | --- |
| Bosque 1 | 0,86 | 68,36 | 30,71 | 61,33 | Mayor densidad aparente media entre los bosques. Agua útil relativamente uniforme y marcada dispersión de la estabilidad de agregados. |
| Bosque 2 | 0,74 | 70,56 | 36,73 | 91,00 | Mayor porosidad media del conjunto de parcelas y segunda mayor agua útil entre los bosques. La retención presenta variación entre submuestras. |
| Bosque 3 | 0,84 | 66,11 | 23,91 | 97,33 | Menor porosidad y agua útil medias entre los bosques, junto con la mayor estabilidad de agregados de este grupo. |
| Bosque 4 | 0,73 | 70,41 | 49,75 | 96,00 | Menor densidad aparente y mayor agua útil medias de toda la base; combina una porosidad relativamente alta con estabilidad de agregados cercana entre submuestras. |

**Bosque 1 destaca por la distribución de su estabilidad de agregados.** Sus valores son 17, 84 y 83 %. La media de 61,33 % resume las tres observaciones, mientras la mediana de 83 % muestra la posición central. Dos submuestras se concentran en 83–84 % y una tiene un valor mucho menor. El boxplot representa precisamente esa heterogeneidad; describir la parcela solo con la media ocultaría esta distribución. En cambio, su agua útil presenta un CV de **7,00 %**, el menor entre los bosques.

**Bosque 2 reúne baja densidad aparente y elevada porosidad total dentro del conjunto.** La media de porosidad es 70,56 % y la mediana 69,07 %. La submuestra con densidad de 0,56 g/cm³ y porosidad de 77,69 % contribuye a esa diferencia entre media y mediana. Su agua útil varía de **28,71 a 47,22 %**, por lo que la media de 36,73 % debe acompañarse de esa amplitud.

**Bosque 3 muestra que la estabilidad de agregados y el agua útil describen aspectos diferentes.** La estabilidad se concentra en 97–98 %, pero el agua útil varía de **11,84 a 34,79 %**, con CV de 48,19 %. Es un perfil de agregados estables en las submuestras medidas y retención de agua heterogénea dentro de parcela.

**Bosque 4 destaca por la magnitud del agua útil.** Incluso su menor valor, 40,27 %, supera las medias de agua útil de los otros bosques. Su media de 49,75 % y mediana de 53,12 % muestran que este resultado no depende de una sola observación elevada. Esa característica acompaña a una densidad aparente media de 0,73 g/cm³ y una porosidad media de 70,41 %.

Gráficos relacionados: [boxplots de densidad y porosidad](figuras/agronomico/densidad_porosidad_boxplot_bosque.png), [retención de humedad](figuras/agronomico/retencion_humedad_boxplot_bosque.png) y [textura y estabilidad](figuras/agronomico/textural_boxplot_bosque.png).

## 3. Caracterización de las parcelas de Piña

La tabla presenta medias de parcela. Las posiciones relativas de la última columna corresponden al grupo de Piña.

| Parcela | Densidad aparente (g/cm³) | Porosidad (%) | Agua útil (% gravimétrico) | Estabilidad de agregados (%) | Lectura del perfil |
| --- | --- | --- | --- | --- | --- |
| Piña 1 | 0,76 | 70,37 | 15,40 | 90,00 | Menor densidad aparente y mayor porosidad medias del grupo; el agua útil ocupa una posición intermedia. |
| Piña 2 | 0,94 | 62,55 | 16,44 | 87,00 | Densidad aparente relativamente alta y uniforme entre submuestras; menor estabilidad media del grupo. |
| Piña 3 | 0,89 | 65,28 | 12,26 | 89,33 | Mayor proporción de arcilla y segunda menor agua útil media; esta última es la más uniforme del grupo. |
| Piña 4 | 0,93 | 62,78 | 14,59 | 94,00 | Mayor dispersión relativa del agua útil; estabilidad de agregados idéntica en las tres observaciones registradas. |
| Piña 5 | 0,88 | 66,43 | 21,63 | 98,00 | Mayor agua útil y estabilidad medias del grupo; menor proporción de arcilla del conjunto de parcelas. |
| Piña 6 | 0,97 | 60,20 | 12,06 | 95,67 | Menor agua útil media de la base; segunda mayor densidad aparente y segunda menor porosidad del grupo. |
| Piña 7 | 0,99 | 60,09 | 14,43 | 91,67 | Mayor densidad aparente y menor porosidad medias de la base; este patrón acompaña a un agua útil inferior a la de Piña 5 y Piña 8. |
| Piña 8 | 0,87 | 65,74 | 19,14 | 97,00 | Segunda mayor agua útil media del grupo, con una submuestra que eleva la media respecto de la mediana. |

**Piña 1, Piña 5 y Piña 8 destacan por características distintas.** Piña 1 sobresale en menor densidad y mayor porosidad; Piña 5 en agua útil y estabilidad; Piña 8 combina estabilidad de 96–98 % con agua útil media relativamente elevada. Estas diferencias impiden asignar una posición global a las parcelas usando un único indicador.

**Piña 6 y Piña 7 concentran las mayores densidades aparentes y las menores porosidades medias del grupo.** Piña 6 añade la menor agua útil media, de 12,06 %, aunque su estabilidad alcanza 95,67 %. Estos perfiles permiten identificar dónde se concentran las diferencias físicas dentro del cultivo. Los valores relativos por sí solos no establecen un umbral de compactación limitante para el crecimiento.

**Piña 2 es uniforme en densidad, y Piña 3 lo es en agua útil.** El CV de densidad aparente de Piña 2 es 3,53 %, el menor del grupo. En Piña 3, el agua útil se sitúa entre 11,77 y 12,61 %, con CV de 3,58 %. Una dispersión pequeña describe la similitud de las submuestras; puede acompañar tanto valores relativamente bajos como relativamente altos del indicador.

**Piña 4 necesita una lectura explícita de su dispersión.** El agua útil de sus submuestras va de 8,88 a 22,67 %, con media de 14,59 %, mediana de 12,21 % y CV de 49,33 %. Es el mayor CV de agua útil de las 12 parcelas. En la misma parcela, la estabilidad de agregados es 94 % en las tres submuestras: la homogeneidad de un indicador no implica homogeneidad de los demás.

**En Piña 8, la media y la mediana aportan información complementaria.** El agua útil es 15,80, 15,40 y 26,21 % en R1, R2 y R3. La media de 19,14 % refleja las tres observaciones; la mediana de 15,80 % muestra que dos están próximas al extremo inferior. Se conservan las tres en la caracterización.

Gráficos relacionados: [boxplots de densidad y porosidad](figuras/agronomico/densidad_porosidad_boxplot_pina.png), [retención de humedad](figuras/agronomico/retencion_humedad_boxplot_pina.png) y [textura y estabilidad](figuras/agronomico/textural_boxplot_pina.png).

## 4. Textura y retención: lectura conjunta

Todas las submuestras están registradas en la clase **Arcilloso**, pero las medias de arcilla van de **48,67 % en Piña 5 a 69,00 % en Piña 3**. Compartir una clase textural no equivale a tener la misma proporción de arena, limo y arcilla. El [gráfico de composición textural](figuras/agronomico/composicion_textural_parcelas.png) permite observar estas diferencias dentro de la misma clase.

Piña 3 tiene más arcilla que Piña 5, pero su agua útil media es menor: **12,26 frente a 21,63 %**. La humedad a 0,33 bar es 40,79 % en Piña 3 y 47,06 % en Piña 5; a 15 bar es 28,53 y 25,44 %, respectivamente. La combinación de ambas mediciones explica la diferencia del intervalo de agua útil. En estas parcelas, el porcentaje de arcilla por sí solo no ordena la disponibilidad gravimétrica medida.

También conviene distinguir retención a una presión determinada y agua útil. Piña 8 presenta una humedad media a 0,33 bar ligeramente mayor que Piña 5 (**47,94 frente a 47,06 %**), pero retiene más agua a 15 bar (**28,80 frente a 25,44 %**). Como resultado, su agua útil es menor: **19,14 frente a 21,63 %**. Una mayor retención a 0,33 bar no se traduce automáticamente en un intervalo mayor entre ambas presiones.

Estas lecturas describen los perfiles observados. No se ha ajustado un modelo que estime cuánto de la variación del agua útil corresponde a textura, estructura u otros indicadores.

## 5. Qué aporta la variación entre repeticiones

El [mapa de CV](figuras/agronomico/variabilidad_interna_parcelas.png) permite localizar parcelas cuya media necesita acompañarse especialmente de la distribución de los valores.

| Indicador y parcela | Valores o intervalo observados | Lectura de la variabilidad |
| --- | --- | --- |
| Estabilidad de agregados, Bosque 1 | 17, 84 y 83 %; CV 62,60 % | La media y la mediana se separan porque una submuestra tiene un valor mucho menor que las otras dos. |
| Agua útil, Piña 4 | 8,88–22,67 %; CV 49,33 % | La amplitud entre submuestras es grande respecto de la media de la parcela. |
| Agua útil, Bosque 3 | 11,84–34,79 %; CV 48,19 % | Existe dispersión marcada del agua útil, aunque la estabilidad de agregados es muy uniforme. |
| Agua útil, Piña 8 | 15,40–26,21 %; CV 32,03 % | Una observación eleva la media respecto de la mediana. |
| Agua útil, Piña 3 | 11,77–12,61 %; CV 3,58 % | El valor relativamente bajo se presenta de forma consistente en las tres submuestras. |

Un **CV alto representa variación relativa dentro de parcela**, no una categoría de deterioro. Un CV de cero, como en la estabilidad de Piña 4 y Piña 5, indica que los valores registrados son iguales a la precisión de los datos. La interpretación corresponde a las submuestras observadas.

## 6. Comparaciones Piña–Bosque dentro de finca

Estas comparaciones complementan la caracterización individual. Se utiliza la correspondencia de la ficha de campo; el número original de Bosque no siempre coincide con el de Piña.

En la tabla, **Δ = media de Piña − media de Bosque**. Las diferencias de variables expresadas en porcentaje se presentan en **puntos porcentuales (pp)**. Los cálculos se realizaron antes del redondeo.

| Finca y pareja | Δ densidad aparente (g/cm³) | Δ porosidad (pp) | Δ agua útil (pp gravimétricos) | Δ estabilidad (pp) |
| --- | --- | --- | --- | --- |
| Finca 1: Piña 1 / Bosque 1 | −0,09 | +2,01 | −15,32 | +28,67 |
| Finca 3: Piña 3 / Bosque 2 | +0,15 | −5,28 | −24,47 | −1,67 |
| Finca 4: Piña 4 / Bosque 3 | +0,09 | −3,33 | −9,32 | −3,33 |
| Finca 5: Piña 5 / Bosque 4 | +0,14 | −3,98 | −28,12 | +2,00 |

**El patrón más consistente es la menor agua útil media de Piña en las cuatro parejas.** La diferencia va de −9,32 a −28,12 pp. Expresada respecto de cada bosque, la media de Piña es entre **38,98 y 66,61 % menor**. Esto describe la magnitud de las diferencias observadas, sin agregar las submuestras de distintas fincas en una sola comparación.

**Densidad y porosidad muestran una dirección compartida en tres parejas.** En las fincas 3, 4 y 5, Piña tiene mayor densidad aparente y menor porosidad que su bosque correspondiente. La finca 1 presenta la dirección contraria, aunque también tiene menor agua útil en Piña. Esta combinación confirma la utilidad de mantener visibles las diferencias por parcela.

**La estabilidad de agregados no presenta una dirección uniforme.** Piña supera al bosque en las fincas 1 y 5 y queda por debajo en las fincas 3 y 4. La mayor diferencia media ocurre en la finca 1 y debe leerse junto con los valores 17, 84 y 83 % de Bosque 1. Como referencia complementaria, las medianas de Piña 1 y Bosque 1 son 90 y 83 %, una diferencia de 7 pp, frente a los 28,67 pp de diferencia entre medias. Ambas describen aspectos distintos de las distribuciones.

Las parcelas Piña 2, Piña 6, Piña 7 y Piña 8 se interpretan mediante sus perfiles propios y su posición dentro del conjunto de piñas; no tienen una pareja de Bosque asignada en la ficha.

## 7. Lectura agronómica integrada

Los datos permiten distinguir tres aspectos de la caracterización:

- **Magnitud de los indicadores:** Bosque 4 destaca por su agua útil; entre las piñas, Piña 5 destaca por agua útil y estabilidad, Piña 1 por menor densidad y mayor porosidad, y Piña 6 y Piña 7 por la combinación de mayor densidad y menor porosidad dentro del grupo.
- **Heterogeneidad dentro de parcela:** Bosque 1 en estabilidad de agregados y Piña 4, Bosque 3 y Piña 8 en agua útil muestran por qué los puntos individuales, las medianas y los rangos complementan las medias.
- **Dirección de las diferencias entre usos:** el agua útil es menor en Piña en las cuatro parejas; la densidad y la porosidad siguen una misma dirección en tres; la estabilidad cambia de dirección según la finca.

La caracterización física reúne indicadores complementarios. Una evaluación integral de salud del suelo incorpora también información química y biológica; un único indicador no resume todas las funciones del suelo. [USDA-NRCS: evaluación de la salud del suelo](https://www.nrcs.usda.gov/conservation-basics/soil/soil-health/soil-health-assessment).

Esta interpretación corresponde a las tablas actuales. Al incorporar nuevas muestras o actualizar los resultados, deben revisarse las cifras y las conclusiones de este documento junto con las figuras del informe.
