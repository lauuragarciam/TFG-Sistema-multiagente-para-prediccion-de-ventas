# Plan de análisis — Sprint 1

**Proyecto:** TFG — Sistema multiagente para la predicción de ventas (M5)
**Sprint:** 1 — Carga, división temporal y EDA
**Fecha de creación:** 2026-11-18
**Plazo:** 16 h de trabajo
**Brief:** [requisitos.md](requisitos.md) (RF-01, RF-02, RF-03, RNF-06, RNF-07, RNF-12) y [notas.md](notas.md)
**Estado:** Borrador

---

## Pregunta principal

> ¿Qué propiedades de la demanda diaria del M5 (intermitencia, eventos y SNAP, precio y estacionalidad), medidas solo con el conjunto de entrenamiento, justifican que haya cuatro agentes especializados y orientan el diseño de sus variables?

Decisión a la que sirve: qué variables construye cada agente (RF-06 a RF-09), qué contexto usa el coordinador (RF-10) y cómo se clasifican las series (RF-03).

---

## Subpreguntas y secuencia

| # | Subpregunta / tarea | Depende de | Horas est. | Estado |
|---|---|---|---|---|
| 1 | **Carga eficiente.** Leer cada CSV con tipos reducidos (`int16` para ventas, `category` para identificadores, `float32` para precios), guardar en Parquet y medir la memoria. Pasar las ventas de formato ancho a largo **por tienda** (10 bloques), sin cargar la tabla larga completa | — | 2,5 | Pendiente |
| 2 | **División temporal sin fuga.** Fechas de corte configurables; propuesta: train d_1–d_1829 (hasta 2016-01-31), validación 3×28 días d_1830–d_1913 (hasta 2016-04-24), test d_1914–d_1941 (2016-04-25 a 2016-05-22). Comprobar que los intervalos no se solapan y que el test no se lee en el EDA | 1 | 1,0 | Pendiente |
| 3 | **EDA de calendar** (una fila = un día): estructura, cobertura de fechas, nulos estructurales de eventos, días SNAP por estado | 1 | 0,75 | Pendiente |
| 4 | **EDA de sell_prices** (una fila = tienda × producto × semana): rangos, distribución de precios, cambios de precio por serie, semanas de alta de cada producto | 1 | 1,25 | Pendiente |
| 5 | **EDA de una muestra de ventas en formato largo** (una fila = serie × día), solo días de train: distribución, ceros, outliers (se detectan y documentan, no se eliminan) | 1, 2 | 1,5 | Pendiente |
| 6 | **P1 Intermitencia.** ADI y CV² de las 30.490 series en train, contando desde el primer precio; clasificación de Syntetos-Boylan-Croston y proporción por categoría y tienda | 2, 4 | 2,0 | Pendiente |
| 7 | **P2 Eventos y SNAP.** Ventas medias en días con y sin evento, por tipo de evento y en los días previos; ventas en días SNAP frente a no SNAP por estado y categoría | 2, 3 | 1,5 | Pendiente |
| 8 | **P3 Precio.** Correlación entre la variación de precio (frente al precio habitual de la serie) y la variación de ventas, por categoría; se calcula tienda a tienda | 2, 4, 5 | 2,0 | Pendiente |
| 9 | **P4 Estacionalidad.** Perfil por día de la semana y por mes; tendencia anual de la serie agregada y por categoría | 2, 3 | 1,0 | Pendiente |
| 10 | **Cierre.** Registro de supuestos completo, resumen de hallazgos y conclusiones por agente | 3–9 | 0,5 | Pendiente |

**Esfuerzo estimado:** 14,0 h
**Margen (≈14 %):** 2,0 h
**Estimación revisada:** 16,0 h, justo en el plazo

Secuencia: el paso 1 bloquea todo lo demás. Los pasos 3 y 4 son independientes entre sí, y lo mismo pasa con P2 y P4, que solo necesitan las ventas agregadas por día. P3 es el paso más incierto, así que va después de tener el perfil de precios.

**Si el plazo se queda corto** (por orden de recorte): P3 solo en una tienda por estado → P4 sin desglose por categoría → paso 5 con una muestra más pequeña. P1 no se recorta, porque RF-03 depende de él.

---

## Plan de datos

| Dato | Fuente | Disponible | Uso |
|---|---|---|---|
| Calendario (1.969 días, eventos, SNAP) | `data/raw/calendar.csv` (0,1 MB) | Sí | Pasos 2, 3, 7, 9 |
| Precios semanales | `data/raw/sell_prices.csv` (203 MB) | Sí | Pasos 4, 6, 8 |
| Ventas diarias, 30.490 series × 1.941 días | `data/raw/sales_train_evaluation.csv` (122 MB) | Sí | Pasos 1, 5–9 |

Memoria: la tabla larga completa tiene unos 59 M de filas, así que no se carga nunca entera en el EDA. Las ventas en formato ancho con `int16` ocupan unos 120 MB y bastan para P1, P2 y P4. P3 y el paso 5 trabajan por tienda o con una muestra. Objetivo: un pico de memoria inferior a 5 GB (RNF-07), que se mide en cada paso.

---

## Enfoque

Se perfila cada fichero por separado con los scripts de `programmatic-eda`, sin unir las tablas completas. Las cuatro preguntas se responden con agregados calculados solo sobre los días de entrenamiento (RF-01, RNF-12), desde el inicio de disponibilidad de cada serie. Las tablas van a `output/eda/` en CSV y las figuras, en PNG. Cada decisión se anota en el registro de supuestos (`docs/registro_supuestos.md`).

---

## Riesgos y dependencias

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Superar 8 GB al pasar a formato largo o al unir con precios | Media | +2 h | Proceso por tienda, tipos reducidos, Parquet, medición de memoria en cada paso |
| Fuga: que el EDA use días de validación o test | Media | Invalida conclusiones | Filtrar por la fecha de corte de train en el momento de la carga, con aserción |
| Ceros anteriores al alta del producto que inflan la intermitencia | Alta | P1 sesgada | Contar desde la semana del primer precio (RF-03) |
| Confundir el efecto del precio con el de eventos o la estacionalidad | Alta | P3 poco fiable | Variación relativa al precio habitual de la serie y comparación dentro de la misma serie; se presenta como asociación, no como causalidad |
| Que la muestra no represente todas las tiendas y categorías | Baja | Paso 5 sesgado | Muestreo estratificado por tienda y departamento con semilla fija |
| Scripts de la skill pensados para tablas pequeñas | Media | +1 h | Ejecutar sobre Parquet y una muestra; revisar cada script antes de lanzarlo |

---

## Hitos

| Hito | Horas acumuladas | Estado |
|---|---|---|
| Datos en Parquet y división definida | 3,5 | |
| EDA de los tres ficheros | 7,0 | |
| Cuatro preguntas respondidas | 13,5 | |
| Registro de supuestos y resumen cerrados | 14,0 (+2 de margen) | |

---

## Fuera de alcance

- Unir ventas, precios y calendario en la tabla final y generar las variables de cada agente: RF-02 completo, siguiente sprint.
- Cualquier análisis del conjunto de test, incluida la comparación de distribuciones.
- Eliminar o recortar outliers de ventas.
- Modelado o predicción.

*Ampliar el alcance obliga a revisar el plazo.*
