import datetime
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from peewee import *
from pymongo import MongoClient

MONGO_CONNECTION_STRING = "mongodb://localhost:27017"

mongo = MongoClient(MONGO_CONNECTION_STRING)

db = PostgresqlDatabase(
    'flask-vue-crud-db',
    user='postgres',
    password='sample_pass',
    host="0.0.0.0",
    port=5432
)


class BaseModel(Model):
    class Meta:
        database = db


class Book(BaseModel):
    id = UUIDField(unique=True)
    title = TextField()
    author = TextField()
    read = BooleanField()

    def dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "author": self.author,
            "read": self.read
        }


db.create_tables([Book, ], safe=True)

app = Flask("app")

# enable CORS
CORS(app, resources={r'/*': {'origins': '*', "Access-Control-Allow-Headers": "*"}})


@cross_origin()
@app.route('/books', methods=['GET', 'POST'])
def all_books():
    response_object = {'status': 'success'}

    if request.method == 'POST':
        post_data = request.get_json()

        Book.insert(
            id=uuid.uuid4().hex,
            title=post_data.get('title'),
            author=post_data.get('author'),
            read=post_data.get('read'),
        ).execute()

        response_object['message'] = 'Book added!'

        log("post", post_data)

    else:
        response_object['books'] = [b.dict() for b in Book.select()]

    response = jsonify(response_object)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@cross_origin()
@app.route('/books/<book_id>', methods=['PUT', 'DELETE'])
def single_book(book_id):
    response_object = {'status': 'success'}
    if request.method == 'PUT':
        post_data = request.get_json()

        b = Book.get(id=book_id)

        b.id = uuid.uuid4().hex
        b.title = post_data.get('title')
        b.author = post_data.get('author')
        b.read = post_data.get('read')

        Book() \
            .update(
            title=post_data.get('title'),
            author=post_data.get('author'),
            read=post_data.get('read'),
        ) \
            .where(Book.id == book_id) \
            .execute()

        response_object['message'] = 'Book updated!'

        log("put", {"data": post_data, "book_id": book_id})

    if request.method == 'DELETE':
        Book.delete().where(Book.id == book_id).execute()
        response_object['message'] = 'Book removed!'

        log("delete", {"book_id": book_id})

    response = jsonify(response_object)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route('/logs', methods=['GET'])
def get_logs():
    logs_db = mongo.get_database('logs')
    if logs_db is None:
        print("cant log")
        return

    coll = logs_db.get_collection('operations')

    objects = list(coll.find({}))
    if len(objects) == 0:
        return

    arr = []
    for obj in objects:
        if obj is None:
            continue

        arr.append(
            {
                "opname": str(obj["opname"]),
                "data": obj["data"],
                "ts": str(obj["ts"]),
            }
        )

    return jsonify(arr)


def log(opname, data):
    logs_db = mongo.get_database('logs')
    if logs_db is None:
        print("cant log")
        return

    coll = logs_db.get_collection('operations')
    coll.insert_one({
        "opname": opname,
        "data": data,
        "ts": datetime.datetime.now().strftime("%d-%m-%Y, %H:%M:%S")
    })


if __name__ == '__main__':
    app.run(port=5000)
