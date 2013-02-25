#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import random
import datetime
import threading
import pickle
from network import *


#evolution constrains
_POPULATION_SIZE = 200            #size of genome's population
_TESTS_PER_INDIVIDUAL = 500       #amount of tests by individual
_GENERATIONS = 50                 #amount of generations the program will evolve
_SELECTION_SAMPLE_SIZE = 20       #size of the random sample group where the best ranked will be father or mother
_MUTATION_RATE = 0.02             #chance of gene being mutated
_PARENTS_SELECTED = 0             #number of individuals that will stay without crossover or mutation for the next generation (elitist selection)
_LOG_FILE = "logs/evolution100.txt"

#network constrains
_N_NODES = 1000                   #number of nodes in the network
_TOTAL_CONNECTIONS = int(1.5*_N_NODES)  #fixed amount of connections, distributed in the graph
_NODE_VALUES_RANGE = 100          #range of network's nodes value
_ITERATIONS = 400                 #how many iterations each individual will try to survive
_LOWER_ENERGY_LIMIT_RULE = 45     #lower limit of energy used in rule (the node will *try* to stay above it)
_UPPER_ENERGY_LIMIT_RULE = 55     #upper limit of energy used in rule (the node will *try* to stay under it)
_LOWER_ENERGY_LIMIT_DANGER = 40   #absolute lower limit. If the node stay bellow this level for G generations, it dies
_UPPER_ENERGY_LIMIT_DANGER = 60   #absolute upper limit. If the node stay above this level for G generations, it dies
_GENERATIONS_IN_DANGER_LIMIT = 3  #maximum # of generations the node can stay in danger level
_MAX_ENERGY_INPUT = 10            #maximum amount of energy inputed to the system during execution


random.seed()

class Evolution:
    def __init__(self, population_size, n_nodes, total_connections, start_from_file=False, bkp_file_path=""):
        self.individuals = []
        self.n_nodes = n_nodes
        self.pop_size = population_size
        self.noise = []

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

        #generate random noise to be inputed in all networks tested in this generation
        for i in range(_TESTS_PER_INDIVIDUAL):
            self.noise.append(NoiseControl.random_noise_generator(self.n_nodes, _NODE_VALUES_RANGE))

        #old:
        #for i in range(self.pop_size):
        #    self.run_individual(i) #TODO: thread this
			
        threads = []	
        for i in range(self.pop_size):
            t = threading.Thread(target=self.run_individual, args=(i,))
            t.start()
            threads.append(t)

        for i in range(self.pop_size):
            threads[i].join() #wait for all threads to finish

        #order individuals by fitness
        self.individuals.sort(key = lambda x: x[1]) #Sort the sample by fitness


		#copy genome population to a file, to be able to start from this population, in case of broken execution
        bkp = open("genome.dat", "wb")
        pickle.dump(self.individuals, bkp)
        bkp.close()

    def run_individual(self, num):
	
        print(">>starting thread ", num)
		
        #generate connections_matrix, from the genome
        connections_matrix = [0] * self.matrix_size #initialize with zeroes 
        for connection in self.individuals[num][0]:
            connections_matrix[connection] = 1 #replace to 1, the edges indicated in the genome

        partial_fitness = 0

        for j in range(_TESTS_PER_INDIVIDUAL):
            #generate network from genome 
            network = Network(self.n_nodes)
            network.initialize_from_matrix(connections_matrix)

            #initialize network with values
            NoiseControl.apply_random_noise(network, self.noise[j])

            old_values_list = network.get_values()
            #run for certain time
            for k in range(_ITERATIONS):
                #[input energy]
                NoiseControl.apply_random_noise(network, noise_range=_MAX_ENERGY_INPUT, negative_range=True)
                #run network
                network.run(_LOWER_ENERGY_LIMIT_RULE, _UPPER_ENERGY_LIMIT_RULE)
                #update network
                network.update_network(_LOWER_ENERGY_LIMIT_DANGER, _UPPER_ENERGY_LIMIT_DANGER, _GENERATIONS_IN_DANGER_LIMIT)
                #[lose energy]
                new_values_list = network.get_values()
                if new_values_list == old_values_list: #check if there was really an update. if not, you don't need more iterations
                    break
                old_values_list = new_values_list #update list os values for next iteration
                if k==_ITERATIONS-1:
                    print("went until the end!")

            #evaluate fitness of the individual
            partial_fitness += network.count_survivors()
        #network.print_network(True)
        fitness = partial_fitness / float(_TESTS_PER_INDIVIDUAL)
        self.individuals[num][1] = fitness

        print("<<closing thread ", num)



    def evolute(self, gen):
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

        #copy genome population to a file, to be able to start from this population, in case of broken execution
        bkp = open("genome_"+str(gen)+".dat", "wb")
        pickle.dump(self.individuals, bkp)
        bkp.close()


    def select(self, sample_size):
        sample = random.sample(self.individuals, sample_size) #get a sample, to select the parent
        sample.sort(key = lambda x: x[1]) #Sort the sample by fitness
        return sample[sample_size - 1][0] #Return phenotype of the best individual

    def sex(self, father, mother, mutation_rate):
        #1-crossover

        #put the parents genes in a bag, removing duplicates
        bag = list(set(father+mother))
        #the child will be a sample from this bag
        child = random.sample(bag, self.genome_size)

        #2-mutation
        for i in range(len(child)): #There is a mutation_rate of being changed for each gene of the phenotype
            if random.random() < mutation_rate:
                new_gene = random.randrange(self.genome_size) #choose a new gene randomly #TODO: choose only from neighbours
                while(new_gene in child): #it need to be unique
                    new_gene = random.randrange(self.genome_size)
                child[i] = new_gene

        return child

    def print_results(self, generation):
        #print best result, avg result, median, worst and the phenotype (represented in hexadecimal) of the best result
        best = self.individuals[self.pop_size-1][1] #self.individuals list was sorted in beggining of evolution method
        median = self.individuals[round(self.pop_size/2)][1]
        worst = self.individuals[0][1]
        fitness_sum = sum([fit[1] for fit in  self.individuals])
        avg = fitness_sum/float(self.pop_size)

        best_phenotype = self.individuals[self.pop_size-1][0].copy()
        best_phenotype.sort()

        #print in the output
        print("generation:", generation)
        print("Best =", best, "avg =", avg, "median=", median, "worst =", worst)
        print("Best phenotype:")
        print(best_phenotype)

        #print in file
        self.log_file = open(_LOG_FILE, 'a') #open and close file every print, to save broken executions

        self.log_file.write("generation: " + str(generation) + "\n")
        self.log_file.write("Best = " + str(best) + " avg = " + str(avg) + " median= " + str(median) + " worst = " + str(worst) + "\n")
        self.log_file.write("Best phenotype:" + "\n")
        self.log_file.write(str(best_phenotype) + "\n")

        self.log_file.close()



def main(argv):

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
        evolution.print_results(i)
        #evolve
        evolution.evolute(i)
    print(">>>>>>FINAL RESULT:")
    for i in range(len(evolution.individuals)):
            print(evolution.individuals[i][0])

if __name__ == "__main__":
    main(sys.argv)

