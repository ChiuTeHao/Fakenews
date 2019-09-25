import re
class AbusiveWordDetection:
    def __init__(self):
        self.abusivewords=list()
        self.abusivescore=list()
        self.startworddic=dict()
        self.pattern=re.compile('[^。!?]+')
        with open('Abusiveword','r',encoding='utf-8') as f:
            lines=f.readlines()
            for line in lines:
                word=line.split()[0]
                score=int(line.split()[1])
                self.abusivewords.append(word)
                self.abusivescore.append(score)
        with open('startworddic','r',encoding='utf-8') as f:
            lines=f.readlines()
            for line in lines:
                tmplist=line.split()
                self.startworddic[tmplist[0]]=(int(tmplist[1]),int(tmplist[2]))
    def stringmatch(self,sentence):
        result=[]
        data=''
        i=0
        while i<len(sentence):
            if sentence[i] in self.startworddic:
                start=self.startworddic[sentence[i]][0]
                end=self.startworddic[sentence[i]][1]
                for j in range(start,end+1):
                    length=len(self.abusivewords[j])
                    if sentence[i:i+length]==self.abusivewords[j]:
                        if data!='':
                            result.append((data,0,0))
                            data=''
                        result.append((sentence[i:i+length],2,self.abusivescore[j]))
                        i=i+length-1
                        break
                    elif j==end:
                        data+=sentence[i]
            else:
                data+=sentence[i]
            i+=1
        if data!='':
            result.append((data,0,0))
        return result
                
    def title_detection(self,title):
        nonzerocnt=0
        totalsum=0
        result=self.stringmatch(title)
        for pair in result:
            if  pair[2]!=0:
                totalsum+=pair[2]
                nonzerocnt+=1
        score=0
        if nonzerocnt==0:
            score=0
        else:
            score=totalsum/nonzerocnt
        return result,round(score,3)    
    def content_detection(self,data):
        contents=data['content']
        title=data['title']
        flag=False
        sentences=re.findall(self.pattern,contents)
        result=[]
        for sentence in sentences:
                result+=self.stringmatch(sentence)
                result.append(('。',0,0))
        nonzerocnt=0
        totalsum=0
        for pair in result:
            if  pair[1]!=0:
                totalsum+=pair[1]
                nonzerocnt+=1
        score=0
        if nonzerocnt==0:
            score=0
        else:
            score=totalsum/nonzerocnt
        return result,round(totalsum/nonzerocnt,3)

detector=AbusiveWordDetection()
while True:
    string1=input('請輸入標題:')
    result1,score1=detector.title_detection(string1)
    string2=input('請輸入內文:')
    result2,score2=detector.title_detection(string2)
    print(result1,score1)
    print(result2,score2)
