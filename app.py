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

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(
    ENV_PATH,
    override=True
)


# =========================================================
# 2. MUGEN KNOWLEDGE BASE
# =========================================================

KNOWLEDGE_DIR = os.path.join(
    BASE_DIR,
    "knowledge"
)

KNOWLEDGE_FILE = os.path.join(
    KNOWLEDGE_DIR,
    "mugen_knowledge.txt"
)


def load_mugen_knowledge():

    try:

        if not os.path.exists(KNOWLEDGE_FILE):

            print(
                "Mugen Knowledge Base: FILE NOT FOUND"
            )

            return ""

        with open(
            KNOWLEDGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            knowledge = file.read().strip()

        print(
            "Mugen Knowledge Base: LOADED",
            len(knowledge),
            "characters"
        )

        return knowledge

    except Exception as error:

        print(
            "Mugen Knowledge Base ERROR:",
            repr(error)
        )

        return ""


# =========================================================
# 3. ENV VARIABLES
# =========================================================

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

FLASK_SECRET_KEY = os.getenv(
    "FLASK_SECRET_KEY"
)


# =========================================================
# 4. FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = (
    FLASK_SECRET_KEY
    or "development-secret-change-me"
)


# =========================================================
# 5. STARTUP INFORMATION
# =========================================================

print("----------------------------------------")
print(" SmartAttendance V1")
print(" Student Panel")
print(" AI: Mugen")
print(" Creator: Shiva Pandey")
print(" Version: V1")
print("----------------------------------------")

print(
    "ENV FILE:",
    ENV_PATH
)

print(
    "ENV EXISTS:",
    os.path.exists(ENV_PATH)
)

print(
    "SUPABASE:",
    "FOUND"
    if SUPABASE_URL and SUPABASE_KEY
    else "NOT FOUND"
)

print(
    "GROQ:",
    "FOUND"
    if GROQ_API_KEY
    else "NOT FOUND"
)

print(
    "FLASK SECRET:",
    "FOUND"
    if FLASK_SECRET_KEY
    else "NOT FOUND"
)


# =========================================================
# 6. SUPABASE CONNECTION
# =========================================================

supabase: Client | None = None


if SUPABASE_URL and SUPABASE_KEY:

    try:

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        print(
            "Supabase: CONNECTED"
        )

    except Exception as error:

        print(
            "Supabase connection error:",
            repr(error)
        )

else:

    print(
        "WARNING: Supabase credentials not found."
    )


# =========================================================
# 7. GROQ CONNECTION
# =========================================================

groq_client = None


if GROQ_API_KEY:

    try:

        groq_client = Groq(
            api_key=GROQ_API_KEY
        )

        print(
            "Groq AI: CONNECTED"
        )

    except Exception as error:

        print(
            "Groq connection error:",
            repr(error)
        )

else:

    print(
        "WARNING: GROQ_API_KEY not found."
    )


# =========================================================
# 8. MUGEN IDENTITY
# =========================================================

MUGEN_IDENTITY = """
You are Mugen, the official College AI assistant
inside SmartAttendance.

IDENTITY:

- Your name is Mugen.
- You are the College AI assistant of SmartAttendance.
- You were created and developed by Shiva Pandey in 2025.
- SmartAttendance was created and developed by Shiva Pandey.
- Your current version is V1.
- You are currently running as V1.
- V6 is only a future planned upgrade.
- Never claim that you are currently V6.

If someone asks:

"Who are you?"

Answer naturally that you are Mugen,
the College AI assistant inside SmartAttendance.

If someone asks:

"Who created you?"

Say:

"I was created and developed by Shiva Pandey in 2025.
I am Mugen, the College AI assistant inside
SmartAttendance."

If someone asks:

"Who made SmartAttendance?"

Say that SmartAttendance was created and developed
by Shiva Pandey.

If someone asks:

"Who is Shiva Pandey?"

Say that Shiva Pandey is the creator and developer
of SmartAttendance and Mugen.

Always speak respectfully about Shiva Pandey.

Do not invent additional personal information
about Shiva Pandey.
"""


# =========================================================
# 9. MUGEN SYSTEM RULES
# =========================================================

MUGEN_RULES = """
YOUR JOB:

Help college students with:

- College information
- Attendance
- Academics
- Notices
- Complaints
- Placements
- Career guidance
- College facilities
- Courses and branches
- SmartAttendance website usage
- General student questions


COLLEGE INFORMATION:

Use the provided Mugen Knowledge Base for
college-specific information.

Do not invent college-specific facts.

If a college-specific answer is not available
in the knowledge base, clearly say:

"Verified information is not currently available
in the college knowledge base."


WEBSITE HELP:

If a student asks how to use SmartAttendance,
use the SmartAttendance Website Guide contained
in the knowledge base.

Give simple step-by-step instructions.

Do not invent buttons, sections or features
that are not described in the knowledge base.


STUDENT PRIVACY:

1. You are talking to the currently logged-in student.

2. Use the current student's information when relevant.

3. Never assume another student's information
   belongs to the current student.

4. Never reveal another student's private information.

5. Never provide another student's personal information.

6. Never reveal passwords.

7. Never reveal API keys.

8. Never reveal secret keys.

9. Never reveal database credentials.

10. Never reveal confidential system information.


BEHAVIOUR:

- Be helpful.
- Be clear.
- Be respectful.
- Be concise.
- Understand normal student language.
- Hinglish is allowed when the student speaks Hinglish.
- Answer naturally.
- Do not unnecessarily repeat the same information.
"""


# =========================================================
# 10. HOME
# =========================================================

@app.route("/")
def index():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# 11. LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

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
        # EMPTY FIELDS
        # -------------------------------------------------

        if not student_id or not password:

            error = (
                "Please enter Student ID and Password."
            )

            return render_template(
                "login.html",
                error=error
            )


        # -------------------------------------------------
        # SUPABASE CHECK
        # -------------------------------------------------

        if supabase is None:

            error = (
                "Supabase database is not connected."
            )

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
            # SEARCH BY ROLL NUMBER
            # =================================================

            if not students:

                response = (
                    supabase
                    .table("students")
                    .select("*")
                    .eq(
                        "roll_number",
                        student_id
                    )
                    .limit(1)
                    .execute()
                )

                students = response.data or []


            # =================================================
            # STUDENT NOT FOUND
            # =================================================

            if not students:

                error = (
                    "Student ID or Roll Number not found."
                )

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
                student.get(
                    "password",
                    ""
                )
            )

            if saved_password != password:

                error = (
                    "Incorrect password."
                )

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

            print(
                "LOGIN ERROR:",
                repr(error)
            )

            error_message = (
                "Unable to connect to the database."
            )

            return render_template(
                "login.html",
                error=error_message
            )


    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# 12. DASHBOARD
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

# =========================================================
# COMPLAINTS PAGE
# =========================================================

@app.route("/complaints")
def complaints_page():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "complaints.html"
    )

# =========================================================
# 13. AI PAGE
# =========================================================

@app.route("/ai")
def ai_page():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "ai.html"
    )


# =========================================================
# 14. LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# 15. CURRENT STUDENT API
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
# 16. MUGEN AI API
# =========================================================

@app.route(
    "/api/ai",
    methods=["POST"]
)
def college_ai():

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if "student_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    # -----------------------------------------------------
    # GROQ CHECK
    # -----------------------------------------------------

    if groq_client is None:

        return jsonify({
            "success": False,
            "message": "Groq AI is not configured."
        }), 500


    try:

        # =================================================
        # GET USER MESSAGE
        # =================================================

        data = request.get_json(
            silent=True
        ) or {}

        message = str(
            data.get(
                "message",
                ""
            )
        ).strip()


        if not message:

            return jsonify({
                "success": False,
                "message": "Please enter a message."
            }), 400


        # =================================================
        # CURRENT STUDENT
        # =================================================

        student_id = session.get(
            "student_id"
        )


        if supabase is None:

            return jsonify({
                "success": False,
                "message": (
                    "Supabase database is not connected."
                )
            }), 500


        student_result = (
            supabase
            .table("students")
            .select("*")
            .eq(
                "id",
                student_id
            )
            .limit(1)
            .execute()
        )


        students = (
            student_result.data
            or []
        )


        if not students:

            return jsonify({
                "success": False,
                "message": (
                    "Student account was not found."
                )
            }), 404


        student = students[0]


        # =================================================
        # STUDENT CONTEXT
        # =================================================

        student_context = f"""
CURRENT LOGGED-IN STUDENT:

Name:
{student.get("name", "Not available")}

Roll Number:
{student.get("roll_number", "Not available")}

Branch:
{student.get("branch", "Not available")}

Semester:
{student.get("semester", "Not available")}
"""


        # =================================================
        # LOAD KNOWLEDGE BASE
        # =================================================

        mugen_knowledge = (
            load_mugen_knowledge()
        )


        if not mugen_knowledge:

            mugen_knowledge = """
No verified college knowledge is currently available.
"""


        # =================================================
        # FINAL SYSTEM PROMPT
        # =================================================

        system_prompt = f"""

==================================================
MUGEN — SMARTATTENDANCE COLLEGE AI
==================================================

{MUGEN_IDENTITY}


==================================================
MUGEN RULES
==================================================

{MUGEN_RULES}


==================================================
VERIFIED KNOWLEDGE BASE
==================================================

The following information is provided as the
knowledge base for Mugen.

Use this information when answering
college-specific and SmartAttendance-related
questions.

---------------- KNOWLEDGE START ----------------

{mugen_knowledge}

----------------- KNOWLEDGE END -----------------


==================================================
CURRENT LOGGED-IN STUDENT
==================================================

{student_context}


==================================================
FINAL INSTRUCTIONS
==================================================

- The current student is the person using this chat.
- Use their information only when relevant.
- Do not expose private student information.
- Prefer verified knowledge from the knowledge base.
- Never invent college-specific facts.
- Use the website guide for questions about
  using SmartAttendance.
- If verified information is missing, say so clearly.
- Your name is Mugen.
- Your current version is V1.
- Your creator/developer is Shiva Pandey.
- You were created and developed in 2025.
- V6 is a future planned upgrade, not your current version.
"""


        # =================================================
        # MODELS
        # =================================================

        models = [

            "openai/gpt-oss-120b",

            "groq/compound",

            "groq/compound-mini"

        ]


        # =================================================
        # TRY MODELS ONE BY ONE
        # =================================================

        last_error = None


        for model_name in models:

            try:

                print(
                    "----------------------------------------"
                )

                print(
                    "MUGEN MODEL:",
                    model_name
                )

                print(
                    "----------------------------------------"
                )


                completion = (
                    groq_client
                    .chat
                    .completions
                    .create(

                        model=model_name,

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
                )


                answer = (
                    completion
                    .choices[0]
                    .message
                    .content
                )


                if answer and answer.strip():

                    print(
                        "MUGEN SUCCESS:",
                        model_name
                    )


                    return jsonify({

                        "success": True,

                        "answer": answer,

                        "model": model_name

                    })


                print(
                    "EMPTY RESPONSE FROM:",
                    model_name
                )


            except Exception as error:

                last_error = error

                print(
                    "MODEL ERROR:",
                    model_name,
                    repr(error)
                )

                continue


        # =================================================
        # ALL MODELS FAILED
        # =================================================

        print(
            "ALL MUGEN MODELS FAILED:",
            repr(last_error)
        )


        return jsonify({

            "success": False,

            "message":
                "College AI is temporarily unavailable."

        }), 503


    except Exception as error:

        print(
            "MUGEN API ERROR:",
            repr(error)
        )


        return jsonify({

            "success": False,

            "message":
                "College AI is temporarily unavailable."

        }), 500

# =========================================================
# 17. COMPLAINT API
# =========================================================

@app.route(
    "/api/complaint",
    methods=["POST"]
)
def submit_complaint():

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if "student_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    # -----------------------------------------------------
    # SUPABASE CHECK
    # -----------------------------------------------------

    if supabase is None:

        return jsonify({
            "success": False,
            "message": "Supabase database is not connected."
        }), 500


    try:

        # -------------------------------------------------
        # CURRENT STUDENT
        # -------------------------------------------------

        student_id = str(
            session.get("student_id")
        )


        student_result = (
            supabase
            .table("students")
            .select("*")
            .eq(
                "id",
                student_id
            )
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


        # -------------------------------------------------
        # FORM DATA
        # -------------------------------------------------

        category = request.form.get(
            "category",
            ""
        ).strip()


        title = request.form.get(
            "title",
            ""
        ).strip()


        description = request.form.get(
            "description",
            ""
        ).strip()


        photo = request.files.get(
            "photo"
        )


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not category:

            return jsonify({
                "success": False,
                "message":
                    "Please select a complaint category."
            }), 400


        if not title:

            return jsonify({
                "success": False,
                "message":
                    "Please enter a complaint title."
            }), 400


        if not description:

            return jsonify({
                "success": False,
                "message":
                    "Please describe your complaint."
            }), 400


        # -------------------------------------------------
        # PHOTO UPLOAD
        # -------------------------------------------------

        photo_url = None


        if photo and photo.filename:

            import uuid


            filename = photo.filename


            allowed_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            }


            extension = os.path.splitext(
                filename
            )[1].lower()


            if extension not in allowed_extensions:

                return jsonify({
                    "success": False,
                    "message":
                        "Only JPG, JPEG, PNG and WEBP images are allowed."
                }), 400


            # Create unique filename
            unique_filename = (
                f"{student_id}/"
                f"{uuid.uuid4().hex}"
                f"{extension}"
            )


            # Read image
            file_bytes = photo.read()


            # Upload image to Supabase Storage
            supabase.storage.from_(
                "complaint-photos"
            ).upload(
                unique_filename,
                file_bytes,
                {
                    "content-type":
                        photo.content_type
                }
            )


            # Get public URL
            photo_url = (
                supabase
                .storage
                .from_("complaint-photos")
                .get_public_url(
                    unique_filename
                )
            )


        # -------------------------------------------------
        # COMPLAINT DATA
        # -------------------------------------------------

        complaint_data = {

            "student_id":
                student_id,

            "student_name":
                student.get(
                    "name",
                    ""
                ),

            "roll_number":
                student.get(
                    "roll_number",
                    ""
                ),

            "category":
                category,

            "title":
                title,

            "description":
                description,

            "photo_url":
                photo_url,

            "status":
                "Pending"
        }


        # -------------------------------------------------
        # INSERT INTO SUPABASE
        # -------------------------------------------------

        result = (
            supabase
            .table("complaints")
            .insert(
                complaint_data
            )
            .execute()
        )


        # -------------------------------------------------
        # SUCCESS LOG
        # -------------------------------------------------

        print(
            "----------------------------------------"
        )

        print(
            "NEW COMPLAINT SAVED"
        )

        print(
            "Student:",
            student_id
        )

        print(
            "Category:",
            category
        )

        print(
            "Title:",
            title
        )

        print(
            "Photo uploaded:",
            bool(photo_url)
        )

        print(
            "----------------------------------------"
        )


        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "success":
                True,

            "message":
                "Complaint submitted successfully.",

            "complaint":
                result.data[0]
                if result.data
                else None

        })


    except Exception as error:

        print(
            "COMPLAINT ERROR:",
            repr(error)
        )


        return jsonify({

            "success":
                False,

            "message":
                "Unable to submit complaint right now."

        }), 500


# =========================================================
# MY COMPLAINTS API
# =========================================================

@app.route("/api/my-complaints")
def my_complaints():

    if "student_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    if supabase is None:

        return jsonify({
            "success": False,
            "message": "Supabase database is not connected."
        }), 500


    try:

        student_id = str(
            session.get("student_id")
        )


        result = (
            supabase
            .table("complaints")
            .select("*")
            .eq(
                "student_id",
                student_id
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )


        return jsonify({

            "success": True,

            "complaints":
                result.data or []

        })


    except Exception as error:

        print(
            "MY COMPLAINTS ERROR:",
            repr(error)
        )


        return jsonify({

            "success": False,

            "message":
                "Unable to load your complaints."

        }), 500
# =========================================================
# 18. STATUS API
# =========================================================

@app.route("/api/status")
def status():

    return jsonify({

        "application":
            "SmartAttendance V1",

        "ai_name":
            "Mugen",

        "creator":
            "Shiva Pandey",

        "created":
            "2025",

        "version":
            "V1",

        "supabase":
            supabase is not None,

        "groq":
            groq_client is not None,

        "knowledge_base":
            os.path.exists(
                KNOWLEDGE_FILE
            ),

        "logged_in":
            "student_id" in session

    })


# =========================================================
# 19. 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success": False,

        "message":
            "Page not found."

    }), 404


# =========================================================
# 20. RUN
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                5000
            )
        ),

        debug=True
    )
