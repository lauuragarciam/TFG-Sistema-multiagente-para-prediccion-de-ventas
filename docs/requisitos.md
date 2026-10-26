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
| RF-01 | Análisis exploratorio automatizado | El sistema generará, a partir de los ficheros del datset, tablas resumen en formato CSV en `/output/eda/` y las figuras asociadas en formato PNG. Las tablas incluirán estadísticos de ventas por categoría, departamento y tienda, porcentaje de ceros por serie, clasificación de series según tipo de demanda, correlación entre variación de precio y ventas, ventas medias por día de la semana, ventas medias por evento y por día SNAP | Must | Pendiente | |
| RF-02 | Preparación de datos | El sistema transformará los datos del M5 para su consumo por los agentes: conversión del formato ancho a largo, reducción del uso de memoria mediante tipos de datos eficientes, unión de ventas, precios y calendario en una única tabla, y almacenamiento del resultado en `/data/processed/` | Must |Pendiente | |
| RF-03 | Clasificación de series por tipo de demanda | El sistema clasificará cada serie como suave, errática, intermitente o irregular a partir de ADI y CV², y guardará la clasificación en `/data/processed/` para su uso por el agente intermitente, el coordinador y la evaluación por segmentos. | Must | Pendiente | RF-02 |
| RF-04 | Entrenamiento de agentes | Los agentes aprenderán basándose en los datos de entrenamiento preparados específicamente para cada uno | Must | Pendiente | RF-02, RF-03 |
| RF-05 | Entrenamiento del agente coordinador | El agente coordinador aprenderá a asignar pesos a las predicciones de los agentes especializados según el contexto. Se entrenará con las predicciones de los agentes sobre el conjunto de validación para no verse sesgado. | Must | Pendiente | RF-02, RF-03 |
| RF-06 | Predecir según temporalidad | Un agente especializado predecirá la cantidad de producto vendido en cada tienda basándose en las ventas previas, empleando su histórico reciente para capturar tendencias y patrones de estacionalidad  | Must | Pendiente | RF-04 |
| RF-07 | Predecir según precios | Un agente especializado analizará las modificaciones de precio, tales como descuentos o promociones, para estimar su efecto sobre el volumen de ventas, aportando una predicción sensible a estos cambios | Must | Pendiente | RF-03 |
| RF-08 | Predecir según eventos | Un agente especializado detectará si hay eventos especiales, festivos o fechas señaladas que puedan afectar a las ventas, generando una predicción que anticipe posibles picos de demanda asociados a estos factores | Must | Pendiente | RF-04 |
| RF-09 | Predecir según demanda intermitente | Un agente especializado realizará una predicción teniendo en cuenta si se trata de un artículo de venta intermitente  | Must | Pendiente | RF-04 |
| RF-10 | Combinar predicciones | El agente coordinador analizará el contexto de cada predicción y, según este, combinará las predicciones parciales de los agentes especializados para obtener la predicción final | Must | Pendiente | RF-06, RF-07, RF-08, RF-09 |
| RF-11 | Exportación de pesos del coordinador | El sistema guardaría, para cada predicción, las predicciones parciales de cada agente y los pesos asignados por el coordinador en `/output/`. | Should | Pendiente | RF-10 |
| RF-12 | Devolver predicciones | El sistema guardará en `/output/` las predicciones de todos los productos y tiendas del conjunto de test para todo el horizonte | Must | Pendiente | RF-10 |
| RF-13 | Consultar predicción | El sistema devolverá por consola la predicción individual de un producto en una tienda y fecha o intervalo especificados (dentro de los disponibles), consultando las predicciones ya almacenadas en `/output/` | Should | Pendiente | RF-12 |
| RF-14 | Consultar predicciones de los agentes | El sistema devolverá por consola las predicciones de cada agente especializado y sus pesos para una serie y fecha, consultando los ficheros de `/output/` | Should | Pendiente | RF-11, RF-12 |
| RF-15 | Visualización de predicciones frente a ventas reales | El sistema devolvería una gráfica donde se mostraría la diferencia entre las predicciones y las ventas reales, la cual se almacenaría en `/output/`| Could | Pendiente | RF-12 |
| RF-16 | Guardar y cargar modelos entrenados | Se almacenarían los modelos entrenados, de modo que cada agente podría guardarse individualmente, además del sistema al completo  | Should | Pendiente | RF-04, RF-05 |
| RF-17 | Interfaz | El sistema ofrecería una interfaz (por consola o gráfica) desde la que realizar las consultas de RF-11, RF-15, RF-16 y RF-17 | Could | Pendiente | RF-12 |
| RF-18 | Cálculo de stock de seguridad | El sistema calculará el stock de seguridad de un producto y tienda a partir de la predicción y de costes y plazos ficticios o introducidos por consola, ya que el dataset no los contiene. Su finalidad es ilustrar la utilidad de la predicción, no realizar una gestión real de inventario. | Could | Pendiente | RF-12 |
| RF-19 | Entrenamiento del modelo baseline | El sistema entrenará un modelo baseline, es decir, un único modelo global alimentado con todas las variables a la vez, entrenado sobre los mismos datos de entrenamiento y con la misma división temporal que el sistema multiagente | Must | Pendiente | RF-02 |
| RF-20 | Baselines simples de referencia | El sistema calcularía adicionalmente predictores simples de referencia como la media móvil | Could | Pendiente | RF-02 |
| RF-21 | Cálculo de métricas de evaluación | El sistema calculará, para el sistema multiagente, el baseline y los predictores simples, las métricas RMSE, MAE y sesgo medio (*bias*) sobre el conjunto de test | Must | Pendiente | RF-12, RF-19, RF-20 |
| RF-22 | Informe comparativo | El sistema generará un informe comparativo que contraponga las métricas del sistema multiagente con las del baseline, para evaluar las mejoras obtenidas | Must | Pendiente | RF-21 |
| RF-23 | Evaluación por segmentos | El sistema calcularía las métricas de RF-21 por segmentos: categoría, departamento, tienda y tipo de demanda | Could | Pendiente | RF-12, RF-19, RF-20 |
| RF-24 | Análisis de protagonismo de los agentes | El sistema calcularía los pesos medios asignados por el coordinador a cada agente según contexto y los presentaría en tablas y gráficas en `/output/` | Could | Pendiente | RF-11 |




---

## 4. Requisitos no funcionales

| ID | Requisito | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|--------|
| RNF-01 | Precisión de la predicción | El sistema multiagente obtendrá, en el conjunto de test, un error (RMSE y MAE) menor o igual que el del baseline. El ajuste de hiperparámetros se realizará únicamente con entrenamiento y validación, y el conjunto de test se usará una sola vez para la evaluación final | Must | Pendiente |
| RNF-02 | Rendimiento | Minimizará el tiempo de predicción en la medida de lo posible | Must | Pendiente |
| RNF-03 | Usabilidad | Los ficheros de salida tendrán formato CSV con columnas de nombres claros (`item_id`, `store_id`, `date`, `prediction`, ...). Los mensajes por consola serán comprensibles | Must | Pendiente |
| RNF-04 | Mantenibilidad | El código estaría comentado, sobre todo las partes más complejas, para facilitar la legibilidad y comprensión | Could | Pendiente |
| RNF-05 | Modularidad | Se podría añadir o quitar agentes especializados modificando únicamente la configuración y el módulo del agente, sin tocar el resto del sistema | Should | Pendiente |
| RNF-06 | Reproducibilidad | Dos ejecuciones con la misma configuración y datos producirán los mismos resultados | Must | Pendiente |
| RNF-07 | Eficiencia | El sistema funcionará completo en un equipo personal con 16 GB de RAM, para lo cual usará tipos de datos eficientes (`int16`, `float32`, `category`) y procesamiento por bloques cuando sea necesario | Must | Pendiente |
| RNF-08 | Tolerancia a fallos | Fallo de un agente | Si un agente no pudiera producir predicción para una serie, el coordinador renormalizaría los pesos entre los agentes restantes en lugar de interrumpir la ejecución | Should | Pendiente |
| RNF-09 | Legalidad del uso del dataset | El dataset M5 se utilizará de acuerdo con las condiciones de uso de la competición de Kaggle y exclusivamente con fines académicos. No se redistribuirán los datos originales en el repositorio | Must | Pendiente |
| RNF-10 | Portabilidad | El sistema se ejecutaría en Windows, Linux y macOS con una versión de Python igual o superior a la que se fije en la documentación | Could | Pendiente |
| RNF-11 | Documentación | El repositorio incluirá un README con instrucciones de instalación y ejecución, un manual de usuario y un manual técnico | Must | Pendiente |


---

## 5. Fuera de alcance (Won't)

| ID | Requisito | Descripción | Motivo |
|----|-----------|-------------|--------|
| RF-25 | Gestión de inventario | El sistema definiría el stock de seguridad de los datos, además de plazos de reposición, proveedores y costes asociados basandose en el dataset | No se disponen de los datos necesarios para realizar estos cálculos, por ello se propone como posible RF-15, pudiendo mostrar la aplicación y ventasjas que supondría este cálculo de ventas |
| RF-30 | Reentrenamiento en línea | El sistema se reentrenaría automáticamente al recibir datos nuevos | Excede el alcance del proyecto y no es necesario para evaluar el enfoque multiagente |

---

## 6. Trazabilidad

Relaciona cada requisito con su tarjeta de Trello, el código que lo implementa y la prueba que lo verifica.

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


*(Los requisitos Should y Could se añadirán a esta tabla cuando se decida implementarlos.)*
