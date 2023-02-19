from test import StrReader


def get_config():
    return {"timeout": 1}


def verifier(input, output) -> bool:
    sr = StrReader(input)
    N = int(sr.read())
    boy_name = []
    girl_name = []
    boy_pref = {}
    girl_pref = {}
    for _ in range(N):
        boy_name.append(sr.read())
    for _ in range(N):
        girl_name.append(sr.read())
    for boy in boy_name:
        pref = []
        for _ in range(N):
            pref.append(sr.read())
        boy_pref[boy] = pref
    for girl in girl_name:
        pref = []
        for _ in range(N):
            pref.append(sr.read())
        girl_pref[girl] = pref

    sr = StrReader(output)
    bg = {}
    gb = {}
    for _ in range(N):
        boy = sr.read()
        girl = sr.read()
        bg[boy] = girl
        gb[girl] = boy

    for boy in boy_name:
        for girl in girl_name:
            if boy_pref[boy].index(girl) < boy_pref[boy].index(bg[boy]) and girl_pref[
                girl
            ].index(boy) < girl_pref[girl].index(gb[girl]):
                return False

    return True
