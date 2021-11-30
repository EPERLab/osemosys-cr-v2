.. _chapter-OSeMOSYS-CR-v2-execution-guide:
OSeMOSYS-CR-v2 execution guide
=====

The prerequisites to execute the model and tools are i) the Anaconda Python package,
ii) the GLPK solver, iii) the OSeMOSYS GNU Mathprog version (access the source folder).
To access the OSeMOSYS-CR-v2 scripts, visit the GitHub repository and download the
**mmf_tier1** folder. Users can rename the folder and copy and paste it to build multiple analyses.

The tools are functional in Windows 10 operating systems; adjustments may be necessary for
other operating systems Users can use Anaconda's Spyder or other execution platforms to
run the Python files. Here we summarize the modeling and execution process
with the support of Figure 10:

1.	Identify the reference energy system (RES) of interest, defining sectoral
demands, supply options, and transformation technologies. Pick the modeling
approach for every sector; our framework only supports detailed versions for
transport and industry.

2.	Complete the files inside the A1_Inputs folder following Section 2.1.

3.	Execute A1_Model_Structure.py and edit the format of the files created
inside A1_Outputs folder using Microsoft Excel to increase clarity and manipulate the tables.

4.	Complete the technology interconnections using the files inside A1_Outputs and following Section 2.2.

5.	Define the additional sets using files inside A2_Extra_Inputs following Section 2.3.

6.	Parameterize all the files inside A1_Outputs following Section 3.

7.	Execute the A2_Compiler.py as explained in Section 2.4.

8.	Create the scenarios following the process explained in Section 4.
Remember to copy and paste each parameter's comma-separated file from A2_Output_Params to B1_Output_Params.

9.	Once the scenarios are parameterized, execute B1_Base_Scenarios.py.
Make sure the folder Executables exists inside the project's folder. 
he OSeMOSYS_model.txt (see Figure 1) file is available in its repository.
We advise this file to be executed in Spyder with the configuration
"Console: Execute in an external system terminal" and "External system terminal:
Interact with the Python console after execution".

10.	Execute the B2_Results_Creator_f0.py to create the results files in wide format
(i.e., each data variable has a column), named f0_OSMOSYS_CR_Output.csv and f0_OSMOSYS_CR_Input.csv.


All input, output, and parameter-based files for the research article are in
the GitHub repository.

.. figure:: images/execution_guide.png
   :align:   center
   :width:   700 px

   Figure 10: Diagram of supporting software tools of OSeMOSYS-CR-v2.