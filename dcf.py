'''
    A simple implementation of the discrete correlation function (DCF)

    Usage:
      $ python dcf.py -h for help and basic instruction

'''

import numpy as np

'''
    Subroutines
'''

def lndtrnd(ts, vrbs, plyft): 
    if plyft == 0:
        ts_mean = np.mean(ts[:,1])
        ts[:,1] = ts[:,1] - ts_mean
        if vrbs:
            print "Mean subtraction: %.4e" %ts_mean
    elif plyft == 1:
        from scipy.optimize import curve_fit
        lnfnc = lambda x, a, b: a*x + b
        p0, c0 = curve_fit(lnfnc, ts[:,0], ts[:,1], sigma=ts[:,2])
        ts[:,1] = ts[:,1] - lnfnc(ts[:,0], p0[0], p0[1])
        if vrbs:
            print "Linear De-trend Coefficients"
            print "a:", p0[0]
            print "b:", p0[1]
    else:
        from scipy.optimize import curve_fit
        lnfnc = lambda x, a, b, c: a*x**2.0 + b*x + c
        p0, c0 = curve_fit(lnfnc, ts[:,0], ts[:,1], sigma=ts[:,2])
        ts[:,1] = ts[:,1] - lnfnc(ts[:,0], p0[0], p0[1], p0[2])
        if vrbs:
            print "Quadratic De-trend Coefficients"
            print "a:", p0[0]
            print "b:", p0[1]
            print "c:", p0[2]
    return ts

def set_unitytime(ts1, ts2):
    unitytime = min(np.min(ts1[:,0]), np.min(ts2[:,0]))
    ts1[:,0] = ts1[:,0] - unitytime
    ts2[:,0] = ts2[:,0] - unitytime
    return ts1, ts2

def get_timeseries(infile1, infile2, vrbs, plyft):
    ts1 = np.loadtxt(infile1, comments='!')
    ts2 = np.loadtxt(infile2, comments='!')
    ts1, ts2 = set_unitytime(ts1, ts2)
    ts1 = lndtrnd(ts1, vrbs, plyft)
    ts2 = lndtrnd(ts2, vrbs, plyft)
    return ts1, ts2

def sdcf(ts1, ts2, t, dt):
    dcf = np.zeros(t.shape[0])
    dcferr = np.zeros(t.shape[0])
    n = np.zeros(t.shape[0])

    dst = np.empty((ts1.shape[0], ts2.shape[0]))
    for i in range(ts1.shape[0]):
        for j in range(ts2.shape[0]):
            dst[i,j] = ts2[j,0] - ts1[i,0]

    for k in range(t.shape[0]):
        tlo = t[k] - dt/2.0
        thi = t[k] + dt/2.0
        ts1idx, ts2idx = np.where((dst <= thi) & (dst >= tlo))

        mts2 = np.mean(ts2[ts2idx,1])
        mts1 = np.mean(ts1[ts1idx,1])
        n[k] = ts1idx.shape[0]

        dcfdnm = np.sqrt((np.var(ts1[ts1idx,1]) - np.mean(ts1[ts1idx,2])**2) \
                         * (np.var(ts2[ts2idx,1]) - np.mean(ts2[ts2idx,2])**2))

        dcfs = (ts2[ts2idx,1] - mts2) * (ts1[ts1idx,1] - mts1) / dcfdnm

        dcf[k] = np.sum(dcfs) / float(n[k])
        dcferr[k] = np.sqrt(np.sum((dcfs - dcf[k])**2)) / float(n[k] - 1)
    return dcf, dcferr

def gdcf(ts1, ts2, t, dt):
    h = dt/4.0
    gkrn = lambda x: np.exp(-1.0 * np.abs(x)**2 / (2.0 * h**2)) \
           / np.sqrt(2.0 * np.pi * h)
    cntrbt = gkrn(3.290527*h)

    dcf = np.zeros(t.shape[0])
    dcferr = np.zeros(t.shape[0])
    n = np.zeros(t.shape[0])

    dst = np.empty((ts1.shape[0], ts2.shape[0]))
    #n = ts1.shape[0] * ts2.shape[0]
    for i in range(ts1.shape[0]):
        for j in range(ts2.shape[0]):
            dst[i,j] = ts2[j,0] - ts1[i,0]

    for k in range(t.shape[0]):
        gdst = gkrn(dst - t[k])
        ts1idx, ts2idx = np.where(gdst >= cntrbt)

        mts2 = np.mean(ts2[ts2idx,1])
        mts1 = np.mean(ts1[ts1idx,1])
        n[k] = ts1idx.shape[0]

        dcfdnm = np.sqrt((np.var(ts1[ts1idx,1]) - np.mean(ts1[ts1idx,2])**2) \
                         * (np.var(ts2[ts2idx,1]) - np.mean(ts2[ts2idx,2])**2))

        dcfs = (ts2[ts2idx,1] - mts2) * (ts1[ts1idx,1] - mts1) / dcfdnm
        dcf[k] = np.sum(dcfs) / float(n[k])
        dcferr[k] = np.sqrt(np.sum((dcfs - dcf[k])**2)) / float(n[k] - 1)
    return dcf, dcferr

'''
    MAIN
'''

import argparse

INPUT = argparse.ArgumentParser(description='DCF USER PARAMETERS')

'''
    USER PARAMETER INPUT
    STANDARD PARAMETERS (REQUIRED):
        time_series1.dat - path/filename
        time_series2.dat - path/filename
        lag_range_low    - float
        lag_range_high   - float
        lag_bin_width    - float
'''

INPUT.add_argument('infile1', metavar='time_series1', type=file, nargs=1,
                   help='Time Series 1')
INPUT.add_argument('infile2', metavar='time_series2', type=file, nargs=1,
                   help='Time Series 2')
INPUT.add_argument('lgl', metavar='lag_range_low', type=float, nargs=1,
                   help='Lag range low')
INPUT.add_argument('lgh', metavar='lag_range_high', type=float, nargs=1,
                   help='Lag range high')
INPUT.add_argument('dt', metavar='lag_bin_width', type=float, nargs=1,
                   help='Width of lag bin, dt')

'''
    USER PARAMETER INPUT
    OPTIONAL PARAMETERS:
        weight   = 'slot' or 'gauss'
        polyfit  = 0, 1, 2
        plot     = True or False
        verbose  = True or False
'''

INPUT.add_argument('-w', '--weight', metavar='weight', type=str, nargs=1,
                   default=['slot'], choices=['slot', 'gauss'],
                   required=False, help='Lag bin weighting scheme')
INPUT.add_argument('-p', '--polyfit', metavar='polyfit', type=int, nargs=1,
                   default=[0], choices=[0, 1, 2],
                   required=False, help='Polynomial fit subtraction')
INPUT.add_argument('-np', '--no-plot', dest='noplot', action='store_false',
                   help='Show plot?')
INPUT.add_argument('-v', '--verbose', dest='verbose', action='store_true', 
                   help='Show all steps')

OPTS = INPUT.parse_args()

'''
    USER PARAMETER CHECK AND READOUT
    This section will fail if:
        Parameters 'lag_range_low' and 'lag_range_high' are not symmetric
            about zero, ie: |lag_range_low| == |lag_range_high|
        Parameter 'lag_range_low' is greater than 'lag_range_high'.

    **PITFALL**
        There is no check to make sure the user enters a sensible
        number of lag bins. See README for more details.
'''

#assert abs(OPTS.lgl[0]) == abs(OPTS.lgh[0]), "INPUT ERROR - LAG RANGE"
assert OPTS.lgl[0] < OPTS.lgh[0], "INPUT ERROR - LAG RANGE"

if OPTS.verbose:
    print "\nPYTHON SCRIPT: dcf"
    print
    print "INPUT TIMESERIES 1:", OPTS.infile1[0]
    print "INPUT TIMESERIES 2:", OPTS.infile2[0]
    print "LAG RANGE PROBED  :", OPTS.lgl[0], " : ", OPTS.lgh[0]
    print "LAG BIN WIDTH     :", OPTS.dt[0]

'''
    TIME SERIES PREPARATION
    This section subtracts a n'th order polynomial from both input time series
    prior to the DCF. The user may choose:
        0'th order polynomial - subtracting the mean or zeroing the data.
        1'st order polynomial - subtracting a linear fit
        2'nd order polynomial - subtracting a quadratic fit
    The default setting is subtracting a 0'th order polynomial (the mean). This
    simply zeros the data and doesn't change any intrinsic qualities.

    **PITFALL**
        Just because you can subtract a n'th order polynomial doesn't mean you 
        should. The program doesn't monitor or tell you a subtraction is
        harmful or unnecessary. If you don't know why you are subtracting a
        1'st or 2'nd order polynomial, don't, leave the default subtraction in
        place. Go research non-stationary time series and filtering low
        frequency noise before trying again.

    **PITFALL 2**
        If you have subtracted your own fits from the time series, leave the
        default setting, 0, as is. It won't change your data.
'''
if OPTS.verbose:
    print "\nTime series preparation"
TS1, TS2 = get_timeseries(OPTS.infile1[0], OPTS.infile2[0], OPTS.verbose, \
                          OPTS.polyfit[0])

'''
    DCF
    This section earns the paycheck for the entire program - runs the DCF
    algorithm. The user main choose the rectangular 'slot' weighting or 
    the gaussian 'gauss' weighting. See README for details on pair weighting.

    The regular weighting scheme is the 'slot' and also default. If you are
    unsure why you might pick 'gauss' - don't.
'''

DT = OPTS.dt[0]
N = np.around((OPTS.lgh[0] - OPTS.lgl[0]) / float(DT))
T = np.linspace(OPTS.lgl[0]+(DT/2.0), OPTS.lgh[0]-(DT/2.0), N)

if OPTS.weight[0] == 'slot':
    if OPTS.verbose:
        print "\nDCF INITIATED USING SLOT WEIGHTING"
    DCF, DCFERR = sdcf(TS1, TS2, T, DT)
else:
    if OPTS.verbose:
        print "\nDCF INITIATED USING GAUSSIAN WEIGHTING"
    DCF, DCFERR = gdcf(TS1, TS2, T, DT)

if OPTS.verbose:
    print "DCF COMPLETE"

'''
    PLOT RESULTS
    No brainer - plots the results if the user wishes with -pl=True on the
    command line.

    For plot to function the python module matplotlib must be installed.
'''

if OPTS.noplot:
    import matplotlib.pyplot as plt
    plt.figure(0)
    plt.errorbar(T, DCF, DCFERR, color='k', ls='-', capsize=0) 
    plt.xlim(OPTS.lgl[0], OPTS.lgh[0])
    plt.show()
