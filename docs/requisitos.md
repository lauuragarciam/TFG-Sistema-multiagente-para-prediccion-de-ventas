# Requisitos del sistema

## 1. Introducción

### 1.1 Propósito de este documento

Este documento recoge los requisitos funcionales y no funcionales del sistema. Su objetivo es definir con claridad qué debe hacer el sistema y bajo qué condiciones de calidad, delimitar su alcance y servir de referencia durante todo el desarrollo.

Cada requisito tiene un identificador único, una prioridad y un estado, de modo que pueda trazarse hasta las tareas de planificación, el código que lo implementa y las pruebas que lo verifican.


### 1.2 Alcance del sistema

El sistema desarrollado es un sistema multiagente que predice la demanda de productos en el sector retail a partir de datos históricos de ventas de Walmart. Está compuesto por agentes especializados, cada uno centrado en un factor determinante de la demanda (temporal, precios, eventos y demanda intermitente), y por un agente coordinador que combina sus predicciones parciales en una predicción final según el contexto específico.

**El sistema incluye:**

- El análisis exploratorio automatizado del dataset y la preparación de los datos para el entrenamiento de los agentes.
- El entrenamiento de los agentes especializados y del agente coordinador.
- La predicción de ventas diarias por producto y tienda, dentro de un intervalo de tiempo determinado.
- La evaluación del sistema frente a un modelo baseline, con el fin de valorar si el enfoque multiagente aporta mejoras.

**El sistema no incluye:**

- Reentrenamiento en línea ni actualización automática con datos nuevos.
- Uso de fuentes de datos distintas del dataset M5 de Walmart.

**Datos utilizados:** dataset M5 Forecasting (Walmart), con ventas diarias por producto y tienda, precios y calendario de eventos.

### 1.3 Definiciones y abreviaturas

| Término | Definición |
|---------|------------|
| RF | Requisito funcional |
| RNF | Requisito no funcional |
| M5 | Dataset de la competición *M5 Forecasting* (Walmart, Kaggle) |
| SNAP | *Supplemental Nutrition Assistance Program*: indicador del calendario M5 que señala los días en que se permite el uso de estos cupones en cada estado |
| Baseline | Modelo de referencia con el que se compara el sistema multiagente |
| Serie | Secuencia temporal de ventas diarias de un producto en una tienda |
| Demanda intermitente | Demanda con largos periodos sin ventas intercalados con picos irregulares |
| ADI | *Average Demand Interval*: intervalo medio entre demandas no nulas |
| CV² | Cuadrado del coeficiente de variación de las demandas no nulas; junto con ADI sirve para clasificar series (suave, errática, intermitente, irregular) |
| RMSE / MAE | Error cuadrático medio (raíz) / error absoluto medio |
| Fuga de información | Uso, durante el entrenamiento o la predicción, de información que no estaría disponible en el momento real de predecir |

---

## 2. Convenciones

### 2.1 Identificadores

- Requisitos funcionales: `RF-01`, `RF-02`, ...
- Requisitos no funcionales: `RNF-01`, `RNF-02`, ...
- Los IDs son **estables**: si un requisito se elimina, su ID no se reutiliza (se marca como *Descartado*).

### 2.2 Prioridad (MoSCoW)

| Valor | Significado |
|-------|-------------|
| **Must** | Imprescindible |
| **Should** | Importante, pero el sistema funciona sin él |
| **Could** | Deseable si sobra tiempo |
| **Won't** | Fuera de alcance en esta versión |

### 2.3 Estado

`Pendiente` · `En progreso` · `Completado` · `Descartado`

---

## 3. Requisitos funcionales

| ID | Requisito | Descripción | Prioridad | Estado | Dependencia |
|------|-----------|-----------|--------|--------|--------|
| RF-01 | Análisis exploratorio automatizado | El sistema generará, a partir de los ficheros del dataset, tablas resumen en formato CSV en `/output/eda/` y las figuras asociadas en formato PNG. Las tablas incluirán estadísticos de ventas por categoría, departamento y tienda, porcentaje de ceros por serie, clasificación de series según tipo de demanda, correlación entre variación de precio y ventas, ventas medias por día de la semana, ventas medias por evento y por día SNAP | Must | Pendiente | RF-03 |
| RF-02 | Preparación de datos | El sistema transformará los datos del M5 para su consumo por los agentes: conversión del formato ancho a largo, reducción del uso de memoria mediante tipos de datos eficientes, unión de ventas, precios y calendario en una única tabla, tratamiento de los valores ausentes (en particular los precios nulos de los días en que un producto aún no se vendía) con un criterio documentado, y generación de las variables propias de cada agente a partir de los datos. Además, se dividirán los datos de forma temporal en entrenamiento, validación y test (test = últimos 28 días; validación = los 28 anteriores; entrenamiento = el resto), con fechas de corte configurables. El resultado se almacenará en `/data/processed/` | Must | Pendiente | |
| RF-03 | Clasificación de series por tipo de demanda | El sistema clasificará cada serie como suave, errática, intermitente o irregular a partir de ADI y CV², calculados únicamente con los datos del conjunto de entrenamiento, y guardará la clasificación en `/data/processed/` para su uso por el agente intermitente, el coordinador y la evaluación por segmentos | Must | Pendiente | RF-02 |
| RF-04 | Entrenamiento de agentes | Los agentes aprenderán basándose en los datos de entrenamiento preparados específicamente para cada uno | Must | Pendiente | RF-02, RF-03 |
| RF-05 | Entrenamiento del agente coordinador | El agente coordinador aprenderá a asignar pesos a las predicciones de los agentes especializados según el contexto. Se entrenará con las predicciones de los agentes sobre el conjunto de validación para no verse sesgado | Must | Pendiente | RF-06, RF-07, RF-08, RF-09 |
| RF-06 | Predecir según temporalidad | Un agente especializado predecirá la cantidad de producto vendido en cada tienda basándose en las ventas previas, empleando su histórico reciente para capturar tendencias y patrones de estacionalidad  | Must | Pendiente | RF-04 |
| RF-07 | Predecir según precios | Un agente especializado analizará las modificaciones de precio, tales como descuentos o promociones, para estimar su efecto sobre el volumen de ventas, aportando una predicción sensible a estos cambios | Must | Pendiente | RF-04 |
| RF-08 | Predecir según eventos | Un agente especializado detectará si hay eventos especiales, festivos o fechas señaladas que puedan afectar a las ventas, generando una predicción que anticipe posibles picos de demanda asociados a estos factores | Must | Pendiente | RF-04 |
| RF-09 | Predecir según demanda intermitente | Un agente especializado realizará una predicción teniendo en cuenta si se trata de un artículo de venta intermitente  | Must | Pendiente | RF-03, RF-04 |
| RF-10 | Combinar predicciones | El agente coordinador analizará el contexto de cada predicción y, según este, combinará las predicciones parciales de los agentes especializados para obtener la predicción final | Must | Pendiente | RF-06, RF-07, RF-08, RF-09 |
| RF-11 | Exportación de pesos del coordinador | El sistema guardaría, para cada predicción, las predicciones parciales de cada agente y los pesos asignados por el coordinador en `/output/` | Should | Pendiente | RF-10 |
| RF-12 | Devolver predicciones | El sistema guardará en `/output/` las predicciones de todos los productos y tiendas del conjunto de test para un horizonte de 28 días, con una fila por producto, tienda y día | Must | Pendiente | RF-10 |
| RF-13 | Consultar predicción | El sistema devolvería por consola la predicción individual de un producto en una tienda y fecha o intervalo especificados (dentro de los disponibles), consultando las predicciones ya almacenadas en `/output/` | Should | Pendiente | RF-12 |
| RF-14 | Consultar predicciones de los agentes | El sistema devolvería por consola las predicciones de cada agente especializado y sus pesos para una serie y fecha, consultando los ficheros de `/output/` | Should | Pendiente | RF-11, RF-12 |
| RF-15 | Visualización de predicciones frente a ventas reales | El sistema devolvería una gráfica donde se mostraría la diferencia entre las predicciones y las ventas reales, la cual se almacenaría en `/output/` | Could | Pendiente | RF-12 |
| RF-16 | Guardar y cargar modelos entrenados | Se almacenarían los modelos entrenados, de modo que cada agente podría guardarse individualmente, además del sistema al completo  | Should | Pendiente | RF-04, RF-05 |
| RF-17 | Interfaz | El sistema ofrecería una interfaz (por consola o gráfica) desde la que realizar las consultas de RF-13, RF-14, RF-15 y RF-18 | Could | Pendiente | RF-12 |
| RF-18 | Cálculo de stock de seguridad | El sistema calcularía el stock de seguridad de un producto y tienda a partir de la predicción y de costes y plazos ficticios o introducidos por consola, ya que el dataset no los contiene. Su finalidad sería ilustrar la utilidad de la predicción, no realizar una gestión real de inventario | Could | Pendiente | RF-12 |
| RF-19 | Entrenamiento del modelo baseline | El sistema entrenará un modelo baseline, es decir, un único modelo global alimentado con todas las variables a la vez, entrenado sobre los mismos datos de entrenamiento y con la misma división temporal que el sistema multiagente | Must | Pendiente | RF-02 |
| RF-20 | Baselines simples de referencia | El sistema calcularía adicionalmente predictores simples de referencia como la media móvil | Could | Pendiente | RF-02 |
| RF-21 | Cálculo de métricas de evaluación | El sistema calculará, para el sistema multiagente, el baseline y los predictores simples (si se implementaran), las métricas RMSE, MAE y sesgo medio (*bias*) sobre el conjunto de test | Must | Pendiente | RF-12, RF-19 |
| RF-22 | Informe comparativo | El sistema generará un informe comparativo que contraponga las métricas del sistema multiagente con las del baseline, para evaluar las mejoras obtenidas | Must | Pendiente | RF-21 |
| RF-23 | Evaluación por segmentos | El sistema calcularía las métricas de RF-21 por segmentos: categoría, departamento, tienda y tipo de demanda | Could | Pendiente | RF-03, RF-12, RF-19, RF-20 |
| RF-24 | Análisis de protagonismo de los agentes | El sistema calcularía los pesos medios asignados por el coordinador a cada agente según contexto y los presentaría en tablas y gráficas en `/output/` | Should | Pendiente | RF-11 |




---

## 4. Requisitos no funcionales

| ID | Requisito | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|--------|
| RNF-01 | Evaluación de la precisión | El sistema evaluará el error (RMSE y MAE) del sistema multiagente frente al del baseline en el conjunto de test. El ajuste de hiperparámetros se realizará únicamente con entrenamiento y validación, y el conjunto de test se usará una sola vez para la evaluación final | Must | Pendiente |
| RNF-02 | Rendimiento | Minimizará el tiempo de predicción en la medida de lo posible | Must | Pendiente |
| RNF-03 | Usabilidad | Los ficheros de salida tendrán formato CSV con columnas de nombres claros (`item_id`, `store_id`, `date`, `prediction`, ...). Los mensajes por consola serán comprensibles | Must | Pendiente |
| RNF-04 | Mantenibilidad | El código estaría comentado, sobre todo las partes más complejas, para facilitar la legibilidad y comprensión | Could | Pendiente |
| RNF-05 | Modularidad | Se podría añadir o quitar agentes especializados modificando únicamente la configuración y el módulo del agente, sin tocar el resto del sistema | Should | Pendiente |
| RNF-06 | Reproducibilidad | Dos ejecuciones con la misma configuración y datos producirán los mismos resultados | Must | Pendiente |
| RNF-07 | Eficiencia | La ejecución completa del sistema funcionará dentro de los límites de memoria del entorno de ejecución, para lo cual usará tipos de datos eficientes (`int16`, `float32`, `category`), formatos de almacenamiento columnares y procesamiento por bloques. En el equipo local (8 GB de RAM) el pico de memoria no superará los 5 GB; en un entorno en la nube (por ejemplo Kaggle o Google Colab), si se emplea para las ejecuciones más costosas, no superará la memoria disponible en dicho entorno. Como mínimo, la fase de predicción y las consultas se podrán ejecutar en el equipo local | Must | Pendiente |
| RNF-08 | Tolerancia a fallos | Si un agente no pudiera producir predicción para una serie, el coordinador renormalizaría los pesos entre los agentes restantes en lugar de interrumpir la ejecución | Should | Pendiente |
| RNF-09 | Legalidad del uso del dataset | El dataset M5 se utilizará de acuerdo con las condiciones de uso de la competición de Kaggle y exclusivamente con fines académicos. No se redistribuirán los datos originales en el repositorio | Must | Pendiente |
| RNF-10 | Portabilidad | El sistema se ejecutaría en Windows, Linux y macOS con una versión de Python igual o superior a la que se fije en la documentación | Could | Pendiente |
| RNF-11 | Documentación | El repositorio incluirá un README con instrucciones de instalación y ejecución, un manual de usuario y un manual técnico | Must | Pendiente |
| RNF-12 | Ausencia de fuga de información | Ni los agentes, ni el coordinador, ni el baseline utilizarán datos posteriores a la fecha de predicción. El coordinador se entrenará solo con predicciones de los agentes sobre el conjunto de validación | Must | Pendiente |
| RNF-13 | Control de versiones | Todo el código se mantendrá en un repositorio Git alojado en GitHub, con commits frecuentes y mensajes descriptivos que referencien el requisito correspondiente. Además, se usará Trello para la organización personal de los sprints | Must | Pendiente |



---

## 5. Fuera de alcance (Won't)

| ID | Requisito | Descripción | Motivo |
|----|-----------|-------------|--------|
| RF-25 | Gestión de inventario real | El sistema definiría el stock de seguridad a partir de los datos, además de plazos de reposición, proveedores y costes asociados, basándose en el dataset | El dataset no contiene los datos necesarios (costes, plazos, proveedores). Como alternativa, RF-18 ofrece una demostración con valores ficticios o introducidos por el usuario, que permite ilustrar la utilidad de la predicción |
| RF-26 | Reentrenamiento en línea | El sistema se reentrenaría automáticamente al recibir datos nuevos | Excede el alcance del proyecto y no es necesario para evaluar el enfoque multiagente |

---

## 6. Trazabilidad

Relaciona cada requisito con el código que lo implementa y la prueba que lo verifica.

| Requisito |  Módulo / fichero | Prueba asociada |
|-----------|------------------|-----------------|
| RF-01 |  |  | 
| RF-02 |  |  |  
| RF-03 |  |  |
| RF-04 |  |  |  
| RF-05 |  |  |  
| RF-06 |  |  |  
| RF-07 |  |  |  
| RF-08 |  |  |  
| RF-09 |  |  |  
| RF-10 |  |  |  
| RF-12 |  |  |
| RF-19 |  |  |  
| RF-21 |  |  |  
| RF-22 |  |  |  


*(Los requisitos Should y Could se añadirán a esta tabla cuando se decida implementarlos)*
