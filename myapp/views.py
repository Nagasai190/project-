from flask import Blueprint, render_template, request, url_for, redirect, session, flash, jsonify
from myapp.database import *
from functools import wraps

import pandas as pd
import matplotlib.pyplot as plt
from myapp import socket

views = Blueprint('views', __name__, static_folder='static', template_folder='templates')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("views.login"))
        return f(*args, **kwargs)

    return decorated


@views.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for("views.login"))


# Register a new user and hash password
@views.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("User already exists with that username.")
            return redirect(url_for("views.login"))

        new_user = User(username=username, email=email, password=password)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        new_chat = Chat(user_id=new_user.id, chat_list=[])
        db.session.add(new_chat)
        db.session.commit()

        flash("Registration successful.")
        return redirect(url_for("views.login"))

    return render_template("auth.html")


@views.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user"] = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
            return redirect(url_for("views.chat"))
        else:
            flash("Invalid login credentials. Please try again.")
            return redirect(url_for("views.login"))

    return render_template("auth.html")


@views.route("/new-chat", methods=["POST"])
@login_required
def new_chat():
    user_id = session["user"]["id"]
    new_chat_email = request.form["email"].strip().lower()

    if new_chat_email == session["user"]["email"]:
        return redirect(url_for("views.chat"))

    recipient_user = User.query.filter_by(email=new_chat_email).first()
    if not recipient_user:
        return redirect(url_for("views.chat"))

    existing_chat = Chat.query.filter_by(user_id=user_id).first()
    """if not existing_chat:
        existing_chat = Chat(user_id=user_id, chat_list=[])
        db.session.add(existing_chat)
        db.session.commit()"""

    # Check if the new chat is already in the chat list
    if recipient_user.id not in [user_chat["user_id"] for user_chat in existing_chat.chat_list]:
        room_id = str(int(recipient_user.id) + int(user_id))[-4:]

        # Add the new chat to the chat list of the current user
        updated_chat_list = existing_chat.chat_list + [{"user_id": recipient_user.id, "room_id": room_id}]
        existing_chat.chat_list = updated_chat_list

        # Save the changes to the database
        existing_chat.save_to_db()

        # Create a new chat list for the recipient user if it doesn't exist
        recipient_chat = Chat.query.filter_by(user_id=recipient_user.id).first()
        if not recipient_chat:
            recipient_chat = Chat(user_id=recipient_user.id, chat_list=[])
            db.session.add(recipient_chat)
            db.session.commit()

        # Add the new chat to the chat list of the recipient user
        updated_chat_list = recipient_chat.chat_list + [{"user_id": user_id, "room_id": room_id}]
        recipient_chat.chat_list = updated_chat_list
        recipient_chat.save_to_db()

        # Create a new message entry for the chat room
        new_message = Message(room_id=room_id)
        db.session.add(new_message)
        db.session.commit()

    return redirect(url_for("views.chat"))

from cryptography.fernet import Fernet

def load_key():
    return b'j_Z-NTrAUh1pixmkAPI__CWWngT9SjNl3PrvtTkfyec='

cipher = Fernet(load_key())

@views.route("/chat/", methods=["GET", "POST"])
@login_required
def chat():
    room_id = request.args.get("rid", None)

    current_user_id = session["user"]["id"]
    current_user_chats = Chat.query.filter_by(user_id=current_user_id).first()
    chat_list = current_user_chats.chat_list if current_user_chats else []

    data = []

    for chat in chat_list:
        # Query the database to get the username of users in a user's chat list
        username = User.query.get(chat["user_id"]).username
        is_active = room_id == chat["room_id"]

        try:
            message = Message.query.filter_by(room_id=chat["room_id"]).first()

            last_message = message.messages[-1]
            print(last_message)
            last_message_content = cipher.decrypt(last_message.content.encode()).decode()
        except (AttributeError, IndexError):
            last_message_content = "This place is empty. No messages ..."

        data.append({
            "username": username,
            "room_id": chat["room_id"],
            "is_active": is_active,
            "last_message": last_message_content,
        })

    #messages = Message.query.filter_by(room_id=room_id).first().messages if room_id else []
    messages = []
    if room_id:
        chat = Message.query.filter_by(room_id=room_id).first()
        if chat:
            for msg in chat.messages:
                decrypted = cipher.decrypt(msg.content.encode()).decode()
                msg.content = decrypted  # Replace encrypted content with decrypted
            messages = chat.messages

    print(messages)
    return render_template(
        "chat.html",
        user_data=session["user"],
        room_id=room_id,
        data=data,
        messages=messages,
    )


@views.app_template_filter("ftime")
def ftime(date):
    dt = datetime.fromtimestamp(int(date))
    time_format = "%I:%M %p"
    formatted_time = dt.strftime(time_format)

    formatted_time += " | " + dt.strftime("%m/%d")
    return formatted_time


@views.route('/visualize')
def visualize():
    pass


@views.route('/get_name')
def get_name():
    data = {'name': ''}
    if 'username' in session:
        data = {'name': session['username']}

    return jsonify(data)


@views.route('/get_messages')
def get_messages():
    pass


@views.route('/leave')
def leave():
    socket.emit('disconnect')
    return redirect(url_for('views.home'))
