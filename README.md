# -parallel-simulation-of-a-battle-game-with-MPI



This project includes the following python files:
- helper_functions
- boundary_functions
- unit
- grid
- main

 This repo presents the implementation of a parallel simulation of an elemental battle using the Message Passing Interface (MPI) framework. The
 simulation models interactions between four factions—Earth, Fire, Water,
 and Air—on an N ×N grid. The objective is to evaluate and simulate faction interactions in a distributed computing environment using efficient grid
 partitioning and inter-process communication strategies.The assumptions included in the project and strategically crucial points are explained in detail.

# Assumptions
 - Unit actions prioritize healing if their health falls below 50%.
- The fire attack power increases if it the enemy unit can be destroyed
 by just its attack.(enemy health- attack power of fire<= 0)
 - All processes synchronize at each phase to ensure consistent state tran
sitions with sending signals to each other .
 -If two Air units tries to move to a same coordinate, they merge. That
 means their attack power and health are summed up but health can’t
 exceed the full health.
 - The Air unit do not calculate the move possibility of other air units
 while calculating the attack number in windrush special ability.
-The special ability of faction Earth reduces incoming damage by 50%
 (rounded down). The attacks are reduced by half for each attack and
 we put the halved damage to attacks queue.
 - The air units could pass just one neutral unit.
 - The number of processors and grid size are given such that grid can be
 divided into worker processors with equal sizes

# Running the Project
To run the project, execute the main.py file using the following command, replacing [P] with the appropriate processor number:

mpiexec -n [P] python main.py input.txt output.txt
