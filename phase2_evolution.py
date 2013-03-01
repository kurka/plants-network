#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import random
import datetime
#import threading
from multiprocessing import Pool
import pickle
from network import *
import math
#from numpy import var, std, sqrt


#evolution constrains
_POPULATION_SIZE = 50            #size of genome's population
_TESTS_PER_INDIVIDUAL = 1000       #amount of tests by individual
_GENERATIONS = 50                 #amount of generations the program will evolve
_SELECTION_SAMPLE_SIZE = 2       #size of the random sample group where the best ranked will be father or mother
_MUTATION_RATE = 0.02             #chance of gene being mutated
_PARENTS_SELECTED = 0             #number of individuals that will stay without crossover or mutation for the next generation (elitist selection)
_LOG_FILE = "logs/evolutionmulti.txt"

#network constrains
_N_NODES = 1000                   #number of nodes in the network
_TOTAL_CONNECTIONS = int(2*_N_NODES)  #fixed amount of connections, distributed in the graph
_NODE_VALUES_RANGE = 100          #range of network's nodes value
_ITERATIONS = 10                  #how many iterations each individual will try to survive
_LOWER_ENERGY_LIMIT_RULE = 45     #lower limit of energy used in rule (the node will *try* to stay above it)
_UPPER_ENERGY_LIMIT_RULE = 55     #upper limit of energy used in rule (the node will *try* to stay under it)
_LOWER_ENERGY_LIMIT_DANGER = 40   #absolute lower limit. If the node stay bellow this level for G generations, it dies
_UPPER_ENERGY_LIMIT_DANGER = 60   #absolute upper limit. If the node stay above this level for G generations, it dies
_GENERATIONS_IN_DANGER_LIMIT = 3  #maximum # of generations the node can stay in danger level
_MAX_ENERGY_INPUT = 10            #maximum amount of energy inputed to the system during execution

_MATRIX_SIZE = int(((_N_NODES-1)*_N_NODES)/2)

random.seed()

def run_individual(args):

    #print(">>starting process")

    individual = args[0]
    noise = args[1]

    partial_fitness = 0

    for j in range(_TESTS_PER_INDIVIDUAL):
        #generate network from genome 
        network = Network(_N_NODES)
        network.initialize_from_genome(individual[0])

        #initialize network with values
        NoiseControl.apply_random_noise(network, noise[j])

        old_values_list = network.get_values()
        similar_runs = 0
        #run for certain time
        for k in range(_ITERATIONS):
            #[input energy]
            #NoiseControl.apply_random_noise(network, noise_range=_MAX_ENERGY_INPUT, negative_range=True)
            #run network
            network.run(_LOWER_ENERGY_LIMIT_RULE, _UPPER_ENERGY_LIMIT_RULE)
            #update network
            network.update_network(_LOWER_ENERGY_LIMIT_DANGER, _UPPER_ENERGY_LIMIT_DANGER, _GENERATIONS_IN_DANGER_LIMIT)
            #[lose energy]
            new_values_list = network.get_values()
            if new_values_list == old_values_list: #check if there was really an update. if not, you don't need more iterations
                similar_runs += 1
            else:
                similar_runs = 0
            if similar_runs == 3:
                break
            old_values_list = new_values_list #update list os values for next iteration

        #evaluate fitness of the individual
        indiv_fitness = network.count_survivors()
        partial_fitness += indiv_fitness

    #network.print_network(True)
    fitness = partial_fitness / float(_TESTS_PER_INDIVIDUAL)
    individual[1] = fitness
    #print("<<closing process")
    return individual



class Evolution:
    def __init__(self, population_size, n_nodes, total_connections, start_from_file=False, bkp_file_path=""):
        self.individuals = []
        self.n_nodes = n_nodes
        self.pop_size = population_size
        self.noise = []
        self.generation = 0 #keep track of which generation is currently in
        #paralelizing the work
        self.pool = Pool()

        #initialize the log file
        self.log_file = open(_LOG_FILE, 'a')
        t0 = datetime.datetime.now()

        #each individual is represented by an array, of size |total_connections|, with the 'address' of its connections in the connections_matrix
        self.genome_size = total_connections

        #To represent the connections in the network, we are using a matrix of size n_nodesXn_nodes. 
        #(i.e: When connections_matrix[i][j] == 1, there is a connection between nodes i and j)
        #To save space, as [i][j] == [j][i] (the graph isn't directional) and i != j (no self connections),
        # we will just store the triangular part of the matrix, above the main diagonal, in an array.
        self.matrix_size = int(((n_nodes - 1)*n_nodes)/2) #this is the size of the triangular region lower to the main diagonal of the matrix.

        if not start_from_file: #create individuals randomly
            #generate individuals as samples of |genome_size| from the possible connections_matrix slots.
            for i in range(population_size):
                connections = random.sample(range(self.matrix_size), self.genome_size) #get a genome_size sample in a matrix_size range
                self.individuals.append([connections,0.0]) #add individual and fitness to individual array
            self.log_file.write("--------------------------- " + str(t0) + " -----------------------------" + "\n")

        if start_from_file: #created individuals from a previous execution (used to continue broken executions)
            bkp_file = open(bkp_file_path, "rb")
            self.individuals = pickle.load(bkp_file)
            self.log_file.write(">>>>>>>>>>>>>>>>> Continuing from previous execution. " + str(t0) + "\n")

        self.log_file.close()


    def step(self):

        #save population in a file, to be able to restore it
        filename = "execution/genome"
        bkp = open("execution/genome_"+str(self.generation)+"_initial.dat", "wb")
        pickle.dump(self.individuals, bkp)
        bkp.close()


        #generate random noise to be inputed in all networks tested in this generation
        for i in range(_TESTS_PER_INDIVIDUAL):
            self.noise.append(NoiseControl.random_noise_generator(self.n_nodes, _NODE_VALUES_RANGE))

        #old:
        #for i in range(self.pop_size):
        #    self.run_individual(i) 

        args = [[self.individuals[i], self.noise] for i in range(self.pop_size)]
        self.individuals = self.pool.map(run_individual, args)

        #order individuals by fitness
        self.individuals.sort(key = lambda x: x[1]) #Sort the sample by fitness


        #copy genome population to a file, to be able to start from this population, in case of broken execution
        bkp = open("execution/genome_"+str(self.generation)+"_fitness.dat", "wb")
        pickle.dump(self.individuals, bkp)
        bkp.close()


    def evolute(self):
        new_generation = []

        #keep some of them in new generation (elitist selection)
        for i in range(_PARENTS_SELECTED):
            new_generation.append([self.individuals[self.pop_size-1-i][0], 0])

        #create the rest as combination of two parents
        for i in range(self.pop_size - _PARENTS_SELECTED):
            #select parents to reproduce
            father = self.select(_SELECTION_SAMPLE_SIZE)
            mother = self.select(_SELECTION_SAMPLE_SIZE)
            #generate new individuals
            child = self.sex(father, mother, _MUTATION_RATE)
            new_generation.append([child, 0])

        self.individuals = new_generation #Exchange old individuals with the new generation
        self.generation += 1


    def select(self, sample_size):
        sample = random.sample(self.individuals, sample_size) #get a sample, to select the parent
        sample.sort(key = lambda x: x[1]) #Sort the sample by fitness
        return sample[-1][0] #Return phenotype of the best individual

    def sex(self, father, mother, mutation_rate):
        #1-crossover
        #put the parents genes in a bag, removing duplicates
        bag = list(set(father+mother))
        #the child will be a sample from this bag
        child = random.sample(bag, self.genome_size)

        #2-mutation
        for i in range(len(child)): #There is a mutation_rate of being changed for each gene of the phenotype
            if random.random() < mutation_rate:
                #the mutation will create a new edge, changing only one side of it (keeping one of the nodes with the same number of connections)
                old_gene_line, old_gene_column = self.array_to_matrix(child[i])
                new_gene_column = random.randrange(self.n_nodes) #choose which node will receive the new end of the edge
                new_gene = self.matrix_to_array(old_gene_line, new_gene_column)
                while(new_gene in child): #it need to be unique
                    new_gene_column = random.randrange(self.n_nodes)
                    new_gene = self.matrix_to_array(old_gene_line, new_gene_column)
                child[i] = new_gene

        return child

    def matrix_to_array(self, line, column):
        #given a pair of lower triangular matrix coordinates, return its position in an compacted array
        pos = int( (line * (line - 1)) / 2 + column)
        return pos

    def array_to_matrix(self, pos):
        #given an position in an array, return it equivalent position in a matrix
        line = int((1 + math.sqrt(1 + 8*pos)) / 2.0)
        column = int(pos - (line * (line-1)) / 2.0)

        return line, column


    def print_results(self):
        #print best result, avg result, median, worst and the phenotype (represented in hexadecimal) of the best result
        best = self.individuals[self.pop_size-1][1] #self.individuals list was sorted in beggining of evolution method
        median = self.individuals[round(self.pop_size/2)][1]
        worst = self.individuals[0][1]
        fitness_sum = sum([fit[1] for fit in  self.individuals])
        avg = fitness_sum/float(self.pop_size)

        best_phenotype = self.individuals[self.pop_size-1][0].copy()
        best_phenotype.sort()

        #print in the output
        print("generation:", self.generation)
        print("Best =", best, "avg =", avg, "median=", median, "worst =", worst)
        #print("Best phenotype:")
        #print(best_phenotype)

        #print in file
        self.log_file = open(_LOG_FILE, 'a') #open and close file every print, to save broken executions

        self.log_file.write("generation: " + str(self.generation) + "\n")
        self.log_file.write("Best = " + str(best) + " avg = " + str(avg) + " median= " + str(median) + " worst = " + str(worst) + "\n")
        self.log_file.write("Best phenotype:" + "\n")
        self.log_file.write(str(best_phenotype) + "\n")

        self.log_file.close()



def program(argv):

    #evolution of the network
    if len(argv) > 1:
        bkp_file = argv[1]
        use_file = True
    else:
        bkp_file = ""
        use_file = False

    #generate initial population P
    evolution = Evolution(_POPULATION_SIZE, _N_NODES, _TOTAL_CONNECTIONS, use_file, bkp_file)
    for i in range(_GENERATIONS):
        print(">>>>>>GENERATION", i)
        #run program
        evolution.step()
        evolution.print_results()
        #evolve
        evolution.evolute()
    print(">>>>>>FINAL RESULT:")
    for i in range(len(evolution.individuals)):
            print(evolution.individuals[i][0])

def main(argv):

    #import cProfile
    #cProfile.run("program(sys.argv)", "test.profile")
    program(argv)

if __name__ == "__main__":
    main(sys.argv)

