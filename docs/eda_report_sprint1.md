# Informe EDA: M5, ficheros de train del Sprint 1

**Analista:** autora del TFG
**Fecha:** 2026-11-19
**Ficheros:** `data/interim/calendar_train.parquet`, `data/interim/sell_prices_train.parquet` y `data/interim/ventas_muestra_largo.parquet`
**Contexto:** predicción de demanda diaria por producto y tienda (M5) con agentes y un coordinador. El EDA decide las variables de los agentes (RF-06 a RF-09), el contexto del coordinador (RF-10) y la clasificación de series (RF-03).

Plantilla: `.claude/skills/programmatic-eda/assets/eda_report_template.md`, con una ficha por fichero. Solo usa datos que ya existen:
- Las salidas de los scripts de la skill están en `output/eda/skill_perfilado/`. Se ejecutaron solo sobre calendar_train y sell_prices_train (T3).
- Para la muestra no se ejecutó la skill (T11). Sus cifras salen de nuestras salidas.
- Cuando una comprobación no está en ningún fichero, se indica como **no comprobado**.

---

## Ficha A: calendar_train (una fila = un día)

### 1. Visión general

| Propiedad | Valor | Fuente |
|---|---|---|
| Filas | 1.829 | `calendar_train_data_overview.txt` |
| Columnas | 15 | ídem |
| Memoria (MB) | 0,14 | ídem |
| Rango de fechas | 2011-01-29 → 2016-01-31 | `calendar_perfil_train.csv` |
| Grano | un día | — |
| Clave | `date` / `dia_num`: únicas (1.829 valores distintos para 1.829 filas) | `calendar_train_data_overview.txt` |

**Esquema:**
- `date`: datetime64.
- `wm_yr_wk`, `year` y `dia_num`: int16.
- `wday`, `month` y `snap_CA/TX/WI`: int8.
- `weekday`, `event_name_1/2` y `event_type_1/2`: category.
- `d`: string.

Todas las columnas están completas al 100 % salvo las de eventos (`calendar_train_data_overview.txt`).

### 2. Nulos

| Columna | % de nulos | Estado (skill) | Acción |
|---|---|---|---|
| `event_name_1`, `event_type_1` | 92,02 | FAIL | Ninguna: nulo estructural, el día no tiene evento (D1) |
| `event_name_2`, `event_type_2` | 99,78 | FAIL | Ninguna (D1) |
| resto (11 columnas) | 0,00 | OK | — |

Fuente: `calendar_train_null_profiler.csv`. `cargar_calendar` comprueba que no hay `event_name_2` en días sin `event_name_1` (D1).

### 3. Duplicados

| Comprobación | Resultado | Fuente |
|---|---|---|
| Filas duplicadas | 0 (las 1.829 fechas son distintas) | `calendar_train_data_overview.txt` |
| Claves duplicadas (`date`, `dia_num`) | 0 | ídem |

### 4. Validez

| Columna | Comprobación | Resultado | Fuente |
|---|---|---|---|
| `dia_num` | 1–1829, sin días posteriores al corte | PASS | `calendar_train_outlier_detector.csv`; `test_calendar_train_solo_train` |
| `wm_yr_wk` | 11101–11601 (11601 = semana del corte) | PASS | `calendar_train_outlier_detector.csv`; N7 |
| `snap_*` | solo 0 y 1; 600 días SNAP por estado | PASS | `calendar_train_data_overview.txt`; `calendar_perfil_train.csv` |
| `event_type_*` | 4 tipos (Cultural, National, Religious, Sporting) | PASS | `calendar_train_data_overview.txt` |

### 5. Distribuciones

Las columnas numéricas son índices de tiempo o indicadores binarios, así que sus estadísticos no aportan nada (`calendar_train_distribution_summary.csv`). Lo relevante es el perfil (`calendar_perfil_train.csv`):
- 146 días con evento y 4 con dos eventos.
- 30 eventos distintos.
- Días-evento por tipo, contando `event_type_1` y `event_type_2` (N9): Cultural 35, National 50, Religious 50 y Sporting 15.

### 6. Outliers

`calendar_train_outlier_detector.csv` no marca ningún outlier en ninguna columna. Decisión: ninguna.

### 7. Correlaciones

| Columna A | Columna B | r | Explicación |
|---|---|---|---|
| `wm_yr_wk` | `dia_num` | 0,9955 | Las dos son índices de tiempo |
| `wm_yr_wk` | `year` | 0,9862 | Índices de tiempo |
| `year` | `dia_num` | 0,9800 | Índices de tiempo |

Fuente: `calendar_train_correlation_explorer.txt`. No implican riesgo: estas columnas no entran juntas como variables sin transformar.

### 8. Lógica de negocio

| Comprobación | Resultado | Notas |
|---|---|---|
| Los cortes de la división corresponden a las fechas de la configuración | PASS | `tests/test_division.py` (N1) |
| `dia_num` deriva de `d` | PASS | `test_indices_de_corte_coinciden_con_las_fechas` |

---

## Ficha B: sell_prices_train (una fila = tienda, producto y semana)

### 1. Visión general

| Propiedad | Valor | Fuente |
|---|---|---|
| Filas | 6.231.329 | `sell_prices_train_data_overview.txt` |
| Columnas | 4 | ídem |
| Memoria (MB) | 53,73 | ídem |
| Rango de semanas | 11101 → 11601 (262 semanas distintas) | `sell_prices_train_data_overview.txt`, `sell_prices_train_distribution_summary.csv` |
| Grano | tienda × producto × semana | — |
| Clave | (`store_id`, `item_id`, `wm_yr_wk`): 0 duplicados en el fichero completo de 6.841.121 filas, del que este es un subconjunto | `sell_prices_estructura.csv` |

**Esquema:** `store_id` y `item_id` son category (10 y 3.049 valores distintos), `wm_yr_wk` es int16 y `sell_price` es float32. Todas las columnas están completas al 100 %.

### 2. Nulos

Ningún nulo en las 4 columnas; estado OK (`sell_prices_train_null_profiler.csv`).

### 3. Duplicados

| Comprobación | Resultado | Fuente |
|---|---|---|
| Filas duplicadas | 0 (implícito: 0 claves duplicadas) | `sell_prices_estructura.csv` |
| Claves duplicadas | 0 | ídem |

### 4. Validez

| Columna | Comprobación | Resultado | Fuente |
|---|---|---|---|
| `sell_price` | > 0; mínimo 0,01 y máximo 107,32 | PASS | `sell_prices_train_outlier_detector.csv` |
| `wm_yr_wk` | ≤ 11601 (semana del corte) | PASS | ídem; `test_precios_train_hasta_semana_de_corte` |
| `store_id` / `item_id` | 10 tiendas y 3.049 productos | PASS | `sell_prices_train_data_overview.txt` |
| Integridad referencial | 30.482 pares tienda-producto con precio en train; 8 series sin ninguno | Documentado | registro D2 |

### 5. Distribuciones

| Columna | Media | Mediana | Desv. típ. | p5 | p95 | Asimetría | Marca |
|---|---|---|---|---|---|---|---|
| `sell_price` | 4,404 | 3,47 | 3,396 | 0,97 | 10,98 | 2,217 | asimetría > 2 |

Fuente: `sell_prices_train_distribution_summary.txt`. La asimetría viene de mezclar productos de precios muy distintos. Los análisis usan la variación de precio respecto a la mediana de cada serie (N4), no el precio absoluto.

### 6. Outliers

| Columna | Nº de outliers | % | Clasificación | Decisión |
|---|---|---|---|---|
| `sell_price` | 274.101 (IQR) | 4,4 | Reales: el IQR global mezcla productos distintos | Se mantienen (T3) |

Fuente: `sell_prices_train_outlier_detector.csv`.

### 7. Correlaciones

No hay pares con |r| ≥ 0,8. Entre `wm_yr_wk` y `sell_price`, r = 0,0196 (`sell_prices_train_correlation_explorer.txt`). Para obtenerlo hubo que usar `--threshold 0` (T3).

### 8. Lógica de negocio

| Comprobación | Resultado | Notas |
|---|---|---|
| Ninguna serie vende antes de su primer precio | PASS | 0 unidades en días excluidos (`metadatos_eda.json`; D2) |
| No hay huecos de precio intermedios | PASS | notas.md; supuesto de `precio_eventos.py` |
| La unión con las ventas no crea filas ni días posteriores al corte | PASS | N7 |

---

## Ficha C: muestra larga de ventas (una fila = serie × día)

### 1. Visión general

| Propiedad | Valor | Fuente |
|---|---|---|
| Filas | 4.350.570 | `metadatos_eda.json` |
| Columnas | 10 | `memoria_tabla_larga.csv` |
| Memoria (MB) | 91,8 (22,114 bytes por fila) | `memoria_tabla_larga.csv` (`bytes_muestra` TOTAL = 96.207.059) |
| Rango | d_1 → como mucho d_1829 | `test_muestra_larga_solo_train` |
| Grano | serie × día a la venta (desde el primer precio) | D2 |
| Series | 3.060 seleccionadas; 3.059 con filas | `metadatos_eda.json` |
| Clave (`id`, `dia_num`) | **no comprobado** como clave única con un fichero | — |

**Esquema** (`memoria_tabla_larga.csv`):
- `id`, `item_id`, `dept_id`, `cat_id`, `store_id` y `state_id`: category.
- `ventas`, `dia_num` y `wm_yr_wk`: int16.
- `date`: datetime64.

### 2. Nulos

**No hay perfil de nulos en ningún fichero** (T11). Las ventas se leen como int32, y esa lectura falla si hay valores vacíos. Después se reducen a int16 tras comprobar el rango (T1).

### 3. Duplicados

**No comprobado** con un fichero. Por construcción, la tabla es el `melt` de una fila por serie, así que no debería haber duplicados, pero no hay un recuento guardado.

### 4. Validez

| Columna | Comprobación | Resultado | Fuente |
|---|---|---|---|
| `ventas` | rango compatible con int16 y ≥ 0 | PASS | T1 |
| `dia_num` | ≤ 1829 | PASS | `test_muestra_larga_solo_train` |
| Filas antes del primer precio | excluidas: 1.246.170, con 0 unidades | PASS | `metadatos_eda.json` |
| Filas en tienda-días cerrados | 5.871; se mantienen, pero se excluyen de ADI y de la comparación con el total | Documentado | C2; registro de validaciones |

### 5. Distribuciones

| Indicador | Muestra | Total (30.490) | Fuente |
|---|---|---|---|
| % de días sin venta | 60,08 | 59,79 | `muestra_vs_total.csv` |
| Ventas medias por serie-día | 1,394 | 1,432 | ídem |
| Mediana por serie del % de días sin venta | 64,47 | 63,77 | ídem |

Es una distribución con muchos ceros. Por eso no se resume con media y desviación típica globales (T11).

### 6. Outliers

| Columna | Nº de outliers | % | Clasificación | Decisión |
|---|---|---|---|---|
| `ventas` (serie a serie, k = 5) | 11.707 días | 0,6751 % de los días con venta | Reales: el lift es 2,320 con descuento y 1,334 en fin de semana | Se mantienen y solo se marcan (D3, T9) |

Fuentes: `outliers_sensibilidad_k.csv` y `outliers_contexto.csv`.

### 7. Correlaciones

La skill no se ejecutó (T11). La relación entre precio y ventas se trata en P3: mediana de Spearman −0,009 (`p3_correlacion_resumen.csv`; E1).

### 8. Lógica de negocio

| Comprobación | Resultado | Notas |
|---|---|---|
| La muestra concuerda con el total en días y días con venta por serie | PASS (0 series distintas) | `distribucion_adi.py`, tras C2 |
| Los totales por categoría suman el global | PASS | `muestra_vs_total.csv`: 1.440 + 570 + 1.049 = 3.059 |

---

## 9. Checklist de la skill

Fuente: `references/eda_checklist.md`. Tiene 43 puntos, aunque su título dice 40.

- C: cubierto.
- P: parcial.
- N/A: no aplica.
- S: sin cubrir.

| # | Punto | Estado | Lo cubre |
|---|---|---|---|
| 1 | Carga sin errores | C | `cargar_calendar` y `cargar_precios` (T1); los scripts de la skill funcionaron (T3) |
| 2 | Número de filas plausible | C | 1.829, 6.231.329, 30.490 series y 4.350.570 filas (fichas A-C) |
| 3 | Número de columnas igual al esquema | C | `TIPOS_CALENDAR` y `TIPOS_PRECIOS` de `carga.py` (la lectura falla si falta alguna columna) |
| 4 | Nombres de columna sin ambigüedad | C | `*_data_overview.txt` |
| 5 | Grano identificado | C | Fichas A-C; D4 |
| 6 | Clave única verificada | P | Calendar y precios, sí. La muestra (`id`, `dia_num`), no |
| 7 | Tipos correctos | C | T1 |
| 8 | Uniones sin multiplicar filas | C | N7; `unir_precio` en `outliers_series.py` |
| 9 | Nulos revisados en todas las columnas | P | Calendar y precios con `null_profiler`; en la muestra solo de forma implícita para `ventas` |
| 10 | % de nulos frente a umbrales | C | `*_null_profiler.csv` |
| 11 | Columnas con > 30 % de nulos justificadas | C | D1 |
| 12 | Ceros estructurales verificados | C | D2, C2, D7, N3 |
| 13 | Nulos esperados documentados | C | D1 |
| 14 | Filas duplicadas | P | Calendar y precios, sí; la muestra, no |
| 15 | Claves duplicadas | P | Ídem |
| 16 | Duplicados parciales (versiones) | N/A | Un precio por clave y semana; no hay versiones |
| 17 | Tasa de duplicados < 1 % | C | 0 (`sell_prices_estructura.csv`) |
| 18 | Rangos numéricos plausibles | C | Precio de 0,01 a 107,32; ventas (T1) |
| 19 | Categorías esperadas | C | 10 tiendas, 3.049 productos, 4 tipos de evento, 7 días de la semana |
| 20 | Fechas en rango | C | `tests/test_division.py` |
| 21 | Integridad referencial | C | D2: 8 series sin precio, documentadas |
| 22 | Booleanos coherentes | C | `snap_*` solo 0/1 |
| 23 | Estadísticos descriptivos | C | `*_distribution_summary.csv`, `muestra_vs_total.csv`, `adi_cuantiles.csv` |
| 24 | Asimetría > 2 anotada | P | Precio 2,217, anotado en este informe; no hay asimetría de ventas en ningún fichero |
| 25 | Outliers IQR/z revisados | C | T3 (precios), T9 y T11 (ventas serie a serie) |
| 26 | Ninguna categoría domina (> 90 %) | C | `intermitencia_resumen_global.csv` (máximo: intermitente, 72,75 %) |
| 27 | Cobertura de fechas continua | C | 1.829 fechas distintas en 1.829 días |
| 28 | Correlaciones por pares | C | `*_correlation_explorer.txt` |
| 29 | Pares fuertes explicados | C | Ficha A §7 |
| 30 | Relaciones de negocio conocidas | C | E3 (SNAP en FOODS), E1 (precio) |
| 31 | Correlaciones casi nulas investigadas | C | Precio-ventas ≈ 0, investigado en el estudio de eventos (E1) |
| 32 | Tiempo monótono o huecos documentados | C | Días contiguos (`test_conjuntos_contiguos_y_ordenados`); sin huecos de precio |
| 33 | Actualidad de los datos | N/A | Conjunto histórico cerrado; el corte es d_1829 por diseño (N1) |
| 34 | Caídas o picos de volumen | P | Tienda cerrada en Navidad (C2); no hay revisión guardada de caídas parciales de volumen diario |
| 35 | Efectos de fin de semana y festivos | C | P2, P4 |
| 36 | Relación ingresos-margen | N/A | No hay ingresos ni márgenes |
| 37 | Columnas derivadas verificadas | C | `dia_num` frente a `d` (tests); ADI y tipo recalculados desde el parquet |
| 38 | Totales por segmento cuadran | C | `muestra_vs_total.csv`; suma de `intermitencia_por_categoria.csv` = 30.490 |
| 39 | Peculiaridades conocidas documentadas | C | N7, D2, C2, D7 |
| 40 | FAIL resueltos o aceptados | C | Nulos de eventos aceptados (D1) |
| 41 | WARN anotados en el resumen | N/A | `null_profiler` no dio ningún WARN |
| 42 | Informe EDA completo | C | Este documento |
| 43 | Siguiente paso confirmado | S | Propuesto en `findings_summary_sprint1.md`; falta tu confirmación |

**Estado del EDA:** listo para continuar, con dos puntos abiertos que no bloquean: la clave y los duplicados de la muestra (puntos 6, 14 y 15) y la confirmación del siguiente paso.
