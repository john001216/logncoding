# korean_gampe.py
# utils.py

from googletrans import Translator
import random
from sentence_transformers import SentenceTransformer, util


def kor_pos_tagger(kor_sentence, model):
    korean_sentence_pos = model.analyze(kor_sentence)
    return korean_sentence_pos

def translate_english_to_korean(text):
    translator = Translator()
    try:
        translation = translator.translate(text, src='en', dest='ko')
        return translation.text
    except Exception as e:
        print("Error occurred during translation:", e)
        return None
    
def translate_korean_to_english(text):
    translator = Translator()
    try:
        translation = translator.translate(text, src='ko', dest='en')
        print(translation)
        return translation.text
    except Exception as e:
        print("Error occurred during translation:", e)
        return None

def easy_form(tagged_pos):
    pos_list = []
    for i in range (len(tagged_pos[0][0])):
        element = []
        element.append(tagged_pos[0][0][i].form)
        element.append(tagged_pos[0][0][i].tag)
        pos_list.append(element)
    return pos_list

def get_J(pos_list):
    essential_pos = ['JKS', 'JKC', 'JKG', 'JKO', 'JKB', 'JKV', 'JKQ', 'JX', 'JC']
    J_list = []
    for i in range(len(pos_list)):
        if pos_list[i][1] in essential_pos:
            J_list.append(pos_list[i])
    return J_list
# [['그', 'MM'], ['사람', 'NNG'], ['은', 'JX'], ['학교', 'NNG'], ['로', 'JKB'], ['달려가', 'VV'], ['고', 'EC'], ['있', 'VX'], ['어', 'EF']]        
# [['은', 'JX'], ['로', 'JKB']]

def replace_J(sentence, J_list):
    # num_deleted_J = random.randint(1, 2)
    # if num_deleted_J > len(J_list):
    #     num_deleted_J = 1
    num_deleted_J = 1
    random_J_list = random.sample(J_list , num_deleted_J)
    
    quiz_sentence = sentence
    for i in range(0, len(random_J_list)):
        quiz_sentence = quiz_sentence.replace(random_J_list[i][0], '_')
    
    return quiz_sentence

def remove_J(sentence, J_list):
    # num_deleted_J = random.randint(1, 2)
    # if num_deleted_J > len(J_list):
    #     num_deleted_J = 1
    num_deleted_J = 1
    random_J_list = random.sample(J_list , num_deleted_J)
    
    quiz_sentence = sentence
    for i in range(0, len(random_J_list)):
        quiz_sentence = quiz_sentence.replace(random_J_list[i][0], '_')
    
    return quiz_sentence

def sim_score_bw_sentences(sentence1, sentence2):
    model_name = 'roberta-base-nli-mean-tokens'
    model = SentenceTransformer(model_name)

    # Get sentence embeddings
    embeddings = model.encode([sentence1, sentence2], convert_to_tensor=True)
    # print(len(embeddings[0]))
    # Calculate cosine similarity
    similarity_score = util.pytorch_cos_sim(embeddings[0], embeddings[1])
    print("Similarity Score:", similarity_score.item())

    return similarity_score.item()

def make_options(my_list):
    candiates = ['에게', '로써', '을', '를', '에게']
    my_set = set(my_list)
    while len(my_set) < len(my_list):
        my_set.add(random.choice(candiates))

    my_list = list(my_set)

    random.shuffle(my_list)

    return my_list