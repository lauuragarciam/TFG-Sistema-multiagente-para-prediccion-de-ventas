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
| CU-01 | Preparar los datos | RF-02, RF-03, RNF-06, RNF-07 | Must | Pendiente |
| CU-02 | | | | Pendiente |

Estado: `Pendiente` · `En progreso` · `Completado` · `Descartado`
Prioridad (MoSCoW): `Must` · `Should` · `Could`

---

## 5. Relaciones entre casos de uso

| Caso de uso | Relación | Caso de uso relacionado |
|-------------|----------|-------------------------|
| CU-xx | `«include»` / `«extend»` / precondición | CU-yy |

---

## 6. Descripción de los casos de uso

### CU-01: Preparar los datos

| Campo | Contenido |
|-------|-----------|
| **ID** | CU-01 |
| **Nombre** | Preparar los datos |
| **Actor principal** | Analista |
| **Actores secundarios** | Dataset M5 |
| **Prioridad** | Must |
| **Requisitos relacionados** | RF-02, RF-03, RNF-06, RNF-07 |
| **Descripción** | El analista transforma los ficheros originales del M5 en un conjunto de datos listo para los agentes, con división temporal en entrenamiento, validación y test, y con cada serie clasificada por tipo de demanda |
| **Disparador** | El analista ejecuta el comando de preparación de datos por consola |

**Precondiciones**

1. Los ficheros del dataset M5 están en la ruta especificada

**Flujo principal**

| Paso | Actor / Sistema | Acción |
|------|-----------------|--------|
| 1 | Analista | Ejecuta el comando de preparación de datos |
| 2 | Sistema | Comprueba que existen los ficheros de entrada y que la configuración es válida |
| 3 | Sistema | Lee los ficheros del dataset M5 |
| 4 | Sistema | Convierte las ventas de formato ancho al largo usando tipos de datos eficientes |
| 5 | Sistema | Trata los valores ausentes según los criterios establecidos para ellos |
| 6 | Sistema | Une ventas, precios y calendario en una única tabla |
| 7 | Sistema | Divide los datos en entrenamiento, validación y test | 
| 8 | Sistema | Calcula ADI y CV² de cada serie exclusivamente con los datos de entrenamiento y la clasifica como suave, errática, intermitente o irregular |
| 9 | Sistema | Genera las variables propias para cada agente a partir de los datos |
| 10 | Sistema | Guarda los datos procesados y la clasificación de cada serie en `/data/processed/` |
| 11 | Sistema | Informa por consola de que ha terminado y da un resumen con series, filas por conjunto y fechas de corte usadas |

**Flujos alternativos**

- **FA-1 (paso 10):** Ya existen datos procesados -> el sistema los sobreescribe (RNF-06)

**Excepciones**

- **EX-1 (paso 2):** Faltan ficheros de entrada -> el sistema indica por consola el error, especifica que ficheros faltan y donde esperaba encontrarlos
- **EX-1 (pasos 4-5):** Memoria insuficiente -> procesa en bloques (RNF-07)  

**Postcondiciones**

1. Los datos procesados que necesitan los agentes están preparados en `/data/processed/`.
2. Los ficheros originales del dataset M5 no se han alterado ni incluido al repositorio.

**Relaciones**

- `«include»`: Ninguna
- `«extend»`: Ninguna

**Notas**

- EN **EX-1 (paso 4-5):** NO SE SI TAMBIEN PUEDE PONER QUE HACEMOS ALGO EN LA NUBE

---

### CU-02: Realizar analisis exploratorio

| Campo | Contenido |
|-------|-----------|
| **ID** | CU-02 |
| **Nombre** | Realizar analisis exploratorio |
| **Actor principal** | Analista |
| **Actores secundarios** | Ninguno |
| **Prioridad** | Must |
| **Requisitos relacionados** | RF-01, RNF-06, RNF-07 |
| **Descripción** | El analista genera automáticamente tablas resumen y figuras que muestran los patrones de ventas, la demanda intermitente y la relacion entre precios, ventas y calendario |
| **Disparador** | El analista ejecuta el comando de analisis exploratorio por consola |

**Precondiciones**

1. Los datos necesarios estan procesados en `/data/processed/`

**Flujo principal**

| Paso | Actor / Sistema | Acción |
|------|-----------------|--------|
| 1 | Analista | Ejecuta el comando de análisis exploratorio |
| 2 | Sistema | Carga los datos |
| 3 | Sistema | Calcula estadísticos de ventas por categoría, departamento y tienda|
| 4 | Sistema | Resume la clasificación de series por tipo de demanda, indicando además el porcentaje de ceros de cada una |
| 5 | Sistema | Calcula la correlación entre variación de precio y ventas |
| 6 | Sistema | Calcula las ventas medias por día de la semana, por evento y SNAP |
| 7 | Sistema | Guarda las tablas en CSV y las figuras en PNG en `/output/eda/` |
| 8 | Sistema | Indica por consola que ha terminado el analisis, además de la ruta donde se encuentran los resultados obtenidos |


**Flujos alternativos**

- **FA-1 (paso 7):** Ya existen resultados de una ejecución anterior -> se sobreescriben (RF-06)

**Excepciones**

- **EX-1 (paso 3):** Memoria insuficiente -> procesa en bloques (RNF-07) 

**Postcondiciones**

1. Las tablas y figuras proporcionadas por el análisis están en `/output/eda/` 
2. Los datos procesados no han sido modificados

**Relaciones**

- `«include»`: 
- `«extend»`: 

**Diagrama de secuencia** (opcional, recomendado en los casos complejos)

**Notas**

- MISMA DUDA QUE ANTES

---

### CU-XX: Verbo + objeto

| Campo | Contenido |
|-------|-----------|
| **ID** | CU-XX |
| **Nombre** | |
| **Actor principal** | |
| **Actores secundarios** | |
| **Prioridad** | Must / Should / Could |
| **Requisitos relacionados** | RF-xx, RF-yy, RNF-zz |
| **Descripción** | Una o dos frases con el objetivo del caso de uso. |
| **Disparador** | Qué inicia el caso de uso (por ejemplo, comando por consola). |

**Precondiciones**

1. 
2. 

**Flujo principal**

| Paso | Actor / Sistema | Acción |
|------|-----------------|--------|
| 1 | Actor | |
| 2 | Sistema | |
| 3 | Sistema | |

**Flujos alternativos**

- **FA-1 (paso N):** condición → qué ocurre.

**Excepciones**

- **EX-1 (paso N):** qué falla → cómo responde el sistema (indicar el RNF si aplica, por ejemplo RNF-08).

**Postcondiciones**

1. Estado final del sistema y ficheros generados (por ejemplo, rutas en `/output/`).

**Relaciones**

- `«include»`: 
- `«extend»`: 

**Diagrama de secuencia** (opcional, recomendado en los casos complejos)

**Notas**

- Supuestos, dudas abiertas o decisiones de diseño.

---
