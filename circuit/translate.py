# input file type : .bench
# output file type : .ckt658
# important : the finin parameter is not useable

import re


def translator(src, dst):
    fin = open('../data/bench/' + src, 'r')
    f = fin.readlines()
    fin.close()
    for i in range(len(f)):
        f[i] = f[i].strip()

    input_list = []
    output_list = []
    internal_list = []

    for item in f:
        if item[0] == 'I':
            input_list.append(item)
        if item[0] == 'O':
            output_list.append(item)
        if item[0] == '0' or item[0] == '1'or item[0] == '2'\
        or item[0] == '3'or item[0] == '4'or item[0] == '5'\
        or item[0] == '6'or item[0] == '7'or item[0] == '8'\
        or item[0] == '9':
            internal_list.append(item)

    in_list = set()
    for item in input_list:
        item=item.split('#')
        item=re.findall('[0-9]+',item[0])
        in_list.add(item[0])
    
    out_list = set()
    for item in output_list:
        item=item.split('#')
        item=re.findall('[0-9]+',item[0])
        out_list.add(item[0])

    def gate_index(string):
        out = 0
        if string.upper().find('BUFF') >= 0:
            out=1
        elif string.upper().find('XOR') >= 0:
            out = 2
        elif string.upper().find('NOR') >= 0:
            out = 4
        elif string.upper().find('OR') >= 0:
            out = 3
        elif string.upper().find('NOT') >= 0:
            out = 5
        elif string.upper().find('NAND') >= 0:
            out = 6
        elif string.upper().find('AND') >= 0:
            out = 7
        return out

    ckt_set=list()
    for item in in_list:
        node=[1,item,0,1,0]
        ckt_set.append(node)

    for item in internal_list:
        item=item.split('#')
        item=item[0]
        item=re.findall('[a-z0-9]+',item)
        if(item[0] in out_list):
            if(gate_index(item[1])==1):
                node=[3,item[0],gate_index(item[1]),0,1,item[2]]
            else:
                node=[3,item[0],gate_index(item[1]),1,len(item[2:])]+item[2:]
            out_list.remove(item[0])
        else:
            if(gate_index(item[1])==1):
                node=[2,item[0],1,item[2]]
            else:
                node=[0,item[0],gate_index(item[1]),1,len(item[2:])]+item[2:]
        ckt_set.append(node)
    for item in out_list:
        if(item in in_list):
            node=[3,item,0,0,0]
            ckt_set.append(node)
        else:
            print("error input")
    output_write=[]
    for item in ckt_set:
        item2 = [str(x) for x in item]
        output_str="    ".join(item2)+'\n'
        output_write.append(output_str)
    fv = open('../data/ckt/' + dst, 'w')
    fv.writelines(output_write)
    fv.close()

translator("c2670", "c2670.ckt")
translator("c3540", "c3540.ckt")
translator("c5315", "c5315.ckt")
translator("c7552", "c7552.ckt")

