#!/usr/bin/env python3
# Copyright (c) 2014 The Bitcoin Core developers
# Copyright (c) 2018 The Zencash developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
from test_framework.test_framework import BitcoinTestFramework
from test_framework.test_framework import MINIMAL_SC_HEIGHT, MINER_REWARD_POST_H200
from test_framework.authproxy import JSONRPCException
from test_framework.util import assert_equal, assert_true, initialize_chain_clean, \
    stop_nodes, wait_bitcoinds, \
    start_nodes, sync_blocks, sync_mempools, connect_nodes_bi, mark_logs, \
    dump_sc_info_record
from test_framework.mc_test.mc_test import *
import os
from decimal import Decimal
import pprint

NUMB_OF_NODES = 3
DEBUG_MODE = 1
SC_COINS_MAT = 2
SC_VK_SIZE = 1024


class SCCreateTest(BitcoinTestFramework):
    alert_filename = None

    def setup_chain(self, split=False):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, NUMB_OF_NODES)
        self.alert_filename = os.path.join(self.options.tmpdir, "alert.txt")
        with open(self.alert_filename, 'w'):
            pass  # Just open then close to create zero-length file

    def setup_network(self, split=False):
        self.nodes = []

        self.nodes = start_nodes(NUMB_OF_NODES, self.options.tmpdir,
                                 extra_args=[["-sccoinsmaturity=%d" % SC_COINS_MAT, '-logtimemicros=1', '-debug=sc',
                                              '-debug=py', '-debug=mempool', '-debug=net',
                                              '-debug=bench']] * NUMB_OF_NODES)

        if not split:
            # 1 and 2 are joint only if split==false
            connect_nodes_bi(self.nodes, 1, 2)
            sync_blocks(self.nodes[1:NUMB_OF_NODES])
            sync_mempools(self.nodes[1:NUMB_OF_NODES])

        connect_nodes_bi(self.nodes, 0, 1)
        self.is_network_split = split
        self.sync_all()

    def run_test(self):
        '''
        This test try creating a SC with sc_create using invalid parameters and valid parameters.
        It also checks the coin mature time of the FT. For SC creation an amount of 1 ZAT is used.
        '''
        # network topology: (0)--(1)--(2)

        mark_logs("Node 1 generates {} block".format(MINIMAL_SC_HEIGHT), self.nodes, DEBUG_MODE)
        self.nodes[1].generate(MINIMAL_SC_HEIGHT)
        self.sync_all()

        creation_amount = Decimal("0.000015")
        fwt_amount_1 = Decimal("2.0")
        fwt_amount_2 = Decimal("2.0")
        fwt_amount_3 = Decimal("3.0")
        fwt_amount_many = fwt_amount_1 + fwt_amount_2 + fwt_amount_3

        #generate wCertVk and constant
        mcTest = CertTestUtils(self.options.tmpdir, self.options.srcdir)
        vk = mcTest.generate_params("sc1")
        constant = generate_random_field_element_hex()

        # Set of invalid data to test sc_create parsing
        parserTests = [
            {
                "title"    : "Node 2 tries to create a SC with empty params",
                "node"     : 2,
                "expected" : "Expected params as object",
                "input"    : {}
            },
            {
                "title"    : "Node 2 tries to create a SC with unexpected member",
                "node"     : 2,
                "expected" : "Invalid parameter \"unknown\": unexpected",
                "input"    : {
                    "unknown" : None
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with missing mandatory version",
                "node"     : 2,
                "expected" : "Invalid parameter \"version\": missing",
                "input"    : {
                    "withdrawalEpochLength" : 123
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory version set to null",
                "node"     : 2,
                "expected" : "Invalid parameter \"version\": can not be null",
                "input"    : {
                    "version" : None,
                    "withdrawalEpochLength" : 123
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory toaddress missing",
                "node"     : 2,
                "expected" : "Invalid parameter \"toaddress\": missing",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory toaddress set to null",
                "node"     : 2,
                "expected" : "Invalid parameter \"toaddress\": can not be null",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : None
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory amount missing",
                "node"     : 2,
                "expected" : "Invalid parameter \"amount\": missing",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba"
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory amount set to null",
                "node"     : 2,
                "expected" : "Invalid parameter \"amount\": can not be null",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : None
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory wCertVk missing",
                "node"     : 2,
                "expected" : "Invalid parameter \"wCertVk\": missing",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : "1.0"
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory wCertVk set to null",
                "node"     : 2,
                "expected" : "Invalid parameter \"wCertVk\": can not be null",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : "1.0",
                    "wCertVk" : None
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory non parseable version",
                "node"     : 2,
                "expected" : "Invalid parameter \"version\": JSON value",
                "input"    : {
                    "version" : [],
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : "1.0",
                    "wCertVk" : vk
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory non parseable withdrawalEpochLength",
                "node"     : 2,
                "expected" : "Invalid parameter \"withdrawalEpochLength\": JSON value",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : "qwerty",
                    "toaddress" : "abba",
                    "amount" : "1.0",
                    "wCertVk" : vk
                }
            },
            {
                "title"    : "Node 2 tries to create a SC with mandatory invalid withdrawalEpochLength",
                "node"     : 2,
                "expected" : "Invalid parameter \"withdrawalEpochLength\":",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : -1,
                    "toaddress" : "abba",
                    "amount" : "1.0",
                    "wCertVk" : vk
                }
            },

            {
                "title"    : "Node 2 tries to create a SC with insufficient funds",
                "node"     : 2,
                "expected" : "Insufficient transparent funds",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : "1.0",
                    "wCertVk" : vk,
                    "constant" : constant
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with empty toaddress",
                "node"     : 1,
                "expected" : "Invalid parameter \"toaddress\": not a valid hex",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "",
                    "amount" : "1.0",
                    "wCertVk" : vk,
                    "constant" : constant
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with empty amount",
                "node"     : 1,
                "expected" : "Invalid parameter \"amount\":",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : "",
                    "wCertVk" : vk,
                    "constant" : constant
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with zero amount",
                "node"     : 1,
                "expected" : "Invalid parameter \"amount\": can not be zero",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : "0",
                    "wCertVk" : vk,
                    "constant" : constant
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with negative amount",
                "node"     : 1,
                "expected" : "Invalid parameter \"amount\": Amount out of range",
                "input"    : {
                    "version" : 0,
                    "withdrawalEpochLength" : 123,
                    "toaddress" : "abba",
                    "amount" : "-1",
                    "wCertVk" : vk,
                    "constant" : constant
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with non hex wCertVk",
                "node"     : 1,
                "expected" : "Invalid parameter \"wCertVk\":",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': "0abcdefghijklmno",
                    'constant': constant
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with non hex wCertVk (odd chars)",
                "node"     : 1,
                "expected" : "Invalid parameter \"wCertVk\":",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': "abc"
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with too short wCertVk",
                "node"     : 1,
                "expected" : "Invalid parameter \"wCertVk\":",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': "aa" * (SC_VK_SIZE - 1)
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with too long wCertVk",
                "node"     : 1,
                "expected" : "Invalid parameter \"wCertVk\":",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': "aa" * (SC_VK_SIZE + 1)
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with invalid wCertVk",
                "node"     : 1,
                "expected" : "Invalid parameter \"wCertVk\":",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': "aa" * SC_VK_SIZE # Why should this be invalid ?
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with non hex customData",
                "node"     : 1,
                "expected" : "Invalid parameter \"customData\": Invalid format: not an hex",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk' : vk,
                    'customData': "abcdefghijklmnop"
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with non hex customData (odd chars)",
                "node"     : 1,
                "expected" : "Invalid parameter \"customData\": Invalid format: not an hex",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk' : vk,
                    'customData': "012"
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with too long customData",
                "node"     : 1,
                "expected" : "Invalid parameter \"customData\": Invalid length",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': vk,
                    'customData': "bb" * 1025
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with non hex constant (odd chars)",
                "node"     : 1,
                "expected" : "Invalid parameter \"constant\": Invalid format: not an hex",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': vk,
                    'constant': "abc"
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with too short constant (below field size)",
                "node"     : 1,
                "expected" : "Invalid parameter \"constant\": Invalid length",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': vk,
                    'constant': "bb" * (SC_FIELD_SIZE - 1)
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with non hex char in constant",
                "node"     : 1,
                "expected" : "Invalid parameter \"constant\": Invalid format",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': vk,
                    'constant': "bz" * SC_FIELD_SIZE
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with too long constant (above field size)",
                "node"     : 1,
                "expected" : "Invalid parameter \"constant\": Invalid length",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': vk,
                    'constant': "bb" * (SC_FIELD_SIZE + 1)
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with invalid constant",
                "node"     : 1,
                "expected" : "Invalid parameter \"constant\":",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 123,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': vk,
                    'constant': "aa" * SC_FIELD_SIZE
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with epoch length == 0",
                "node"     : 1,
                "expected" : "Invalid parameter \"withdrawalEpochLength\": not in range",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 0,
                    'toaddress': "0ada",
                    'amount': 0.1,
                    'wCertVk': vk,
                    'constant': "aa" * SC_FIELD_SIZE
                }
            },
            {
                "title"    : "Node 1 tries to create a SC with epoch length > 4032",
                "node"     : 1,
                "expected" : "Invalid parameter \"withdrawalEpochLength\": not in range",
                "input"    : {
                    'version': 0,
                    'withdrawalEpochLength': 4033,
                    'toaddress': "0ada",
                    'amount': Decimal("1.0"),
                    'wCertVk': vk,
                    'customData': "aa" * SC_FIELD_SIZE
                }
            },
        ]

        for test in parserTests:
            mark_logs(test['title'], self.nodes, DEBUG_MODE)
            try:
                self.nodes[test['node']].sc_create(test['input'])
                assert_true(False) # We should not get here
            except JSONRPCException as ex:
                errorString = ex.error['message']
                mark_logs(" ... " + errorString, self.nodes, DEBUG_MODE)
                assert_true(test['expected'] in errorString)

        # ---------------------------------------------------------------------------------------
        
        # Node 1 create the SC
        mark_logs("\nNode 1 creates SC", self.nodes, DEBUG_MODE)
        cmdInput = {
            'version': 0,
            'withdrawalEpochLength': 123,
            'toaddress': "dada",
            'amount': creation_amount,
            'wCertVk': vk,
            'customData': "bb" * 1024,
            'constant': constant
        }

        ret = self.nodes[1].sc_create(cmdInput)
        creating_tx = ret['txid']
        scid = ret['scid']
        self.sync_all()

        decoded_tx = self.nodes[1].getrawtransaction(creating_tx, 1)
        assert_equal(scid, decoded_tx['vsc_ccout'][0]['scid'])

        mark_logs("\n...Node0 generating 1 block", self.nodes, DEBUG_MODE)
        self.nodes[0].generate(1)
        self.sync_all()

        mark_logs("Verify all nodes see the new SC...", self.nodes, DEBUG_MODE)
        scinfo0 = self.nodes[0].getscinfo(scid)['items'][0]
        scinfo1 = self.nodes[1].getscinfo(scid)['items'][0]
        scinfo2 = self.nodes[2].getscinfo(scid)['items'][0]
        assert_equal(scinfo0, scinfo1)
        assert_equal(scinfo0, scinfo2)

        mark_logs("Verify fields are set as expected...", self.nodes, DEBUG_MODE)
        assert_equal(scinfo0['wCertVk'], vk)
        assert_equal(scinfo0['customData'], "bb" * 1024)
        assert_equal(scinfo0['constant'], constant)
        pprint.pprint(scinfo0)

        # ---------------------------------------------------------------------------------------
        # Check maturity of the coins
        curh = self.nodes[2].getblockcount()
        mark_logs("\nCheck maturiy of the coins", self.nodes, DEBUG_MODE)

        dump_sc_info_record(self.nodes[2].getscinfo(scid)['items'][0], 2, DEBUG_MODE)
        mark_logs("Check that %f coins will be mature at h=%d" % (creation_amount, curh + 2), self.nodes, DEBUG_MODE)
        ia = self.nodes[2].getscinfo(scid)['items'][0]["immatureAmounts"]
        for entry in ia:
            if entry["maturityHeight"] == curh + SC_COINS_MAT:
                assert_equal(entry["amount"], creation_amount)

        # Node 1 sends 1 amount to SC
        mark_logs("\nNode 1 sends " + str(fwt_amount_1) + " coins to SC", self.nodes, DEBUG_MODE)

        mc_return_address = self.nodes[1].getnewaddress()
        cmdInput = [{'toaddress': "abcd", 'amount': fwt_amount_1, "scid":scid, 'mcReturnAddress': mc_return_address}]
        self.nodes[1].sc_send(cmdInput)
        self.sync_all()

        # Node 1 sends 3 amounts to SC
        mark_logs("\nNode 1 sends 3 amounts to SC (tot: " + str(fwt_amount_many) + ")", self.nodes, DEBUG_MODE)

        mc_return_address = self.nodes[1].getnewaddress()

        amounts = []
        amounts.append({"toaddress": "add1", "amount": fwt_amount_1, "scid": scid, "mcReturnAddress": mc_return_address})
        amounts.append({"toaddress": "add2", "amount": fwt_amount_2, "scid": scid, "mcReturnAddress": mc_return_address})
        amounts.append({"toaddress": "add3", "amount": fwt_amount_3, "scid": scid, "mcReturnAddress": mc_return_address})

        # Check that mcReturnAddress was properly set.
        tx_id = self.nodes[1].sc_send(amounts)
        tx_obj = self.nodes[1].getrawtransaction(tx_id, 1)
        for out in tx_obj['vft_ccout']:
            assert_equal(mc_return_address, out["mcReturnAddress"], "FT mc return address is different.")
        self.sync_all()

        mark_logs("\n...Node0 generating 1 block", self.nodes, DEBUG_MODE)
        self.nodes[0].generate(1)
        self.sync_all()

        # Check maturity of the coins at actual height
        curh = self.nodes[2].getblockcount()

        dump_sc_info_record(self.nodes[2].getscinfo(scid)['items'][0], 2, DEBUG_MODE)
        count = 0
        mark_logs("Check that %f coins will be mature at h=%d" % (creation_amount, curh + 1), self.nodes, DEBUG_MODE)
        mark_logs("Check that %f coins will be mature at h=%d" % (fwt_amount_many + fwt_amount_1, curh + 2), self.nodes, DEBUG_MODE)
        ia = self.nodes[2].getscinfo(scid)['items'][0]["immatureAmounts"]
        for entry in ia:
            count += 1
            if entry["maturityHeight"] == curh + SC_COINS_MAT:
                assert_equal(entry["amount"], fwt_amount_many + fwt_amount_1)
            if entry["maturityHeight"] == curh + SC_COINS_MAT - 1:
                assert_equal(entry["amount"], creation_amount)

        assert_equal(count, 2)

        # Check maturity of the coins at actual height+1
        mark_logs("\n...Node0 generating 1 block", self.nodes, DEBUG_MODE)

        self.nodes[0].generate(1)
        self.sync_all()
        curh = self.nodes[2].getblockcount()

        dump_sc_info_record(self.nodes[2].getscinfo(scid)['items'][0], 2, DEBUG_MODE)
        count = 0
        mark_logs("Check that %f coins will be mature at h=%d" % (fwt_amount_many + fwt_amount_1, curh + 1), self.nodes, DEBUG_MODE)
        ia = self.nodes[2].getscinfo(scid)['items'][0]["immatureAmounts"]
        for entry in ia:
            if entry["maturityHeight"] == curh + SC_COINS_MAT - 1:
                assert_equal(entry["amount"], fwt_amount_many + fwt_amount_1)
                count += 1

        assert_equal(count, 1)

        # Check no immature coin at actual height+2
        mark_logs("\n...Node0 generating 1 block", self.nodes, DEBUG_MODE)

        self.nodes[0].generate(1)
        self.sync_all()

        scinfo = self.nodes[0].getscinfo(scid, False, False)['items'][0]
        pprint.pprint(scinfo)

        mark_logs("Check that there are no immature coins", self.nodes, DEBUG_MODE)
        ia = self.nodes[2].getscinfo(scid)['items'][0]["immatureAmounts"]
        assert_equal(len(ia), 0)

        mark_logs("Checking blockindex persistance stopping and restarting nodes", self.nodes, DEBUG_MODE)
        scgeninfo = self.nodes[2].getscgenesisinfo(scid)

        stop_nodes(self.nodes)
        wait_bitcoinds()
        self.setup_network(False)

        scgeninfoPost = self.nodes[0].getscgenesisinfo(scid)
        assert_equal(scgeninfo, scgeninfoPost)


if __name__ == '__main__':
    SCCreateTest().main()
