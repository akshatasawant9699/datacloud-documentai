"""
Vercel Serverless Function Entry Point
This file is used by Vercel to deploy the Flask app as serverless functions
"""
from app import app

# Vercel expects the app to be named 'app' or 'handler'
# This file exposes the Flask app for Vercel's Python runtime
