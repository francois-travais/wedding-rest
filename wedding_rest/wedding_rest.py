# -*- coding: utf8 -*-
import datetime

from flask import Flask, jsonify, request, abort
from pymongo import MongoClient
from flask_cors import CORS, cross_origin
import ConfigParser
import os

configParser = ConfigParser.SafeConfigParser()
configParser.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'))


def getDatabase(configParser):
    return configParser.get('db', 'database')


def getMongoURI(configParser):
    host = configParser.get('db', 'host')
    port = configParser.getint('db', 'port')
    user = configParser.get('db', 'user')
    password = configParser.get('db', 'password')
    credentials = ''
    if user is not None and user != '':
        credentials = '@'
        if password is not None and password != '':
            credentials = ':%s@' % password
        credentials = '%s%s' % (user, credentials)
    database = getDatabase(configParser)
    return 'mongodb://%s%s:%i/%s' % (credentials, host, port, database)


def getMongoClient(configParser):
    URI = getMongoURI(configParser)
    client = MongoClient(URI)
    return client[getDatabase(configParser)]

app = Flask(__name__)
cors = CORS()
app.config['CORS_HEADERS'] = 'Content-Type'

db = getMongoClient(configParser)


def unmongoised(el):
    return {k: v for k, v in el.items() if k != '_id'}


def retrieve_if_exists(req, field, result):
    if field in req.json:
        result[field] = req.json[field]
    return result


@app.route('/v1/accommodations', methods=['GET'])
@cross_origin()
def get_accommodations():
    app.logger.debug("Accommodations: access")
    accommodations = []
    for a in db.accommodations.find():
        accommodations.append(unmongoised(a))
    return jsonify({'accommodations': accommodations})


@app.route('/v1/contact', methods=['POST'])
@cross_origin()
def post_contact():
    if not request.json or 'name' not in request.json or 'message' not in request.json:
        app.logger.warning("Contact: Missing name or message in contact form")
        abort(400)
    app.logger.debug("Contact: access")
    contact = {
        'name': request.json['name'],
        'message': request.json['message'],
        'date': datetime.datetime.utcnow()
    }
    contact = retrieve_if_exists(request, 'email', contact);
    contacts = db.contacts
    contact_id = contacts.insert(contact)
    result = contacts.find_one({"_id": contact_id})
    return jsonify({'contact': unmongoised(result)}), 201


@app.route('/v1/reply', methods=['POST'])
@cross_origin()
def post_reply():
    if not request.json or 'name' not in request.json or 'adultNb' not in request.json:
        app.logger.warning("Reply: Missing name or adult number")
        abort(400)
    if not isinstance(request.json['adultNb'], (int, long)):
        app.logger.warning("Reply: Adult nb is not a number")
        abort(400)
    app.logger.debug("Reply: access")
    reply = {
        'name': request.json['name'],
        'adultNb': request.json['adultNb'],
        'date': datetime.datetime.utcnow()
    }
    reply = retrieve_if_exists(request, 'email', reply)
    reply = retrieve_if_exists(request, 'comment', reply)
    reply = retrieve_if_exists(request, 'childNb', reply)
    if not isinstance(reply['childNb'], (int, long)):
        app.logger.warning("Reply: Child nb is not a number")
        abort(400)
    replies = db.replies
    reply_id = replies.insert(reply)
    result = replies.find_one({"_id": reply_id})
    return jsonify({'reply': unmongoised(result)}), 201


if __name__ == '__main__':
    app.run(debug=True)
