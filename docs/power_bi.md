# Power BI
1. Ejecutar el pipeline y abrir Obtener datos → Texto/CSV.
2. Importar season_stats.csv, player_match_stats.csv y shots.csv.
3. Definir player_id/match_id como identificadores; season como texto; date como fecha.
4. Relaciones: crear una dimensión de partidos desde los match_id únicos y relacionarla 1:* con estadísticas y disparos. No unir season_stats directamente con shots mediante season: multiplica registros.
5. Usar medidas con suma de numeradores y denominadores:
```dax
Goles por 90 = DIVIDE(SUM(player_match_stats[goals]) * 90, SUM(player_match_stats[minutes]))
Asistencias por 90 = DIVIDE(SUM(player_match_stats[assists]) * 90, SUM(player_match_stats[minutes]))
Partidos = DISTINCTCOUNT(player_match_stats[match_id])
```
Añadir filtros de scope, team y competition. Mostrar aviso de cobertura, fuente StatsBomb y su logo. No hay un .pbix incluido: esta guía permite construirlo desde las exportaciones.
