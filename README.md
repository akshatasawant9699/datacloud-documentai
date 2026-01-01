# DocAI Mini

A simplified web application for processing documents using Salesforce Data Cloud Document AI.

## Features

- **OAuth 2.0 Authentication**: Secure login with Salesforce using the Authorization Code flow.
- **Runtime Configuration**: Configure Salesforce credentials directly in the UI (no .env file needed).
- **Document Processing**: Upload documents, generate schemas, and process them using Salesforce Document AI.
- **Vercel Ready**: Optimized for deployment on Vercel with serverless functions.

## Setup

### Prerequisites
- A Salesforce Org with Data Cloud and Document AI enabled.
- Python 3.9+
- [Salesforce Connected App Setup](SALESFORCE_SETUP.md)

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Local Server**
   ```bash
   # Runs on port 5002 by default to avoid conflicts
   python backend/app_local.py
   ```

3. **Open Browser**
   Navigate to `http://localhost:5002`

## Deployment on Vercel

1. **Push to GitHub**:
   Push this repository to your GitHub account.

2. **Import to Vercel**:
   - Go to [Vercel](https://vercel.com) and click "Add New Project".
   - Import your GitHub repository.
   - Framework Preset: **Other** (Vercel will detect Python/Flask or use `vercel.json`).
   - Click **Deploy**.

3. **Configure Salesforce**:
   - Update your Salesforce Connected App **Callback URL** to match your Vercel domain:
     `https://<your-project>.vercel.app/auth/callback`
   - Wait 2-10 minutes for Salesforce changes to propagate.

## Usage Guide

1. **Configure**: Enter your Salesforce Connected App details (Login URL, Client ID, Client Secret).
2. **Login**: Authenticate securely with Salesforce.
3. **Upload**: Select a document (PDF, image) to process.
4. **Process**: Review the schema and extract data using Document AI.

## Troubleshooting

- **Authentication Errors**: Ensure your Callback URL in Salesforce matches EXACTLY the URL you are accessing the app from (http vs https, port number, trailing slash).
- **CORS Errors**: If running locally, ensure you access via `localhost` and not `127.0.0.1`.
- **API Errors**: Check the browser console and Vercel logs for detailed error messages.
