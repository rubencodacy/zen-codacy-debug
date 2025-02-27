#!/usr/bin/env python3
# Copyright (c) 2014-2015 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test addressindex generation and fetching
#

import time
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.script import *
from test_framework.mininode import *
import binascii

class SpentIndexTest(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory "+self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 4)

    def setup_network(self):
        self.nodes = []
        # Nodes 0/1 are "wallet" nodes
        self.nodes.append(start_node(0, self.options.tmpdir, ["-debug"]))
        self.nodes.append(start_node(1, self.options.tmpdir, ["-debug", "-spentindex"]))
        # Nodes 2/3 are used for testing
        self.nodes.append(start_node(2, self.options.tmpdir, ["-debug", "-spentindex"]))
        self.nodes.append(start_node(3, self.options.tmpdir, ["-debug", "-spentindex", "-txindex"]))
        connect_nodes(self.nodes[0], 1)
        connect_nodes(self.nodes[0], 2)
        connect_nodes(self.nodes[0], 3)

        self.is_network_split = False
        self.sync_all()

    def run_test(self):
        print("Mining blocks...")
        self.nodes[0].generate(105)
        self.sync_all()

        chain_height = self.nodes[1].getblockcount()
        assert_equal(chain_height, 105)

        # Check that
        print("Testing spent index...")

        privkey = "cSdkPxkAjA4HDr5VHgsebAPDEh9Gyub4HK8UJr2DFGGqKKy4K5sG"
        address = "ztUB6YWTcj2uUe5Rbucnc7oFevn7wCKyN63"
        op_dup = "76"
        op_hash160 = "a9"
        op_push_20_bytes_onto_the_stack = "14"
        addressHash = "0b2f0a0c31bfe0406b0ccc1381fdbe311946dadc"
        op_equalverify = "88"
        op_checksig = "ac"
        genesisCbah = "20bb1acf2c1fc1228967a611c7db30632098f0c641855180b5fe23793b72eea50d00b4"
        scriptPubKey = binascii.unhexlify(op_dup + op_hash160 + op_push_20_bytes_onto_the_stack + addressHash + op_equalverify + op_checksig + genesisCbah)
        unspent = self.nodes[0].listunspent()
        tx = CTransaction()
        amount = to_satoshis(unspent[0]["amount"])
        tx.vin = [CTxIn(COutPoint(int(unspent[0]["txid"], 16), unspent[0]["vout"]))]
        tx.vout = [CTxOut(amount, scriptPubKey)]
        tx.rehash()

        signed_tx = self.nodes[0].signrawtransaction(binascii.hexlify(tx.serialize()).decode("utf-8"))
        txid = self.nodes[0].sendrawtransaction(signed_tx["hex"], True)
        self.nodes[0].generate(1)
        self.sync_all()

        print("Testing getspentinfo method...")

        # Check that the spentinfo works standalone
        info = self.nodes[1].getspentinfo({"txid": unspent[0]["txid"], "index": unspent[0]["vout"]})
        assert_equal(info["txid"], txid)
        assert_equal(info["index"], 0)
        assert_equal(info["height"], 106)

        print("Testing getrawtransaction method...")

        # Check that verbose raw transaction includes spent info
        txVerbose = self.nodes[3].getrawtransaction(unspent[0]["txid"], 1)
        assert_equal(txVerbose["vout"][unspent[0]["vout"]]["spentTxId"], txid)
        assert_equal(txVerbose["vout"][unspent[0]["vout"]]["spentIndex"], 0)
        assert_equal(txVerbose["vout"][unspent[0]["vout"]]["spentHeight"], 106)

        # Check that verbose raw transaction includes input values
        txVerbose2 = self.nodes[3].getrawtransaction(txid, 1)
        assert_equal(txVerbose2["vin"][0]["value"], Decimal(unspent[0]["amount"]))
        assert_equal(txVerbose2["vin"][0]["valueZat"], amount)

        # Check that verbose raw transaction includes address values and input values
        privkey2 = "cSdkPxkAjA4HDr5VHgsebAPDEh9Gyub4HK8UJr2DFGGqKKy4K5sG"
        address2 = "ztUB6YWTcj2uUe5Rbucnc7oFevn7wCKyN63"
        addressHash2 = "0b2f0a0c31bfe0406b0ccc1381fdbe311946dadc"
        scriptPubKey2 = binascii.unhexlify(op_dup + op_hash160 + op_push_20_bytes_onto_the_stack + addressHash2 + op_equalverify + op_checksig + genesisCbah)
        tx2 = CTransaction()
        tx2.vin = [CTxIn(COutPoint(int(txid, 16), 0))]
        tx2.vout = [CTxOut(amount, scriptPubKey2)]
        tx.rehash()
        self.nodes[0].importprivkey(privkey)
        signed_tx2 = self.nodes[0].signrawtransaction(binascii.hexlify(tx2.serialize()).decode("utf-8"))
        txid2 = self.nodes[0].sendrawtransaction(signed_tx2["hex"], True)

        # Check the mempool index
        self.sync_all()
        txVerbose3 = self.nodes[1].getrawtransaction(txid2, 1)
        assert_equal(txVerbose3["vin"][0]["address"], address2)
        assert_equal(txVerbose3["vin"][0]["value"], Decimal(unspent[0]["amount"]))
        assert_equal(txVerbose3["vin"][0]["valueZat"], amount)

        # Check the database index
        block_hash = self.nodes[0].generate(1)
        self.sync_all()

        txVerbose4 = self.nodes[3].getrawtransaction(txid2, 1)
        assert_equal(txVerbose4["vin"][0]["address"], address2)
        assert_equal(txVerbose4["vin"][0]["value"], Decimal(unspent[0]["amount"]))
        assert_equal(txVerbose4["vin"][0]["valueZat"], amount)


        # Check block deltas
        print("Testing getblockdeltas...")

        block = self.nodes[3].getblockdeltas(block_hash[0])
        assert_equal(len(block["deltas"]), 2)
        assert_equal(block["deltas"][0]["index"], 0)
        assert_equal(len(block["deltas"][0]["inputs"]), 0)
        assert_equal(len(block["deltas"][0]["outputs"]), 4) # Miner, CF, SN, XN
        assert_equal(block["deltas"][1]["index"], 1)
        assert_equal(block["deltas"][1]["txid"], txid2)
        assert_equal(block["deltas"][1]["inputs"][0]["index"], 0)
        assert_equal(block["deltas"][1]["inputs"][0]["address"], "ztUB6YWTcj2uUe5Rbucnc7oFevn7wCKyN63")
        assert_equal(block["deltas"][1]["inputs"][0]["satoshis"], amount * -1)
        assert_equal(block["deltas"][1]["inputs"][0]["prevtxid"], txid)
        assert_equal(block["deltas"][1]["inputs"][0]["prevout"], 0)
        assert_equal(block["deltas"][1]["outputs"][0]["index"], 0)
        assert_equal(block["deltas"][1]["outputs"][0]["address"], "ztUB6YWTcj2uUe5Rbucnc7oFevn7wCKyN63")
        assert_equal(block["deltas"][1]["outputs"][0]["satoshis"], amount)

        print("Passed\n")


if __name__ == '__main__':
    SpentIndexTest().main()
