.. _chapter-ScenarioModeling:
Scenario modeling
=====

This section explains how to modify each one of the sheets inside B1_Scenario_Config.xlsx
(see Figure 1). The scenario description used for the analysis is inside this
repository's paper: "Prioritizing policy options to transform energy systems:
aligning decarbonization and production sophistication in Costa Rica." The
file consists of nine sheets:

- Scenarios: it defines the scenarios to model in the simulation. Generally,
  there are two main scenarios. One of them is the business-as-usual (BAU)
  scenario where fossil fuels prevail. The other is a decarbonization scenario.
  It has electrification and other measures that make the energy system more efficient.
  Other scenarios derive from the other two.

- Overall_Parameters: it defines the **Initial_Year_of_Uncertainty.** It is a
  parameter that ``B1_Base_Scenarios.py`` uses to start separating demand and
  restriction projections between scenarios.

- Distance_Levers: it changes the distance traveled by every vehicle group.
  By default, this value is 1. The entered value multiplies the 2050 value from
  the parameterization phase. The table in the sheet must specify the scenario
  and the transport group technology.

- Mode_Shift: it is another scenario-specific and technology-specific table.
  Under the "Conext" column, modelers can specify "Demand" or "Technology",
  depending on the set under "Tech_Set". "Demand" sets are used to parameterize
  the mode shift equations presented in the article. The technology sets activate
  or deactivate the entrance of rail transport options.

- Occupancy_Rate: it changes the occupancy rate of a transport group set and
  works like the Distance_Levers sheet.

- TElasticity: changes the **SpecifiedAnnualDemand** parameter of passenger and
  freight demand commodity sets. Hence, any change to demand in a scenario because
  of changes in elasticity of demand must be done exogenously.

- Tech_Adoption: has the same logic as the Mode_Shift but specifies technological
  penetration. Another difference is the "Restriction_Type" column: "Max" fixes
  the **TotalAnnualMaxCapacity** restriction, "Min" the
  **TotalAnnualTechnologyActivityLowerLimit,** and “Min/Max” both.

- Electrical: has a table per scenario and technology. This sheet is reserved
  for technologies in Table 2, which represent power generation technologies.
  Modelers must enter the parameter they want to change: often **TotalAnnualMaxCapacity**
  and **TotalAnnualMinCapacity** to enter a fixed amount of new installed capacity
  or place a cap. Other parameters are **TotalAnnualTechnologyActivityLowerLimit**
  and **TotalAnnualTechnologyActivityUpperLimit** to determine the electricity
  generation per power plant in Petajoules. These two, combined with **CapacityFactor**,
  can reflect a determined operational result. The **ResidualCapacity** parameter
  can be changed to phase-out plants existing in the base year.

- Efficiency: is similar to TElasticity for demand sectors in Petajoule units,
  i.e., the sets with a simple approach demand.

In the following subsections, we elaborate on implementation details not covered in the previous list.

.. _defining-scenarios:

Defining scenarios
------------

The Scenarios sheet has columns "Name" and "Description" to define the scenario.
The scenario can be activated by entering "YES" under the "Activated" column
or a "NO" for an opposite condition.

Only the BAU scenario should have a "YES" under the "Base" column because the
parameterization phase is for the BAU; the rest should have a "NO". If a
scenario is a copy of another, modelers should type "based" under "Reference"
and the reference scenario under the "Based_On" column.

Conversely, if the scenario needs to be specified across all sheets, the
"Reference" scenario must have the name of the scenario itself and the
"Based_On" column must have the string "ref".


.. _modeling-mode-shift:

Modeling mode shift and technology adoption
------------

Here we explain how to populate the common columns in the Mode_Shift and
Tech_Adoption. First, the "Logistic" and "Linear" columns indicate the shape
of the time series. If one of the two columns has a "YES" for a given row,
the other column must have a "NO".

Notably, the values of both sheets are ratios normalized to 1 as 100%.

For a logistic curve, users must specify the "L", "C", and "M": the last value,
the value in the inflection year, and the infection year, respectively. Other
columns are "R2021" and "R2050" which make the curve fit the customary
2021-2050 planning horizon. Edits to the code must be made if the planning
horizon is to change as well.

The linear curves have the option of decadal interpolation. Columns" v_2030",
"v_2040", and "v_2050" are for placing the desired values on each year.
If the modeler only needs an interpolation to 2050, they must type "interp"
on the other columns. The "y_ini" column indicates the year in which the
interpolation starts; values before this year will be the existing under the
initial parameterization (see Section 3) or zero.


.. _modeling-electrical

Modeling the electrical sector
------------

The Electrical sheet has a "Built-in Parameter Set" column: modelers must
enter "NO" if they had not defined the parameter in the parameterization phase
(Section 3.3). If they wish to overwrite the previous value, they must indicate
"YES" under the column. In this sheet, all the values must be "YES" under the "Linear" column.

The" Exact_Years" and "Exact_Values" columns have values separated with semicolons ";".
The string entered must have the same number of years and values. If the parameter
is built-in, the modelers can enter "intact" to leave the parameter unchanged
for the corresponding scenario and technology combination.

The "y_ini" column indicates the start of an interpolation, most useful for
the "intact" option. If it is empty, the last year in the" Exact_Years"
string is the initial year of the interpolation.

The "Milestone_Year" and "Milestone_Value" columns work in tandem: they are
the final value for the parameter (specific to the scenario – technology
combination). These values are multiplied by the "Security_Multiplier" column,
which helps modelers avoid incoherent restriction definitions. The "Unit" column
is informative only. 

The "Method" column specifies instructions about the manipulation of the time
series, separated by semicolons. The options are described below:

- The "Write" and "Overwrite" substrings relate to whether the parameter is
  built-in or not.

- The "Interpolate" option makes a linear interpolation between the last known
  value and the desired value. On the other hand, the "Interpolate_Escalate" value
  fixes the last known value until the year before the target year.

- The "Fix_Last" option fixes the target value for all years after the target year.
  In contrast, the "Fix_Indicated" option leaves a single value under the
  "Exact_Values" column as constant throughout the period.
