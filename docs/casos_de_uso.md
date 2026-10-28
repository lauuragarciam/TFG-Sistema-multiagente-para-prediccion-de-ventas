# Casos de uso del sistema

## 1. Introducción

Este documento recoge los casos de uso del sistema. Cada caso de uso describe una tarea con valor para un actor, y se traza hasta los requisitos de `requisitos.md`.

---

## 2. Diagrama de casos de uso

<!-- Insertar imagen exportada desde draw.io / PlantUML -->
![Diagrama de casos de uso](img/diagrama_casos_uso.png)

---

## 3. Índice de casos de uso

| ID | Nombre | RF relacionados | Prioridad | Estado |
|----|--------|-----------------|-----------|--------|
| CU-01 | Preparar los datos | RF-02, RF-03, RNF-06, RNF-07, RNF-09, RNF-12 | Must | Pendiente |
| CU-02 | Realizar análisis exploratorio | RF-01, RNF-03, RNF-06, RNF-07, RNF-12 | Must | Pendiente |
| CU-03 | Entrenar el sistema multiagente | RF-04, RF-05, RF-16, RF-27, RNF-01, RNF-06, RNF-07, RNF-08, RNF-12 | Must | Pendiente |

Estado: `Pendiente` · `En progreso` · `Completado` · `Descartado`
Prioridad (MoSCoW): `Must` · `Should` · `Could`

---

## 4. Relaciones entre casos de uso

| Caso de uso | Relación | Caso de uso relacionado |
|-------------|----------|-------------------------|
| CU-02 | Precondición | CU-01 |
| CU-03 | Precondición | CU-01 |


---

## 5. Descripción de los casos de uso

### CU-01: Preparar los datos

| | |
|---|---|
| **Nombre del caso de uso** | Preparar los datos |
| **Objetivo** | Transformar los ficheros del dataset en un conjunto de datos listo para consumir por los agentes, con división temporal en entrenamiento, validación y test, y con cada serie clasificada por tipo de demanda |
| **Prioridad** | Must |
| **Precondiciones** | El analista ha descargado el dataset M5 de Kaggle |
| **Postcondiciones** | 1. Los datos procesados y la clasificación de cada serie están en `/data/processed/` <br>2. Ninguna variable generada ni la clasificación usan información posterior a su fecha de corte <br>3. Los ficheros originales del dataset M5 no se han alterado ni incluido en el repositorio |
| **Flujo de eventos** | 1. El analista ejecuta el comando de preparación de datos por consola <br>2. El sistema comprueba que los ficheros de entrada están en la ruta especificada y que la configuración es válida (alt 1, alt 2)<br>3. El sistema lee los ficheros del dataset M5 <br>4. El sistema convierte las ventas del formato ancho al largo usando tipos de datos eficientes (alt 3) <br>5. El sistema une ventas, precios y calendario en una única tabla (alt 3)<br>6. El sistema excluye de la tabla los días sin precio, que corresponden a días previos a la disponibilidad del producto <br>7. El sistema divide los datos en entrenamiento, validación y test según las fechas establecidas en la documentación <br>8. El sistema calcula ADI y CV² de cada serie y la clasifica según su demanda <br>9. El sistema genera las variables propias de cada agente a partir de los datos <br>10. El sistema guarda los datos procesados y la clasificación de series en `/data/processed/` (alt 4) <br>11. El sistema informa por consola de que ha terminado, con un resumen de series, filas por conjunto y fechas de corte usadas |
| **Flujos alternativos** | 1) Faltan ficheros de entrada -> el sistema muestra un mensaje de error que indica qué ficheros faltan y dónde esperaba encontrarlos, y termina sin generar resultados <br>2) La configuración no es válida (fechas de corte solapadas, fuera del rango del dataset o con un conjunto vacío) -> el sistema muestra un mensaje de error con el motivo específico y termina <br>3) La memoria es insuficiente -> el sistema procesa los datos por bloques. Si aun así no es posible, muestra un mensaje indicando que se requiere más memoria y termina <br>4) Ya existen datos procesados de una ejecución anterior -> el sistema los sobrescribe |
| **Requisitos no funcionales** | RNF-06 (Reproducibilidad): con la misma configuración y datos, el resultado es idéntico <br>RNF-07 (Eficiencia): el pico de memoria no supera los 5 GB en el equipo local <br>RNF-09 (Legalidad): el dataset se usa solo con fines académicos y no se redistribuye <br>RNF-12 (Ausencia de fuga de información): ningún dato posterior a la fecha de predicción se usa en el entrenamiento ni en la clasificación |
| **Notas** | El caso de uso es independiente del entorno de ejecución (local o nube) |

---

### CU-02: Realizar análisis exploratorio

| | |
|---|---|
| **Nombre del caso de uso** | Realizar análisis exploratorio |
| **Objetivo** | Generar automáticamente tablas resumen y figuras que muestren los patrones de ventas, la demanda intermitente y la relación entre precios, ventas y calendario en el conjunto de entrenamiento |
| **Prioridad** | Must |
| **Precondiciones** | CU-01 ejecutado correctamente, los datos procesados y la clasificación de series están en `/data/processed/` |
| **Postcondiciones** | 1. Las tablas CSV y las figuras PNG del análisis están en `/output/eda/` <br>2. Los datos procesados no se han modificado <br>3. Los resultados se han calculado únicamente con el conjunto de entrenamiento |
| **Flujo de eventos** | 1. El analista ejecuta el comando de análisis exploratorio por consola <br>2. El sistema carga los datos procesados (alt 1) <br>3. El sistema calcula estadísticos de ventas por categoría, departamento y tienda (alt 1) <br>4. El sistema resume la clasificación de series por tipo de demanda <br>5. El sistema calcula la correlación entre variación de precio y ventas <br>6. El sistema calcula las ventas medias por día de la semana, por evento y por día SNAP <br>7. El sistema guarda las tablas en CSV y las figuras en PNG en `/output/eda/` (alt 2) <br>8. El sistema indica por consola de que ha terminado y la ruta donde se encuentran los resultados |
| **Flujos alternativos** | 1) La memoria es insuficiente -> el sistema procesa los datos por bloques. Si aun así no es posible, muestra un mensaje indicando que se requiere más memoria y termina <br>2) Ya existen resultados de una ejecución anterior -> el sistema los sobrescribe |
| **Requisitos no funcionales** | RNF-03 (Usabilidad): los CSV tienen columnas con nombres claros y los mensajes por consola son comprensibles <br>RNF-06 (Reproducibilidad): con los mismos datos, el resultado es idéntico <br>RNF-07 (Eficiencia): el pico de memoria no supera los 5 GB en el equipo local <br>RNF-12 (Ausencia de fuga de información): el análisis no usa datos de validación ni de test, de modo que no influye en decisiones de diseño con información futura |
| **Notas** | El caso de uso es independiente del entorno de ejecución (local o nube) |

---

### CU-03: Entrenar el sistema multiagente

| | |
|---|---|
| **Nombre del caso de uso** | Entrenar el sistema multiagente |
| **Objetivo** | Entrenar los agentes especializados con los datos de entrenamiento y, a continuación, entrenar el agente coordinador con las predicciones de esos agentes sobre el conjunto de validación, de modo que el sistema quede listo para predecir |
| **Prioridad** | Must |
| **Precondiciones** | CU-01 ejecutado correctamente, los datos procesados y la clasificación de series están en `/data/processed/` |
| **Postcondiciones** | 1. Los modelos de los agentes especializados y del agente coordinador están guardados <br>2. Los agentes se han entrenado solo con el conjunto de entrenamiento y el coordinador solo con las predicciones de los agentes sobre el conjunto de validación <br>3. No se ha utilizado el conjunto de test <br>4. Los datos procesados no se han modificado |
| **Flujo de eventos** | 1. El analista ejecuta el comando de entrenamiento por consola (alt 4) <br>2. El sistema carga los conjuntos de entrenamiento y validación y la clasificación de series (alt 3) <br>3. El sistema entrena cada agente especializado (temporal, precios, eventos y demanda intermitente) con el conjunto de entrenamiento y las variables propias de cada uno (alt 2, alt 3) <br>4. El sistema genera las predicciones de cada agente sobre el conjunto de validación (alt 2) <br>5. El sistema construye el contexto de cada predicción de validación <br>6. El sistema entrena el agente coordinador con las predicciones de los agentes, el contexto y las ventas reales de validación (alt 3) <br>7. El sistema guarda los modelos entrenados (alt 1) <br>8. El sistema informa por consola que ha terminado, con un resumen de los agentes entrenados y su error sobre el conjunto de validación |
| **Flujos alternativos** | 1) Ya existen modelos guardados de una ejecución anterior -> el sistema los sobrescribe <br>2) Falla un agente o no está disponible, ya sea al entrenarse o al generar sus predicciones de validación -> el sistema indica por consola qué agente es y el motivo, lo excluye y continúa con los agentes disponibles. Si quedan menos de dos agentes disponibles, muestra un mensaje indicándolo y termina sin entrenar el coordinador <br>3) La memoria es insuficiente -> el sistema procesa los datos por bloques. Si aun así no es posible, muestra un mensaje indicando que se requiere más memoria y termina <br>4) El analista indica un único agente en el comando -> el sistema entrena y guarda solo ese agente (pasos 2, 3 y 7), sin reentrenar los demás agentes ni el coordinador. Para que el coordinador tenga en cuenta el agente actualizado, hay que volver a entrenarlo |
| **Requisitos no funcionales** | RNF-01 (Evaluación de la precisión): el ajuste de hiperparámetros usa solo entrenamiento y validación, y el conjunto de test no interviene <br>RNF-06 (Reproducibilidad): con la misma configuración y datos, los modelos obtenidos son idénticos <br>RNF-07 (Eficiencia): el pico de memoria no supera los 5 GB en el equipo local <br>RNF-08 (Tolerancia a fallos): si un agente falla, el sistema continúa con los restantes y lo indica por consola <br>RNF-12 (Ausencia de fuga de información): ni los agentes ni el coordinador utilizan datos posteriores a la fecha de predicción |
| **Notas** | El caso de uso es independiente del entorno de ejecución (local o nube) aunque, ya que es el más costoso del sistema, es el mas probable de ejecutarse en la nube (RNF-07) |


---

### CU-04: Entrenar el modelo baseline

| | |
|---|---|
| **Nombre del caso de uso** | Entrenar el modelo baseline |
| **Objetivo** | Entrenar un único modelo global alimentado con todas las variables a la vez, con los mismos datos de entrenamiento y la misma división temporal que el sistema multiagente, para disponer de un modelo de referencia con el que compararlo |
| **Prioridad** | Must |
| **Precondiciones** | CU-01 ejecutado correctamente: los datos procesados y la clasificación de series están en `/data/processed/` |
| **Postcondiciones** | 1. El modelo baseline entrenado está guardado <br>2. El modelo se ha entrenado con el mismo conjunto de entrenamiento y la misma división temporal que el sistema multiagente <br>3. No se ha utilizado el conjunto de test <br>4. Los datos procesados no se han modificado |
| **Flujo de eventos** | 1. El analista ejecuta el comando de entrenamiento del baseline por consola <br>2. El sistema carga el conjunto de entrenamiento (alt 2) <br>3. El sistema entrena un único modelo global con todas las variables a la vez (alt 2, alt 3) <br>4. El sistema guarda el modelo entrenado (alt 1) <br>5. El sistema informa por consola de que ha terminado, con un resumen del entrenamiento |
| **Flujos alternativos** | 1) Ya existe un modelo baseline guardado de una ejecución anterior -> el sistema lo sobrescribe <br>2) La memoria es insuficiente -> el sistema procesa los datos por bloques. Si aun así no es posible, muestra un mensaje indicando que se requiere más memoria y termina <br>3) Falla el entrenamiento -> el sistema muestra un mensaje de error con el motivo y termina sin guardar ningún modelo |
| **Requisitos no funcionales** | RNF-01 (Evaluación de la precisión): el conjunto de test no interviene en el ajuste del modelo <br>RNF-06 (Reproducibilidad): con la misma configuración y datos, el modelo obtenido es idéntico <br>RNF-07 (Eficiencia): el pico de memoria no supera los 5 GB en el equipo local <br>RNF-12 (Ausencia de fuga de información): el baseline no utiliza datos posteriores a la fecha de predicción |
| **Notas** | El caso de uso es independiente del entorno de ejecución (local o nube) y de CU-03 ya que el baseline no depende de los agentes ni del coordinador |