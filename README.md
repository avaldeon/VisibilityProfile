# Visibility Profile Plugin

![Plugin Logo](https://github.com/avaldeon/VisibilityProfile/blob/main/logo.png) 

## Descripción

El plugin **Visibility Profile** genera imágenes que muestran el perfil del terreno entre dos puntos: el observador y el objetivo, teniendo en cuenta la altura de ambos elementos, mostrando así si el objetivo es visible o no.

## Características

- **Cálculo de Línea de Visión**: El plugin añade líneas de visión directas entre los elementos, así como la línea de visión con el terreno en el ángulo más alto.
- **Visualización del Elemento Observado**: Muestra la proporción del elemento visible observado, así como la visibilidad del mismo a lo largo de la línea entre los dos puntos (es decir, si acercamos el objetivo al observador desde la ubicación inicial), utilizando un gráfico que se llena en tres colores.
  - **Visibilidad Completa**: Si en cada punto se ve el elemento en su totalidad (el terreno es visible). Color verde.
  - **Visibilidad Parcial**: Si solo se ve parcialmente. Color amarillo.
  - **No Visible**: Si el objeto no es visible (queda totalmente oculto por la topografía). Color rojo.

## Requisitos

Para utilizar el plugin, necesitas las siguientes capas de origen:

- **Capa DEM Raster**: Un modelo digital de elevación.
- **Capa de Puntos**: Debe contener un campo llamado `tipo_punto` de tipo numérico, donde:
  - 0: representa el observador.
  - 1: representa el objetivo.

## Instalación

Instrucciones sobre cómo instalar el plugin.

## Uso

Guía rápida sobre cómo utilizar el plugin.

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas contribuir, por favor sigue estos pasos...

## Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

## Contacto

Para más información, puedes contactar a [tu nombre](mailto:tu-email@example.com).
