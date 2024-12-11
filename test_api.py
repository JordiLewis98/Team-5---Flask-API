import pytest
from app import app, db, Observation
from datetime import date, time

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

#-------------------------------------------------------------------------------------------------------
def test_login_success(client):
    """Test successful login"""
    response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6QVBJUGFzc3dvcmQ='  # Base64 for 'Team5:APIPassword'
    })
    assert response.status_code == 200
    assert 'token' in response.json

#-------------------------------------------------------------------------------------------------------
def test_login_failure(client):
    """Test unsuccessful login"""
    response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6SW5jb3JyZWN0UGFzcw=='  # Base64 for 'Team5:IncorrectPass'
    })
    assert response.status_code == 401
    assert response.json['message'] == "error - username or password is incorrect"
    
#-------------------------------------------------------------------------------------------------------
def test_add_observation(client):
    """Test adding an observation"""
    # Log in to get a valid token
    login_response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6QVBJUGFzc3dvcmQ=' 
    })
    token = login_response.json['token']

    # Prepare observation data
    observation_data = {
        "observation_date": "2024-12-10",
        "observation_time": "12:00:00",
        "observation_timeZone": "UTC+00:00",
        "observation_coordinates": "51.5074,-0.1278",
        "observation_waterTemp": 15.5,
        "observation_airTemp": 20.0,
        "observation_humidity": 60,
        "observation_windSpeed": 5.5,
        "observation_windDirection": 180,
        "observation_precipitation": 10,
        "observation_haze": 0.1,
        "observation_becquerel": 200
    }

    # Send the POST request
    response = client.post(
        '/observations/add_observations_json',
        json=observation_data,
        headers={'x-access-tokens': token}
    )

    assert response.status_code == 200 

#-------------------------------------------------------------------------------------------------------
def test_get_observations(client):
    """Test retrieving all observations"""
    # Log in to get a valid token
    login_response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6QVBJUGFzc3dvcmQ=' 
    })
    token = login_response.json['token']

    # Create an observation instance instead of a dictionary
    observation_data = {
        "observation_date": date(2024, 12, 10),
        "observation_time": time(12,00,00),
        "observation_timeZone": "UTC+00:00",
        "observation_coordinates": "51.5074,-0.1278",
        "observation_waterTemp": 15.5,
        "observation_airTemp": 20.0,
        "observation_humidity": 60,
        "observation_windSpeed": 5.5,
        "observation_windDirection": 180,
        "observation_precipitation": 10,
        "observation_haze": 0.1,
        "observation_becquerel": 200
    }

    # Create the Observation instance
    observation = Observation(**observation_data)

    # Add the observation to the database
    with app.app_context():
        db.session.add(observation)
        db.session.commit()

    # Retrieve observations
    response = client.get('/observations/get_observations', headers={
        'x-access-tokens': token
    })
    assert response.status_code == 200
    assert len(response.json) > 0  # Ensure observations are returned

#-------------------------------------------------------------------------------------------------------
def test_get_one_observation(client):
    """Test retrieving a single observation using route parameters"""
    # Log in to get token
    login_response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6QVBJUGFzc3dvcmQ='
    })
    token = login_response.json['token']

    # Create a sample observation
    observation_data = {
        "observation_date": date(2024, 12, 10), # Date and Time passed through as objects  
        "observation_time": time(12, 0, 0),     # due to String conversion being handled when adding an Observation
        "observation_timeZone": "UTC+00:00",
        "observation_coordinates": "51.5074,-0.1278",
        "observation_waterTemp": 15.5,
        "observation_airTemp": 20.0,
        "observation_humidity": 60,
        "observation_windSpeed": 5.5,
        "observation_windDirection": 180,
        "observation_precipitation": 10,
        "observation_haze": 0.1,
        "observation_becquerel": 200,
    }
    observation = Observation(**observation_data)

    # Add observation to database
    with app.app_context():
        db.session.add(observation)
        db.session.commit()
        observation_id = observation.observation_id


    # Retrieve the observation
    response = client.get(f'/observations/get_one_observation/{observation_id}', headers={
        'x-access-tokens': token
    })

    assert response.status_code == 200
    assert response.json["observation_waterTemp"] == observation_data["observation_waterTemp"]

#-------------------------------------------------------------------------------------------------------
def test_get_one_observation_query(client):
    """Test retrieving a single observation using query parameters"""
    # Log in to get token
    login_response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6QVBJUGFzc3dvcmQ='
    })
    token = login_response.json['token']

    # Create a sample observation
    observation_data = {
        "observation_date": date(2024, 12, 10),
        "observation_time": time(12, 0, 0),
        "observation_timeZone": "UTC+00:00",
        "observation_coordinates": "51.5074,-0.1278",
        "observation_waterTemp": 15.5,
        "observation_airTemp": 20.0,
        "observation_humidity": 60,
        "observation_windSpeed": 5.5,
        "observation_windDirection": 180,
        "observation_precipitation": 10,
        "observation_haze": 0.1,
        "observation_becquerel": 200,
    }
    observation = Observation(**observation_data)

    with app.app_context():
        db.session.add(observation)
        db.session.commit()
        observation_id = observation.observation_id

    # Retrieve the observation using query params
    response = client.get(f'/observations/get_one_observation?observation_id={observation_id}', headers={
        'x-access-tokens': token
    })

    assert response.status_code == 200
    assert response.json["observation_waterTemp"] == observation_data["observation_waterTemp"]

#-------------------------------------------------------------------------------------------------------
def test_get_one_observation_json(client):
    """Test retrieving a single observation using JSON"""
     # Log in to get token
    login_response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6QVBJUGFzc3dvcmQ='
    })
    token = login_response.json['token']

    # Create a sample observation
    observation_data = {
        "observation_date": date(2024, 12, 10),
        "observation_time": time(12, 0, 0),
        "observation_timeZone": "UTC+00:00",
        "observation_coordinates": "51.5074,-0.1278",
        "observation_waterTemp": 15.5,
        "observation_airTemp": 20.0,
        "observation_humidity": 60,
        "observation_windSpeed": 5.5,
        "observation_windDirection": 180,
        "observation_precipitation": 10,
        "observation_haze": 0.1,
        "observation_becquerel": 200,
    }
    observation = Observation(**observation_data)

    with app.app_context():
        db.session.add(observation)
        db.session.commit()
        observation_id = observation.observation_id

    # Retrieve the observation using JSON
    response = client.get('/observations/get_one_observation_json', headers={
        'x-access-tokens': token,
        'Content-Type': 'application/json'
    }, json={"observation_id": observation_id})

    assert response.status_code == 200
    assert response.json["observation_waterTemp"] == observation_data["observation_waterTemp"]

#-------------------------------------------------------------------------------------------------------
def test_delete_one_observation(client):
    """Test deleting a single observation"""
    # Log in to get token
    login_response = client.get('/login', headers={
        'Authorization': 'Basic VGVhbTU6QVBJUGFzc3dvcmQ='
    })
    token = login_response.json['token']

    # Create a sample observation
    observation_data = {
        "observation_date": date(2024, 12, 10),
        "observation_time": time(12, 0, 0),
        "observation_timeZone": "UTC+00:00",
        "observation_coordinates": "51.5074,-0.1278",
        "observation_waterTemp": 15.5,
        "observation_airTemp": 20.0,
        "observation_humidity": 60,
        "observation_windSpeed": 5.5,
        "observation_windDirection": 180,
        "observation_precipitation": 10,
        "observation_haze": 0.1,
        "observation_becquerel": 200,
    }
    observation = Observation(**observation_data)

    with app.app_context():
        db.session.add(observation)
        db.session.commit()
        observation_id = observation.observation_id

    # Delete the observation
    response = client.delete(f'/observations/delete_one_observation/{observation_id}', headers={
        'x-access-tokens': token
    })

    assert response.status_code == 200
    assert f"observation_id: {observation_id}" in response.json["Observation Deleted"]

    # Verify deletion
    with app.app_context():
        deleted_observation = Observation.query.filter_by(observation_id=observation_id).first()
        assert deleted_observation is None
