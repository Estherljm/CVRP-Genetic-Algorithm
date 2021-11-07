# Project
Comparison of Genetic Algorithm Selection Methods Solving a Capacitated Vehicle Routing Problem for Vaccine Distribution

# Capacitated Vehicle Routing Problem (CVRP)
- Considers **multiple** routes where each route is associated to a vehicle 
- Multiple vehicles with **uniform capacities** are involved 
- Each customer is visited only **once**

**Goal**
: Minimize total distance cost and number of vehicles while assuring that the total demand per route is within the given vehicle capacity

# Genetic Algorithm (GA) 
The Genetic Algorithm (GA) based on the Darwin’s principal of “survival of the fittest” is a type of adaptive heuristic search algorithm 
that has been often applied to solve optimization problems in various fields (Pandey, 2016).

Mainly consists of 5 main steps:
1. Population generation 
2. Fitness Evaluation
3. Parent selection
4. Crossover 
5. Mutation 

# Objective 
Solve CVRP using GA while comparing the performance of different selection methods such as the Roulette Wheel Selection (RWS) and Tournament Selection (TS)

# Flowchart of proposed GA 
![alt text](https://github.com/Estherljm/CVRP-Genetic-Algorithm/blob/master/Images/img1.png)

** Elitism was included to ensure that the best individuals in the population are not lost through due to other operators in the GA such as crossover and mutation. 

# Plots 
Left : Optimization performance with each generation 

Right : Visualization of vehicles travelling pattern from depot

![alt text](https://github.com/Estherljm/CVRP-Genetic-Algorithm/blob/master/Images/img2.png)
![alt text](https://github.com/Estherljm/CVRP-Genetic-Algorithm/blob/master/Images/img3.png)

# Results 
In an overall comparison, the RWS method with 300 generations on the top 10 elite population performed the best 
with average fitness values of 7 for number of vehicles and 390.1198 for total transportation cost


