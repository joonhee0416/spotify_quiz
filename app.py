from flask import Flask, render_template, redirect, request, session, make_response,session,redirect
import spotipy
import spotipy.util as util
import time
import os
import random
import pandas as pd

app = Flask(__name__)
app.secret_key = os.urandom(16)

# set to your unique values
# CLI_ID=''
# CLI_SEC=''

API_BASE = 'https://accounts.spotify.com'
REDIRECT_URI = 'http://127.0.0.1:5000/api_callback'
SCOPE = 'user-top-read'
SHOW_DIALOG = True

class Question:
    question= ""
    option1= ""
    option2= ""
    option3= ""
    option4= ""
    correct= ""
    qnum= ""

questionsDefault = ["Who is your top artist?", "What is your top track?"]
globalQuiz = []
user = []

# step 1: user logs in, allows access
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/verify", methods = ['POST'])
def verify():
    #store user information
    user_name = request.form.get("name")
    user_age = request.form.get("age")
    user_occupation = request.form.get("occupation")
    user_reason = request.form.get("reason_use")
    user.append([user_name, user_age, user_occupation, user_reason])


    # authenticate spotify
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = CLI_ID, client_secret = CLI_SEC, redirect_uri = REDIRECT_URI, scope = SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/api_callback")
def api_callback():
    # auth continued
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = CLI_ID, client_secret = CLI_SEC, redirect_uri = REDIRECT_URI, scope = SCOPE)
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    # Saving access token
    session["token_info"] = token_info


    return redirect("quiz")


@app.route("/quiz", methods=['GET', 'POST'])
def quiz():
    session['token_info'], authorized = get_token(session)
    session.modified = True
    if not authorized:
        return redirect('/')

    # get user info from spotipy
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    artistResults = sp.current_user_top_artists(limit=10, time_range='medium_term')['items']
    topArtist = artistResults.pop(0)["name"]
    random.shuffle(artistResults)
    topFourArtists = [0]*4
    topFourArtists[0] = topArtist
    for i in range(1, 4):
        topFourArtists[i] = artistResults[i-1]["name"]
    random.shuffle(topFourArtists)
    songsResults = sp.current_user_top_tracks(limit=10, time_range='medium_term')['items']
    topSong = songsResults.pop(0)["name"]
    random.shuffle(songsResults)
    topFourSongs = [0]*4
    topFourSongs[0] = topSong
    for i in range(1, 4):
        topFourSongs[i] = songsResults[i-1]["name"]
    random.shuffle(topFourSongs)

    questionNumber = 1
    quiz = []
    obj1 = Question()
    obj1.question = questionsDefault[questionNumber - 1]
    obj1.correct = topArtist
    obj1.option1 = topFourArtists[0]
    obj1.option2 = topFourArtists[1]
    obj1.option3 = topFourArtists[2]
    obj1.option4 = topFourArtists[3]
    obj1.qnum = questionNumber
    quiz.append(obj1)
    questionNumber += 1

    obj2 = Question()
    obj2.question = questionsDefault[questionNumber - 1]
    obj2.correct = topSong
    obj2.option1 = topFourSongs[0]
    obj2.option2 = topFourSongs[1]
    obj2.option3 = topFourSongs[2]
    obj2.option4 = topFourSongs[3]
    obj2.qnum = questionNumber
    quiz.append(obj2)
    questionNumber += 1

    globalQuiz.extend(quiz)
    print(quiz)

    return render_template("quiz.html", form=quiz)

# Checks for valid token
def get_token(session):
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if token is present
    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # check expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refresh
    if (is_token_expired):
        sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = CLI_ID, client_secret = CLI_SEC, redirect_uri = REDIRECT_URI, scope = SCOPE)
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid

@app.route("/submit", methods=['POST'])
def submit_quiz():
    # find number of correct answers, append to csv, and reset global variables
    attempts = []
    score = 0
    lenQuiz = len(questionsDefault)
    correctAnswers = []
    global globalQuiz
    correctAnswers.extend(globalQuiz)
    global user

    for idx in range(lenQuiz):
        mcq="mcq"+str(idx+1)
        attempts.append(request.form.get(mcq))

    for idx in range(lenQuiz):
        if correctAnswers[idx].correct == attempts[idx]:
            score += 1
    
    user[0].append(score)
    formatted_user = pd.DataFrame(user)
    formatted_user.to_csv("user_info.csv", mode='a', header=False, 
        index=False, na_rep="NA")
    
    user = []
    globalQuiz = []

    return render_template("results.html", score=score, lenQuiz=lenQuiz)

if __name__ == "__main__":
    app.run(debug=True)