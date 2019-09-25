import random
import re
output=[]
with open('Abusiveword','r',encoding='utf-8') as f:
    lines=f.readlines()
    for line in lines:
        word=line.split()[0]
        output.append(word)
with open('Abusiveword','w',encoding='utf-8') as f:
    for word in output:
        f.write(word+'\n')
