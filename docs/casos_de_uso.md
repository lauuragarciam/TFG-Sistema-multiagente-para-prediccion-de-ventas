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
| CU-01 | | | | Pendiente |
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
