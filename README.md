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

## More

Any attempt to ease coding burden and to accelerate the workflow is welcomed!
Code style for python codes is "[black](https://github.com/psf/black)" and that
for cpp is "[llvm](https://llvm.org/docs/CodingStandards.html)"


