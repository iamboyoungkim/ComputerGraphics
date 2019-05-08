import numpy as np

M = np.array([i+2 for i in range(25)])
print(M)
print("\n")

M = M.reshape(5,5)
print(M)
print("\n")

for i in range(1,4):
    for j in range(1,4):
        M[i][j] = 0

print(M)
print("\n")

M = M @ M
print(M)
print("\n")

v = M[0]

sum = 0
for i in range(5):
    sum += v[i]*v[i]

x = np.sqrt(sum)

print(x)
