import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from dotenv import load_dotenv
from supabase import create_client, Client
from groq import Groq


# =========================================================
# 1. LOAD .ENV
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH, override=True)


# =========================================================
# 2. ENV VARIABLES
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")


# =========================================================
# 3. FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = FLASK_SECRET_KEY or "development-secret-change-me"


# =========================================================
# 4. STARTUP INFORMATION
# =========================================================

print("----------------------------------------")
print(" SmartAttendance V1")
print(" Student Panel")
print("----------------------------------------")

print("ENV FILE:", ENV_PATH)
print("ENV EXISTS:", os.path.exists(ENV_PATH))

print(
    "SUPABASE:",
    "FOUND" if SUPABASE_URL and SUPABASE_KEY else "NOT FOUND"
)

print(
    "GROQ:",
    "FOUND" if GROQ_API_KEY else "NOT FOUND"
)

print(
    "FLASK SECRET:",
    "FOUND" if FLASK_SECRET_KEY else "NOT FOUND"
)


# =========================================================
# 5. SUPABASE CONNECTION
# =========================================================

supabase: Client | None = None

if SUPABASE_URL and SUPABASE_KEY:

    try:

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        print("Supabase: CONNECTED")

    except Exception as error:

        print("Supabase connection error:", error)

else:

    print("WARNING: Supabase credentials not found.")


# =========================================================
# 6. GROQ CONNECTION
# =========================================================

groq_client = None

if GROQ_API_KEY:

    try:

        groq_client = Groq(
            api_key=GROQ_API_KEY
        )

        print("Groq AI: CONNECTED")

    except Exception as error:

        print("Groq connection error:", error)

else:

    print("WARNING: GROQ_API_KEY not found.")


# =========================================================
# 7. COLLEGE AI SYSTEM PROMPT
# =========================================================

COLLEGE_AI_PROMPT = """
You are College AI inside SmartAttendance V1.

You are an assistant for college students.

You can help with:
- College information
- Attendance
- Notices
- Complaints
- Career and placement
- Courses and branches
- Campus facilities
- General student questions

Answer in a friendly, clear and concise way.

IMPORTANT:
Do not invent college-specific facts.

If exact college information is not available,
tell the student that the information is not currently
available in the college knowledge base.

Never reveal passwords, API keys, secret keys,
database credentials or other private information.
"""


# =========================================================
# 8. HOME
# =========================================================
@app.route("/")
def index():
    if "student_id" not in session:
        return redirect(url_for("login"))

    return redirect(url_for("dashboard"))


# =========================================================
# 9. LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if "student_id" in session:

        return redirect(
            url_for("dashboard")
        )

    error = None

    if request.method == "POST":

        student_id = request.form.get(
            "student_id",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # -------------------------------------------------
        # Empty fields
        # -------------------------------------------------

        if not student_id or not password:

            error = "Please enter Student ID and Password."

            return render_template(
                "login.html",
                error=error
            )

        # -------------------------------------------------
        # Supabase check
        # -------------------------------------------------

        if supabase is None:

            error = "Supabase database is not connected."

            return render_template(
                "login.html",
                error=error
            )

        try:

            # =================================================
            # SEARCH BY STUDENT ID
            # =================================================

            response = (
                supabase
                .table("students")
                .select("*")
                .eq("id", student_id)
                .limit(1)
                .execute()
            )

            students = response.data or []


            # =================================================
            # IF NOT FOUND → SEARCH BY ROLL NUMBER
            # =================================================

            if not students:

                response = (
                    supabase
                    .table("students")
                    .select("*")
                    .eq("roll_number", student_id)
                    .limit(1)
                    .execute()
                )

                students = response.data or []


            # =================================================
            # STUDENT NOT FOUND
            # =================================================

            if not students:

                error = "Student ID or Roll Number not found."

                return render_template(
                    "login.html",
                    error=error
                )


            # =================================================
            # GET STUDENT
            # =================================================

            student = students[0]


            # =================================================
            # PASSWORD CHECK
            # =================================================

            saved_password = str(
                student.get("password", "")
            )

            if saved_password != password:

                error = "Incorrect password."

                return render_template(
                    "login.html",
                    error=error
                )


            # =================================================
            # LOGIN SUCCESS
            # =================================================

            session.clear()

            session["student_id"] = str(
                student.get("id")
            )

            session["student"] = student

            print(
                "Student logged in:",
                student.get("id")
            )

            return redirect(
                url_for("dashboard")
            )


        except Exception as error:

            print("LOGIN ERROR:", error)

            error_message = (
                "Unable to connect to the database."
            )

            return render_template(
                "login.html",
                error=error_message
            )


    # GET request

    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# 10. DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student = session.get(
        "student",
        {}
    )

    return render_template(
        "dashboard.html",
        student=student
    )



@app.route("/ai")
def ai_page():
    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template("ai.html")
# =========================================================
# 11. LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# 12. CURRENT STUDENT API
# =========================================================

@app.route("/api/student")
def current_student():

    if "student_id" not in session:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401


    student = session.get(
        "student",
        {}
    )

    return jsonify({
        "success": True,
        "student": student
    })


# =========================================================
# 13. COLLEGE AI API
# =========================================================
@app.route("/api/ai", methods=["POST"])
def college_ai():

    if "student_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    if groq_client is None:
        return jsonify({
            "success": False,
            "message": "Groq AI is not configured."
        }), 500

    try:

        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()

        if not message:
            return jsonify({
                "success": False,
                "message": "Please enter a message."
            }), 400

        # Current logged-in student
        student_id = session.get("student_id")

        # Get student information from Supabase
        student_result = (
            supabase
            .table("students")
            .select("*")
            .eq("id", student_id)
            .limit(1)
            .execute()
        )

        students = student_result.data or []

        if not students:
            return jsonify({
                "success": False,
                "message": "Student account was not found."
            }), 404

        student = students[0]

        # Student context
        student_context = f"""
CURRENT LOGGED-IN STUDENT:

Name: {student.get("name", "Not available")}
Roll Number: {student.get("roll_number", "Not available")}
Branch: {student.get("branch", "Not available")}
Semester: {student.get("semester", "Not available")}
"""

        # Mugen identity + student context
        system_prompt = f"""
You are Mugen, the official College AI assistant inside SmartAttendance.

IDENTITY:
- Your name is Mugen.
- You were created and developed by Shiva Pandey in 2025.
- You are made by Shiva Pandey.
- Your current version is V1.
- You are currently running as V1.
- V6 is a future planned upgrade.
- You must NEVER claim that you are currently V6.
- If someone asks your current version, say that you are currently Mugen V1.
- If someone asks who created you, say:
  "I was created and developed by Shiva Pandey in 2025. I am Mugen, the College AI assistant inside SmartAttendance."
- If someone asks who made SmartAttendance, say that SmartAttendance was created and developed by Shiva Pandey.
- If someone asks who Shiva Pandey is, say that Shiva Pandey is the creator and developer of SmartAttendance and Mugen.
- Always speak respectfully about Shiva Pandey.
- Never insult, mock, or disrespect Shiva Pandey.
- Do not invent additional personal information about Shiva Pandey.

YOUR CURRENT VERSION:
- Name: Mugen
- Version: V1
- Creator: Shiva Pandey
- Created: 2025
- Product: SmartAttendance
- Future planned upgrade: V6

YOUR JOB:
Help college students with:
- college-related questions
- attendance
- academics
- notices
- placements
- career guidance
- college facilities
- general student questions

COLLEGE INFORMATION:
If you do not have verified information about a college-specific fact,
clearly say that you do not have verified information.
Never invent college-specific information.

CURRENT LOGGED-IN STUDENT:
{student_context}

STUDENT PRIVACY:
1. You are talking to the CURRENTLY LOGGED-IN student.
2. Use this student's information when relevant.
3. Never assume another student's information belongs to this student.
4. Never reveal private information about another student.
5. Never provide another student's personal information.
6. If the required student information is unavailable, clearly say so.

BEHAVIOUR:
- Be helpful, clear, respectful and concise.
- Always respect the student.
- If asked who you are, introduce yourself as Mugen.
- If asked your current version, say V1.
- Never claim you are currently V6.
"""

        completion = groq_client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ],

            temperature=0.4,
            max_tokens=700
        )

        print("GROQ RAW RESPONSE:")
        print(completion)

        answer = completion.choices[0].message.content

        if not answer:
            return jsonify({
                "success": False,
                "message": "AI returned an empty response."
            }), 500

        return jsonify({
            "success": True,
            "answer": answer
        })

    except Exception as e:

        print("GROQ ERROR:", repr(e))

        return jsonify({
            "success": False,
            "message": "College AI is temporarily unavailable."
        }), 500


    # -------------------------------------------------
    # Student information
    # -------------------------------------------------

    student = session.get(
        "student",
        {}
    )

    student_name = student.get(
        "name",
        "Student"
    )

    roll_number = student.get(
        "roll_number",
        ""
    )

    branch = student.get(
        "branch",
        student.get("class_name", "")
    )


    # -------------------------------------------------
    # AI prompt
    # -------------------------------------------------

    system_prompt = f"""
{COLLEGE_AI_PROMPT}

CURRENT STUDENT:

Name: {student_name}
Roll Number: {roll_number}
Branch/Class: {branch}

Remember:
Never expose private student information.
"""


    # -------------------------------------------------
    # Call Groq
    # -------------------------------------------------

    try:

        response = groq_client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ],

            temperature=0.4,

            max_tokens=700
        )


        answer = response.choices[0].message.content


        return jsonify({
            "success": True,
            "answer": answer
        })


    except Exception as error:

        print("GROQ ERROR:", error)

        return jsonify({
            "success": False,
            "message": "College AI is temporarily unavailable."
        }), 500


# =========================================================
# 14. COMPLAINT API
# =========================================================

@app.route("/api/complaint", methods=["POST"])
def submit_complaint():

    if "student_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    data = request.get_json(
        silent=True
    ) or {}


    category = str(
        data.get("category", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()


    if not category:

        return jsonify({
            "success": False,
            "message": "Please select a complaint category."
        }), 400


    if not message:

        return jsonify({
            "success": False,
            "message": "Please describe your complaint."
        }), 400


    # -------------------------------------------------
    # TEMPORARY
    # -------------------------------------------------
    # Complaint table ke exact columns confirm hone ke
    # baad yahan Supabase insert add karenge.

    print("----------------------------------------")
    print("NEW COMPLAINT")
    print("Student:", session.get("student_id"))
    print("Category:", category)
    print("Message:", message)
    print("----------------------------------------")


    return jsonify({
        "success": True,
        "message": "Complaint submitted successfully."
    })


# =========================================================
# 15. STATUS API
# =========================================================

@app.route("/api/status")
def status():

    return jsonify({

        "application": "SmartAttendance V1",

        "supabase": (
            supabase is not None
        ),

        "groq": (
            groq_client is not None
        ),

        "logged_in": (
            "student_id" in session
        )

    })


# =========================================================
# 16. 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "Page not found."
    }), 404


# =========================================================
# 17. RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv("PORT", 5000)
        ),
        debug=True
    )
