from flask import Flask, request, jsonify, make_response
import json
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime, timedelta
import jwt
from functools import wraps

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
    observation_id = db.Column(db.String(80), primary_key=True)
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
    json_data = request.get_json() # req.get_json() used to access json sent
    print(json_data) # used for debugging purposes

    # Parse and validate date and time
    observation_date = datetime.strptime(json_data['observation_date'], '%Y-%m-%d').date()
    observation_time = datetime.strptime(json_data['observation_time'], '%H:%M:%S').time()

    new_observation = Observation (
        observation_id = json_data['observation_id'],
        observation_date = observation_date,
        observation_time = observation_time,
        observation_timeZone = json_data['observation_timeZone'],
        observation_coordinates = json_data['observation_coordinates'],
        observation_waterTemp = json_data['observation_waterTemp'],
        observation_airTemp = json_data['observation_airTemp'],
        observation_humidity = json_data['observation_humidity'],
        observation_windSpeed = json_data['observation_windSpeed'],
        observation_windDirection = json_data['observation_windDirection'],
        observation_precipitation = json_data['observation_precipitation'],
        observation_haze = json_data['observation_haze'],
        observation_becquerel = json_data['observation_becquerel']
    )
    db.session.add(new_observation)

    db.session.commit()
    print ("Record added:")
    print (json.dumps(json_data, indent=4)) # used for debugging purposes
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
     observation_id = request.args.get("observation_id") # req.args.get() used to access query parameters
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
@token_required
@app.delete("/observations/delete_one_observation/<observation_id>")
def delete_one_observation_route(observation_id): # observation_id accepted as an argument
     Observation.query.filter_by(observation_id=observation_id).delete()
     db.session.commit()

     return {"Observation Deleted" : f"observation_id: {observation_id}"}
#--------------------------------------------------------------------------------
# endpoint to update observation
@app.put("/observations/update_observation/<observation_id>")
@token_required
def update_observation(observation_id):
     observation = Observation.query.filter_by(observation_id=observation_id).first()
     
     json_data = request.get_json() # req.get_json() used to access json sent
     
     observation_id = request.json['observation_id']
     observation_date = datetime.strptime(json_data['observation_date'], '%Y-%m-%d').date()
     observation_time = datetime.strptime(json_data['observation_time'], '%H:%M:%S').time()
     observation_timeZone = request.json['observation_timeZone']
     observation_coordinates = request.json['observation_coordinates']
     observation_waterTemp = request.json['observation_waterTemp']
     observation_airTemp = request.json['observation_airTemp']
     observation_humidity = request.json['observation_humidity']
     observation_windSpeed = request.json['observation_windSpeed']
     observation_windDirection = request.json['observation_windDirection']
     observation_precipitation = request.json['observation_precipitation']
     observation_haze = request.json['observation_haze']
     observation_becquerel = request.json['observation_becquerel']

     observation.observation_id = observation_id
     observation.observation_date = observation_date
     observation.observation_time = observation_time
     observation.observation_timeZone = observation_timeZone
     observation.observation_coordinates = observation_coordinates
     observation.observation_waterTemp = observation_waterTemp
     observation.observation_airTemp = observation_airTemp
     observation.observation_humidity = observation_humidity
     observation.observation_windSpeed = observation_windSpeed
     observation.observation_windDirection = observation_windDirection
     observation.observation_precipitation = observation_precipitation
     observation.observation_haze = observation_haze
     observation.observation_becquerel = observation_becquerel

     db.session.commit()
     return observation_schema.jsonify(observation)
#--------------------------------------------------------------------------------
# endpoint to update one user
@app.patch("/observations/patch_one_observation/<observation_id>")
@token_required
def patch_one_observation_route(observation_id): # observation_id accepted as an argument
     
     json_data = request.get_json() # req.get_json() used to access json sent
     observation = Observation.query.filter_by(observation_id=observation_id).first()
     observation_id = request.json['observation_id']

     observation.observation_id = observation_id
     db.session.commit()

     return observation_schema.jsonify(observation)
#--------------------------------------------------------------------------------
if __name__ == '__main__':
     with app.app_context():
          db.create_all()
     app.run(debug=True)