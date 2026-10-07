# Metodología y límites
## Definiciones
- Aparición: presencia en el once inicial o entrada por sustitución; no basta estar en el banquillo.
- Minutos: reloj reglamentario calculado a partir de timestamps de cada periodo; descuento eliminado. Incluye prórroga si existe. Sustitución y roja terminan exposición. No se descuentan salidas temporales por lesión. No son minutos oficiales exactos.
- Goles: eventos Shot con outcome Goal; excluye tanda de penaltis y autogoles del jugador. Penaltis durante el partido incluidos.
- Asistencia: bandera goal_assist de StatsBomb, no mezcla definiciones de otros proveedores.
- Pases clave: bandera shot_assist; pases que generan disparos, no únicamente los que no terminan en gol.
- xG: valor original StatsBomb, no un modelo propio entrenado por el proyecto.
- Tasa por 90: 90 × suma del indicador / suma de minutos. Nunca promediar las tasas de cada partido.
- Edad: días desde el nacimiento / 365.2425; por temporada se muestra el promedio de edad de las apariciones.
- Distancia del disparo: normalización de coordenadas 120×80 a un campo supuesto 105×68 metros; aproximación, no medición real del estadio.

## ML
Clustering KMeans sobre tasas de goles, asistencias, disparos, pases clave, regates y pases. Solo temporadas de clubes con 450 minutos o más. StandardScaler, n_init=20, semilla 42. Se exploran k=2..5 y se elige silhouette máximo. Los números de grupo son arbitrarios; no equivalen a etiquetas tácticas. Pocos puntos implican inestabilidad; no confundir clustering con validación de una teoría.

Ridge con edad y edad², escalado dentro de cada fold y alpha=10. Evaluación leave-one-out retrospectiva frente a media del entrenamiento. No estima causalidad ni valida pronósticos futuros: para pronosticar se necesitan splits temporales y datos de muchos jugadores. No extrapolar a edades sin observación.

## Índice
Percentiles dentro de cada ámbito entre temporadas elegibles. Pesos iniciales goles .40, asistencias .25, pases clave .20, xG .15. Componentes correlacionados: puede premiar dos veces producción similar. El usuario puede cambiar pesos; no es un ranking universal. Una nueva temporada cambia la referencia del percentil.

## Equipo on/off
Se comparan goles y xG del equipo por minutos reglamentarios con el jugador presente/ausente dentro de partidos cubiertos con una aparición. Las fronteras se infieren de sustituciones y tarjetas; un evento justo en el mismo timestamp es ambiguo y se asigna al intervalo activo. No existe grupo de control representativo: parte del archivo de origen se seleccionó por participación de Messi. No afirmar que Messi causó la diferencia.

## Publicación
Distinguir datos de liga, torneos internacionales y títulos. No sumar selectivamente para llamar a un resultado «total de carrera». El umbral de minutos reduce ruido, no elimina sesgos por competición o edad. Cada publicación debe conservar revisión fuente, filtros, denominador, fecha y atribución de StatsBomb.

## Referencias técnicas
- Streamlit: https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
- OpenAI function calling: https://developers.openai.com/api/docs/guides/function-calling
- Estadísticas fuente: https://github.com/statsbomb/open-data

## Conciliación de cobertura
La revisión procesada produce 519 apariciones de Barcelona, 58 de PSG, 6 de Inter Miami y 16 de Argentina. Los partidos candidatos sin aparición se excluyen. Estos conteos son de la revisión fuente, no una validación de toda la carrera. Por ejemplo, 2007/2008 contiene 27 apariciones y 8 goles en los eventos disponibles: verificar contra un registro oficial antes de usarlo como total de esa temporada. No se rellenan registros faltantes con cifras inventadas.
