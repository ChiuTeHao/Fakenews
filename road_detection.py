import re
import datetime
import json
from landslide import parser2

test_input = {
    "content": "災情封閉共計1路段如下：1.台8線中橫公路碧綠溪路段(98k)，發生土石流坍方，交通阻斷，預計明(3)日下午17時搶通船班6/2富岡綠島蘭嶼、富岡綠島、後壁湖蘭嶼三條航線停航，預估6/3所有航班正常行駛。",
    "datetime": "2017-06-02",
    "media": "",
    "reporter": "",
    "time": "",
    "title": "不斷更新／雨炸北台　鐵路、航空、客運最新交通狀況懶人包",
    "url": "https://www.ettoday.net/news/20170602/936937.htm"
}


class term(object):
    def __init__(self, word, score, pos, is_reg=False):
        self.word = word
        self.pos = pos
        self.score = score
        self.is_reg = is_reg


typhon_database = json.load(open("typhon_list.json", 'r', encoding='utf8'))
for i in typhon_database:
    typhon_database[i] = [datetime.datetime.strptime(j, "%Y-%m-%d") for j in typhon_database[i]]
verb = {-1:[],
        0:["[中阻]斷", "封[路閉鎖]", "坍方", "受阻", "管制", "決定", "崩落", "沖毀"],
        1:["通行"]
        }
adj = {-1:["定時性?", "預警性?", "預防性?", "間歇性?", "高[乘承]載", "將", "視", "易發生", "考量"],
        0:["多處", "雙向", "緊急", "災[害情]", "南下", "北上", "全面"],
        1:["無法", "淹水"]
        }
noun = ["落石", "土石", "車道", "交通", "橋", "[台投苗北][0-9一二三四五六七八九十廿卅零百甲乙丙丁戊己庚辛壬癸]{1,7}公路",
        "[台投苗北][0-9一二三四五六七八九十廿卅零百甲乙丙丁戊己庚辛壬癸]{1,7}線", r"\d*[.,]?\d*[KkＫ]", "[公道]?路[基段]?", "積水"]

tr_keyword = ["雨", "颱", "風災", "外圍環流"]

event = {
        -1:["結冰", "積雪", "蟹", "演練", "演習", "拒馬", "拓寬", "拆除", "警戒區"],  # and no keyword
        1:["土石.{0,5}沖[刷毀]", "[雨水].{0,5}沖[刷毀]", "路基.{0,5}流失", "路基.{0,5}下陷", "沖刷陷落",
            "[淘掏][空刷]", "[積淹]水", "土石.{0,5}[陷崩]落", "受損", "[崩坍][方塌]", "落石", "土石泥?流",
            "帶來.{0,5}雨量"]
        }
time_pp = ["去年", "前年", "往年", "每當", "每日", "每逢"]

exception = {-1:["不排除", "恢復"],
                1:["再次"]}

grammar = [
            r"<exception(-?\d)>.{0,20}<verb(-?\d)><noun(-?\d)>",  # 
            r"<exception(-?\d)>.{0,10}<verb(-?\d)>",  # 
            r"<adj(-?\d)><verb(-?\d)><noun(-?\d)>",  # 暫時性中斷道路
            r"<adj(-?\d)>[^，、；]{0,4}<noun(-?\d)>[^，、；]{0,4}<verb(-?\d)>",  # 暫時性道路中斷
            r"<noun(-?\d)><adj(-?\d)><verb(-?\d)>",  # 路基嚴重受損
            r"<noun(-?\d)>[^，、；]{0,4}<verb(-?\d)>",  # 道路中斷 路基遭沖刷
            r"<verb(-?\d)><adj(-?\d)><noun(-?\d)>",  # 封閉南下路段
            r"<adj(-?\d)><verb(-?\d)>",  # 暫時性中斷
            r"<verb(-?\d)>[^，、；]{0,1}<verb(-?\d)>", # 中斷雙向道路
            r"<verb(-?\d)><noun(-?\d)>",  # 封閉道路
            r"<verb(-?\d)>[^，、；]{1,2}至[^，、；]{1,2}<noun(-?\d)>"  # 封閉道路
            ]
reg_rule = lambda s: re.search(r"[嘉台投苗北].{1,6}線", s) or re.search(r"[嘉台投苗北中].{1,6}公路", s) or re.search(r"\d*[.,]?\d*[Kk]", s) or re.search(r"嘉[0-9]{1,3}-?[0-9]{0,1}", s)
def reg_rules(s):
    res = []
    a = re.search(r"[台投苗北].{1,6}線", s)
    b = re.search(r"[台投苗北中].{1,6}公路", s)
    c = re.search(r"\d*[.,]?\d*[Kk]", s)
    d = re.search(r"嘉[0-9]{1,3}-?[0-9]{0,1}", s)
    if a:
        res.append((a.group(0), a.span()))
    if b:
        res.append((b.group(0), b.span()))
    if c:
        res.append((c.group(0), c.span()))
    if d:
        res.append((d.group(0), d.span()))
    return res

term_list = []
idx = 0
for s in verb:
    for v in verb[s]:
        idx += 1
        tt = term(v, s, "<verb"+str(s)+">", is_reg=True if ('[' in v) or ('?' in v) else False)
        term_list.append(tt)
for s in exception:
    for a in exception[s]:
        idx += 1
        tt = term(a, s, "<exception"+str(s)+">", is_reg=True if ('[' in a) or ('?' in a) else False)
        term_list.append(tt)
for s in adj:
    for a in adj[s]:
        idx += 1
        tt = term(a, s, "<adj"+str(s)+">", is_reg=True if ('[' in a) or ('?' in a) else False)
        term_list.append(tt)
for n in noun:
    idx += 1
    tt = term(n, 0, "<noun0>", is_reg=True if ('[' in n) or ('?' in n) or ('.' in n) else False)
    term_list.append(tt)




def replace_term(term_list, ss):
    matched_list = []
    for t in term_list:
        if t.is_reg:
            temp = re.search(t.word, ss)
            if temp is None:
                pass
            else:
                keyword = temp.group(0)
                position = temp.span()
                matched_list.append((keyword, position))
                new_ss = re.sub(t.word, t.pos, ss)
                ss = new_ss
        else:
            if t.word in ss:
                position = ss.find(t.word)
                matched_list.append((t.word, position, position+len(t.word)))
                new_ss = ss.replace(t.word, t.pos)
                ss = new_ss
    return ss, matched_list


def get_score(replace_sentence, g):
    p = re.compile(g)
    matched_scores = []
    for m in p.finditer(replace_sentence):
        matched_scores.append((sum([int(i) for i in m.groups()]), m.start(), m.end()))
    if len(matched_scores) != 0:
        return max(matched_scores, key=lambda x:x[0])
    else:
        return None


def judge(sentence, pre_has_reg=False):
    related = False
    reason = []
    matched_grammar = "None"
    red_keywords = []
    if pre_has_reg or reg_rule(sentence):
        red_keywords += reg_rules(sentence)
        pre_has_reg = True
        replace_sentence, matched_list = replace_term(term_list, sentence)
        if sentence == replace_sentence:
            reason.append("no keyword matched")
            return related, pre_has_reg, reason, red_keywords
        for g in grammar:
            temp = get_score(replace_sentence, g)
            if not (temp is None):
                score, start, end = temp
                if pre_has_reg == False:
                    for time_keyword in time_pp:
                        if time_keyword in sentence:
                            reason.append("past time: " + time_keyword)
                            red_keywords.append((time_keyword, (sentence.find(time_keyword), sentence.find(time_keyword)+len(time_keyword))))
                            score -= 1
                            break
                if score >= 0:
                    matched_grammar = g + " : " + replace_sentence
                    reason.append(matched_grammar)
                    related = True
                    break
                elif score < 0:
                    break
    else:
        reason.append('no "公[尺分釐厘]" or "毫米"')
    return related, pre_has_reg, reason, red_keywords


def convert(result):
    index = []
    for w, s in result:
        ss, ee = s
        for i in range(ss, ee):
            index.append(i)
    return index


def check_interval(k, intervals):
    for i in intervals:
        if i[0] <= k < i[1]:
            return True
    return False

def check_interval2(k, intervals):
    for i in intervals:
        if i[0] <= k < i[1]:
            return i[2]
    return -1

def road_detection(news_structure):
    red_keywords = []
    text = news_structure["content"]
    title = news_structure["title"]
    url = news_structure["url"]
    pub_time = news_structure['datetime']
    if pub_time != "":
        pub_date_time = datetime.datetime.strptime(pub_time, "%Y-%m-%d")
    else:
        pub_date_time = ""
    results = []
    # check tr_keyword
    have_tr_keyword = False
    for tr in tr_keyword:
        if tr in title+text:
            have_tr_keyword = True
            iii = (title+text).find(tr)
            while iii >= 0:
                if "可能" in (title+text)[iii-5:iii]:
                    have_tr_keyword = False
                    break
                else:
                    iii = (title+text).find(tr, iii+1)
            if have_tr_keyword:
                red_keywords.append((tr, ((title+text).find(tr), (title+text).find(tr) + len(tr))))
            break
    if not have_tr_keyword:
        return [(s, 0, -1) for s in re.split("。|\?|\!", text)], []

    # check event
    changed = False
    event_related = 0
    for score, events in event.items():
        for e in events:
            res = re.search(e, text+title)
            if res:
                red_keywords.append((res.group(0), res.span()))
                event_related += score
                changed = True
    if changed == False:
        event_related = -1 
    if event_related < 0:
        indices = convert(red_keywords)
        return [(s, 0, -1) for s in re.split("。|\?|\!", text)], []
    
    sentences = re.split("。|\?|\!", text)
    reasons = []
    temptext = text
    attr_table = []
    for idsen, sen in enumerate(sentences):
        comma = "。"
        if len(sen) < len(temptext):
            comma = temptext[len(sen)]
        if len(sen) + 1 != len(temptext):
            temptext = temptext[len(sen)+1:]
        if sen == "":
            continue
        r_s = []
        pre_has_reg = False
        for ids, s in enumerate(sen.split("；")):
            # 檢查過去事件
            have_past_event = False
            for past_event, occ_dates in typhon_database.items():
                if past_event in s:
                    have_past_event = True
                    if pub_date_time != "":
                        for occ_date in occ_dates:
                            if occ_date - datetime.timedelta(days=14) < pub_date_time < occ_date + datetime.timedelta(days=60):
                                have_past_event = False
                                break
                    if have_past_event == False:
                        break
            is_related = False
            related, pre_has_reg, reason, red_keyword = judge(s, pre_has_reg=pre_has_reg)
            red_keywords += red_keyword
            if related:
                reasons.append(reason)
                is_related = True
                is_related = is_related and not have_past_event
                attr = parser2([(s, 'S')], "1890-01-01")
                interval = []
                for iii, i in enumerate(attr):
                    for jjj, j in enumerate(i):
                        if j == "None" or j == "none":
                            continue
                        j = j.strip()
                        if re.match("18[0-9][0-9]-[0-9][0-9]-[0-9][0-9]", j):
                            j = j.split(' ')[-1]
                            attr[iii][jjj] = j
                        print(j)
                        start = s.find(j)
                        end = start + len(j)
                        interval.append((start, end, jjj))
                attr_table += attr
                if ids != 0:
                    results += [("；", 0, -1)]
                results += [(w, 2 if check_interval(k, interval) else 1, check_interval2(k, interval)) for k, w in enumerate(s)]
            else:
                if ids != 0:
                    results += [("；", 0, -1)]
                results += [(w, 0, -1) for w in s]
            r_s.append(str(int(is_related)))
        # print(attr_table)
        # if '1' in r_s:
        #     indices = convert(red_keywords)
        #     results += [(sen, 1)]
        # else:
        #     indices = convert(red_keywords)
        #     results += [(sen, 0)]
        results += [(comma, 0, -1)]
    return results, attr_table


if __name__ == "__main__":
    # print(road_detection(test_input))
    pass
