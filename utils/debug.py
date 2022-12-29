from core.Constants import DEBUG


def dprint(*args):
    if DEBUG:
        print(*args)
