from scipy import signal
from scipy.signal import TransferFunction
from math import pi

Tstep_GS = 0.01
Tstep=Tstep_GS

N_dP = 2 #VELOCITY XY
wc_dP = 30*2*pi #rad/s

#[NB_dP,DB_dP] = besself(N_dP,wc_dP)
NB_dP,DB_dP = signal.bessel(N_dP, wc_dP)


# BF_dP = c2d(tf(NB_dP,DB_dP),Tstep,'zoh',wc_dP)
# [NB_dP,DB_dP] = tfdata(BF_dP,'v')
#
# N_dPz = 2 #VELOCITY Z
# wc_dPz = 3*2*pi #rad/s  10
# [NB_dPz,DB_dPz] = besself(N_dPz,wc_dPz)
# BF_dPz = c2d(tf(NB_dPz,DB_dPz),Tstep,'zoh',wc_dPz)
# [NB_dPz,DB_dPz] = tfdata(BF_dPz,'v')
#
# N_dPopti = 2 #VELOCITY OPTITRACK
# wc_dPopti = 10*2*pi #rad/s
# [NB_dPopti,DB_dPopti] = besself(N_dPopti,wc_dPopti)
# BF_dPopti = c2d(tf(NB_dPopti,DB_dPopti),Tstep,'zoh',wc_dPopti)
# [NB_dPopti,DB_dPopti] = tfdata(BF_dPopti,'v')
#
# # REFERENCES LPF
# p = 5
# Gref = c2d(tf(p,[1 p]),Tstep_GS,'zoh')
# [Nref,Dref] = tfdata(Gref,'v')
#
# # STEP LPF
# p = 1
# Gstep = c2d(tf(p,[1 p]),Tstep_GS,'zoh')
# [Nstep,Dstep] = tfdata(Gstep,'v')
#
# # # PLANNER REF LPF
# # p = 6
# # Gref_PLAN = c2d(tf(p,[1 p]),Tstep_GS,'zoh')
# # [Nref_PLAN,Dref_PLAN] = tfdata(Gref_PLAN,'v')
#
# # SMOOTHER LPF
# p = 100 # 20
# Gsmooth = c2d(tf(p,[1 p]),Tstep_GS,'zoh')
# [Nsmooth,Dsmooth] = tfdata(Gsmooth,'v')

