from flask import Flask, render_template, request, redirect
from markupsafe import Markup
import json
import requests
from bs4 import BeautifulSoup
from random import randint, shuffle

app = Flask(__name__)

def fetch_words_from_google_doc(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    words = {}

    for item in soup.find_all('p'):
        text = item.get_text().strip()
        if '/' in text:
            word, definition = text.split('/', 1)
            words[word.strip()] = definition.strip()

    return words

words = fetch_words_from_google_doc("https://docs.google.com/document/u/2/d/1InWk9gTECwuWmbc7j7HaJd9jQZTt11Ep8muFoHfPLUY/pub?pli=1")

def generate_choice(words, wordfreq):
    rnds = []
    choicelist = []
    for i in enumerate(words):
        try:
            wordfreq[i[1]]
        except KeyError:
            wordfreq[i[1]] = 3
        choicelist += [i[0]] * wordfreq[i[1]]

    while len(rnds) < 4:
        rnd = randint(0, len(choicelist) - 1)
        if choicelist[rnd] not in rnds:
            rnds.append(choicelist[rnd])
    return rnds

def generate_qa(question_no, words, wordfreq):
    rnds = generate_choice(words, wordfreq)
    ans_no = rnds[0]
    quiz_word = list(words)[ans_no]
    qa = "<p>問題: " + str(question_no) + "<br/>單字 '" + quiz_word + "' 的意思是什麼？</p><p></p>"
    shuffle(rnds)
    for i in range(4):
        qa += "<p>" + str(i + 1) + ". " + words[list(words)[rnds[i]]] + "</p>"
    return ans_no, rnds, qa

def savewordfreq(wordfreq):
    with open(user + ".json", "w", encoding='utf-8') as f:
        json.dump(wordfreq, f)

@app.route("/", methods=['GET', 'POST'])
def submit_name():
    global wordfreq, user, question_no, score, total_questions
    question_no = 1
    score = 0
    if request.method == 'POST':
        user = str(request.form['name'])
        total_questions = int(request.form['total_questions'])

        try:
            with open(user + ".json", "r", encoding='utf-8') as f:
                wordfreq = json.load(f)
        except IOError:
            freq = 3
            wordfreq = {word: freq for word in words}
        return redirect('/test')
    else:
        return render_template('index.html')

@app.route("/test", methods=['GET', 'POST'])
def submit_answer():
    global question_no, rnds, score, ans_no, quiz_word, qa, last_question_correct

    if request.method == 'POST':
        try:
            ans = int(request.form['answer'])
            # 檢查答案是否在有效範圍內
            if ans < 1 or ans > 5:  # 假設有五個選項，5 是結束遊戲的選項
                return render_template('test.html', question_and_choices=Markup(qa), result=Markup("<p>您的答案無效！請重新輸入</p>"))
        except ValueError:
            return render_template('test.html', question_and_choices=Markup(qa), result=Markup("<p>您的答案無效！請重新輸入</p>"))

        if ans == 5:  # 假設 5 是結束遊戲的選項
            savewordfreq(wordfreq)
            result = '遊戲結束'
            result += '<p>得分: ' + str(score) + '</p>'
            return render_template('end.html', question_and_choices='', result=Markup(result), last_question_result=last_question_correct)

        if ans in [1, 2, 3, 4]:
            if rnds[ans - 1] == ans_no:
                result = '正確！'
                score += 1
                last_question_correct = True  # 標記最後一題正確
                if wordfreq[quiz_word] > 1:
                    wordfreq[quiz_word] -= 1
            else:
                result = '錯誤，正確答案是 "' + words[quiz_word] + '"'
                wordfreq[quiz_word] += 1
                last_question_correct = False  # 標記最後一題錯誤

        question_no += 1

        if question_no > total_questions:  # 如果已經超過問題數量
            savewordfreq(wordfreq)
            result = '遊戲結束'
            result += '<p>得分: ' + str(score) + '</p>'
            return render_template('end.html', question_and_choices='', result=Markup(result), last_question_result=last_question_correct)

        ans_no, rnds, qa = generate_qa(question_no, words, wordfreq)
        quiz_word = list(words)[ans_no]
        return render_template('test.html', question_and_choices=Markup(qa), result=Markup(result))

    else:  # GET 請求
        ans_no, rnds, qa = generate_qa(question_no, words, wordfreq)
        quiz_word = list(words)[ans_no]
        last_question_correct = None  # 重置最後一題結果
        return render_template('test.html', question_and_choices=Markup(qa), result='')

if __name__ == '__main__':
    app.run(debug=True)


