startdic=dict()
pairs=[]
with open('Abusiveword','r',encoding='utf-8') as f:
    lines=f.readlines()
    for line in lines:
        print(line)
        word=line.split()[0]
        score=int(line.split()[1])
        pairs.append((word,score))
    pairs=sorted(pairs,key=lambda x:x[0])
ptr=0
while ptr<len(pairs):
    if pairs[ptr][0] not in startdic:
        ptr2=ptr
        start=ptr
        end=start
        while ptr2<len(pairs) and pairs[ptr2][0][0]==pairs[ptr][0][0]:
            end=ptr2
            ptr2+=1
        startdic[pairs[ptr][0][0]]=(start,end)
    ptr=end+1
with open('startworddic','w',encoding='utf-8') as f:
    for key,val in startdic.items():
        f.write(key[0]+' '+str(val[0])+' '+str(val[1])+'\n')
with open('Abusiveword','w' ,encoding='utf-8') as f:
    for pair in pairs:
        f.write(pair[0]+' '+str(pair[1])+'\n')
