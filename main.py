from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy 
from hashlib import sha256
from hmac import compare_digest
from math import isfinite
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

app = Flask(__name__)

#Create a database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mytravel.db'

db = SQLAlchemy(app)

class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(100), unique=True, nullable=False)
    country = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'destination': self.destination,
            'country': self.country,
            'rating': self.rating
        }

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }
    
with app.app_context():
    db.create_all()


def validated_data(fields, partial=False):
    try:
        data = request.get_json()
    except (BadRequest, UnsupportedMediaType):
        raise ValueError('Send a valid JSON object with Content-Type application/json')
    if not isinstance(data, dict) or not data:
        raise ValueError('Request body must be a non-empty JSON object')
    unknown = set(data) - set(fields)
    if unknown:
        raise ValueError('Unknown fields: ' + ', '.join(sorted(unknown)))
    if not partial:
        missing = set(fields) - set(data)
        if missing:
            raise ValueError('Required fields: ' + ', '.join(sorted(missing)))
    cleaned = {}
    for field, value in data.items():
        if field == 'rating':
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError('rating must be a finite number')
            try:
                finite = isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError('rating must be a finite number')
        else:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(field + ' must be a non-empty string')
            if field != 'password':
                value = value.strip()
            limit = fields[field]
            if limit is not None and len(value) > limit:
                raise ValueError(f'{field} must be at most {limit} characters')
        cleaned[field] = value
    return cleaned


@app.errorhandler(ValueError)
def validation_error(error):
    return jsonify({'error': str(error)}), 400


def find_record(model, record_id):
    if record_id <= 0:
        raise ValueError('ID must be a positive integer')
    return db.session.get(model, record_id)


def duplicate_exists(model, field, value, exclude_id=None):
    query = model.query.filter(getattr(model, field) == value)
    if exclude_id is not None:
        query = query.filter(model.id != exclude_id)
    return query.first() is not None


def save_changes():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'A unique value already exists or a database constraint was violated'}), 409
    return None


DESTINATION_FIELDS = {'destination': 100, 'country': 200, 'rating': None}
USER_FIELDS = {'name': 100, 'email': 200, 'password': None}
LOGIN_FIELDS = {'email': 200, 'password': None}


#Create Routes
#Main-Home page route
@app.route('/')
def home():
    return jsonify({"message": "Welcome to VibeTag!"})

#GET Destination(s)
@app.route('/destinations', methods=['GET'])
def get_destinations():
    
    destinations = Destination.query.all()
    return jsonify([dest.to_dict() for dest in destinations])

@app.route('/destinations/<int:destination_id>', methods=['GET'])
def get_destination(destination_id):    
    destination = find_record(Destination, destination_id)
    if destination:
        return jsonify(destination.to_dict())
    else: return jsonify({"error": "Destination not found"}), 404

#POST: Create a new destination
@app.route('/destinations', methods=['POST'])
def add_destination():
    data = validated_data(DESTINATION_FIELDS)
    if duplicate_exists(Destination, 'destination', data['destination']):
        return jsonify({'error': 'Destination already exists'}), 409
    new_destination = Destination(
                        destination=data['destination'],
                        country=data['country'],
                        rating=data['rating']
    )
    db.session.add(new_destination)
    error = save_changes()
    if error:
        return error
    return jsonify(new_destination.to_dict()), 201

#PUT: Update an existing destination
@app.route('/destinations/<int:destination_id>', methods=['PUT', 'PATCH'])
def update_destination(destination_id):
    dest = find_record(Destination, destination_id)
    if not dest:
        return jsonify({"error": "Destination not found"}), 404

    userinputdata = validated_data(DESTINATION_FIELDS, partial=True)
    if 'destination' in userinputdata and duplicate_exists(
        Destination, 'destination', userinputdata['destination'], destination_id
    ):
        return jsonify({'error': 'Destination already exists'}), 409
    dest.destination = userinputdata.get('destination', dest.destination)
    dest.country = userinputdata.get('country', dest.country)
    dest.rating = userinputdata.get('rating', dest.rating)

    error = save_changes()
    if error:
        return error
    return jsonify(dest.to_dict())

#DELETE: Delete a destination
@app.route('/destinations/<int:destination_id>', methods=['DELETE'])
def delete_destination(destination_id):
    dest = find_record(Destination, destination_id)
    if not dest:
        return jsonify({"error": "Destination not found"}), 404

    db.session.delete(dest)
    error = save_changes()
    if error:
        return error
    return jsonify({"message": "Destination deleted successfully"})

#GET: Get all users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


#GET: Get a single user
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = find_record(User, user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict())


#POST: Create a new user
@app.route('/users', methods=['POST'])
def register():
    data = validated_data(USER_FIELDS)
    if duplicate_exists(User, 'email', data['email']):
        return jsonify({'error': 'Email already exists'}), 409
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=sha256(data['password'].encode()).hexdigest()
    )
    db.session.add(new_user)
    error = save_changes()
    if error:
        return error
    return jsonify(new_user.to_dict()), 201


@app.route('/login', methods=['POST'])
def login():
    data = validated_data(LOGIN_FIELDS)
    user = User.query.filter_by(email=data['email']).first()
    password_hash = sha256(data['password'].encode()).hexdigest()
    stored_hash = user.password if user is not None else '0' * 64
    password_matches = compare_digest(password_hash, stored_hash)
    if user is None or not password_matches:
        return jsonify({'error': 'Invalid email or password'}), 401
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200


@app.route('/users/<int:user_id>', methods=['PUT', 'PATCH'])
def update_user(user_id):
    user = find_record(User, user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    data = validated_data(USER_FIELDS, partial=True)
    if 'email' in data and duplicate_exists(User, 'email', data['email'], user_id):
        return jsonify({'error': 'Email already exists'}), 409
    for field, value in data.items():
        if field == 'password':
            value = sha256(value.encode()).hexdigest()
        setattr(user, field, value)
    error = save_changes()
    if error:
        return error
    return jsonify(user.to_dict())


@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = find_record(User, user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    db.session.delete(user)
    error = save_changes()
    if error:
        return error
    return jsonify({'message': 'User deleted successfully'})


if __name__ == "__main__":
    app.run(debug=True)
