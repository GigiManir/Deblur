import numpy as np
import matplotlib.pyplot as plt
from skimage import data, filters, io

def gkern(kernlen, nsig):
  """
  Genera un kernel per la realizzazione di un filtro di sfocatura Gaussiana.

  Input ->
  kernlen: diametro della sfocatura gaussiana.
  nsig:    varianza della sfocatura. Più basso, più sfoca.

  Output -> Kernel Gaussiano di dimensione (kernlen+1) x (kernlen+1) e varianza nsig.
  """
  import scipy.stats as st

  x = np.linspace(-nsig, nsig, kernlen+1)
  kern1d = np.diff(st.norm.cdf(x))
  kern2d = np.outer(kern1d, kern1d)
  return kern2d/kern2d.sum()

def A(x, d=7, sigma=0.5):
  """
  Esegue il prodotto Ax, dove A è la matrice di sfocamento (che, per aumentare l'efficienza, non viene memorizzata).
  
  Input ->
  x:     Immagine di dimensione m x n, che si vuole sfocare.
  d:     Diametro della sfocatura Gaussiana.
  sigma: Varianza della sfocatura Gaussiana.
  
  Output -> Immagine di dimensione m x n, sfocata.
  """
  from scipy.signal import convolve2d
  from numpy import fft
  m, n = x.shape

  K_ext = np.zeros((m, n))
  K = gkern(d, sigma)
  K_ext[:d, :d] = K
  K_ext = fft.fft2(K_ext)
  x = fft.fft2(x)

  return np.real(fft.ifft2(K_ext * x))

def AT(x, d=7, sigma=0.5):
  """
  Esegue il prodotto A^T x, dove A è la matrice di sfocamento (che, per aumentare l'efficienza, non viene memorizzata).
  
  Input ->
  x:     Immagine di dimensione m x n, che si vuole sfocare.
  d:     Diametro della sfocatura Gaussiana.
  sigma: Varianza della sfocatura Gaussiana.
  
  Output -> Immagine di dimensione m x n, sfocata.
  """
  from scipy.signal import convolve2d
  from numpy import fft
  m, n = x.shape

  K_ext = np.zeros((m, n))
  K_ext[:d, :d] = gkern(d, sigma)
  K_ext = fft.fft2(K_ext)
  x = fft.fft2(x)

  return np.real(fft.ifft2(np.conj(K_ext) * x))


#assegniamo ad una variabile X l'immagine
X = data.camera()
#X = io.imread("https://i.imgur.com/YBpbx8Z.png", as_gray=True) #QR
#X = io.imread("https://i.imgur.com/8r0Q1Xn.png", as_gray=True) #Foto
#X = io.imread("https://i.imgur.com/MHuTv2X.jpeg", as_gray=True) #Testo
m, n = X.shape
x = X.reshape(m*n)


# 2
X_blur = A(X)
x_blur = X_blur.reshape(m*n)


# 3
# Generiamo il rumore eta
sigma = 0.1 # Varianza del rumore
eta = np.random.normal(size=X_blur.shape)
eta /= np.linalg.norm(eta, 'fro')
eta *= sigma * np.linalg.norm(X_blur,'fro')
print(eta.shape)

# Aggiungiamo il rumore all'immagine sfocata
B = X_blur + eta
b = B.reshape(m*n)

# Visualizziamo i risultati
plt.figure(figsize=(20, 7))

ax1 = plt.subplot(1, 3, 1)
ax1.imshow(X, cmap='gray')
plt.title('Immagine Originale', fontsize=25)

ax2 = plt.subplot(1, 3, 2)
ax2.imshow(X_blur, cmap='gray')
plt.title('Immagine Sfocata', fontsize=25)

ax3 = plt.subplot(1, 3, 3)
ax3.imshow(B, cmap='gray')
plt.title('Immagine Corrotta', fontsize=25)

plt.show()

max_it = 50
STOP = 10**-6

def f_x(x, b):
  return 0.5 * (np.linalg.norm(A(x) - b)**2)

def grad_f(x, b):
  return AT(A(x) - b)

def backtracking_next(x, b, grad):
  alpha = 1.1
  rho = 0.5 #1/2
  c1 = 0.25 #1/4
  while f_x(x - alpha * grad, b) >f_x(x, b) - alpha * c1 * np.linalg.norm(grad, 'fro') ** 2:
    alpha = alpha * rho
  return alpha

def min(x0, x_true, b, maxit, stop):
  x = x0
  grad = grad_f(x, b)
  err = np.zeros(maxit) 
  k = 0

  while (np.linalg.norm(grad) > stop) and (k < maxit):
    x = x + backtracking_next(x, b, grad) * (-grad) 
    grad = grad_f(x, b)
    err[k]  = np.linalg.norm(x_true - x)  
    k += 1

  err = err[0:k]  
  return(x, k, err)

x0 = np.zeros(X.shape)
(x_naive, ite_naive, err_naive) = min(B, X, B, max_it, STOP)

err_plot = np.linspace(1, ite_naive, err_naive.size)
plt.plot(err_plot, err_naive)
plt.title('Errore metodo Naive')
plt.grid()
plt.show()

def min_trunc(x0, x_true, b, maxit, stop):
  x = x0
  x_r = x0
  grad = grad_f(x, b)
  err = np.zeros(maxit)
  k = 0
  while(np.linalg.norm(grad) > stop) and (k < maxit):
    x = x - backtracking_next(x, b, grad) * grad
    grad = grad_f(x, b)
    err[k] = np.linalg.norm(x_true - x) 
    if(err[k] < err[k - 1]) and (k > 0):
      x_r = x
      k_r= k
    k = k + 1
    
  err = err[0 : k] 
  return(x_r, grad, k, err)

semiconv=np.where(err_naive == np.amin(err_naive))[0]
print(semiconv)
#(x_trunc, ite_tronc, err_trunc) = min(x0, X, B, semiconv+1, STOP)
(x_trunc, grad_trunc,ite_tronc, err_trunc)=min_trunc(x0,X,B,max_it,STOP)


err_plot = np.linspace(1, ite_tronc, err_trunc.size)
plt.plot(err_plot, err_trunc)
plt.title('Errore metodo trunc')
plt.grid()
plt.show()

plt.figure(figsize=(30, 10))

ax1 = plt.subplot(1, 3, 1)
ax1.imshow(B, cmap='gray')
plt.title('Immagine corrotta (iniziale)', fontsize=20)

ax2 = plt.subplot(1, 3, 2)
ax2.imshow(x_naive, cmap='gray')
plt.title('Immagine ricostruta con metodo naive', fontsize=20)

ax3 = plt.subplot(1, 3, 3)
ax3.imshow(x_trunc, cmap='gray')
plt.title('Immagine nel punto di semiconvergenza', fontsize=20)

def f_regolar(x, b, lamb):
  return 0.5*(np.linalg.norm(A(x)-b))**2 + 0.5*lamb*np.linalg.norm(x)**2

def grad_f_regolar(x, b, lamb):
  return AT(A(x)-b) + lamb*x

def backtracking_next_regolar(x, b, grad, lamb):
  alpha = 1.1
  rho = 0.5
  c1 = 0.25
  k = 0

  while f_regolar(x-alpha*grad, b, lamb) > f_regolar(x, b, lamb) - alpha * c1 * np.linalg.norm(grad, 'fro') ** 2:
    alpha *= rho
    k += 1

  return alpha;

def min_regolar(x0, x_true, b, lamb, maxit, abstop):
  x = x0
  grad = grad_f_regolar(x, b, lamb)
  err = np.zeros(maxit) 

  k = 0
  while (np.linalg.norm(grad) > abstop) and (k < maxit):
    x = x + backtracking_next_regolar(x, b, grad, lamb) * (-grad) 
    grad = grad_f_regolar(x, b, lamb)
    err[k]  = np.linalg.norm(x_true - x)/(m*n)  
                                          
    k += 1

  err = err[:k]  
  return(x, k, err)


def lambottimale(b, max):
  lamb= 0.031
  k=0
  x,_,err = min_regolar(B,X,B,lamb, max, STOP) 
  x_index=np.where(err == np.amin(err))[0]
  x,_,_ = min_regolar(B, X, B, lamb, x_index+1, STOP)
  rat = 1.1
  while np.linalg.norm(A(x)-b)**2 <= np.linalg.norm(eta)**2:
    lamb *= rat
    x,_,_ = min_regolar(B,X,B,lamb, max, STOP)
    x_index=np.where(err == np.amin(err))[0]
    x,_,_ = min_regolar(B, X, B, lamb, x_index+1, STOP)
    k+=1
  return lamb/rat

lambeuristico = 0.04
x0 = np.zeros(X.shape)
lamb=lambottimale(B, max_it)

print(lamb) 

(x_euristico, ite_euristico, errore_euristico) = min_regolar(B, X, B,lambeuristico, max_it, STOP)

(x_disc, ite_disc, errore_disc) = min_regolar(B, X, B, lamb, max_it, STOP)

err_eur_plot = np.linspace(1, ite_euristico, errore_euristico.size)
plt.plot(err_eur_plot, errore_euristico)
plt.title('Errore metodo euristico')
plt.grid()
plt.show()

err_lambda_plot = np.linspace(1, ite_disc, errore_disc.size)
plt.plot(err_lambda_plot, errore_disc)
plt.title('Errore metodo lambda')
plt.grid()
plt.show()

plt.figure(figsize=(15,5))

ax1 = plt.subplot(1, 3, 1)
ax1.imshow(B, cmap='gray')
plt.title('Immagine Corrotta', fontsize=20)

ax2 = plt.subplot(1, 3, 2)
ax2.imshow(x_euristico, cmap='gray')
plt.title('Lambda euristico', fontsize=20)

ax3 = plt.subplot(1, 3, 3)
ax3.imshow(x_disc, cmap='gray')
plt.title('Lambda ottimale', fontsize=20)

def f_norm1(x, b, lamb):
  return 0.5 * np.linalg.norm(A(x) - b)**2 + lamb * np.linalg.norm(x, 1)

def gradf_norm1(x, b, lamb):
  return AT(A(x) - b) + lamb * np.sign(x)

def backtracking_next_norm1(x, b, grad, lamb):
  alpha=1.1
  rho = 0.5
  c1 =0.25
  while f_norm1(x - alpha * grad, b, lamb) > f_norm1(x, b, lamb) - alpha * c1 * np.linalg.norm(grad, 'fro') ** 2:
    alpha = alpha * rho
  return alpha

def min_norm1(lamb, x0, x_true, b, maxit, stop):
  x = x0
  x_r = x
  grad = gradf_norm1(x, b, lamb)
  err = np.zeros(maxit)
  k = 0
  while np.linalg.norm(grad) > stop and k < maxit:
    x = x - backtracking_next_norm1(x, b, grad, lamb) * grad
    grad = gradf_norm1(x, b, lamb)
    err[k] = np.linalg.norm(x_true - x)
    if(err[k] < err[k - 1]) and (k > 0):
      x_r = x
    k = k + 1

  err = err[0 : k] 
  return(x_r, grad, k, err)

x0 = np.zeros(X.shape)
lamb2 = 0.4
(lambda_norm1, grad_lambda2, ite_lambda2, errore_lambda2) = min_norm1(lamb2, x0, X, B, max_it, STOP)

err3_plot = np.linspace(1, ite_lambda2, errore_lambda2.size)
plt.plot(err3_plot, errore_lambda2)
plt.title('Errore metodo lambda norma 1')
plt.grid()
plt.show()

plt.figure(figsize=(30, 10))

ax1 = plt.subplot(1, 3, 1)
ax1.imshow(B, cmap='gray')
plt.title('Immagine Corrotta', fontsize=30)

ax2 = plt.subplot(1, 3, 2)
ax2.imshow(lambda_norm1, cmap='gray')
plt.title('Immagine Lambda norma 1', fontsize=30)

ax3 = plt.subplot(1, 3, 3)
ax3.imshow(x_disc, cmap='gray')
plt.title('Immagine Lambda', fontsize=30)

def f_norm_m(x, b, lamb, mu):
  return 0.5*(np.linalg.norm(A(x)-b))**2 + 0.5*lamb*np.linalg.norm(x)**2 + mu*np.linalg.norm(x,1)

def gradf_norm_m(x, b, lamb, mu):
  return AT(A(x)-b) + lamb*x +  mu*np.sign(x)

def backtracking_next_norm_m(x, b, grad, lamb, mu):
  alpha=1.1
  rho = 0.5
  c1 =0.25
  while (f_norm_m(x - alpha * grad, b, lamb, mu) > (f_norm_m(x, b, lamb, mu) - alpha * c1 * np.linalg.norm(grad, 'fro') ** 2)):
    alpha = alpha * rho
  return alpha

def min_norm_m(b, x0, x_true, lamb, mu, maxiterazioni, stop):
  x = x0
  x_star = x
  grad = gradf_norm_m(x, b, lamb, mu)
  errore = np.zeros(maxiterazioni)
  k = 0
  k_star = 0
  while(np.linalg.norm(grad) > stop) and (k < maxiterazioni):
    x = x - backtracking_next_norm_m(x, b, grad, lamb, mu) * grad
    grad = gradf_norm_m(x, b, lamb, mu)
    errore[k] = np.linalg.norm(x_true - x)
    if(errore[k] < errore[k - 1]) and (k > 0):
      x_star = x
      k_star = k
    k = k + 1
    
  errore = errore[0 : k] 
  return (x_star, grad, k, errore, k_star) 

def lambottimale(b, max, mu=0.1):
  lamb= 0.031
  k=0
  (x, gradiente, iterazioni, errore, err_min) = min_norm_m(B, X, B, lamb, mu, max, STOP)
  rat = 1.1
  while (np.linalg.norm(A(x)-b)**2 <= np.linalg.norm(eta)**2):
    lamb *= rat
    (x, gradiente, iterazioni, errore, err_min) = min_norm_m(B, X, B, lamb, mu, max, STOP)
    k+=1
  return lamb/rat

mu=0.1
lamb_m = lambottimale(B, max_it) 
print(lamb_m)

(x_norm_m, grad_norm_m, ite_norm_m, err_norm_m, err_min_m) = min_norm_m(B, x0, X, lamb_m, mu, max_it, STOP)

err_m_plot = np.linspace(1, ite_norm_m, err_norm_m.size)
plt.plot(err_m_plot, err_norm_m)
plt.title('Errore metodo lambda norma mista')
plt.grid()
plt.show()

plt.figure(figsize=(30, 10))

ax2 = plt.subplot(1, 3, 2)
ax2.imshow(x_norm_m, cmap='gray')
plt.title('Immagine Lambda norma mista', fontsize=30)

def plot_all_images():
  plt.figure(figsize=(32, 60))
  ax1 = plt.subplot(4,2, 1)
  ax1.imshow(X, cmap='gray')
  plt.title('Immagine Originale', fontsize=30)

  ax2 = plt.subplot(4,2, 2)
  ax2.imshow(X_blur, cmap='gray')
  plt.title('Immagine Sfocata', fontsize=30)

  ax3 = plt.subplot(4,2, 3)
  ax3.imshow(B, cmap='gray')
  plt.title('Immagine Corrotta', fontsize=30)

  ax3 = plt.subplot(4,2, 4)
  ax3.imshow(x_naive, cmap='gray')
  plt.title('Metodo Naive', fontsize=30)

  ax3 = plt.subplot(4,2, 4)
  ax3.imshow(x_trunc, cmap='gray')
  plt.title('Metodo troncamento', fontsize=30)

  ax3 = plt.subplot(4,2, 5)
  ax3.imshow(x_euristico, cmap='gray')
  plt.title('Metodo Lambda euristico', fontsize=30)

  ax3 = plt.subplot(4,2, 6)
  ax3.imshow(x_disc, cmap='gray')
  plt.title('Metodo Lambda ottimale', fontsize=30)

  ax3 = plt.subplot(4,2, 7)
  ax3.imshow(lambda_norm1, cmap='gray')
  plt.title('Metodo Lambda norma 1', fontsize=30)

  ax3 = plt.subplot(4,2, 8)
  ax3.imshow(x_norm_m, cmap='gray')
  plt.title('Metodo con norma mista', fontsize=30)

  plt.show()

print("Errore relativo immagine corrotta: ", np.linalg.norm(X - B)/np.linalg.norm(X))
print("Errore relativo metodo naive: ", np.linalg.norm(X - x_naive)/np.linalg.norm(X))
print("Errore relativo metodo troncato: ", np.linalg.norm(X - x_trunc)/np.linalg.norm(X))
print("Errore relativo metodo euristico: ", np.linalg.norm(X - x_euristico)/np.linalg.norm(X))
print("Errore relativo metodo discrepanza: ", np.linalg.norm(X - x_disc)/np.linalg.norm(X))
print("Errore relativo metodo norma 1: ", np.linalg.norm(X - lambda_norm1)/np.linalg.norm(X))
print("Errore relativo metodo norma mista: ", np.linalg.norm(X - x_norm_m)/np.linalg.norm(X))
print()
print("PSNR immagine corrotta: ", 20 * np.log10(np.max(B) / ((1 / x.size) * np.linalg.norm(eta))))
print("PSNR metodo naive: ", 20 * np.log10(np.max(x_naive) / ((1 / x.size) * np.linalg.norm(eta))))
print("PSNR metodo troncamento: ", 20 * np.log10(np.max(x_trunc) / ((1 / x.size) * np.linalg.norm(eta))))
print("PSNR metodo euristico: ", 20 * np.log10(np.max(x_euristico) / ((1 / x.size) * np.linalg.norm(eta))))
print("PSNR metodo discrepanza: ", 20 * np.log10(np.max(x_disc) / ((1 / x.size) * np.linalg.norm(eta))))
print("PSNR metodo norma 1: ", 20 * np.log10(np.max(lambda_norm1) / ((1 / x.size) * np.linalg.norm(eta))))
print("PSNR metodo norma mista: ", 20 * np.log10(np.max(x_norm_m) / ((1 / x.size) * np.linalg.norm(eta))))

plot_all_images()