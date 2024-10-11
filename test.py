storage=""
def prefRevCapStr(a):
    if a.isupper() is False :
        global storage
        storage=a
    if len(a)==1:
        return a+" -> "+storage
    b=a.upper()
    return b[-1]+prefRevCapStr(b[:-1]) 

print(prefRevCapStr("Diwali-to-come"))