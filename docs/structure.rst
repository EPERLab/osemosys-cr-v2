OSeMOSYS-CR-v2 execution in steps
=====

La finalidad de esta sección es definir los parámetros de entrada para el
modelo. En :doc:`scenarios` se define cómo se van a conectar cada uno de
los modelos.

Al finalizar el llenado de todos los archivos enumerados enseguida se debe
ejecutar el script de python con nombre ``A1_Model_structure``.

.. _RES:

RES
------------
La RES es el primer paso para tener claro la estructura de modelo que se va a 
tener. En ella se incluye la información sobre la oferta y demanda,
además en este paso se especifica el nivel de detalle con el que se desean
parametrizar cada uno de los sectores.

Para configurar la estructura se deben modificar los archivos presentes en la 
carpeta ``A1_inputs``, donde en los siguientes archivos se cambian ciertos parámetros, 
tal y como se enumera enseguida:
*	*A-1_Horizon Configuration* se configura el período que se desea analizar.
*	*A-1_Clasiffier_Modes_Demand* especifica qué sectores existen y la forma en que
se van a modelar.
*	*A-1_Modes_Transport* debido a que el transporte se va a modelar de forma detallada (compleja),
sus parámetros se configuran en este archivo.
*	*A-1_Classifier_Modes_Supply* detalla cómo se produce cada una de las fuentes
de energía necesarias para satisfacer la demanda.

En las siguientes secciones se detalla la información que debe presentarse en cada
uno de los archivos anteriormente listados.

A-1_Clasiffier_Modes_Demand
----------------

Este archivo presenta varias hojas. En la hoja ``Sectors`` se detalla cuáles
sectores existen, y si se van a modelar de forma detallada, o en su defecto, simple.
En caso de que el modelo sea simple, se utilizan unidades de energía final (J), mientras
que si es detallado, 

Por su parte, en la hoja ``Fuel_per_Sectors`` se encuentra una matriz que especifica qué combustibles se van
a utilizar por sector, utilizando como etiqueta del sector el código dado en la
hoja ``Sectors``. Por ejemplo, el sector comercial podría utilizar Gasolina, Gas LPG, leña,
entre otros.

De forma análoga al código que tienen los sectores, la materia prima utilizada
para generar energía se especifica en la hoja ``Fuel_to_Code``.


A-1_Modes_Transport
----------------
Este archivo debe ser llenado para todos aquellos casos en que su modelado sea
detallado. En este caso de ejemplo, la única demanda que se modelará de esta forma
será la del transporte, la cual será tomada a modo de ejemplo.

En la hoja ``Mode_Broad`` se especifican las demandas finales (de carga o de
pasajeros) y los distintos tipos de vehículos que pueden satisfacer dicha demanda.
Por ejemplo, automóviles, camiones, buses, motos, entre otros.

Por su parte, en la hoja ``Dem_to_Code`` se especifican los códigos utilizados para
cada demanda existente en la hoja ``Mode_Broad``.

Asimismo, en la hoja ``Mode_per_VehFuel`` se detalla la tecnología que tiene cada uno
de los vehículos que puede satisfacer la demanda, que son los presentes
en la hoja ``Mode_Broad``.

La hoja ``Fuel_per_VehFuel`` presenta la fuente de energía que puede tener cada
tecnología de vehículo mostrada en la hoja ``Mode_per_VehFuel``. Por ejemplo,
los híbridos pueden tener la gasolina y la electricidad como fuente de energía,
mientras que los vehículos de gasolina tendrían a la gasolina como combustible.

A-1_Classifier_Modes_Supply
----------------

En la hoja ``Primary_Energy`` especifica todas las tecnologías que pueden producir
cierto vector energético sin necesidad de tener una entrada. Por ejemplo, la electricidad
puede obtenerse de varias fuentes, como la solar, el viento, electricidad, entre otras.

Además, se debe especificar cómo se produce este vector energético, ya sea 
importación, extracción, transformación, entre otros. Esta información debe completarse
en esta hoja. 

Al completar todas las columnas para una fila en específico queda claro qué
vector energético produce cada tecnología.

Además, en la hoja ``Secondary_Energy`` se completa cómo se transforma cada
energía antes de ser transportada. Por ejemplo, en esta hoja se podría definir
que el diesel no se transforma antes de ser transportada, mientras que la electricidad
sí se transforma mediante el sistema de transmisión y distribución.

Terminé en el minuto 11.
