This repo is created to share programs, matching test codes, unit test code for
students to avoid duplicated workload.

## File hierarchy
Illustration:
```
.
├── lab01
│   ├── 12112807
│   │   ├── a
│   │   └── b
│   ├── 23333333
│   │   ├── b
│   │   └── d
│   └── test
├── lab02
│   ├── 23333333
│   │   └── z
│   └── test
└── README.md
```
*Remark*: 
- `lab01` and `lab02` represent lab IDs.
- `12112807` and `23333333` are student IDs.
- `a`, `b`, `d`, `z` are executables and the letter indecates the index of the
  problem
- `test` stores testcase files and testcase generators. See more in `python
  test.py --help`

## Example
Compile this simple program to get an executable `add` in this directory.
```c
#include<stdio.h>

int main() {
  int a, b, c;
  scanf("%d %d", &a, &b);
  if(c >= 100){
    c += 1;
  }
  printf("%d", a + b);
  return 0
}
```
`lab00` is for usage of helping developemnt and problem `a` requires an
algorithm to add two numbers. Try out using
``` bash
python test.py -R5 lab00 a add
```
to run the default testset in `lab00/test/a` and 5 random test cases.
And
```bash
python test.py -r10 -m12112807 lab00 a add
```
will perform matching test between `add` and the counterpart of Yuan Xu on 10
random generated testcases.

It is recommended to use a script(bash/bat) file to avoid input the cumbersome
command repeatedly.

See `python test.py --help` for details.

## More

Any attempt to ease coding burden and to accelerate the workflow is welcomed!
Code style for python codes is "[black](https://github.com/psf/black)" and that
for cpp is "[llvm](https://llvm.org/docs/CodingStandards.html)"


