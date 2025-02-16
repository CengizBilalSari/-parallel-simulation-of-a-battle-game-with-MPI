# -parallel-simulation-of-a-battle-game-with-MPI

This project includes the following python files:
- helper_functions
- boundary_functions
- unit
- grid
- main

# Running the Project
To run the project, execute the main.py file using the following command, replacing [P] with the appropriate processor number:

mpiexec -n [P] python main.py input.txt output.txt
