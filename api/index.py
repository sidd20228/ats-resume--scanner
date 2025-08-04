from flask import Flask
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from the parent directory
from app import app

# Export the Flask app for Vercel
app = app
