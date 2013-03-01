#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import random
import datetime
import threading
import pickle
from network import *

#evolution constrains
_TESTS_PER_INDIVIDUAL = 10      #amount of tests by individual
_LOG_FILE = "logs/rule.txt"

#network constrains
_NODE_VALUES_RANGE = 100          #range of network's nodes value
_ITERATIONS = 20                  #how many iterations each individual will try to survive
_LOWER_ENERGY_LIMIT_DANGER = 40   #absolute lower limit. If the node stay bellow this level for G generations, it dies
_UPPER_ENERGY_LIMIT_DANGER = 60   #absolute upper limit. If the node stay above this level for G generations, it dies
_GENERATIONS_IN_DANGER_LIMIT = 3  #maximum # of generations the node can stay in danger level


random.seed()

    n_nodes = int(argv[1]) #number of nodes in the network

    #generate connections_matrix, from the genome
    connections_matrix = [0] * matrix_size #initialize with zeroes 
    for connection in genome:
        connections_matrix[connection] = 1 #replace to 1, the edges indicated in the genome

    #analyse frequency of connections, among the population
    #connections_frequency(genome_population)

    #create Network object
    #net = create_network_net(n_nodes, connections_matrix)
    #net.print_network(True)

def main(argv):
    if len(argv) != 3:
        print("usage: rules_evolution [n_nodes] [pickle_file]")
        print(len(argv))
        return

    ##create network
    #the network will be chosen from the result of the network evolution
    n_nodes = int(argv[1]) #number of nodes in the network
    matrix_size = int(((n_nodes - 1)*n_nodes)/2) #this is the size of the triangular region lower to the main diagonal of the matrix.
    pickle_file = open(argv[2], "rb")
    genome_population = pickle.load(pickle_file)
    pop_size = len(genome_population)
    genome = genome_population[-1][0] #get the last genome, to test. if the list is initialized, it will contain the best individual

    #generate network from genome 
    network = Network(n_nodes)
    network.initialize_from_genome(genome)


    ##create the candidates
    #each candidate is a pair of LOWER_LIMIT, HIGHER_LIMIT numbers plus a fitness value (initially 0)
    #as the number of possible combinations is not that high (_NODE_VALUES_RANGE**2), we can test all of them.
    candidates = []
    values_range = _NODE_VALUES_RANGE
    for i in range(values_range):
        for j in range(values_range):
            candidates.append([i,j,0])
    print(candidates)
    ##run execution
    #generate random noise to be inputed in all networks tested
    noise = []
    for i in range(_TESTS_PER_INDIVIDUAL):
        noise.append(NoiseControl.random_noise_generator(n_nodes, _NODE_VALUES_RANGE))

    for i in range(values_range*values_range):
        partial_fitness = 0
        print(i)

        for j in range(_TESTS_PER_INDIVIDUAL):
            network = Network(n_nodes)
            network.initialize_from_genome(genome) #FIXME: dont need to create everytime
            #initialize network with values
            NoiseControl.apply_random_noise(network, noise[j])

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
        print(fitness)
        candidates[i][2] = fitness #store the fitness in candidate

    #sort candidates by fitness
    candidates.sort(key = lambda x: x[2]) #Sort the sample by fitness



    #copy candidates population to a file
    result_file = open("rules_result.dat", "wb")
    pickle.dump(candidates, result_file)
    result_file.close()

    print("100 best rules:")
    print("format: (lower, high, fitness)")
    for i in range(1, 1001):
        print(candidates[-i][0], candidates[i][1], candidates[i][2])

    #TODO: enhance print_results



if __name__ == "__main__":
    main(sys.argv)

