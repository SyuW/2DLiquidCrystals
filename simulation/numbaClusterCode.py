import numpy as np
from numpy.linalg.linalg import norm
import numpy.random as rd

from math import trunc
from numba import jit
from operator import itemgetter

import argparse
import math
import os
import pickle
import sys



def dist(x1, y1, x2, y2):
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def atan2(x, y):
    if x > 0:
        val = np.arctan(y / x)
    elif x < 0 and y >= 0:
        val = np.arctan(y / x) + np.pi
    elif x < 0 and y < 0:
        val = np.arctan(y / x) - np.pi
    elif x == 0 and y > 0:
        val = np.pi / 2
    elif x == 0 and y < 0:
        val = np.pi / 2

    return val


#@jit(cache=True)
def overlap_Ellipse(x1, y1, theta1, x2, y2, theta2, a, b):
    k = b / a
    xi = (k ** 2 - 1) / (k ** 2 + 1)
    w = 2 * a
    r_val = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    r_vec = np.array([(x2 - x1) / r_val, (y2 - y1) / r_val])

    u1 = np.array([np.cos(theta1), np.sin(theta1)])
    u2 = np.array([np.cos(theta2), np.sin(theta2)])

    r_dot_u1 = np.dot(r_vec, u1)

    r_dot_u2 = np.dot(r_vec, u2)

    # u1_dot_u2 = np.cos(theta_2_prime)

    u1_dot_u2 = np.dot(u1, u2)

    denom = (1 - 0.5 * xi * (((r_dot_u1 + r_dot_u2) ** 2 / (1 + xi * u1_dot_u2)) + (
                (r_dot_u1 - r_dot_u2) ** 2 / (1 - xi * u1_dot_u2)))) ** (0.5)

    sigma_2D = w / denom

    if r_val >= sigma_2D:
        val = False
    else:
        val = True

        # print('sigma: ',sigma_2D,' r dist: ',r_dist,' xi: ',xi,' u1: ',u1, ' u2: ', u2, ' r vec: ',r)

    return val


#@jit(cache=True)
def overlap_Ellipse2(x1, y1, theta1, x2, y2, theta2, a, b):
    k = b / a
    xi = (k ** 2 - 1) / (k ** 2 + 1)
    w = 2 * a
    r_val = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    r_vec = np.array([(x2 - x1) / r_val, (y2 - y1) / r_val])

    u1 = np.array([np.cos(theta1), np.sin(theta1)])
    u2 = np.array([np.cos(theta2), np.sin(theta2)])

    r_dot_u1 = np.dot(r_vec, u1)

    r_dot_u2 = np.dot(r_vec, u2)

    # u1_dot_u2 = np.cos(theta_2_prime)

    u1_dot_u2 = np.dot(u1, u2)

    denom = (1 - 0.5 * xi * (((r_dot_u1 + r_dot_u2) ** 2 / (1 + xi * u1_dot_u2)) + (
                (r_dot_u1 - r_dot_u2) ** 2 / (1 - xi * u1_dot_u2)))) ** (0.5)

    sigma_2D = w / denom

    # sigma_2D = contact(theta_r,phi,xi,w)

    return sigma_2D


#@jit(cache=True)
def GeometricPotential(x1, y1, theta1, x2, y2, theta2, LongAxis1, ShortAxis1, LongAxis2, ShortAxis2):
    small = 10 ** (-14)

    k1 = [np.cos(theta1), np.sin(theta1)]
    k2 = [np.cos(theta2), np.sin(theta2)]

    k1k1_dyad = [[np.cos(theta1) ** 2, np.sin(theta1) * np.cos(theta1)],
                 [np.sin(theta1) * np.cos(theta1), np.sin(theta1) ** 2]]
    k2k2_dyad = [[np.cos(theta2) ** 2, np.sin(theta2) * np.cos(theta2)],
                 [np.sin(theta2) * np.cos(theta2), np.sin(theta2) ** 2]]
    identity = [[1, 0], [0, 1]]

    e1 = np.sqrt(1 - (ShortAxis1 / LongAxis1) ** 2)
    e2 = np.sqrt(1 - (ShortAxis2 / LongAxis2) ** 2)

    eta = (LongAxis1 / ShortAxis1) - 1

    a_prime1 = (ShortAxis1 / ShortAxis2) ** 2 * np.add(np.array(identity), (eta * np.array(k1k1_dyad)))
    a_prime2 = np.add(np.array(identity), (-1) * (e2 ** 2) * np.array(k2k2_dyad))
    a_prime3 = np.add(np.array(identity), eta * np.array(k1k1_dyad))

    A_prime = np.matmul(np.matmul(np.array(a_prime1), np.array(a_prime2)), np.array(a_prime3))

    eigenVal, eigenVec = np.linalg.eig(A_prime)

    if eigenVal[0] > eigenVal[1]:
        LongAxis2_prime = 1 / (np.sqrt(eigenVal[1]))
        k_minus = eigenVec[:, 1]
        ShortAxis2_prime = 1 / (np.sqrt(eigenVal[0]))
        k_plus = eigenVec[:, 0]
    else:
        LongAxis2_prime = 1 / (np.sqrt(eigenVal[0]))
        k_minus = eigenVec[:, 0]
        ShortAxis2_prime = 1 / (np.sqrt(eigenVal[1]))
        k_plus = eigenVec[:, 1]

    d_hat = (1 / np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)) * np.array([x1 - x2, y1 - y2])

    d_hat_prime = (1 / (np.sqrt(1 - (e1 ** 2) * (np.dot(np.array(k1), d_hat)) ** 2))) * np.add(d_hat, (
                ShortAxis1 / LongAxis1 - 1) * (np.dot(np.array(k1), d_hat)) * np.array(k1))

    sinPhi = np.dot(k_minus, d_hat_prime)
    cosPhi = np.dot(k_plus, d_hat_prime)

    delta = (LongAxis2_prime / ShortAxis2_prime) ** 2 - 1

    if np.abs(cosPhi) < small:

        d_prime = 1 + LongAxis2_prime
    else:
        tanPhiSq = (sinPhi / cosPhi) ** 2

        A = (-1 / (ShortAxis2_prime ** 2)) * (1 + tanPhiSq)
        B = (-2 / ShortAxis2_prime) * (1 + tanPhiSq + delta)
        C = -tanPhiSq - (1 + delta) ** 2 + (1 / (ShortAxis2_prime ** 2)) * (1 + tanPhiSq * (1 + delta))
        D = (2 / ShortAxis2_prime) * (1 + tanPhiSq) * (1 + delta)
        E = (1 + tanPhiSq + delta) * (1 + delta)

        alpha = -(3 * B ** 2) / (8 * A ** 2) + C / A
        beta = B ** 3 / (8 * A ** 3) - (B * C) / (2 * A ** 2) + D / A
        gamma = -3 * B ** 4 / (256 * A ** 4) + (C * B ** 2) / (16 * A ** 3) - (B * D) / (4 * A ** 2) + (E / A)

        settings = np.seterr(divide='raise')

        P = - (alpha ** 2 / 12) - gamma
        Q = - (alpha ** 3 / 108) + (alpha * gamma / 3) - (beta ** 2 / 8)
        U = (-Q / 2 + np.sqrt((Q ** 2 / 4) + (P ** 3 / 27))) ** (1 / 3)

        if np.abs(U) < small or math.isnan(U) == True:
            y = -(5 * alpha / 6) - (Q ** (1 / 3))
        else:
            y = -(5 * alpha / 6) + U - P / (3 * U)

        q = -(B / (4 * A)) + (1 / 2) * (
                    np.sqrt(alpha + 2 * y) + np.sqrt(-(3 * alpha + 2 * y + (2 * beta / (np.sqrt(alpha + 2 * y))))))

        d_prime = np.sqrt(
            ((q ** 2 - 1) / delta) * (1 + (ShortAxis2_prime * (1 + delta) / q)) ** 2 + (1 - ((q ** 2 - 1) / delta)) * (
                        1 + ShortAxis2_prime / q) ** 2)

        d = d_prime * ShortAxis1 / (np.sqrt(1 - (e1 ** 2) * (np.dot(k1, d_hat) ** 2)))

    return d


#@jit(cache=True)
def HardBoundaryCircle_Disc(R, shortAxis, longAxis, xc, yc, theta):
    overlap = False

    cos = np.cos(theta)
    sin = np.sin(theta)
    sin2 = np.sin(2 * theta)

    A = longAxis ** 2 + xc ** 2 + yc ** 2 - 2 * longAxis * (xc * cos + yc * sin) - R ** 2
    B = 4 * shortAxis * (yc * cos - xc * cos)
    C = 4 * (shortAxis ** 2) - 2 * (longAxis ** 2) + 2 * (xc ** 2) + 2 * (yc ** 2) - 2 * (R ** 2)
    D = 4 * shortAxis * (yc * cos - xc * cos)
    E = longAxis ** 2 + 2 * longAxis * (xc * cos + yc * sin) + xc ** 2 + yc ** 2 - R ** 2

    delta = (256 * (A * E) ** 3
             - 192 * (B * D) * (A * E) ** 2
             - 128 * (A * C * E) ** 2
             + 144 * (C * E) * (A * D) ** 2
             - 27 * (A ** 2) * (D ** 4)
             + 144 * (A * C) * (B * E) ** 2
             - 80 * (A * B * D * E) * (C) ** 2
             + 18 * (A * B * C) * (D ** 3)
             + 16 * (A * E) * (C ** 4)
             - 4 * A * (C ** 3) * (D ** 2)
             - 27 * (E ** 2) * (B ** 4)
             + 18 * (C * D * E) * (B ** 3)
             - 4 * (B * D) ** 3
             - 4 * E * (B ** 2) * (C ** 3)
             + (B ** 2) * (C ** 2) * (D ** 2)
             )

    P = 8 * A * C - 3 * (B ** 2)
    R_d = B ** 3 + 8 * D * (A ** 2) - 4 * A * B * C
    delta_0 = C ** 2 - 3 * B * D + 12 * A * E
    D_d = 64 * (A ** 3) * E - 16 * (A ** 2) * (C ** 2) + 16 * A * (B ** 2) * C - 16 * (A ** 2) * B * D - 3 * (B ** 4)

    if delta < 0:
        overlap = True
    elif delta > 0 and (P < 0 and D_d < 0):
        overlap = True
    elif delta == 0:
        if P < 0 and D_d < 0 and delta_0 != 0:
            overlap = True
        elif D_d > 0 or (P > 0 and (D_d != 0 or R_d != 0)):
            overlap = False
        elif delta_0 == 0 and D_d != 0:
            overlap = True
        elif D_d == 0 and P < 0:
            overlap = True
        elif D_d == 0 and P > 0 and R_d == 0:
            overlap = False
        else:
            overlap = False

    return overlap


def init_Circ_H_Gr(n, a, b, R):
    v = np.ceil(R / a)
    h = np.ceil(R / b)

    N = int(v * h)

    xgrid = np.linspace(b - R, (b - R) + (int(h) - 1) * (2 * b), int(h))
    ygrid = np.linspace(a - R, (a - R) + (int(v) - 1) * (2 * a), int(v))
    thetaArray = np.full((N, 1), 0)

    X, Y = np.meshgrid(xgrid, ygrid)

    posArr = np.array([X.flatten(), Y.flatten()]).T

    posArr = np.c_[posArr, thetaArray]
    nDel = 0
    indexDel = []
    incorrect = []

    for p in range(len(posArr)):

        if posArr[p, 0] ** 2 + posArr[p, 1] ** 2 > R ** 2 or (
                HardBoundaryCircle_Disc(R, a, b, posArr[p, 0], posArr[p, 1], posArr[p, 2]) == True):
            indexDel.append(p)
            incorrect.append(posArr[p, :])
            nDel += 1
        else:
            pass

    redE = np.array(incorrect)

    c = 0

    for i in indexDel:
        newArr = np.delete(posArr, i - c, 0)
        posArr = newArr
        c += 1

    #print(len(posArr))
    #print(len(redE))
    newLength = len(posArr)

    if n >= newLength:
        pass
    elif n < newLength:
        d = 0

        while d != newLength - n:
            k = rd.randint(0, newLength - n - d)
            newArr = np.delete(posArr, k, 0)
            posArr = newArr
            d += 1

    #print(len(posArr))

    return [posArr, redE]


def init_Circ_H_Rd(n, l, a, b):
    init_pos = np.zeros((n, 3))

    # Correct overlapping positions
    sortedInitPos = [[i, init_pos[i, 0], init_pos[i, 1], init_pos[i, 2], ] for i in range(n)]

    for x in range(n):

        valid = False
        overlapVar = False

        while valid == False:

            radius = rd.uniform(0, l)
            angle = rd.uniform(0, 2 * np.pi)
            init_pos[x, 0] = radius * np.cos(angle)
            init_pos[x, 1] = radius * np.sin(angle)
            init_pos[x, 2] = rd.uniform(0, 2 * np.pi)

            if (init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2) > ((l - 2 * b) ** 2):
                if (init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2) > (l ** 2) or (
                        init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2) > (l - a) ** 2 or (
                        HardBoundaryCircle_Disc(l, a, b, init_pos[x, 0], init_pos[x, 1], init_pos[x, 2]) == True):
                    print('init - border overlap')
                    continue
                else:

                    for j in range(n):
                        if j != x and (overlap_Ellipse(init_pos[x, 0], init_pos[x, 1], init_pos[x, 2], init_pos[j, 0],
                                                       init_pos[j, 1], init_pos[j, 2], a, b) == True):
                            overlapVar = True
                            print('iter' + str(x) + ' init - particle overlap')
                            break
                        else:
                            print('iter' + str(x) + 'init - no particle overlap')
                            overlapVar = False

                    if overlapVar == True:
                        continue
                    else:
                        valid = True


            else:
                for j in range(n):
                    if j != x and (overlap_Ellipse(init_pos[x, 0], init_pos[x, 1], init_pos[x, 2], init_pos[j, 0],
                                                   init_pos[j, 1], init_pos[j, 2], a, b) == True):
                        overlapVar = True
                        print('iter' + str(x) + ' init - particle overlap')
                        break
                    else:
                        print('iter' + str(x) + 'init - no particle overlap')
                        overlapVar = False

                if overlapVar == True:
                    continue
                else:
                    valid = True

    return init_pos


def init_Ann_H_Gr(n, a, b, R, r):
    """
    Initialize grid state using grid method
    
    :param: n - number of particles
    :param: a - short axis length
    :param: b - long axis length
    :param: R - outer radius
    :param: r - inner radius
    """
    v = np.ceil(R / a)
    h = np.ceil(R / b)

    N = int(v * h)

    xgrid = np.linspace(b - R, (b - R) + (int(h) - 1) * (2 * b), int(h))
    ygrid = np.linspace(a - R, (a - R) + (int(v) - 1) * (2 * a), int(v))
    thetaArray = np.full((N, 1), 0)

    X, Y = np.meshgrid(xgrid, ygrid)

    posArr = np.array([X.flatten(), Y.flatten()]).T

    posArr = np.c_[posArr, thetaArray]
    nDel = 0
    indexDel = []
    incorrect = []

    for p in range(len(posArr)):

        if posArr[p, 0] ** 2 + posArr[p, 1] ** 2 > R ** 2 or posArr[p, 0] ** 2 + posArr[p, 1] ** 2 < r ** 2 or (
                HardBoundaryCircle_Disc(R, a, b, posArr[p, 0], posArr[p, 1], posArr[p, 2]) == True) or (
                HardBoundaryCircle_Disc(r, a, b, posArr[p, 0], posArr[p, 1], posArr[p, 2]) == True):
            indexDel.append(p)
            incorrect.append(posArr[p, :])
            nDel += 1
        else:
            pass

    redE = np.array(incorrect)

    c = 0

    for i in indexDel:
        newArr = np.delete(posArr, i - c, 0)
        posArr = newArr
        c += 1

    print(len(posArr))
    print(len(redE))
    newLength = len(posArr)

    if n >= newLength:
        pass
    elif n < newLength:
        d = 0

        while d != newLength - n:
            k = rd.randint(0, newLength - n - d)
            newArr = np.delete(posArr, k, 0)
            posArr = newArr
            d += 1

    print(len(posArr))

    return [posArr, redE]


def init_Ann_H_GrC(n, a, b, R, r, d, e):
    """
    Initialize grid state using grid chord method
    
    :param: n - number of particles
    :param: a - semi-minor axis
    :param: b - semi-major axis
    :param: r - inner radius
    :param: R - outer radius
    :param: d - y shift
    :param: e - x shift
    """
    
    ## When an exact contact distance method is reliable use that instead of xStar

    a_tilde = a * (1 + (d / 100))
    b_tilde = b + a * ((e / 100))

    Nv1 = int(np.floor(r / a_tilde))

    if Nv1 % 2 == 0:
        ygrid1 = np.linspace(-(Nv1 * a_tilde), Nv1 * a_tilde, Nv1)

    else:
        ygrid1 = np.linspace(-a_tilde * (Nv1 - 1), (Nv1 - 1) * a_tilde, Nv1)

    diffArray = []
    totalN = 0
    for k in range(Nv1):
        xStar = np.sqrt(r ** 2 - (ygrid1[k]) ** 2)
        diff = R - xStar
        Nh1 = 2 * int(np.floor(diff / (2 * b_tilde)))
        diffArray.append([xStar, Nh1])
        totalN += Nh1

    initalizedArray = np.zeros((1, 3))
    corrected = False
    countVar = 0
    for w in range(len(diffArray)):

        if diffArray[w][1] != 0:

            if diffArray[w][1] > 1:
                right = np.array(
                    [((2 * (s + 1) - 1) * b_tilde + diffArray[w][0]) for s in range(int(diffArray[w][1] / 2))])
                left = -1 * right
                xVal = np.concatenate((right, left), axis=0)
            else:
                xVal = np.array((diffArray[w][0] + b_tilde))

            # xVal=np.linspace(-chordArray[w][0]+b_tilde,chordArray[w][0]-b_tilde,chordArray[w][1])
            for vals in xVal:
                interimArray = np.append(initalizedArray, [[vals, ygrid1[w], 0]], axis=0)
                initalizedArray = interimArray
        else:
            pass

    Nv2_half = int(np.floor((R - r) / (2 * a_tilde)))

    if Nv2_half != 0:

        up = np.linspace(r + 2 * a_tilde, r + (2 * Nv2_half) * a_tilde, Nv2_half)
        down = -1 * up
        ygrid2 = np.concatenate((up, down), axis=0)

        chordArray = []
        for k in range(2 * Nv2_half):
            chord = np.sqrt(R ** 2 - (ygrid2[k]) ** 2)
            NC = int(np.floor(2 * chord / (2 * b_tilde)))
            chordArray.append([chord, NC])
            totalN += NC

        corrected = False
        countVar = 0
        for w in range(len(chordArray)):

            if chordArray[w][1] != 0:

                if chordArray[w][1] > 1:
                    if chordArray[w][1] % 2 == 0:
                        right = np.array([((2 * (s + 1) - 1) * b_tilde) for s in range(int(chordArray[w][1] / 2))])
                        left = -1 * right
                        xVal = np.concatenate((right, left), axis=0)
                    else:
                        right = np.array([((2 * (s + 1)) * b_tilde) for s in range(int(chordArray[w][1] / 2))])
                        left = -1 * right
                        xVal = np.concatenate((right, left), axis=0)
                        interimX = np.append(xVal, [0], axis=0)
                        xVal = interimX
                else:
                    xVal = np.array([0])

                # xVal=np.linspace(-chordArray[w][0]+b_tilde,chordArray[w][0]-b_tilde,chordArray[w][1])
                for vals in xVal:
                    interimArray = np.append(initalizedArray, [[vals, ygrid2[w], 0]], axis=0)
                    initalizedArray = interimArray
            else:
                pass

    posArr = np.delete(initalizedArray, 0, 0)

    nDel = 0
    indexDel = []
    incorrect = []
    """
    for p in range(len(posArr)):
        
        if posArr[p,0]**2 + posArr[p,1]**2 > R**2 or (HardBoundaryCircle_Disc(R,a,b,posArr[p,0],posArr[p,1],posArr[p,2])==True) :
            indexDel.append(p)
            incorrect.append(posArr[p,:])
            nDel+=1
        else:       
            pass
    
    """
    redE = np.array(incorrect)

    c = 0

    for i in indexDel:
        newArr = np.delete(posArr, i - c, 0)
        posArr = newArr
        c += 1

    #print(len(posArr))
    #print(len(redE))
    newLength = len(posArr)

    if n >= newLength:
        pass
    elif n < newLength:
        de = 0

        while de != newLength - n:
            k = rd.randint(0, newLength - n - de)
            newArr = np.delete(posArr, k, 0)
            posArr = newArr
            de += 1

    #print(len(posArr))

    return [posArr, redE]


def init_Ann_H_Rd(n, l, r2, a, b):
    """
    Random initialization of particle positions for hard annular BCs
    
    :param: n
    :param: l
    :param: r2
    :param: a
    :param: b
    """
    
    # FIX 0.2

    init_pos = np.zeros((n, 3))

    # Correct overlapping positions
    sortedInitPos = [[i, init_pos[i, 0], init_pos[i, 1], init_pos[i, 2], ] for i in range(n)]

    for x in range(n):

        valid = False
        overlapVar = False

        while valid == False:

            radius = rd.uniform(r2, l)
            angle = rd.uniform(0, 2 * np.pi)
            init_pos[x, 0] = radius * np.cos(angle)
            init_pos[x, 1] = radius * np.sin(angle)
            init_pos[x, 2] = rd.uniform(0, 2 * np.pi)

            if (init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2) > ((l - b) ** 2) or (
                    init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2) < ((r2 + b) ** 2):

                if (init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2) > (l - a) ** 2 or (
                        HardBoundaryCircle_Disc(l - 0.2, a, b, init_pos[x, 0], init_pos[x, 1], init_pos[x, 2]) == True):
                    # print('init - border overlap')
                    continue
                elif (init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2) < ((r2 + a) ** 2) or (
                        GeometricPotential(init_pos[x, 0], init_pos[x, 1], init_pos[x, 2], 0, 0, 0, b, a, r2,
                                           r2) > np.sqrt(init_pos[x, 0] ** 2 + init_pos[x, 1] ** 2)):
                    # print('init - border overlap')
                    continue
                else:
                    pass

                for j in range(n):
                    if j != x and (overlap_Ellipse(init_pos[x, 0], init_pos[x, 1], init_pos[x, 2], init_pos[j, 0],
                                                   init_pos[j, 1], init_pos[j, 2], a, b) == True):
                        overlapVar = True
                        # print('iter' + str(x)+' init - particle overlap')
                        break
                    else:
                        # print('iter' + str(x)+'init - no particle overlap')
                        overlapVar = False

                if overlapVar == True:
                    continue
                else:
                    valid = True


            else:
                for j in range(n):
                    if j != x and (overlap_Ellipse(init_pos[x, 0], init_pos[x, 1], init_pos[x, 2], init_pos[j, 0],
                                                   init_pos[j, 1], init_pos[j, 2], a, b) == True):
                        overlapVar = True
                        # print('iter' + str(x)+' init - particle overlap')
                        break
                    else:
                        # print('iter' + str(x)+'init - no particle overlap')
                        overlapVar = False

                if overlapVar == True:
                    continue
                else:
                    valid = True

    return init_pos


## -- Grid state based on Chord instead of lattice grid

def init_Circ_H_GrC(n, a, b, R, d, e):
    """
    Initialize the grid state using a Chord method
    
    :param: n - number of particles
    :param: a - length of short axis
    :param: b - length of long axis
    :param: R - radius of outer boundary
    :param: d - 
    :param: e - 
    """
    
    a_tilde = a * (1 + (d / 100))
    b_tilde = b + a * ((e / 100))

    v = int(np.floor(R / a_tilde))

    if v % 2 == 0:
        ygrid = np.linspace(-(v * a_tilde), v * a_tilde, v)

    else:
        ygrid = np.linspace(-a_tilde * (v - 1), (v - 1) * a_tilde, v)

    chordArray = []
    totalN = 0
    for k in range(v):
        chord = np.sqrt(R ** 2 - (ygrid[k]) ** 2)
        NC = int(np.floor(2 * chord / (2 * b_tilde)))
        chordArray.append([chord, NC])
        totalN += NC

    initalizedArray = np.zeros((1, 3))
    corrected = False
    countVar = 0
    for w in range(len(chordArray)):

        if chordArray[w][1] != 0:

            if chordArray[w][1] > 1:
                if chordArray[w][1] % 2 == 0:
                    right = np.array([((2 * (s + 1) - 1) * b_tilde) for s in range(int(chordArray[w][1] / 2))])
                    left = -1 * right
                    xVal = np.concatenate((right, left), axis=0)
                else:
                    right = np.array([((2 * (s + 1)) * b_tilde) for s in range(int(chordArray[w][1] / 2))])
                    left = -1 * right
                    xVal = np.concatenate((right, left), axis=0)
                    interimX = np.append(xVal, [0], axis=0)
                    xVal = interimX
            else:
                xVal = np.array([0])

            # xVal=np.linspace(-chordArray[w][0]+b_tilde,chordArray[w][0]-b_tilde,chordArray[w][1])
            for vals in xVal:
                interimArray = np.append(initalizedArray, [[vals, ygrid[w], 0]], axis=0)
                initalizedArray = interimArray
        else:
            pass

    posArr = np.delete(initalizedArray, 0, 0)

    nDel = 0
    indexDel = []
    incorrect = []
    """
    for p in range(len(posArr)):
        
        if posArr[p,0]**2 + posArr[p,1]**2 > R**2 or (HardBoundaryCircle_Disc(R,a,b,posArr[p,0],posArr[p,1],posArr[p,2])==True) :
            indexDel.append(p)
            incorrect.append(posArr[p,:])
            nDel+=1
        else:       
            pass
    
    """
    redE = np.array(incorrect)

    c = 0

    for i in indexDel:
        newArr = np.delete(posArr, i - c, 0)
        posArr = newArr
        c += 1

    #print(len(posArr))
    #print(len(redE))
    newLength = len(posArr)

    if n >= newLength:
        pass
    elif n < newLength:
        de = 0

        while de != newLength - n:
            k = rd.randint(0, newLength - n - de)
            newArr = np.delete(posArr, k, 0)
            posArr = newArr
            de += 1

    #print(len(posArr))

    return [posArr, redE]


#@jit()
def MC_Ann_Hard(PosArray, d_pos, d_ang, steps, R, r, a, b, save_every, out_dir=os.getcwd()):
    """
    Run Monte Carlo simulation with hard BCs for annular geometry
    
    :param: PosArray - array of positions
    :param: d_pos - magnitude of positional shift
    :param: d_ang - magnitude of angular shift
    :param: steps - total number of steps in simulation
    :param: R - outer radius of annular confinement
    :param: r - inner radius of annular confinement
    :param: a - length of short axis
    :param: b - length of long axis
    :param: save_every - number of every MC steps to save snapshot
    """

    moves = 0
    accepted_moves = 0
    numE = len(PosArray)
    kVal = b / a

    main_folder_name = os.path.join(out_dir, 'annulus_R{}_r{}_n_{}_k_{}_HardBC'.format(R, r, numE, kVal))
    
    # make the directory to save results at
    if os.path.exists(main_folder_name):
        pass
    else:
        os.makedirs(main_folder_name)
        
    # pickle the simulation parameters to be used by other code (e.g. plotting)
    var_fname = os.path.join(main_folder_name, "params.pickle")
    pickled_vars = {"b":b, "a":a, "r":r, "R":R, "total_steps":steps, "current_step":0, "save_every":save_every}
    with open(var_fname, "wb") as f:
        pickle.dump(pickled_vars, f)
  
    # save the initial state
    initial_array_name = 'step_0.csv'
    complete_name = os.path.join(main_folder_name, initial_array_name)
    np.savetxt(complete_name, PosArray, delimiter=',')
    
    # total number of particles
    n = len(PosArray)
    
    # minimum positional/angular shift magnitudes
    minPos = .05 * a
    minAng = .025
    
    # counters for move adjusts and plots
    fixCount = 0
    plotCount = 0
    
    # repeat for every Monte Carlo step
    for u in range(steps):
        
        # for every particle
        for w in range(n):
            
            # adjust coordinate shift magnitudes
            if fixCount == (np.ceil(steps / 100)):
                
                fixCount = 0
                
                d_ang_old = d_ang
                d_pos_old = d_pos
                
                # if coordinate shifts are above minimum threshold, adjust to meet acceptance rate
                if d_ang > minAng and d_pos > minPos:
                    if accepted_moves / moves < 0.47:
                        d_ang = 0.9 * d_ang
                        d_pos = 0.9 * d_ang
                    elif accepted_moves / moves < 0.37:
                        d_ang = 0.75 * d_ang
                        d_pos = 0.75 * d_ang
                    elif accepted_moves / moves < 0.27:
                        d_ang = 0.6 * d_ang
                        d_pos = 0.6 * d_ang
                    elif accepted_moves / moves < 0.17:
                        d_ang = 0.35 * d_ang
                        d_pos = 0.35 * d_ang
                    elif accepted_moves / moves < 0.07:
                        d_ang = 0.2 * d_ang
                        d_pos = 0.2 * d_ang
                    elif accepted_moves / moves > 0.57:
                        d_ang = 1.1 * d_ang
                        d_pos = 1.1 * d_ang
                    elif accepted_moves / moves > 0.67:
                        d_ang = 1.35 * d_ang
                        d_pos = 1.35 * d_ang
                    elif accepted_moves / moves > 0.77:
                        d_ang = 1.5 * d_ang
                        d_pos = 1.5 * d_ang
                    elif accepted_moves / moves > 0.87:
                        d_ang = 1.65 * d_ang
                        d_pos = 1.65 * d_ang
                    elif accepted_moves / moves > 0.97:
                        d_ang = 1.8 * d_ang
                        d_pos = 1.8 * d_ang
                
                # else, set them to the minimum values
                else:
                    d_ang = minAng
                    d_pos = minPos
                
                msg = (f"Monte Carlo step [{u}/{steps}], Monte Carlo move [{w}/{n}]: "
                       f"changed move sizes: d_pos - ({d_pos_old:.4f} -> {d_pos:.4f}), "
                       f"d_ang - ({d_ang_old:.4f} -> {d_ang:.4f})"
                      )
                #print(msg)
            
            # compute uniformly random coordinate shift magnitudes
            x = d_pos * rd.uniform(-1, 1)
            y = d_pos * rd.uniform(-1, 1)
            t = d_ang * rd.uniform(-1, 1)
            
            # apply coordinate shifts as a test
            testX = PosArray[w, 0] + x
            testY = PosArray[w, 1] + y
            testT = PosArray[w, 2] + t
            
            # check for possible overlaps with other particles or boundary
            if (testX ** 2 + testY ** 2) > ((R - b) ** 2) or (testX ** 2 + testY ** 2) < ((r + 2 * b) ** 2):
                
                # check if ellipse rotation would cause boundary overlap
                if (testX ** 2 + testY ** 2) > ((R - b) ** 2) and (testX ** 2 + testY ** 2) < ((r + 2 * b) ** 2):
                    
                    # ellipse can't be within one short axis length of outer boundary
                    if (testX ** 2 + testY ** 2) > ((R - a) ** 2):
                        overlapVar = True
                        
                    # ellipse can't be within one short axis length of inner boundary
                    elif (testX ** 2 + testY ** 2) < ((r + a) ** 2):
                        overlapVar = True
                        
                    # check for overlap with inner boundary
                    elif HardBoundaryCircle_Disc(r * 1.02, a, b, testX, testY, testT) == True:
                        overlapVar = True
                    
                    # check for overlap with outer boundary
                    elif HardBoundaryCircle_Disc(R, a, b, testX, testY, testT) == True:
                        overlapVar = True
                        
                    # check for overlap with other ellipses
                    else:
                        for j in range(n):
                            rij = np.sqrt((testX - PosArray[j, 0]) ** 2 + (testY - PosArray[j, 1]) ** 2)
                            if rij < (2 * b):                               
                                if j != w and (overlap_Ellipse(testX, testY, testT, PosArray[j, 0], PosArray[j, 1],
                                                               PosArray[j, 2], a, b) == True):
                                    overlapVar = True
                                    break                                 
                                else:
                                    overlapVar = False                                    
                            else:
                                overlapVar = False
                
                # check if ellipse rotation would cause boundary overlap
                elif (testX ** 2 + testY ** 2) > ((R - b) ** 2):
                    
                    # ellipse can't be within one short axis-length of boundary
                    if (testX ** 2 + testY ** 2) > ((R - a) ** 2):
                        overlapVar = True
                        
                    # check for overlap with outer boundary
                    elif (HardBoundaryCircle_Disc(R, a, b, testX, testY, testT) == True):
                        overlapVar = True
                        
                    # check for overlap with other ellipses
                    else:
                        for j in range(n):
                            
                            # center-to-center distance from other ellipses
                            rij = np.sqrt((testX - PosArray[j, 0]) ** 2 + (testY - PosArray[j, 1]) ** 2)
                            
                            # ellipse-ellipse overlap only possible if centers with two long axis lengths
                            if rij < (2 * b):
                                if j != w and (overlap_Ellipse(testX, testY, testT, PosArray[j, 0], PosArray[j, 1],
                                                               PosArray[j, 2], a, b) == True):
                                    overlapVar = True
                                    break
                                    
                                else:
                                    overlapVar = False
                                    
                            else:
                                overlapVar = False
                                
                else:
                    
                    # center of mass position can't be within one short axis length of inner boundary
                    if (testX ** 2 + testY ** 2) < ((r + a) ** 2):
                        overlapVar = True
                        
                    # check for overlap with inner boundary
                    elif (HardBoundaryCircle_Disc(r * 1.02, a, b, testX, testY, testT) == True):
                        overlapVar = True
                        
                    # check for overlap with other ellipses
                    else:
                        for j in range(n):
                            
                            # center-to-center distance between ellipses
                            rij = np.sqrt((testX - PosArray[j, 0]) ** 2 + (testY - PosArray[j, 1]) ** 2)
                            
                            # overlap only possible if ellipses centers are within 2 long axis lengths
                            if rij < (2 * b):
                                if j != w and (overlap_Ellipse(testX, testY, testT, PosArray[j, 0], PosArray[j, 1],
                                                               PosArray[j, 2], a, b) == True):
                                    overlapVar = True
                                    break                                    
                                else:
                                    overlapVar = False                                    
                            else:
                                overlapVar = False
                                
            # check for overlap with other ellipses if boundary overlap impossible
            else:
                for j in range(n):
                    
                    # center-to-center distance between ellipses
                    rij = np.sqrt((testX - PosArray[j, 0]) ** 2 + (testY - PosArray[j, 1]) ** 2)
                    
                    # overlap only possible if ellipse centers are within 2 long axis lengths
                    if rij < (2 * b):
                        if j != w and (
                                overlap_Ellipse(testX, testY, testT, PosArray[j, 0], PosArray[j, 1], PosArray[j, 2], a,
                                                b) == True):
                            overlapVar = True
                            break                     
                        else:
                            overlapVar = False                            
                    else:
                        overlapVar = False
            
            # don't do anything if particle-particle overlap detected
            if overlapVar == True:
                pass
            
            # accept the move and update
            elif overlapVar == False:
                accepted_moves += 1
                PosArray[w, 0] = testX
                PosArray[w, 1] = testY
                PosArray[w, 2] = testT

            moves += 1
            fixCount += 1
            x = 0
            y = 0

        plotCount += 1
        # periodically save data snapshots
        if plotCount == (save_every):
            plotCount = 0

            fileNameArray = 'step_.csv'
            new_fileName = fileNameArray.split(".csv")[0] + str(u) + ".csv"
            complete_name = os.path.join(main_folder_name, new_fileName)
            np.savetxt(complete_name, PosArray, delimiter=',')
            
            print("Monte Carlo step [{}/{}], Monte Carlo move [{}/{}]: plotted snapshot".format(u, steps, w, n))
   
    final_array_name = 'step_'+str(steps)+'.csv'
    complete_name = os.path.join(main_folder_name, final_array_name)
    np.savetxt(complete_name, PosArray, delimiter=',')
    
    # area fraction for simulation
    area_fraction = n * a * b / (R ** 2 - r ** 2)

    print(f"Total number of accepted moves: {accepted_moves}")
    print(f"Total number of moves: {moves}")
    print(f"Acceptance rate: {accepted_moves / moves}")
    
    # write simulation parameters to a text file
    file_name = "MonteCarlo_Annulus_SimNotes.txt"
    with open(os.path.join(main_folder_name, file_name), 'w+') as text_file:
        text_file.write("Parameters" + "\r\n")
        text_file.write("- - - - -" + "\r\n")
        text_file.write("Monte Carlo steps: " + str(steps) + "\r\n")
        text_file.write("R: " + str(R) + "\r\n")
        text_file.write("r: " + str(r) + "\r\n")
        text_file.write("d_pos / step size: " + str(d_pos) + "\r\n")
        text_file.write("d_ang / step size: " + str(d_ang) + "\r\n")
        text_file.write("# of Ellipse: " + str(n) + "\r\n")
        text_file.write("reduced density: " + str(area_fraction) + "\r\n")
        text_file.write("Semi Minor Axis: " + str(a) + "\r\n")
        text_file.write("Semi Major Axis: " + str(b) + "\r\n")
        text_file.write("Accepted Moves: " + str(accepted_moves) + "\r\n")
        text_file.write("Total Moves: " + str(moves) + "\r\n")
        text_file.write("Acceptance Rate: " + str(100 * (accepted_moves / moves)) + " %" + "\r\n")


#@jit(cache=True)
def MC_Circ_Hard(PosArray, out_dir, R, a, b, d_pos, d_ang, start_step, end_step, save_every):
    """
    Monte Carlo simulation for hard ellipses with hard circle boundary
    
    :param: PosArray
    :param: d_pos
    :param: d_ang
    :param: steps
    :param: n
    :param: R
    :param: a
    :param: b
    :param: save_every
    :param: out_dir
    :param: step_start
    """
        
    # pickle the simulation parameters for checkpointing
    var_fname = os.path.join(out_dir, "checkpoint.pickle")
    checkpoint_vars = {"pos_array":PosArray, "b":b, "a":a, "r":0, "R":R, "d_pos":d_pos, "d_ang":d_ang,
                       "start_step":start_step, "end_step":end_step, "save_every":save_every}
    with open(var_fname, "wb") as f:
        pickle.dump(checkpoint_vars, f)
  
    #save the initial state
    fileNameArray = 'step_0.csv'
    complete_name = os.path.join(out_dir, fileNameArray)
    np.savetxt(complete_name, PosArray, delimiter=',')
    
    # total number of particles
    n = len(PosArray)
    
    # fix and plot counters
    fixCount = 0
    plotCount = 0
    moves = 0
    accepted_moves = 0
    
    # iterate over all steps
    for u in range(start_step, end_step+1):
        
        # iterate over all particles 
        for w in range(n):
            
            # adjust the move sizes 50 times per simulation
            if fixCount == (np.ceil(steps / 50)):
                
                # reset the fix counter
                fixCount = 0
                
                d_pos_old = d_pos
                d_ang_old = d_ang
                
                # adjust move sizes
                if accepted_moves / moves < 0.47:
                    d_ang = 0.9 * d_ang
                    d_pos = 0.9 * d_ang
                elif accepted_moves / moves < 0.37:
                    d_ang = 0.75 * d_ang
                    d_pos = 0.75 * d_ang
                elif accepted_moves / moves < 0.27:
                    d_ang = 0.6 * d_ang
                    d_pos = 0.6 * d_ang
                elif accepted_moves / moves < 0.17:
                    d_ang = 0.35 * d_ang
                    d_pos = 0.35 * d_ang
                elif accepted_moves / moves < 0.07:
                    d_ang = 0.2 * d_ang
                    d_pos = 0.2 * d_ang
                elif accepted_moves / moves > 0.57:
                    d_ang = 1.1 * d_ang
                    d_pos = 1.1 * d_ang
                elif accepted_moves / moves > 0.67:
                    d_ang = 1.35 * d_ang
                    d_pos = 1.35 * d_ang
                elif accepted_moves / moves > 0.77:
                    d_ang = 1.5 * d_ang
                    d_pos = 1.5 * d_ang
                elif accepted_moves / moves > 0.87:
                    d_ang = 1.65 * d_ang
                    d_pos = 1.65 * d_ang
                elif accepted_moves / moves > 0.97:
                    d_ang = 1.8 * d_ang
                    d_pos = 1.8 * d_ang
                
                # print the adjustments at Monte Carlo step
                msg = (f"Monte Carlo step [{u}/{steps}], Monte Carlo move [{w}/{n}]: "
                       f"changed move sizes: d_pos - ({d_pos_old:.4f} -> {d_pos:.4f}), "
                       f"d_ang - ({d_ang_old:.4f} -> {d_ang:.4f})"
                      )
                #print(msg)
            
            # uniformly random scaling
            x = d_pos * rd.uniform(-1, 1)
            y = d_pos * rd.uniform(-1, 1)
            t = d_ang * rd.uniform(-1, 1)
            
            # apply proposed shifts and check for overlap
            testX = PosArray[w, 0] + x
            testY = PosArray[w, 1] + y
            testT = PosArray[w, 2] + t
            
            # check if long axis definitely overlaps with boundary
            if (testX ** 2 + testY ** 2) > ((R - 2 * b) ** 2):
                
                # check if short axis definitely overlaps with boundary
                if (testX ** 2 + testY ** 2) > ((R - a) ** 2):
                    overlapVar = True
                
                # apply circular boundary overlap check algorithm
                elif (HardBoundaryCircle_Disc(R, a, b, testX, testY, testT) == True):
                    overlapVar = True
                    
                else:
                    
                    # check for overlap with other ellipses
                    for j in range(n):
                        
                        # center of mass distance between ellipses
                        rij = np.sqrt((testX - PosArray[j, 0]) ** 2 + (testY - PosArray[j, 1]) ** 2)
                        
                        # c.o.m distance less than long-long end distance; may overlap
                        if rij < (2 * b):
                            
                            # check for ellipse-ellipse overlap
                            if j != w and (
                                    overlap_Ellipse(testX, testY, testT, PosArray[j, 0], PosArray[j, 1], PosArray[j, 2],
                                                    a, b) == True):
                                overlapVar = True
                                break
                                
                            else:
                                overlapVar = False
                                
                        # c.o.m distance greater/equal to long end-to-end distance; no overlap        
                        else:
                            overlapVar = False
            
            else:
                
                # check for overlap with other ellipses
                for j in range(n):
                    
                    # center of mass distance between ellipses
                    rij = np.sqrt((testX - PosArray[j, 0]) ** 2 + (testY - PosArray[j, 1]) ** 2)
                    
                    # c.o.m distance less than long-long end distance; may overlap
                    if rij < (2 * b):
                        
                        # check for ellipse-ellipse overlap
                        if j != w and (
                                overlap_Ellipse(testX, testY, testT, PosArray[j, 0], PosArray[j, 1], PosArray[j, 2], a,
                                                b) == True):
                            overlapVar = True
                            break
                            
                        else:
                            overlapVar = False
                    
                    # c.o.m distance greater/equal to long end-to-end distance; no overlap
                    else:
                        overlapVar = False
            
            # if overlap, don't accept the move
            if overlapVar == True:
                pass
            
            # accept the move
            elif overlapVar == False:
                accepted_moves += 1
                PosArray[w, 0] = testX
                PosArray[w, 1] = testY
                PosArray[w, 2] = testT
            
            # increment moves/fix counters
            moves += 1
            fixCount += 1
        
        # increment the plot counter
        plotCount += 1
        
        # periodically save snapshots
        if plotCount == (save_every):
            
            # reset the plot counter
            plotCount = 0

            fileNameArray = 'step_.csv'
            new_fileName = fileNameArray.split(".csv")[0] + str(u) + ".csv"
            complete_name = os.path.join(out_dir, new_fileName)
            np.savetxt(complete_name, PosArray, delimiter=',')
            
            # open and write to parameters file
            with open(var_fname, "rb") as f:
                checkpoint_vars = pickle.load(f)
            checkpoint_vars["ang_shift"] = d_ang
            checkpoint_vars["pos_shift"] = d_pos
            checkpoint_vars["current_step"] = u
            checkpoint_vars["pos_array"] = PosArray
            with open(var_fname, "wb") as f:
                pickle.dump(checkpoint_vars, f)
            
            print("Monte Carlo step [{}/{}], Monte Carlo move [{}/{}]: plotted snapshot".format(u, steps, w, n))
    
    # packing fraction
    area_fraction = n * a * b / (R ** 2)

    print(f"Total Accepted Moves: {accepted_moves}")
    print(f"Total Moves: {moves}")
    print(f"Acceptance Rate: {accepted_moves / moves}")
    
    # save a snapshot of the final positions of the particles
    fileNameArray = f'step_{steps}.csv'
    complete_name = os.path.join(out_dir, fileNameArray)
    np.savetxt(complete_name, PosArray, delimiter=',')
    
    # write the simulation notes file
    file_name = "MonteCarlo_Circle_SimNotes.txt"
    complete_name = os.path.join(out_dir, file_name)
    with open(complete_name, 'w+') as text_file:
        text_file.write("Parameters" + "\r\n")
        text_file.write("- - - - -" + "\r\n")
        text_file.write("Monte Carlo steps: " + str(steps) + "\r\n")
        text_file.write("R: " + str(R) + "\r\n")
        text_file.write("d_pos / step size: " + str(d_pos) + "\r\n")
        text_file.write("d_ang / step size: " + str(d_ang) + "\r\n")
        text_file.write("# of Ellipse: " + str(n) + "\r\n")
        text_file.write("reduced density: " + str(area_fraction) + "\r\n")
        text_file.write("Semi Minor Axis: " + str(a) + "\r\n")
        text_file.write("Semi Major Axis: " + str(b) + "\r\n")
        text_file.write("Accepted Moves: " + str(accepted_moves) + "\r\n")
        text_file.write("Total Moves: " + str(moves) + "\r\n")
        text_file.write("Acceptance Rate: " + str(100 * (accepted_moves / moves)) + " %" + "\r\n")
    
    
if __name__ == "__main__":
    
    # start the timer
    import time
    start = time.perf_counter()
    
    # argument parsing
    parser = argparse.ArgumentParser(description="Run a Monte Carlo simulation of liquid crystals")
    
    # dimensions and shape of the confinement geometry
    parser.add_argument("--confinement", choices=["Circle", "Annulus"], help="Type of confinement to simulate")
    parser.add_argument("--outer_radius", type=float, help="Radius of outer boundary")
    parser.add_argument("--outer_increment", type=float, help="Increment to outer boundary")
    parser.add_argument("--inner_radius", type=float, help="Radius of inner boundary")
    
    # characteristics of simulated particles
    parser.add_argument("-N", type=int, help="Number of particles to simulate")
    parser.add_argument("--long_axis", type=float, help="Semi-major axis of ellipse")
    parser.add_argument("--short_axis", type=float, help="Semi-minor axis of ellipse")
    
    # related to the Monte Carlo simulation
    parser.add_argument("--steps", type=int, help="Number of steps to run simulation for")
    parser.add_argument("--save_every", type=int, help="Number of every MC steps to save system state")
    
    # saving and checkpointing
    parser.add_argument("--res-path", help="Path to store results at")
    parser.add_argument("--checkpoint", type=int, help="checkpoint file to use")
    
    args = parser.parse_args()
    
    # load parameters from checkpoint
    if args.checkpoint is not None:
        print("Loading parameters from checkpoint file")
        with open(args.checkpoint, "rb") as in_f:
            params = pickle.load(in_f)
        initial_state = params["pos_array"]
        a = params["a"]
        b = params["b"]
        outer_radius = params["R"]
        inner_radius = params["r"]
        start_step = params["current_step"]
        end_step = params["total_steps"]
        step_xy = params["d_pos"]
        step_th = params["d_ang"]
        save_every = params["save_every"]
    
    # if no checkpoint, create the initial state from scratch
    else:
        print("Checkpoint file not provided. Creating the initial state from scratch")
        
        # get parameters from command line arguments
        a = args.short_axis
        b = args.long_axis
        inner_radius = args.inner_radius
        outer_radius = args.outer_radius
        start_step = 0
        end_step = args.steps
        step_xy = 0.5 * inner_radius
        step_th = np.pi / 2
        dely = 0  # % of a
        delx = 0  # % of a
    
        # create the initial state from scratch
        if confinement = "Circle":
            initial_state = init_Circ_H_GrC(args.N, a, b, args.outer_radius, dely, delx)[0]
            print(f"Time for circle boundary state initialization for N={args.N}: {time.perf_counter()-start} seconds.")
        elif confinement = "Annulus":
            initial_state = init_Ann_H_GrC(args.N, a, b, args.outer_radius, args.inner_radius, dely, delx)[0]
            print(f"Time for annular boundary state initialization for N={args.N}: {time.perf_counter()-start} seconds")
        else:
            raise NotImplementedError("Confinement type not supported")
    
    # save directory for simulation outputs
    out_dir = args.res_dir
    if os.path.exists(out_dir):
        pass
    else:
        os.makedirs(out_dir)
    
    # circle monte carlo
    if args.confinement == "Circle":
        
        inc_scaling = 0.35
        MC_Circ_Hard(initial_state, args.res_dir, R=outer_radius+args.outer_increment*inc_scaling,
                     a=a, b=b, d_pos=step_xy, d_ang=step_th,
                     start_step=start_step, end_step=end_step, save_every=save_every)
    
    # annulus monte carlo
    elif args.confinement == "Annulus":
        
        MC_Ann_Hard(initial_state, step_xy, step_th, args.steps, args.outer_radius, args.inner_radius,
                    a, b, save_every=args.save_every, out_dir=args.res_path)
    
    else:
        raise NotImplementedError("Confinement type not supported") 
    
    print(f"Simulation execution time: {time.perf_counter() - start} seconds")