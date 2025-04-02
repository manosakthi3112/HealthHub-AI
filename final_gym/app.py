import os
import io
import gridfs
from bson import ObjectId
import json
import tempfile
import datetime
from flask import Response
import re
from admin_utils import *
import pandas as pd
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file, session, flash
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
import certifi

# Secure API key using environment variables
GENAI_API_KEY = "AIzaSyBSxiJEVwYZTNx6n-nnGxslYbJGMPKcLhc"
if not GENAI_API_KEY:
    raise ValueError("Missing GENAI_API_KEY. Set it in environment variables.")

genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

app = Flask(__name__)
CORS(app)
app.secret_key = "your_secret_key"

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# MongoDB Setup
client = MongoClient("mongodb+srv://manot6114:z4oxzOhu1nDpQRK0@vicky.u6lm4.mongodb.net",
                     tls=True, tlsCAFile=certifi.where())
#client = MongoClient("mongodb+srv://manot6114:z4oxzOhu1nDpQRK0@vicky.u6lm4.mongodb.net/?retryWrites=true&w=majority&appName=vicky")
db = client["diet_tracker"]
excerise_db = client["exercise_videos"]
fs = gridfs.GridFS(excerise_db)
# MongoDB collections
profile_collection = db["profile"]

users_collection = db["users"]
food_collection = db["food_entries"]
meal_plan_collection = db["meal_plans"]
exercise_collection = excerise_db["video_metadata"]

# User class for authentication
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if users_collection.find_one({"_id": user_id}) else None

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        if users_collection.find_one({"_id": username}):
            return "Username already exists!"
        users_collection.insert_one({"_id": username, "password": password})
        return redirect(url_for("index"))
    return render_template("register.html")
@app.route("/profile")
@login_required
def profile():
    """Display the user's profile info."""
    user_id = current_user.id

    # Fetch user profile info
    user = users_collection.find_one({"_id": user_id})
    profile_data = profile_collection.find_one({"user_id": user_id})
    
    profile_photo_id = profile_data["photo_id"] if profile_data and "photo_id" in profile_data else None
    photo_url = url_for('get_photo', photo_id=str(profile_photo_id)) if profile_photo_id else None
    password = user.get('password', 'N/A') 
    return render_template(
        "profile.html", 
        username=user_id, 
        photo_url=photo_url,
        password=password # Mask password for display
    )
@app.route("/upload_photo", methods=["POST"])
@login_required
def upload_photo():
    """Upload and save the profile photo."""
    if 'photo' not in request.files:
        return "No photo uploaded!", 400

    photo = request.files['photo']
    if photo.filename == '':
        return "No selected file!", 400

    user_id = current_user.id

    # Store the photo in GridFS
    photo_id = fs.put(photo, content_type=photo.content_type, filename=photo.filename)

    # Store photo_id in the user's profile
    profile_collection.update_one(
        {"user_id": user_id},
        {"$set": {"photo_id": photo_id}},
        upsert=True
    )

    return redirect(url_for("profile"))
@app.route('/photo/<photo_id>')
@login_required
def get_photo(photo_id):
    """Serve the profile photo."""
    try:
        photo = fs.get(ObjectId(photo_id))
        return Response(photo.read(), content_type=photo.content_type)
    except gridfs.errors.NoFile:
        return "Photo not found", 404
@app.route("/edit_password", methods=["POST"])
@login_required
def edit_password():
    """Update user password."""
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")

    user_id = current_user.id
    user = users_collection.find_one({"_id": user_id})

    # Verify current password
    if not bcrypt.check_password_hash(user["password"], current_password):
        return "Incorrect current password!", 400

    # Update password
    hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
    users_collection.update_one({"_id": user_id}, {"$set": {"password": hashed_password}})

    return redirect(url_for("profile"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        user = users_collection.find_one({"_id": username})
        if user and bcrypt.check_password_hash(user["password"], request.form["password"]):
            login_user(User(username))
            return redirect(url_for("index"))
        return "Invalid username or password!"
    return render_template("login.html")
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple authentication
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('admin.html')
@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))

    # Fetch counts
    user_count = get_user_count(users_collection)
    exercise_count = get_exercise_count(exercise_collection)
    food_count = get_food_count(food_collection)
    meal_plan_count = get_meal_plan_count(meal_plan_collection)

    # Fetch user details
    users = list(users_collection.find())
    print(users)
    # Fetch diet plans with associated user info
    diet_plans = list(meal_plan_collection.find())
    exercise_collection_=exercise_collection.find()
    print(exercise_collection_)
    excercise=[{'title':f['title'],'description':f['description'],'file_id':f['file_id']} for f in exercise_collection_]
    return render_template(
        'dashboard.html',
        user_count=user_count,
        exercise_count=exercise_count,
        food_count=food_count,
        meal_plan_count=meal_plan_count,
        users=users,
        diet_plans=diet_plans,
        excercise=excercise
    )
@app.route('/excerise')
def excerise():
    page = int(request.args.get('page', 1))
    per_page = 10
    videos = list(excerise_db.video_metadata.find().skip((page-1)*per_page).limit(per_page))
    total_videos = excerise_db.video_metadata.count_documents({})
    total_pages = (total_videos + per_page - 1) // per_page
    body_parts = list(set(video['body_part'] for video in videos))
    return render_template('excerise.html', body_parts=body_parts, videos=videos, page=page, total_pages=total_pages)
@app.route('/video/<file_id>')
def video(file_id):
    """Display individual video with metadata"""
    try:
        # Query by string ID (since stored as string)
        video = excerise_db.video_metadata.find_one({"file_id": file_id})
        if not video:
            return "Video not found", 404

        # Get content type from metadata
        mime_type = video.get("contentType", "video/mp4")
        return render_template('video.html', video=video, file_id=video['file_id'], mime_type=mime_type)

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route('/stream/<file_id>')
def stream(file_id):
    """Stream the video with byte-range support"""
    try:
        # Convert to ObjectId if valid, otherwise use string ID
        try:
            file_id_obj = ObjectId(file_id)
        except Exception:
            file_id_obj = file_id  # Use string ID if ObjectId conversion fails

        # Retrieve file by ID
        if isinstance(file_id_obj, ObjectId):
            file = fs.get(file_id_obj)
        else:
            file = fs.find_one({"filename": file_id})  # Use filename for string IDs

        if not file:
            return "Invalid video ID or file not found", 404

        # Stream the video content
        def generate():
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                yield chunk

        return Response(generate(), content_type="video/mp4")

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Function to check if the question is fitness-related
def is_fitness_question(question):
    fitness_keywords = ["hi","hello","exercise", "workout", "gym", "fitness", "calories", "weight loss", "muscle", "diet", "nutrition", "training"]
    return any(word in question.lower() for word in fitness_keywords)

# Function to get detailed nutrition information
def get_food_nutrition(food_name):
    prompt = f"Provide nutritional values per 100g of {food_name}. Format as JSON: {{'calories': X, 'protein': Y, 'fat': Z, 'cholesterol': A, 'carbohydrates': B}}."
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, "text") else str(response)

        # Extract JSON portion safely
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        nutrition_data = json.loads(response_text[json_start:json_end])
        return nutrition_data

    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing AI response: {e}")
        return {
            "calories": "Unknown",
            "protein": "Unknown",
            "fat": "Unknown",
            "cholesterol": "Unknown",
            "carbohydrates": "Unknown"
        }

@app.route("/")
@login_required
def index():
     
    return render_template("index.html")

@app.route("/chatbot")
@login_required
def chatbot():
    return render_template("chatbot.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"response": "Please enter a message."})
    if not is_fitness_question(user_input):
        return jsonify({"response": "I only answer fitness-related questions. Ask about workouts, nutrition, or training!"})

    try:
        response = model.generate_content(user_input)

        # Extract response text properly
        response_text = response.text if hasattr(response, 'text') else "I'm sorry, I couldn't understand that."

        # Limit response to 300 characters or 3 sentences (whichever is shorter)
        max_chars = 300
        max_sentences = 3

        # Truncate by character limit
        if len(response_text) > max_chars:
            response_text = response_text[:max_chars] + "..."

        # Truncate by sentence limit
        sentences = response_text.split('. ')
        if len(sentences) > max_sentences:
            response_text = '. '.join(sentences[:max_sentences]) + "..."

        return jsonify({"response": response_text.strip()})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "Error processing your request. Please try again later."})

@app.route("/diet_tracker", methods=["GET", "POST"])
@login_required
def diet_tracker():
    if request.method == "POST":
        food_name = request.form["food_name"]
        quantity = float(request.form["quantity"])
        nutrition_data = get_food_nutrition(food_name)

        def calculate_per_quantity(value):
            return round((value * quantity) / 100, 2) if isinstance(value, (int, float)) else "Unknown"
        
        food_entry = {
            "user": current_user.id,
            "food_name": food_name,
            "quantity": quantity,
            "calories": calculate_per_quantity(nutrition_data["calories"]),
            "protein": calculate_per_quantity(nutrition_data["protein"]),
            "fat": calculate_per_quantity(nutrition_data["fat"]),
            "cholesterol": calculate_per_quantity(nutrition_data["cholesterol"]),
            "carbohydrates": calculate_per_quantity(nutrition_data["carbohydrates"]),
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        food_collection.insert_one(food_entry)
        return redirect(url_for("diet_tracker"))
    
    selected_date = request.args.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
    food_entries = list(food_collection.find({"user": current_user.id, "date": selected_date}, {"_id": 0}))
    total_calories = sum(entry["calories"] for entry in food_entries if isinstance(entry["calories"], (int, float)))
    return render_template("diet_tracker.html", food_entries=food_entries, selected_date=selected_date, total_calories=total_calories)

@app.route("/export")
@login_required
def export():
    user_entries = list(food_collection.find({"user": current_user.id}, {"_id": 0}))
    df = pd.DataFrame(user_entries)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="diet_data.csv")
@app.route("/edit_food/<food_id>", methods=["GET", "POST"])
@login_required
def edit_food(food_id):
    food_entry = food_collection.find_one({"_id": ObjectId(food_id), "user": current_user.id})
    if not food_entry:
        return "Food entry not found!", 404

    if request.method == "POST":
        new_food_name = request.form["food_name"]
        new_quantity = float(request.form["quantity"])
        nutrition_data = get_food_nutrition(new_food_name)

        def calculate_per_quantity(value):
            return round((value * new_quantity) / 100, 2) if isinstance(value, (int, float)) else "Unknown"

        updated_entry = {
            "food_name": new_food_name,
            "quantity": new_quantity,
            "calories": calculate_per_quantity(nutrition_data["calories"]),
            "protein": calculate_per_quantity(nutrition_data["protein"]),
            "fat": calculate_per_quantity(nutrition_data["fat"]),
            "cholesterol": calculate_per_quantity(nutrition_data["cholesterol"]),
            "carbohydrates": calculate_per_quantity(nutrition_data["carbohydrates"])
        }
        food_collection.update_one({"_id": ObjectId(food_id)}, {"$set": updated_entry})
        return redirect(url_for("diet_tracker"))

    return render_template("edit_food.html", food_entry=food_entry)

@app.route("/delete_food/<food_id>", methods=["POST"])
@login_required
def delete_food(food_id):
    food_collection.delete_one({"_id": ObjectId(food_id), "user": current_user.id})
    return redirect(url_for("diet_tracker"))

@app.route("/food_by_date")
@login_required
def food_by_date():
    dates = food_collection.distinct("date", {"user": current_user.id})
    return render_template("food_by_date.html", dates=sorted(dates, reverse=True))
@app.route("/meal_suggestion", methods=["GET", "POST"])
@login_required
def meal_suggestion():
    if request.method == "POST":
        diet_type = request.form.get("diet_type")
        fitness_goal = request.form.get("fitness_goal")
        meal_type = request.form.get("meal_type")

        # AI Prompt
        prompt = (
            f"Suggest a {meal_type} meal for {fitness_goal} with a {diet_type} diet. "
            "Include ingredients, instructions, and nutritional information. "
            "Format it as JSON: {'meal': 'Meal Name', 'ingredients': ['ingredient1', 'ingredient2'], 'instructions': 'step-by-step instructions', 'calories': X, 'protein': Y, 'carbs': Z, 'fat': W}"
        )

        try:
            # Generate meal suggestion
            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, "text") else str(response)

            # Extract JSON portion safely
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            meal_data = json.loads(response_text[json_start:json_end])

            return render_template("meal_suggestion.html", meal=meal_data)

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing AI response: {e}")
            return "Failed to generate meal suggestion."

    return render_template("meal_form.html")
@app.route('/users')
def users():
    if not session.get('admin'):
        return redirect(url_for('login'))

    users = list(users_collection.find())
    return render_template('users.html', users=users)

# Edit user
@app.route('/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        users_collection.update_one(
            {'_id': user_id},
            {'$set': {
                '_id': request.form['name'],
                'password': bcrypt.generate_password_hash(request.form['email']).decode("utf-8")
            }}
        )
        flash("User updated successfully!", "success")
        return redirect(url_for('dashboard'))

    user = users_collection.find_one({'_id': user_id})
    return render_template('edit_user.html', user=user)

# Edit exercise video
@app.route('/edit_exercise/<exercise_id>', methods=['GET', 'POST'])
def edit_exercise(exercise_id):
    """Edit exercise video details"""
    if request.method == 'POST':
        exercise_collection.update_one(
            {'_id': exercise_id},
            {'$set': {
                'title': request.form['title'],
                'description': request.form['description'],
                'video_url': request.form['video_url']
            }}
        )
        flash("Exercise video updated successfully!", "success")
        return redirect(url_for('dashboard'))

    exercise = exercise_collection.find_one({'_id': ObjectId(exercise_id)})
    return render_template('edit_exercise.html', exercise=exercise)

# Delete user
@app.route('/delete_user/<user_id>')
def delete_user(user_id):
    users_collection.delete_one({'_id': ObjectId(user_id)})
    flash("User deleted successfully!", "success")
    return redirect(url_for('users'))

# Delete exercise video
@app.route('/delete_exercise/<exercise_id>')
def delete_exercise(exercise_id):
    """Delete an exercise video"""
    exercise_collection.delete_one({'_id': ObjectId(exercise_id)})
    flash("Exercise video deleted successfully!", "success")
    return redirect(url_for('dashboard'))



if __name__ == "__main__":
    app.run(debug=True)
