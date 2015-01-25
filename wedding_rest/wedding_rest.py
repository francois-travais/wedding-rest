# -*- coding: utf8 -*-
import datetime
import ConfigParser

from flask import Flask, jsonify, request, abort
from pymongo import MongoClient
from flask_cors import CORS, cross_origin
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


def validate_password(password):
    result = db.passwords.find_one({"password": password})
    if result is not None:
        app.logger.info('Password of user %s found' % result['user'])
        return True
    app.logger.warn('Password %s not found' % password)
    return False


@app.route('/v1/accommodations', methods=['GET'])
@cross_origin()
def get_accommodations():
    app.logger.debug("Accommodations: access")
    accommodations = []
    for a in db.accommodations.find():
        accommodations.append(unmongoised(a))
    return jsonify({'accommodations': accommodations})


@app.route('/v1/gifts', methods=['GET'])
@cross_origin()
def get_gifts():
    app.logger.debug("Gifts: access")
    gifts = []
    for g in db.gifts.find():
        tmp = unmongoised(g)
        gift = tmp.copy()
        gift['booked'] = 0
        for booking in tmp['booked']:
            gift['booked'] += booking['value']
        gifts.append(gift)
    return jsonify({'gifts': gifts})


@app.route('/v1/gift/<string:gift_id>', methods=['GET'])
@cross_origin()
def get_gift(gift_id):
    app.logger.debug("Gift: access")
    gifts = []
    gift = db.gifts.find_one({"id": gift_id})
    tmp = unmongoised(gift)
    gift = tmp.copy()
    gift['booked'] = 0
    for booking in tmp['booked']:
        gift['booked'] += booking['value']
    return jsonify({'gift': gift})


@app.route('/v1/booking', methods=['POST'])
@cross_origin()
def book_gift():
    if not request.json or 'password' not in request.json or not validate_password(request.json['password']):
        app.logger.warning('Attempt to post booking form with wrong password')
        return forbidden('wrong password')
    if 'name' not in request.json:
        app.logger.warning("Booking: Missing name in booking form")
        abort(400)
    if 'gift' not in request.json or 'booked' not in request.json:
        app.logger.warning("Booking: Missing gift ID or booked in booking form")
        abort(400)
    app.logger.debug("Booking: access")
    booking = {
        'name': request.json['name'],
        'value': request.json['booked'],
        'date': datetime.datetime.utcnow()
    }
    booking = retrieve_if_exists(request, 'message', booking)
    # app.logger.debug(request.json)
    gifts = db.gifts
    app.logger.debug(gifts.find_one())
    gift = gifts.find_one({"id": request.json['gift']})
    if gift is None:
        app.logger.warning("Booking: unknown gift ID " + request.json['gift'])
        abort(400)
    gift['booked'].append(booking)
    gift_id = gifts.update({"_id": gift['_id']}, {"$set": {"booked": gift['booked']}}, upsert=False, multi=False)
    if gift_id is None:
        app.logger.warning("Booking: something wrong with the update of " + request.json['gift'])
        abort(400)
    return jsonify({'booking': booking}), 201


@app.route('/v1/contact', methods=['POST'])
@cross_origin()
def post_contact():
    if not request.json or 'password' not in request.json or not validate_password(request.json['password']):
        app.logger.warning('Attempt to post contact form with wrong password')
        return forbidden('wrong password')
    if 'name' not in request.json or 'message' not in request.json:
        app.logger.warning("Contact: Missing name or message in contact form")
        abort(400)
    app.logger.debug("Contact: access")
    contact = {
        'name': request.json['name'],
        'message': request.json['message'],
        'date': datetime.datetime.utcnow()
    }
    contact = retrieve_if_exists(request, 'email', contact)
    contacts = db.contacts
    contact_id = contacts.insert(contact)
    result = contacts.find_one({"_id": contact_id})
    return jsonify({'contact': unmongoised(result)}), 201


@app.route('/v1/reply', methods=['POST'])
@cross_origin()
def post_reply():
    if not request.json or 'password' not in request.json or not validate_password(request.json['password']):
        app.logger.warning('Attempt to post reply form with wrong password')
        return forbidden('wrong password')
    if 'name' not in request.json or 'adultNb' not in request.json:
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


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'result': 'error',
                    'data': 'bad request',
                    'message': str(error)}), 400


@app.errorhandler(403)
def forbidden(error):
    return jsonify({'result': 'error',
                    'data': 'forbidden',
                    'message': str(error)}), 403


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'result': 'error',
                    'data': 'unauthorized',
                    'message': str(error)}), 401


@app.errorhandler(404)
def not_found(error):
    return jsonify({'result': 'error',
                    'data': 'url not found',
                    'message': str(error)}), 404


@app.errorhandler(500)
def runtime_error(error):
    return jsonify({'result': 'error',
                    'data': 'internal server error',
                    'message': str(error)}), 500


if __name__ == '__main__':
    app.run(debug=True)
