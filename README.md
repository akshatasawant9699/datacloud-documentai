# Document AI Gateway

A comprehensive Salesforce Document AI integration platform that extracts structured data from documents (invoices, sales orders, healthcare forms, etc.) with confidence scores.

## Features

- **Universal Document Extraction**: Works with any document type (PDF, PNG, JPG, TIFF)
- **Confidence Scores**: Each extracted field includes AI confidence percentage
- **Smart Document Detection**: Automatically identifies Invoice vs Sales Order
- **Multiple Interfaces**: Web UI, Apex classes, LWC components, and Flow
- **Vercel Ready**: Deploy to Vercel with one click

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd doc-ai-gateway

# Copy environment template
cp .env.example .env

# Edit .env with your Salesforce credentials
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Locally

```bash
python app.py
```

Open http://localhost:3000 in your browser.

## Configuration

Create a `.env` file with your Salesforce Connected App credentials:

```env
LOGIN_URL=login.salesforce.com
CLIENT_ID=your-connected-app-client-id
CLIENT_SECRET=your-connected-app-client-secret
API_VERSION=v65.0
TOKEN_FILE=access-token.secret
```

### Connected App Setup

1. Go to Salesforce Setup → App Manager → New Connected App
2. Enable OAuth Settings
3. Add callback URL: `http://localhost:3000/auth/callback`
4. Select OAuth Scopes:
   - Full access (full)
   - Perform requests at any time (refresh_token, offline_access)
   - Manage user data via APIs (api)

## Deployment

### Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/doc-ai-gateway)

1. Click the deploy button
2. Set environment variables in Vercel:
   - `LOGIN_URL`
   - `CLIENT_ID`
   - `CLIENT_SECRET`
   - `API_VERSION`
3. Add your Vercel URL to Connected App callback URLs

### Deploy Salesforce Components

```bash
cd sf-apex-classes
sf project deploy start --source-dir force-app
```

## Project Structure

```
doc-ai-gateway/
├── app.py                    # Flask application
├── api_client.py             # Salesforce API client
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel deployment config
├── templates/               # HTML templates
├── static/                  # CSS, JS assets
├── schemas/                 # JSON schema definitions
├── demo/                    # Demo scripts
└── sf-apex-classes/         # Salesforce Apex & LWC
    └── force-app/
        └── main/default/
            ├── classes/     # Apex classes
            ├── lwc/         # Lightning Web Components
            └── flows/       # Screen Flows
```

## API Endpoint

```
POST /services/data/v65.0/ssot/document-processing/actions/extract-data
    ?htmlEncode=false
    &extractDataWithConfidenceScore=true
```

### Request Body

```json
{
  "mlModel": "llmgateway__VertexAIGemini20Flash001",
  "schemaConfig": "{...JSON schema...}",
  "files": [{
    "mimeType": "application/pdf",
    "data": "<base64-encoded-file>"
  }]
}
```

## Confidence Scores

Each extracted field includes a confidence score:

| Score | Indicator | Meaning |
|-------|-----------|---------|
| 90%+ | 🟢 Green | High confidence - Reliable |
| 70-89% | 🟡 Yellow | Medium confidence - Review |
| <70% | 🔴 Red | Low confidence - Verify |

## Supported File Types

- PDF (`.pdf`)
- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- TIFF (`.tiff`, `.tif`)
- BMP (`.bmp`)

## Security

- Never commit `.env` files or credentials
- Use environment variables for all secrets
- Token files are automatically gitignored

## License

MIT License - see [LICENSE](LICENSE) file
