#!/usr/bin/env python
# -*- coding: utf-8 -*-
#ensinando git pro marcos
import random
import datetime
import math


#constants 
_ITERATIONS = 20                    #number of cycles the sytem will run
_N_NODES = 10                       #number of nodes in the network
_N_CONNECTIONS = 2                  #number of initial connections of each node
_P = 0.1                            #probability of rewire
_NODE_VALUES_RANGE = 100            #range of values received
_LOWER_ENERGY_LIMIT_RULE = 40       #lower limit of energy used in rule (the node will *try* to stay above it)
_UPPER_ENERGY_LIMIT_RULE = 60       #upper limit of energy used in rule (the node will *try* to stay under it)
_LOWER_ENERGY_LIMIT_DANGER = 30     #absolute lower limit. If the node stay bellow this level for G generations, it dies
_UPPER_ENERGY_LIMIT_DANGER = 70     #absolute upper limit. If the node stay above this level for G generations, it dies
_GENERATIONS_IN_DANGER_LIMIT = 3    #maximum # of generations the node can stay in danger level
_MAX_ENERGY_INPUT = 10              #maximum amount of energy inputed to the system 

random.seed()


class Node:
    #Initialize the node with neighbour connections (to be randomized later)
    def __init__(self):
        self.connections = []
        self.value = 0.0
        self.status = 0                 #statuses: 0- stay; 1-asking for energy; 2-offering energy (see run function)
        self.transactional_energy = 0.0 #ammount of energy to be transfered by the node
        self.candidates = 0.0           #amount of neighbours avaiable to exchange energy
        self.endanger = 0               #number of generations that the node is under or above the safe limits of energy
        self.is_alive = True            #if the node is alive or not

    def add_connection(self, node_id):
        if node_id not in self.connections:
            self.connections.append(node_id)

    def remove_connection(self, node_id):
        if node_id in self.connections:
            self.connections.remove(node_id)

    def connect_to_neighbours(self, i, n_nodes, n_connections):
        for j in range(n_connections + 1):
            target = int((j + i - n_connections/2) % n_nodes) #Regular connection with neighbours 
            if target != i: #avoid self connections
                self.connections.append(target) #Add connection to node



class Network:
    def __init__(self, n_nodes):
    #initialize a network with n_nodes
        self.n_nodes = n_nodes
        self.nodes = []
        self.values_list = [0]* n_nodes #store in a list the nodes values

        for i in range(self.n_nodes):
            new_node = Node() #create the node
            self.nodes.append(new_node)

    def initialize_from_genome(self, genome):
    #initialize connections, from the genome.
        #genome is an array with the positions, in the connections matrix, where there is connections.
        for p in genome:
            line = int((1 + math.sqrt(1 + 8*p)) / 2.0)
            column = int(p - (line * (line-1)) / 2.0)

            self.nodes[line].connections.append(column)
            self.nodes[column].connections.append(line) #connect in both ways

    def initialize_from_matrix(self, connections_matrix):
    #initialize connections, using a connections_matrix.

        #connections_matrix is an array with the values of a triangular matrix below the main diagonal. 
        #(eg: connections_matrix[0] == matrix[1,0]; connections_matrix[1] == matrix[2,0]; connections_matrix[2] == matrix[2,1]; ... 
        position = 0 #current position in connections_matrix array
        for i in range(self.n_nodes):
            for j in range(i):
                if connections_matrix[position] == 1:
                    self.nodes[i].connections.append(j)
                    self.nodes[j].connections.append(i) #connect in both ways
                position += 1

    #create an edge between nodes i and j
    def connect_nodes(self, i, j):
        self.nodes[i].add_connection(j)
        self.nodes[j].add_connection(i)


    def run(self, lower_limit, upper_limit):
    #run the network, allowing energy transfusions
	

        #First Round: each node decides to: 1-ask energy from neighbours 2-offer energy to neighbours 0-stay as it is
        for node in self.nodes: #first evaluate which nodes need energy, or will keep their levels
            #TODO: swap order
            if node.value < lower_limit: #if energy is too low
                node.status = 1 #set status to "asking for energy"
                node.transactional_energy = lower_limit - node.value #the ammount of energy to be received
                node.candidates = sum(1.0 for i in node.connections if self.nodes[i].value > upper_limit) #amount of neighbours offering energy
            elif node.value > upper_limit: #if energy is too high
                node.status = 2 #set status to "offering energy"
                node.transactional_energy = node.value - upper_limit #the ammount of energy to be given away
                node.candidates = sum(1.0 for i in node.connections if self.nodes[i].value < lower_limit) #amount of neighbours asking for energy
            else: #if energy is nor low or high
                node.status = 0 #sets status to stay as it is (ie: do nothing)
                node.transactional_energy = 0.0
                node.candidates = 0.0

        #Second Round: performs the energy transactions
        #a transaction occurs always when a node with status 1 (asking) is connected to one (or more) nodes with status 2 (offering)
        for node in self.nodes:
            if node.status == 1: #found a node in need of energy
                energy_avaiable = 0.0
                for connection in node.connections: #first, check how much energy is avaiable in total
                    neighbour = self.nodes[connection]
                    if neighbour.status == 2:
                        energy_avaiable += neighbour.transactional_energy / neighbour.candidates #to be fair, the node will just receive a fraction of the neighbour's spare energy
                for connection in node.connections:
                    neighbour = self.nodes[connection]
                    if neighbour.status == 2:
                        #if the total energy avaiable is less than what the node needs, the node accepts all the energy being offered
                        if energy_avaiable <= node.transactional_energy:
                            energy_offered = neighbour.transactional_energy / neighbour.candidates
                            energy_transmited = energy_offered
                        #when there is more energy avaiable than needed, the node gets energy from its neighbours proportional to the offered amount
                        else:
                            energy_offered = neighbour.transactional_energy / neighbour.candidates
                            energy_transmited = node.transactional_energy * (energy_offered / energy_avaiable)
                        node.value += energy_transmited #needy node gets energy
                        energy_avaiable -= energy_offered
                        node.transactional_energy -= energy_transmited
                        node.candidates -= 1.0
                        neighbour.value -= energy_transmited #rich node looses energy
                        neighbour.transactional_energy -= energy_transmited
                        neighbour.candidates -= 1.0



    def update_network(self, lower_limit, upper_limit, endanger_limit):
        #check which nodes are under or above the safe energy levels
        i = 0
        for node in self.nodes:
            self.values_list[i] = node.value #update the values_list
            if node.is_alive:
                if node.value < lower_limit or node.value > upper_limit:
                    node.endanger += 1 #for each generation it is out of the safe limits, increase endenger
                else:
                    node.endanger = 0 #when energy levels are restored to safe limits, clear endenger index

                if node.endanger >= endanger_limit and node.is_alive: #kill node if it is in endanger condition for too many generations
                    self.remove_node(node, i)
            i += 1

    def remove_node(self, node, node_index):
        #remove node from network (i.e.: remove connections to and from it)

        #print(">>OMG, node", node_index, "is dead!")
        #first remove the connections to this node
        for connection in node.connections:
            if connection != node_index: #don't remove connection to himself now, otherwise it will break the loop
                self.nodes[connection].connections.remove(node_index)
        #then, remove the connections of the node itself
        node.connections.clear()
        node.is_alive = False

    def count_survivors(self):
        survivors = 0
        deaths = 0
        for node in self.nodes:
            if node.is_alive == True:
                survivors += 1
            else:
                deaths += 1
        return survivors

    def get_values(self):
        return self.values_list.copy()


    def print_network(self, show_connections=False): #Prints the value of each node (0 to _NODE_VALUES_RANGE) of the network on a single line
        values_str = ''
        for i in range(self.n_nodes):
            connections_str = 'node ' + str(i) + ' is connected to: ' + ', '.join(str(x) for x in self.nodes[i].connections)
            if show_connections:
                print(connections_str)
            values_str += str(self.nodes[i].value.__round__()) + ' '
        print(values_str)



class LocalNetwork(Network):
    """Circular Network, where each node is connected to n_connections neighbours
        Parameters: n_nodes, n_connections (number of connections per node)"""
    def __init__(self, n_nodes, n_connections):
        Network.__init__(self, n_nodes)

        #Create "n_nodes" nodes, each with "n_connections" connections to other nodes.
        for i in range(self.n_nodes):
            self.nodes[i].connect_to_neighbours(i, n_nodes, n_connections)



class SmallWorldNetwork(Network):
    """Creates a Small World network
        Parameters: n_nodes, n_connections (number of connections per node), p (probability of rewiring)"""
    def __init__(self, n_nodes, n_connections, p):
        Network.__init__(self, n_nodes) #create the nodes

        #Create "n_nodes" nodes, each with "n_connections" connections to other nodes and a probability "p" of rewiring
        for i in range(self.n_nodes):
            self.nodes[i].connect_to_neighbours(i, n_nodes, n_connections) #connect it to its neighbours (before the randomization)
        for i in range(self.n_nodes):#rewire
            self.reorder_edges(i, p)

    def reorder_edges(self, node_id, p):
        node = self.nodes[node_id]
        for j in range(len(node.connections)): #For each connection, consider rewiring it.
            if random.random() < p: #Chance this connection will be rewired to a random node 
            #FIXME: should it be p/2 (as edges are considered twice?)
                target = random.randint(0, self.n_nodes - 1) #Find newRewire randomly, obeying some constraints (see function valid_connection)
                while (target == node_id) or (target in self.nodes[node_id].connections): #Can't connect to itself or to an already connected node
                    target = random.randint(0, self.n_nodes - 1)
                old_target = node.connections[j]
                self.nodes[old_target].remove_connection(node_id) #remove connection from old target
                node.connections[j] = target #replace old connection to new target
                self.nodes[target].add_connection(node_id)#add new connection on target node (two-way connection)

class RandomNetwork(Network):
    """Network with random connected nodes
        Parameters: n_nodes, n_edges"""
    def __init__(self, n_nodes, n_edges):
        Network.__init__(self, n_nodes)

        #create n_edges random connections
        for i in range(n_edges):
            origin = random.randint(0, self.n_nodes-1)
            destination = random.randint(0, self.n_nodes-1)
            while (destination in self.nodes[origin].connections) or (origin == destination): #check if connection already exist
                origin = random.randint(0, self.n_nodes-1)
                destination = random.randint(0, self.n_nodes-1)
            self.nodes[origin].add_connection(destination)
            self.nodes[destination].add_connection(origin)


class GlobalNetwork(Network):
    """In a Global Network, every node is connected to every node
        Parameters: n_nodes"""
    def __init__(self, n_nodes):
        Network.__init__(self, n_nodes) #create the nodes

        #make the connections
        #for i in range(self.n_nodes):
        #    for j in range(self.n_nodes):
        #        if i != j: #don't make self-connections
        #            self.connect_nodes(i, j)

    def run(self, lower_limit, upper_limit):
    #run the network, allowing energy transfusions

        full_nodes = []
        empty_nodes = []
        #First Round: each node decides to: 1-ask energy from neighbours 2-offer energy to neighbours 0-stay as it is
        for node in self.nodes: #first evaluate which nodes need energy, or will keep their levels
            #TODO: swap order
            if node.value < lower_limit: #if energy is too low
                empty_nodes.append(node)
                node.status = 1 #set status to "asking for energy"
                node.transactional_energy = lower_limit - node.value #the ammount of energy to be received
            elif node.value > upper_limit: #if energy is too high
                full_nodes.append(node)
                node.status = 2 #set status to "offering energy"
                node.transactional_energy = node.value - upper_limit #the ammount of energy to be given away
            else: #if energy is nor low or high
                node.status = 0 #sets status to stay as it is (ie: do nothing)
                node.transactional_energy = 0.0

        empty_candidates = len(empty_nodes)
        full_candidates = len(full_nodes)
        energy_avaiable = 0.0

        for node in full_nodes:
            energy_avaiable += node.transactional_energy
        original_energy_avaiable = energy_avaiable #backup

        #Second Round: performs the energy transactions
        #a transaction occurs always when a node with status 1 (asking) is connected to one (or more) nodes with status 2 (offering)
        for node in empty_nodes:
            energy_per_node = energy_avaiable / empty_candidates
            if energy_per_node <= node.transactional_energy:
                energy_transmited = energy_per_node
            else:
                energy_transmited = node.transactional_energy

            node.value += energy_transmited #needy node gets energy
            node.transactional_energy -= energy_transmited
            empty_candidates -= 1
            energy_avaiable -= energy_transmited

        if original_energy_avaiable != 0:
            energy_used = 1 - (energy_avaiable / original_energy_avaiable)
        else:
            energy_used = 0
        for node in full_nodes:
           node.value -= energy_used * node.transactional_energy #rich node looses energy


class VonNeumannNetwork(Network):
    """In a Global Network, nodes are connected in a circular grid
        Parameters: n_nodes, grid dimensions"""
    def __init__(self, n_nodes, grid_lines, grid_columns):
        Network.__init__(self, n_nodes)

        pos = 0
        for i in range(grid_lines):
            for j in range(grid_columns):
                #connect to left
                if j != 0:
                    left = pos-1
                elif j == 0: #connect to the other edge
                    left = pos + grid_columns - 1
                self.nodes[pos].add_connection(left)

                #connect to right
                if j != grid_columns-1:
                    right = pos+1
                elif j == grid_columns-1:
                    right = pos - grid_columns + 1
                self.nodes[pos].add_connection(right)

                #connect up
                up = (pos - grid_columns) % (grid_lines*grid_columns)
                self.nodes[pos].add_connection(up)

                #connect down
                down = (pos+grid_columns) % (grid_lines*grid_columns)
                self.nodes[pos].add_connection(down)

                pos += 1


class ScaleFreeNetwork(Network):
    def __init__(self, n_nodes, m_zero, m): #m < m_zero 
        #create m_zero nodes, full connected
        Network.__init__(self, n_nodes)
        roulette = [] #from where connections will be sorted

        for i in range(m_zero):
            for j in range(m_zero):
                if i != j: #don't make self-connections
                    self.connect_nodes(i, j)
                    roulette.append(i)

        for i in range(n_nodes-m_zero):
            new_node_id = m_zero + i
            
            #draw the nodes the new node will be connected, from the roulette
            roulette_selection = []
            for j in range(m):
                result = random.sample(roulette, 1)[0]
                while(result in roulette_selection): #don't get repeated connections
                    result = random.sample(roulette, 1)[0]
                roulette_selection.append(result)

            #print(roulette_selection, roulette)
            #add the connections and add the new connections to the roulette (need to be after, to dont compromize the drawn)
            for j in range(m):
                self.connect_nodes(new_node_id, roulette_selection[j])
                roulette.append(roulette_selection[j])
                roulette.append(new_node_id)





class NoiseControl:
    """Implementations of different input paterns to nodes in a network"""
    def random_noise_generator(network_size, noise_range):
        random_noise = []
        for node in range(network_size):
            random_noise.append(random.randrange(noise_range))
        return random_noise

    def apply_regular_noise(network, noise):
        for node in network.nodes:
            node.value = noise

    def apply_random_noise(network, predefined_noise=[], noise_range=_NODE_VALUES_RANGE, negative_range=True):
        if predefined_noise: #if it is just applying a noise created befoere in random_noise_generator
            for i in range(len(network.nodes)):
                network.nodes[i].value += predefined_noise[i]
        else: #create a new noise patern now
            if negative_range:
                for node in network.nodes:
                        node.value += random.randrange(noise_range*(-1), noise_range) #generate either a positive or a negative value
            elif not negative_range:
                for node in network.nodes:
                    if node.is_alive:
                        node.value += random.randrange(0, noise_range) #generate only positive values


    def apply_circular_noise(network, noise_range=_NODE_VALUES_RANGE):
        net_size = len(network.nodes)
        for i in range(net_size):
            networl.nodes[i].value += math.cos(i/float(net_size) * 2*math.pi) * noise_range #apply circular noise to the network





def main():
    #generate network
    network = SmallWorldNetwork(_N_NODES, _N_CONNECTIONS, _P)
    #[initialize network with values]
    NoiseControl.apply_random_noise(network, _NODE_VALUES_RANGE)
    network.print_network(True)
    #loop numero de geracoes
    for i in range(_ITERATIONS):
        #[input energy]
        #NoiseControl.apply_random_noise(network, noise_range=_MAX_ENERGY_INPUT)
        #run network
        network.run(_LOWER_ENERGY_LIMIT_RULE, _UPPER_ENERGY_LIMIT_RULE)
        #update network
        network.update_network(_LOWER_ENERGY_LIMIT_DANGER, _UPPER_ENERGY_LIMIT_DANGER, _GENERATIONS_IN_DANGER_LIMIT)
        network.print_network()
    network.print_network(True)
    #analyse result network


if __name__ == "__main__":
    main()

