import base64
import binascii
import os
import socket
import uuid
from collections import namedtuple
from http import HTTPStatus
from io import BytesIO
from urllib.parse import urlunparse, urlencode

from flask import Flask, jsonify, Response, make_response, request
from flask_sqlalchemy import SQLAlchemy
from pydub import AudioSegment
from sqlalchemy import Column, String, Integer, ForeignKey, LargeBinary

API_HOSTNAME = os.environ.get("API_HOSTNAME", socket.gethostname())
API_PORT = int(os.environ.get("API_PORT", 8080))

app: Flask = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("POSTGTRES_SQL_URI", "sqlite:///test.db")
db: SQLAlchemy = SQLAlchemy(app)


class User(db.Model):
    __tablename__: str = 'user'
    id = Column(Integer, autoincrement=True, index=True, primary_key=True)
    user_token = Column(String(36), nullable=False, index=True)
    user_name = Column(String(20), nullable=False, default="")


class Record(db.Model):
    __tablename__: str = 'record'
    id = Column(Integer, autoincrement=True, index=True, primary_key=True)
    mp3_token = Column(String(36), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    mp3_data = Column(LargeBinary)

    def resp_mp3(self):
        buf = BytesIO(self.mp3_data)
        response: Response = make_response(buf.getvalue())
        buf.close()
        response.headers['Content-Type'] = 'audio/mp3'
        response.headers['Content-Disposition'] = 'attachment; filename=sound.mp3'
        return response


with app.app_context():
    db.create_all()


def wav2mp3(wav: bytes) -> bytes:
    out_f = BytesIO()
    sound = AudioSegment.from_file(BytesIO(wav), format="wav")
    sound.export(out_f=out_f)
    return out_f.read()


def generate_url(record_id, user_id):
    Components = namedtuple(
        typename='Components',
        field_names=['scheme', 'netloc', 'url', 'path', 'query', 'fragment']
    )
    query_params = {
        'id'  : record_id,
        'user': user_id
    }
    url = urlunparse(
        Components(
            scheme='http',
            netloc=API_HOSTNAME + ':' + str(API_PORT),
            query=urlencode(query_params),
            path='record',
            url='/',
            fragment='',
        )
    )
    return url.replace(";", "", 1)


@app.route('/add_user', methods=['POST'])
def add_user():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return jsonify({}), HTTPStatus.BAD_REQUEST
    json = request.get_json()
    user_name = json.get('name', None)
    if user_name is None:
        return jsonify({}), HTTPStatus.BAD_REQUEST
    user_token = str(uuid.uuid4())
    new_user = User(user_name=user_name, user_token=user_token)
    db.session.add(new_user)
    db.session.flush()
    user_id = new_user.id
    db.session.commit()
    return jsonify({"id": user_id, "token": user_token}), HTTPStatus.OK


@app.route('/add_wav', methods=['POST'])
def add_record():
    content_type = request.headers.get('Content-Type')
    if content_type != 'application/json':
        return jsonify({}), HTTPStatus.BAD_REQUEST
    json = request.get_json()
    user_id = json.get('user_id')
    user_token = json.get('user_token')
    if user := db.session.query(User).filter(User.id == user_id).first():
        if user.user_token != user_token:
            return jsonify({}), HTTPStatus.FORBIDDEN
    else:
        return jsonify({}), HTTPStatus.FORBIDDEN
    coded_wav = json.get('wav')
    try:
        wav = base64.b64decode(coded_wav)
    except binascii.Error:
        return jsonify({}), HTTPStatus.BAD_REQUEST
    mp3_data = wav2mp3(wav)
    token_record = str(uuid.uuid4())
    new_record = Record(mp3_token=token_record, user_id=user_id, mp3_data=mp3_data)
    db.session.add(new_record)
    db.session.commit()
    return generate_url(token_record, user_id)


@app.route('/record', methods=['GET'])
def get_record():
    user_id = request.args.get('user', None)
    mp3_id = request.args.get('id', None)
    if user_id is None or mp3_id is None:
        return "", HTTPStatus.BAD_REQUEST
    try:
        user_id = int(user_id)
    except ValueError:
        return "", HTTPStatus.BAD_REQUEST
    record = db.session.query(Record).filter(Record.mp3_token == mp3_id and Record.user_id == user_id).first()
    if record:
        return record.resp_mp3(), HTTPStatus.OK
    return "", HTTPStatus.NOT_FOUND


if __name__ == '__main__':
    app.run(debug=True, port=API_PORT)
