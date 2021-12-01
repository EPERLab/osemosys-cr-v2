.. _chapter-ModelStructure:
Model structure
=====

The model structure is a group of interconnected technologies through energy
carriers that satisfy demands. Figure 2 illustrates the technological setup.

.. figure:: images/model_structure.png
   :align:   center
   :width:   700 px

   Figure 2: Energy supply chain modeled in OSeMOSYS-CR for this analysis.


The secondary energy sources are fossil fuels, electricity, and hydrogen. First,
fossil fuels are all imported. Second, power plants generate electricity with
renewables or burning fossil fuels. In turn, electricity is used to produce
hydrogen. The secondary energy carriers are then transported for distribution.
Distributed power generation feeds the demand without transmission and distribution losses.

We model transport and industry technologies in detail, which consume energy
and transform it into mobility or heat, force, or electrical end-uses. The
agricultural, commercial, residential, and public services consume final energy
directly, having a more straightforward modeling structure.

We consider emission reductions from biofuel blends as in the first model
version [1]: CO2 equivalent (CO2e) emission factors decrease proportionally to
the biofuel share of the blend. Also, relative cost differences between biofuels
and conventional fuels are not considered. Finally, off-road, maritime, and
air transport are not modeled here.

This version's temporal resolution is yearly and covers the period between
2018 and 2050, with only one region (i.e., Costa Rica) and one mode of operation.

Creating the model structure
------------

For a fast model interconnection following the reference energy system (RES)
of Figure 2, we use multiple Microsoft Excel files inside the ``A1_Inputs folder``
(see Figure 1):

-	A-I_Horizon Configuration.xlsx (file 1): it configures the initial and last
   years of the analysis period. This file is straightforward to complete.
- A-I_Clasiffier_Modes_Demand.xlsx (file 2): specifies the demand sectors and
  their modeling approach. Table 1 shows how to specify the sectors and their approaches.

*Table 1.* Modeling approach per sector in sheet Sectors of file 2.

.. table:: 
   :align:   center
+--------------+----------------+--------------------+
| Sector code  | Sector         | Modeling approach  |
+==============+================+====================+
| AGR          | Agriculture    | Simple             |
+--------------+----------------+--------------------+
| COM          | Commercial     | Simple             |
+--------------+----------------+--------------------+
| IND          | Industrial     | Detailed           |
+--------------+----------------+--------------------+
| PUB          | Public Sector  | Simple             |
+--------------+----------------+--------------------+
| RES          | Residential    | Simple             |
+--------------+----------------+--------------------+
| TRN          | Transport      | Detailed           |
+--------------+----------------+--------------------+
| EXP          | Exports        | Simple             |
+--------------+----------------+--------------------+

Sectors with simple approaches demand final energy in Petajoules. Detailed
sectors have more transformation stages. Figure 3 shows the fuels used in the
sectors with a simple approach and lists the energy carriers demanded by the
energy system. Unmarked energy carriers are used only in detailed sectors.

.. figure:: images/fuels_per_sector.png
   :align:   center
   :width:   700 px

   Figure 3: Fuels per sector with a simple modeling approach in sheet
   Fuel_per_Sectors of file 2.
