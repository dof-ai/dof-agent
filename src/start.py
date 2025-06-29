from dof import DOF

sim = DOF()        

# Add object to the scene
sim.add_ground()    
sim.add_ball()      
sim.add_robot("franka")     
