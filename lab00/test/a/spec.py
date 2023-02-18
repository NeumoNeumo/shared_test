from test import RandomTestSetBase
import random

def get_config():
    return {"timeout": 1}

class RandomTestSet(RandomTestSetBase):
    def __init__(self, labID, problemID, case_num):
        super().__init__(labID, problemID, case_num)
    
    def generate(self):
        a = random.randint(0, 255)
        b = random.randint(0, 255)
        tc_name = "rand" + str(self.cnt)
        tc_input = f"{a} {b}"
        tc_output = f"{a+b}"
        return (tc_name, tc_input, tc_output)

        
        
