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
| RF-01 | Análisis exploratorio automatizado | HAY QUE ESPECIFICAR QUE TABLAS CREA Y DONDE LAS GUARDA | Must | Pendiente | |
| RF-02 | Preparación de datos | El sistema transformará los datos para su consumo por los agentes. HAY QUE ESPECIFICAR MÁS | Must |Pendiente | |
| RF-03 | Entrenamiento de agentes | Los agentes aprenderán basándose en los datos de entrenamiento preparados específicamente para cada uno | Must | Pendiente | RF-01, RF-02|
| RF-04 | Entrenamiento del agente coordinador | El agente coordinador aprenderá a asignar pesos a las predicciones de los agentes específicos según el contexto y utilizando los datos del conjunto de validación para no verse sesgado | Must | Pendiente | RF-03 |
| RF-05 | Predecir según temporalidad | Un agente especializado predecirá la cantidad de producto vendido en cada tienda basándose en las ventas previas, empleando su histórico reciente para capturar tendencias y patrones de estacionalidad  | Must | Pendiente | RF-03 |
| RF-06 | Predecir según precios | Un agente especializado analizará las modificaciones de precio, tales como descuentos o promociones, para estimar su efecto sobre el volumen de ventas, aportando una predicción sensible a estos cambios | Must | Pendiente | RF-03 |
| RF-07 | Predecir según eventos | Un agente especializado detectará si hay eventos especiales, festivos o fechas señaladas que puedan afectar a las ventas, generando una predicción que anticipe posibles picos de demanda asociados a estos factores | Must | Pendiente | RF-03 |
| RF-08 | Predecir según demanda intermitente | Un agente especializado realizará una predicción teniendo en cuenta si se trata de un artículo de venta intermitente  | Must | Pendiente | RF-03 |
| RF-09 | Combinar predicciones | El agente coordinador analizará el contexto de cada predicción y según este combina las predicciones parciales de los agentes especializados para llegar a la predicción final más plausible  | Must | Pendiente | RF-04 - RF-08 |
| RF-10 | Devolver predicciones | El sistema devolverá las predicciones para todos los productos y tiendas del conjunto de datos de test en el fichero /output | Must | Pendiente | RF-09 |
| RF-11 | Consultar predicción | El sistema devolvería la predicción individual de un producto en la tienda y fecha o intervalo de tiempo especificados (dentro de los disponibles) mediante una consulta por consola en la que consultaría las predicciones ya almacenadas en /output | Should | Pendiente | RF-10 |
| RF-12 | Entrenamiento del modelo baseline | NO SE QUE MODELO BASELINE PONDRÉ | Must | Pendiente | RF-02 |
| RF-13 | Cálculo de métricas de evaluación | TENGO QUE PENSAR COMO COMPARARLOS | Must | Pendiente | RF-09, RF-12 |
| RF-14 | Comparar predicciones | El sistema comparará las predicciones con un modelo baseline para evaluar las mejoras obtenidas | Must | Pendiente | RF-09, RF-12, RF-13 |
| RF-15 | Calcular stock de seguridad | El sistema calcularía el stock de seguridad para un producto y tienda suponiendo ciertos costes y plazos no incluidos en el dataset, es decir, usando datos inventados o introducidos por consola | Could | Pendiente | RF-10 |
| RF-16 | Devolver predicciones de todos los agentes especializados | El sistema devolvería las predicciones de cada agente especializado por consola, consultando las predicciones en el fichero /output | Should | Pendiente | RF-10 |
| RF-17 | Visualización de predicciones frente a ventas reales | El sistema devolvería una gráfica donde se mostraría la diferencia entre las predicciones y las ventas reales, la cual se almacenaría en /output | Could | Pendiente | RF-10 |
| RF-18 | Guardar y cargar modelos entrenados | Se almacenarían los modelos entrenados, de modo que cada agente podría guardarse individualmente, además del sistema al completo  | Should | Pendiente | RF-03, RF-04 |
| RF-19 | Interfaz | Se podrían realizar las consultas asociadas a requisitos como RF-11, RF-15, RF-16 o RF17. | Could | Pendiente | RF-10 |



---

## 4. Requisitos no funcionales

| ID | Requisito | Descripción | Prioridad | Estado |
|----|-------------|-----------|--------|--------|
| RNF-01 | Precisión | Buscará minimizar el error lo máximo posible sin adaptarse a los datos | Must | Pendiente |
| RNF-02 | Rendimiento | Minimizará el tiempo de predicción en la medida de lo posible | Must | Pendiente |
| RNF-03 | Usabilidad | Los ficheros y salidas por consola serán legibles, bien estructurados, con nombres claros | Must | Pendiente |
| RNF-04 | Mantenibilidad | El código estará comentado, sobre todo las partes más complejas, para facilitar la legibilidad y comprensión | Must | Pendiente |
| RNF-05 |  |  |  | Pendiente |
| RNF-06 |  |  |  | Pendiente |
| RNF-07 |  |  |  | Pendiente |
| RNF-08 |  |  |  | Pendiente |



---

## 5. Fuera de alcance (Won't)

| ID | Requisito | Descripción | Motivo |
|----|-----------|-------------|--------|
| RF-25 | Gestión de inventario | El sistema definiría el stock de seguridad de los datos, además de plazos de reposición, proveedores y costes asociados basandose en el dataset | No se disponen de los datos necesarios para realizar estos cálculos, por ello se propone como posible RF-15, pudiendo mostrar la aplicación y ventasjas que supondría este cálculo de ventas |

---

## 6. Trazabilidad

Relaciona cada requisito con su tarjeta de Trello, el código que lo implementa y la prueba que lo verifica.

| Requisito | Tarjeta Trello | Módulo / fichero | Prueba asociada |
|-----------|----------------|------------------|-----------------|
| RF-01 |  |  |  |

