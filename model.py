import numpy as np
import imageio
import matplotlib.pyplot as plt
import scipy.ndimage as img
from PIL import Image

def delta1(r, sigma):
    return np.where(r < sigma, 1 - r/sigma, 0)

def delta2(r, sigma):
    return np.where(r < sigma, 1 - r**2/sigma**2, 0)

def delta3(r, sigma):
    return np.where(r < sigma, np.sqrt(np.abs(sigma**2 - r**2)) / sigma, 0)

def delta4(r, sigma):
    return 1 - np.tanh(r/sigma)

def delta5(r, sigma):
    return np.exp(-0.5 * (r/sigma)**2)

def fisheye_effect(arrF, vecC, sigma=100., dfct=delta1):
    vecC = np.array(vecC).reshape(-1,1)
    M, N = arrF.shape
    u, v = np.meshgrid(np.arange(N), np.arange(M))
    matX = np.vstack((v.flatten(), u.flatten())).astype(float) # u
    matR = vecC - matX                      # vectors pointing to center # r = c-u
    dist = np.sqrt(np.sum(matR**2, axis=0)) # distances to center # ||r||
    matX = matX + matR * dfct(dist, sigma)  # W(u,c,sigma)= u + r*delta
    
    arrG = img.map_coordinates(arrF, matX)  # matX MUST be float
    arrG = arrG.reshape(M,N)
    return np.clip(arrG,0,1)

####################################################################################

def swirl_effect(arrF, vecC, sigma, magnitude):
    M, N = arrF.shape
    u, v = np.meshgrid(np.arange(N), np.arange(M))
    matX = np.stack((v, u)).astype(float)
    
    # compute polar coordinates with respect to vecC
    vecC = np.asarray(vecC).reshape(2,1,1)
    diff = matX - vecC 
    r = np.linalg.norm(diff, axis=0)
    angle = np.arctan2(diff[1], diff[0])
    
    dist = r/r.max()
    gaussian = np.exp(- dist**2 / (2*(sigma**2)))
    
    angle += magnitude*gaussian
    
    # compute euclidian coordinates with respect to image zero
    matX = np.stack([r * np.cos(angle) , r * np.sin(angle)])
    matX += vecC

    arrG = img.map_coordinates(arrF, matX) # matX MUST be float
    arrG = arrG.reshape(M,N)
    return np.clip(arrG, 0, 1)

####################################################################################

def waves_effect(arrF, amplitude, frequency, phase):
    M, N = arrF.shape
    u, v = np.meshgrid(np.arange(N+amplitude[1]*2), np.arange(M+amplitude[0]*2))
    matX = np.stack((v, u)).astype(float)
      
    # for j axis
    b = amplitude[1] * np.sin(matX[0]/frequency[1] + phase[1])
    matX[1] += b - amplitude[1]
    
    # for i axis
    a = amplitude[0] * np.sin(matX[1]/frequency[0] + phase[0]) 
    matX[0] += a - amplitude[0]
    
    arrG = img.map_coordinates(arrF, matX) # matX MUST be float
    arrG = arrG.reshape(matX.shape[1],matX.shape[2])
    return np.clip(arrG, 0, 1)

####################################################################################

def cylinder(arrF, angle_shift):
    M, N = arrF.shape
    u, v = np.meshgrid(np.arange(N), np.arange(M))
    matX = np.stack((v, u)).astype(float)
    
    # compute polar coordinates with respect to vecC
    vecC = np.array([arrF.shape[0]//2, arrF.shape[1]//2]).reshape(2,1,1)
    diff = matX - vecC 
    
    r = np.linalg.norm(diff, axis=0)
    #y = (1 - r/(arrF.shape[0]//2)) * (arrF.shape[0]-1)
    y = (r/(arrF.shape[0]//2)) * (arrF.shape[0]-1) 
    
    angle = np.arctan2(diff[0], diff[1])
    angle = angle-angle.min() # min angle is 0 with this line
    angle = angle/angle.max() # angle is normalized to 0-1
    #angle = (angle + 0.3) % 1.0
    angle = (angle + angle_shift/360.0) % 1.0
    x = angle * (arrF.shape[1]-1)

    matX = np.stack([y, x])
    
    #arrG = img.map_coordinates(arrF, matX) # matX MUST be float
    arrG = img.map_coordinates(np.flipud(arrF), matX) # matX MUST be float
    arrG = arrG.reshape(M,N)
    return np.clip(arrG, 0, 1)

######################### RADIAL BLUR EFFECT ########################################

def to_r_phi_plane_(f, m, n, rmax, phimax):
    
    rs, phis = np.meshgrid(np.linspace(0, rmax, n), np.linspace(0, phimax, m), sparse=True)
    
    xs, ys = rs * np.cos(phis), rs * np.sin(phis)
    xs, ys = xs.reshape(-1), ys.reshape(-1)
    
    coords = np.vstack((ys, xs))
    #print(coords.shape)
    
    vecC = np.array([f.shape[0]//2, f.shape[1]//2]).reshape(2,1)
    coords += vecC
    
    g = img.map_coordinates(f, coords, order=3)
    g = g.reshape(m, n)
    return np.flipud(g)

def from_r_phi_plane_V2_(g, m, n, rmax, phimax):
    xs, ys = np.meshgrid(np.arange(n), np.arange(m), sparse=True)
    
    xs -= n//2
    ys -= m//2
    
    rs, phis = np.sqrt(xs**2 + ys**2), np.arctan2(ys, xs)
    #print(rs, phis)
    phis += np.pi

    rs, phis = rs.reshape(-1), phis.reshape(-1)
     
    iis = phis / phimax * (m-1)
    jjs = rs / rmax * (n-1)
    coords = np.vstack((iis, jjs)) 
    #print(iis, jjs)
    
    h = img.map_coordinates(g, coords, order=3)
    h = h.reshape(m, n)
    return np.fliplr(np.flipud(h))

def radial_blur_effect(arrF, sigma):
    arrF = np.flipud(arrF)
    m, n = arrF.shape
    rmax = np.sqrt((m/2)**2 + (n/2)**2)
    phimax = 2 * np.pi

    arrG = to_r_phi_plane_(arrF, m, n, rmax, phimax)

    blurred_arrG = img.gaussian_filter1d(arrG, sigma=sigma, axis=0, mode="wrap")

    arrH = from_r_phi_plane_V2_(blurred_arrG, m, n, rmax, phimax)

    return np.clip(arrH, 0, 1)

####################################################################################

def perspective_mapping(arrF, arrH, u_ul, u_ur, u_ll, u_lr, debug=False):
    if len(arrF.shape)==2 and len(arrH.shape)==2:
        return perspective_mapping_(arrF, arrH, u_ul, u_ur, u_ll, u_lr, debug)
    else:
        arrF_ = Image.fromarray((arrF*255).astype(np.uint8)).convert(mode="RGB")
        arrF_ = np.array(arrF_) / 255.0
        arrH_ = Image.fromarray((arrH*255).astype(np.uint8)).convert(mode="RGB")
        arrH_ = np.array(arrH_) / 255.0

        output = []
        for i in range(3):
            output.append( perspective_mapping_(arrF_[:,:,i], arrH_[:,:,i], u_ul, u_ur, u_ll, u_lr, debug) )
        return np.stack(output, axis=2)

def perspective_mapping_(arrF, arrH, u_ul, u_ur, u_ll, u_lr, debug=False):
    M, N = arrH.shape
    u, v = np.meshgrid(np.arange(N), np.arange(M))
    matX = np.stack((u, v)).astype(float)
    
    u1, v1 = u_ul
    u2, v2 = u_ur
    u3, v3 = u_ll
    u4, v4 = u_lr
    
    x1, y1 = 0, 0
    x2, y2 = arrF.shape[1], 0
    x3, y3 = 0, arrF.shape[0]
    x4, y4 = arrF.shape[1], arrF.shape[0]
    
    A = [[u1, v1, 1, 0, 0, 0, -u1*x1, -v1*x1],
         [u2, v2, 1, 0, 0, 0, -u2*x2, -v2*x2],
         [u3, v3, 1, 0, 0, 0, -u3*x3, -v3*x3],
         [u4, v4, 1, 0, 0, 0, -u4*x4, -v4*x4],
         [0, 0, 0, u1, v1, 1, -u1*y1, -v1*y1],
         [0, 0, 0, u2, v2, 1, -u2*y2, -v2*y2],
         [0, 0, 0, u3, v3, 1, -u3*y3, -v3*y3],
         [0, 0, 0, u4, v4, 1, -u4*y4, -v4*y4]]
    
    A = np.array(A)
    b = np.array([x1, x2, x3, x4, y1, y2, y3, y4]).T
    X, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    a,b,c,d,e,f,g,h = X
    
    X_ = (a*matX[0] + b*matX[1] + c) / (g*matX[0] + h*matX[1] + 1)
    Y_ = (d*matX[0] + e*matX[1] + f) / (g*matX[0] + h*matX[1] + 1)
    
    matX = np.stack((Y_, X_))
    
    arrG = img.map_coordinates(arrF, matX, cval=-1) # matX MUST be float
    arrG = arrG.reshape(matX.shape[1],matX.shape[2])
    
    mask = arrG != -1
    #mask = np.bitwise_and(arrG != -1, arrG<230)
    
    if debug:
        plt.imshow(arrG, cmap="gray"); plt.title("Transformed Image"); plt.show()
        plt.imshow(mask, cmap="gray"); plt.title("Mask")

    newArr = arrH.copy()
    newArr[mask] = arrG[mask]
    return np.clip(newArr, 0, 1)

def perspective_mapping_transparent(arrF, arrH, u_ul, u_ur, u_ll, u_lr, debug=False):
    M, N = arrH.shape
    u, v = np.meshgrid(np.arange(N), np.arange(M))
    matX = np.stack((u, v)).astype(float)
    
    u1, v1 = u_ul
    u2, v2 = u_ur
    u3, v3 = u_ll
    u4, v4 = u_lr
    
    x1, y1 = 0, 0
    x2, y2 = arrF.shape[1], 0
    x3, y3 = 0, arrF.shape[0]
    x4, y4 = arrF.shape[1], arrF.shape[0]
    
    A = [[u1, v1, 1, 0, 0, 0, -u1*x1, -v1*x1],
         [u2, v2, 1, 0, 0, 0, -u2*x2, -v2*x2],
         [u3, v3, 1, 0, 0, 0, -u3*x3, -v3*x3],
         [u4, v4, 1, 0, 0, 0, -u4*x4, -v4*x4],
         [0, 0, 0, u1, v1, 1, -u1*y1, -v1*y1],
         [0, 0, 0, u2, v2, 1, -u2*y2, -v2*y2],
         [0, 0, 0, u3, v3, 1, -u3*y3, -v3*y3],
         [0, 0, 0, u4, v4, 1, -u4*y4, -v4*y4]]
    
    A = np.array(A)
    b = np.array([x1, x2, x3, x4, y1, y2, y3, y4]).T
    X, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    a,b,c,d,e,f,g,h = X
     
    X_ = (a*matX[0] + b*matX[1] + c) / (g*matX[0] + h*matX[1] + 1)
    Y_ = (d*matX[0] + e*matX[1] + f) / (g*matX[0] + h*matX[1] + 1)
    
    matX = np.stack((Y_, X_))
    
    arrG = img.map_coordinates(arrF, matX, cval=-1) # matX MUST be float
    arrG = arrG.reshape(matX.shape[1],matX.shape[2])
    
    #mask = arrG != -1
    mask = np.bitwise_and(arrG != -1, arrG<230)
    
    if debug:
        plt.imshow(arrG, cmap="gray"); plt.title("Transformed Image"); plt.show()
        plt.imshow(mask, cmap="gray"); plt.title("Mask")

    newArr = arrH.copy()
    newArr[mask] = arrG[mask]
    return newArr

####################################################################################

def lpNorm(matX, p):
    return np.power(np.sum(np.power(np.abs(matX), p), axis=0), 1/p)

def square_eye_effect(arrF, vecC, sigma, p):
    vecC = np.array(vecC).reshape(-1,1)
    M, N = arrF.shape
    u, v = np.meshgrid(np.arange(N), np.arange(M))
    
    matX = np.vstack((v.flatten(), u.flatten())).astype(float) 
    matR = vecC - matX     # vectors pointing to center
    matX = matX + matR * np.exp(-lpNorm(matR, p)**2 / (2*sigma**2))
    
    arrG = img.map_coordinates(arrF, matX)
    arrG = arrG.reshape(M,N)
    return np.clip(arrG, 0, 1)

####################################################################################


#out = fisheye(arrF, (350, 200), sigma=300)
#axs[1].imshow(out / 255, cmap="gray", vmin=0, vmax=1)

#out = custom_swirl_effect(arrF)
#_ = plt.imshow(out / 255, cmap="gray")

#out = waves_effect(arrF, amplitude=[10,7], frequency=[10.0,6.5], phase=[0,2])
#plt.imshow(out / 255, cmap="gray")