# Casos de uso del sistema

## 1. Introducción

Este documento recoge los casos de uso del sistema. Cada caso de uso describe una tarea con valor para un actor, y se traza hasta los requisitos de `requisitos.md`.

---

## 2. Actores

| Actor | Tipo | Descripción |
|-------|------|-------------|
| Analista | Principal | Persona que lanza el pipeline y consulta resultados |
| Dataset M5 | Secundario (sistema externo) | Ficheros de Kaggle de los que lee el sistema |

---

## 3. Diagrama de casos de uso

<!-- Insertar imagen exportada desde draw.io / PlantUML -->
![Diagrama de casos de uso](img/diagrama_casos_uso.png)

---

## 4. Índice de casos de uso

| ID | Nombre | RF relacionados | Prioridad | Estado |
|----|--------|-----------------|-----------|--------|
| CU-01 | Preparar los datos | RF-02, RF-03, RNF-06, RNF-07, RNF-09, RNF-12 | Must | Pendiente |
| CU-02 | Realizar análisis exploratorio | RF-01, RNF-03, RNF-06, RNF-07, RNF-12 | Must | Pendiente |

Estado: `Pendiente` · `En progreso` · `Completado` · `Descartado`
Prioridad (MoSCoW): `Must` · `Should` · `Could`

---

## 5. Relaciones entre casos de uso

| Caso de uso | Relación | Caso de uso relacionado |
|-------------|----------|-------------------------|
| CU-02 | Precondición | CU-01 |

---

## 6. Descripción de los casos de uso

### CU-01: Preparar los datos

| | |
|---|---|
| **Nombre del caso de uso** | Preparar los datos |
| **Objetivo** | Transformar los ficheros del dataset en un conjunto de datos listo para consumir por los agentes, con división temporal en entrenamiento, validación y test, y con cada serie clasificada por tipo de demanda |
| **Prioridad** | Must |
| **Precondiciones** | El analista ha descargado el dataset M5 de Kaggle |
| **Postcondiciones** | 1. Los datos procesados y la clasificación de cada serie están en `/data/processed/` <br>2. Ninguna variable generada ni la clasificación usan información posterior a su fecha de corte <br>3. Los ficheros originales del dataset M5 no se han alterado ni incluido en el repositorio |
| **Flujo de eventos** | 1. El analista ejecuta el comando de preparación de datos por consola <br>2. El sistema comprueba que los ficheros de entrada están en la ruta especificada y que la configuración es válida (alt 1, alt 2)<br>3. El sistema lee los ficheros del dataset M5 <br>4. El sistema convierte las ventas del formato ancho al largo usando tipos de datos eficientes (alt 3) <br>5. El sistema une ventas, precios y calendario en una única tabla (alt 3)<br>6. El sistema trata los precios ausentes, que corresponden a días previos a la disponibilidad del producto <br>7. El sistema divide los datos en entrenamiento, validación y test según las fechas establecidas <br>8. El sistema calcula ADI y CV² de cada serie y la clasifica según su demanda <br>9. El sistema genera las variables propias de cada agente a partir de los datos <br>10. El sistema guarda los datos procesados y la clasificación de series en `/data/processed/` (alt 4) <br>11. El sistema informa por consola de que ha terminado, con un resumen de series, filas por conjunto y fechas de corte usadas |
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