import sys
sys.path.insert(0, './sources')
from data_loader import data_loader
from model import model
import numpy as np



class lstm_model(object):
    def __init__(self,model_path = None, max_sentence_length = 15):
        self.max_sentence_length = max_sentence_length
        dd = data_loader(data_dir = "./data/",\
                batch_size = 128,\
                val_ratio = 0.1,\
                word_dict = "./vocab_file/vocab.txt",\
                max_length = max_sentence_length,\
                testing= True)

        self.model_ = model(word_embedding_file = "./vocab_file/word_vec_array.npy",\
                        data_loader = dd)

        self.model_.build_model(max_sentence_length =  max_sentence_length,\
                            gru_dim = 64)

        self.model_.train_model(epoch = 0,\
                            learning_rate = 0.001,\
                            training = False)

        self.model_.restore_model(model_path+"/model-BEST.ckpt")

        self.key_word_sets = []
        
        with open(model_path+"/keywords.txt",'r',encoding="utf-8") as f:
            lines = f.readlines()
        
        for l in lines:
            self.key_word_sets.append(l.replace("\n",""))

                
        
    def predict(self, sentence):
        return self.model_.predict(sentence)

    def other_stats(self,sents, labels, attentions):
        alert_word = dict()
        question_sentence_count = 0
        all_sentence_number = 0
        all_word_number = 0
        for sentence_num in range(len(labels)):
            all_sentence_number += 1
            if labels[sentence_num] == 1:
                question_sentence_count += 1
            out_len = min(len(sents[sentence_num]), len(attentions[sentence_num]))
            for word_num in range(out_len):
                all_word_number += 1
                word = sents[sentence_num][word_num]

                if attentions[sentence_num][word_num] >= 0.2 and labels[sentence_num] == 1:
                    if word in alert_word:
                        score =  alert_word[word]
                        score += 1 
                        alert_word[word] = score
                    else:
                        alert_word[word] = 1    
                elif attentions[sentence_num][word_num] >= 0.2 and labels[sentence_num] == 0:
                    if word in alert_word:
                        score =  alert_word[word]
                        score += 1 
                        alert_word[word] = score
                    else:
                        alert_word[word] = 1
                
        result = []
        result.append("總共包含有找到主題的句子"+str(question_sentence_count)+"句。")
        key_word_count = 0
        for k, v in alert_word.items():
            result.append("找到關鍵字"+k+"出現過"+str(v)+"次。")
            key_word_count += 1
        score = self.get_score(key_word_count, question_sentence_count, all_word_number, all_sentence_number)
        result.append("分數: "+str(score))
        
        return result

                    
    def predict_new_server(self, title, content):

        final_result = []
        sentences = [title, content]

        for sentence in sentences:


            if sentence != '':
        
                sents, labels, attentions, probs = self.model_.predict(sentence)
                

                this_result = []
                has_result = False

                for sentence_num in range(len(labels)):
                    out_len = min(len(sents[sentence_num]), len(attentions[sentence_num]))
                    for word_num in range(out_len):
                        
                        
                        if sents[sentence_num][word_num] in self.key_word_sets:
                            if attentions[sentence_num][word_num] < 0.5:
                                attentions[sentence_num][word_num] += (1 - attentions[sentence_num][word_num]) * 0.5 \
                                    + attentions[sentence_num][word_num]
                        

                        if attentions[sentence_num][word_num] >= 0.5 and labels[sentence_num] == 1:
                            has_result = True
                            this_result.append((sents[sentence_num][word_num],2))
                        elif attentions[sentence_num][word_num] <= 0.5 and labels[sentence_num] == 1:
                            has_result = True
                            this_result.append((sents[sentence_num][word_num],1))
                        elif attentions[sentence_num][word_num] >= 0.5 and labels[sentence_num] == 0:
                            this_result.append((sents[sentence_num][word_num],3))
                        else:
                            this_result.append((sents[sentence_num][word_num],0))

                print( attentions )
                
                
                result = self.other_stats(sents, labels, attentions)


                
                if has_result == True:
                    final_result.append([this_result,result])
                else:
                    final_result.append(["",""])

                

                    
                
            else:

                final_result.append([[],[('',''),['']]])

        #print(final_result)
        
            
        return final_result

    def get_score(self, key_word_count = 0, question_sentence_count = 0, all_word_number = 0, all_sentence_number = 0):
        max_score = 10
        final_score = 0
        final_score += question_sentence_count / all_sentence_number * 10
        final_score += key_word_count / all_word_number * 10
        return round(min(max_score, final_score),3)

        








        
        


   
