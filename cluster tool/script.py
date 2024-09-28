import time
import torch

for i in range(1000):
    time.sleep(0.2)
    a = torch.randn(5, 5)
    b = torch.randn(5, 5)

    c = a + b

    print(f"tensor 'a': {a}")
    print(f"tensor 'b': {b}")
    print(f"tensor 'a + b': {c}")
    

print("success")