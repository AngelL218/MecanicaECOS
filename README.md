# EcoSuelo: simulador de humedad del suelo

Aplicación de escritorio para un proyecto escolar de monitoreo de humedad.
Permite configurar un terreno, dividirlo en bloques, ver sus centros, generar
rutas en zigzag y explorar lecturas ficticias. **No se conecta a sensores,
Arduino, ESP32, motores ni otros dispositivos.**

## Requisitos e instalación

- Python 3.9 o posterior.
- Tkinter, incluido en las instalaciones estándar de Python para Windows.
- No se necesitan paquetes externos. La gráfica de estadísticas no se incluye
  en esta primera versión; por eso no hace falta instalar Matplotlib.

Comprueba que Python esté disponible desde PowerShell o la terminal:

```powershell
python --version
```

En Windows, si el comando `python` no está configurado, también puedes probar:

```powershell
py --version
```

## Ejecutar

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
python main.py
```

O, si utilizas el lanzador de Python:

```powershell
py main.py
```

## Uso de la aplicación

Puedes arrastrar el separador vertical entre el panel de controles y las
pestañas para ajustar cuánto espacio ocupa cada lado. El contenido se adapta
al cambiar el tamaño de la ventana.

1. En **Configuración del terreno**, escribe el nombre, el largo (eje X), el
   ancho (eje Y) y el tamaño de los bloques. Las medidas deben ser mayores que
   cero. Si una dimensión no es múltiplo del bloque, el bloque del borde se
   recorta para no salir del terreno.
2. Selecciona **Generar terreno**. El mapa muestra bloques a escala, su número,
   el centro de medición y, cuando hay espacio, sus coordenadas X e Y. Las
   coordenadas comienzan en la esquina inferior izquierda. El punto verde
   oscuro indica el centro exacto.
3. Pulsa **Generar ruta zigzag** para dibujar la ruta que visita todos los
   bloques. **Mostrar / ocultar ruta** alterna su visualización. Las flechas y
   los números marcan el sentido y el orden de visita.
4. Ajusta los límites de humedad baja y alta, y pulsa **Aplicar límites**. Los
   límites deben estar entre 0 y 100, y el límite bajo debe ser menor que el
   alto. Los bloques se clasifican como bajos, medios o altos.
5. Pulsa **Simular mediciones** para obtener una nueva lectura ficticia por
   bloque. La lectura en u.a. (unidades arbitrarias, escala 0–1023) y el
   porcentaje derivado son datos aleatorios de prueba; **no representan una
   medición real**. Repite esta acción para realizar otra simulación.
6. En **Resultados y estadísticas** consulta los valores por bloque, el orden
   de la ruta, el promedio, los extremos y el recuento por nivel de humedad.
   Pulsa los encabezados de la tabla para ordenar sus columnas; el porcentaje
   se puede ordenar de menor a mayor o al revés.
7. **Ruta de zonas secas** muestra una ruta zigzag que visita solo los bloques
   clasificados como bajos con los límites actuales. Si no hay bloques secos,
   la aplicación lo informa.
8. **Historial de mediciones** conserva las simulaciones de la sesión actual.
   **Exportar CSV** guarda las lecturas actuales, las dimensiones, las
   coordenadas, el estado y el orden de la ruta (si se generó).
9. **Reiniciar terreno** borra el mapa y las mediciones después de pedir
   confirmación. También se solicita confirmación al reemplazar un terreno
   existente. El botón **Salir** y el control de cierre de la ventana piden
   confirmación antes de cerrar la aplicación.

## Archivos

- `main.py`: aplicación, cálculos del terreno, rutas, simulación, interfaz y
  exportación CSV.
- `test_main.py`: pruebas de división del terreno, límites y ruta serpentina.

Para ejecutar las pruebas desde la carpeta del proyecto:

```powershell
python -m unittest -v
```

La aplicación se mantiene en un solo archivo para que sea fácil de estudiar en
esta primera versión. Si el proyecto crece, las funciones de terreno y rutas
pueden trasladarse a `terreno.py` y `rutas.py`, respectivamente, y la interfaz
a `interfaz.py`.
