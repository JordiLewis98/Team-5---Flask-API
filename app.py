from flask import Flask, request, jsonify, make_response
import json
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime, timedelta
import jwt
from functools import wraps
import re
import uuid

app = Flask(__name__)
#--------------------------------------------------------------------------------
# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///observations.db' # path to db
app.config['SQLALCHEMY_ECHO'] = True # echoes SQL for debug
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Team5APISecretKey'
#--------------------------------------------------------------------------------
db = SQLAlchemy(app)
ma = Marshmallow(app)
#--------------------------------------------------------------------------------
class Observation(db.Model):
    """Definition of the Observation Model used by SQLAlchemy"""
    observation_id = db.Column(db.String(80), primary_key=True, default=lambda: str(uuid.uuid4()))
    observation_date = db.Column(db.Date, nullable=False)
    observation_time = db.Column(db.Time, nullable=False)
    observation_timeZone = db.Column(db.String(80), nullable=False)
    observation_coordinates = db.Column(db.String(80), nullable=False)
    observation_waterTemp = db.Column(db.REAL, nullable=False)
    observation_airTemp = db.Column(db.REAL, nullable=False)
    observation_humidity = db.Column(db.Integer, nullable=False)
    observation_windSpeed = db.Column(db.REAL, nullable=False)
    observation_windDirection = db.Column(db.String(80), nullable=False)
    observation_precipitation = db.Column(db.Integer, nullable=False)
    observation_haze = db.Column(db.REAL, nullable=False)
    observation_becquerel = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return '<Observation %r>' % self.observation_id
#--------------------------------------------------------------------------------
class ObservationSchema(ma.SQLAlchemyAutoSchema):
        """Definition used by serialization library based on Observation Model"""
        class Meta:
            fields = ("observation_id","observation_date","observation_time", "observation_timeZone", "observation_coordinates", "observation_waterTemp", "observation_airTemp", "observation_humidity", "observation_windSpeed", "observation_windDirection", "observation_precipitation", "observation_haze", "observation_becquerel")

# instantiate objs based on Marshmallow schemas
observation_schema = ObservationSchema()
observations_schema = ObservationSchema(many=True)

#--------------------------------------------------------------------------------
def token_required(f):
     @wraps(f)
     def decorator(*args, **kwargs):
          token = None

          if 'x-access-tokens' in request.headers:
               token = request.headers['x-access-tokens']

          if not token:
               return jsonify({'message': 'a valid token is missing'})
          
          try:
               data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"] )

          except:
               return jsonify({'message': 'token is invalid'})
          
          return f( *args, **kwargs)
     
     return decorator
#--------------------------------------------------------------------------------
# Helper methods for validation

def validate_date(date):
    # Validate date in the format YYYYMMDD
    return bool(re.match(r"^\d{4}\d{2}\d{2}$", date))

def validate_time(time):
    # Validate time in the format hh:mm:ss
    return bool(re.match(r"^\d{2}:\d{2}:\d{2}$", time))

def validate_timezone_offset(offset):
    # Validate timezone offset in the format UTC+hh:mm or UTC-hh:mm
    return bool(re.match(r"^UTC([+-])\d{2}:\d{2}$", offset))

def validate_coordinates(coord):
    # Validate coordinates in decimal degrees (float)
    try:
        float(coord)
        return True
    except ValueError:
        return False

def validate_temperature(temp):
    # Validate temperature in Celsius (float)
    return isinstance(temp, (int, float))

def validate_humidity(humidity):
    # Validate humidity in g/kg (float)
    return isinstance(humidity, (int, float))

def validate_wind_speed(wind_speed):
    # Validate wind speed in km/h (float)
    return isinstance(wind_speed, (int, float))

def validate_wind_direction(direction):
    # Validate wind direction in degrees (float)
    return isinstance(direction, (int, float))

def validate_precipitation(precipitation):
    # Validate precipitation in mm (float)
    return isinstance(precipitation, (int, float))

def validate_haze(haze):
    # Validate haze in percentage (float)
    return isinstance(haze, (int, float))

def validate_becquerel(becquerel):
    # Validate becquerel (Bq)
    return isinstance(becquerel, (int, float))
#--------------------------------------------------------------------------------
@app.get("/login")
def login():
    auth = request.authorization

    # If basic authentication values are present
    if auth:
        # Check if username and password are correct
        if auth.username == 'Team5' and auth.password == "APIPassword":
            # Current time
            now = datetime.utcnow()

            # JWT payload
            payload = {
                'sub': auth.username,               
                'iat': now,                         
                'exp': now + timedelta(minutes=30) 
            }

            # Encode the token
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

            return {"token": token}
        else:
            return {"message": "error - username or password is incorrect"}, 401
    else:
        return {"message": "no authorisation details"}, 401
          
#--------------------------------------------------------------------------------
@app.post("/observations/add_observations_json")
def observations_add_json():
    """endpoint uses json to add observation details to db"""
    json_data = request.get_json()  # req.get_json() used to access json sent
    print(json_data)  # used for debugging purposes

    # Validate the fields in the incoming JSON data
    observation_date = json_data.get('observation_date')
    observation_time = json_data.get('observation_time')
    observation_timeZone = json_data.get('observation_timeZone')
    observation_coordinates = json_data.get('observation_coordinates')
    observation_waterTemp = json_data.get('observation_waterTemp')
    observation_airTemp = json_data.get('observation_airTemp')
    observation_humidity = json_data.get('observation_humidity')
    observation_windSpeed = json_data.get('observation_windSpeed')
    observation_windDirection = json_data.get('observation_windDirection')
    observation_precipitation = json_data.get('observation_precipitation')
    observation_haze = json_data.get('observation_haze')
    observation_becquerel = json_data.get('observation_becquerel')

    # Parse and validate date and time
    try:
        observation_date = datetime.strptime(observation_date, '%Y-%m-%d').date()
        observation_time = datetime.strptime(observation_time, '%H:%M:%S').time()
    except ValueError:
        return {"message": "Invalid date or time format"}, 400

    # Validate other fields
    if not (validate_timezone_offset(observation_timeZone) and
            validate_coordinates(observation_coordinates) and
            validate_temperature(observation_waterTemp) and
            validate_temperature(observation_airTemp) and
            validate_humidity(observation_humidity) and
            validate_wind_speed(observation_windSpeed) and
            validate_wind_direction(observation_windDirection) and
            validate_precipitation(observation_precipitation) and
            validate_haze(observation_haze) and
            validate_becquerel(observation_becquerel)):
        return {"message": "Invalid data format"}, 400

    # Generate UUID if not provided
    observation_id = str(uuid.uuid4())

    # Create new observation object
    new_observation = Observation(
        observation_id=observation_id,
        observation_date=observation_date,
        observation_time=observation_time,
        observation_timeZone=observation_timeZone,
        observation_coordinates=observation_coordinates,
        observation_waterTemp=observation_waterTemp,
        observation_airTemp=observation_airTemp,
        observation_humidity=observation_humidity,
        observation_windSpeed=observation_windSpeed,
        observation_windDirection=observation_windDirection,
        observation_precipitation=observation_precipitation,
        observation_haze=observation_haze,
        observation_becquerel=observation_becquerel
    )

    # Add and commit to the database
    db.session.add(new_observation)

    db.session.commit()

    print("Record added:")
    print(json.dumps(json_data, indent=4))  # used for debugging purposes
    return observation_schema.jsonify(new_observation)
#--------------------------------------------------------------------------------
# endpoint to show all observations
@app.get("/observations/get_observations")
@token_required
def get_observations():
    all_observations = Observation.query.all()
    return observations_schema.jsonify(all_observations)
#--------------------------------------------------------------------------------
# endpoint uses route parameters to determine observation to be queried from db
@app.get("/observations/get_one_observation/<observation_id>")
@token_required
def get_one_observation(observation_id):
    observation = Observation.query.filter_by(observation_id=observation_id).first()
    return observation_schema.jsonify(observation)
#--------------------------------------------------------------------------------
#endpoint uses query parameters to get observation
@app.get("/observations/get_one_observation")
@token_required
def get_one_observation_query():
    observation_id = request.args.get("observation_id")
    observation = Observation.query.filter_by(observation_id=observation_id).first()
    return observation_schema.jsonify(observation)
#--------------------------------------------------------------------------------
# endpoint used to get observation by json
@app.get("/observations/get_one_observation_json")
@token_required
def get_one_observation_json():
     json_data = request.get_json() # used to access json data
     print(json_data) # used for debugging
     observation_id = json_data["observation_id"]
     observation = Observation.query.filter_by(observation_id=observation_id).first()
     return observation_schema.jsonify(observation)
#--------------------------------------------------------------------------------
# endpoint to delete one observation
@app.delete("/observations/delete_one_observation/<observation_id>")
@token_required
def delete_one_observation_route(observation_id): # observation_id accepted as an argument
     Observation.query.filter_by(observation_id=observation_id).delete()
     db.session.commit()

     return {"Observation Deleted" : f"observation_id: {observation_id}"}
#--------------------------------------------------------------------------------
if __name__ == '__main__':
     with app.app_context():
          db.create_all()
     app.run(debug=True)