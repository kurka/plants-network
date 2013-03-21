#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import random
import datetime
import threading
import pickle
from network import *
from multiprocessing import Pool

#evolution constrains
_TESTS_PER_INDIVIDUAL = 50      #amount of tests by individual
_RESULT_FILE = "rules/result_" #dat"
_ITERATIONS = 100                 #how many iterations each individual will try to survive
_LOWER_ENERGY_LIMIT_DANGER = 40   #absolute lower limit. If the node stay bellow this level for G generations, it dies
_UPPER_ENERGY_LIMIT_DANGER = 60   #absolute upper limit. If the node stay above this level for G generations, it dies
_GENERATIONS_IN_DANGER_LIMIT = 3  #maximum # of generations the node can stay in danger level
_MAX_ENERGY_INPUT = 10            #maximum amount of energy inputed to the system during execution
_NOISE_DURING = False             #apply (or not) noise during execution

#network constrains
_NODE_VALUES_RANGE = 100          #range of network's nodes value
_N_NODES = 1000                   #total number of nodes in the network
_N_CONNECTIONS = 4                #number of connections per node
_N_EDGES = 2*_N_NODES             #total number of edges
#small-world specs
_P = 0.04                         #chance of rewiring
#scale-free specs
_M_ZERO = 10                      #initial nodes in the scale-free network
_M = 2                            #number of added connections per iteration in the scale-free network
#von-neumann specs
_LIN_SIZE = 40                    #dimensions of von-neumann grid 
_COL_SIZE = 25                    #WARNING: _LIN_SIZE * _COL_SIZE must be equal _N_NODES

random.seed()

def get_genome_from_file(filename):
    pickle_file = open(filename, "rb")
    genome_population = pickle.load(pickle_file)
    genome = genome_population[-1][0] #get the last genome, to test. if the list is initialized, it will contain the best individual

def create_my_network(args):
    #create network from file resulting of the evolution
    n_nodes = args[0]
    genome = args[1]

    #generate network from genome 
    network = Network(n_nodes)
    network.initialize_from_genome(genome)
    return network

def create_small_world(args):
    return SmallWorldNetwork(args[0], args[1], args[2]) #n_nodes, n_connections, p

def create_local(args):
    return LocalNetwork(args[0], args[1]) #n_nodes, n_connections

def create_global(args):
    return GlobalNetwork(args[0]) #n_nodes

def create_von_neuman(args):
    return VonNeumannNetwork(args[0], args[1], args[2]) #n_nodes, grid_lines, grid_columns

def create_random(args):
    return RandomNetwork(args[0], args[1]) #n_nodes, n_edges

def create_scale_free(args):
    return ScaleFreeNetwork(args[0], args[1], args[2]) #n_nodes, m_zero, m (m < m_zero)

def run_test(candidates, create_net_func, func_args, init_noise=[]):
    ##run execution in paralel
    pool = Pool()
    map_args = [[candidates[i], create_net_func, func_args, init_noise] for i in range(_NODE_VALUES_RANGE**2)]
    candidates = pool.map(iteration, map_args)

    #linear (old):
    #candidates = []
    #for i in range(_NODE_VALUES_RANGE**2):
    #    candidates.append(iteration(map_args[i]))

    #sort candidates by fitness
    candidates.sort(key = lambda x: x[2]) #Sort the sample by fitness
    return candidates


def iteration(args):
    candidate = args[0]
    create_net_func = args[1]
    func_args = args[2]
    init_noise = args[3]

    partial_fitness = 0

    for j in range(_TESTS_PER_INDIVIDUAL):
        network = create_net_func(func_args)
        #initialize network with values
        if not _NOISE_DURING:
            NoiseControl.apply_random_noise(network, init_noise[j])
        else:
            NoiseControl.apply_regular_noise(network, (_LOWER_ENERGY_LIMIT_DANGER+_UPPER_ENERGY_LIMIT_DANGER)/2)

        old_values_list = network.get_values()
        similar_runs = 0
        #run for certain time
        for k in range(_ITERATIONS):
            #[input energy]
            if(_NOISE_DURING):
                NoiseControl.apply_random_noise(network, noise_range=_MAX_ENERGY_INPUT, negative_range=True) #TODO: dont randomize every time
            #run network
            network.run(candidate[0], candidate[1]) #test candidates rule
            #update network
            network.update_network(_LOWER_ENERGY_LIMIT_DANGER, _UPPER_ENERGY_LIMIT_DANGER, _GENERATIONS_IN_DANGER_LIMIT)
            new_values_list = network.get_values()
            if new_values_list == old_values_list: #check if there was really an update. if not, you don't need more iterations
                similar_runs += 1
            else:
                similar_runs = 0
            if similar_runs == 3:
                break
            old_values_list = new_values_list #update list os values for next iteration

        #evaluate fitness of the individual
        partial_fitness += network.count_survivors()
    #network.print_network(True)
    fitness = partial_fitness / float(_TESTS_PER_INDIVIDUAL)
    print(candidate[0], candidate[1], fitness)
    #print(fitness)
    candidate[2] = fitness #store the fitness in candidate
    return candidate

def main(argv):
    if len(argv) == 3:
        #usage: rules_evolution [n_nodes] [pickle_file]
        genome = get_genome_from_file(argv[1], argv[2])


    ########create the candidates
    #each candidate is a pair of LOWER_LIMIT, HIGHER_LIMIT numbers plus a fitness value (initially 0)
    candidates = []
    values_range = _NODE_VALUES_RANGE
    for i in range(values_range):
        for j in range(values_range):
            candidates.append([i,j,0])

    ########create noise
    if not _NOISE_DURING:
        #generate random noise to be inputed in all networks tested
        noise = []
        for i in range(_TESTS_PER_INDIVIDUAL):
            noise.append(NoiseControl.random_noise_generator(_N_NODES, _NODE_VALUES_RANGE))
    else:
        noise = []

    ########run tests
    test_params = [
        #[candidates.copy(), create_local, [_N_NODES, _N_CONNECTIONS], noise],  #local args
        #[candidates.copy(), create_small_world, [_N_NODES, _N_CONNECTIONS, _P], noise], #small world args
        #[candidates.copy(), create_von_neuman, [_N_NODES, 40, 25], noise], #von neuman args
        #[candidates.copy(), create_random, [_N_NODES, _N_EDGES], noise], #random args
        #[candidates.copy(), create_global, [_N_NODES], noise], #global args
        [candidates.copy(), create_scale_free, [_N_NODES, _M_ZERO, _M], noise] #scale free
    ]

    results = []
    for i in range(len(test_params)):
        print(">>>>>>>>>> TEST", i)
        results = run_test(test_params[i][0], test_params[i][1], test_params[i][2], test_params[i][3])
        #copy candidates population to a file
        result_file = open(_RESULT_FILE+test_params[i][1].__name__+".dat", "wb")
        pickle.dump(results, result_file)
        result_file.close()



if __name__ == "__main__":
    main(sys.argv)

