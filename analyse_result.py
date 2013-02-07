#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from network import *
from graph_tool.all import *

def main(argv):

    if len(argv) != 3:
        print("usage: analyse_result [n_nodes] [hex_string]")
        return

    n_nodes = int(argv[1]) #number of nodes in the network

    #read the result as a hexadecimal string
    #hex_s = "0x20010000080400001000000000000a0000000020000048000000000002021003000200010400208000400800001044000000400002010000200000000000500000000000022000000800012000000800000082220004000040000020018000000000080000400000000000000000901010008000000100000000800001000000002000a002000000004000000020024000080000800000000400200202200000000840040000000008000000001006000800000000000800008480000000000001000004020008000c004000040020020004000000000c00800110001018000000000002000480000010000010000000000000000000000001100080000200001000200100000000000080800401020000000000000001000001000000000000000040000080200000100000000200012080000000800400000028800000020000000410000000000000100000000000400020002002002000008000080001000001100003000000000800400000000000002000116000000400080002000000080000000010000180008408000000010000080002000602000200000000802000000210001080000000010c0200000000000084000000102020000000000800000000400202000000000000000090000004000000208140000080000000000800000010000008000400000000000000011000200000880000010828002080000000012004001040200000000b0000000040a00800000004000000000200800400400480000003000000000000000000020400000000000000000008004004000000040200000000000c00200000000101000005000000000000020800000000002000000000400280004"
    hex_s = argv[2]
    bin_s = bin(eval(hex_s)) #convert it to a binary string
    bin_s = bin_s[2:] #remove the "0b" prefix
    genome_size = int(((n_nodes-1)*n_nodes)/2)
    bin_s = bin_s.zfill(genome_size) #fill the binary with zeroes
    genome = [int(i) for i in bin_s] #transform it in a list of zeros and ones

    #generate network from genome 
    network = Network(n_nodes)
    network.initialize_from_matrix(genome)
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
            if genome[position] == 1:
                g.add_edge(g.vertex(i), g.vertex(j))
				#elist.append(g.add_edge(vlist[i], vlist[j]))
            position += 1
    #pos = fruchterman_reingold_layout(g, circular=True)
    pos = arf_layout(g)
    #graph_draw(g, pos=pos, output="100.pdf")
    graph_draw(g, output="100.pdf")
    g.save("100.dot")
    #draw.interactive_window(g)



if __name__ == "__main__":
    main(sys.argv)

