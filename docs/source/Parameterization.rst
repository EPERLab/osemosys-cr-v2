Parameterization
=====

Exogenous demands
------------

Add distance Equation here

.. table:: 
   :align:   center
   
+-----------------+--------------------------------------------+
| Code            | Name                                       |                                                                 
+=================+============================================+
| CO2_sources     | Carbon Dioxide from primary sources        |                                                                      
+-----------------+--------------------------------------------+
| CO2_transport   | Carbon Dioxide from transport              |                                                                      
+-----------------+--------------------------------------------+
| CO2_AGR         | Carbon Dioxide from agriculture            |                                                                         
+-----------------+--------------------------------------------+
| CO2_COM         | Carbon Dioxide from the commercial sector  |                                                                         
+-----------------+--------------------------------------------+
| CO2_IND         | Carbon Dioxide from the industrial sector  |                                                                         
+-----------------+--------------------------------------------+
| CO2_RES         | Carbon Dioxide from the residential sector |                                                                         
+-----------------+--------------------------------------------+
| CO2_Freigt      | Carbon Dioxide from freigt transport       |                                                                         
+-----------------+--------------------------------------------+
| CO2_HeavyCargo  | Carbon Dioxide from heavy cargo            |                                                                         
+-----------------+--------------------------------------------+
| CO2_LightCargo  | Carbon Dioxide from light cargo            |                                                                         
+-----------------+--------------------------------------------+

.. table:: 
   :align:   center
+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+
| Model component                                                                    | Source                                                                                                                                                 |
+====================================================================================+========================================================================================================================================================+
| Occupancy rates                                                                    | We use a national transport survey from 2013 [11]                                                                                                      |
+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+
| Driven distance by vehicle type                                                    | Costa Rica's technical revision entity [12]                                                                                                            |
+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+
| Energy intensity by demand sector                                                  | Costa Rica's energy balances [13]                                                                                                                      |
+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+
| Gross Domestic Product to drive demands and normalize expense and revenue results  | We use official and publicly available GDP time series[20] and assume that all costs are in USD using the reported yearly average exchange rate [21].  |
+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------+


.. figure:: images/parameterezation.png
   :align:   center
   :width:   700 px

   Figure 3: Exogenous and endogenous variables


.. math::

   V_{k,y}=\frac{D_{k,y}}{d_{k,y}\cdot OR_{k,y}}

*Table X.* Model input references for demand modeling.

% Table generated by Excel2LaTeX from sheet 'Hoja1'
\begin{table}[htbp]
  \centering
  \caption{Model input references for demand modeling}
    \begin{tabular}{p{8.665em}p{12.11em}}
    \textbf{Model component} & \textbf{Source} \\
    \midrule
    Occupancy rates & We use a national transport survey from 2013 [11] \\
    \midrule
    Driven distance by vehicle type & Costa Rica's technical revision entity [12] \\
    \midrule
    Energy intensity by demand sector & Costa Rica's energy balances [13] \\
    \midrule
    Gross Domestic Product to drive demands and normalize expense and revenue results & We use official and publicly available GDP time series[20] and assume that all costs are in USD using the reported yearly average exchange rate [21]. \\
    \end{tabular}%
  \label{tab:addlabel}%
\end{table}%

Fleet composition assumptions
------------

Explain how to parameterize the BAU


Primary technologies
------------

Explain technologies, parameters, and assumptions

*Table X.* Model input references for primary technologies.

.. table:: 
   :align:   center

| **Model component**                                                         | **Source**                                                                                                                                                                                                   |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| LPG infrastructure characterization                                         | U.S. Department of Energy \[8\]                                                                                                                                                                              |
| Biofuel blend for biodiesel and ethanol                                     | RECOPE's (the national fuel state-owned monopoly) biofuel strategy \[15\]                                                                                                                                    |
| International fuel prices: present and projection                           | National statistics from RECOPE's website \[16\] for years up to 2020, and the trajectory of oil prices suggested by the IEA in the 2019 World Energy Outlook \[17\], which we take at 1.9% growth annually. |
| Capacity factor of bioenergy power generation in 2050                       | We model a transition from a bagasse-based option with energy balance to IRENA's characterization \[18\]<sup>.</sup>                                                                                         |
| Capacity factor and costs of geothermal, hydro run-of-river, and dam        | Personal communication with the Instituto Costarricense de Electricidad (ICE)                                                                                                                                |
| Future capacity factors aligned with the National Generation Expansion Plan | ICE's 2019 Generation Expansion Plan \[19\]                                                                                                                                                                  |


Secondary, transport, and other technologies
------------

Explain technologies, parameters, and assumptions

*Table X.* Model input references for secondary, transport, and other technologies.
.. table:: 
   :align:   center

| **Model component**                       | **Source**                                                                                                                                                       |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hydrogen charging infrastructure          | The International Council on Clean Transportation \[6\]                                                                                                          |
| Hydrogen electrolyzer characterization    | IRENA'S "Hydrogen from renewable power: outlook for the energy transition" \[7\]                                                                                 |
| Freight rail costs and energy consumption | Report for the Netherlands on costs per ton-kilometer \[9\] and rail electricity consumption from Spain \[10\]; there is no detailed information for Costa Rica. |
| Fleet characterization and vehicle costs  | Costa Rica's Ministry of Finance (personal communication; dataset unavailable).                                                                                  |
| Passenger rail and urban interventions    | Financial analysis of Costa Rica's passenger rail project \[14\]                                                                                                 |

