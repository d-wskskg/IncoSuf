from importlib.resources import path
from flask import *
from flask_sqlalchemy import *
import random
import smtplib
from email.message import EmailMessage
from flask_login import *
from flask_login import *
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import *
from Blockchain import Blockchain
import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "IncoSuf"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voters.db"
app.config["SQLALCHEMY_BINDS"] = { 
    "admin" : "sqlite:///admin.db",
    "polls" : "sqlite:///polls.db",
    "positions" : "sqlite:///positions.db",
    "candidates" : "sqlite:///candidates.db",
    "logs" : "sqlite:///logs.db"
}

db = SQLAlchemy(app)

blockchain = Blockchain()

voted = []

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(voters_id):
    return Voters.query.get(int(voters_id))





class Voters(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) 
    email = db.Column( db.String(200),nullable=False, unique=True)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return "<Voters %r>" % self.id

db.create_all()
db.session.commit()





@app.route("/")
@app.route("/home_page", methods=["GET", "POST"])
def home_page():
    session.clear()
    return render_template("home_page.html")





@app.route("/login", methods=["GET", "POST"])
def login():
    logout_user()
    return render_template("login_page.html")





@app.route("/get_otp", methods=["GET", "POST"])
def get_otp():
    
    try:
        email = request.form["email"]

        voter_id = Voters.query.filter_by(email=email).first()
        voter_id = (voter_id.id)

        if voter_id in voted:
            flash("You already voted, thank you for using IncoSuf")
            return redirect("/login")

    except:
        flash("Email does not exist")
        return redirect("/login")

    exists = Voters.query.filter_by(email=email).count()

    if exists > 0:
        session["email"] = str(email)
        send_otp(email)
        flash("OTP Successfully Sent!")
        return render_template("otp_login.html", email=email)

    else:
        flash("Email does not exist")
        return render_template("login_page.html")

def send_otp(email):
    message = EmailMessage()
    otp = generate_otp()
    otp_name = generate_otp()
    session["otp_name"] = otp_name
    session["response"] = str(otp)
    message.set_content(
        f"""
You are coded/named {otp_name} in the blockchain.

Your IncoSuf OTP is {otp}
        """
    )
    message["Subject"] = "IncoSuf OTP"
    message["From"] = "incosuf@gmail.com"
    message["To"] = email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("incosuf@gmail.com", "vzcgyzuujfkwgmuf")
    server.send_message(message)
    server.quit()

def generate_otp():
    OTP = "".join([str(random.randint(0,9)) for i in range(6)])
    return OTP





@app.route("/otp_login", methods=["GET", "POST"])
def otp_login():
    
    position = Positions.query.all()
    position = Positions.query.first()
    position = position.position


    try:
        otp = request.form["otp"]
    except:
        flash("Please login to access this page")
        return redirect("/login")

    if "response" and "email" in session:
        s = session["response"]
        session.pop("response", None)
        user = session["email"]
        session.pop("email", None)

        if s == otp:
            user = Voters.query.filter_by(email=user).first()
            login_user(user)
            return redirect(url_for("voting_page", position=position))
        else:
            flash("Wrong OTP")
            return render_template("login_page.html")

    return redirect("/login")





vote_count = {}
position_voted = {}
@app.route("/voting_page", methods=["GET", "POST"])
@app.route("/voting_page/<position>", methods=["GET", "POST"])
@login_required
def voting_page(position):

    # fhand = open("blockchain.json", "w")
    # block = json.dumps(block)
    # fhand.write(block)
    # fhand.close()
    cur = position

    poll_date = Polls.query.all()

    for poll in poll_date:
        poll_date1 = poll.from_date
        poll_date1 = datetime.datetime.strptime(poll_date1,"%Y-%m-%d")
        poll_date2 = poll.to_date
        poll_date2 = datetime.datetime.strptime(poll_date2,"%Y-%m-%d")
        date_now = datetime.datetime.today()

        if date_now >= poll_date1 and date_now <= poll_date2:
            break
        else:
            flash("No ongoing polls")
            return redirect("/login")

    candidate = Candidates.query.all()

    if len(vote_count) < 1:
        for c in candidate:
            c = c.name
            vote_count[c] = 0

    pos = Positions.query.all()
    if len(position_voted) < 1:
        for p in pos:
            p = p.position
            position_voted[p] = []

    try:
        position = Positions.query.filter_by(position=position).first()
        id = position.id

        candidate = Candidates.query.filter_by(position_id=id).all()

        if request.method == "POST":
            name = request.form["name"]
            cur_pos = request.form["cur_pos"]
            if check_if_voted(cur_pos):
                vote_count[name] += 1
                dic_list = position_voted[cur_pos]
                dic_list.append(current_user.id)
                position_voted[cur_pos] = dic_list
                voter = Voters.query.filter_by(id=current_user.id).first()
                voter = voter.name
                get_block(name, voter)

    except:

        if request.method == "POST":
            name = request.form["name"]
            cur_pos = request.form["cur_pos"]
            if check_if_voted(cur_pos):
                vote_count[name] += 1
                dic_list = position_voted[cur_pos]
                dic_list.append(current_user.id)
                position_voted[cur_pos] = dic_list
                voter = Voters.query.filter_by(id=current_user.id).first()
                voter = voter.name
                get_block(name, voter)

        voted.append(current_user.id)
        return redirect(url_for("tracking"))

    try:
        next_position = Positions.query.filter_by(id=(id+1)).first()
        next_position = next_position.position
    except:
        voted.append(current_user.id)
        next_position = redirect(url_for("tracking"))

    try:

        filename = candidate.filename
        display_image = url_for("static", filename="uploads/" + filename)
        
        return render_template("voting_page.html", candidate=candidate, position=position, display_image=display_image, next_position=next_position)
    
    except:
        return render_template("voting_page.html", candidate=candidate, position=position, next_position=next_position)

def get_block(name, voter):

    previous_block = blockchain.previous_block()
    previous_proof = previous_block["7_proof"]
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.previous_hash()
    voter = session["otp_name"]
    vote = name

    blockchain.create_block(proof, previous_hash, vote, voter)
    # block = blockchain.create_block(proof, previous_hash, vote, voter)
    # blockchain.create_blockchain(proof, previous_hash, voter, vote)

    # response = {
    #     "index" : block["index"],
    #     "voter" : voter,
    #     "vote" : vote,
    #     "timestamp" : block["timestamp"],
    #     "proof" : block["proof"],
    #     "previous_hash" : block["previous_hash"]
    # }

def check_if_voted(cur_pos):
    check_this_list = list(position_voted[cur_pos])
    if current_user.id not in check_this_list:
        return True



# def write_json(data):
#     fhand = open("blockchain.json", "w")
#     # old_data = fhand.read()
#     fhand = fhand.read()
#     old_data = json.load(fhand)
#     old_data.update(data)
#     json.dump(old_data, fhand)





@app.route("/tracking", methods=["GET", "POST"])
def tracking():

    session.clear()
    positions = Positions.query.all()
    candidates = Candidates.query.all()
    
    return render_template("tracking.html", positions=positions, candidates=candidates, vote_count=vote_count)















# ----------------------- HERE LIES ADMIN CODES ----------------------
from functools import *

class Admin(db.Model, UserMixin):
    __bind_key__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True) 
    password = db.Column( db.String(256),nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return "<Admin %r>" % self.id

db.create_all()
db.session.commit()





class Polls(db.Model, UserMixin):
    __bind_key__ = "polls"
    id = db.Column(db.Integer, primary_key=True)
    poll = db.Column( db.String(100),nullable=False)
    from_date = db.Column( db.String(100),nullable=False)
    to_date = db.Column( db.String(100),nullable=False)
    positions = db.relationship("Positions", backref="position_poll")
    polls = db.relationship("Candidates", backref="candidate_poll")

    def __init__(self, poll, from_date, to_date):
        self.poll = poll
        self.from_date = from_date
        self.to_date = to_date
        

    def __repr__(self):
        return "<Polls %r>" % self.id





class Positions(db.Model, UserMixin):
    __bind_key__ = "positions"
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column( db.String(100),nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id"))
    candidates = db.relationship("Candidates", backref="candidate_position")

    def __init__(self, position, poll_id):
        self.position = position
        self.poll_id = poll_id
        

    def __repr__(self):
        return "<Poisitions %r>" % self.id

db.create_all()
db.session.commit()

class Logs(db.Model, UserMixin):
    __bind_key__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    log = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __init__(self, log, date):
        self.log = log
        self.date = date

    def __repr__(self):
        return "<Logs %r>" % self.id

db.create_all()
db.session.commit()



class Candidates(db.Model, UserMixin):
    __bind_key__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column( db.String(200),nullable=False)
    college = db.Column( db.String(200),nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"))
    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id"))
    filename = db.Column(db.String(200), nullable=False)

    def __init__(self, name, college, position_id, poll_id, filename):
        self.name = name
        self.college = college
        self.position_id = position_id
        self.poll_id = poll_id
        self.filename = filename
        

    def __repr__(self):
        return "<Candidates %r>" % self.id

db.create_all()
db.session.commit()





def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to access this page")
            return redirect("/admin_login")
    return wrap
# admin_manager = LoginManager()
# admin_manager.init_app(app)
# admin_manager.login_view = "admin_login"

# @admin_manager.user_loader
# def load_admin(admin_id):
#     return Admin.query.get(int(admin_id))
# login_manager2 = LoginManager()
# login_manager2.init_app(app)
# login_manager2.login_view = "admin_login"

# @login_manager2.user_loader
# def load_user2(admin_id):
#     return Voters.query.get(int(admin_id))





@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    session.clear()
    if request.method == "POST":
        
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username).count()

        if admin > 0:
            admin = Admin.query.filter_by(username=username).first()
            check = check_password_hash(admin.password, password)

            if check:
                session["admin_logged_in"] = True
                session["admin_username"] = admin.username
                # login_user(admin)
                return redirect("/polls")
            else:
                flash("Incorrect username or password")
                return render_template("admin_login.html")

        else:
            flash("Incorrect username or password")
            return render_template("admin_login.html")

    return render_template("admin_login.html")





@app.route("/admin_logout", methods=["GET", "POST"])
@admin_required
def admin_logout():
    logout_user()
    flash("Logged out")
    return redirect("/admin_login")





@app.route("/polls", methods=["GET", "POST"])
@admin_required
def polls():

    poll = Polls.query.all()

    return render_template("polls.html", poll=poll)





@app.route("/poll/add_poll", methods=["GET", "POST"])
@admin_required
def add_poll():

    poll = Polls.query.all()

    if request.method == "POST":

        if not request.form["poll_name"] and not request.form["from_date"] and not request.form["to_date"]:
            flash("FILL ALL FIELDS")
            return render_template("add_position.html")

        else:
            poll = Polls(request.form["poll_name"], request.form["from_date"], request.form["to_date"])

            flash("Successfully added!")
            
            log = Logs(f"""{session["admin_username"]} added the poll {request.form["poll_name"]}""", datetime.datetime.now())
            db.session.add(log)

            db.session.add(poll)
            db.session.commit()

            return redirect(url_for("polls"))
    
    return render_template("add_poll.html")





@app.route("/update_poll/<int:id>", methods=["GET", "POST"])
@admin_required
def update_poll(id):

    update_id = Polls.query.get_or_404(id)
    
    poll_date = Polls.query.filter_by(id=id).first()
    poll_date1 = poll_date.from_date
    poll_date1 = datetime.datetime.strptime(poll_date1,"%Y-%m-%d")
    poll_date2 = poll_date.to_date
    poll_date2 = datetime.datetime.strptime(poll_date2,"%Y-%m-%d")
    date_now = datetime.datetime.today()

    if date_now > poll_date1 and date_now < poll_date2:
        flash("Ongoing poll, admin prohibited from editing")
        return redirect("/polls")

    if request.method == "POST":

        log = Logs(f"""{session["admin_username"]} updated poll {update_id.poll} to {request.form["poll_name"]}""", datetime.datetime.now())
        db.session.add(log)

        update_id.poll = request.form["poll_name"]
        update_id.from_date = request.form["from_date"]
        update_id.to_date = request.form["to_date"]
        flash("UPDATED SUCCESSFULLY!")
        db.session.commit()
        return redirect("/polls")
        
    else:
        return render_template("update_poll.html", update_id=update_id)





@app.route("/poll/delete_poll/<int:id>", methods=["GET", "POST"])
@admin_required
def delete_poll(id):

    delete_id = Polls.query.get_or_404(id)
    candidate_data = Candidates.query.filter_by(poll_id=id).all()
    position_data = Positions.query.filter_by(poll_id=id).all()

    poll_date = Polls.query.filter_by(id=id).first()
    poll_date1 = poll_date.from_date
    poll_date1 = datetime.datetime.strptime(poll_date1,"%Y-%m-%d")
    poll_date2 = poll_date.to_date
    poll_date2 = datetime.datetime.strptime(poll_date2,"%Y-%m-%d")
    date_now = datetime.datetime.today()

    if date_now > poll_date1 and date_now < poll_date2:
        flash("Ongoing poll, admin prohibited from editing")
        return redirect("/polls")

    for data in candidate_data:
        picture_file = os.path.join(app.config["UPLOAD_FOLDER"], data.filename)
        os.remove(picture_file)
        db.session.delete(data)
        
        if data.position_id is None:
            db.session.delete(data)

    for p in position_data:
        db.session.delete(p)

    flash("POLL DELETED!")

    log = Logs(f"""{session["admin_username"]} deleted poll {poll_date.poll}""", datetime.datetime.now())
    db.session.add(log)

    db.session.delete(delete_id)
    db.session.commit()

    return redirect("/polls")





@app.route("/position/<poll>", methods=["GET", "POST"])
@admin_required
def position(poll):

    poll_date = Polls.query.filter_by(poll=poll).first()
    poll_date1 = poll_date.from_date
    poll_date1 = datetime.datetime.strptime(poll_date1,"%Y-%m-%d")
    poll_date2 = poll_date.to_date
    poll_date2 = datetime.datetime.strptime(poll_date2,"%Y-%m-%d")
    date_now = datetime.datetime.today()

    if date_now > poll_date1 and date_now < poll_date2:
        flash("Ongoing poll, admin prohibited from editing")
        return redirect("/polls")


    pol = Polls.query.filter_by(poll=poll).first()
    pol_id = pol.id
    poll = pol.poll

    position = Positions.query.filter_by(poll_id=pol_id).all()

    # try:
    #     filename = candidate.filename
    #     display_image = url_for("static", filename="uploads/" + filename)

    #     return render_template("candidate_view.html", candidate=candidate, position=position, display_image=display_image)

    # except:
    #     return render_template("candidate_view.html", candidate=candidate, position=position)

    # position = Positions.query.all()

    return render_template("position.html", position=position, poll=poll)





@app.route("/add_position/<poll>", methods=["GET", "POST"])
@admin_required
def add_position(poll):

    if request.method == "POST":

        if not request.form["position"]:
            flash("FILL ALL FIELDS")
            return render_template("add_position.html")

        else:
            poll_id = Polls.query.filter_by(poll=poll).first()
            poll_id = poll_id.id
            position = Positions(request.form["position"], poll_id)

            flash("Successfully added!")

            log = Logs(f"""{session["admin_username"]} added position {request.form["position"]}""", datetime.datetime.now())
            db.session.add(log)

            db.session.add(position)
            db.session.commit()

            return redirect(url_for("position", poll=poll)) 
    
    return render_template("add_position.html", poll=poll)





@app.route("/delete/<int:id>", methods=["GET", "POST"])
@admin_required
def delete_position(id):

    delete_id = Positions.query.get_or_404(id)
    candidate_data = Candidates.query.all()
    poll = delete_id.poll_id
    poll = Polls.query.filter_by(id=poll).first()
    poll = poll.poll



    for data in candidate_data:
        if data.position_id == id:
            picture_file = os.path.join(app.config["UPLOAD_FOLDER"], data.filename)
            os.remove(picture_file)
            db.session.delete(data)
        elif data.position_id is None:
            db.session.delete(data)

    flash("DATA DELETED!")

    log = Logs(f"""{session["admin_username"]} deleted position {delete_id.position}""", datetime.datetime.now())
    db.session.add(log)

    db.session.delete(delete_id)
    db.session.commit()

    return redirect("/position/" + poll)





@app.route("/update_position/<int:id>", methods=["GET", "POST"])
@admin_required
def update_position(id):

    update_id = Positions.query.get_or_404(id)
    poll = update_id.poll_id
    poll = Polls.query.filter_by(id=poll).first()
    poll = poll.poll

    if request.method == "POST":
        log = Logs(f"""{session["admin_username"]} updated position {update_id.position} to {request.form["position"]}""", datetime.datetime.now())
        db.session.add(log)

        update_id.position = request.form["position"]
        flash("UPDATED SUCCESSFULLY!")

    

        db.session.commit()
        return redirect("/position/" + poll)
        
    else:
        return render_template("update_position.html", update_id=update_id, poll=poll)





@app.route("/candidate_view/<position>", methods=["GET", "POST"])
@admin_required
def candidate_view(position):
    
    pos_id = Positions.query.filter_by(position=position).first()
    poll = pos_id.poll_id
    poll = Polls.query.filter_by(id=poll).first()
    poll = poll.poll

    # session["position_id"] = id
    # session["position"] = position
    # session.pop("position_id", None)

    pos = Positions.query.filter_by(position=position).first()
    pos_id = pos.id
    position = pos.position

    candidate = Candidates.query.filter_by(position_id=pos_id).all()

    try:
        filename = candidate.filename
        display_image = url_for("static", filename="uploads/" + filename)

        return render_template("candidate_view.html", candidate=candidate, position=position, display_image=display_image, poll=poll)

    except:
        return render_template("candidate_view.html", candidate=candidate, position=position, poll=poll)

    



UPLOAD_FOLDER = "static/uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(*args):

    if "image" not in request.files:
        flash("Please upload an image")
        return render_template("add_candidate.html", position=args)

    pic = request.files["image"]

    if pic.filename == "":
        flash("No image uploaded")
        return render_template("add_candidate.html", position=args)

    if pic and allowed_file(pic.filename):
        check = check_filename(pic.filename)
        filename = secure_filename(check)
        pic.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        return filename

    else:
        flash("Allow image types: png/jpg/jpeg")
        return redirect(url_for("add_candidate", position=args))

def check_filename(filename):

    path = UPLOAD_FOLDER + filename

    if os.path.exists(path):

        file_type = os.path.splitext(path)[1]
        name = random.randint(0000000000, 9999999999)
        new = str(name) + file_type
        return new

    else:
        return filename





@app.route("/add_candidate/<position>", methods=["GET", "POST"])
@admin_required
def add_candidate(position):

    if request.method == "POST":

        if not request.form["name"] or not request.form["college"] or not request.files["image"]:
            flash("FILL ALL FIELDS")
            return render_template("add_candidate.html", position=position)

        else:
            filename = upload_image(position)

            pos = Positions.query.filter_by(position=position).first()
            pos_id = pos.id
            pol_id = pos.poll_id
            position = pos.position

            candidate = Candidates(request.form["name"], request.form["college"], pos_id, pol_id, filename)

            log = Logs(f"""{session["admin_username"]} added candidate {request.form["name"]}""", datetime.datetime.now())
            db.session.add(log)

            db.session.add(candidate)
            db.session.commit()

            return redirect(url_for("candidate_view", position=position))
    
    return render_template("add_candidate.html", position=position)





@app.route("/delete_candidate/<int:id>/<position>", methods=["GET", "POST"])
@admin_required
def delete_candidate(id, position):

    delete_id = Candidates.query.get_or_404(id)
    
    candidate_data = Candidates.query.all()

    for data in candidate_data:
        if data.id == id:
            picture_file = os.path.join(app.config["UPLOAD_FOLDER"], data.filename)
            os.remove(picture_file)
            db.session.delete(data)

    flash("DATA DELETED!")

    log = Logs(f"""{session["admin_username"]} deleted candidate {delete_id.name}""", datetime.datetime.now())
    db.session.add(log)

    db.session.delete(delete_id)
    db.session.commit()

    return redirect(url_for("candidate_view", position=position))





@app.route("/update_candidate/<int:id>", methods=["GET", "POST"])
@admin_required
def update_candidate(id):

    update_id = Candidates.query.get_or_404(id)
    position = Candidates.query.filter_by(id=id).first()
    position = position.position_id
    position = Positions.query.filter_by(id=position).first()
    position = position.position

    picture_file = Candidates.query.filter_by(id=id).all()

    if request.method == "POST":

        for picture in picture_file:
            if picture.id == id:
                picture_file = os.path.join(app.config["UPLOAD_FOLDER"], picture.filename)
                os.remove(picture_file)


        position = Candidates.query.filter_by(id=id).first()
        position = position.position_id
        
        position = Positions.query.filter_by(id=position).first()
        position = position.position
        
        filename = upload_image(id)

        log = Logs(f"""{session["admin_username"]} updated candidate {update_id.name} to {request.form["name"]}""", datetime.datetime.now())
        db.session.add(log)

        update_id.name = request.form["name"]
        update_id.college = request.form["college"]
        update_id.filename = filename
        
        flash("UPDATED SUCCESSFULLY!")

        

        db.session.commit()


        return redirect(url_for("candidate_view", position=position))

    return render_template("update_candidate.html", update_id=update_id, position=position)





@app.route("/get_chain", methods=["GET", "POST"])
def get_chain():


    if request.method == "POST":
        voter = request.form["voter"]
        filtered_chain = []

        for block in blockchain.chain:
            if voter.lower().strip() == block["2_voter"].lower():
                filtered_chain.append(block)

        if len(filtered_chain) < 1:
            flash("Voter not found")
            return render_template("get_chain.html", blockchain=blockchain.chain)
            
        else:
            flash("Voter found!")
            return render_template("get_chain.html", blockchain=filtered_chain)
    else:
        return render_template("get_chain.html", blockchain=blockchain.chain)


@app.route("/logs", methods=["GET", "POST"])
@admin_required
def logs():

    logs = Logs.query.all()

    return render_template("logs.html", logs=logs)


@app.route("/pyscript", methods=["GET", "POST"])
def pyscript():

    return render_template("pyscript.html")

if __name__ == "__main__":
    app.debug = True
    app.run()