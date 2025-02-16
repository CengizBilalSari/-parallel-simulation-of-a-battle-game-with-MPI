
import numpy as np
from mpi4py import MPI
import pickle
from grid import Grid
from unit import Earth, Fire, Water, Air, Unit

# Function to parse the input file and extract all of the parameters
def parse_input_file(file_name):
    #take the file and the first line gives N,R,M,T
    with open(file_name,"r") as file:
        first_line= file.readline().strip()
        N,W,T,R= map(int,first_line.split())
        content= file.read().strip().split("Wave")[1:]
        waves=[]
        #take we waves from the rest part of the file
        # the wave is an array which includes 4 array for the E,F,W,A in this sequence.
        # every element of an wave includes coordinate tuples for specific location.
        for wave in content:
            lines = wave.strip().split("\n")
            wave_data = [[], [], [], []]
            for line in lines[1:]:
                unit_type, coordinates= line.split(":")
                unit_type= unit_type.strip()
                coordinate_tuples= [tuple(map(int, coordinate.split())) for coordinate in coordinates.split(",")]
                if unit_type == "E":
                    wave_data[0] = coordinate_tuples
                elif unit_type == "F":
                    wave_data[1] = coordinate_tuples
                elif unit_type == "W":
                    wave_data[2] = coordinate_tuples
                elif unit_type == "A":
                    wave_data[3] = coordinate_tuples
            waves.append(wave_data)
    #the function returns N,R,M,T and waves  so that we have all things we need at the end of this function from the file.
    return waves, N,W,T,R

# Function to place units from a wave onto the grid
def place_units_on_grid(grid, wave,i):
    row_number= len(grid.grid)
    col_number= len(grid.grid[0])
    # the waves will be placed in the grid according to this function.
    for coordinates in wave[i][0]:
        if  coordinates[0]>=0 and coordinates[1]>=0 and  coordinates[0]<row_number and coordinates[1]<col_number:
            if grid.grid[coordinates[0]][coordinates[1]].unit_type=="neutral":
                grid.set(coordinates[0], coordinates[1], Earth())
    for coordinates in wave[i][1]:
        if  coordinates[0]>=0 and coordinates[1]>=0 and  coordinates[0]<row_number and coordinates[1]<col_number:
            if grid.grid[coordinates[0]][coordinates[1]].unit_type=="neutral":
                grid.set(coordinates[0], coordinates[1], Fire())
    for coordinates in wave[i][2]:
        if  coordinates[0]>=0 and coordinates[1]>=0 and  coordinates[0]<row_number and coordinates[1]<col_number:
            if grid.grid[coordinates[0]][coordinates[1]].unit_type=="neutral":
                grid.set(coordinates[0], coordinates[1], Water())
    for coordinates in wave[i][3]:
        if  coordinates[0]>=0 and coordinates[1]>=0 and  coordinates[0]<row_number and coordinates[1]<col_number:
            if grid.grid[coordinates[0]][coordinates[1]].unit_type=="neutral":
                grid.set(coordinates[0], coordinates[1], Air())


# Function to check and apply inferno effect for Fire units at the grid boundary
def check_for_inferno_boundary(grid_part,is_destroyed,row,column,unit_type):
     if unit_type =="Fire" and is_destroyed:
          if  grid_part[row][column].inferno== False:
            grid_part[row][column].apply_inferno()
            grid_part[row][column].inferno= True # until the next round

# Function to check and apply inferno effect during normal attacks
def check_for_inferno(grid_part,row, column ,target_row,target_column,attack_power,unit_type):
    if unit_type =="Fire" and  grid_part[target_row][target_column].health- attack_power<=0:
         if  grid_part[row][column].inferno== False:
            grid_part[row][column].apply_inferno()
            grid_part[row][column].inferno= True # until the next round

# Function to partition the grid into stripes and send to processes
def striped_partitioning(processor_number,grid,grid_size,comm):
    rows_assigned= int(grid_size/processor_number)
    for i in range(0,processor_number):
        start_row = i * rows_assigned
        end_row = (i + 1) * rows_assigned
        rows_data = np.array([row for row in grid.grid[start_row:end_row, :]])
        serialized_data = pickle.dumps(rows_data)
        data_size = np.array([len(serialized_data)], dtype=np.int32)  
        comm.Send([data_size, MPI.INT], dest=i + 1)
        comm.Send([serialized_data, MPI.BYTE], dest=i + 1)
