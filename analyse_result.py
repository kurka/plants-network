#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import pickle
from network import *
import networkx as nx
#from graph_tool.all import *

def population_analysis(n_nodes, genome_population):

    print(">>>>>>analysis of the whole population")

    fit = [genome_population[j][1] for j in range(50)]
    edges_max = n_nodes * (n_nodes-1) / 2.0
    gen = [genome_population[j][0] for j in range(50)]

    #1
    print("1 - fitness")
    print(fit)

    #2
    print("2 - Frequency of connections")
    #concatenate all genome_lists
    from functools import reduce
    gens = reduce(lambda a, b: a + b, gen)

    import collections
    counter=collections.Counter(gens)

    print("top 100 frequency of connections in the genome population:")
    #print(counter.values())
    print(counter.most_common(100))

    #3
    print("3 - genes similarity")
    soma = 0
    for i in range(len(gen)):
        for j in range(i):
                soma += len(set(gen[i]) & set(gen[j]))
    avg = soma / (len(gen)*(len(gen)-1)/2.0)
    print("average similarity: ", avg)

    print()


def create_network_net(n_nodes, connections_matrix):
    #create the network as a Network class and print its topology

    #generate network from genome 
    network = Network(n_nodes)
    network.initialize_from_matrix(connections_matrix)
    return network


def create_graphtool_net(n_nodes, connections_matrix):
    #using graphtool library!
    g = Graph(directed=False)
    #add vertex
    vlist = g.add_vertex(n_nodes)

    #add edges
    position = 0 #current position in genome array
    for i in range(n_nodes):
        for j in range(i):
            if connections_matrix[position] == 1:
                g.add_edge(g.vertex(i), g.vertex(j))
            position += 1

    return g

def create_networkx_net(n_nodes, connections_matrix):
    g = nx.Graph()

    position = 0
    for i in range(n_nodes):
        for j in range(i):
            if connections_matrix[position] == 1:
                g.add_edge(i, j)
    return g

def draw_graphtool(graph):
    #pos = fruchterman_reingold_layout(g, circular=True)
    pos = arf_layout(graph)
    #graph_draw(g, pos=pos, output="100.pdf")
    graph_draw(graph, output="analysis/graphtool.pdf")
    #draw.interactive_window(g)

def draw_dot(graph):
    graph.save("analysis/graphviz.dot")
    os.system("circo -Tsvg analysis/graphviz.dot -o analysis/graphviz.svg")

def draw_dot_netx(netx):
    nx.write_dot(netx,"analysis/grid.dot")
    os.system("circo -Tsvg analysis/grid.dot -o analysis/netx.svg")

def graphtool_analysis(graph):

    print("bla")
    #vertex_hist - Return the vertex histogram of the given degree type or property.

    #edge_hist - Return the edge histogram of the given property.
    #vertex_average - Return the average of the given degree or vertex property.
    #edge_average - Return the average of the given degree or vertex property.
    #label_parallel_edges - Label edges which are parallel, i.e, have the same source and target vertices.
    #remove_parallel_edges - Remove all parallel edges from the graph.
    #label_self_loops - Label edges which are self-loops, i.e, the source and target vertices are the same.
    #remove_self_loops - Remove all self-loops edges from the graph.
    #remove_labeled_edges - Remove every edge e such that label[e] != 0.
    #distance_histogram - Return the shortest-distance histogram for each vertex pair in the graph.


def main(argv):

    if len(argv) != 3:
        print("usage: analyse_result [n_nodes] [pickle_file]")
        return

    n_nodes = int(argv[1]) #number of nodes in the network
    bkp_file = open(argv[2], "rb")
    genome_population = pickle.load(bkp_file)
    pop_size = len(genome_population)
    genome = genome_population[-1][0] #get the last genome, to test. if the list is initialized, it will contain the best individual
    matrix_size = int(((n_nodes - 1)*n_nodes)/2) #this is the size of the triangular region lower to the main diagonal of the matrix.

    #generate connections_matrix, from the genome
    connections_matrix = [0] * matrix_size #initialize with zeroes 
    for connection in genome:
        connections_matrix[connection] = 1 #replace to 1, the edges indicated in the genome

    #analyse population
    population_analysis(n_nodes, genome_population)
    #connections_frequency(genome_population)

    #create Network object
    #net = create_network_net(n_nodes, connections_matrix)
    #net.print_network(True)

    netx = create_networkx_net(n_nodes, connections_matrix)
    draw_dot_netx(netx)
    #Create graphtool object
    #g = create_graphtool_net(n_nodes, connections_matrix)

    #draw_graphtool(graph):
    #draw_dot(graph):

    #graph_tool analysis
    #graphtool_analysis(g)

    #TODO:
    #grau medio
    #distribuição de graus (histograma)
    #distancia média
    #grau de clusterizacao
    #distribuição conjunta de graus (no graus de grau "n1", conecta com graus "n2") (assortividade)

if __name__ == "__main__":
    main(sys.argv)

