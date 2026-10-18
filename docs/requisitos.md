# Requisitos del sistema

**Proyecto:** Sistema multiagente para la predicción de ventas y optimización de inventario en retail
**Autora:** Laura García Medina
**Última actualización:** 18-10-2026

---

## 1. Introducción

### 1.1 Propósito de este documento

Este documento recoge los requisitos funcionales y no funcionales del sistema. Su objetivo es definir con claridad qué debe hacer el sistema y bajo qué condiciones de calidad, delimitar su alcance y servir de referencia durante todo el desarrollo.

Cada requisito tiene un identificador único, una prioridad y un estado, de modo que pueda trazarse hasta las tareas de planificación, el código que lo implementa y las pruebas que lo verifican.


### 1.2 Alcance del sistema

El sistema desarrollado es un sistema multiagente que predice la demanda de productos en el sector retail a partir de datos históricos de ventas. Está compuesto por agentes especializados, cada uno centrado en un factor determinante de la demanda (temporal, precios, eventos y demanda intermitente), y por un agente coordinador que combina sus predicciones parciales en una predicción final según el contexto de cada caso.

**El sistema incluye:**

- El análisis exploratorio automatizado del dataset y la preparación de los datos para el entrenamiento de los agentes.
- El entrenamiento de los agentes especializados y del agente coordinador.
- La predicción de ventas diarias por producto y tienda [dentro de un horizonte de X días a partir del último dato disponible].
- Un modo de consulta que permite obtener la predicción de un producto, tienda y fecha o rango de fechas concretos.
- La evaluación del sistema frente a un modelo único de referencia (baseline), con el fin de valorar si el enfoque multiagente aporta mejoras.

**El sistema no incluye:**

- [Predicciones fuera del horizonte definido.]
- Reentrenamiento en línea ni actualización automática con datos nuevos.
- Uso de fuentes de datos distintas del dataset M5 de Walmart.

**Datos utilizados:** dataset M5 Forecasting (Walmart), con ventas diarias por producto y tienda, precios y calendario de eventos.

### 1.3 Definiciones y abreviaturas

| Término | Definición |
|---------|------------|
| RF | Requisito funcional |
| RNF | Requisito no funcional |
|  |  |

---

## 2. Convenciones

### 2.1 Identificadores

- Requisitos funcionales: `RF-01`, `RF-02`, ...
- Requisitos no funcionales: `RNF-01`, `RNF-02`, ...
- Los IDs son **estables**: si un requisito se elimina, su ID no se reutiliza (se marca como *Descartado*).

### 2.2 Prioridad (MoSCoW)

| Valor | Significado |
|-------|-------------|
| **Must** | Imprescindible: sin él el TFG no cumple sus objetivos |
| **Should** | Importante, pero el sistema funciona sin él |
| **Could** | Deseable si sobra tiempo |
| **Won't** | Fuera de alcance en esta versión (se documenta a propósito) |

### 2.3 Estado

`Pendiente` · `En progreso` · `Completado` · `Descartado`

---

## 3. Requisitos funcionales

| ID | Requisito | Descripción | Prioridad | Sprint | Estado | Dependencia |
|------|-----------|-----------|--------|--------|--------|--------|
| RF-01 | Análisis exploratorio automatizado | HAY QUE ESPECIFICAR QUE TABLAS CREA Y DONDE LAS GUARDA | Must |  | Pendiente | |
| RF-02 | Preparación de datos | El sistema transformará los datos para para su consumo por los agentes. HAY QUE ESPECIFICAR MÁS | Must |  |Pendiente | |
| RF-03 | Entrenamiento de agentes |  | Must |  | Pendiente | |
| RF-04 | Entrenamiento de agente coordinador |  | Must |  | Pendiente | |
| RF-05 | Predecir según temporalidad | Un agente especializado predecirá la cantidad de producto vendido en cada tienda basándose en las ventas previas, empleando su histórico reciente para capturar tendencias y patrones de estacionalidad  | Must |  | Pendiente | |
| RF-06 | Predecir según precios | Un agente especializado analizará las modificaciones de precio, tales como descuentos o promociones, para estimar su efecto sobre el volumen de ventas, aportando una predicción sensible a estos cambios | Must |  | Pendiente | |
| RF-07 | Predecir según eventos | Un agente especializado detectará si hay eventos especiales, festivos o fechas señaladas que puedan afectar a las ventas, generando una predicción que anticipe posibles picos de demanda asociados a estos factores | Must |  | Pendiente | |
| RF-08 | Detectar demanda intermitente | Un agente especializado analizará si se trata de un producto que se vende de manera irregular y adapta su predicción a este tipo de comportamiento | Must |  | Pendiente | |
| RF-09 | Combinar predicciones | El agente coordinador analizará el contexto de cada predicción y según este combina las predicciones parciales de los agentes anteriores para llegar a la predicción final más plausible  | Must |  | Pendiente | |
| RF-10 | Devolver predicciones | El sistema devolverá en bloque las predicciones de todos los productos y tiendas del conjunto de datos de test | Must |  | Pendiente | |
| RF-11 | Consultar predicción | El sistema devolvería la predicción individual de un producto en la tienda y fecha o intervalo de tiempo especificados | Should |  | Pendiente | |
| RF-12 | Entrenamiento del modelo baseline |  | Must |  | Pendiente | |
| RF-13 | Cálculo de métricas de evaluación |  | Must |  | Pendiente | |
| RF-14 | Comparar predicciones | El sistema comparará las predicciones con un modelo baseline para evaluar las mejoras obtenidas | Must |  | Pendiente | |
| RF-15 | Calcular stock de seguridad | El sistema calcularía el stock de seguridad para un producto y tienda suponiendo ciertos costes y plazos no incluidos en el dataset | Could |  | Pendiente | |
| RF-16 | Devolver predicciones de todos los agentes especializados | El sistema devolvería las predicciones de cada agente especializado  | Should |  | Pendiente | |
| RF-17 | Devolver los pesos asignados por el coordinador |  El sistema devolvería los pesos asignados y usados para el cálculo de la predicción final | Should |  | Pendiente | |
| RF-18 | Visualización de predicciones frente a ventas reales | El sistema devolvería una gráfica visual donde se mostría la diferencia entre las predicciones y las ventas reales | Could |  | Pendiente | |
| RF-19 | Guardar y cargar modelos entrenados |  | Should |  | Pendiente | |





---

## 4. Requisitos no funcionales

| ID | Requisito | Descripción | Prioridad | Sprint | Estado |
|----|-------------|-----------|--------|--------|--------|
| RNF-01 |  |  |  |  | Pendiente |
| RNF-02 |  |  |  |  | Pendiente |
| RNF-03 |  |  |  |  | Pendiente |
| RNF-04 |  |  |  |  | Pendiente |
| RNF-05 |  |  |  |  | Pendiente |


---

## 5. Fuera de alcance (Won't)

| ID | Descripción | Motivo |
|----|-------------|--------|
|  |  |  |

---

## 6. Trazabilidad

Relaciona cada requisito con su tarjeta de Trello, el código que lo implementa y la prueba que lo verifica.

| Requisito | Tarjeta Trello | Módulo / fichero | Prueba asociada |
|-----------|----------------|------------------|-----------------|
| RF-01 |  |  |  |

---

## 7. Historial de cambios

| Fecha | Versión | Cambio | Motivo |
|-------|---------|--------|--------|
| 18-10-2026 | 0.1 | Creación del documento |  |
