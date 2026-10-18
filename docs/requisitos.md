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
- [Un modo de consulta que permite obtener la predicción de un producto, tienda y fecha o rango de fechas concretos.]
- La evaluación del sistema frente a un modelo único de referencia (baseline), con el fin de valorar si el enfoque multiagente aporta mejoras.

**El sistema no incluye:**

- [Predicciones fuera del horizonte definido.]
- [Reentrenamiento en línea ni actualización automática con datos nuevos.]
- [Uso de fuentes de datos distintas del dataset M5 de Walmart.]
- [Interfaz gráfica de usuario.]
- La gestión de inventario en sí (reposición, pedidos o decisiones de compra). El sistema genera predicciones de demanda que podrían servir de base para ello.

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

| ID | Descripción | Prioridad | Sprint | Estado |
|----|-------------|-----------|--------|--------|
| RF-01 |  |  |  | Pendiente |

---

## 4. Requisitos no funcionales

| ID | Descripción | Prioridad | Sprint | Estado |
|----|-------------|-----------|--------|--------|
| RNF-01 |  |  |  | Pendiente |

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
