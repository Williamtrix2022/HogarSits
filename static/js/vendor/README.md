# Bibliotecas de terceros (copiadas al proyecto)

Se sirven desde el mismo dominio, sin depender de un CDN en tiempo de ejecución. Git **no convierte** sus saltos de línea (`.gitattributes`: `static/js/vendor/** -text`), para que la huella siga siendo verificable.

| Archivo | Versión | Licencia | Origen |
|---|---|---|---|
| `chart.umd.min.js` | Chart.js 4.4.7 | MIT | https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js |

## Huellas SHA-256
| | SHA-256 |
|---|---|
| **Original** (tal como lo publica el origen) | `206b6e8bb00fc7bba2c7ee80ca41db3e9e05ba7be0aa35abeba9cfd5357f5d0e` |
| **Copia en este repositorio** (con la modificación de abajo) | `42f4dbfe70c430ffc22c7128f36cae8d599cac90b8cd37c8f42a59e565e5deb7` |

## Única modificación
Se eliminó la **última línea**, `//# sourceMappingURL=chart.umd.js.map`, y el salto de línea que la precede (queda un único `\n` final). Es un mapa de depuración que no se copia al proyecto, y `collectstatic` en producción (almacenamiento con manifiesto de WhiteNoise) **se niega a recoger** un archivo que referencia otro inexistente: sin este cambio la imagen de producción no se construye. No altera el código de la biblioteca.

## Cómo verificarlo
1. Descargar el original del origen y comprobar que su SHA-256 es el de la fila «Original».
2. Quitarle la última línea como se describe arriba y comprobar que da la fila «Copia».
3. `tests/test_produccion.py::test_la_biblioteca_copiada_coincide_con_su_huella_documentada` lo hace automáticamente con la copia del repositorio.

## Para actualizar
Descargar la versión nueva del mismo origen, **verificar la licencia**, repetir la modificación, actualizar las dos huellas de esta tabla y comprobar los gráficos del panel de análisis.
