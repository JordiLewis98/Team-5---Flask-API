from flask import Flask, request
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_marshmallow import Marshmallow
from datetime import datetime

app = Flask(__name__)

# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///observations.db' # path to db
app.config['SQLALCHEMY_ECHO'] = True # echoes SQL for debug
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Observation(db.Model):
    """Definition of the Observation Model used by SQLAlchemy"""
    observation_id = db.Column(db.String (80), primary_key=True)
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

class ObservationSchema(ma.SQLAlchemyAutoSchema):
        """Definition used by serialization library based on Observation Model"""
        class Meta:
            fields = ("observation_id","observation_date","observation_time", "observation_timeZone", "observation_coordinates", "observation_waterTemp", "observation_airTemp", "observation_humidity", "observation_windSpeed", "observation_windDirection", "observation_precipitation", "observation_haze", "observation_becquerel")
# instantiate objs based on Marshmallow schemas
observation_schema = ObservationSchema()
observations_schema = ObservationSchema(many=True)

@app.get("/")
def hello_world():
    return "Hello World"

@app.post("/observations/add-observations-json")
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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()