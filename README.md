# VibeTag

VibeTag is a travel discovery project built around finding places and people that match your vibe. The current application is a Flask API for managing travel destinations and users, with login credential verification and SQLite storage.

## Long-term vision

VibeTag aims to help users discover places that reflect their interests, travel style, and the experiences they enjoy. Over time, users will be able to:

- Review, tag, and comment on places that match their vibe, sharing experiences and helping others discover destinations.
- Share travel plans and interests so others can learn where they want to go and what they enjoy doing.
- Create wishlists of places they would like to visit.
- Find like-minded people whose vibe, interests, and travel plans align with their own.
- Connect with compatible travel companions and tag along to visit places together.

These capabilities are planned for the future. The current API provides the foundation through destination and user management.

## Technology stack

| Technology | Role |
| --- | --- |
| Python | Application language |
| Flask | Web framework for API routes and JSON responses |
| Flask-SQLAlchemy | Integration between Flask and the database models |
| SQLAlchemy | Object-relational mapping and database access |
| SQLite | Local storage for destinations and users |
| Werkzeug | HTTP utilities used by Flask, including request exceptions |
| Python `hashlib` and `hmac` | Password hashing and credential comparison in the current implementation |
| pip and `requirements.txt` | Dependency installation and version specifications |

Flask-Migrate is also listed as a dependency for database migration support; migration commands are not currently configured in the application.

## Current capabilities

- Create, list, retrieve, update, and delete destinations with a name, country, and numeric rating.
- Create, list, retrieve, update, and delete users.
- Verify login credentials using an email address and password. The login endpoint returns a user record; it does not issue a session or authentication token.
- Validate JSON request bodies and report invalid input, missing records, and duplicate destination names or user email addresses.
- Store records in a local SQLite database, with database tables created automatically when the application starts.

## Run locally

From the project directory, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

The development API runs at `http://127.0.0.1:5000`. SQLite data is stored in `instance/mytravel.db`. The application starts with Flask debug mode enabled for local development.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Welcome message |
| GET, POST | `/destinations` | List destinations or create a destination |
| GET | `/destinations/<id>` | Retrieve a destination |
| PUT, PATCH | `/destinations/<id>` | Update supplied destination fields |
| DELETE | `/destinations/<id>` | Delete a destination |
| GET, POST | `/users` | List users or register a user |
| GET | `/users/<id>` | Retrieve a user |
| PUT, PATCH | `/users/<id>` | Update supplied user fields |
| DELETE | `/users/<id>` | Delete a user |
| POST | `/login` | Verify login credentials |

Send request bodies as JSON with the `Content-Type: application/json` header. Destination creation requires `destination`, `country`, and `rating`; user registration requires `name`, `email`, and `password`; login requires `email` and `password`. Both PUT and PATCH currently accept partial updates. User responses omit passwords.
