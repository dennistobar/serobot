# SeroBOT

SeroBOT es un bot que revierte ediciones vandálicas usando [ORES](https://mediawiki.org/wiki/ORES) para calificar las ediciones usando los parámetros de `goodfaith`y `damaging` que provee la plataforma.

Este bot está disponible bajo licencia MIT

## Instalación

Este script requiere de [pywikibot](https://mediawiki.org/wiki/pywikibot) para funcionar, por lo cual se deben seguir los pasos de instalación de pywikibot. Además requiere [pandas](https://pandas.pydata.org/) para hacer el filtrado del log más eficiente y fácil de entender.

Para las dependencias, se deben instalar lo siguiente:
`pip3 install sseclient requests pandas`

Una vez hecho, se debe clonar el repositorio y ejecutar el script `python pwb.py <carpeta>/main` para comenzar la ejecución del bot.

## Coopera

Para cooperar con la construcción del bot, puede hacer pull request o reportar un [issue nuevo](https://github.com/dennistobar/serobot/issues/new) en [github](https://github.com/dennistobar/serobot.git)
