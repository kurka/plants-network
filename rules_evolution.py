#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import random
import datetime
import threading
import pickle
from network import *

#evolution constrains
_POPULATION_SIZE = 500            #size of genome's population
_TESTS_PER_INDIVIDUAL = 1000      #amount of tests by individual
_GENERATIONS = 50                 #amount of generations the program will evolve
_SELECTION_SAMPLE_SIZE = 20       #size of the random sample group where the best ranked will be father or mother
_MUTATION_RATE = 0.02             #chance of gene being mutated
_PARENTS_SELECTED = 0             #number of individuals that will stay without crossover or mutation for the next generation (elitist selection)
_LOG_FILE = "logs/rule.txt"

#network constrains
_N_NODES = 100                    #number of nodes in the network
_TOTAL_CONNECTIONS = 2*_N_NODES   #fixed amount of connections, distributed in the graph
_NODE_VALUES_RANGE = 100          #range of network's nodes value
_ITERATIONS = 20                  #how many iterations each individual will try to survive
_LOWER_ENERGY_LIMIT_RULE = 40     #lower limit of energy used in rule (the node will *try* to stay above it)
_UPPER_ENERGY_LIMIT_RULE = 60     #upper limit of energy used in rule (the node will *try* to stay under it)
_LOWER_ENERGY_LIMIT_DANGER = 30   #absolute lower limit. If the node stay bellow this level for G generations, it dies
_UPPER_ENERGY_LIMIT_DANGER = 70   #absolute upper limit. If the node stay above this level for G generations, it dies
_GENERATIONS_IN_DANGER_LIMIT = 3  #maximum # of generations the node can stay in danger level
_MAX_ENERGY_INPUT = 10            #maximum amount of energy inputed to the system 


random.seed()

def main(argv):
    if len(argv) != 3:
        print("usage: analyse_result [n_nodes] [list]")
        return

    ##create network
    #the network will be chosen from the result of the network evolution
    n_nodes = int(argv[1]) #number of nodes in the network
    matrix_size = int(((n_nodes - 1)*n_nodes)/2) #this is the size of the triangular region lower to the main diagonal of the matrix.
    network_genome = eval(argv[2])

    #generate connections_matrix, from the network_genome
    connections_matrix = [0] * matrix_size #initialize with zeroes 
    for connection in network_genome:
        connections_matrix[connection] = 1 #replace to 1, the edges indicated in the genome

    #generate network from genome 
    network = Network(n_nodes)
    network.initialize_from_matrix(connections_matrix)


    ##create the candidates
    #each candidate is a pair of LOWER_LIMIT, HIGHER_LIMIT numbers plus a fitness value (initially 0)
    #as the number of possible combinations is not that high (_NODE_VALUES_RANGE**2), we can test all of them.
    candidates = []
    values_range = _NODE_VALUES_RANGE
    for i in range(values_range):
        for j in range(values_range):
            candidates.append([i,j,0])

    ##run execution
    #generate random noise to be inputed in all networks tested 
    for i in range(_TESTS_PER_INDIVIDUAL):
        self.noise.append(NoiseControl.random_noise_generator(self.n_nodes, _NODE_VALUES_RANGE))

    for i in range(values_range*values_range)
        partial_fitness = 0

        for j in range(_TESTS_PER_INDIVIDUAL):
            #initialize network with values
            NoiseControl.apply_random_noise(network, self.noise[j])

            #run for certain time
            for k in range(_ITERATIONS):
                #[input energy]
                #run network
                network.run(candidates[i][0], candidates[i][1]) #test candidates rule
                #update network
                network.update_network(_LOWER_ENERGY_LIMIT_DANGER, _UPPER_ENERGY_LIMIT_DANGER, _GENERATIONS_IN_DANGER_LIMIT)

            #evaluate fitness of the individual
            partial_fitness += network.count_survivors()
        #network.print_network(True)
        fitness = partial_fitness / float(_TESTS_PER_INDIVIDUAL)
        candidates[i][2] = fitness #store the fitness in candidate

        #isort candidates by fitness
        candidates.sort(key = lambda x: x[2]) #Sort the sample by fitness



        #copy candidates population to a file
        result_file = open("rules_result.dat", "wb")
        pickle.dump(candidates, bkp)
        result_file.close()

        print("10 best rules:")
        print("format: (lower, high, fitness)")
        for i in range(10):
            print(candidates[i][0], candidates[i][1], candidates[i][2]

        #TODO: enhance print_results



if __name__ == "__main__":
    main(sys.argv)

