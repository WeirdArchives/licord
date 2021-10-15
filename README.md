# licord
An almost dependency-less, synchronous Discord gateway library meant for my personal use.

# Installation
```
pip install git+https://github.com/oliver-ni/erlpack
pip install git+https://github.com/h0nde/licord
```

# Usage
```python
from licord import Gateway, find_token

gateway = Gateway(token=find_token())

while True:
    payload = gateway.recv()
    print(payload)
```
