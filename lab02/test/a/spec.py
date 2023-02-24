from test import RandomTestSetBase
import random

def get_config():
    return {"timeout":1}

class RandomTestSet(RandomTestSetBase):
    def generate(self):
        output = ""
        verifier = ""
        t = random.randint(1, 100)
        output += str(t)
        for _ in range(t):
            n = random.randint(1, 10**9)
            output += "\n" + str(n)
            if n % 6 == 0:
                verifier += "Bob\n"
            else:
                verifier += "Alice\n"

        return ("rand", output, verifier)
