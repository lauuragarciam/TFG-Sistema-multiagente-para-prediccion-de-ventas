# Notas de diseño y memoria (pendientes de resolver o justificar)

## Fuga de información
- Sellar datos, modelos y predicciones con la configuración de la división temporal y comprobar que coincide al predecir y evaluar (RNF-12, RNF-06).
- Las predicciones de los agentes sobre validación deben generarse sin ver las ventas del propio periodo de validación, para reproducir la situación de test. 
- El conjunto de test se usa una sola vez (RNF-01). Durante el desarrollo, iterar con validación y no mirar test.

## Diseño de agentes y coordinador
- El contexto del coordinador se apoya en variables generales (existencia y tipo de evento, día de la semana, SNAP, variación de precio, tipo de demanda) y no en el nombre concreto del evento.
- Entrenar un agente suelto deja al coordinador desfasado, porque sus pesos se aprendieron con la versión anterior de ese agente.
- Un sistema entrenado con agentes incompletos sirve para probar, no para evaluar.

## Datos y división
- Valores exactos de la división (fechas de corte, número de ventanas de validación): a la configuración y a la memoria. Con 3 ventanas de 28 días hay 8 series sin historial en entrenamiento y los cuatro tipos de evento aparecen en validación.
- Los eventos concretos de test no aparecen en validación con ninguna cantidad razonable de ventanas. Los tipos de test (cultural y religioso) tienen solo 3 días cada uno en validación.
- Cifras de las comprobaciones: 0 series sin ventas, 1 con una sola venta, ninguna serie vende antes de su primer precio y no hay huecos de precio intermedios.

## Evaluación
- Test de 28 días en un único periodo (abril-mayo de 2016) con solo 4 días de evento: las conclusiones por contexto, y sobre el agente de eventos, tienen baja confianza estadística.
- Imparcialidad de la comparación: decidir y documentar si el baseline usa o no el conjunto de validación.
- WRMSSE: la historia se cuenta desde el primer precio. El WRMSSE por segmento es una adaptación y no equivale al global.
- RMSE y MAE están dominados por las series de más volumen. Con demanda intermitente, predecir 0 minimiza el MAE.
- Stock de seguridad (CU-13): se calcula con el RMSE de cada serie en test, no con validación, para que ambos modelos se comparen con los mismos datos. Es retrospectivo, se ejecuta tras la evaluación final, y supone errores normales e independientes, lo que no se cumple con demanda intermitente.

## Decisiones aplazadas
- RF-20 (predictores simples de referencia): sin caso de uso por ahora. Si se implementa, será un caso de predicción similar a CU-06 que CU-10 incluya en la comparación.
- RF-17 (interfaz): sin caso de uso, porque es un canal de acceso y no una tarea. Los casos de uso asumen consola.
- Límite de filas de consola y carpeta `/output/consultas/`: parámetros comunes a CU-07 y CU-08, configurables.
- Ajuste de hiperparámetros de los agentes: solo con entrenamiento (validación cruzada temporal dentro de entrenamiento), reservando validación para el coordinador.
- RMSE y MAE por segmento siguen dependiendo de la escala: dentro de cada segmento mandan las series de más volumen.