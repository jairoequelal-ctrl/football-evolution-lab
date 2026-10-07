# Diccionario de datos
| Tabla | Clave | Contenido |
|---|---|---|
| player_match_stats | player_id + match_id | Equipo, rival, fecha, edad, exposición y producción ofensiva |
| season_stats | player_id + scope + team + competition + season | Sumas de eventos y tasas por 90 |
| shots | event_id | Disparo, coordenadas, resultado, xG, parte del cuerpo y distancia aproximada |
| honours | player_id + team + competition + season | Títulos verificados y URL fuente; catálogo inicial parcial |
| manifest | source_revision | Revisión, cobertura, fallos, definición de minutos y SHA256 |

scope: club / national. team: equipo del jugador, no ganador del partido. season se conserva como string del proveedor. games cuenta apariciones en los partidos cubiertos. Los valores faltantes se mantienen vacíos; no se inventan coordenadas ni se imputan con cero. Las columnas *_p90 usan minutos de exposición reglamentaria; xg ya viene modelado por StatsBomb. player_id es el identificador del proveedor.

Los CSV se generan localmente. Para un catálogo futuro de varios jugadores, incorporar players (ID, nombre, nacimiento, fuente), sources (proveedor, licencia, revisión) y separar matches de player_match_stats. Nunca unir por nombre sin resolver identidades.
