BAD_WORDS = ["시발","병신","개새키","ㅅㅂ","ㅂㅅ","ㅄ","니애미", "조까","섹스","보지","개새키","창녀","창련","븅신"]

def contains_bad_word(text):
    text = text.lower()
    return any(word in text for word in BAD_WORDS)


