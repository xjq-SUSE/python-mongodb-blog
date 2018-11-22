#!/usr/bin/env python
from flask import Flask, redirect
from flask.globals import request
from flask.templating import render_template
from pymongo.errors import AutoReconnect
import datetime
import json
import os
import pymongo
import time

static_path = os.path.abspath(os.path.join(__file__, '..', '..', 'public', 'static'))
app = Flask(__name__, static_folder=static_path)

@app.route("/")
def index():
    db = connect_db()
    posts = db.posts.find().sort('date', pymongo.DESCENDING)
    return render_template('index.html', posts=posts)

@app.route("/post/new", methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        title = request.form.get('post[title]', None)
        body = request.form.get('post[body]', None)
        if not title or not body:
            return render_template('post.html', error='Must provide title and body')
        # create a post in mongodb
        db = connect_db()
        post = {'title': title, 'body': body, 'date': datetime.datetime.now()}
        success, attempts = False, 1
        while success is False and attempts < 10:
            try:
                db.posts.insert(post)
                success = True
            except AutoReconnect:
                attempts += 1
                time.sleep(3)
        return redirect('/')
    else:
        return render_template('post.html')


def connect_db():
    if 'VCAP_SERVICES' in os.environ:
        vcap_json = json.loads(os.getenv('VCAP_SERVICES'))
        mongo_host = vcap_json['mongodb'][0]['credentials']['host']
        mongo_username = vcap_json['mongodb'][0]['credentials']['username']
        mongo_password = vcap_json['mongodb'][0]['credentials']['password']
        mongo_port = vcap_json['mongodb'][0]['credentials']['port']
        mongo_uri = vcap_json['mongodb'][0]['credentials']['uri']
        conn = pymongo.MongoClient(mongo_host,
                                  username=mongo_username,
                                  password=mongo_password,
                                  authSource='admin',
                                  authMechanism='SCRAM-SHA-1')
    else:
        mongo_uri = 'mongodb://localhost:27017'
        conn = pymongo.MongoClient(mongo_uri)
    return conn['blog']

if __name__ == "__main__":
    # NOTE: debug True breaks PyDev debugger
    app.debug = os.environ.get('DEBUG', True)
    host = os.environ.get('BIND', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
