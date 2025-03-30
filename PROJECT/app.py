import ast
import random
import sqlite3
import requests
import json
from datetime import datetime

from flask import Flask, flash, request, session, redirect, render_template, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import trivia_data

app = Flask(__name__)

app.secret_key = "pythonflasktrivia"

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

database = "trivia.db"


@app.template_filter('shuffle')
def shuffle_filter(seq):
    try:
        shuffled = list(seq)
        random.shuffle(shuffled)
        return shuffled
    except:
        return seq


app.jinja_env.filters['shuffle'] = shuffle_filter


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods={"GET", "POST"})
def register():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        verify_password = request.form.get("verify-password")

        if validate(username, password, verify_password):
            return flash_message("Please enter in all fields.", "error", "/register")

        if password != verify_password:
            return flash_message("Passwords do not match.", "error", "/register")

        db = sqlite3.connect(database)
        cursor = db.cursor()

        print(username)
        if cursor.execute("SELECT username FROM users WHERE username = ?", (username, )).fetchone():
            return flash_message("Username already in use.", "error", "/register")

        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, generate_password_hash(password)))
        db.commit()
        db.close()

        return flash_message("Account successfully registered", "success", "/login")

    else:
        return render_template("/account-related/register.html")


@app.route("/login", methods={"GET", "POST"})
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if validate(username, password):
            return flash_message("Please enter in all fields.", "error", "/login")

        db = get_database()
        cursor = db.cursor()

        login_details = cursor.execute("SELECT * FROM USERS WHERE username = ?", (username, )).fetchone()

        if validate(login_details) or username != login_details[1] or not check_password_hash(login_details[2],
                                                                                              password):
            return flash_message("Username or Password is incorrect.", "error", "/login")

        session["user_id"] = login_details[0]
        session["username"] = username

        db.close()
        return flash_message("Successfully Logged In.", "success", "/")

    else:
        return render_template("/account-related/login.html")


@app.route("/logout")
def logout():
    session.clear()
    return flash_message("You have logged out.", "error", "/")


@app.route("/play", methods={"GET", "POST"})
def play():
    trivia_id = session.get("trivia_id")

    categories = trivia_data.categories

    if request.method == "POST":
        if request.form.get("play-again"):
            return render_template("/play-trivia/trivia.html", questions=session["questions"])

        number_of_questions = request.form.get("number-of-questions")
        chosen_category = request.form.get("category")
        difficulty = request.form.get("difficulty")
        type_of_questions = request.form.get("type-of-questions")

        trivia = get_trivia_questions(number_of_questions, chosen_category, difficulty, type_of_questions)

        if trivia.status_code != 200:
            return flash_message(f"Unknown Error Occurred, Please Try Again. CODE: {trivia}", "error", "/play")

        trivia = trivia.json()

        if trivia["response_code"] == 1:
            flash("Due to lack of questions, some may be missing.", "warning")

        if not is_valid_category(chosen_category):
            chosen_category = "any category"

        if difficulty not in trivia_data.categories:
            difficulty = "any difficulty"

        if type_of_questions not in trivia_data.questionType:
            type_of_questions = "any type"

        session["questions"] = trivia["results"]

        db = get_database()
        cursor = db.cursor()

        if is_logged_in():
            trivia_id = insert_trivia_in_db(cursor, session["questions"], chosen_category,
                                            number_of_questions, difficulty, type_of_questions, "private")

            cursor.execute("INSERT INTO played_trivias (trivia_id, user_id) VALUES (?, ?);",
                           (trivia_id, session.get("user_id")))

            db.commit()

        db.close()

        return render_template("/play-trivia/trivia.html", questions=trivia["results"])

    else:
        if not trivia_id:
            return render_template("play.html", categories=categories)

        else:
            db = get_database()
            cursor = db.cursor()

            if is_logged_in():
                cursor.execute("INSERT INTO played_trivias (trivia_id, user_id) VALUES (?, ?);",
                               (session.get("trivia_id"), session.get("user_id")))
                db.commit()

            results = \
                cursor.execute("SELECT trivia from trivias WHERE id = ?;", (session.get('trivia_id'),)).fetchone()[0]

            db.close()

            results = db_convert_to_valid_trivia(results)
            session["questions"] = results

            session.pop("trivia_id", default=None)

            return render_template("/play-trivia/trivia.html", questions=session["questions"])


@app.route("/confirm-answer", methods={"POST"})
def validate_answers():
    question_number = 1
    questions = session["questions"]

    chosen_answer = []
    is_correct = []

    for question in questions:
        if question['type'] == "boolean":
            answer = request.form.get(f"truefalse-{question_number}")
        else:
            answer = request.form.get(f"multiple-{question_number}")

        chosen_answer.append(answer)
        if answer == question["correct_answer"]:
            is_correct.append("correct")
        else:
            is_correct.append("incorrect")

        question_number += 1

    return render_template("/play-trivia/triviaResults.html", questions=questions, chosenAnswer=chosen_answer,
                           isCorrect=is_correct)


@app.route("/create", methods={"GET", "POST"})
def create():
    if not is_logged_in():
        return flash_message("Login Required", "error", "/login")

    trivia_categories = trivia_data.categories
    if request.method == "POST":

        number_of_questions = request.form.get("number-of-questions")
        if not number_of_questions or not number_of_questions.isdecimal() or not 1 <= int(number_of_questions) <= 20:
            return flash_message("Please enter in a valid amount", "error", "/create")
        session["number-of-questions"] = number_of_questions

        category = request.form.get("category")
        if not is_valid_category(category):
            category = "any category"
        elif category != "any category":
            category = category.split(",")

        difficulty = request.form.get("difficulty")
        if not difficulty:
            difficulty = "any difficulty"

        type_of_questions = request.form.get("type-of-questions")
        if type_of_questions not in trivia_data.questionType:
            type_of_questions = "any type"

        return render_template("/create-trivia/create-trivia.html", numberOfQuestions=number_of_questions,
                               chosenCategory=category, categories=trivia_categories, difficulty=difficulty,
                               typeOfQuestions=type_of_questions)

    else:
        return render_template("create.html", categories=trivia_categories)


@app.route("/create-trivia", methods={"POST"})
def create_trivia():
    if not is_logged_in():
        return flash_message("Login Required", "error", "/login")

    fields_warning = lambda: flash_message("Please correctly fill in all the fields.", "error", "/create")
    trivia_categories = trivia_data.categories

    chosen_category = request.form.get("chosen-category")

    try:
        chosen_category = ast.literal_eval(chosen_category)
        chosen_category = f"{chosen_category[0]}: {chosen_category[1]}"
    except:
        if not is_valid_category(chosen_category):
            chosen_category = "any category"

    chosen_question_amount = session.get("number-of-questions")
    chosen_difficulty = request.form.get("difficulty")
    if not chosen_difficulty:
        chosen_difficulty = "any difficulty"

    chosen_question_type = request.form.get("type-of-questions")
    if not chosen_question_type:
        chosen_question_type = "any type"

    print(chosen_category, chosen_question_amount, chosen_difficulty, chosen_question_type)

    created_visibility = request.form.get("visibility")

    results = []

    for i in range(1, int(session.get("number-of-questions")) + 1):

        created_question = request.form.get(f"question-{i}")
        created_category = request.form.get(f"category-{i}")
        created_difficulty = request.form.get(f"difficulty-{i}")
        created_correct_answer = request.form.get(f"correct-answer-{i}")
        created_incorrect_answer = request.form.get(f"incorrect-answers-{i}")
        created_type = "multiple"

        if validate(created_question, created_category, created_difficulty, created_correct_answer,
                    created_incorrect_answer):
            return fields_warning()

        created_category = created_category.split(",")
        if len(created_category) != 2:
            return fields_warning()

        if created_category[0] not in trivia_categories.keys() or created_category[1] not in trivia_categories[
            created_category[0]].keys():
            return fields_warning()

        if created_difficulty not in trivia_data.difficulty:
            return fields_warning()

        if (created_correct_answer.strip().lower() == "true" and created_incorrect_answer.strip().lower() == "false" or \
                created_correct_answer.strip().lower() == "false" and created_incorrect_answer.strip().lower() == "true") \
                and (chosen_question_type == "boolean" or chosen_question_type == "any type"):
            created_correct_answer = created_correct_answer.capitalize()
            created_incorrect_answer = created_incorrect_answer.capitalize()
            created_type = "boolean"

        elif len(created_incorrect_answer.split(",")) == 3 and (
                created_type == "multiple" or created_type == "any type"):
            continue

        else:
            return flash_message("Please enter in valid answers according to your chosen question type.", "error",
                                 "/create")

        created_incorrect_answer = strip_array(created_incorrect_answer.split(","))

        results.append(
            {"type": f"{created_type}", "difficulty": f"{created_difficulty}",
             "category": f"{created_category[0]}: {created_category[1]}",
             "question": f"{created_question}",
             "correct_answer": f"{created_correct_answer}", "incorrect_answers": f"{created_incorrect_answer}"})

    if not created_visibility or created_visibility != "public":
        created_visibility = "private"

    db = get_database()
    cursor = db.cursor()

    trivia_id = insert_trivia_in_db(cursor, results, chosen_category, chosen_question_amount,
                                    chosen_difficulty, chosen_question_type, created_visibility)
    cursor.execute("INSERT INTO created_trivias (trivia_id, user_id) VALUES (?, ?);",
                   (trivia_id, session.get("user_id")))

    db.commit()
    db.close()

    flash("Trivia Created Successfully.", "success")
    return render_template("/create-trivia/created-trivia.html", triviaId=trivia_id)


@app.route("/created-trivia", methods={"POST"})
def created_trivia():
    if not is_logged_in():
        return flash_message("Login Required", "error", "/login")

    trivia_id = request.form.get("trivia-id")
    session["trivia_id"] = trivia_id

    return redirect("/play")


@app.route("/public-trivia")
def public_trivia():
    db = get_database()
    cursor = db.cursor()

    created_trivias = cursor.execute(
        "SELECT users.id AS user_id,users.username,trivias.id AS trivia_id, trivias.trivia, trivias.category, "
        "trivias.number_of_questions, trivias.difficulty, trivias.type_of_questions, trivias.visibility, "
        "trivias.creation_date FROM created_trivias JOIN trivias ON "
        "created_trivias.trivia_id = trivias.id JOIN users ON created_trivias.user_id = users.id WHERE "
        "trivias.visibility = 'public' ORDER BY creation_date DESC;").fetchall()
    db.close()

    created_trivias = list(created_trivias)
    for i in range(len(created_trivias)):
        created_trivias[i] = list(created_trivias[i])
        created_trivias[i][3] = db_convert_to_valid_trivia(created_trivias[i][3])

    print(created_trivias)
    return render_template("public-trivia.html", createdTrivias=created_trivias)


@app.route("/choose-public-trivia", methods={"POST"})
def chosen_public_trivia():
    session["trivia_id"] = request.form.get("trivia-id")
    return redirect("/play")


@app.route("/history/created-trivias")
def history_of_created_trivias():
    if not is_logged_in():
        return flash_message("Login Required", "error", "/login")

    db = get_database()
    cursor = db.cursor()

    created_trivias = cursor.execute(
        "SELECT users.id AS user_id,users.username,trivias.id AS trivia_id, trivias.trivia, trivias.category, "
        "trivias.number_of_questions, trivias.difficulty, trivias.type_of_questions, trivias.visibility, "
        "trivias.creation_date FROM created_trivias JOIN trivias ON "
        "created_trivias.trivia_id = trivias.id JOIN users ON created_trivias.user_id = users.id WHERE "
        "user_id = ? ORDER BY creation_date DESC;", (session.get("user_id"),)).fetchall()
    db.close()

    return render_template("/history/created-trivias.html", createdTrivias=created_trivias)


@app.route("/history/change-visibility", methods={"POST"})
def change_visibility():
    if not is_logged_in():
        return flash_message("Login Required", "error", "/login")

    trivia_id = request.form.get("trivia-id-visibility-swap")
    print(trivia_id)

    db = get_database()
    cursor = db.cursor()

    visibility = cursor.execute("SELECT visibility FROM trivias WHERE id = ?;", (trivia_id,)).fetchone()[0]
    print(visibility)

    if visibility == "public":
        visibility = "private"
    else:
        visibility = "public"

    cursor.execute("UPDATE trivias SET visibility = ? WHERE id = ?;", (visibility, trivia_id))
    db.commit()

    db.close()

    return flash_message("Visibility successfully changed.", "success", "/history/created-trivias")


@app.route("/history/played-trivias")
def history_of_played_trivias():
    if not is_logged_in():
        return flash_message("Login Required", "error", "/login")

    db = get_database()
    cursor = db.cursor()

    played_trivias = cursor.execute(
        "SELECT users.id AS user_id,users.username,trivias.id AS trivia_id, trivias.trivia, trivias.category, "
        "trivias.number_of_questions, trivias.difficulty, trivias.type_of_questions, trivias.visibility, "
        "trivias.creation_date FROM played_trivias JOIN trivias ON "
        "played_trivias.trivia_id = trivias.id JOIN users ON played_trivias.user_id = users.id WHERE "
        "user_id = ? ORDER BY creation_date DESC;", (session.get("user_id"),)).fetchall()
    db.close()

    print(played_trivias)

    return render_template("/history/played-trivias.html", playedTrivias=played_trivias)


def get_trivia_questions(number_of_questions, chosen_category, difficulty, type_of_questions):
    url = "https://opentdb.com/api.php?"

    if not number_of_questions or not number_of_questions.isdigit() \
            or int(number_of_questions) < 1 or int(number_of_questions) > 20:
        return flash_message("Please enter in a valid amount of questions", "error", "/play")

    else:
        url += f"amount={number_of_questions}"

    if chosen_category:
        chosen_category = chosen_category.split(",")

        if len(chosen_category) == 2:

            category = chosen_category[0]
            sub_category = chosen_category[1]

            categories = trivia_data.categories
            if category in categories.keys() and sub_category in categories[category].keys():
                url += f"&category={categories[category][sub_category]}"

    if difficulty in trivia_data.difficulty:
        url += f"&difficulty={difficulty}"

    if type_of_questions in trivia_data.questionType:
        url += f"&type={type_of_questions}"

    return requests.get(url)


def flash_message(message, messageType, url):
    flash(message, messageType)
    return redirect(url)


def validate(*args):
    for arg in args:
        if arg is None:
            return True
    return False


def is_valid_category(category):
    trivia_categories = trivia_data.categories

    if not category:
        return False

    elif category != "any category":
        category = category.split(",")
        if category[0] not in trivia_categories.keys() or category[1] not in trivia_categories[
            category[0]].keys():
            return False

    return True


def insert_trivia_in_db(cursor, trivia, category, number_of_questions, difficulty, type_of_questions, visibility):
    cursor.execute("INSERT INTO trivias (trivia, category, number_of_questions, difficulty, "
                   "type_of_questions, visibility, creation_date) VALUES (?, ?, ?, ?, ?, ?, ?);",
                   (json.dumps(trivia), category, number_of_questions, difficulty,
                    type_of_questions, visibility, get_current_time()))

    trivia_id = cursor.execute("SELECT id from trivias ORDER BY id DESC LIMIT 1;").fetchone()[0]

    return trivia_id


def db_convert_to_valid_trivia(results):
    results = json.loads(results)

    for result in results:
        if isinstance(result["incorrect_answers"], str):
            result["incorrect_answers"] = ast.literal_eval(result["incorrect_answers"])

    return results


def get_current_time():
    return datetime.now().strftime("%Y %b %d %I:%M %p")


def strip_array(arr):
    for i in range(len(arr)):
        if isinstance(arr[i], str):
            arr[i] = arr[i].strip()

    return arr


def get_database():
    return sqlite3.connect(database)


def is_logged_in():
    return session.get("user_id") is not None


app.run(debug=True)
