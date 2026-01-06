# Salesforce Data Cloud - Document AI API Testbed

## Introduction

This project provides a sample implementation demonstrating how to use the Salesforce Data Cloud Document AI APIs. It creates a simple web interface that allows users to upload documents (PDFs or images) along with a JSON schema, and then processes these documents using Salesforce's document extraction capabilities.

The application showcases how to:
- Make authenticated API calls to Salesforce Data Cloud Document AI endpoints using OAuth 2.0
- Process document uploads and convert them to base64 encoding
- Submit documents for intelligent extraction with custom schema configurations
- Display the extracted structured data from documents

This testbed serves as a reference implementation for developers looking to integrate Salesforce Data Cloud's document processing capabilities into their own applications.

## Project Structure

```
sf-datacloud-idp-testbed/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings (API URLs, OAuth settings)
├── api_client.py          # API client for token management
├── requirements.txt       # Python dependencies
├── static/                # Static assets
│   ├── css/               # CSS stylesheets
│   │   └── style.css      # Main stylesheet
│   ├── js/                # JavaScript files
│   │   └── script.js      # Client-side functionality
│   └── json-jazz.html     # JSON Schema Generator tool
├── templates/             # HTML templates
│   └── index.html         # Main interface page
├── .env.example           # Example environment file
└── README.md              # Project documentation
```

## Environment Setup

1. **Clone the Repository**
    ```bash
    git clone https://github.com/ananth-anto/sf-datacloud-idp-testbed
    cd sf-datacloud-idp-testbed
    ```

2. **Create Environment File**
    ```bash
    cp .env.example .env
    ```

3. **Configure Salesforce Connected App**
    - Follow the [Setting Up External Client App guide](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_authenticate.htm&type=5)
    - **Important:** Use callback URL as `http://localhost:3000/auth/callback`
    - Copy your `ClientId`, `ClientSecret`, and `LoginUrl` from your Salesforce Connected App to your `.env` file

    Example `.env`:
    ```env
    LOGIN_URL=your-salesforce-login-url
    CLIENT_ID=your-salesforce-connected-app-client-id
    CLIENT_SECRET=your-salesforce-connected-app-client-secret
    API_VERSION=vXX.X
    TOKEN_FILE=access-token.secret
    ```

4. **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    ```
    - On macOS/Linux:
      ```bash
      source venv/bin/activate
      ```
    - On Windows:
      ```bash
      venv\Scripts\activate
      ```

5. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

6. **Run the Application**
    ```bash
    python app.py
    ```
    - The application will start and be available at `http://localhost:3000/` in your web browser.

---

## Using the Application

### Authentication Flow (OAuth 2.0 Web Server Flow)

1. **First Time Setup**: When you first visit the application, you'll see an "Authenticate with Salesforce" button
2. **Click Authenticate**: This will redirect you to Salesforce login page
3. **Login**: Enter your Salesforce credentials
4. **Authorize**: Grant permissions to the connected app
5. **Return**: You'll be redirected back to the application with a code in the URL
6. **Token Exchange**: The backend exchanges the code for an access token and instance URL
7. **Ready to Use**: The "Analyze Document" button will now be enabled

### Document Processing

1. Upload a document (supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP)
2. Enter a JSON schema defining the data structure you want to extract
3. Click "Analyze Document" to process the document
4. View the extracted structured data in the results section

## JSON Schema Format

The schema should be formatted as a JSON object that defines the fields you want to extract from the document. For example:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "VendorName": {
      "type": "string",
      "description": "Name of the vendor issuing the invoice"
    },
    "Vendor Address": {
      "type": "string",
      "description": "Full address of the vendor"
    },
    "Vendor Phone number": {
      "type": "string",
      "description": "Phone number"
    },
    "Billing Address": {
      "type": "string",
      "description": "Full name and address of the billing entity"
    },
    "Product Item List": {
      "type": "array",
      "items": {
        "type": "object",
        "description": "Table containing the list of products",
        "properties": {
          "Item ID": {
            "type": "string",
            "description": "Item id"
          },
          "Item Description": {
            "type": "string",
            "description": "Full description for the item"
          },
          "Quantity": {
            "type": "number",
            "description": "Number of items"
          },
          "Unit Price": {
            "type": "number"
          },
          "Line total": {
            "type": "number",
            "description": "Line total for the product line item"
          }
        }
      },
      "description": "Table containing the list of products"
    },
    "Total amount": {
      "type": "number"
    }
  }
}
```

## Authentication

The application uses OAuth 2.0 Web Server Flow (Authorization Code Grant) for authentication with Salesforce Data Cloud. The authentication flow:

1. **User clicks "Authenticate" button** - Frontend calls `/api/auth-info` to get Salesforce configuration
2. **User logs into Salesforce** - User enters credentials on Salesforce login page
3. **Salesforce redirects back** - With a code in the URL
4. **Token is exchanged and saved** - Backend exchanges the code for an access token and instance URL, which are stored in `access-token.secret`
5. **Token is used for API calls** - All subsequent API calls use the stored token and instance URL

### Token Management

- **Storage**: Access tokens and instance URLs are stored locally in `access-token.secret`
- **Security**: The token file is automatically added to `.gitignore` to prevent accidental commits
- **Expiration**: Salesforce access tokens expire. When expired, users will need to re-authenticate
- **Validation**: The application checks authentication status before allowing document processing

## Troubleshooting

### Common Issues

1. **Authentication Errors**: If you receive a 401 or 403 error, your access token may be expired. Click the "Authenticate" button to get a new token.
   
2. **Connected App Configuration**: Ensure your Salesforce Connected App has the correct callback URL and OAuth scopes configured.

3. **Schema Errors**: Ensure your schema is valid JSON and follows the expected format for the Salesforce Data Cloud Document AI API.

4. **File Format Issues**: Check that your document is in one of the supported formats and is not corrupted.

### Debugging

The application has logging enabled. Check the console output for detailed error messages and debugging information.

## Security Considerations

This testbed is intended for development and testing purposes only. For production use:

1. Never hardcode authentication tokens in your code
2. Implement proper user authentication and authorization
3. Use HTTPS in production for secure token transmission
4. Consider implementing token refresh logic for long-running applications
5. Store tokens in secure, encrypted storage rather than local files

## API Endpoints

- `GET /` - Main application interface
- `GET /api/status` - Check authentication status
- `GET /api/auth-info` - Get OAuth configuration
- `GET /auth/callback` - OAuth callback page (handles code exchange)
- `POST /extract-data` - Process document extraction

## Dependencies

- Flask==3.0.2
- Werkzeug==3.0.1
- requests==2.31.0

## License

This project is licensed under the MIT License - see the LICENSE file for details.
