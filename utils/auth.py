from flask import session, redirect
from functools import wraps

def is_logged_in():
    return 'user_id' in session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function