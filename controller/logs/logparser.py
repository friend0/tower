__author__ = 'Kevin-Patxi'


import matplotlib.pyplot as plt

with open("octrl.log",'r') as f:

    loc_x =[]
    loc_y = []
    loc_z = []
    roll= []
    pitch = []
    yaw = []
    thrust = []
    in_out_toggle = 0
    i=0

    for line in f:
        if "DEBUG" in line:
            if ("Processed State" in line)&(not(in_out_toggle)):
                in_out_toggle = 1
                print line


            if ("Control Output" in line) &(in_out_toggle):
                in_out_toggle = 0
                parts = line.split(':,')

                print
                i = i+1
    f.close()
    print i





