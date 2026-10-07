# Investigación y diseño editorial

Inspiración: https://theanalyst.com/articles/lionel-messi-greatest-player-of-all-time-debate-settled-world-cup-2026

Se incorporan participación relativa en disparos, separación de creación y remate, cuadrículas comparables y piezas originales con foto y una conclusión por imagen. Las figuras y cifras de Opta no se copian: proveedores, cobertura y convenciones son distintos. Este proyecto no contiene eventos del Mundial 2026.

## Ejecutar desde la raíz

```bash
pip install -e '.[dev]'
bash scripts/build.sh
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python research/analyze.py
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python research/editorial.py
streamlit run app.py
```

Los resultados se escriben en artifacts/research y artifacts/editorial. Los datos originales se descargan con el pipeline y no se redistribuyen. research/assets/messi.jpg es una fotografía real de 2022 empleada de forma ilustrativa, incluso en gráficas de Barcelona; no documenta la temporada representada.

## Créditos de la fotografía

Autor: Hossein Zohrevand / Tasnim News Agency.
Ficha: https://commons.wikimedia.org/wiki/File:Lionel_Messi_WC2022.jpg
Licencia: https://creativecommons.org/licenses/by/4.0/
Original: https://upload.wikimedia.org/wikipedia/commons/c/c8/Lionel_Messi_WC2022.jpg
Uso: redimensionado para integrarlo en una composición original; sin implicar patrocinio. Al compartir, conservar el crédito en la imagen y añadir ficha y licencia al pie de publicación.

## Participación en disparos

Numerador: unión de IDs de disparos de Messi y disparos de Argentina asistidos mediante pases de Messi con shot_assist y assisted_shot_id válido. Cada disparo se cuenta una vez. Denominador: todos los disparos de Argentina en cada encuentro cubierto, periodos 1–4, excluidas tandas. Incluye minutos sin Messi; no se limita a su exposición personal. No mide causalidad ni combina datos Opta.

2018: cuatro partidos, 18 disparos propios + 8 asistidos = 26 de 58 (44,8%).
2022: siete partidos, 32 propios + 16 asistidos = 48 de 101 (47,5%).
La diferencia es descriptiva; no se interpreta como significativa ni independiente del calendario.

Las cuadrículas muestran disparos, no todos los toques. El mismo color representa el mismo recuento en ambos paneles. El tamaño de muestra y duración de torneos difieren; no equivalen a tasas por 90.

## Pendientes científicos

Conciliar un partido y dos goles de Barcelona; estimar minutos con descuento; validación con edad fijada al inicio; comparar varias carreras y controlar contexto. Las categorías K-means y el índice compuesto siguen siendo exploratorios. El paper v1 no se ha revisado por pares.
