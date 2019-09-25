import re
import string
import datrie
from nltk.corpus import words
black_list = []
white_list = []

with open("black_list.txt", 'r') as fff:
    for l in fff:
        black_list.append(l.strip())

with open("white_list.txt", 'r') as fff:
    for l in fff:
        white_list.append(l.strip())

white_trie = datrie.Trie(string.printable)
for url in white_list:
    white_trie[url[::-1]] = url[::-1]

black_trie = datrie.Trie(string.printable)
for url in black_list:
    black_trie[url[::-1]] = url[::-1]

FarmTrie = datrie.Trie(string.ascii_lowercase)
FarmTrie['tw'] = 'tw'
FarmTrie['hk'] = 'hk'
FarmTrie['giga'] = 'giga'
FarmTrie['beetify'] = 'beetify'
FarmTrie['daliulian'] = 'daliulian'
FarmTrie['newtop'] = 'newtop'
FarmTrie['joylah'] = 'joylah'
FarmTrie['asia'] = 'asia'
FarmTrie['blog'] = 'blog'
FarmTrie['baiyongqin'] = 'baiyongqin'
FarmTrie['info'] = 'info'
FarmTrie['keyword'] = 'keyword'
FarmTrie['imama'] = 'imama'
FarmTrie['chinese'] = 'chinese'
FarmTrie['ptt'] = 'ptt'
for w in words.words():
    FarmTrie[w] = w

# inv_trie = datrie.Trie(string.ascii_lowercase)
# for w in FarmTrie:
#     inv_trie[w[::-1]] = w[::-1]

def check_prefix(trie, ss):
    try:
        qq = trie.longest_prefix(ss[::-1])
        return True
    except Exception as e:
        return False


## TODO: 處理'-'號


def word_parser(domain_name, debug=False):
    list_of_keywords = []
    domain_name = re.sub("[0-9]+", "", domain_name)
    piece = domain_name.split('.')
    if debug:
        print("domain_name: ", domain_name)
    for p in piece:
        # if not p.islower():
        #     list_of_keywords += sep_by_cap(p)
        #     continue
        if p in ['net', 'com', 'tw', 'gov', 'org', 'www', '*']:  # 無關域名
            continue
        if len(p) < 5:  # 視為一個單字
            list_of_keywords.append(p)
            continue
        # print("piece: ", p)
        prefix = ""
        while True:
            try:
                prefix = FarmTrie.longest_prefix(p)
            except:
                list_of_keywords.append(p)
                break
            if len(prefix) < 2:
                list_of_keywords.append(p)
                break
            list_of_keywords.append(prefix)
            if prefix == p:
                break
            else:
                p = p[len(prefix):]
            # no_pre = False
            # no_post = False
            # try:
            #     prefix = FarmTrie.longest_prefix(p)
            # except:
            #     no_pre = True
            # try:
            #     postfix = inv_trie.longest_prefix(p[::-1])
            # except:
            #     no_post = True
            # if no_pre and no_post:
            #     # print("no key: ", p)
            #     list_of_keywords.append(p)
            #     break
            # if (no_post and len(prefix) < 2) or (no_pre and len(postfix) < 2) or (len(prefix) < 2 and len(postfix) < 2):
            #     list_of_keywords.append(p)
            #     break
            # if no_post or len(prefix) >= len(postfix):
            #     list_of_keywords.append(prefix)
            #     if prefix == p:
            #         break
            #     else:
            #         p = p[len(prefix):]
            # elif no_pre or len(prefix) < len(postfix):
            #     list_of_keywords.append(postfix[::-1])
            #     if postfix[::-1] == p:
            #         break
            #     else:
            #         p = p[:-len(postfix)]
            # else:
            #     print("QQ")
    list_of_keywords = [i for i in list_of_keywords if len(i) != 1]
    if debug:
        print("words: ", list_of_keywords)
    return list_of_keywords

all_word_set = []
for url in black_list:
    all_word_set += word_parser(url)
all_word_set = set(all_word_set)

def url_detection(url):
    ERROR = 2
    NORMAL = 1
    ABNORMAL = 0
    res = re.search("https?://([a-zA-Z0-9.]+)/?.*", url)
    if res:
        domain_name = res.group(1)
        print(domain_name)
        if check_prefix(black_trie, domain_name):
            return "內容農場網站 (黑名單): " + domain_name
        elif check_prefix(white_trie, domain_name):
            return "正常網站 (白名單): " + domain_name
        else:
            word_set = set(word_parser(domain_name))
            if word_set <= all_word_set:
                return "疑似內容農場網站: " + domain_name
            else:
                return "未知網域: " + domain_name
            # for u in black_list:
            #     if "." in u:
            #         if ".".join(u.split('.')[:-1]) in domain_name:
            #             return ABNORMAL, u
            #     else:
            #         if u in domain_name:
            #             return ABNORMAL, u
            # return NORMAL, domain_name
    else:
        return "URL 格式錯誤"


if __name__ == "__main__":
    # for url in black_list:
    #     word_parser(url, debug=True)
    # print(sep_by_cap("BuzzHand"))
    # word_parser("roys.joylah.co")
    print(url_detection("http://ptt.cc"))