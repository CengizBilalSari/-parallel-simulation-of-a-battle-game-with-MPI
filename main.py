from mpi4py import MPI
import numpy as np
import pickle
import sys
from grid import Grid
from unit import Earth, Fire, Water, Air, Unit
from helper_functions import parse_input_file, place_units_on_grid,check_for_inferno, striped_partitioning,check_for_inferno_boundary
from boundary_functions import  take_the_response_boundary ,request_boundary_data, providing_to_others, requested_boundaries, manager_take_back, give_back_to_manager,check_for_flood,flood,take_the_air_info


# Function to perform the action phase, where units attack based on their type and health
def action_phase(comm,grid_part,rank,size):
    attacks_queue=[]#which will include the attacks as  [row,col,attack_power]
    for row_index, row  in enumerate(grid_part):    
        for col_idx, unit in enumerate(row):
            if unit.unit_type!= "neutral":
                if unit.health< unit.full_health/2:
                    continue
                else:
                    if( unit.unit_type=="Air"):
                        for x, y in unit.attack_pattern:
                            target_row, target_col = row_index + x, col_idx + y
                            for z in range(2):
                                   target_row+= z*x
                                   target_col+=z*y
                                   if target_row<len(grid_part)and target_row>=0 and target_col<len(grid_part[0]) and target_col>=0:      
                                        target_unit = grid_part[target_row][target_col]
                                        if target_unit.unit_type=="neutral":
                                                        continue
                                        elif target_unit.unit_type=="Air":
                                                break
                                        else:
                                                grid_part[row_index][col_idx].attack= True
                                                attacks_queue.append([target_row,target_col,  unit.attack_power if target_unit.unit_type != "Earth" else int(unit.attack_power/ 2)])
                                                break
                                   elif  target_row<0 and target_col<len(grid_part[0]) and target_col>=0 and rank!=1:
                                        # require information from upper

                                        requested_data= requested_boundaries(unit.unit_type,len(grid_part)-1,target_col,unit.attack_power,2-z,x,y)
                                        request_boundary_data(comm,rank-1,requested_data) 
                                        (is_attacked,is_destroyed)=take_the_response_boundary(comm,rank-1)
                                        if is_attacked:
                                            grid_part[row_index][col_idx].attack= True
                                        break
                                   elif  target_row>len(grid_part)-1 and target_col<len(grid_part[0]) and target_col>=0 and rank !=size-1:
                                        # require information from lower
                                        requested_data= requested_boundaries(unit.unit_type,0,target_col,unit.attack_power,2-z,x,y)
                                        request_boundary_data(comm,rank+1,requested_data)
                                           
                                        (is_attacked,is_destroyed)=take_the_response_boundary(comm,rank+1)
                                        if is_attacked:
                                            grid_part[row_index][col_idx].attack= True
                                        break
                                   else:
                                        break
                                                    
                    else:        
                        if(row_index==0 and rank!=1 ):
                                # take  information from upper part
                                requested_data= requested_boundaries(unit.unit_type,len(grid_part)-1,col_idx,unit.attack_power)
                                request_boundary_data(comm,rank-1,requested_data) # [[Unit,row,col],[Unit,row,col],..]
                                (is_attacked,is_destroyed)=take_the_response_boundary(comm,rank-1)
                                if is_attacked:
                                    grid_part[row_index][col_idx].attack= True
                                    check_for_inferno_boundary(grid_part,is_destroyed,row_index, col_idx, unit.unit_type )
                        elif(row_index==len(grid_part)-1 and rank!=size-1):
                                    
                                #attacked_parts= provide_boundary_data(comm,grid_part,rank-1)
                                # take  information from upper part
                                    requested_data= requested_boundaries(unit.unit_type,0,col_idx,unit.attack_power)
                                    request_boundary_data(comm,rank+1,requested_data) # [[Unit,row,col],[Unit,row,col],..]
                                    (is_attacked,is_destroyed)=take_the_response_boundary(comm,rank+1)
                                    if is_attacked:
                                        grid_part[row_index][col_idx].attack= True
                                        check_for_inferno_boundary(grid_part,is_destroyed,row_index, col_idx, unit.unit_type )  
                        for x, y in unit.attack_pattern:
                            target_row, target_col = row_index + x, col_idx + y
                            if(target_row<len(grid_part)and target_row>=0 and target_col<len(grid_part[0]) and target_col>=0):
                                target_unit = grid_part[target_row][target_col]
                                if target_unit.unit_type!= "neutral" and target_unit.unit_type!= unit.unit_type and   unit.full_health/2 <= unit.health:
                                    grid_part[row_index][col_idx].attack= True
                                    check_for_inferno(grid_part,row_index, col_idx ,target_row,target_col,unit.attack_power if target_unit.unit_type != "Earth" else int(unit.attack_power/ 2),unit.unit_type)
                                    attacks_queue.append([target_row,target_col,  unit.attack_power if target_unit.unit_type != "Earth" else int(unit.attack_power/ 2)])
                    
    if rank!=1:
        request_boundary_data(comm,rank-1,"I am ended.")
    if rank!=size-1:
        request_boundary_data(comm,rank+1,"I am ended.")
    return attacks_queue

        
# Function to resolve attacks on units by reducing their health and removing defeated units
def resolution_phase(attack_queue,grid_part):     
     for i in range(0,len(attack_queue)):
        attacked_coordinates= [attack_queue[i][0],attack_queue[i][1]] # target x,y coordinates for grid part
        attack_power= attack_queue[i][2]
        grid_part[attacked_coordinates[0]][attacked_coordinates[1]].health-= attack_power
     for row in range(0,len(grid_part)):
                    for unit in range(0,len(grid_part[0])):
                        if(grid_part[row][unit].health<=0):
                            grid_part[row][unit]= Unit()

# Function to heal units that did not attack in the current round
def healing_phase(grid_part):
    for row in range(0,len(grid_part)):
                    for unit in range(0,len(grid_part[0])):
                        if grid_part[row][unit].unit_type== "Fire":
                             grid_part[row][unit].inferno=False
                        if(grid_part[row][unit].attack==False and grid_part[row][unit].unit_type!="neutral"):
                            grid_part[row][unit].health+= grid_part[row][unit].healing_rate
                            if (grid_part[row][unit].health>grid_part[row][unit].full_health):
                                grid_part[row][unit].health = grid_part[row][unit].full_health
                        else:
                            grid_part[row][unit].attack=False

# Function to find max attack number for Air units
def calculation_of_air_positions(grid_part,comm,rank,size):
    changed_airs=[]
    for row_index, row  in enumerate(grid_part):    
        for col_idx, unit in enumerate(row):
            if grid_part[row_index][col_idx].unit_type=="Air":
                    (new_x,new_y,attack__power,health)=calculate_air_position(comm,grid_part,rank,size,row_index,col_idx,grid_part[row_index][col_idx])
                    if new_x<0 and rank!=1:
                          request_boundary_data(comm,rank-1,[[len(grid_part)-1,col_idx],["Air",grid_part[row_index][col_idx].attack_power,5,grid_part[row_index][col_idx].health]])
                    elif new_x>=len(grid_part) and rank!=size-1:
                        request_boundary_data(comm,rank+1,[[0,col_idx],["Air",grid_part[row_index][col_idx].attack_power,5,grid_part[row_index][col_idx].health]])

                    changed_airs.append([row_index,col_idx,new_x,new_y,attack__power,health])
    if rank!=1:
            request_boundary_data(comm,rank-1,"I am ended.")
    if rank!=size-1:
            request_boundary_data(comm,rank+1,"I am ended.")
    return changed_airs
def calculate_air_position(comm,grid_part,rank,size,row_index,col_idx,unit):
    attacks_number_arr=[0,0,0,0,0,0,0,0,0]
    adjacents=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,0),(0,1),(1,-1),(1,0),(1,1)]
    attacks_number_index=0
    for a, b  in adjacents:
            attacks_number=0
            new_row, new_col= row_index+a, col_idx+b
            if new_col>=0 and new_col<len(grid_part[0]) :
                if(new_row>=0 and new_row<=len(grid_part)-1):
                    if grid_part[new_row][new_col].unit_type=="neutral" or (a==0 and b==0):
                        for x, y in unit.attack_pattern:
                                target_row, target_col = new_row + x, new_col + y
                                for z in range(2):
                                    target_row+= z*x
                                    target_col+=z*y
                                    if target_row<len(grid_part)and target_row>=0 and target_col<len(grid_part[0]) and target_col>=0:      
                                            target_unit = grid_part[target_row][target_col]
                                            if target_unit.unit_type=="neutral" or (target_row==row_index and target_col==col_idx):
                                                            continue
                                            elif target_unit.unit_type=="Air":
                                                    break
                                            else:
                                                    #grid_part[row_index][col_idx].attack= True
                                                    attacks_number+=1
                                                    break
                                    elif  target_row<0 and target_col<len(grid_part[0]) and target_col>=0 and rank!=1:
                                            # require information from upper
                                            requested_data= requested_boundaries(unit.unit_type,len(grid_part)-1,target_col,unit.attack_power,2-z,x,y)
                                            request_boundary_data(comm,rank-1,requested_data) 
                                            (is_attacked,is_destroyed)=take_the_response_boundary(comm,rank-1)                                           
                                            if is_attacked:
                                                attacks_number+=1
                                            break
                                    elif  target_row>len(grid_part)-1 and target_col<len(grid_part[0]) and target_col>=0 and rank !=size-1:
                                            # require information from lower
                                            requested_data= requested_boundaries(unit.unit_type,0,target_col,unit.attack_power,2-z,x,y)
                                            request_boundary_data(comm,rank+1,requested_data)
                                            (is_attacked,is_destroyed)=take_the_response_boundary(comm,rank+1)
                                            if is_attacked:
                                                attacks_number+=1
                                            break
                                    else:
                                            break
                                    
                        attacks_number_arr[attacks_number_index]=attacks_number  
                        attacks_number_index+=1
                                    
                    else:
                            attacks_number_arr[attacks_number_index]= -1
                            attacks_number_index+=1
                elif new_row<0 and  rank!=1:
                      requested_data= requested_boundaries(unit.unit_type,len(grid_part)-1,new_col,unit.attack_power,2,0,0,1)
                      request_boundary_data(comm,rank-1,requested_data)
                      (is_attacked,attack_from_upper)=take_the_air_info(comm,rank-1)
                      if is_attacked:
                        for x, y in [(1, -1),(1,0), (1, 1)]:
                                    target_row, target_col = new_row + x, new_col + y
                                    for z in range(2):
                                        if target_row<len(grid_part)and target_row>=0 and target_col<len(grid_part[0]) and target_col>=0:      
                                                target_unit = grid_part[target_row][target_col]
                                                if target_unit.unit_type=="neutral":
                                                                continue
                                                elif target_unit.unit_type=="Air":
                                                        break
                                                else:
                                                        attacks_number+=1
                                                        break
                        attacks_number+=attack_from_upper
                        attacks_number_arr[attacks_number_index]=attacks_number
                        attacks_number_index+=1
                      else:
                        attacks_number_arr[attacks_number_index]=-1
                        attacks_number_index+=1
                            
                      
                elif new_row>=len(grid_part) and  rank!=size-1:
                      requested_data= requested_boundaries(unit.unit_type,0,new_col,unit.attack_power,2,0,0,2)
                      request_boundary_data(comm,rank+1,requested_data)
                      (is_attacked,attack_from_lower)=take_the_air_info(comm,rank+1)
                      for x, y in [(-1, 0), (-1, -1), (-1, 1)]:
                                target_row, target_col = new_row + x, new_col + y
                                for z in range(2):
                                      if target_row<len(grid_part)and target_row>=0 and target_col<len(grid_part[0]) and target_col>=0:      
                                            target_unit = grid_part[target_row][target_col]
                                            if target_unit.unit_type=="neutral":
                                                            continue
                                            elif target_unit.unit_type=="Air":
                                                    break
                                            else:
                                                    attacks_number+=1
                                                    break
                      attacks_number+=attack_from_lower
                      attacks_number_arr[attacks_number_index]=attacks_number
                      attacks_number_index+=1
                elif rank==1 and new_row<0:
                    attacks_number=-1
                    attacks_number_arr[attacks_number_index]=attacks_number
                    attacks_number_index+=1
            else:
                attacks_number=-1
                attacks_number_arr[attacks_number_index]=attacks_number
                attacks_number_index+=1
    max_value = max(attacks_number_arr)  # Find the maximum value in the array
    
    first_index = attacks_number_arr.index(max_value)  # F
    if attacks_number_arr[4]==attacks_number_arr[first_index]:
          return (row_index,col_idx,unit.attack_power,unit.health)
    else:
          
       return (row_index+ adjacents[first_index][0],col_idx+ adjacents[first_index][1],unit.attack_power,unit.health)

# Function to execute movement phase for Air units
def movement_phase(changed_airs,grid_part,rank):
    for i in changed_airs:
            row_index,col_index= i[0],i[1]
            if row_index>=0 and row_index<len(grid_part):
                grid_part[row_index][col_index]=Unit()
            new_row,new_col= i[2],i[3]
            if new_row>=0 and new_row <len(grid_part):
                if(grid_part[new_row][new_col].unit_type=="neutral"):
                    grid_part[new_row][new_col]= Air(i[4],i[5])
                else:
                    merged_attack_power=grid_part[new_row][new_col].attack_power + i[4]
                    merged_health=grid_part[new_row][new_col].health+ i[5]
                    if merged_health> 10:
                        merged_health=10
                    grid_part[new_row][new_col]= Air(attack_power=merged_attack_power, health=merged_health)
    
# Main function to handle the overall simulation process
def main(input_file,output_file):    
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    # the manager process
    if rank==0:
        waves, N,W,T,R=parse_input_file(input_file)
        grid= Grid(rows=N,cols=N)
        for i in range(0,size-1):
            round_number = np.array([R], dtype=np.int32)  
            comm.Send([round_number, MPI.INT], dest=i + 1)
            wave_number = np.array([W], dtype=np.int32)  
            comm.Send([wave_number, MPI.INT], dest=i + 1)
        for i in range(W):
            place_units_on_grid(grid,waves,i)
            striped_partitioning(size-1,grid,N,comm)
            comm.Barrier()
            manager_take_back(grid,rank,size,comm)
        with open(output_file, "w") as file:
            for row in grid.grid:
                for unit in row:
                    if unit.unit_type[0] == "n":
                        file.write(". ")
                    else:
                        file.write(unit.unit_type[0] + " ")
                file.write("\n")
    #the workers processes with even ranks
    elif rank%2==0:
        round_number = np.zeros(1, dtype=int)
        comm.Recv(round_number, source=0)
        round_number= round_number[0]
        w = np.zeros(1, dtype=int)
        comm.Recv(w, source=0)
        w= w[0]
        for j in range(w):
            data_size = np.zeros(1, dtype=int)
            comm.Recv(data_size, source=0)
            data_size = data_size[0]
            serialized_data = bytearray(data_size)
            comm.Recv([serialized_data, MPI.BYTE], source=0)
            grid_part = pickle.loads(serialized_data)
            sys.stdout.flush() 
            comm.Barrier()
            for i in range(0,round_number):
                changed_airs= calculation_of_air_positions(grid_part,comm,rank,size)
                coming_airs= providing_to_others(comm,grid_part,rank,size,air_simulation=1)
                for k in coming_airs:
                    changed_airs.append(k)
                movement_phase(changed_airs,grid_part,rank)
                attacks=action_phase(comm, grid_part,rank,size)
                attacked_parts_boundary=providing_to_others(comm,grid_part,rank,size)
                for b in attacked_parts_boundary:
                    attacks.append(b)

                resolution_phase(attacks,grid_part)
                healing_phase(grid_part)
            added_waters=check_for_flood(comm,grid_part,rank,size)
            coming_waters=flood(comm,grid_part,rank,size)   
            for  i in coming_waters:
                if len(i)==2:
                    grid_part[i[0]][i[1]]=Water()
            for  i in added_waters:
                if len(i)==2:
                    grid_part[i[0]][i[1]]=Water()
            for row_index, row  in enumerate(grid_part):    
                for col_idx, unit in enumerate(row):
                      if grid_part[row_index][col_idx].unit_type=="Fire":
                             grid_part[row_index][col_idx].inferno=False
                             grid_part[row_index][col_idx].attack_power=4
            give_back_to_manager(grid_part,comm)
    else:
        round_number = np.zeros(1, dtype=int)
        comm.Recv(round_number, source=0)
        round_number= round_number[0]
        w = np.zeros(1, dtype=int)
        comm.Recv(w, source=0)
        w= w[0]
        for j in range(w):
            data_size = np.zeros(1, dtype=int)
            comm.Recv(data_size, source=0)
            data_size = data_size[0]
            serialized_data = bytearray(data_size)
            comm.Recv([serialized_data, MPI.BYTE], source=0)
            grid_part = pickle.loads(serialized_data)
            comm.Barrier()
            for i in range(round_number):
                coming_airs= providing_to_others(comm,grid_part,rank,size,air_simulation=1)
                changed_airs= calculation_of_air_positions(grid_part,comm,rank,size)
                for a in coming_airs:
                    changed_airs.append(a)
                movement_phase(changed_airs,grid_part,rank)
                attacked_parts_boundary=providing_to_others(comm,grid_part,rank,size)
                sys.stdout.flush()
                attacks=action_phase(comm, grid_part,rank,size)
                for b in attacked_parts_boundary:
                    attacks.append(b)

                resolution_phase(attacks,grid_part)
                healing_phase(grid_part)           
            coming_waters=flood(comm,grid_part,rank,size)
            added_waters=check_for_flood(comm,grid_part,rank,size)
            for  i in coming_waters:
                if len(i)==2:
                    grid_part[i[0]][i[1]]=Water()
            for  i in added_waters:
                if len(i)==2:
                        grid_part[i[0]][i[1]]=Water()
            for row_index, row  in enumerate(grid_part):    
                for col_idx, unit in enumerate(row):
                      if grid_part[row_index][col_idx].unit_type=="Fire":
                             grid_part[row_index][col_idx].inferno=False
                             grid_part[row_index][col_idx].attack_power=4
        
            give_back_to_manager(grid_part,comm)
            
    #Finalize the MPI environment
    MPI.Finalize()
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)