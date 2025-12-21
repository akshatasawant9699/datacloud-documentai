# DocAI Mini

A simplified web application for processing documents using Salesforce Data Cloud Document AI.

## Features

- **OAuth 2.0 Authentication**: Secure login with Salesforce using the Authorization Code flow.
- **Runtime Configuration**: Configure Salesforce credentials directly in the UI (no .env file needed).
- **Document Processing**: Upload documents, generate schemas, and process them using Salesforce Document AI.
- **Vercel Ready**: Optimized for deployment on Vercel with serverless functions.

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Local Server**
   ```bash
   python backend/app_local.py
   ```

3. **Open Browser**
   Navigate to `http://localhost:5001`

## Usage

1. **Configure**: Enter your Salesforce Connected App details (Login URL, Client ID, Client Secret).
2. **Login**: Authenticate securely with Salesforce.
3. **Upload**: Select a document (PDF, image) to process.
4. **Process**: Review the schema and extract data using Document AI.

## Connected App Configuration

For the app to work, your Salesforce Connected App must have:
- **Callback URL**: `http://localhost:5001/auth/callback` (or your Vercel URL)
- **OAuth Scopes**: `api`, `full`, `refresh_token`, `offline_access`
- **Flows Enabled**: Authorization Code and Credentials Flow

## Deployment

Deploy to Vercel using the provided `vercel.json` configuration.
