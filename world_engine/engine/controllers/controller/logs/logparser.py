__author__ = 'Kevin-Patxi'


import matplotlib.pyplot as plt

with open("octrl.log",'r') as f:

    loc_x = []
    loc_y = []
    loc_z = []
    loc_yaw =[]
    loc_pitch =[]
    loc_roll =[]
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
                parts = line.split()
                loc_x.append(float(parts[6].split(':')[1]))
                loc_y.append(float(parts[7].split(':')[1]))
                loc_z.append(float(parts[8].split(':')[1]))
                loc_yaw.append(float(parts[9].split(':')[1]))
                loc_roll.append(float(parts[10].split(':')[1]))
                loc_pitch.append(float(parts[11].split(':')[1]))

            if ("Control Output" in line) &(in_out_toggle):
                in_out_toggle = 0
                parts = line.split(',')

                roll.append(float(parts[0].split('=')[1]))
                pitch.append(float(parts[1].split('=')[1]))
                yaw.append(float(parts[2].split('=')[1]))
                thrust.append(float(parts[3].split('=')[1]))

                i = i+1
    f.close()
    plt.figure(1)
    plt.subplot(211)
    plt.plot(thrust)
    plt.ylabel('thrust')
    plt.subplot(212)
    plt.plot(loc_z)
    plt.axhline(.5)
    plt.ylabel('Real Z')

    plt.figure(2)
    plt.subplot(211)
    plt.plot(roll)
    plt.ylabel('roll')
    plt.subplot(212)
    plt.plot(loc_roll)
    plt.axhline(0)
    plt.ylabel('real roll')


    plt.figure(3)
    plt.subplot(211)
    plt.plot(pitch)
    plt.ylabel('pitch')
    plt.subplot(212)
    plt.plot(loc_pitch)
    plt.ylabel('real pitch')


    plt.figure(4)
    plt.subplot(211)
    plt.plot(yaw)
    plt.ylabel('yaw')
    plt.subplot(212)
    plt.plot(loc_yaw)
    plt.axhline(0)
    plt.ylabel('real yaw')


    plt.figure(5)
    plt.plot(loc_x[-2000:],loc_y[-2000:])
    plt.axhline(0)
    plt.axvline(0)
    plt.ylabel('Y')
    plt.xlabel('X')


    plt.show()


    print i





