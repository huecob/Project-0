"""Main Server!! Woohoo!"""

from flask import (Flask, render_template, request, flash, get_flashed_messages, session, redirect, jsonify)
from datetime import datetime, timedelta
from model import connect_to_db, db, User, GameSession, Difficulties, GameDifficulty, Game
import random
import crud
import json

from jinja2 import StrictUndefined

app = Flask(__name__)
app.secret_key = "dev"
app.jinja_env.undefined = StrictUndefined

tips = ["Enemies speed up as scores increase! Be careful for the unexpected!",
        "While called so lovingly, Dunderhead can definitely outsmart their foes!",
        "UFOs are relentless in trying to obtain our precious technology! Keep A.D. charged and moving.",
        "Collecting health-up items doesn't increase points so it might be a good idea to heal up before moving in for those points!"]


@app.route('/')
def show_homepage():
    """Landing page"""

    highest_score = crud.get_highest_score()
    user = highest_score.user_id
    user_id = crud.get_users_by_id(user)

    user_name = user_id.user_display_name

    friendly_tip = random.choice(tips)

    return render_template('homepage.html',user=user, user_name=user_name, highest_score=highest_score, friendly_tip=friendly_tip)
    
@app.route('/log-in')
def render_login_page():

    return render_template('/login-page.html')

@app.route('/handle-login', methods=["POST"])
def login_user():
    """This logs the user in"""

    email = request.form.get("email")
    password = request.form.get("password")

    user = crud.get_user_by_email(email)

    if user.user_email != email or user.user_password != password:
        flash("Sorry yo! Something's up with your login info. :P")
    else:
        flash("Welcome back friend!")
        session['email'] = user.user_email
        session['user_id'] = user.user_id
    
    return redirect('/')

@app.route('/registration')
def show_registration():
    """Displays the registration page"""

    return render_template('registration.html')

@app.route('/profile/search')
def show_profile_search():
    """Shows the results of a profile search"""

    keyword = request.args.get('keyword')

    target_string = keyword[1:len(keyword) -1]

    if keyword == "Search Profiles!":
        users = crud.get_users()
        user_data = [(user.user_display_name, user.user_id)for user in users]
        
    elif len(keyword) > 0:
        users = crud.find_users_like(target_string)
        user_data = [(user.user_display_name, user.user_id) for user in users]
    else:
        user_data = [("There are no users that match.", None)]

    return render_template('profile-search-results.html', user_data=user_data)


@app.route('/register-user', methods = ['POST'])
def create_user():
    """Registers a user, shoots them to the DB"""

    email = request.form.get("email")
    password = request.form.get("password")
    display_name = request.form.get("display name")

    if crud.check_bad_word(display_name) == False:
        if not crud.get_user_by_email(email):
         flash("Saddle up, Player!")
         user = crud.create_user(email,password, display_name)
        db.session.add(user)
        db.session.commit()

        user = crud.get_user_by_email(email)
        user_id = user.user_id

        session['user_id'] = user_id
        session['email'] = email

        return redirect('/')

    elif crud.check_bad_word(display_name) == True:
        flash("Please keep the language clean!!")
    
    elif crud.get_user_by_email(email):
        flash("Multiverse Error: There's someone else with the email. 🤪")

    return redirect('/registration')

@app.route('/player-profile/<user_id>')
def show_profile(user_id):
    """Loads Player Profile"""

    user = crud.get_users_by_id(user_id)

    user_high_score = crud.get_user_highest_score(user_id)

    if user_high_score is not None:
         score = user_high_score.score
    else:
        score = "No games yet!"

    return render_template('player-profile.html', user=user, score=score)

@app.route('/user-score-data')
def get_user_score_data():
    """Handle sending user score data to FE"""

    user = crud.get_user_by_email(session['email'])

    user_id = user.user_id

    user_high_score = crud.get_user_highest_score(user_id)

    return jsonify({ "score": user_high_score})

@app.route('/update-display-name', methods=['POST'])
def update_name():
    """Updates display name"""

    user_id = request.json['user_id']
    user_id = int(user_id)

    newName = request.json['updated_name']

    crud.update_display_name(user_id, newName)

    return jsonify({"code": "Success",
                    "name": newName})

@app.route('/game-1')
def play_game1():
    """This will be where your game will live"""

    user = crud.get_user_by_email(session['email'])
    user_name = user.user_display_name

    return render_template('game-page-1.html', user_name=user_name)

@app.route('/logout')
def logout_user():
    """handles the logout"""

    session.pop('email', None)
    session.pop('user_id', None)

    flash("Thanks for playing!")

    return redirect('/')

@app.route('/scores', methods=['POST'])
def handle_score():
    """Collects Game Session Data"""

    # user_ID, game_ID, score

    user = crud.get_user_by_email(session['email'])

    user_id = user.user_id
    game_id = request.json["game_id"]
    score = request.json["userScore"]
    time_played = request.json["seconds"]

    game_session = GameSession(session_date = datetime.now(), 
                               user_id = user_id, 
                               game_id = game_id, 
                               score = score, 
                               time_played = time_played)
    
    db.session.add(game_session)
    db.session.commit()

    return "Score receivced: {}".format(score)

@app.route('/game-2')
def play_game2():
    """Let's play game 2!"""

    return render_template('game-page-2.html')

@app.route('/game-3')
def play_game3():
    """Let's play game 3!"""

    return render_template('game-page-3.html')

@app.route('/user-metrics/<user_id>')
def deliver_user_metrics(user_id):
    """Deliver metrics"""

    retval = {}

    user_data = crud.last_7_days(user_id)

    for data in user_data:
        dates = data['session_date']
        if dates not in retval:
            retval[dates] = data['score']
        elif retval[dates]:
            retval[dates] += data['score'] 

    return jsonify(retval)

@app.route('/game-1-user-metrics/<user_id>')
def deliver_game1_user_metrics(user_id):
    """Delivers a dictionary with values of game data organized game_ids as keys"""

    retval = {}

    user_data = crud.last_7_days(user_id)

    for data in user_data:
        dates = data['session_date']
        if data['game_id'] == 1:
            if dates not in retval:
                retval[dates] = data['score']
            else:
                retval[dates] += data['score']

    if not retval:
        return jsonify({'No Data ):': "No Game Data"})

    return jsonify(retval)

@app.route('/game-2-user-metrics/<user_id>')
def deliver_game2_user_metrics(user_id):
    """Delivers a dictionary with values of game data organized game_ids as keys"""

    retval = {}

    user_data = crud.last_7_days(user_id)

    for data in user_data:
        dates = data['session_date']
        if data['game_id'] == 2:
            if dates not in retval:
                retval[dates] = data['score']
            else:
                retval[dates] += data['score']

    if not retval:
        return jsonify({'error-code': "No Game Data"})

    return jsonify(retval)

@app.route('/game-3-user-metrics/<user_id>')
def deliver_game3_user_metrics(user_id):
    """Delivers a dictionary with values of game data organized game_ids as keys"""

    retval = {}

    user_data = crud.last_7_days(user_id)

    for data in user_data:
        dates = data['session_date']
        if data['game_id'] == 3:
            if dates not in retval:
                retval[dates] = data['score']
            else:
                retval[dates] += data['score']

    if not retval:
        return jsonify({'error-code': "No Game Data"})

    return jsonify(retval)

@app.route('/about-author')
def show_about_me():
    """Author Page"""

    return render_template('about-me.html')

#"number_of_games": total_num_of_games
#"games_live": games,
#"game_ids": game_ids
#need a set so the game IDs list has unique values

if __name__ == "__main__":
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)