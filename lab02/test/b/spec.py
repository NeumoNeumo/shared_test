from test import RandomTestSetBase
import random

def get_config():
    return {"timeout":1}

class RandomTestSet(RandomTestSetBase):
    def generate(self):
        output = ""
        verifier = ""
        n = random.randint(1, 10**9)
        k = random.randint(1, n)
        output = f"{n} {k}"
        verifier = str(2 * min(k, n+1-k))
        if n == 1:
            verifier = "1"
        return ("rand", output, verifier)

