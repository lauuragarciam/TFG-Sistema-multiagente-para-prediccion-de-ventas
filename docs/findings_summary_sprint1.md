# Resumen de hallazgos del EDA: M5 (Sprint 1)

**Fecha:** 2026-11-19
**Analista:** autora del TFG
**Informe completo:** [eda_report_sprint1.md](eda_report_sprint1.md)
**Registro de supuestos:** [registro_supuestos.md](registro_supuestos.md) · **Plan:** [plan_sprint1.md](plan_sprint1.md)

Plantilla: `.claude/skills/programmatic-eda/assets/findings_summary.md`, ampliada con las cuatro preguntas del plan. Todas las cifras son de train (d_1–d_1829) y llevan entre paréntesis el fichero del que salen (`output/eda/`, `data/interim/`) o el supuesto del registro.

---

## Los datos de un vistazo

- **Ventas:** 30.490 series (producto × tienda) en formato ancho, una columna por día (`intermitencia_resumen_global.csv`). El EDA lee solo d_1–d_1829, del 2011-01-29 al 2016-01-31 (`calendar_perfil_train.csv`; N1, N2).
- **Calendario de train:** 1.829 días.
- **Precios de train:** 6.231.329 filas tienda × producto × semana, hasta la semana 11601 (`skill_perfilado/sell_prices_train_data_overview.txt`; N7).
- **Muestra larga del EDA:** 4.350.570 filas serie × día de 3.059 series con filas, de las 3.060 seleccionadas (`data/interim/metadatos_eda.json`; D4).
- **División:** train hasta d_1829, validación hasta d_1913 y test hasta d_1941. La firma es 9d6150930aea32ee (`metadatos_eda.json`; N1).

**Calidad general: buena.**
- No hay claves duplicadas (`sell_prices_estructura.csv`).
- No hay ventas antes del primer precio (`metadatos_eda.json`).
- Los tipos reducidos no pierden información (T1).

El problema principal es otro: muchos ceros de venta no son demanda nula, y hay que tratarlos por separado (ver Problema 1).

---

## Respuestas a las preguntas del plan

### P1. Intermitencia (ADI / CV²)

- **Tipo de demanda** (`intermitencia_resumen_global.csv`):

  | Tipo | % de series |
  |---|---|
  | suave | 6,14 |
  | errática | 2,84 |
  | intermitente | 72,75 |
  | irregular | 18,27 |

  **El 91,02 % de las series tiene ADI ≥ 1,32.**
- **Por categoría**, % con ADI ≥ 1,32, calculado con los conteos de `intermitencia_por_categoria.csv`: FOODS 87,31 %, HOBBIES 98,16 % y HOUSEHOLD 92,24 %.
- **Por tienda** (`intermitencia_por_tienda.csv`): entre el 82,32 % (CA_3) y el 95,15 % (CA_4).
- **Distribución del ADI** (`adi_cuantiles.csv`): mediana 2,760, p05 1,205 y p99 23,75.
- **Equivalencia con la frecuencia de venta:** ADI ≥ 1,32 equivale a vender en ≤ 75,76 % de los días. Se cumple en las 3.058 series de la muestra con ADI definido (N3; `muestra_dias_con_venta.csv`).
- **Consecuencia:** la clase discrimina poco, así que el coordinador usará también ADI y CV² continuos (C1).

### P2. Eventos y SNAP

- **Día de la semana:** sábado 1,207 y domingo 1,195, frente a 0,877-0,885 de martes a jueves. Es el índice normalizado por serie (`p2_dia_semana.csv`, TOTAL).
- **Eventos.** Índice dentro del mismo día de la semana (`p2_eventos_por_tipo.csv`):

  | Contexto | Índice |
  |---|---|
  | 2 días previos al evento | 1,035 |
  | Día de evento National | 0,855 |
  | National sin Navidad | 0,953 |
  | Cultural | 0,933 |
  | Religious | 1,015 |
  | Sporting | 1,010 |

  El día del evento, el índice baja a 0,941 (`p2_eventos_dias_previos.csv`). La ventana previa es de 2 días (N5).
- **SNAP.** Comparando dentro de los días 1-15 del mes y del mismo día de la semana, el efecto solo aparece en FOODS: CA ×1,062, TX ×1,129 y WI ×1,174 (`p2_snap.csv`; E3). En HOBBIES y HOUSEHOLD va de ×0,970 a ×1,046.

### P3. Precio

- **Efecto no atribuible en el EDA (E1).**
  - **Estudio de eventos** (`p3_eventos_precio.csv`). Se analizaron 1.592 bajadas y 1.864 subidas ≥ 5 %.
    - Semana del cambio: las bajadas dan 1,079, con un IC 95 % de 0,976 a 1,212. Las subidas dan 0,871.
    - La semana anterior hay una caída común en los dos tipos de cambio (0,876 y 0,819), así que la referencia está contaminada.
  - **Correlación dentro de cada serie:** la mediana de Spearman es −0,009, y el 31,06 % de las series no tiene ningún cambio de precio (`p3_correlacion_resumen.csv`).
  - **Los dos controles se contradicen** (`p3_precio_por_tramo.csv`, TOTAL). En el tramo ≤ −15 %, el índice por día de la semana es 1,230, pero el índice local es 0,962.
- **Señal indirecta:** los días outlier se concentran en semanas con descuento ≥ 5 %, con un lift de 2,320 (`outliers_contexto.csv`; T9).

### P4. Estacionalidad

- **Semanal**, índice del sábado por departamento (`p4_semanal_departamento.csv`): entre 1,112 (HOBBIES_2) y 1,264 (HOUSEHOLD_1).
- **Anual**, índice mensual normalizado por año con 2012-2015 (`p4_anual_ajustado_departamento.csv`; E4):
  - Es moderada: entre 0,874 (FOODS_3, diciembre) y 1,136 (FOODS_2, enero).
  - La excepción es HOBBIES_2: febrero 1,320 y julio 0,779.

---

## Principales problemas de calidad

### Problema 1: ceros que no son demanda
- **Qué:**
  - Días anteriores al primer precio: 1.246.170 filas excluidas en la muestra, con 0 unidades vendidas (`metadatos_eda.json`; D2).
  - 24 tienda-días cerrados, todos en Navidad (`ceros_tiendas_cerradas.csv`; C2).
  - 2.762 series con una racha final sin ventas compatible con una salida de venta (`salida_venta_resumen.csv`; D7).
- **Impacto:** inflan el ADI y el número de ceros que los agentes deben aprender.
- **Acción:**
  - Los días antes del primer precio y los de tienda cerrada se excluyen del ADI y del CV² (N3, C2).
  - La posible salida de venta **solo se marca** (D7).
- **Responsable:** analista (CU-01).

### Problema 2: series sin historial en train
- **Qué:** 8 series sin ningún precio en train y 2 a la venta sin ninguna venta. En las 10, ADI y CV² están indefinidos y se clasifican como intermitentes con aviso (`clasificacion_series_train.parquet`; C1).
- **Impacto:** no tienen contexto para el coordinador.
- **Acción:** el tratamiento queda para el modelado (C1).
- **Responsable:** analista (Sprint 2).

### Problema 3: nulos estructurales de eventos
- **Qué:** `event_name_1` y `event_type_1` tienen un 92,02 % de nulos, y `event_name_2` y `event_type_2` un 99,78 % (`skill_perfilado/calendar_train_null_profiler.csv`). Superan el umbral FAIL del 30 % de la skill.
- **Impacto:** ninguno. Un nulo significa que ese día no hay evento.
- **Acción:** riesgo aceptado; no se imputan (D1).
- **Responsable:** analista.

### Problema 4: semana de precios a caballo del corte
- **Qué:** la semana 11601 va del 30-01 al 05-02-2016 (N7).
- **Impacto:** puede haber fuga si se usan sus días de validación.
- **Acción:** el precio se conoce el 31-01 y la unión con las ventas verifica que no hay días > d_1829 (N7; `test_division.py`).
- **Responsable:** analista.

---

## Lo que está bien

- 0 claves duplicadas tienda-producto-semana en sell_prices completo, que tiene 6.841.121 filas (`sell_prices_estructura.csv`).
- Calendario de train continuo: 1.829 fechas distintas, del 2011-01-29 al 2016-01-31 (`skill_perfilado/calendar_train_data_overview.txt`, `calendar_perfil_train.csv`).
- Sin nulos en sell_prices_train (`skill_perfilado/sell_prices_train_null_profiler.csv`).
- La muestra es representativa: 60,08 % de días sin venta frente a 59,79 % en el total, y 1,394 frente a 1,432 ventas por serie-día (`muestra_vs_total.csv`; D4).
- Picos de memoria de 883 MB en `preparar_eda` y de 791 MB en `intermitencia_global`, frente al límite de 5 GB (T2; `metadatos_eda.json`).

---

## Salvedades

- **E1, precio:** el efecto no es atribuible en el EDA. Las cifras de P3 son asociaciones, no efectos causales.
- **E4, estacionalidad anual:** la normalización por año sube enero y baja diciembre en los departamentos con tendencia dentro del año (FOODS_3: diciembre 0,874). Queda por valorar una media móvil centrada de 2×12 meses.
- **D7, posible salida de venta:** es solo una marca. La clasificación vigente no cambia. Además, M5 no distingue la retirada del producto de la falta de stock.
- **Muestra:** P2, P3, P4 y los outliers se calculan con la muestra de 3.059 series (D4). P1 y D7 usan las 30.490.

## Decisiones pendientes

- **C3:** fuga suave dentro de train si ADI, CV² y L se calculan con todo train y se usan como contexto. Hay que elegir entre (a) calcularlos en el origen de cada predicción y (b) aceptarlos como propiedad casi estática de la serie. Se decide en el Sprint 2 (CU-01).
- **T8:** la tabla larga ocupa 22,114 bytes por fila, lo que supone 916,7 MB para las 30.490 series y 43.466.893 filas (`memoria_tabla_larga.csv`). La columna `date` ocupa 8 bytes y se puede derivar de `dia_num`. Falta decidir si se quita en la tabla procesada de CU-01.

---

## Siguiente paso

- [x] Los datos están listos para el análisis. Siguiente paso: Sprint 2, con la tabla procesada de CU-01 y las variables de los agentes.
- [ ] Hace falta corregir datos antes de continuar: no.
- [ ] Hace falta investigar más: C3 y T8 antes de fijar el esquema de CU-01.
