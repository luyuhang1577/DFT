# -*- coding: utf-8 -*-

import re
import random
from enum import Enum
import math
import sys
from classdef import node
from classdef import gtype
from classdef import ntype
from gate import GAND_m, GOR_m, GXOR_m, GNOT
from gate import GNAND_m, GNOR_m# , GXNOR_m, GNOT
# from faultdict_gen import faultdict_gen
from mini_faultlist_gen import mini_faultlist_gen
from equv_domain import equv_domain
from d_alg import D_alg
from classdef import five_value
from classdef import podem_node_5val
from podem import podem
import networkx as nx
import matplotlib.pyplot as plt
from random import randint
import time
import pdb
from multiprocessing import Process, Pipe
import numpy as np
# from podem_m import podem
# from D_alg import imply_and_check

#TODO: one issue with ckt (2670 as example) is that some nodes are both PI and PO
#TODO: Error "NoneType' object has no attribute 'add_dnodes" because of size error

#__________________________________________________#
#________________main_test for cread_______________#
#__________________________________________________#

class Circuit:
    def __init__(self, c_name):
        ''' a digital logic circuit
        c_name:             circuit name, without .ckt extension
        nodes:              list of nodes objects
        input_num_list:     list of PI node numbers
        nodes_cnt:          total number of nodes in the circuit
        nodes_lev:          circuit information after levelization,
                            each node has level info, previous nodelist_order
        nodes_sim:          circuit information after logic simulation, each node has value
        fautl_name:         full fault list in string format
        fault_node_num:     node numbers in full fault list
        '''
        #TODO: we need a list of PI nodes
        #TODO: we need a list of PO nodes

        self.c_name = c_name
        self.nodes = []
        self.input_num_list = []
        self.nodes_cnt = None
        self.nodes_lev = None
        self.nodes_sim = None
        self.fault_name = []
        self.fault_node_num = []
        self.fault_type = [] # fault type for each node in fault list, (stuck at)1 or (stuck at)0
        self.d_coverage = None
        self.pd_coverage = None
        self.fd_data = None
        self.d_correctness_rate = None
        self.pd_correctness_rate = None
        self.pass_cnt = 0
        self.input_cnt = None
        self.rfl_node = []
        self.rfl_ftype = []
        self.lvls_list = [] #controllability and observability
        self.node_ids = [] #for mapping random node ids to 0-len(nodes)

        # possibly Redundant, Saeed added temporary:
        self.PI = []

    def read_circuit(self):
        """
        Read circuit from .ckt file, instantiate each node as a class,
        initialize self.nodes
        """
        path = "../data/ckt/{}.ckt".format(self.c_name)
        f = open(path,'r')
        indx = 0
        nodedict = {}
        fileList = []
        # TODO: this is a big issue here, emergency to fix
        # Referred to as size error
        nodedict_list = [None] * (100*int(self.c_name[1:]))
        temp_dict = {}
        lines = f.readlines()

        for line in lines:
            if (line != "\n"):
                fileList.append(line.split())
        for i in fileList:
            i[1] = int(i[1])
        for line in fileList:
            new_node = node()
            new_node.ntype = ntype(int(line[0])).name
            new_node.num = int(line[1])
            if new_node.num not in self.node_ids:
                self.node_ids.append(new_node.num)
            new_node.gtype = gtype(int(line[2])).name

            if (ntype(int(line[0])).value == 2):   #if BRCH --> unodes
                new_node.add_unodes(nodedict_list[int(line[3])])
                new_node.fout = 1
            else:                                       #if not BRCH --> fout
                new_node.fout = int(line[3])

            if (ntype(int(line[0])).value != 2):
                new_node.fin = int(line[4])
                for i in range (int(line[4])):
                    if (nodedict_list[int(line[5 + i])] == None):
                        new_node_temp = node()
                        new_node_temp.num = int(line[5 + i])
                        nodedict.update({new_node_temp.num: new_node_temp})
                        nodedict_list[new_node_temp.num] = new_node_temp
                        new_node.add_unodes(nodedict_list[int(line[5 + i])])
                        temp_dict.update({int(line[5 + i]): new_node.num})
                    else:
                        new_node.add_unodes(nodedict_list[int(line[5 + i])])
            else:
                new_node.fin = 1

            if ((ntype(int(line[0])).value == 1) or (ntype(int(line[0])).value == 2)):
                new_node.cpt = 1

            new_node.index = indx
            indx = indx + 1
            self.nodes.append(new_node)
            if (temp_dict.get(new_node.num) != None):
                for i in self.nodes:
                    if (i.num == temp_dict.get(new_node.num)):
                        for j in i.unodes:
                            if (j.num == new_node.num):
                                i.unodes.remove(j)
                                i.unodes.append(new_node)
            nodedict_list[new_node.num] = new_node
            nodedict.update({new_node.num: new_node})
            #TODO:feedback only to one gate
        f.close()
        for i in range(len(self.nodes)):
            if (self.nodes[i].ntype != 'PI'):
                for j in range (self.nodes[i].fin):
                    # TODO: debugging
                    if self.nodes[i].unodes[j] == None:
                        print(i, j, self.nodes[i].num)
                        pdb.set_trace()
                    self.nodes[i].unodes[j].add_dnodes(self.nodes[i])
            else:
                self.input_num_list.append(self.nodes[i].num)

        self.nodes_cnt = len(self.nodes)
        self.input_cnt = len(self.input_num_list)
        # return self.nodes

    def lev_DFS(self):
        print("levelization with BFS")


    def lev_orgin(self):
        """
        Levelization.
        Based on gate type of the nodes and connection relationship between nodes,
        give every node a level information. Primary inputs have the loweset level, i.e., 0
        """
        count = self.nodes_cnt
        flag_changed = True
        for i in self.nodes:
            if i.gtype == 'IPT':
                i.lev = 0
                count -= 1
            else:
                i.lev = -1

        while flag_changed:
            flag_changed = False
            for i in self.nodes:
                if i.lev == -1:
                    for k in range(0, i.fin):
                        flag = 0
                        if i.unodes[k].lev == -1:
                            flag = 1
                            break

                    if flag == 0:
                        flag_changed = True
                        max_lvl = 0
                        for j in range(0, i.fin):
                            if i.unodes[j].lev >= max_lvl:
                                max_lvl = i.unodes[j].lev
                        i.lev = max_lvl + 1
                        count -= 1
        self.nodes_lev = sorted(self.nodes, key=lambda x: x.lev)

        self.num_lvls = 0
        for i in self.nodes_lev:
            self.num_lvls = max(i.lev, self.num_lvls)

        for j in range(self.num_lvls + 1):
            self.lvls_list.append([])
            for i in self.nodes_lev:
                if i.lev == j:
                    self.lvls_list[j].append(i)
        
    def lev(self):
        """
        Levelization.
        Based on gate type of the nodes and connection relationship between nodes,
        give every node a level information. Primary inputs have the loweset level, i.e., 0
        """
        ilist=set()
        nextlist=set()
        for i in self.nodes:
            if i.gtype == 'IPT':
                i.lev = 0
                ilist.add(i)
            else:
                i.lev = -1
        flag=1
        while(flag):
            for i in ilist:
                for k in range(0, i.fout):
                    if(i.dnodes[k].lev < i.lev+1):
                        i.dnodes[k].lev = i.lev+1
                        nextlist.add(i.dnodes[k])
            if(not nextlist):
                flag=0
            ilist=nextlist
            nextlist=set()  
        self.nodes_lev = sorted(self.nodes, key=lambda x: x.lev)

        self.num_lvls = 0
        for i in self.nodes_lev:
            self.num_lvls = max(i.lev, self.num_lvls)

        for j in range(self.num_lvls + 1):
            self.lvls_list.append([])
            for i in self.nodes_lev:
                if i.lev == j:
                    self.lvls_list[j].append(i)


    def get_random_input_pattern(self):
        """
        Randomly generate a test pattern for input nodes.
        Could be used to check the validity of logic simulation
        and deductive fault simulation.
        """
        rand_input_val_list = []
        for i in range(len(self.input_num_list)):
            rand_input_val_list.append(random.randint(0,1))
        return rand_input_val_list


    def read_PO(self):
        res = {}
        for node in self.nodes:
            if node.ntype == "PO":
                res["out" + str(node.num)] = node.value
        return res


    def logic_sim(self, input_val_list):
        """
        Logic simulation:
        Reads a given pattern and perform the logic simulation
        For now, this is just for binary logic
        """
        node_dict = dict(zip(self.input_num_list, input_val_list))
        # TODO Emergency: why did they make a copy
        # self.nodes_sim = self.nodes_lev.copy()

        for i in self.nodes_lev:

            i.D1 = False
            i.D2 = False

            unodes_val = []
            for unode in i.unodes:
                unodes_val.append(unode.value)

            if (i.gtype == 'IPT'):
                i.value = node_dict[i.num]

            elif (i.gtype == 'BRCH'):
                i.value = i.unodes[0].value

            elif (i.gtype == 'XOR'):
                i.value = GXOR_m(unodes_val)

            elif (i.gtype == 'OR'):
                i.value = GOR_m(unodes_val)

            elif (i.gtype == 'NOR'):
                i.value = GNOR_m(unodes_val)

            elif (i.gtype == 'NOT'):
                i.value = GNOT(i.unodes[0].value)

            elif (i.gtype == 'NAND'):
                i.value = GNAND_m(unodes_val)

            elif (i.gtype == 'AND'):
                i.value = GAND_m(unodes_val)


    def dfs(self):
        """
        Deductive fault simulation:
        For a given test pattern,
        DFS simulates a set of faults detected by the test pattern.
        Validate the test pattern return by D or Podem
        """
        control = {'AND':0, 'NAND':0, 'OR':1, 'NOR':1}
        c_list = []
        nc_list = []
        fault_list = set()
        for item in self.nodes_sim:
            if item.gtype == 'IPT':
                item.add_faultlist((item.num, GNOT(item.value)))
                # print(item.num, item.faultlist_dfs)
            elif item.gtype == 'BRCH':
                item.faultlist_dfs = item.unodes[0].faultlist_dfs.copy()
                item.add_faultlist((item.num, GNOT(item.value)))
            elif item.gtype == 'XOR':
                s = set()
                for i in item.unodes:
                    s = s.symmetric_difference(set(i.faultlist_dfs))
                s.add((item.num, GNOT(item.value)))
                item.faultlist_dfs = list(s)
                if item.ntype == 'PO':
                    fault_list = fault_list.union(set(item.faultlist_dfs))
            elif item.gtype == 'NOT':
                item.faultlist_dfs = item.unodes[0].faultlist_dfs.copy()
                item.add_faultlist((item.num, GNOT(item.value)))
                if item.ntype == 'PO':
                    fault_list = fault_list.union(set(item.faultlist_dfs))
            else :  #gtype = gate beside xor
                flag = 0
                # find if input has control value
                for i in item.unodes:
                    c = control[item.gtype]
                    # print(item.num,i.num)
                    if i.value == c:
                        flag = 1
                        c_list.append(i)
                    else :
                        nc_list.append(i)
                # all input is no controlling value
                if flag == 0:
                    s = set()
                    for j in nc_list:
                        s = s.union(set(j.faultlist_dfs))
                    item.faultlist_dfs.clear()
                    item.faultlist_dfs = list(s)
                    item.add_faultlist((item.num, GNOT(item.value)))
                # input has control value
                else :
                    s_control = set(c_list[0].faultlist_dfs)
                    for j in c_list:
                        s_control = s_control.intersection(set(j.faultlist_dfs))
                    if nc_list == []:
                        s_ncontrol = set()
                    else:
                        s_ncontrol = set(nc_list[0].faultlist_dfs)
                        for j in nc_list:
                            s_ncontrol = s_ncontrol.union(set(j.faultlist_dfs))
                    s_control.difference(s_ncontrol)
                    item.faultlist_dfs.clear()
                    item.faultlist_dfs = list(s_control)
                    item.add_faultlist((item.num, GNOT(item.value)))
                c_list.clear()
                nc_list.clear()
                if item.ntype == 'PO':
                    fault_list = fault_list.union(set(item.faultlist_dfs))

        return fault_list


    def get_full_fault_list(self):
        """
        Generate a list of all SSAFs in the circuit.
        Given N nodes, there should be 2N SSAFs.
        """
        for node in self.nodes_lev:
            sa0_str = "{}@0".format(node.num)
            self.fault_name.append(sa0_str)
            self.fault_node_num.append(node.num)
            self.fault_type.append(0)

            sa1_str = "{}@1".format(node.num)
            self.fault_name.append(sa1_str)
            self.fault_node_num.append(node.num)
            self.fault_type.append(1)



    def pfs(self,input_val):
        """
        Parallel Fault Simulation:
        For a given test pattern,
        PFS simulates a set of faults detected by the test pattern.
        """
        faultnum = len(self.fault_node_num)
        n = sys.maxsize
        bitlen = int(math.log2(n))+1

        output_num = list()
        for i in self.nodes_lev:
            if i.ntype == 'PO':
                output_num.append(i.num)

        node_num = []
        node_val = []

        node_num = self.input_num_list
        node_val = input_val
        # hash map
        node_input_dict = dict(zip(node_num, node_val))

        # hash map: node_num is key, object of node is value
        node_all_num = list()
        for i in self.nodes_lev:
            node_all_num.append(i.num)
        node_dict = dict(zip(node_all_num, self.nodes_lev))
        for i in range(len(node_all_num)):
            node_dict[node_all_num[i]].parallel_value = 0

        # cal iter
        if faultnum % (bitlen-1) == 0:
            iter = int(faultnum / (bitlen - 1))
        else:
            iter = int(faultnum / (bitlen - 1))+1
        #print("the value of iter: %d"%(iter))

        # write result
        detected_node = []
        detected_node_value = []

        output_empty = 0
        pfs_fault_val = []
        pfs_fault_num = []
        for n in self.fault_node_num:
            pfs_fault_num.append(n)
        for t in self.fault_type:
            pfs_fault_val.append(t)
        while (iter != 0):
            fault_num = []
            fault_val = []
            for i in self.nodes_lev:
                i.sa0 = 0
                i.sa1 = 0
            read_fault_ind = 0
        #print("begin to while")

            # save bitlen -1 fault
            while(1):
                content1 = len(pfs_fault_num)
                if content1==0:
                    break

                fault_val.append(pfs_fault_val.pop())
                fault_num.append(pfs_fault_num.pop())


                read_fault_ind = read_fault_ind + 1
                if read_fault_ind == bitlen - 1:
                    break
            for i in range(len(fault_num)):
                if fault_val[i] == 1:
                    node_dict[fault_num[i]
                            ].sa1 = node_dict[fault_num[i]].sa1 + 2**(i+1)
                else:
                    node_dict[fault_num[i]
                            ].sa0 = node_dict[fault_num[i]].sa0 + 2**(i+1)

            for i in self.nodes_lev:
                if i.gtype == 'IPT':
                    if i.num in node_num:
                        i.parallel_value = 0
                        for j in range(bitlen):
                            i.parallel_value = i.parallel_value + \
                                (int(node_input_dict[i.num]) << j)
                        i.parallel_value = ((~i.sa0) & i.parallel_value) | i.sa1
                elif i.gtype == 'BRCH':
                    i.parallel_value = ((~i.sa0) & (
                        i.unodes[0].parallel_value)) | i.sa1

                elif i.gtype == 'XOR':
                    for j in range(0, i.fin):
                        if j == 0:
                            temp_value = i.unodes[j].parallel_value
                        else:
                            temp_value = temp_value ^ i.unodes[j].parallel_value
                    i.parallel_value = ((~i.sa0) & temp_value) | i.sa1
                elif i.gtype == 'OR':
                    for j in range(0, i.fin):
                        if j == 0:
                            temp_value = i.unodes[j].parallel_value
                        else:
                            temp_value = temp_value | i.unodes[j].parallel_value
                    i.parallel_value = ((~i.sa0) & temp_value) | i.sa1
                elif i.gtype == 'NOR':
                    for j in range(0, i.fin):
                        if j == 0:
                            temp_value = i.unodes[j].parallel_value
                        else:
                            temp_value = temp_value | i.unodes[j].parallel_value
                    i.parallel_value = ((~i.sa0) & (~temp_value)) | i.sa1
                elif i.gtype == 'NOT':
                    i.parallel_value = ((~i.sa0) & (
                        ~i.unodes[0].parallel_value)) | i.sa1
                elif i.gtype == 'NAND':
                    for j in range(0, i.fin):
                        if j == 0:
                            temp_value = i.unodes[j].parallel_value
                        else:
                            temp_value = temp_value & i.unodes[j].parallel_value
                    i.parallel_value = ((~i.sa0) & (~temp_value)) | i.sa1
                elif i.gtype == 'AND':
                    for j in range(0, i.fin):
                        if j == 0:
                            temp_value = i.unodes[j].parallel_value
                        else:
                            temp_value = temp_value & i.unodes[j].parallel_value
                    i.parallel_value = ((~i.sa0) & temp_value) | i.sa1
            iter -= 1

            for i in range(read_fault_ind):
                for j in output_num:
                    temp = node_dict[j].parallel_value
                    # t0 is to choose the value responding to the specific fault node in output
                    # t1 is to move the value to most significant bit
                    t0 = (temp & (1 << (i+1)))
                    t1 = t0 << (bitlen-i-2)
                    t2 = 1 << (bitlen-1)
                    t3 = t1 & t2
                    # t4 is to calculate most least bit which is fault free bit
                    t4 = (temp & 1) << (bitlen-1)
                    if t3 != t4:
                        if fault_num[i] not in detected_node:
                            detected_node.append(fault_num[i])
                            detected_node_value.append(fault_val[i])
                            # print(j,fault_num[i],fault_val[i])
            # output is a set of tuple
            if output_empty == 0:
                output = {(detected_node[0], detected_node_value[0])}
                output_empty += 1
            for i in range(len(detected_node)):
                output.add((detected_node[i], detected_node_value[i]))

        return output


    def gen_fault_dic(self):
        """
        Fault Dictionary:
        key: input pattern value: detected fault (returned by PFS)
        Fault Dictionary can only be generated for small circuits
        because the file size will become too large for big circuits.
        """
        fault_dict = {}
        inputnum = len(self.input_num_list)
        total_pattern = pow(2,inputnum) # produce 2^n different input files for pfs to use

        for i in range(total_pattern):
            #print ('{:05b}'.format(i))#str type output #Suit different input numbers!!!!
            b = ('{:0%db}'%inputnum).format(i)
            list_to_pfs = []
            for j in range(inputnum):
                list_to_pfs.append(int(b[j]))

            #do pfs based on the prodeuced input files
            result = []
            result = self.pfs(list_to_pfs)
            fault = []
            for i in result:
                fault.append("%d@%d" % (i[0], i[1]))

            fault.sort(key = lambda i:int(re.match(r'(\d+)',i).group()))
            #jb51.net/article/164342.htm for referance to sort the output

            fault_dict.update({b: fault})

        fault_dict_result = open("../fault_dic/{}.fd".format(self.c_name), "w")
        for i in range(len(self.input_num_list)):
            if (i<len(self.input_num_list)-1):
                fault_dict_result.write('%d->' % self.input_num_list[i])
            else:
                fault_dict_result.write('%d' % self.input_num_list[i])

        fault_dict_result.write(' as sequence of inputs')
        fault_dict_result.write('\n')
        fault_dict_result.write('input_patterns\t\t\tdetected_faults\n')
        for i in range(total_pattern):
            #print ('{:05b}'.format(i))#str type output #Suit different input numbers!!!!
            b = ('{:0%db}'%inputnum).format(i)
            fault_dict_result.write('%s\t\t\t\t' % b)
            for i in range(len(fault_dict.get(b))):
                fault_dict_result.write('%-5s ' % fault_dict.get(b)[i])#format ok?
            fault_dict_result.write('\n')

        fault_dict_result.close()


    def gen_fault_dic_multithreading(self, thread_cnt, idx):
        """
        Create threads to generate fault dictionaries.
        Speed up the fault dictionary generation process.
        """
        fault_dict = {}
        total_pattern = pow(2, self.input_cnt)
        pattern_per_thread = int(total_pattern / thread_cnt)

        for i in range(idx * pattern_per_thread, (idx + 1) * pattern_per_thread):
            #print ('{:05b}'.format(i))#str type output #Suit different input numbers!!!!
            b = ('{:0%db}'%self.input_cnt).format(i)
            list_to_pfs = []
            for j in range(self.input_cnt):
                list_to_pfs.append(int(b[j]))
        #do pfs based on the prodeuced input files
            result = []
            result = self.pfs(list_to_pfs)
            fault = []
            #print(result)
            for i in result:
                fault.append("%d@%d" % (i[0], i[1]))

            fault.sort(key = lambda i:int(re.match(r'(\d+)',i).group()))
            fault_dict.update({b: fault})

        with open ("../fault_dic/{}_{}.fd".format(self.c_name, idx), "w") as fo:
            for i in range(self.input_cnt):
                if (i < self.input_cnt - 1):
                    fo.write('%d->' % self.input_num_list[i])
                else:
                    fo.write('%d' % self.input_num_list[i])
            fo.write(' as sequence of inputs')
            fo.write('\n')
            fo.write('input_patterns\t\t\tdetected_faults\n')
            for i in range(idx * pattern_per_thread, (idx + 1) * pattern_per_thread):
                b = ('{:0%db}'%self.input_cnt).format(i)
                fo.write('%s\t\t\t\t' % b)
                for i in range(len(fault_dict.get(b))):
                    fo.write('%-5s ' % fault_dict.get(b)[i])#format ok?
                fo.write('\n')
        print("thread #{} of {} threads finished".format(idx, thread_cnt))

    def get_reduced_fault_list(self):
        """
        Using checkpoint theorem,
        generate reduced fault list
        """
        faults_fanout = []
        for i in range(len(self.nodes)):
            if (self.nodes[i].cpt == 1):
                #print self.nodes[i].num
                for j in range(self.nodes[i].fout):
                    faults_fanout.append(self.nodes[i].dnodes[j].index)
                self.nodes[i].sa0 = 1
                self.nodes[i].sa1 = 1
        # uniquefanout = sorted(set(faults_fanout))
        # print uniquefanout
        for i in range(len(faults_fanout)):
            cptflag = 0
            if ((self.nodes[faults_fanout[i]].gtype == 'NOR') or (self.nodes[faults_fanout[i]].gtype == 'OR')):
                for j in range(self.nodes[faults_fanout[i]].fin):
                    if self.nodes[faults_fanout[i]].unodes[j].cpt == 1:
                        if cptflag == 0:
                            cptflag = 1
                        else: self.nodes[faults_fanout[i]].unodes[j].sa1 = 0
            elif ((self.nodes[faults_fanout[i]].gtype == 'NAND') or (self.nodes[faults_fanout[i]].gtype == 'AND')):
                for j in range(self.nodes[faults_fanout[i]].fin):
                    if self.nodes[faults_fanout[i]].unodes[j].cpt == 1:
                        if cptflag == 0:
                            cptflag = 1
                        else: self.nodes[faults_fanout[i]].unodes[j].sa0 = 0
        for i in range(len(self.nodes)):
            if self.nodes[i].sa0 == 1:
                self.rfl_node.append(self.nodes[i].num)
                self.rfl_ftype.append(0)
            if self.nodes[i].sa1 == 1:
                self.rfl_node.append(self.nodes[i].num)
                self.rfl_ftype.append(1)

    #to be continued
    def equvalenceAndDominance(self):
        return

    def D_alg(self, fault_index, imply_counter):
        """
        Given a fault, returns whether it can be detected,
        if can, returns a test pattern.
        """
        res = D_alg(self.nodes, fault_index, imply_counter)
        return res
    #to be continued
    def podem(self, i):
        """
        Given a fault, returns whether it can be detected,
        if can, returns a test pattern.
        """
        res = podem(self.fault_node_num[i], self.fault_type[i], self.nodes, self.nodes_lev)
        return res

    def read_fault_dict(self):
        """read already generated fault dictionary"""
        fd = open("../fault_dic/{}.fd".format(self.c_name),"r")
        self.fd_data = fd.read()
        fd.close()

    def get_patterns(self, test_pattern):
        """
        Given a test pattern with "X"s,
        generate all possible patterns represent by that pattern.
        """
        xidx = []
        xcnt = 0
        for i in range(len(test_pattern)):
            if test_pattern[i] == 'X':
                xidx.append(i)
                xcnt += 1

        fmt_str = '{0:0%db}'%(xcnt)
        bit = []

        plist = []
        for i in range(2 ** (xcnt)):
            bit = [int(j) for j in fmt_str.format(i)]
            plist.append(bit)

        search = []
        for p in plist:
            binary_patterns = test_pattern
            for i in range(xcnt):
                binary_patterns[xidx[i]] = p[i]
            search.append(''. join(map(str, binary_patterns)))
        return search


    def check_failure(self, fault_name):
        """
        Check if the fault is undetected by searching the fault dictionary
        called for small circuit with fault fictionary only.
        """
        srch_str = '\s{}'.format(fault_name)
        if re.findall(srch_str, self.fd_data):
            return False
        else:
            return True

    def check_success(self, fault_name, search_patterns):
        """
        Check if the returned pattern can detected the given fault
        by searching the fault dictionary.
        called for small circuit with fault fictionary only.
        """
        pattern_found = 0
        for p in search_patterns:
            srch_str = '{}.*?\s{}'.format(p, fault_name)
            # print (srch_str)
            res = re.findall(srch_str, self.fd_data)
            if res:
                pattern_found = 1
            else:
                pattern_found = 0
        if pattern_found:
            return True
        else:
            return False

    def get_Xless_pattern(self, pattern):
        """
        For big circuit with too many Xs,
        randomly assign 1 or 0 to each X and returns a pattern.
        """
        pattern_Xless = []
        for v in pattern:
            if v == 'X':
                entry = random.getrandbits(1)
            else:
                entry = v
            pattern_Xless.append(entry)
        return pattern_Xless

    def get_d_correctness(self):
        """
        Check correctness of D algorithm for both detected and undetected faults.
        Called for small circuit.
        """
        self.read_fault_dict()
        d_error_cnt = 0
        # run the faults in full fault list
        for j in range(len(self.fault_node_num)):
            fault_index = -1
            for i in range(len(self.nodes_lev)):
                self.nodes_lev[i].value = five_value.X.value
                if self.nodes_lev[i].num == self.fault_node_num[j]:
                    # stuck at 0
                    if self.fault_type[j] == 0:
                        self.nodes_lev[i].value = five_value.D.value
                        fault_index = i
                    # stuck at 1
                    elif self.fault_type[j] == 1:
                        self.nodes_lev[i].value = five_value.D_BAR.value
                        fault_index = i
                    else:
                        print("operator error")
            imply_counter = Imply_counter(8000)
            res = self.D_alg(fault_index, imply_counter)

            # If the fault is detectable in
            if res.result == 1:
                # print("D_alg SUCCESS")
                search_patterns = self.get_patterns(res.pattern)
                pattern_found = self.check_success(self.fault_name[j], search_patterns)
                if pattern_found == 0:
                    print("D algorithm Error at fault {}, type SUCCESS".format(self.fault_name[j]))
                    d_error_cnt += 1
                else:
                    pass

            else:
                # print("D_alg FAILURE")
                error_not_found = self.check_failure(self.fault_name[j])
                if error_not_found == 0:
                    print("D algorithm Error at fault {}, type FAILURE".format(self.fault_name[j]))
                    d_error_cnt += 1
                else:
                    pass
        self.d_correctness_rate = ((len(self.fault_node_num) - d_error_cnt) / len(self.fault_node_num)) * 100
        print ("D algorithm correctness rate: {}%".format(self.d_correctness_rate))

    def get_d_coverage(self):
        """
        Count the percentage of faults in the full fault list D algorithm claimed as detected.
        Further revise the coverage by passing the test pattern returned by D to DFS to see
        if the given fault is in the detected fault set.
        called for big circuits
        """
        failure_fault_list = []
        check_cnt = 0
        self.pass_cnt = 0

        for j in range(len(self.fault_node_num)):
            fault_index = -1
            for i in range(len(self.nodes)):
                if self.nodes[i].num == self.fault_node_num[j]:
                    # stuck at 0
                    if self.fault_type[j] == 0:
                        self.nodes[i].d_value.append(five_value.D.value)
                        fault_index = i
                    # stuck at 1
                    elif self.fault_type[j] == 1:
                        self.nodes[i].d_value.append(five_value.D_BAR.value)
                        fault_index = i
                    else:
                        print("operator error")
                else:
                    self.nodes[i].d_value.append(five_value.X.value)
            imply_counter = Imply_counter(8000)
            res = self.D_alg(fault_index, imply_counter)

            if res.result == 1:
                self.pass_cnt += 1

            else:
                failure_fault_list.append(self.fault_name[j])


            check_cnt += 1
            print ("check_cnt={}".format(check_cnt))
        self.d_coverage = (self.pass_cnt / len(self.fault_node_num)) * 100
        print ("D algorithm fault coverage: {}".format(self.d_coverage))
        self.pass_cnt = 0
        return failure_fault_list

    def get_podem_correctness(self):
        """
        Check correctness of Podem for both detected and undetected faults.
        Called for small circuit.
        """
        self.read_fault_dict()
        pd_error_cnt = 0
        for i in range(len(self.fault_node_num)):
            res = self.podem(i)
            if res.result == 1:
                search_patterns = self.get_patterns(res.pattern)
                pattern_found = self.check_success(self.fault_name[i], search_patterns)
                if pattern_found == 0:
                    print("Podem algorithm Error at fault {}, type SUCCESS".format(self.fault_name[i]))
                    pd_error_cnt += 1
                else:
                    pass
            else:
                # print("Podem_alg FAILURE")
                error_not_found = self.check_failure(self.fault_name[i])
                if error_not_found == 0:
                    print("Podem algorithm Error at fault {}, type FAILURE".format(self.fault_name[i]))
                    pd_error_cnt += 1
                else:
                    pass
        self.pd_correctness_rate = ((len(self.fault_node_num) - pd_error_cnt) / len(self.fault_node_num)) * 100
        print ("Podem algorithm correctness rate: {}%".format(self.pd_correctness_rate))

    def get_podem_coverage(self):
        """
        Count the percentage of faults in the full fault list Podem claimed as detected.
        Further revise the coverage by passing the test pattern returned by Podem to DFS to see
        if the given fault is in the detected fault set.
        called for big circuits
        """
        self.pass_cnt = 0
        for i in range(len(self.fault_node_num)):
            res = self.podem(i)
            if res.result == 1:
                self.pass_cnt += 1
                pattern = res.pattern
                input_pattern = self.get_Xless_pattern(pattern)
                # print(input_pattern)
                self.logic_sim(input_pattern)
                fault_set = self.dfs()
                fault = (self.fault_node_num[i],self.fault_type[i])
                if fault in fault_set:
                    pass
                else:
                    self.pass_cnt -= 1
                    print("Test Pattern error for Podem at fault {}".format(fault))
            else:
                pass
        self.pd_coverage = self.pass_cnt / len(self.fault_node_num) * 100
        self.pass_cnt = 0
        print ("Podem algorithm fault coverage: {}%".format(self.pd_coverage))


    def podem_single_test(self, fault_node_num, fault_type):
        res = podem(fault_node_num, fault_type, self.nodes, self.nodes_lev)
        return res


    def time_for_podem(self):
        totaltime = 0
        for i in range(len(self.fault_node_num)):
            starttime = time.time()
            res = self.podem_single_test(self.fault_node_num[i], self.fault_type[i])
            endtime = time.time()
            totaltime = totaltime + (endtime - starttime)
        print(totaltime)


    def co_ob_info(self):
        print("\t".join(self.nodes_lev[0].print_info(get_labels=True)))
        for lvl in self.lvls_list:
            for n in lvl:
                n.print_info(print_labels=False)

    def SCOAP_CC(self):

        for i in self.lvls_list[0]:
            i.CC0 = 1
            i.CC1 = 1

        for i in range(1, self.num_lvls+1):

            for j in self.lvls_list[i]:
                unodes_CC0 = []
                unodes_CC1 = []
                for unode in j.unodes:
                    unodes_CC0.append(unode.CC0)
                    unodes_CC1.append(unode.CC1)
                minCC0 = min(unodes_CC0)
                minCC1 = min(unodes_CC1)

                # TODO: this seems not ok!
                # For BRCH, the same as upnode
                if j.gtype == "BRCH":
                    j.CC0 = minCC0
                    j.CC1 = minCC1

                # TODO: this is only for XOR with 2 inputs
                elif j.gtype == "XOR":
                    j.CC0 = 1 + min(j.unodes[0].CC1+j.unodes[1].CC0, j.unodes[0].CC0+j.unodes[1].CC1)
                    j.CC1 = 1 +  min(j.unodes[0].CC0+j.unodes[1].CC0, j.unodes[0].CC1+j.unodes[1].CC1)

                elif j.gtype == "OR":
                    j.CC0 = 1 + sum(unodes_CC0)
                    j.CC1 = 1 + minCC1

                elif j.gtype == "NOR":
                    j.CC1 = 1 + sum(unodes_CC0)
                    j.CC0 = 1 + minCC1

                elif j.gtype == "NOT":
                    j.CC0 = j.unodes[0].CC1 + 1
                    j.CC1 = j.unodes[0].CC0 + 1

                elif j.gtype == "NAND":
                    j.CC0 = 1 + sum(unodes_CC1)
                    j.CC1 = 1 + minCC0

                elif j.gtype == "AND":
                    j.CC1 = 1 + sum(unodes_CC1)
                    j.CC0 = 1 + minCC0


    def SCOAP_CO(self):

        for i in self.lvls_list[-1]:
            i.CO = 1

        for lvl in range(self.num_lvls, -1, -1):
            for j in self.lvls_list[lvl]:

                unodes_CC0 = []
                unodes_CC1 = []
                for unode in j.unodes:
                    unodes_CC0.append(unode.CC0)
                    unodes_CC1.append(unode.CC1)

                if j.gtype == "BRCH":
                    dnodes_CO =  []
                    for k in j.unodes[0].dnodes:
                        dnodes_CO.append(k.CO)
                    j.unodes[0].CO = min(dnodes_CO)

                # TODO: Only works for XOR2
                elif j.gtype == "XOR":
                    j.unodes[0].CO = min(j.unodes[1].CC1, j.unodes[1].CC0)+ j.CO + 1
                    j.unodes[1].CO = min(j.unodes[0].CC1, j.unodes[0].CC0)+ j.CO + 1

                elif j.gtype == "NOT":
                    j.unodes[0].CO = j.CO + 1

                elif j.gtype == "OR":
                    for k in j.unodes:
                        k.CO = sum(unodes_CC0) - k.CC0 + j.CO + 1

                elif j.gtype == "NOR":
                    for k in j.unodes:
                        k.CO = sum(unodes_CC0) - k.CC0 + j.CO + 1

                elif j.gtype == "NAND":
                    for k in j.unodes:
                        k.CO = sum(unodes_CC1) - k.CC1 + j.CO + 1

                elif j.gtype == "AND":
                    for k in j.unodes:
                        k.CO = sum(unodes_CC1) - k.CC1 + j.CO + 1




    ## TODO: What about inverter?
    def STAFAN_CS(self, num_pattern, limit=None, detect=False):
        ''' note:
        we are generating random numbers with replacement
        if u need to test all the patterns, add a new flag
        initial test showed when 10**7 in 4G patterns, 16M replacements
        random.choice is very inefficient
        '''
        inputnum = len(self.input_num_list)
        limit = [0, pow(2, inputnum)-1] if limit==None else limit
        # patterns = np.random.choice(limit[1]-limit[0], num_pattern, replace=False)
        # patterns = [x+limit[0] for x in patterns]

        # for pattern in patterns:
        for k in range(num_pattern):
            # TODO: Read note about replacement
            b = ('{:0%db}'%inputnum).format(randint(limit[0], limit[1]))
            list_to_logicsim = []
            for j in range(inputnum):
                list_to_logicsim.append(int(b[j]))
            # list_to_logicsim = [1,1,1,1,1]
            # print(b)
            self.logic_sim(list_to_logicsim)

            for i in self.nodes_lev:

                # counting values
                i.one_count = i.one_count + 1 if i.value == 1 else i.one_count
                i.zero_count = i.zero_count + 1 if i.value ==0 else i.zero_count

                # sensitization
                if i.is_sensible():
                    i.sen_count += 1

            for node in reversed(self.nodes_lev):
                node.sense = node.is_sensible()
                node.is_detectable()

        # calculate percentage/prob
        for i in self.nodes_lev:
            i.C1 = i.one_count / num_pattern
            i.C0 = i.zero_count / num_pattern
            i.S = i.sen_count / num_pattern
            i.D0_p = i.D0_count / num_pattern
            i.D1_p = i.D1_count / num_pattern


    def STAFAN_B(self):
        # TODO: comment and also the issue of if C1==1
        # calculate observability
        for i in reversed(self.nodes_lev):

            if (i.ntype == 'PO'):
                i.B1 = 1.0
                i.B0 = 1.0

            else:
                if (i.dnodes[0].gtype == 'AND'):
                    if (i.C1 == 0):
                        # print("case 0")
                        i.B1 = 1.0
                    else :
                        i.B1 = i.dnodes[0].B1 * i.dnodes[0].C1 / i.C1

                    if (i.C0 == 0):
                        # print("case 0")
                        i.B0 = 1.0
                    else :
                        i.B0 = i.dnodes[0].B0 * (i.S - i.dnodes[0].C1) / i.C0

                elif(i.dnodes[0].gtype == 'NAND'):
                    if (i.C1 == 0):
                        # print("case 0")
                        i.B1 = 1.0
                    else :
                        i.B1 = i.dnodes[0].B0 * i.dnodes[0].C0 / i.C1
                    if (i.C0 == 0):
                        # print("case 0")
                        i.B0 = 1.0
                    else :
                        i.B0 = i.dnodes[0].B1 * (i.S - i.dnodes[0].C0) / i.C0

                elif(i.dnodes[0].gtype == 'OR'):
                    if (i.C1 == 0):
                        # print("case 0")
                        i.B1 = 1.0
                    else :
                        i.B1 = i.dnodes[0].B1 * (i.S - i.dnodes[0].C0) / i.C1

                    if (i.C0 == 0):
                        # print("case 0")
                        i.B0 = 1.0
                    else :
                        i.B0 = i.dnodes[0].B0 * i.dnodes[0].C0 / i.C0

                elif(i.dnodes[0].gtype == 'NOR'):
                    if (i.C1 == 0):
                        # print("case 0")
                        i.B1 = 1.0
                    else :
                        i.B1 = i.dnodes[0].B0 * (i.S - i.dnodes[0].C1) / i.C1
                    if (i.C0 == 0):
                        # print("case 0")
                        i.B0 = 1.0
                    else :
                        i.B0 = i.dnodes[0].B1 * i.dnodes[0].C1 / i.C0

                elif(i.dnodes[0].gtype == 'NOT'):
                    i.B1 = i.dnodes[0].B0
                    i.B0 = i.dnodes[0].B1

                elif(i.dnodes[0].gtype == 'XOR'):
                    i.B1 = i.dnodes[0].B0
                    i.B0 = i.dnodes[0].B1

                elif(i.dnodes[0].gtype == 'BRCH'):
                    i.B1 = i.dnodes[0].B1 + i.dnodes[1].B1 - (i.dnodes[0].B1 * i.dnodes[1].B1)
                    i.B0 = i.dnodes[0].B0 + i.dnodes[1].B0 - (i.dnodes[0].B0 * i.dnodes[1].B0)


    def control_thread(self, conn, c_name, i, total_T,num_proc):
        circuit = Circuit(c_name)
        circuit.read_circuit()
        circuit.lev()
        inputnum = len(circuit.input_num_list)
        circuit.STAFAN_CS(int(total_T/num_proc), [int(pow(2, inputnum)/num_proc)*i,int(pow(2, inputnum)/num_proc)*(i+1)-1])
        circuit.nodes_lev.sort(key=lambda x: x.num)
        one_count_list = []
        zero_count_list = []
        sen_count_list = []
        D0_count = []
        D1_count = []
        for i in circuit.nodes_lev:
            one_count_list.append(i.one_count)
            zero_count_list.append(i.zero_count)
            sen_count_list.append(i.sen_count)
            D0_count.append(i.D0_count)
            D1_count.append(i.D1_count)
        circuit.nodes_lev.sort(key=lambda x: x.lev)
        conn.send((one_count_list, zero_count_list, sen_count_list, D0_count, D1_count))
        conn.close()


    def STAFAN(self, total_T, num_proc=1):
        start_time = time.time()
        # thread_cnt = 1
        process_list = []
        for i in range(num_proc):
        # for idx in process_list:
            parent_conn, child_conn = Pipe()
            p = Process(target = self.control_thread, args =(child_conn, self.c_name, i, total_T,num_proc, ))
            p.start()
            process_list.append((p, parent_conn))

        one_count_list = [0] * self.nodes_cnt
        zero_count_list = [0] * self.nodes_cnt
        sen_count_list = [0] * self.nodes_cnt
        D1_count_list = [0] * self.nodes_cnt
        D0_count_list = [0] * self.nodes_cnt

        for p, conn in process_list:
            tup = conn.recv()
            for i in range(len(tup[0])):
                one_count_list[i] += tup[0][i]
                zero_count_list[i] += tup[1][i]
                sen_count_list[i] += tup[2][i]
                D0_count_list[i] += tup[3][i]
                D1_count_list[i] += tup[4][i]
            p.join()
        self.nodes_lev.sort(key=lambda x: x.num)
        for i in range(len(self.nodes_lev)):
            self.nodes_lev[i].C1 = one_count_list[i] / total_T
            self.nodes_lev[i].C0 = zero_count_list[i] / total_T
            self.nodes_lev[i].S = sen_count_list[i] / total_T
            self.nodes_lev[i].D0_count = D0_count_list[i]
            self.nodes_lev[i].D1_count = D1_count_list[i]
            self.nodes_lev[i].D0_p = D0_count_list[i] / total_T
            self.nodes_lev[i].D1_p = D1_count_list[i] / total_T

        #print (self.nodes_lev[i].num, self.nodes_lev[i].one_control, self.nodes_lev[i].zero_control,self.nodes_lev[i].sen_p)
        self.nodes_lev.sort(key=lambda x: x.lev)
        self.STAFAN_B()
        end_time = time.time()
        duration = end_time - start_time
        print ("Processor count: {}, Time taken: {:.2f} sec".format(num_proc, duration))


    def gen_graph(self):
        """
        Generate directed graph of the circuit, each node has attributes: CC0, CC1, CO, lev
        """
        G = nx.DiGraph()
        for n in self.nodes_lev:
            n_num_normal = self.node_ids.index(n.num) #TODO: efficient search using dict
            G.add_node(n_num_normal)
            G.nodes[n_num_normal]['lev'] = n.lev
            G.nodes[n_num_normal]['gtype'] = n.gtype
            G.nodes[n_num_normal]['ntype'] = n.ntype
            G.nodes[n_num_normal]['CC0'] = n.CC0
            G.nodes[n_num_normal]['CC1'] = n.CC1
            G.nodes[n_num_normal]['CO'] = n.CO
            G.nodes[n_num_normal]['C0'] = n.C0
            G.nodes[n_num_normal]['C1'] = n.C1
            G.nodes[n_num_normal]['S'] = n.S
            G.nodes[n_num_normal]['B0'] = n.B0
            G.nodes[n_num_normal]['B1'] = n.B1
            G.nodes[n_num_normal]['D0_p'] = n.D0_p
            G.nodes[n_num_normal]['D1_p'] = n.D1_p
            G.nodes[n_num_normal]['D_p'] = n.D0_p + n.D1_p
            if n.gtype != 'IPT':
                for unode in n.unodes:
                    G.add_edge(self.node_ids.index(unode.num), n_num_normal)
            else:
                pass
        return G

    def get_node_attr(self, node_attr):
        data = []
        for node in self.nodes_lev:
            data.append(getattr(node, node_attr))

        return data

    def get_hist(self, node_attr, plot=False, fname=None):
        plt.clf()
        data = self.get_node_attr(node_attr)
        res = plt.hist(data)
        plt.title(self.c_name)
        plt.xlabel(node_attr)
        plt.ylabel("Occurrence")
        if plot:
            plt.show()
        else:
            fname = self.c_name + "_" + node_attr + ".png" if fname==None else fname
            plt.savefig(fname)

# prevent D algorithm deadlock. For debug purposes only
class Imply_counter:
    def __init__(self, abort_cnt):
        self.cnt = 0
        self.abort_cnt = abort_cnt
    def increment(self):
        self.cnt += 1
    def initialize(self):
        self.cnt = 0


