#!/usr/bin/env python3
# Copyright (c) 2014 The Bitcoin Core developers
# Copyright (c) 2018 The Zencash developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
from test_framework.test_framework import BitcoinTestFramework
from test_framework.authproxy import JSONRPCException
from test_framework.util import assert_equal, initialize_chain_clean, \
    start_nodes, start_node, connect_nodes, stop_node, stop_nodes, \
    sync_blocks, sync_mempools, connect_nodes_bi, wait_bitcoinds, p2p_port, check_json_precision, \
    disconnect_nodes
import traceback
import os,sys
import shutil
from random import randint
from decimal import Decimal
import logging

import time
class headers(BitcoinTestFramework):

    alert_filename = None

    def setup_chain(self, split=False):
        print("Initializing test directory "+self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 3)
        self.alert_filename = os.path.join(self.options.tmpdir, "alert.txt")
        with open(self.alert_filename, 'w'):
            pass  # Just open then close to create zero-length file

    def setup_network(self, split=False):
        self.nodes = []

        self.nodes = start_nodes(3, self.options.tmpdir)

        if not split:
            # 1 and 2 are joint only if split==false
            connect_nodes_bi(self.nodes, 1, 2)
            sync_blocks(self.nodes[1:3])
            sync_mempools(self.nodes[1:3])

        connect_nodes_bi(self.nodes, 0, 1)
        self.is_network_split = split
        self.sync_all()

    def split_network(self):
        # Split the network of three nodes into nodes 0-1 and 2.
        assert not self.is_network_split
        disconnect_nodes(self.nodes[1], 2)
        disconnect_nodes(self.nodes[2], 1)
        self.is_network_split = True

    def join_network(self):
        #Join the (previously split) network pieces together: 0-1-2
        assert self.is_network_split
        connect_nodes_bi(self.nodes, 1, 2)
        connect_nodes_bi(self.nodes, 2, 1)
        self.sync_all()
        self.is_network_split = False

    def dump_ordered_tips(self, tip_list):
        sorted_x = sorted(tip_list, key=lambda k: k['status'])
        c = 0
        for y in sorted_x:
            if (c == 0):
                print(y)
            else:
                print(" ",y)
            c = 1

    def mark_logs(self, msg):
        self.nodes[0].dbg_log(msg)
        self.nodes[1].dbg_log(msg)
        self.nodes[2].dbg_log(msg)

    def run_test(self):
        blocks = []
        self.bl_count = 0

        blocks.append(self.nodes[0].getblockhash(0))
        print("\n\nGenesis block is:\n" + blocks[0])

        s = "Node 1 generates a block"
        print("\n\n" + s + "\n")
        self.mark_logs(s)

        blocks.extend(self.nodes[1].generate(1)) # block height 1
        print(blocks[1])
        self.sync_all()

# Node(0): [0]->[1]
#   |
# Node(1): [0]->[1]
#   |
# Node(2): [0]->[1]

        print("\n\nSplit network")
        self.split_network()
        print("The network is split")
        self.mark_logs("The network is split")

        print("\nNode1 generating 7 honest block")
        blocks.extend(self.nodes[1].generate(7)) # block height 2--8
        blA = blocks[2]
        blB = blocks[4]
        blC = blocks[6]
        for i in range(2, 9):
            print(blocks[i])
        self.sync_all()

        print("\nNode2 generating 20 mal block")
        blocks.extend(self.nodes[2].generate(20)) # block height 2--21
        for i in range(9, 29):
            print(blocks[i])
        self.sync_all()

# Node(0): [0]->[1]->[2h]->..->[8h]
#   |                   
# Node(1): [0]->[1]->[2h]->..->[8h]
#                       
# Node(2): [0]->[1]->[2m]->..->..->[21m]

#        raw_input("press enter to go on..")

        print("\n\nJoin network")
        # raw_input("press enter to join the netorks..")
        self.mark_logs("Joining network")
        self.join_network()

        time.sleep(2)
        print("\nNetwork joined") 
        self.mark_logs("Network joined")

        for i in range(0, 3):
            self.dump_ordered_tips(self.nodes[i].getchaintips())
            print("---")

# Node(0): [0]->[1]->[2h]->..->[8h]       **Active**    
#   |             \     
#   |              +->[2m]->..->..->[21m]    
#   |                   
# Node(1): [0]->[1]->[2h->..->[8h]        **Active**    
#   |             \     
#   |              +->[2m]->..->..->[21m]    
#   |                   
#   |                   
# Node(2): [0]->[1]->[2m]->..->..->[21m]  **Active**    
#                 \     
#                  +->[2h]->..->[8h]

#        raw_input("press enter to go on..")

        print("Checking finality of block[", blA, "]")
        print("  Node0 has: %d" % self.nodes[0].getblockfinalityindex(blA))
        print("  Node1 has: %d" % self.nodes[1].getblockfinalityindex(blA))
        print("Checking finality of block[", blB, "]")
        print("  Node0 has: %d" % self.nodes[0].getblockfinalityindex(blB))
        print("  Node1 has: %d" % self.nodes[1].getblockfinalityindex(blB))
        print("Checking finality of block[", blC, "]")
        print("  Node0 has: %d" % self.nodes[0].getblockfinalityindex(blC))
        print("  Node1 has: %d" % self.nodes[1].getblockfinalityindex(blC))

#        raw_input("press enter to go on..")

        for j in range(1, 10):
            print("### block %d ---" % j)
            print("Node2 generating 1 mal block")
            blocks.extend(self.nodes[2].generate(1)) # block height 8--12
            n=len(blocks)-1
            print(blocks[n])
            time.sleep(3)

            try:
                print("Checking finality of block[", blA, "]")
                print("  Node0 has: %d" % self.nodes[0].getblockfinalityindex(blA))
                print("  Node1 has: %d" % self.nodes[1].getblockfinalityindex(blA))
                print("Checking finality of block[", blB, "]")
                print("  Node0 has: %d" % self.nodes[0].getblockfinalityindex(blB))
                print("  Node1 has: %d" % self.nodes[1].getblockfinalityindex(blB))
                print("Checking finality of block[", blC, "]")
                print("  Node0 has: %d" % self.nodes[0].getblockfinalityindex(blC))
                print("  Node1 has: %d" % self.nodes[1].getblockfinalityindex(blC))
            except JSONRPCException as e:
                errorString = e.error['message']
                print(errorString)
                print("\n ===> Malicious attach succeeded after %d blocks!!\n\n" % j)
                break
#            for i in range(0, 3):
#                print self.nodes[i].getchaintips()[0]
#            raw_input("press enter to go on..")


#        self.sync_all()
        time.sleep(2)

        for i in range(0, 3):
            self.dump_ordered_tips(self.nodes[i].getchaintips())
            print("---")

        time.sleep(1)

#        raw_input("press enter to go on..")


if __name__ == '__main__':
    headers().main()
