from pathlib import Path
import argparse

epilog = """With no options, test will read from the config file (./test.conf
by default) automatically test your executable according to the testcase in
`<labID>/test/<problemID>/<testcaseID>` where <labID> and <testcaseID> are two
two-digit numbers and <problemID> is a lowercase letter.

To change the default setting, the following options can be used.

   *`-r` tests your program with random cases if `random.py` or `random.out` is
    provided in `<labID>/test/<problemID>/<testcaseID>/`. When both of these two
    files exist, `random.out` is prefered in consideration of efficiency.
    `random.*` must inherit python class `TestSet` in this file or
    `TestSet.cpp`

   *`-R` behaves the same as `-r` except for using default testcases as well.

   *`-m` helps to match your result with that of other students. Either full
    studentID or the last few digits, if no ambiguity (usually last 4 is
    enough), is acceptable.

   *`-l` helps to list all the available executables you can match with.

   *``

Configuration file describes which problem you are dealing with. It is in the
format of json, containing labID and problemID.
"""


class TestSet:
    """This is the class which all customized test sets should inherit"""

    def __init__(self, labID, problemID):
        self.labID = labID
        self.problemID = problemID

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError()


class DefaultTestSet(TestSet):
    """get test data from given fils in <labID>/test/<problemID>/<testcaseID>"""

    def __init__(self, labID, problemID):
        self.labID = labID
        self.problemID = problemID
        self.data_dir = Path().cwd()/labID/"test"/problemID
        
class Info:
    _RST = "\033[0m"
    _RED = "\033[1;31m"
    _YEL = "\033[1;33m"

    @staticmethod
    def warn(txt):
        print(Info._YEL + "Warn: " + Info._RST + txt)

    @staticmethod
    def error(txt):
        print(Info._RED + "Error: " + Info._RST + txt)


def main(args):
    conf = Path("test.conf")
    if not conf.is_file():
        print("lala")
        Info.warn("Config file not found.")
        yn = input("Confirm to init config? (Y/n)")
        if yn == "n" or yn == "N" or yn == "NO" or yn == "No":
            print("no")
        elif yn == "y" or yn == "Y" or yn == "YES" or yn == "Yes":
            print("yes")
        else:
            Info.error("Invalid option")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="test [-h] [-rRml] EXEC",
        prog="test",
        description="A simple tool for test cpp codes.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-r", "--random", action="store_true", help="random test")
    parser.add_argument(
        "-R", "--Random", action="store_true", help="random test and default test"
    )
    parser.add_argument("-m", "--match", action="store_true", help="matching test")
    parser.add_argument(
        "-l", "--list-available", action="store_true", help="list available executables"
    )
    parser.add_argument("EXEC", help="the executable to be tests")

    main(parser.parse_args())
