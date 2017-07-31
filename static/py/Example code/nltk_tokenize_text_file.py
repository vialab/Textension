import nltk

def tokenizeTextFile(fname):

    file_content = open(fname).read()
    tokens = nltk.word_tokenize(file_content)
    print tokens
