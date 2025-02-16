import numpy as np
from mpi4py import MPI
import pickle
import sys
from grid import Grid
from unit import Earth, Fire, Water, Air, Unit


# Function to receive air unit information from a neighboring process
def take_the_air_info(comm,source_rank):
    data_size = np.zeros(1, dtype=np.int32)
    comm.Recv(data_size, source=source_rank, tag=0)
    data_size = data_size[0]
    serialized_data = bytearray(data_size)
    comm.Recv([serialized_data, MPI.BYTE], source=source_rank, tag=0)
    boundary_data = pickle.loads(serialized_data)
    if boundary_data[0]=="Y":
       return (True,int(boundary_data[1]))
    else:
         return (False,0)  
    
# Function to receive boundary response information from a neighbor process    
def take_the_response_boundary(comm,source_rank):
    data_size = np.zeros(1, dtype=np.int32)
    comm.Recv(data_size, source=source_rank, tag=0)
    data_size = data_size[0]
    serialized_data = bytearray(data_size)
    comm.Recv([serialized_data, MPI.BYTE], source=source_rank, tag=0)
    boundary_data = pickle.loads(serialized_data)
    if boundary_data[0]=="Y" and  boundary_data[1]=="Y":
        return (True,True)
    elif  boundary_data[0]=="Y":
         return (True,False)  
    else:
        return (False,False)
    

# Function to send boundary request data to a neighbor process
def request_boundary_data(comm,source_rank,locations_and_unit_information):
    request_message= pickle.dumps(locations_and_unit_information)
    request_size = np.array([len(request_message)], dtype=np.int32)
    comm.Send([request_size, MPI.INT], dest=source_rank, tag=0)
    comm.Send([request_message, MPI.BYTE], dest=source_rank, tag=0)

# Function to provide boundary data to a requesting process
def provide_boundary_data(comm,grid_part,dest_rank,air_simulation=0):
    request_size = np.zeros(1, dtype=np.int32)
    comm.Recv(request_size, source=dest_rank, tag=0)
    request_size = request_size[0]
    request_message = bytearray(request_size)
    comm.Recv([request_message, MPI.BYTE], source=dest_rank, tag=0)
    request_message = pickle.loads(request_message)
    if request_message== "I am ended.":
         return 0
    # the request is an array of coordinates
    attacked_coordinates=[]
    boundary_data= ["N","N"]  # first N for attak second for destroyed which will be used for inferno
    if request_message[-1][0]=="Air": 
        if request_message[-1][2]==0:
            for i in request_message[0:-1]:
                if i[0]<len(grid_part)and i[0]>=0 and i[1]<len(grid_part[0]) and i[1]>=0: 
                    if grid_part[i[0]][i[1]].unit_type=="neutral":
                        continue
                    elif grid_part[i[0]][i[1]].unit_type=="Air":
                        break
                    else:
                        if not air_simulation:
                            attacked_coordinates.append([i[0],i[1], request_message[-1][1] if grid_part[i[0]][i[1]].unit_type != "Earth" else int(request_message[-1][1]/ 2)])
                        boundary_data[0]="Y" 
                        break
        elif request_message[-1][2]==5:
             attacked_coordinates=[[-1,-1,request_message[0][0],request_message[0][1],request_message[-1][1],request_message[-1][3]]]
             return attacked_coordinates

        else:
            total_attack=0
            if( grid_part[request_message[0][0]][request_message[0][1]].unit_type=="neutral"):
                for i in request_message[1:-1]:
                    for j in i:
                        if j[0]<len(grid_part)and j[0]>=0 and j[1]<len(grid_part[0]) and j[1]>=0: 
                            if grid_part[j[0]][j[1]].unit_type=="neutral":
                                continue
                            elif grid_part[j[0]][j[1]].unit_type=="Air":
                                break
                            else:
                                boundary_data[0]="Y"
                                total_attack+=1 
                                break
                boundary_data[1]=str(total_attack) 
            else:
                boundary_data[1]=str(-1) 
    else:       
        for i in request_message[0:-1]:
            if i[0]<len(grid_part)and i[0]>=0 and i[1]<len(grid_part[0]) and i[1]>=0:
                if grid_part[i[0]][i[1]].unit_type!="neutral" and request_message[-1][0]!= grid_part[i[0]][i[1]].unit_type:
                    attacked_coordinates.append([i[0],i[1], request_message[-1][1] if grid_part[i[0]][i[1]].unit_type != "Earth" else int(request_message[-1][1]/ 2)])
                    if (grid_part[i[0]][i[1]].health-  (request_message[-1][1] if grid_part[i[0]][i[1]].unit_type != "Earth" else int(request_message[-1][1]/ 2)))<=0:
                        boundary_data[1]="Y"
                    boundary_data[0]="Y"
    serialized_data = pickle.dumps(boundary_data)
    data_size = np.array([len(serialized_data)], dtype=np.int32)
    comm.Send([data_size, MPI.INT], dest=dest_rank, tag=0)
    comm.Send([serialized_data, MPI.BYTE], dest=dest_rank, tag=0)
    return attacked_coordinates


# Function to manage boundary data to a requested process used for the list of attack and movement phases
def providing_to_others(comm,grid_part,rank,size,air_simulation=0):
    attacks_queue=[]
    source_rank=0
    break_check=0
    while True:                          
        while comm.Iprobe(source=MPI.ANY_SOURCE, tag=0):
            status = MPI.Status()
            comm.Probe(source=MPI.ANY_SOURCE, tag=0, status=status)
            source_rank = status.Get_source()
            attacks= provide_boundary_data(comm, grid_part, source_rank,air_simulation)
            if attacks==0:
                 break_check+=1
                 continue
            for i in attacks:
                attacks_queue.append(i)
        if break_check==2  and rank!=1 and rank!=size:
             break
        elif break_check==1 and (rank==1 or rank==size-1):
             break
    return attacks_queue


# Function to list the attack coordinates of the unit and the attack power for another process
def requested_boundaries(unit_type,row_index,col_idx,attack_power,number_of_rows=0,direction_x=0,direction_y=0,move_to_air=0):
            if unit_type=="Air" and move_to_air==0:
                attacks=[[row_index+i*direction_x,col_idx+i*direction_y] for i in range(number_of_rows)]
                attacks.append([unit_type,attack_power,move_to_air]) 
                return   attacks
            elif unit_type=="Air" and move_to_air==1:
                 control_location=[row_index,col_idx]
                 attacks=[[[row_index+x,col_idx+y],[row_index+2*x,col_idx+2*y]] for x,y in [(0,-1),(-1,-1),(-1,0),(-1,1),(0,1)] ]
                 attacks.insert(0, control_location)
                 attacks.append([unit_type,attack_power,move_to_air]) 
                 return   attacks
            elif unit_type=="Air" and move_to_air==2:      
                control_location=[row_index,col_idx]
                attacks=[[[row_index+x,col_idx+y],[row_index+2*x,col_idx+2*y]] for x,y in [(0,-1),(1,-1),(1,0),(1,1),(0,1)]   ]
                attacks.insert(0, control_location)
                attacks.append([unit_type,attack_power,move_to_air]) 
                return   attacks
            elif unit_type=="Air" and move_to_air==5: # give the new location of air to other processor
                attacks= [[row_index,col_idx],[unit_type,attack_power,move_to_air]]
                return   attacks
            elif(unit_type=="Fire"):
                   return [[row_index,col_idx-1],[row_index,col_idx],[row_index,col_idx+1],[unit_type,attack_power,number_of_rows]]
            elif(unit_type=="Water"):
                  return [[row_index,col_idx-1],[row_index,col_idx+1],[unit_type,attack_power]]
            else:
                return [[row_index,col_idx],[unit_type,attack_power]]
# Function to send grid parts to manager
def give_back_to_manager(grid_part,comm):
    request_message= pickle.dumps(grid_part)
    request_size = np.array([len(request_message)], dtype=np.int32)
    comm.Send([request_size, MPI.INT], dest=0, tag=0)
    comm.Send([request_message, MPI.BYTE], dest=0, tag=0)

# Function to collect grid parts from worker to manager
def manager_take_back(grid,rank,size,comm):
    taken_ended=size-1
    grid_part_lentgh= len(grid.grid)/(size-1) 
    while True:                         
        while comm.Iprobe(source=MPI.ANY_SOURCE, tag=0):
            status = MPI.Status()
            comm.Probe(source=MPI.ANY_SOURCE, tag=0, status=status)
            source_rank = status.Get_source()
            request_size = np.zeros(1, dtype=np.int32)
            comm.Recv(request_size, source=source_rank, tag=0)
            request_size = request_size[0]
            grid_part = bytearray(request_size)
            comm.Recv([grid_part, MPI.BYTE], source=source_rank, tag=0)
            grid_part = pickle.loads(grid_part)
    
            coefficient= (source_rank-1)* grid_part_lentgh
            for i in range(0,len(grid_part)):
                 grid.grid[int(coefficient+i)]=grid_part[i]
                 continue
            taken_ended-=1
        if taken_ended==0:
             return

# Function to calculate flood for Water units from another process
def flood(comm,grid_part,rank,size):
    source_rank=0
    break_check=0
    new_waters=[]
    while True:                          
        while comm.Iprobe(source=MPI.ANY_SOURCE, tag=0):
            status = MPI.Status()
            comm.Probe(source=MPI.ANY_SOURCE, tag=0, status=status)
            source_rank = status.Get_source()
            new_water= provide_water_info(comm, grid_part, source_rank)
            if type(new_water) == int:
                 break_check+=1
                 continue
            else:
                 new_waters.append(new_water)
                
        if break_check==2  and rank!=1 and rank!=size-1:
             break
        elif break_check==1 and (rank==1 or rank==size-1):
             break
             
    return new_waters

# Function to provide water info for flood part
def provide_water_info(comm,grid_part,dest_rank):
    request_size = np.zeros(1, dtype=np.int32)
    comm.Recv(request_size, source=dest_rank, tag=0)
    request_size = request_size[0]
    request_message = bytearray(request_size)
    comm.Recv([request_message, MPI.BYTE], source=dest_rank, tag=0)
    request_message = pickle.loads(request_message)
    if request_message== "WE.": #water ended
         return 0
    it_is_done=("N","N")
    new_water=[]
    for i in request_message:
        if i[0]<len(grid_part)and i[0]>=0 and i[1]<len(grid_part[0]) and i[1]>=0: 
            if grid_part[i[0]][i[1]].unit_type=="neutral":
                new_water= [i[0],i[1]]
                it_is_done=("Y","N")
                break
    serialized_data = pickle.dumps(it_is_done)
    data_size = np.array([len(serialized_data)], dtype=np.int32)
    comm.Send([data_size, MPI.INT], dest=dest_rank, tag=0)
    comm.Send([serialized_data, MPI.BYTE], dest=dest_rank, tag=0)
    return new_water
# main method for flood checking 
def check_for_flood(comm, grid_part,rank,size):
    added_list=[]
    for row_index, row  in enumerate(grid_part):
        adjacents=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for col_idx, unit in enumerate(row):
            is_found= False
            if unit.unit_type== "Water":
                    if row_index==0 and rank!=1:
                         upper_boundary=[[len(grid_part)-1,col_idx-1],[len(grid_part)-1,col_idx],[len(grid_part)-1,col_idx+1]]
                         request_boundary_data(comm,rank-1,upper_boundary)
                         is_found=take_the_response_boundary(comm,rank-1)
                    if is_found:
                         continue
                    for x, y in adjacents:
                        target_row, target_col = row_index + x, col_idx + y
                        if(target_row<len(grid_part)and target_row>=0 and target_col<len(grid_part[0]) and target_col>=0):
                            if  grid_part[target_row][target_col].unit_type== "neutral":
                                added_list.append([target_row,target_col])
                                is_found=True
                                break
                    if is_found:
                         continue             
                    if row_index==len(grid_part)-1 and rank!=size-1: 
                         lower_boundary=[[0,col_idx-1],[0,col_idx],[0,col_idx+1]]
                         request_boundary_data(comm,rank+1,lower_boundary)
                         is_found=take_the_response_boundary(comm,rank+1)
                         sys.stdout.flush()
                    if is_found:
                         continue
        if is_found:
             continue         
    if rank!=1:
        request_boundary_data(comm,rank-1,"WE.")
    if rank!=size-1:
        request_boundary_data(comm,rank+1,"WE.")
    return added_list

