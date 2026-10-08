# Messi Role Finder

Unidad: jugador-equipo-competición-temporada. Se amplía la extracción a todos los participantes de los partidos de clubes ya cubiertos por el pipeline de Messi (misma revisión StatsBomb). No se descargan jugadores de selecciones. Cada equipo de un jugador transferido se conserva por separado, aunque el ranking muestra una sola entrada por jugador.

Características por 90: xG sin penaltis, disparos (incluyen penaltis del partido), pases que asisten disparos, xA (suma del xG de los remates vinculados; incluye penaltis si están vinculados), pases completos al área, pases completos que avanzan al menos 12 unidades longitudinales StatsBomb y regates completados. “Progresivo” es una definición operacional propia, no la métrica comercial de un proveedor. Un pase dentro del área también puede contar como pase al área. Se excluyen tandas, se incluyen prórrogas. Minutos reglamentarios estimados, sin descuento, coherentes con el pipeline existente. No se calculan edades desconocidas. Se falla ante xG ausente o asistencias de remate sin enlace, en lugar de imputar cero.

Escalado StandardScaler ajustado sobre los otros perfiles de la misma competición-temporada; Messi se transforma con ese escalador. La distancia es euclídea estandarizada dividida por raíz del número de métricas. Pesos iguales; no produce porcentajes de compatibilidad. No representa calidad absoluta. Algunas variables están correlacionadas: el ranking depende de las características seleccionadas.

KMeans elige exploratoriamente k=2..4 por silhouette entre los otros perfiles. Se reporta el mínimo ARI frente a tres semillas adicionales. PCA se ajusta sobre los otros perfiles y reporta la varianza explicada; la proyección no conserva toda la geometría. No es validación predictiva ni estabilidad frente a cambios de partidos/muestra. Los clusters no se etiquetan como roles tácticos demostrados. Creación/finalización/mixto son subconjuntos elegidos por el usuario para comparar, no etiquetas aprendidas.

Mínimo por defecto: 450 minutos en los partidos observados. Mínimo de ocho otros perfiles por cohorte; si no se cumple se muestra un aviso. Inter Miami puede carecer de suficientes minutos/pares en la muestra de 2023. Cada temporada es una referencia independiente; no se promedia Barcelona con PSG/Miami.

Limitación principal: selección de partidos condicionada a apariciones de Messi. Sus compañeros tienen más exposición que muchos rivales; no es una población completa de liga. No ajustar por fuerza de liga/posesión significa que no se hacen rankings transversales entre ligas. El siguiente paso para scouting general sería incorporar temporadas completas y verificar cobertura, minutos oficiales, sensibilidad al umbral y normalización por contexto. No se publican parejas como “reemplazos”: su complementariedad necesitaría una definición y validación adicionales.

Salidas reproducibles (ignoradas por git): artifacts/role_finder/club_profiles.csv y report.json. Reejecutar con --min-minutes para análisis de sensibilidad. Datos de investigación no comercial: mantener créditos y condiciones StatsBomb. No se incluyen eventos crudos en el repositorio.

## Ejecución comprobada

La ejecución sobre el caché disponible procesó **583 partidos de clubes**, produjo **354 perfiles jugador-equipo-temporada** con el umbral de 450 minutos y **18 referencias elegibles de Messi**.

Ejemplo descriptivo del modo mixto (menor distancia estandarizada = más parecido dentro de la cohorte):

| Referencia | Primeros perfiles de la muestra | Distancias |
|---|---|---|
| Barcelona, La Liga 2020/21 | Dembélé; Coutinho; Trincão | 1,705; 2,284; 2,338 |
| PSG, Ligue 1 2022/23 | Neymar; Mbappé; Hakimi | 1,073; 1,280; 2,069 |

Estos nombres reflejan el universo incompleto de partidos cubiertos y el conjunto de métricas seleccionado. No son recomendaciones de fichaje ni sucesores demostrados; un primero del ranking puede seguir siendo bastante distinto a Messi. Comparar también los modos de creación y finalización y la exposición de cada jugador.
