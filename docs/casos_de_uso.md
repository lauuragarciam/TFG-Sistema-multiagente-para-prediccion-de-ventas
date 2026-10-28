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
| CU-04 | Entrenar el modelo baseline | RF-19, RF-16, RNF-01, RNF-06, RNF-07, RNF-12 | Must | Pendiente |
| CU-05 | Generar predicciones con el sistema multiagente | RF-10, RF-11, RF-12, RF-16, RNF-02, RNF-03, RNF-06, RNF-07, RNF-08, RNF-12 | Must | Pendiente |
| CU-06 | Generar predicciones con el baseline | RF-19, RF-16, RNF-02, RNF-03, RNF-06, RNF-07, RNF-12 | Must | Pendiente |
| CU-07 | Consultar predicciones | RF-13, RNF-02, RNF-03 | Should | Pendiente |
| CU-08 | Consultar predicciones de los agentes | RF-14, RNF-03, RNF-08 | Should | Pendiente |

Estado: `Pendiente` · `En progreso` · `Completado` · `Descartado`
Prioridad (MoSCoW): `Must` · `Should` · `Could`

---

## 4. Relaciones entre casos de uso

| Caso de uso | Relación | Caso de uso relacionado |
|-------------|----------|-------------------------|
| CU-02 | Precondición | CU-01 |
| CU-03 | Precondición | CU-01 |
| CU-04 | Precondición | CU-01 |
| CU-05 | Precondición | CU-03 |
| CU-06 | Precondición | CU-04 |
| CU-07 | Precondición | CU-05 (consulta del sistema multiagente) |
| CU-07 | Precondición | CU-06 (consulta del baseline) |
| CU-08 | Precondición | CU-05 |
| CU-08 | `«extend»` | CU-07 |



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
| **Flujo de eventos** | 1. El analista ejecuta el comando de preparación de datos por consola <br>2. El sistema comprueba que los ficheros de entrada están en la ruta especificada y que la configuración es válida (alt 1, alt 2)<br>3. El sistema lee los ficheros del dataset M5 <br>4. El sistema convierte las ventas del formato ancho al largo usando tipos de datos eficientes (alt 3) <br>5. El sistema une ventas, precios y calendario en una única tabla (alt 3)<br>6. El sistema excluye de la tabla los días sin precio, que corresponden a días previos a la disponibilidad del producto <br>7. El sistema divide los datos en entrenamiento, validación y test según las fechas de corte configuradas <br>8. El sistema calcula ADI y CV² de cada serie y la clasifica según el criterio establecido <br>9. El sistema genera las variables propias de cada agente a partir de los datos <br>10. El sistema guarda los datos procesados y la clasificación de series en `/data/processed/` (alt 4) <br>11. El sistema informa por consola de que ha terminado, con un resumen de series, filas por conjunto y fechas de corte usadas |
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
| **Flujo de eventos** | 1. El analista ejecuta el comando de entrenamiento por consola (alt 4) <br>2. El sistema carga los conjuntos de entrenamiento y validación y la clasificación de series (alt 3) <br>3. El sistema entrena cada agente especializado (temporal, precios, eventos y demanda intermitente) con el conjunto de entrenamiento y las variables propias de cada uno (alt 2, alt 3) <br>4. El sistema genera las predicciones de cada agente sobre el conjunto de validación (alt 2) <br>5. El sistema construye el contexto de cada predicción de validación <br>6. El sistema entrena el agente coordinador con las predicciones de los agentes, el contexto y las ventas reales de validación (alt 3) <br>7. El sistema guarda los modelos entrenados (alt 1) <br>8. El sistema informa por consola de que ha terminado, con un resumen de los agentes entrenados y su error sobre el conjunto de validación |
| **Flujos alternativos** | 1) Ya existen modelos guardados de una ejecución anterior -> el sistema los sobrescribe <br>2) Falla un agente o no está disponible, ya sea al entrenarse o al generar sus predicciones de validación -> el sistema indica por consola qué agente es y el motivo, lo excluye y continúa con los agentes disponibles. Si quedan menos de dos agentes disponibles, muestra un mensaje indicándolo y termina sin entrenar el coordinador <br>3) La memoria es insuficiente -> el sistema procesa los datos por bloques. Si aun así no es posible, muestra un mensaje indicando que se requiere más memoria y termina <br>4) El analista indica un único agente en el comando -> el sistema entrena y guarda solo ese agente (pasos 2, 3 y 7), sin reentrenar los demás agentes ni el coordinador. Para que el coordinador tenga en cuenta el agente actualizado, hay que volver a entrenarlo |
| **Requisitos no funcionales** | RNF-01 (Evaluación de la precisión): el ajuste de hiperparámetros usa solo entrenamiento y validación, y el conjunto de test no interviene <br>RNF-06 (Reproducibilidad): con la misma configuración y datos, los modelos obtenidos son idénticos <br>RNF-07 (Eficiencia): el pico de memoria no supera los 5 GB en el equipo local <br>RNF-08 (Tolerancia a fallos): si un agente falla, el sistema continúa con los restantes y lo indica por consola <br>RNF-12 (Ausencia de fuga de información): ni los agentes ni el coordinador utilizan datos posteriores a la fecha de predicción |
| **Notas** | El caso de uso es independiente del entorno de ejecución (local o nube) aunque, ya que es el más costoso del sistema, es el más probable de ejecutarse en la nube (RNF-07) |


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

---

### CU-05: Generar predicciones con el sistema multiagente

| | |
|---|---|
| **Nombre del caso de uso** | Generar predicciones con el sistema multiagente |
| **Objetivo** | Generar las predicciones de ventas diarias por producto y tienda sobre el conjunto de test, combinando las predicciones de los agentes especializados según el contexto |
| **Prioridad** | Must |
| **Precondiciones** | CU-01 y CU-03 ejecutados correctamente: los datos procesados están en `/data/processed/` y los modelos del sistema multiagente están guardados |
| **Postcondiciones** | 1. Las predicciones de todos los productos y tiendas del conjunto de test están en `/output/`, con una fila por producto, tienda y día <br>2. Las predicciones parciales de cada agente y los pesos asignados por el coordinador están guardados <br>3. Ninguna predicción utiliza información posterior a su fecha de predicción <br>4. Los datos procesados y los modelos no se han modificado |
| **Flujo de eventos** | 1. El analista ejecuta el comando de predicción del sistema multiagente por consola <br>2. El sistema carga los modelos del sistema multiagente y los datos del conjunto de test (alt 3) <br>3. Cada agente especializado genera su predicción parcial para cada serie y fecha (alt 1, alt 3) <br>4. El coordinador analiza el contexto de cada predicción y asigna un peso a cada agente (alt 1) <br>5. El coordinador combina las predicciones parciales ponderadas en la predicción final <br>6. El sistema guarda en `/output/` las predicciones finales, las predicciones parciales de cada agente y los pesos asignados (alt 2) <br>7. El sistema informa por consola de que ha terminado e indica la ruta de los resultados |
| **Flujos alternativos** | 1) Un agente no puede producir predicción para una serie -> el coordinador renormaliza los pesos entre los agentes restantes, el sistema indica por consola qué agente ha fallado y la ejecución continúa <br>2) Ya existen predicciones del sistema multiagente de una ejecución anterior -> el sistema las sobrescribe <br>3) La memoria es insuficiente -> el sistema procesa los datos por bloques. Si aun así no es posible, muestra un mensaje indicando que se requiere más memoria y termina |
| **Requisitos no funcionales** | RNF-02 (Rendimiento): se minimiza el tiempo de predicción <br>RNF-03 (Usabilidad): los CSV tienen columnas con nombres claros y los mensajes por consola son comprensibles <br>RNF-06 (Reproducibilidad): con la misma configuración, modelos y datos, las predicciones son idénticas <br>RNF-07 (Eficiencia): el pico de memoria no supera los 5 GB y la predicción se puede ejecutar en el equipo local <br>RNF-08 (Tolerancia a fallos): si un agente no puede predecir una serie, el coordinador renormaliza los pesos y lo indica por consola <br>RNF-12 (Ausencia de fuga de información): ninguna predicción utiliza datos posteriores a la fecha de predicción |
| **Notas** | Si en el entrenamiento se excluyó algún agente, el sistema predice solo con los agentes con los que se entrenó el coordinador |


---


### CU-06: Generar predicciones con el baseline

| | |
|---|---|
| **Nombre del caso de uso** | Generar predicciones con el baseline |
| **Objetivo** | Generar con el modelo baseline las predicciones de ventas diarias por producto y tienda sobre el conjunto de test, con el mismo formato y horizonte que las del sistema multiagente |
| **Prioridad** | Must |
| **Precondiciones** | CU-01 y CU-04 ejecutados correctamente: los datos procesados están en `/data/processed/` y el modelo baseline está guardado |
| **Postcondiciones** | 1. Las predicciones de todos los productos y tiendas del conjunto de test están en `/output/`, con una fila por producto, tienda y día, diferenciadas de las del sistema multiagente <br>2. Ninguna predicción utiliza información posterior a su fecha de predicción <br>3. Los datos procesados y el modelo no se han modificado |
| **Flujo de eventos** | 1. El analista ejecuta el comando de predicción del baseline por consola <br>2. El sistema carga el modelo baseline y los datos del conjunto de test (alt 2) <br>3. El modelo genera la predicción para cada serie y fecha (alt 2) <br>4. El sistema guarda las predicciones en `/output/` (alt 1) <br>5. El sistema informa por consola de que ha terminado e indica la ruta de los resultados |
| **Flujos alternativos** | 1) Ya existen predicciones del baseline de una ejecución anterior -> el sistema las sobrescribe, sin afectar a las del sistema multiagente <br>2) La memoria es insuficiente -> el sistema procesa los datos por bloques. Si aun así no es posible, muestra un mensaje indicando que se requiere más memoria y termina |
| **Requisitos no funcionales** | RNF-02 (Rendimiento): se minimiza el tiempo de predicción <br>RNF-03 (Usabilidad): los CSV tienen columnas con nombres claros y los mensajes por consola son comprensibles <br>RNF-06 (Reproducibilidad): con la misma configuración, modelo y datos, las predicciones son idénticas <br>RNF-07 (Eficiencia): el pico de memoria no supera los 5 GB y la predicción se puede ejecutar en el equipo local <br>RNF-12 (Ausencia de fuga de información): ninguna predicción utiliza datos posteriores a la fecha de predicción |
| **Notas** | El caso de uso es independiente de CU-05, el baseline no depende de los agentes ni del coordinador |


---


### CU-07: Consultar predicciones

| | |
|---|---|
| **Nombre del caso de uso** | Consultar predicciones |
| **Objetivo** | Mostrar por consola las predicciones del modelo que indique el analista (sistema multiagente o baseline) para una serie concreta, para un subconjunto de series filtrado por producto, tienda, categoría, departamento o estado, o para todas las series, en la fecha o el intervalo de fechas indicado, a partir de las predicciones ya almacenadas |
| **Prioridad** | Should |
| **Precondiciones** | Se han generado las predicciones del modelo que se quiere consultar: CU-05 para el sistema multiagente o CU-06 para el baseline |
| **Postcondiciones** | 1. Las predicciones solicitadas se han mostrado por consola o, si superan el límite de filas, se han guardado completas en `/output/consultas/` <br>2. Los ficheros de predicciones de `/output/` no se han modificado |
| **Flujo de eventos** | 1. El analista ejecuta el comando de consulta por consola, indicando el modelo, la fecha o el intervalo de fechas y, opcionalmente, filtros por producto, tienda, categoría, departamento o estado; si no indica filtros, se consultan todas las series (alt 1) <br>2. El sistema comprueba que los parámetros son correctos y que las fechas están dentro del horizonte disponible (alt 1, alt 3) <br>3. El sistema lee de `/output/` las predicciones almacenadas del modelo indicado y selecciona las que cumplen los filtros y las fechas (alt 2) <br>4. El sistema muestra por consola las predicciones seleccionadas (alt 4) |
| **Flujos alternativos** | 1) Falta algún parámetro obligatorio o tiene un formato incorrecto -> el sistema muestra un mensaje de uso con los parámetros esperados y termina <br>2) Ningún dato cumple los filtros (un valor inexistente o una combinación sin series) -> el sistema muestra un mensaje indicándolo y termina <br>3) Alguna fecha está fuera del horizonte disponible -> el sistema muestra un mensaje con el rango de fechas disponible y termina <br>4) El resultado supera el límite de filas configurado para la consola -> el sistema muestra el número total de filas y las primeras, y guarda el resultado completo en un CSV en `/output/consultas/`, indicando su ruta |
| **Requisitos no funcionales** | RNF-02 (Rendimiento): la consulta se resuelve sobre las predicciones almacenadas, sin volver a predecir <br>RNF-03 (Usabilidad): los mensajes por consola son comprensibles y los CSV generados tienen columnas con nombres claros |
| **Notas** | Devuelve filas individuales, no agregados: sumar las predicciones por categoría o tienda sería otra funcionalidad |


---


### CU-08: Consultar predicciones de los agentes

| | |
|---|---|
| **Nombre del caso de uso** | Consultar predicciones de los agentes |
| **Objetivo** | Ampliar la consulta de predicciones del sistema multiagente (CU-07) mostrando, además de la predicción final, la predicción de cada agente especializado y el peso que le asignó el coordinador, para entender cómo se ha construido la predicción final |
| **Prioridad** | Should |
| **Precondiciones** | CU-05 ejecutado correctamente: las predicciones parciales de los agentes y los pesos están guardados en `/output/` |
| **Postcondiciones** | 1. Para cada serie y fecha consultada se muestran, además de la predicción final, la predicción de cada agente y su peso, por consola o en el CSV de la consulta <br>2. Los ficheros de `/output/` con las predicciones y los pesos no se han modificado |
| **Flujo de eventos** | 1. En una consulta de CU-07 sobre el sistema multiagente, el analista solicita el detalle de los agentes (alt 1) <br>2. El sistema lee de `/output/` las predicciones parciales y los pesos de las series y fechas seleccionadas <br>3. El sistema añade a cada predicción mostrada la de cada agente y su peso (alt 2) |
| **Flujos alternativos** | 1) El analista solicita el detalle con el modelo baseline -> el sistema indica que el baseline no tiene agentes ni pesos y muestra solo la predicción de CU-07 <br>2) Algún agente no produjo predicción para una serie y fecha -> el sistema lo indica en la salida junto con los pesos renormalizados entre los agentes restantes |
| **Requisitos no funcionales** | RNF-03 (Usabilidad): los mensajes por consola son comprensibles y los CSV tienen columnas con nombres claros <br>RNF-08 (Tolerancia a fallos): si un agente no produjo predicción, la salida lo refleja con los pesos renormalizados |
| **Notas** | Los filtros, el límite de filas y el volcado a CSV son los de CU-07. Devuelve filas individuales, no pesos medios: el análisis agregado del protagonismo de los agentes corresponde a RF-24 |


---


### CU-09: Visualizar predicciones frente a ventas reales

| | |
|---|---|
| **Nombre del caso de uso** | Visualizar predicciones frente a ventas reales |
| **Objetivo** | Generar una gráfica que compare, para cada fecha del conjunto de test, las ventas reales con las predicciones de uno o ambos modelos, para una serie concreta o para un subconjunto de series filtrado por producto, tienda, categoría, departamento o estado |
| **Prioridad** | Could |
| **Precondiciones** | CU-01 ejecutado correctamente y se han generado las predicciones de cada modelo que se quiere visualizar: CU-05 para el sistema multiagente o CU-06 para el baseline |
| **Postcondiciones** | 1. La gráfica en formato PNG está en `/output/graficas/` <br>2. Los ficheros de predicciones y los datos procesados no se han modificado |
| **Flujo de eventos** | 1. El analista ejecuta el comando de visualización por consola, indicando el modelo o los modelos, el intervalo de fechas y la serie o los filtros por producto, tienda, categoría, departamento o estado (alt 1) <br>2. El sistema comprueba que los parámetros son correctos y que las fechas están dentro del horizonte disponible (alt 1, alt 3) <br>3. El sistema lee las predicciones almacenadas de los modelos indicados y las ventas reales del conjunto de test, y selecciona las que cumplen los filtros y las fechas (alt 2) <br>4. El sistema genera la gráfica que compara, para cada fecha, las ventas reales con las predicciones de cada modelo; si la selección comprende varias series, representa la suma de todas ellas <br>5. El sistema guarda la gráfica en `/output/graficas/` (alt 4) <br>6. El sistema informa por consola de que ha terminado e indica la ruta de la gráfica |
| **Flujos alternativos** | 1) Falta algún parámetro obligatorio o tiene un formato incorrecto -> el sistema muestra un mensaje de uso con los parámetros esperados y termina <br>2) Ningún dato cumple los filtros (un valor inexistente o una combinación sin series) -> el sistema muestra un mensaje indicándolo y termina <br>3) Alguna fecha está fuera del horizonte disponible -> el sistema muestra un mensaje con el rango de fechas disponible y termina <br>4) Ya existe una gráfica con el mismo nombre de una ejecución anterior -> el sistema la sobrescribe |
| **Requisitos no funcionales** | RNF-03 (Usabilidad): los mensajes por consola son comprensibles y la gráfica indica claramente la selección, los modelos y las fechas <br>RNF-06 (Reproducibilidad): con las mismas predicciones y parámetros, la gráfica es idéntica |
| **Notas** | |