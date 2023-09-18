import os
import string
import re
import uuid
import requests
import pdfplumber
import io
import urllib

from flask import render_template, request, session, redirect, url_for
from flask_login import login_user, logout_user, login_required
from wtforms import ValidationError
from werkzeug.utils import secure_filename
from pymongo import MongoClient

from models import app, Users, db, login_manager
from oauth import google
from config import Config
from cli import create_db
from field_ml import get_form_field_type
from sendMail import send_mail


app.config.from_object(Config)
app.cli.add_command(create_db)
app.register_blueprint(google.blueprint, url_prefix="/login")
db.init_app(app)
login_manager.init_app(app)
client = MongoClient(Config.CONNECTION_STRING)

# enabling insecure login for OAuth login
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/dashboard")
@login_required
def dashboard():
    dbname = client['healthpulse_db']
    collection_name = dbname["health_form"]
    user_data = collection_name.find({"id": session.get("user_id")})
    final_response = {}
    for data in user_data:
        for d in data:
            if "’s" in d:
                s = d.replace("’s", "")
            else:
                s = d
            if "_id" in d:
                continue
            if s in final_response:
                final_response[s].append(data[d])
            else:
                final_response[s] = [data[d]]
    responses = list(final_response)
    upper_limits = []
    lower_limits = []
    field_values = []
    for i in range(8, len(responses)):
        temp = []
        for j in range(len(final_response[responses[i]])):
            temp.append(float(final_response[responses[i]][j][0]))
        upper_limits.append(final_response[responses[i]][0][2])
        lower_limits.append(final_response[responses[i]][0][1])
        field_values.append(temp)
        
    return render_template('dashboard.html', patient_details=final_response, field_names=responses[8:], upper_limits=upper_limits, lower_limits=lower_limits, field_values=field_values)


@app.route('/upload_health_form', methods=["POST", "GET"])
@login_required
def upload_health_form():
    if request.method == "POST":
        file = request.files['application_form']
        if file:
            filename = file.filename
            filetype = file.content_type
            filename = secure_filename(filename)
            static = os.path.join(os.path.curdir, "static")
            files = os.path.join(static, "files")
            location = os.path.join(files, filename)
            file.save(location)
            access_token = get_auth_token()
            ocr_response = create_searchable_pdf(access_token, filename, location, filetype)
            file_id = ocr_response['resultItems'][0]['files'][0]['value']
            accept_response = ocr_response['resultItems'][0]['files'][0]['contentType']
            capture_url = f'{Config.BASE_URL}/capture/cp-rest/v2/session/files/{file_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': accept_response
            }
            response = requests.get(capture_url, headers=headers)
            if response.status_code == 200:
                file_content = response.content
                final_response = ''
                with pdfplumber.open(io.BytesIO(file_content)) as my_file:
                    num_pages = len(my_file.pages)
                    for page_number in range(num_pages):
                        page = my_file.pages[page_number]
                        text = page.extract_text()
                        final_response += text
                os.remove(location)
                health_form_data = health_form_parser(final_response)
                dbname = client['healthpulse_db']
                collection_name = dbname["health_form"]
                collection_name.insert_one(health_form_data)
                return redirect(url_for("home"))
            else:
                return "Failed to retrieve the file", 500   
    return render_template("upload_report.html")


@app.route("/upload_form", methods=["POST", "GET"])
@login_required
def upload_form():
    if request.method == "POST":
        file = request.files['application_form']
        if file:
            filename = file.filename
            filetype = file.content_type
            filename = secure_filename(filename)
            static = os.path.join(os.path.curdir, "static")
            files = os.path.join(static, "files")
            location = os.path.join(files, filename)
            file.save(location)
            access_token = get_auth_token()
            ocr_response = create_searchable_pdf(access_token, filename, location, filetype)
            file_id = ocr_response['resultItems'][0]['files'][0]['value']
            accept_response = ocr_response['resultItems'][0]['files'][0]['contentType']
            capture_url = f'{Config.BASE_URL}/capture/cp-rest/v2/session/files/{file_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': accept_response
            }
            response = requests.get(capture_url, headers=headers)
            if response.status_code == 200:
                file_content = response.content
                final_response = ''
                with pdfplumber.open(io.BytesIO(file_content)) as my_file:
                    num_pages = len(my_file.pages)
                    for page_number in range(num_pages):
                        page = my_file.pages[page_number]
                        text = page.extract_text()
                        final_response += text
                if css_download(access_token, location, files):
                    print("Download done")
                os.remove(location)
                final_fields = form_parser(final_response)
                
                return redirect(url_for('form', final_fields=urllib.parse.quote_plus(final_fields)))
                
            else:
                return "Failed to retrieve the file", 500   
    return render_template("upload_form.html")


@app.route('/application_form', methods=['POST', 'GET'])
@login_required
def form():    
    if request.method == "POST":
        dbname = client['healthpulse_db']
        collection_name = dbname["application_form"]
        user_data = collection_name.find({"id": session.get("user_id")})
        user_response = []
        final_dict = {}
        
        for i in range(15):
            user_response.append(request.form[f'form_field_{i}'])
        for data in user_data:
            itr = 0
            for d in data:
                if (itr == 15):
                    break
                if 'id' in d:
                    final_dict[d] = data[d]
                    continue
                if data[d] != "":
                    break
                else:
                    final_dict[d] = user_response[itr]
                    itr += 1
        collection_name.update_one({"_id": final_dict["_id"], "id": session.get("user_id")}, {"$set": final_dict})
        return redirect(url_for("home"))
    
    fields = request.args.get("final_fields")
    final_fields = fields.replace("+", " ")
    final_fields = final_fields.replace("%3A", ": ")
    final_fields = final_fields.split(": ")
    temp = {"id": session["user_id"]}
    for field in final_fields:
        temp[field] = ''
    dbname = client['healthpulse_db']
    collection_name = dbname["application_form"]
    collection_name.insert_one(temp)
    fields = get_form_field_type(final_fields)
    
    return render_template('display_form.html', fields=fields)


@app.route('/sign_up', methods=['GET', 'POST'])
def signup():
    if session.get("user_id"):
        return redirect(url_for('home'))
    email_flag = False
    username_flag = False
    password_flag = False

    if request.method == "POST":
        user_name = request.form['username']
        email = request.form['email']
        password = request.form['password']

        password_flag = check_password(password)
        try:
            email_flag = check_mail(email)
        except ValidationError:
            email_flag = True

        try:
            username_flag = check_username(user_name)
        except ValidationError:
            username_flag = True

        if not username_flag and not email_flag and not password_flag and password_flag != "short":
            unique_id = uuid.uuid4().hex[:8]
            user = Users(unique_id, None, None, user_name, email, password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            login_user(user)

            return redirect(url_for('home'))

    return render_template('sign-up.html',
                           email_flag=email_flag,
                           username_flag=username_flag,
                           password_flag=password_flag)


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if session.get("user_id"):
        return redirect(url_for('home'))
    flag = False
    if request.method == "POST":
        user = Users.query.filter_by(email=request.form['username']).first()
        if user is None:
            user = Users.query.filter_by(user_name=request.form['username']).first()
        if user is not None:
            if user.check_password(request.form['password']):
                user = Users.query.filter_by(email=user.email).first()
                session['user_id'] = user.id
                login_user(user)
                return redirect(url_for("home"))
            else:
                flag = True
        else:
            flag = True
    return render_template('sign-in.html', flag=flag)


@app.route("/logout")
@login_required
def logout():
    session.pop('user_id', None)
    logout_user()
    return redirect(url_for("home"))


@app.route('/contact_us', methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form['txtName']
        email = request.form['txtEmail']
        phone = request.form['txtPhone']
        msg = request.form['txtMsg']
        send_mail(name, email, phone, msg)
    return render_template('contact-us.html')


@app.route('/about_us')
def about_us():
    return render_template('about-us.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def page_not_found(error):
    return render_template('403.html'), 403



def health_form_parser(form_string):
    fields_dict = {"id": session.get("user_id")}
    fields = form_string.split("\n")

    for field in fields:
        if field != '' and ':' in field:
            key, value = field.split(': ', 1)
            response = []
            if '-' in value:
                actual_value = value.split(' ')[0]
                lower_range = value.split(' ')[1].split('-')[0]
                upper_range = value.split(' ')[1].split('-')[1]
                is_healthy = False
                if float(actual_value) >= float(lower_range) and float(actual_value) <= float(upper_range):
                    is_healthy = True
                response.append(actual_value)
                response.append(lower_range)
                response.append(upper_range)
                response.append(is_healthy)
                value = response
            fields_dict[key] = value
    return fields_dict

def form_parser(form_string):
    final_fields = ""
    fields = form_string.split("\n")
    for field in fields:
        if field != '' and ':' in field:
            final_fields += field
    return final_fields

def get_auth_token():
    auth_url = f"{Config.BASE_URL}/tenants/{Config.TENANT_ID}/oauth2/token"
    payload = {
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "grant_type": "password",
        "username": Config.USERNAME,
        "password": Config.PASSWORD
    }

    response = requests.post(auth_url, json=payload)

    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access_token')
        return access_token
    else:
        return None

def handle_upload(file_path, access_token, filetype):
    url = f"{Config.BASE_URL}/capture/cp-rest/v2/session/files"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/hal+json',
        'Accept-Language': 'en-US',
        'Content-Type': filetype
    }
    
    if access_token:
        with open(file_path, 'rb') as file:
            response = requests.post(url, headers=headers, data=file)
        if response.status_code == 200:
            data = response.json()
            return data
    else:
        return None

def create_searchable_pdf(access_token, file_name, file_path, filetype):
    data = handle_upload(file_path, access_token, filetype)
    captured_file_id = data['id']
    file_type = data['contentType']

    url = f'{Config.BASE_URL}/capture/cp-rest/v2/session/services/fullpageocr'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/hal+json',
        'Accept-Language': 'en-US',
        'Content-Type': 'application/hal+json'
    }
    
    payload = {
        "serviceProps": [
            {"name": "Env", "value": "D"},
            {"name": "OcrEngineName", "value": "Advanced"}
        ],
        "requestItems": [
            {
                "nodeId": 1,
                "values": [{"name": "OutputType", "value": "pdf"}],
                "files": [
                    {
                        "name": file_name,
                        "value": captured_file_id,
                        "contentType": file_type
                    }
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        ocr_response = response.json()
        return ocr_response
    else:
        return None

def css_download(access_token, file_path, files):
    url = f"{Config.CSS_URL}/v2/content"
    headers = {
        'Authorization': f"Bearer {access_token}"
    }

    with open(file_path, 'rb') as file:
        response = requests.post(url, headers=headers, data=file)
    
    file_id = response.json()['entries'][0]['id']
    object_id = response.json()['entries'][0]['objectId']
    url_new = f"{Config.CSS_URL}/v2/content/{file_id}/download?object-id={object_id}&avs-scan=false"

    response_new = requests.get(url_new, headers=headers)

    if response_new.status_code == 200:
        with open(f'{files}/{uuid.uuid4().hex[:8]}.pdf', 'wb') as file:
            file.write(response_new.content)
        return True
    else:
        print('Failed to download file. Status code:', response_new.status_code)
        return False

def check_mail(data):
    if Users.query.filter_by(email=data).first():
        raise ValidationError('Your email is already registered.')
    else:
        return False

def check_username(data):
    if Users.query.filter_by(user_name=data).first():
        raise ValidationError('This username is already registered.')
    else:
        return False

def check_password(data):
    special_char = string.punctuation
    if len(data) < 6:
        return "short"
    elif not re.search("[a-zA-Z]", data):
        return True
    elif not re.search("[0-9]", data):
        return True
    for char in data:
        if char in special_char:
            break
    else:
        return True
    return False


if __name__ == '__main__':
    app.run(debug=True)
