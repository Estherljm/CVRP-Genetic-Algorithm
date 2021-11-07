
import os
import io
import random
import numpy
import fnmatch
import csv
import array
import json

from csv import DictWriter
from json import load, dump
from deap import base, creator, tools, algorithms, benchmarks
from deap.benchmarks.tools import diversity, convergence, hypervolume


BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))



# Load the given problem, which can be a json file
def load_instance(json_file):
    """
    Inputs: path to json file
    Outputs: json file object if it exists, or else returns NoneType
    """
    if os.path.exists(path=json_file):
        with io.open(json_file, 'rt', newline='') as file_object:
            return load(file_object)
    return None


# Take a route of given length, divide it into subroute where each subroute is assigned to vehicle
def routeToSubroute(individual, instance):
    """
    Inputs: Sequence of customers that a route has
            Loaded instance problem
    Outputs: Route that is divided in to subroutes
             which is assigned to each vechicle.
    """
    route = []
    sub_route = []
    vehicle_load = 0
    last_customer_id = 0
    vehicle_capacity = instance['vehicle_capacity']
    
    for customer_id in individual:
        # print(customer_id)
        demand = instance[f"customer_{customer_id}"]["demand"]
        # print(f"The demand for customer_{customer_id}  is {demand}")
        updated_vehicle_load = vehicle_load + demand

        if(updated_vehicle_load <= vehicle_capacity):
            sub_route.append(customer_id)
            vehicle_load = updated_vehicle_load
        else:
            route.append(sub_route)
            sub_route = [customer_id]
            vehicle_load = demand
        
        last_customer_id = customer_id

    if sub_route != []:
        route.append(sub_route)

    # Returning the final route with each list inside for a vehicle
    return route


def printRoute(route, merge=False):
    route_str = '0'
    sub_route_count = 0
    for sub_route in route:
        sub_route_count += 1
        sub_route_str = '0'
        for customer_id in sub_route:
            sub_route_str = f'{sub_route_str} - {customer_id}'
            route_str = f'{route_str} - {customer_id}'
        sub_route_str = f'{sub_route_str} - 0'
        if not merge:
            print(f'  Vehicle {sub_route_count}\'s route: {sub_route_str}')
        route_str = f'{route_str} - 0'
    if merge:
        print(route_str)


# Calculate the number of vehicles required, given a route
def getNumVehiclesRequired(individual, instance):
    """
    Inputs: Individual route
            Json file object loaded instance
    Outputs: Number of vechiles according to the given problem and the route
    """
    # Get the route with subroutes divided according to demand
    updated_route = routeToSubroute(individual, instance)
    num_of_vehicles = len(updated_route)
    return num_of_vehicles


# Given a route, give its total cost
def getRouteCost(individual, instance, unit_cost=1):
    """
    Inputs : 
        - Individual route
        - Problem instance, json file that is loaded
        - Unit cost for the route (can be petrol etc)

    Outputs:
        - Total cost for the route taken by all the vehicles
    """
    total_cost = 0
    updated_route = routeToSubroute(individual, instance)

    for sub_route in updated_route:
        # Initializing the subroute distance to 0
        sub_route_distance = 0
        # Initializing customer id for depot as 0
        last_customer_id = 0

        for customer_id in sub_route:
            # Distance from the last customer id to next one in the given subroute
            distance = instance["distance_matrix"][last_customer_id][customer_id]
            sub_route_distance += distance
            # Update last_customer_id to the new one
            last_customer_id = customer_id
        
        # After adding distances in subroute, adding the route cost from last customer to depot
        # that is 0
        sub_route_distance = sub_route_distance + instance["distance_matrix"][last_customer_id][0]

        # Cost for this particular sub route
        sub_route_transport_cost = unit_cost*sub_route_distance

        # Adding this to total cost
        total_cost = total_cost + sub_route_transport_cost
    
    return total_cost


# Get the fitness of a given route
def eval_indvidual_fitness(individual, instance, unit_cost):
    """
    Inputs: individual route as a sequence
            Json object that is loaded as file object
            unit_cost for the distance 
    Outputs: Returns a tuple of (Number of vechicles, Route cost from all the vechicles)
    """

    # we have to minimize number of vehicles
    # TO calculate req vechicles for given route
    vehicles = getNumVehiclesRequired(individual, instance)

    # we also have to minimize route cost for all the vehicles
    route_cost = getRouteCost(individual, instance, unit_cost)

    return (vehicles, route_cost)



# Crossover method with ordering
# This method will let us escape illegal routes with multiple occurences
#   of customers that might happen. We would never get illegal individual from this
#   crossOver
def cxOrderedVrp(input_ind1, input_ind2):
    # Modifying this to suit our needs
    #  If the sequence does not contain 0, this throws error
    #  So we will modify inputs here itself and then 
    #       modify the outputs too

    ind1 = [x-1 for x in input_ind1]
    ind2 = [x-1 for x in input_ind2]
    size = min(len(ind1), len(ind2))
    # 2 is to return 2 samples which will be a & b 
    a, b = random.sample(range(size), 2)
    if a > b:
        a, b = b, a

    # print(f"The cutting points are {a} and {b}")
    # this is to print X number of "TRUE" according to the size 
    holes1, holes2 = [True] * size, [True] * size
    for i in range(size):
        if i < a or i > b:
            holes1[ind2[i]] = False
            holes2[ind1[i]] = False

    # We must keep the original values somewhere before scrambling everything
    temp1, temp2 = ind1, ind2
    k1, k2 = b + 1, b + 1
    for i in range(size):
        if not holes1[temp1[(i + b + 1) % size]]:
            ind1[k1 % size] = temp1[(i + b + 1) % size]
            k1 += 1

        if not holes2[temp2[(i + b + 1) % size]]:
            ind2[k2 % size] = temp2[(i + b + 1) % size]
            k2 += 1

    # Swap the content between a and b (included)
    for i in range(a, b + 1):
        ind1[i], ind2[i] = ind2[i], ind1[i]

    # Finally adding 1 again to reclaim original input
    ind1 = [x+1 for x in ind1]
    ind2 = [x+1 for x in ind2]
    return ind1, ind2


def mutationShuffle(individual, indpb):
    """
    Inputs : Individual route
             Probability of mutation betwen (0,1)
    Outputs : Mutated individual according to the probability
    """
    size = len(individual)
    for i in range(size):
        if random.random() < indpb:
            swap_indx = random.randint(0, size - 2)
            if swap_indx >= i:
                swap_indx += 1
            individual[i], individual[swap_indx] = \
                individual[swap_indx], individual[i]

    return individual,



## Statistics and Logging

def createStatsObjs():
    # Method to create stats and logbook objects
    """
    Inputs : None
    Outputs : tuple of logbook and stats objects.
    """
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)

    # Methods for logging
    logbook = tools.Logbook()
    #logbook.header = "Generation", "evals", "avg", "std", "min", "max", "best_one", "fitness_best_one"
    logbook.header = "avg", "best_one", "fitness_best_one"
    return logbook, stats


def recordStat(invalid_ind, logbook, pop, stats, gen):
    """
    Inputs : invalid_ind - Number of children for which fitness is calculated
             logbook - Logbook object that logs data
             pop - population
             stats - stats object that compiles statistics
    Outputs: None, prints the logs
    """
    record = stats.compile(pop)
    best_individual = tools.selBest(pop, 1)[0]
    record["best_one"] = best_individual
    record["fitness_best_one"] = best_individual.fitness
    logbook.record(Generation=gen, evals=len(invalid_ind), **record)
    #print(logbook.stream)




## Exporting CSV files

def exportCsv(csv_file_name, logbook):
    csv_columns = logbook[0].keys()
    csv_path = os.path.join(BASE_DIR, "results", csv_file_name)
    try:
        with open(csv_path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in logbook:
                writer.writerow(data)
    except IOError:
        print("I/O error")

###################### 1ST METHOD ##############################################
"""
SELECT = NSGA2
MATE = ORDEREDVRP (CUSTOM CODE)
MUTATE = MUTATESHUFFLE
"""

class nsgaAlgo(object):
    random.seed(10)
    def __init__(self):
        f  = open(r'...data\json\Input_Data.json')
        self.json_instance = json.load(f)
        self.ind_size = self.json_instance['Number_of_customers']
        self.pop_size = 400
        self.cross_prob = 0.85
        self.mut_prob = 0.02
        self.num_gen = 150
        self.toolbox = base.Toolbox()
        self.logbook, self.stats = createStatsObjs()
        self.createCreators()

    def createCreators(self):
        creator.create('FitnessMin', base.Fitness, weights=(-1.0, -1.0))
        creator.create('Individual', list, fitness=creator.FitnessMin)

        # Registering toolbox
        self.toolbox.register('indexes', random.sample, range(1, self.ind_size + 1), self.ind_size)

        # Creating individual and population from that each individual
        self.toolbox.register('individual', tools.initIterate, creator.Individual, self.toolbox.indexes)
        self.toolbox.register('population', tools.initRepeat, list, self.toolbox.individual)

        # Creating evaluate function using our custom fitness
        #   toolbox.register is partial, *args and **kwargs can be given here
        #   and the rest of args are supplied in code
        self.toolbox.register('evaluate', eval_indvidual_fitness, instance=self.json_instance, unit_cost=1)

        # Selection method
        self.toolbox.register("select", tools.selNSGA2)

        # Crossover method
        self.toolbox.register("mate", cxOrderedVrp)

        # Mutation method
        self.toolbox.register("mutate", mutationShuffle, indpb=self.mut_prob)


    def generatingPopFitness(self):
        self.pop = self.toolbox.population(n=self.pop_size)
        self.invalid_ind = [ind for ind in self.pop if not ind.fitness.valid]
        self.fitnesses = list(map(self.toolbox.evaluate, self.invalid_ind))

        for ind, fit in zip(self.invalid_ind, self.fitnesses):
            ind.fitness.values = fit
        
        # this part is done just for sorting the population only, no selection is actually done 
        self.pop = self.toolbox.select(self.pop, len(self.pop))

        recordStat(self.invalid_ind, self.logbook, self.pop, self.stats, gen = 0)


    def runGenerations(self):
        # Running algorithm for given number of generations
        for gen in range(self.num_gen):
            print(f"{20*'#'} Currently Evaluating {gen} Generation {20*'#'}")

            # Selecting individuals
            # Selecting offsprings from the population, about 1/2 of them
            self.offspring = tools.selTournamentDCD(self.pop, len(self.pop))
            self.offspring = [self.toolbox.clone(ind) for ind in self.offspring]

            # Performing , crossover and mutation operations according to their probabilities
            for ind1, ind2 in zip(self.offspring[::2], self.offspring[1::2]):
                # Mating will happen 80% of time if cross_prob is 0.8
                if random.random() <= self.cross_prob:
                    # print("Mating happened")
                    self.toolbox.mate(ind1, ind2)

                    # If cross over happened to the individuals then we are deleting those individual
                    #   fitness values, This operations are being done on the offspring population.
                    del ind1.fitness.values, ind2.fitness.values
                self.toolbox.mutate(ind1)
                self.toolbox.mutate(ind2)

            # Calculating fitness for all the invalid individuals in offspring
            self.invalid_ind = [ind for ind in self.offspring if not ind.fitness.valid]
            self.fitnesses = self.toolbox.map(self.toolbox.evaluate, self.invalid_ind)
            for ind, fit in zip(self.invalid_ind, self.fitnesses):
                ind.fitness.values = fit
                #print(ind, fit)

            # Recalcuate the population with newly added offsprings and parents
            # We are using NSGA2 selection method, We have to select same population size
            self.pop = self.toolbox.select(self.pop + self.offspring, self.pop_size)

            # Recording stats in this generation
            recordStat(self.invalid_ind, self.logbook, self.pop, self.stats, gen + 1)
            #print(self.invalid_ind, self.fitnesses)

        print(f"{20 * '#'} End of Generations {20 * '#'} ")


    def getBestInd(self):
        self.best_individual = tools.selBest(self.pop, 1)[0]

        # Printing the best after all generations
        print(f"Best individual is {self.best_individual}")
        print(f"Number of vechicles required are "
              f"{self.best_individual.fitness.values[0]}")
        print(f"Cost required for the transportation is "
              f"{self.best_individual.fitness.values[1]}")

        # Printing the route from the best individual
        printRoute(routeToSubroute(self.best_individual, self.json_instance))

    def doExport(self):
        csv_file_name = f"{self.json_instance['instance_name']}_" \
                        f"pop{self.pop_size}_crossProb{self.cross_prob}" \
                        f"_mutProb{self.mut_prob}_numGen{self.num_gen}.csv"
        exportCsv(csv_file_name, self.logbook)

    def runMain(self):
        self.generatingPopFitness()
        self.runGenerations()
        self.getBestInd()
        self.doExport()

###################### 2ND METHOD ##############################################
"""
SELECT = ROULETTE 
MATE = ORDEREDVRP (CUSTOM CODE)
MUTATE = MUTATESHUFFLE
"""

class rouletteAlgo(object):
    #random.seed(20)
    def __init__(self):
        f  = open(r'...\data\json\Input_Data.json')
        self.json_instance = json.load(f)
        self.ind_size = self.json_instance['Number_of_customers']
        self.pop_size = 500
        self.cross_prob = 0.85
        self.mut_prob = 0.02
        self.num_gen = 800
        self.toolbox = base.Toolbox()
        self.logbook, self.stats = createStatsObjs()
        self.createCreators()

    def createCreators(self):
        creator.create('FitnessMin', base.Fitness, weights=(-1.0, -1.0))
        creator.create('Individual', list, fitness=creator.FitnessMin)

        # Registering toolbox
        self.toolbox.register('indexes', random.sample, range(1, self.ind_size + 1), self.ind_size)

        # Creating individual and population from that each individual
        self.toolbox.register('individual', tools.initIterate, creator.Individual, self.toolbox.indexes)
        self.toolbox.register('population', tools.initRepeat, list, self.toolbox.individual)

        # Creating evaluate function using our custom fitness
        #   toolbox.register is partial, *args and **kwargs can be given here
        #   and the rest of args are supplied in code
        self.toolbox.register('evaluate', eval_indvidual_fitness, instance=self.json_instance, unit_cost=1)

        # Selection method
        self.toolbox.register("select", tools.selNSGA2)

        # Crossover method
        self.toolbox.register("mate", cxOrderedVrp)

        # Mutation method
        self.toolbox.register("mutate", mutationShuffle, indpb=self.mut_prob)


    def generatingPopFitness(self):
        self.pop = self.toolbox.population(n=self.pop_size)
        self.invalid_ind = [ind for ind in self.pop if not ind.fitness.valid]
        self.fitnesses = list(map(self.toolbox.evaluate, self.invalid_ind))

        for ind, fit in zip(self.invalid_ind, self.fitnesses):
            ind.fitness.values = fit
        
        # this part is done just for sorting, no actual purpose, does not affect perf as well
        #self.pop = self.toolbox.select(self.pop, len(self.pop))
        
        # doing this is like elitism where u pick the top 10 or N individuals 
        self.pop = self.toolbox.select(self.pop, 250)

        recordStat(self.invalid_ind, self.logbook, self.pop, self.stats, gen = 0)


    def runGenerations(self):
        # Running algorithm for given number of generations
        for gen in range(self.num_gen):
            #print(f"{20*'#'} Currently Evaluating {gen} Generation {20*'#'}")

            # Selecting individuals
            # Selecting offsprings from the population, about 1/2 of them
            self.offspring = tools.selRoulette(self.pop,len(self.pop))
            self.offspring = [self.toolbox.clone(ind) for ind in self.offspring]

            # Performing , crossover and mutation operations according to their probabilities
            for ind1, ind2 in zip(self.offspring[::2], self.offspring[1::2]):
                # Mating will happen 80% of time if cross_prob is 0.8
                if random.random() <= self.cross_prob:
                    # print("Mating happened")
                    self.toolbox.mate(ind1, ind2)

                    # If cross over happened to the individuals then we are deleting those individual
                    #   fitness values, This operations are being done on the offspring population.
                    del ind1.fitness.values, ind2.fitness.values
                self.toolbox.mutate(ind1)
                self.toolbox.mutate(ind2)
                

            # Calculating fitness for all the invalid individuals in offspring, invalid means new mutated offsprings
            self.invalid_ind = [ind for ind in self.offspring if not ind.fitness.valid]
            self.fitnesses = self.toolbox.map(self.toolbox.evaluate, self.invalid_ind)
            for ind, fit in zip(self.invalid_ind, self.fitnesses):
                ind.fitness.values = fit
                # print(ind, fit) #this is to print the offsprings and its fitness 

            # Recalcuate the population with newly added offsprings and parents
            # We are using NSGA2 selection method, We have to select same population size
            self.pop = self.toolbox.select(self.pop + self.offspring, self.pop_size)

            # Recording stats in this generation
            recordStat(self.invalid_ind, self.logbook, self.pop, self.stats, gen + 1)
            

        #print(f"{20 * '#'} End of Generations {20 * '#'} ")


    def getBestInd(self):
        self.best_individual = tools.selBest(self.pop, 1)[0]

        # Printing the best after all generations
        # print(f"Best individual is {self.best_individual}")
        # print(f"Number of vechicles required are "
        #       f"{self.best_individual.fitness.values[0]}")
        # print(f"Cost required for the transportation is "
        #       f"{self.best_individual.fitness.values[1]}")

        # Printing the route from the best individual
        #printRoute(routeToSubroute(self.best_individual, self.json_instance))

    def doExport(self):
        csv_file_name = f"{self.json_instance['instance_name']}_" \
                        f"pop{self.pop_size}_crossProb{self.cross_prob}" \
                        f"_mutProb{self.mut_prob}_numGen{self.num_gen}.csv"
        exportCsv(csv_file_name, self.logbook)

    def runMain(self):
        self.generatingPopFitness()
        self.runGenerations()
        self.getBestInd()
        self.doExport()
        


################### MAIN RUNING ##################################
if __name__ == "__main__":
    print("Running file directly, Executing nsga2vrp")
    # nsga2vrp()
    ## 1st algo test 
    # someinstance = nsgaAlgo()
    # someinstance.runMain()
    
    ## 2nd algo test 
    
    best_fit1 = []
    best_fit2 = []
    
    for i in range(10,20):
        random.seed(i)

        someinstance =rouletteAlgo()
        someinstance.runMain()
        
        best_fit1.append(someinstance.best_individual.fitness.values[0]) 
        best_fit2.append(someinstance.best_individual.fitness.values[1])
    
    avg_best_fit1 = sum(best_fit1)/len(best_fit1)
    avg_best_fit2 = sum(best_fit2)/len(best_fit2)
    numgen = someinstance.num_gen
    
    print("Number of Generations = ", numgen)
    print("Avg best total vehicles = ", round(avg_best_fit1,2))
    print("Avg best total transportation cost = ", round(avg_best_fit2,4))
    print("Number of iterations = ", len(best_fit2))
    
    # someinstance.generatingPopFitness()
    #
    # print(f"Pop here is {someinstance.pop[0]}")
    # print(f"Fit here is {someinstance.pop[0].fitness.values}")
    # # Running generations
    # someinstance.runGenerations()

    # someinstance.testFunc()




################## ADDITIONAL TESTING ###################################

def testcosts():
    # Sample instance
    test_instance = load_instance('./data/json/Input_Data.json')

    # Sample individual
    sample_individual = [19, 5, 24, 7, 16, 23, 22, 2, 12, 8, 20, 25, 21, 18,11,15, 1, 14, 17, 6, 4, 13, 10, 3, 9]

    # Sample individual 2
    sample_ind_2 = random.sample(sample_individual, len(sample_individual))
    print(f"Sample individual is {sample_individual}")
    print(f"Sample individual 2 is {sample_ind_2}")

    # Cost for each route
    print(f"Sample individual cost is {getRouteCost(sample_individual, test_instance, 1)}")
    print(f"Sample individual 2 cost is {getRouteCost(sample_ind_2, test_instance, 1)}")

    # Fitness for each route
    print(f"Sample individual fitness is {eval_indvidual_fitness(sample_individual, test_instance, 1)}")
    print(f"Sample individual 2 fitness is {eval_indvidual_fitness(sample_ind_2, test_instance, 1)}")

def testroutes():
    # Sample instance
    test_instance = load_instance('./data/json/Input_Data.json')

    # Sample individual
    sample_individual = [19, 5, 24, 7, 16, 23, 22, 2, 12, 8, 20, 25, 21, 18,11,15, 1, 14, 17, 6, 4, 13, 10, 3, 9]
    best_ind_300_gen = [16, 14, 12, 10, 15, 17, 21, 23, 11, 9, 8, 20, 18, 19, 13, 22, 25, 24, 5, 3, 4, 6, 7, 1, 2]


    # Sample individual 2
    sample_ind_2 = random.sample(sample_individual, len(sample_individual))
    print(f"Sample individual is {sample_individual}")
    print(f"Sample individual 2 is {sample_ind_2}")
    print(f"Best individual 300 generations is {best_ind_300_gen}")

    # Getting routes
    print(f"Subroutes for first sample individual is {routeToSubroute(sample_individual, test_instance)}")
    print(f"Subroutes for second sample indivudal is {routeToSubroute(sample_ind_2, test_instance)}")
    print(f"Subroutes for best sample indivudal is {routeToSubroute(best_ind_300_gen, test_instance)}")

    # Getting num of vehicles
    print(f"Vehicles for sample individual {getNumVehiclesRequired(sample_individual, test_instance)}")
    print(f"Vehicles for second sample individual {getNumVehiclesRequired(sample_ind_2, test_instance)}")
    print(f"Vehicles for best sample individual {getNumVehiclesRequired(best_ind_300_gen, test_instance)}")

def testcrossover():
    ind1 = [3,2,5,1,6,9,8,7,4]
    ind2 = [7,3,6,1,9,2,4,5,8]
    anotherind1 = [16, 14, 12, 7, 4, 2, 1, 13, 15, 8, 9, 6, 3, 5, 17, 18, 19, 11, 10, 21, 22, 23, 25, 24, 20]
    anotherind2 = [21, 22, 23, 25,16, 14, 12, 7, 4, 2, 1, 13, 15, 8, 9, 6, 3, 5, 17, 18, 19, 11, 10, 24, 20]


    newind7, newind8 = cxOrderedVrp(ind1, ind2)
    newind9, newind10 = cxOrderedVrp(anotherind1, anotherind2)

    print(f"InpInd1 is {ind1}")
    print(f"InpInd2 is {ind2}")
    # print(f"New_ind is {[x-1 for x in ind1]}")
    print(f"newind7 is {newind7}")
    print(f"newind8 is {newind8}")
    print(f"newind9 is {newind9}")
    print(f"newind10 is {newind10}")

def testmutation():
    ind1 = [3,2,5,1,6,9,8,7,4]
    mut1 = mutationShuffle(ind1)

    print(f"Given individual is {ind1}")
    print(f"Mutation from first method {mut1}")
