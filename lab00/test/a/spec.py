from test import TestSet
import random

class RandomTestSet(TestSet):
    def __init__(self, labID, problemID, case_num):
        super().__init__("Random", labID, problemID)
        self.case_num = case_num
        self.cnt = 0
        self.num = case_num
    
    def __len__(self):
        return self.num
    def __next__(self):
        if self.cnt == self.num:
            raise StopIteration
        a = random.randint(0, 255)
        b = random.randint(0, 255)
        tc_name = "rand" + str(self.cnt)
        tc_input = f"{a} {b}"
        tc_output = f"{a+b}"
        self.cnt += 1
        return (tc_name, tc_input, tc_output)

        
        
