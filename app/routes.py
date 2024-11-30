import bcrypt
import jwt
import datetime
import logging
import secrets
import hashlib
from flask import current_app as app,jsonify, request
from app.models import get_auth_db_connection, get_info_db_connection
from functools import wraps

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(*args, **kwargs)
    return decorated

def init_routes(app):
    #REGISTER NEW USER TO API
    @app.route("/register", methods=["POST"])
    def register():
        try:
            data = request.get_json()
            username = data["username"]
            password = data["password"].encode("utf-8")

            # Hash the password
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

            conn = get_auth_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO I_User (username, password) VALUES (?, ?)",
                (username, hashed_password.decode("utf-8")),
            )
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({"message": "User registered successfully"}), 201
        except Exception as e:
            app.logger.error(f"Error in /register: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500
    
    @app.route("/hello", methods=["POST"])
    def hello():
        return "WELCOME"
        

# LOGIN API
    @app.route("/login", methods=["POST"])
    def login():
        try:
            data = request.get_json()
            username = data["username"]
            password = data["password"].encode("utf-8")

            conn = get_auth_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, password FROM I_User WHERE username = ?", (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                stored_password = user[1].encode("utf-8") 
                if bcrypt.checkpw(password, stored_password):
                    # Generate a secure random token using CSPRNG
                    random_bytes = secrets.token_bytes(32)

                    # Hash the random bytes for added security
                    token_hash = hashlib.sha256(random_bytes).hexdigest()

                    token = jwt.encode(
                        {
                            "user_id": username,
                            "token_hash": token_hash,
                            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                        },
                        app.config["SECRET_KEY"],
                        algorithm="HS256",
                    )

                    return jsonify({
                        "status" : "Success",
                        "token": token})

            # Handle invalid login here
            return jsonify({"message": "Invalid username or password"}), 401

        except jwt.exceptions.PyJWTError as e:  # Catch specific JWT errors
            app.logger.error(f"Error encoding JWT: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

        except Exception as e:
            app.logger.error(f"Error in /login: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

# GET ALL USERS
    @app.route("/users", methods=["GET"])
    @token_required
    def get_users():
        try:
            conn = get_info_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
            PUT YOUR QUERY HERE TO GET EMPLOYEE DATA FROM YOUR TABLE 
            """)
            rows = cursor.fetchall()

            users = []
            for row in rows:
                npk, name, email, jabatan, dir,div,dept = row
                user_info = {
                    "NPK": npk,
                    "NAME": name,
                    "EMAIL": email,
                    "ROLE": jabatan,
                    "Directorat" : dir,
                    "Division" : div,
                    "Dept" : dept
                }
                users.append(user_info)

            conn.close()
            
            return jsonify({
            "status": "Success",
            "total_users": len(users),
            "users": users
            })
        except Exception as e:
            app.logger.error(f"Error in /users: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

# GET ALL STRUCTURES
    @app.route("/structures", methods=["GET"])
    @token_required
    def get_structures():
        level = request.args.get('level', 'subsect').lower()  # Default to 'subsect' if not provided
        dirname = request.args.get('dirname')
        divname = request.args.get('divname')
        dptname = request.args.get('dptname')

        try:
            conn = get_info_db_connection()
            cursor = conn.cursor()

            # Build SQL query dynamically based on the level
            query = "SELECT distinct "
            if level == 'dir':
                query += "dir, dirName, idLokasi "
            elif level == 'div':
                query += "dir, dirName, div, div_name, idLokasi "
            elif level == 'dpt':
                query += "dir, dirName, div, div_name, dept, deptName, idLokasi "
            elif level == 'sct':
                query += "dir, dirName, div, div_name, dept, deptName, sec, idLokasi "
            elif level == 'subsect':
                query += "dir, dirName, div, div_name, dept, deptName, sec, subsec, idLokasi "
            else:
                return jsonify({"error": "Invalid level parameter"}), 400

            query += " FROM HRIS_TrAD"

            # Add filtering conditions if provided
            conditions = []
            if dirname:
                conditions.append(f"dir = '{dirname}'")
            if divname:
                conditions.append(f"div_name = '{divname}'")
            if dptname:
                conditions.append(f"deptName = '{dptname}'")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query)
            rows = cursor.fetchall()

            # Continue processing the results as per your existing logic
            # Create a nested dictionary to represent the structure
            structure = {}
            for row in rows:
                if level == 'dir':
                    dir_code, dir_name, lokasi = row
                    structure.setdefault(dir_code, {}).update({
                        "DIRNAME": dir_name,
                        "LOKASI": lokasi,
                        "DIVISIONS": {}
                    })
                elif level == 'div':
                    dir_code, dir_name, div_code, div_name, lokasi = row
                    structure.setdefault(dir_code, {}).setdefault("DIVISIONS", {}).setdefault(div_code, {}).update({
                        "DIVNAME": div_name,
                        "LOKASI": lokasi,
                        "DEPARTMENTS": {}
                    })
                elif level == 'dpt':
                    dir_code, dir_name, div_code, div_name, dpt_code, dpt_name, lokasi = row
                    structure.setdefault(dir_code, {}).setdefault("DIVISIONS", {}).setdefault(div_code, {}).setdefault("DEPARTMENTS", {}).setdefault(dpt_code, {}).update({
                        "DPTNAME": dpt_name,
                        "LOKASI": lokasi,
                        "SECTION": {}
                    })
                elif level == 'sct':
                    dir_code, dir_name, div_code, div_name, dpt_code, dpt_name, sct_name, lokasi = row
                    structure.setdefault(dir_code, {}).setdefault("DIVISIONS", {}).setdefault(div_code, {}).setdefault("DEPARTMENTS", {}).setdefault(dpt_code, {}).setdefault("SECTION", {}).setdefault(sct_name, {}).update({
                        "SECNAME": sct_name,
                        "LOKASI": lokasi,
                        "SUBSECTION": {}
                    })
                elif level == 'subsect':
                    dir_code, dir_name, div_code, div_name, dpt_code, dpt_name, sct_name, subsect_name, lokasi = row
                    structure.setdefault(dir_code, {}).setdefault("DIVISIONS", {}).setdefault(div_code, {}).setdefault("DEPARTMENTS", {}).setdefault(dpt_code, {}).setdefault("SECTION", {}).setdefault(sct_name, {}).setdefault("SUBSECTION", {}).setdefault(subsect_name, {}).update({
                        "SUBSECNAME": subsect_name,
                        "LOKASI": lokasi
                    })

            # Convert the nested dictionary to the desired JSON format
            def format_structure(data, level_key):
                result = []
                for code, info in data.items():
                    item = {level_key: code}
                    item.update({k: v for k, v in info.items() if not isinstance(v, dict)})
                    for child_level_key, child_data in info.items():
                        if isinstance(child_data, dict):
                            item[child_level_key] = format_structure(child_data, child_level_key[:-1])  # Remove trailing 'S'
                    result.append(item)
                return result

            result = format_structure(structure, "DIR")
            conn.close()
            return jsonify(result)

        except Exception as e:
            app.logger.error(f"Error in get structures /structures: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

# GET USER by NPK
    @app.route("/users/npk/<int:user_id>", methods=["GET"])
    @token_required
    def get_user_npk(user_id):
        try:
            conn = get_info_db_connection()
            cursor = conn.cursor()

            # Execute the SQL query to fetch the user by NPK
            cursor.execute("PUT YOUR QUERY HERE TO GET EMPLOYEE DATA FROM YOUR TABLE WHERE npk = ?",(user_id,),)
            row = cursor.fetchone()

            # Check if the user was found
            if row:
                npk, name, email, jabatan = row
                user_info = {"NPK": npk, "NAME": name, "EMAIL": email, "ROLE": jabatan}
                conn.close()
                return jsonify(user_info)
            else:
                conn.close()
                return jsonify({"error": "User not found"}), 404

        except Exception as e:
            app.logger.error(f"Error in /users/npk/{user_id}: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

       # GET USER by USERNAME
    @app.route("/users/username/<string:username>", methods=["GET"])
    @token_required
    def get_username(username):
        try:
            conn = get_info_db_connection()
            cursor = conn.cursor()

            # Execute the SQL query to fetch the user by NPK
            cursor.execute(
                "SELECT npk, username, name, email, jabatan FROM HRIS_TrAD WHERE username = ?",
                (username,),
            )
            row = cursor.fetchone()

            # Check if the user was found
            if row:
                npk, username, name, email, jabatan = row
                user_info = {
                    "NPK": npk,
                    "NAME": name,
                    "USERNAME": username,
                    "EMAIL": email,
                    "ROLE": jabatan,
                }
                conn.close()
                return jsonify(user_info)
            else:
                conn.close()
                return jsonify({"error": "User not found"}), 404

        except Exception as e:
            app.logger.error(f"Error in /users/username/{username}: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

# GET STRUCTURES by DIR
    @app.route("/structures/dir/<string:dir_id>", methods=["GET"])
    @token_required
    def get_structures_by_dir(dir_id):
        try:
            conn = get_info_db_connection()
            cursor = conn.cursor()
            cursor.execute("PUT YOUR QUERY HERE TO GET EMPLOYEE DATA FROM YOUR TABLE Where dir = ?",(dir_id,),)
            rows = cursor.fetchall()

            # Organize the data into a hierarchical structure
            structure = {}
            for row in rows:
                (
                    dir_code,
                    dir_name,
                    div_code,
                    div_name,
                    dept_code,
                    dept_name,
                    npk,
                    name,
                    email,
                    jabatan,
                ) = row

                # Ensure the directorate exists in the structure
                if dir_code not in structure:
                    structure[dir_code] = {
                        "DIRNAME": dir_name,
                        "DIVISIONS": {},
                        "DIRHEAD": [],
                    }

                # Ensure the division exists under the directorate
                if div_code not in structure[dir_code]["DIVISIONS"]:
                    structure[dir_code]["DIVISIONS"][div_code] = {
                        "DIVNAME": div_name,
                        "DEPARTMENTS": {},
                        "DIVHEAD": [],
                    }

                # Add the department under the division
                if (
                    dept_code
                    not in structure[dir_code]["DIVISIONS"][div_code]["DEPARTMENTS"]
                ):
                    structure[dir_code]["DIVISIONS"][div_code]["DEPARTMENTS"][
                        dept_code
                    ] = {"DPTNAME": dept_name, "DPTHEAD": []}

                person_info = {
                    "NPK": npk,
                    "NAME": name,
                    "EMAIL": email,
                    "ROLE": jabatan,
                }

                if jabatan and "director" in jabatan.lower():
                    structure[dir_code]["DIRHEAD"].append(person_info)

                if jabatan and "division head" in jabatan.lower():
                    structure[dir_code]["DIVISIONS"][div_code]["DIVHEAD"].append(person_info)

                if jabatan and "department head" in jabatan.lower():
                    structure[dir_code]["DIVISIONS"][div_code]["DEPARTMENTS"][dept_code]["DPTHEAD"].append(person_info)

            # Convert structure to the desired JSON format
            result = []
            for dir_code, dir_data in structure.items():
                dir_info = {
                    "DIR": dir_code,
                    "DIRNAME": dir_data["DIRNAME"],
                    "DIRHEAD": dir_data["DIRHEAD"],
                    "DIVISIONS": [],
                }
                for div_code, div_data in dir_data["DIVISIONS"].items():
                    div_info = {
                        "DIV": div_code,
                        "DIVNAME": div_data["DIVNAME"],
                        "DIVHEAD": div_data["DIVHEAD"],
                        "DEPARTMENTS": [
                            {
                                "DPT": dept_code,
                                "DPTNAME": dept_data["DPTNAME"],
                                "DPTHEAD": dept_data["DPTHEAD"],
                            }
                            for dept_code, dept_data in div_data["DEPARTMENTS"].items()
                        ],
                    }
                    dir_info["DIVISIONS"].append(div_info)
                result.append(dir_info)

            conn.close()
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Error in /structures/dir/{dir_id}: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

    # GET STRUCTURES by DIV
    @app.route("/structures/div/<string:div_id>", methods=["GET"])
    @token_required
    def get_structures_by_div(div_id):
        try:
            conn = get_info_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "PUT YOUR QUERY HERE TO GET EMPLOYEE DATA FROM YOUR TABLE WHERE div = ?",
                (div_id,),
            )
            rows = cursor.fetchall()

            # Organize the data into a hierarchical structure
            structure = {}
            for row in rows:
                (
                    div_code,
                    div_name,
                    dept_code,
                    dept_name,
                    npk,
                    name,
                    email,
                    jabatan,
                ) = row

                # Ensure the division exists in the structure
                if div_code not in structure:
                    structure[div_code] = {
                        "DIVNAME": div_name,
                        "DEPARTMENTS": {},
                        "DIVHEAD": [],
                    }

                # Add the department under the division
                if dept_code not in structure[div_code]["DEPARTMENTS"]:
                    structure[div_code]["DEPARTMENTS"][dept_code] = {
                        "DPTNAME": dept_name,
                        "DPTHEAD": [],
                    }

                # Add the person to the division or department if their job title contains "head"
                person_info = {
                    "NPK": npk,
                    "NAME": name,
                    "EMAIL": email,
                    "JABATAN": jabatan,
                }

                if "division head" in jabatan.lower():
                    structure[div_code]["DIVHEAD"].append(person_info)

                if "department head" in jabatan.lower():
                    structure[div_code]["DEPARTMENTS"][dept_code]["DPTHEAD"].append(
                        person_info
                    )

            # Convert structure to the desired JSON format
            result = []
            for div_code, div_data in structure.items():
                div_info = {
                    "DIV": div_code,
                    "DIVNAME": div_data["DIVNAME"],
                    "DIVHEAD": div_data["DIVHEAD"],
                    "DEPARTMENTS": [
                        {
                            "DPT": dept_code,
                            "DPTNAME": dept_data["DPTNAME"],
                            "DPTHEAD": dept_data["DPTHEAD"],
                        }
                        for dept_code, dept_data in div_data["DEPARTMENTS"].items()
                    ],
                }
                result.append(div_info)

            conn.close()
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Error in /structures/div/{div_id}: {e}", exc_info=True)
            return jsonify({"error": "Internal server error"}), 500

