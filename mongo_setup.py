# mongo_setup.py
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["sms_system"]

# Define a collection for program configurations
configurations = db["program_configurations"]
