import re
import os
if os.path.exists('lastlabel'):
    with open('lastlabel','r') as f:
        linenumtxt=f.readline()
        linenum=int(linenumtxt)
    with open('Abusiveword','r',encoding='utf-8') as f:
        lines=f.readlines()
        lastlabel=0
        for i in range(linenum,len(lines)):
            labeltxt=input(lines[i]+' Please give it label : ')
            lines[i]=re.sub('\n','',lines[i])+' '+labeltxt
            lastlabel=i
            with open('Abusiveword-3','a+',encoding='utf-8') as f:
                f.write(lines[i]+'\n')
            with open('lastlabel','w') as f:
                f.write(str(lastlabel))
else:
    with open('Abusiveword','r',encoding='utf-8') as f:
        lines=f.readlines()
        lastlabel=0
        for i in range(len(lines)):
            labeltxt=input(lines[i]+' Please give it label : ')
            if labeltxt!='-1':
                lines[i]=re.sub('\n','',lines[i])+' '+labeltxt
                lastlabel=i
                with open('Abusiveword-3','a+',encoding='utf-8') as f:
                    f.write(lines[i]+'\n')
                with open('lastlabel','w') as f:
                    f.write(str(lastlabel))

