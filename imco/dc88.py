
def divide(a, b):
    if b > a-b:
        return 1
    else:
        return 1 + divide(a-b, b)


