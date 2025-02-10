from flask import Flask, request, render_template, redirect, url_for, jsonify, session
import json
import os
from models import db, User, MatchResult  # Import from models.py
from cook import main as run_cook_logic  # Import the main function from cook.py
import logging

app = Flask(__name__)
app.secret_key = 'uw_dsc_speed_dating' 

# Get the absolute path to the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.txt')

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

logging.basicConfig(level=logging.DEBUG)

@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/main')
def main():
    return render_template('main.html')


@app.route('/friendship-quiz', methods=['GET', 'POST'])
def friendship_quiz():
    if request.method == 'POST':
        name = request.form.get('name')
        discord_handle = request.form.get('discord')
        mbti = request.form.get('mbti')
        message = request.form.get('message')  # Capture the optional message
        # Add other fields as necessary

        if not name or not discord_handle or not mbti:
            return "All fields are required", 400

        try:
            # Create a new User object
            user = User(
                name=name,
                discord_handle=discord_handle,
                mbti=mbti,
                gender=request.form.get('gender'),
                preferred_gender=','.join(request.form.getlist('preferred-gender')),
                communication_style=request.form.get('communication-style'),
                weekend_activity=request.form.get('weekend-activity'),
                preference=request.form.get('preference'),
                movie_genres=','.join(request.form.getlist('movie-genres')),
                party_frequency=request.form.get('party-frequency'),
                relationship_components=','.join(request.form.getlist('relationship-components')),
                fate_belief=request.form.get('fate'),
                message=message  # Store the message
            )
            # Add the user to the database session
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            logging.error("Error adding user to database: %s", e)
            return "An error occurred", 500

        return redirect(url_for('waiting'))
    return render_template('friendship-quiz.html')

@app.route('/waiting')
def waiting():
    return render_template('waiting.html')

@app.route('/pre_result')
def pre_result():
    return redirect(url_for('pre_result'))

@app.route('/check_result')
def check_result():
    # Check if matches exist in the database
    matches_exist = MatchResult.query.first() is not None
    if matches_exist:
        return redirect(url_for('pre_result'))
    return render_template('waiting.html')

@app.route('/host')
def host():
    return render_template('host.html')

@app.route('/result')
def result():
    # Get discord handle from query parameter
    discord_handle = request.args.get('discord')
    if not discord_handle:
        return redirect(url_for('pre_result'))

    # Check if the user exists
    user = User.query.filter_by(discord_handle=discord_handle).first()
    if not user:
        return render_template('pre_result.html', error="Discord handle not found. Please re-enter your Discord handle.", matches_exist=True)

    # Get the match result for the user
    match_result = MatchResult.query.filter_by(user1_id=user.id).first()
    if not match_result:
        return render_template('result.html', match_name=False, names=get_all_names())

    # Get the matched user's details
    matched_user = User.query.get(match_result.user2_id) if match_result.user2_id else None

    return render_template('result.html',
                           match_name=matched_user.name if matched_user else None,
                           match_discord=matched_user.discord_handle if matched_user else None,
                           match_message=matched_user.message if matched_user else None,
                           names=get_all_names())

def get_all_names():
    # Get all user names for the floating animation
    return [user.name for user in User.query.all()]

@app.route('/run-cook')
def run_cook():
    run_cook_logic()  # Call the main function from cook.py
    return "cook.py logic executed!"

@app.route('/delete-for-real')
def delete_for_real():
    try:
        # Delete all entries from the User and MatchResult tables
        num_users_deleted = User.query.delete()
        num_matches_deleted = MatchResult.query.delete()
        db.session.commit()
        logging.info(f"Deleted {num_users_deleted} users and {num_matches_deleted} match results.")
        return "All user inputs and match results have been deleted."
    except Exception as e:
        logging.error("Error deleting data: %s", e)
        return "An error occurred while deleting data.", 500

if __name__ == '__main__':
    app.run(debug=True)
