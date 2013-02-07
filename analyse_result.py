#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from network import *
from graph_tool.all import *

def main(argv):

    if len(argv) != 3:
        print("usage: analyse_result [n_nodes] [list]")
        return

    n_nodes = int(argv[1]) #number of nodes in the network
    matrix_size = int(((n_nodes - 1)*n_nodes)/2) #this is the size of the triangular region lower to the main diagonal of the matrix.

    genome = eval(argv[2])

    #generate connections_matrix, from the genome
    connections_matrix = [0] * matrix_size #initialize with zeroes 
    for connection in genome:
        connections_matrix[connection] = 1 #replace to 1, the edges indicated in the genome

    #generate network from genome 
    network = Network(n_nodes)
    network.initialize_from_matrix(connections_matrix)
    network.print_network(True)

    #using graphtool library!
    g = Graph(directed=False)
    #add vertex
    vlist = g.add_vertex(n_nodes)

    #add edges
    #genome is an array with the values of a triangular matrix below the main diagonal. (eg: genome[0] == matrix[1,0]; genome[1] == matrix[2,0]; genome[2] == matrix[2,1]; ... 
    position = 0 #current position in genome array
    elist = []
    for i in range(n_nodes):
        for j in range(i):
            if connections_matrix[position] == 1:
                g.add_edge(g.vertex(i), g.vertex(j))
				#elist.append(g.add_edge(vlist[i], vlist[j]))
            position += 1
    #pos = fruchterman_reingold_layout(g, circular=True)
    pos = arf_layout(g)
    #graph_draw(g, pos=pos, output="100.pdf")
    graph_draw(g, output="logs/100.pdf")
    g.save("logs/100.dot")
    #draw.interactive_window(g)

    #os.system("dot -Tsvg logs/100.dot -o logs/100.svg")


if __name__ == "__main__":
    main(sys.argv)

