from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException, BackgroundTasks,Depends
import subprocess
from fastapi import FastAPI, HTTPException
from typing import Dict
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import FastAPI
from mongo_setup import configurations 
import mysql.connector  # type: ignore # noqa
from datetime import datetime
import random
import requests
import time

app = FastAPI()

# Define which Python program handles which country-operator pairs
program_mapping = {
    "program1": ["Uzbekistan_UzMobile", "Ukraine_3Mob"],
    "program2": ["Tajikistan_MegaFon_TTMobile", "India_Reliance_WestBengal"],
    "program3": ["India_TATADOCOMO_MaharashtraGoa", "India_ViIndia_MaharashtraGoa"],
    "program4": ["India_AirTel_Gujarat"]
}

def manage_screen_session(action, program_name):
    try:
        if action == "start":
            subprocess.run(["screen", "-dmS", program_name, "python3", f"{program_name}.py"], check=True)
            return {"status": "started", "session": program_name}
        elif action == "stop":
            subprocess.run(["screen", "-S", program_name, "-X", "quit"], check=True)
            return {"status": "stopped", "session": program_name}
        elif action == "restart":
            subprocess.run(["screen", "-S", program_name, "-X", "quit"], check=True)
            subprocess.run(["screen", "-dmS", program_name, "python3", f"{program_name}.py"], check=True)
            return {"status": "restarted", "session": program_name}
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail=f"Failed to {action} session {program_name}")

@app.post("/process/{program}/start")
async def start_session(program: str):
    if program in program_mapping:
        return manage_screen_session("start", program)
    else:
        raise HTTPException(status_code=404, detail="Program not found")

@app.post("/process/{program}/stop")
async def stop_session(program: str):
    if program in program_mapping:
        return manage_screen_session("stop", program)
    else:
        raise HTTPException(status_code=404, detail="Program not found")

@app.post("/process/{program}/restart")
async def restart_session(program: str):
    if program in program_mapping:
        return manage_screen_session("restart", program)
    else:
        raise HTTPException(status_code=404, detail="Program not found")
    







# In-memory metrics storage, could also use Redis for persistent storage
sms_metrics = {}

# Define rate limits and settings
MAX_SMS_PER_MINUTE = 10  # per country
country_send_times = {}

class SMSEntry(BaseModel):
    country_operator: str
    success: bool
    timestamp: datetime = datetime.now()

# Utility function to initialize metrics for a new country-operator
def initialize_metrics(country_operator):
    sms_metrics[country_operator] = {
        "sent": 0,
        "success": 0,
        "failures": 0,
        "last_reset": datetime.now()
    }

# Endpoint to send SMS and track metrics
@app.post("/send_sms/")
async def send_sms(entry: SMSEntry):
    country_operator = entry.country_operator

    # Check if the country-operator is initialized
    if country_operator not in sms_metrics:
        initialize_metrics(country_operator)

    # Rate limiting
    now = datetime.now()
    if country_operator not in country_send_times:
        country_send_times[country_operator] = []
    
    # Remove timestamps older than 1 minute for rate calculation
    country_send_times[country_operator] = [t for t in country_send_times[country_operator] if now - t < timedelta(minutes=1)]

    if len(country_send_times[country_operator]) >= MAX_SMS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded for this country")

    # Log the SMS attempt
    country_send_times[country_operator].append(now)
    sms_metrics[country_operator]["sent"] += 1
    if entry.success:
        sms_metrics[country_operator]["success"] += 1
    else:
        sms_metrics[country_operator]["failures"] += 1
    
    return {"message": "SMS processed", "success": entry.success}

# Endpoint to get metrics for all country-operator pairs
@app.get("/metrics/")
async def get_metrics():
    return sms_metrics

# Endpoint to get metrics for a specific country-operator pair
@app.get("/metrics/{country_operator}")
async def get_country_operator_metrics(country_operator: str):
    if country_operator not in sms_metrics:
        raise HTTPException(status_code=404, detail="Country-operator not found")
    return sms_metrics[country_operator]

# Task to reset metrics periodically (every minute)
def reset_metrics():
    while True:
        time.sleep(60)
        for country_operator, data in sms_metrics.items():
            # Reset only if last reset was over 1 minute ago
            if datetime.now() - data["last_reset"] >= timedelta(minutes=1):
                data["sent"] = 0
                data["success"] = 0
                data["failures"] = 0
                data["last_reset"] = datetime.now()
   






# In-memory database for country-operator configurations
country_operator_configs = {}


class CountryOperatorConfig(BaseModel):
    country: str
    operator: str
    high_priority: bool = False

# Initialize SMS metrics for the new country-operator pair
def initialize_metrics(country_operator):
    sms_metrics[country_operator] = {
        "sent": 0,
        "success": 0,
        "failures": 0,
        "last_reset": datetime.now()
    }

# CRUD Endpoints for Country-Operator Management

# Create new country-operator pair
@app.post("/country_operator/")
async def add_country_operator(config: CountryOperatorConfig):
    country_operator = f"{config.country}_{config.operator}"
    
    if country_operator in country_operator_configs:
        raise HTTPException(status_code=400, detail="Country-operator already exists")
    
    # Add to configurations and initialize metrics
    country_operator_configs[country_operator] = config.dict()
    initialize_metrics(country_operator)
    
    return {"message": "Country-operator added successfully", "config": config}

# Retrieve country-operator configuration
@app.get("/country_operator/{country_operator}")
async def get_country_operator(country_operator: str):
    if country_operator not in country_operator_configs:
        raise HTTPException(status_code=404, detail="Country-operator not found")
    return country_operator_configs[country_operator]

# Update existing country-operator configuration
@app.put("/country_operator/{country_operator}")
async def update_country_operator(country_operator: str, config: CountryOperatorConfig):
    if country_operator not in country_operator_configs:
        raise HTTPException(status_code=404, detail="Country-operator not found")
    
    # Update the configuration
    country_operator_configs[country_operator] = config.dict()
    return {"message": "Country-operator updated successfully", "config": config}

# Delete a country-operator pair
@app.delete("/country_operator/{country_operator}")
async def delete_country_operator(country_operator: str):
    if country_operator not in country_operator_configs:
        raise HTTPException(status_code=404, detail="Country-operator not found")

    # Prevent deletion of high-priority pairs
    if country_operator_configs[country_operator].get("high_priority"):
        raise HTTPException(status_code=403, detail="Cannot delete a high-priority pair")

    # Remove from configurations and metrics
    del country_operator_configs[country_operator]
    del sms_metrics[country_operator]
    
    return {"message": "Country-operator deleted successfully"}

# Endpoint to set high-priority status for a pair
@app.put("/country_operator/{country_operator}/set_priority")
async def set_high_priority(country_operator: str, high_priority: bool):
    if country_operator not in country_operator_configs:
        raise HTTPException(status_code=404, detail="Country-operator not found")
    
    country_operator_configs[country_operator]["high_priority"] = high_priority
    return {"message": f"High-priority status set to {high_priority}", "country_operator": country_operator}







# Configure Telegram Bot
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'

# SMS Metrics and Program Configurations
sms_metrics = {}
country_operator_configs = {}

# Set a critical success rate threshold (e.g., 80%)
CRITICAL_SUCCESS_THRESHOLD = 0.8

class SMSEntry(BaseModel):
    country_operator: str
    success: bool
    timestamp: datetime = datetime.now()

# Function to send alert via Telegram
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Failed to send Telegram message:", e)

# Background task for real-time metrics check
def monitor_metrics(background_tasks: BackgroundTasks):
    for country_operator, metrics in sms_metrics.items():
        sent = metrics.get("sent", 0)
        success = metrics.get("success", 0)
        if sent > 0:
            success_rate = success / sent
            if success_rate < CRITICAL_SUCCESS_THRESHOLD:
                message = (
                    f"Alert: Success rate for {country_operator} has dropped below critical "
                    f"threshold ({success_rate:.2%}). Immediate action required."
                )
                background_tasks.add_task(send_telegram_message, message)

# Endpoint to send SMS and track metrics with alert on failure
@app.post("/send_sms/")
async def send_sms(entry: SMSEntry, background_tasks: BackgroundTasks):
    country_operator = entry.country_operator

    if country_operator not in sms_metrics:
        sms_metrics[country_operator] = {"sent": 0, "success": 0, "failures": 0}

    sms_metrics[country_operator]["sent"] += 1
    if entry.success:
        sms_metrics[country_operator]["success"] += 1
    else:
        sms_metrics[country_operator]["failures"] += 1

    # Run the metrics monitoring in the background
    background_tasks.add_task(monitor_metrics, background_tasks)

    return {"message": "SMS processed", "success": entry.success}

# Endpoint to manage screen sessions (Process Management)
@app.post("/manage_session/")
async def manage_session(action: str, country_operator: str):
    # Placeholder for session management logic
    # Simulate checking for high-priority and adding a failure alert
    if country_operator in country_operator_configs:
        if country_operator_configs[country_operator].get("high_priority"):
            if action == "stop":
                raise HTTPException(status_code=403, detail="Cannot stop a high-priority pair")
        if action == "fail":
            # Simulate program failure alert
            message = f"Alert: Program handling {country_operator} has failed."
            send_telegram_message(message)
    return {"message": f"{action} action executed on {country_operator}"}

# Endpoint to add or update country-operator configuration with high-priority setting
@app.post("/country_operator/")
async def add_country_operator(config: CountryOperatorConfig):
    country_operator = f"{config.country}_{config.operator}"
    
    if country_operator not in country_operator_configs:
        country_operator_configs[country_operator] = config.dict()
        sms_metrics[country_operator] = {"sent": 0, "success": 0, "failures": 0}
    else:
        country_operator_configs[country_operator].update(config.dict())
    
    return {"message": "Country-operator configuration updated", "config": country_operator_configs[country_operator]}



#5
# JWT Configurations
class Settings(BaseModel):
    authjwt_secret_key: str = "supersecret"  # Change this to a more secure secret in production

@AuthJWT.load_config
def get_config():
    return Settings()

# Exception handler for JWT errors
@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

# User model for login
class User(BaseModel):
    username: str
    password: str

# In-memory storage for simplicity, replace with a database in production
users_db = {
    "admin": {"username": "admin", "password": "password"}  # Dummy user
}

# Endpoint to login and receive JWT token
@app.post("/login")
def login(user: User, Authorize: AuthJWT = Depends()):
    # Authenticate user
    if user.username in users_db and users_db[user.username]["password"] == user.password:
        # Create JWT token if authentication passes
        access_token = Authorize.create_access_token(subject=user.username)
        return {"access_token": access_token}
    else:
        raise HTTPException(status_code=401, detail="Bad username or password")

# Define a dependency that checks for JWT
def require_jwt_auth(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

# In-memory metrics storage, replace with Redis or database for persistence
sms_metrics = {}

MAX_SMS_PER_MINUTE = 10  # per country
country_send_times = {}

class SMSEntry(BaseModel):
    country_operator: str
    success: bool
    timestamp: datetime = datetime.now()

# Initialize metrics for a new country-operator
def initialize_metrics(country_operator):
    sms_metrics[country_operator] = {
        "sent": 0,
        "success": 0,
        "failures": 0,
        "last_reset": datetime.now()
    }

# Protected endpoint to send SMS and track metrics
@app.post("/send_sms/", dependencies=[Depends(require_jwt_auth)])
async def send_sms(entry: SMSEntry, Authorize: AuthJWT = Depends()):
    country_operator = entry.country_operator

    # Initialize country_operator if needed
    if country_operator not in sms_metrics:
        initialize_metrics(country_operator)

    now = datetime.now()
    if country_operator not in country_send_times:
        country_send_times[country_operator] = []

    # Enforce rate limiting per country
    country_send_times[country_operator] = [
        t for t in country_send_times[country_operator] if now - t < timedelta(minutes=1)
    ]

    if len(country_send_times[country_operator]) >= MAX_SMS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded for this country")

    # Record SMS attempt
    country_send_times[country_operator].append(now)
    sms_metrics[country_operator]["sent"] += 1
    if entry.success:
        sms_metrics[country_operator]["success"] += 1
    else:
        sms_metrics[country_operator]["failures"] += 1
    
    return {"message": "SMS processed", "success": entry.success}

# Protected endpoint to get metrics
@app.get("/metrics/", dependencies=[Depends(require_jwt_auth)])
async def get_metrics():
    return sms_metrics

# Protected endpoint to get metrics for a specific country-operator pair
@app.get("/metrics/{country_operator}", dependencies=[Depends(require_jwt_auth)])
async def get_country_operator_metrics(country_operator: str):
    if country_operator not in sms_metrics:
        raise HTTPException(status_code=404, detail="Country-operator not found")
    return sms_metrics[country_operator]

# Background task for resetting metrics
def reset_metrics():
    while True:
        time.sleep(60)
        for country_operator, data in sms_metrics.items():
            # Reset every minute if needed
            if datetime.now() - data["last_reset"] >= timedelta(minutes=1):
                data["sent"] = 0
                data["success"] = 0
                data["failures"] = 0
                data["last_reset"] = datetime.now()




#frountend last part
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dummy user data
fake_users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "password": "password",  # Store hashed passwords in real use cases
    }
}

def authenticate_user(email: str, password: str):
    user = fake_users_db.get(email)
    if user and user["password"] == password:
        return user
    return None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user["email"]})
    return {"token": access_token}

#mongodb connection

class ProgramConfig(BaseModel):
    country: str
    operator: str
    priority: bool
    session_details: dict

@app.post("/configurations/")
async def add_configuration(config: ProgramConfig):
    configurations.insert_one(config.dict())
    return {"message": "Configuration added successfully"}

@app.get("/configurations/")
async def get_configurations():
    return list(configurations.find({}, {"_id": 0}))

@app.put("/configurations/{country_operator}")
async def update_configuration(country_operator: str, config: ProgramConfig):
    result = configurations.update_one({"country_operator": country_operator}, {"$set": config.dict()})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"message": "Configuration updated successfully"}



#mysql connection
# Connect to MySQL
mysql_db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",
    database="sms_metrics_db"
)

@app.post("/metrics/")
async def add_sms_metric(country_operator: str, sms_sent: int, success_rate: float, failures: int):
    cursor = mysql_db.cursor()
    query = "INSERT INTO sms_metrics (country_operator, sms_sent, success_rate, failures) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (country_operator, sms_sent, success_rate, failures))
    mysql_db.commit()
    cursor.close()
    return {"message": "SMS metric added successfully"}

@app.get("/metrics/")
async def get_sms_metrics():
    cursor = mysql_db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sms_metrics ORDER BY timestamp DESC LIMIT 100")
    metrics = cursor.fetchall()
    cursor.close()
    return metrics
