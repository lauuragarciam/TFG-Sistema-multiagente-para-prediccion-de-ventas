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
| ADI | *Average Demand Interval*: intervalo medio entre demandas no nulas (nº de periodos / nº de periodos con demanda no nula) |
| CV² | Cuadrado del coeficiente de variación de las demandas no nulas; junto con ADI sirve para clasificar series (suave, errática, intermitente, irregular) |
| RMSE / MAE | Error cuadrático medio (raíz) / error absoluto medio |
| WRMSSE | Raíz del error cuadrático medio escalado y ponderado, métrica de la competición M5 |
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
| RF-01 | Análisis exploratorio automatizado | El sistema generará, a partir del conjunto de entrenamiento de los datos procesados, tablas resumen en formato CSV en `/output/eda/` y las figuras asociadas en formato PNG. Las tablas incluirán estadísticos de ventas por categoría, departamento y tienda, clasificación de series según tipo de demanda, correlación entre variación de precio y ventas, ventas medias por día de la semana, ventas medias por evento y por día SNAP | Must | Pendiente | RF-03 |
| RF-02 | Preparación de datos | El sistema transformará los datos del M5 para su consumo por los agentes: conversión del formato ancho a largo, reducción del uso de memoria mediante tipos de datos eficientes, unión de ventas, precios y calendario en una única tabla, tratamiento de los valores ausentes y generación de las variables propias de cada agente a partir de los datos. Los precios nulos corresponden a días en que el producto aún no estaba a la venta, por lo que esos días se excluirán de la tabla. Además, se dividirán los datos de forma temporal en entrenamiento, validación y test con fechas de corte configurables. El resultado se almacenará en `/data/processed/` | Must | Pendiente | |
| RF-03 | Clasificación de series por tipo de demanda | El sistema clasificará cada serie como suave, errática, intermitente o irregular a partir de ADI y CV², calculados únicamente con el conjunto de entrenamiento y contando los periodos desde la primera fecha con precio registrado de cada producto en cada tienda (inicio de disponibilidad). El criterio de clasificación, con sus umbrales configurables y el tratamiento de los casos límite, se especificará en la documentación. La clasificación se guardará en `/data/processed/` | Must | Pendiente | RF-02 |
| RF-04 | Entrenamiento de agentes | Los agentes aprenderán basándose en los datos de entrenamiento preparados específicamente para cada uno | Must | Pendiente | RF-02, RF-03 |
| RF-05 | Entrenamiento del agente coordinador | El agente coordinador aprenderá a asignar pesos a las predicciones de los agentes especializados según el contexto. Se entrenará con las predicciones de los agentes sobre el conjunto de validación para no verse sesgado | Must | Pendiente | RF-06, RF-07, RF-08, RF-09 |
| RF-06 | Predecir según temporalidad | Un agente especializado predecirá la cantidad de producto vendido en cada tienda basándose en las ventas previas, empleando su histórico reciente para capturar tendencias y patrones de estacionalidad  | Must | Pendiente | RF-04 |
| RF-07 | Predecir según precios | Un agente especializado analizará las modificaciones de precio, tales como descuentos o promociones, para estimar su efecto sobre el volumen de ventas, aportando una predicción sensible a estos cambios | Must | Pendiente | RF-04 |
| RF-08 | Predecir según eventos | Un agente especializado detectará si hay eventos especiales, festivos o fechas señaladas que puedan afectar a las ventas, generando una predicción que anticipe posibles picos de demanda asociados a estos factores | Must | Pendiente | RF-04 |
| RF-09 | Predecir según demanda intermitente | Un agente especializado realizará una predicción teniendo en cuenta si se trata de un artículo de venta intermitente  | Must | Pendiente | RF-03, RF-04 |
| RF-10 | Combinar predicciones | El agente coordinador analizará el contexto de cada predicción y, según este, combinará las predicciones parciales de los agentes especializados para obtener la predicción final | Must | Pendiente | RF-06, RF-07, RF-08, RF-09 |
| RF-11 | Exportación de pesos del coordinador | El sistema guardará, para cada predicción, las predicciones parciales de cada agente y los pesos asignados por el coordinador en `/output/` | Must | Pendiente | RF-10 |
| RF-12 | Devolver predicciones | El sistema guardará en `/output/` las predicciones del modelo multiagente de todos los productos y tiendas del conjunto de test, con una fila por producto, tienda y día | Must | Pendiente | RF-10, RF-16 |
| RF-13 | Consultar predicciones | El sistema devolvería por consola las predicciones del modelo indicado (sistema multiagente o baseline) para una serie concreta, para un subconjunto de series filtrado por producto, tienda, categoría, departamento o estado, o para todas las series, en la fecha o el intervalo especificado (dentro de los disponibles), consultando las predicciones ya almacenadas en `/output/` | Should | Pendiente | RF-12, RF-19 |
| RF-14 | Consultar predicciones de los agentes | El sistema devolvería por consola las predicciones de cada agente especializado y sus pesos para una serie concreta, para un subconjunto de series filtrado por producto, tienda, categoría, departamento o estado, o para todas las series, en la fecha o el intervalo especificado, consultando los ficheros de `/output/` | Should | Pendiente | RF-11, RF-12, RF-13 |
| RF-15 | Visualización de predicciones frente a ventas reales | El sistema devolvería una gráfica donde se mostraría la diferencia entre las predicciones de uno o ambos modelos (multiagente y baseline) y las ventas reales del conjunto de test, para una serie concreta o para un subconjunto de series filtrado por producto, tienda, categoría, departamento o estado, la cual se almacenaría en `/output/graficas/` | Could | Pendiente | RF-12, RF-19 |
| RF-16 | Guardar y cargar modelos entrenados | El sistema guardará los modelos entrenados, de modo que cada agente pueda guardarse individualmente, además del sistema multiagente al completo y del modelo baseline | Must | Pendiente | RF-04, RF-05, RF-19 |
| RF-17 | Interfaz | El sistema ofrecería una interfaz (por consola o gráfica) desde la que realizar las consultas de RF-13, RF-14, RF-15 y RF-18 | Could | Pendiente | RF-12 |
| RF-18 | Cálculo de stock de seguridad | El sistema calcularía el stock de seguridad de un producto y tienda a partir de las predicciones del modelo indicado (sistema multiagente o baseline) y de costes y plazos ficticios o introducidos por consola, ya que el dataset no los contiene. Su finalidad sería ilustrar la utilidad de la predicción, no realizar una gestión real de inventario | Could | Pendiente | RF-12, RF-19 |
| RF-19 | Entrenamiento del modelo baseline | El sistema entrenará un modelo baseline, es decir, un único modelo global alimentado con todas las variables a la vez, entrenado sobre los mismos datos de entrenamiento y con la misma división temporal que el sistema multiagente, y generará sus predicciones sobre el conjunto de test | Must | Pendiente | RF-02 |
| RF-20 | Baselines simples de referencia | El sistema calcularía adicionalmente predictores simples de referencia como la media móvil | Could | Pendiente | RF-02 |
| RF-21 | Cálculo de métricas de evaluación | El sistema calculará, para el sistema multiagente, el baseline y los predictores simples (si se implementaran), las métricas RMSE, MAE, sesgo medio (*bias*) y WRMSSE sobre el conjunto de test | Must | Pendiente | RF-12, RF-19 |
| RF-22 | Informe comparativo | El sistema generará un informe comparativo que contraponga las métricas del sistema multiagente con las del baseline, para evaluar las mejoras obtenidas | Must | Pendiente | RF-21 |
| RF-23 | Evaluación por segmentos | El sistema calcularía las métricas de RF-21 por segmentos: categoría, departamento, tienda y tipo de demanda | Could | Pendiente | RF-03, RF-12, RF-19, RF-20 |
| RF-24 | Análisis de protagonismo de los agentes | El sistema calcularía los pesos medios asignados por el coordinador a cada agente, en conjunto y según cada variable de contexto, junto con el número de observaciones en que se basan, y los presentaría en tablas y gráficas en `/output/protagonismo/` | Should | Pendiente | RF-11 |
| RF-27 | Entrenamiento individual de un agente | El sistema permitirá entrenar un único agente especializado sin reentrenar los demás agentes ni el coordinador, y guardarlo para su uso posterior | Should | Pendiente | RF-04, RF-16 |




---

## 4. Requisitos no funcionales

| ID | Requisito | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|--------|
| RNF-01 | Evaluación de la precisión | El sistema evaluará el error del sistema multiagente frente al del baseline en el conjunto de test. El ajuste de hiperparámetros de los agentes se realizará únicamente con el conjunto de entrenamiento, la validación se reservará para el coordinador y el conjunto de test se usará una sola vez para la evaluación final | Must | Pendiente |
| RNF-02 | Rendimiento | Minimizará el tiempo de predicción en la medida de lo posible | Must | Pendiente |
| RNF-03 | Usabilidad | Los ficheros de salida tendrán formato CSV con columnas de nombres claros (`item_id`, `store_id`, `date`, `prediction`, ...). Los mensajes por consola serán comprensibles | Must | Pendiente |
| RNF-04 | Mantenibilidad | El código estaría comentado, sobre todo las partes más complejas, para facilitar la legibilidad y comprensión | Could | Pendiente |
| RNF-05 | Modularidad | Se podría añadir o quitar agentes especializados modificando únicamente la configuración y el módulo del agente, sin tocar el resto del sistema | Should | Pendiente |
| RNF-06 | Reproducibilidad | Dos ejecuciones con la misma configuración y datos producirán los mismos resultados | Must | Pendiente |
| RNF-07 | Eficiencia | La ejecución completa del sistema funcionará dentro de los límites de memoria del entorno de ejecución, para lo cual usará tipos de datos eficientes, formatos de almacenamiento columnares y procesamiento por bloques. En el equipo local (8 GB de RAM) el pico de memoria no superará los 5 GB; en un entorno en la nube (por ejemplo Kaggle o Google Colab), si se emplea para las ejecuciones más costosas, no superará la memoria disponible en dicho entorno. Como mínimo, la fase de predicción y las consultas se podrán ejecutar en el equipo local | Must | Pendiente |
| RNF-08 | Tolerancia a fallos | Si un agente no estuviera disponible para el entrenamiento o no pudiera producir predicción para una serie, el coordinador renormalizaría los pesos entre los agentes restantes en lugar de interrumpir la ejecución, indicando los cambios por consola | Should | Pendiente |
| RNF-09 | Legalidad del uso del dataset | El dataset M5 se utilizará de acuerdo con las condiciones de uso de la competición de Kaggle y exclusivamente con fines académicos. No se redistribuirán los datos originales en el repositorio | Must | Pendiente |
| RNF-10 | Portabilidad | El sistema se ejecutaría en Windows, Linux y macOS con una versión de Python igual o superior a la que se fije en la documentación | Could | Pendiente |
| RNF-11 | Documentación | El repositorio incluirá un README con instrucciones de instalación y ejecución, un manual de usuario y un manual técnico | Must | Pendiente |
| RNF-12 | Ausencia de fuga de información | Ni los agentes, ni el coordinador, ni el baseline utilizarán datos posteriores a la fecha de predicción. El coordinador se entrenará solo con predicciones de los agentes sobre el conjunto de validación. El sistema comprobará que los modelos y los datos con los que se predice o se evalúa se generaron con la misma división temporal y, si no coinciden, interrumpirá la ejecución indicando la discrepancia | Must | Pendiente |
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

| Requisito | Caso de uso | Módulo / fichero | Prueba asociada |
|-----------|-------------|------------------|-----------------|
| RF-01 | CU-02 | | |
| RF-02 | CU-01 | | |
| RF-03 | CU-01 | | |
| RF-04 | CU-03 | | |
| RF-05 | CU-03 | | |
| RF-06 | CU-03, CU-05 | | |
| RF-07 | CU-03, CU-05 | | |
| RF-08 | CU-03, CU-05 | | |
| RF-09 | CU-03, CU-05 | | |
| RF-10 | CU-05 | | |
| RF-11 | CU-05 | | |
| RF-12 | CU-05 | | |
| RF-16 | CU-03, CU-04, CU-05, CU-06 | | |
| RF-19 | CU-04, CU-06 | | |
| RF-21 | CU-10 | | |
| RF-22 | CU-10 | | |


*(Los requisitos Should y Could se añadirán a esta tabla cuando se decida implementarlos)*


---

## Anexo A. Criterio de clasificación de series (requisito del dominio)

Criterio de Syntetos, Boylan y Croston (2005). ADI y CV² están definidos en la sección 1.3. Los umbrales son configurables.

| | CV² < 0,49 | CV² ≥ 0,49 |
|---|---|---|
| **ADI < 1,32** | Suave | Errática |
| **ADI ≥ 1,32** | Intermitente | Irregular |

**Casos límite**

- Si una serie no tiene ningún día a la venta o no registra ninguna venta en el conjunto de entrenamiento, ADI y CV² no están definidos. El sistema emitirá un aviso y la clasificará como intermitente.
- Si una serie registra una única venta, CV² no se puede estimar y se tomará igual a 0.

---

## Anexo B. Métricas de evaluación

Sean $y_i$ la venta real y $\hat{y}_i$ la predicción de la observación $i$ (una serie en un día del conjunto de test) y $n$ el número de observaciones del conjunto de test (series × días).

### B.1 RMSE (raíz del error cuadrático medio)

$$\text{RMSE}=\sqrt{\frac{1}{n}\sum_{i=1}^{n}\left(y_i-\hat{y}_i\right)^2}$$

### B.2 MAE (error absoluto medio)

$$\text{MAE}=\frac{1}{n}\sum_{i=1}^{n}\left|y_i-\hat{y}_i\right|$$

### B.3 Sesgo medio (bias)

$$\text{Sesgo}=\frac{1}{n}\sum_{i=1}^{n}\left(\hat{y}_i-y_i\right)$$

Un valor positivo indica que el modelo sobreestima la demanda y uno negativo, que la subestima.

### B.4 WRMSSE (raíz del error cuadrático medio escalado y ponderado)

Métrica de la competición M5. Para cada serie $j$ de la jerarquía:

$$\text{RMSSE}_j=\sqrt{\frac{\dfrac{1}{h}\sum_{t=T+1}^{T+h}\left(y_{j,t}-\hat{y}_{j,t}\right)^2}{\dfrac{1}{T-1}\sum_{t=2}^{T}\left(y_{j,t}-y_{j,t-1}\right)^2}}$$

donde $h$ es el horizonte (28 días) y $T$ el número de días de historia anterior al test, contados desde el inicio de disponibilidad de la serie. El denominador es el error cuadrático medio del pronóstico ingenuo de un paso (repetir el valor del día anterior) sobre esa historia.

La métrica final pondera cada serie por su importancia económica y promedia los 12 niveles de agregación:

$$\text{WRMSSE}=\frac{1}{12}\sum_{l=1}^{12}\ \sum_{j\in l} w_j^{(l)}\ \text{RMSSE}_j$$

El peso $w_j^{(l)}$ es la proporción de las ventas en dólares (unidades × precio) de la serie $j$ en los 28 días previos al test respecto al total del nivel $l$, de modo que los pesos suman 1 en cada nivel. Las series agregadas se obtienen sumando las series que las componen, y lo mismo se hace con sus predicciones.

| Nivel | Agregación | Nº de series |
|---|---|---|
| 1 | Total | 1 |
| 2 | Estado | 3 |
| 3 | Tienda | 10 |
| 4 | Categoría | 3 |
| 5 | Departamento | 7 |
| 6 | Estado y categoría | 9 |
| 7 | Estado y departamento | 21 |
| 8 | Tienda y categoría | 30 |
| 9 | Tienda y departamento | 70 |
| 10 | Producto | 3.049 |
| 11 | Producto y estado | 9.147 |
| 12 | Producto y tienda | 30.490 |

### B.5 Comparación de las métricas

| Métrica | Escala | Qué penaliza | Limitación principal |
|---|---|---|---|
| RMSE | Unidades de venta | Los errores grandes, porque se elevan al cuadrado | Lo dominan las series de mucho volumen y los picos |
| MAE | Unidades de venta | Todos los errores por igual | Con muchos ceros, predecir 0 minimiza el MAE, lo que favorece a los modelos que infraestiman la demanda intermitente |
| Sesgo | Unidades de venta | Los errores sistemáticos en un sentido | Errores de signo opuesto se compensan, así que no mide la precisión |
| WRMSSE | Sin unidades | Los errores relativos a la dificultad de cada serie, ponderados por su peso económico | Es más compleja de calcular, porque necesita precios y la jerarquía completa |

Un WRMSSE menor que 1 indica que el error del modelo en el horizonte es menor que el error medio de un pronóstico ingenuo de un paso sobre el histórico.

### WRMSSE por segmento

Para un segmento $S$ (conjunto de series producto-tienda definido por categoría, departamento, tienda o tipo de demanda):

$$\text{WRMSSE}_S=\frac{\sum_{j\in S} w_j\ \text{RMSSE}_j}{\sum_{j\in S} w_j}$$

donde $\text{RMSSE}_j$ es el definido en B.4 y $w_j$ es el peso de la serie $j$ en el nivel 12 (proporción de sus ventas en dólares de los 28 días previos al test respecto al total). Los pesos se renormalizan dentro del segmento. No es la métrica oficial de M5, que promedia 12 niveles jerárquicos, sino una adaptación para comparar el rendimiento entre segmentos.

### Referencias

- Hyndman, R. J. y Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting*.
- Makridakis, S., Spiliotis, E. y Assimakopoulos, V. (2022). M5 accuracy competition: Results, findings, and conclusions. *International Journal of Forecasting*.
- M5 Competitors' Guide (documentación de la competición).


---

---

## Anexo C. Cálculo del stock de seguridad

Sean $L$ el plazo de reposición en días (con $L \le h$, siendo $h$ = 28 días el horizonte de predicción), $\hat{y}_t$ la predicción del día $t$ del horizonte, $y_t$ la venta real de ese día y $\sigma_e$ el error típico de predicción diario de la serie.

**Demanda prevista durante el plazo de reposición**

$$D_L=\sum_{t=1}^{L}\hat{y}_t$$

**Error típico de predicción.** Es el RMSE de la serie sobre el conjunto de test (B.1 aplicado a esa serie):

$$\sigma_e=\sqrt{\frac{1}{h}\sum_{t=1}^{h}\left(y_t-\hat{y}_t\right)^2}$$

**Nivel de servicio objetivo.** Se obtiene del coste de rotura por unidad ($c_r$) y del coste de mantener una unidad en stock ($c_m$):

$$\alpha=\frac{c_r}{c_r+c_m}$$

**Stock de seguridad**

$$SS=z_{\alpha}\,\sigma_e\sqrt{L}$$

donde $z_{\alpha}$ es el cuantil $\alpha$ de la distribución normal estándar.

**Limitaciones.** El cálculo supone errores diarios independientes y aproximadamente normales, por lo que es una aproximación pobre en las series de demanda intermitente. Al calcularse con las ventas reales del conjunto de test, el resultado es retrospectivo: ilustra la relación entre la precisión de un modelo y el stock que necesita, no una decisión de inventario real. Con $h$ = 28 observaciones, la estimación de $\sigma_e$ por serie es ruidosa.