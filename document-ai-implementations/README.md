# Document AI Implementations

This project contains two comprehensive Document AI implementations:

1. **Contact Enrichment Flow** - Automatically extracts and enriches contact information from documents
2. **Loan Pre-qualification Agent** - Processes loan applications and documents for automated pre-qualification

## Project Structure

```
document-ai-implementations/
├── contact-enrichment/
│   ├── salesforce/
│   │   ├── classes/
│   │   ├── flows/
│   │   └── lwc/
│   ├── python/
│   │   ├── app.py
│   │   ├── document_processor.py
│   │   └── contact_enrichment.py
│   └── frontend/
│       ├── index.html
│       └── static/
├── loan-prequalification/
│   ├── salesforce/
│   │   ├── classes/
│   │   ├── flows/
│   │   └── lwc/
│   ├── python/
│   │   ├── app.py
│   │   ├── loan_processor.py
│   │   └── qualification_engine.py
│   └── frontend/
│       ├── index.html
│       └── static/
├── shared/
│   ├── salesforce/
│   │   ├── classes/
│   │   └── objects/
│   └── python/
│       ├── document_ai_client.py
│       └── salesforce_client.py
└── docs/
    ├── setup-guide.md
    ├── contact-enrichment-guide.md
    └── loan-prequalification-guide.md
```

## Features

### Contact Enrichment Flow
- Document upload and processing
- Automatic contact information extraction
- Contact record enrichment
- Data validation and normalization
- Salesforce integration

### Loan Pre-qualification Agent
- Document processing for loan applications
- Automated qualification scoring
- Risk assessment
- Decision automation
- Integration with Salesforce CRM

## Setup Instructions

1. **Prerequisites**
   - Salesforce org with Document AI enabled
   - Python 3.8+
   - Node.js (for LWC development)

2. **Installation**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Deploy Salesforce components
   sfdx force:source:deploy -p salesforce/
   ```

3. **Configuration**
   - Configure Document AI settings in Salesforce
   - Set up authentication credentials
   - Configure webhook endpoints

## Usage

### Contact Enrichment
1. Upload a document (resume, business card, etc.)
2. The system automatically extracts contact information
3. Contact records are enriched with extracted data
4. Review and approve changes

### Loan Pre-qualification
1. Upload loan application documents
2. System processes and extracts relevant information
3. Automated qualification scoring
4. Generate pre-qualification report

## API Endpoints

### Contact Enrichment
- `POST /api/contact-enrichment/process` - Process document for contact enrichment
- `GET /api/contact-enrichment/status/{id}` - Get processing status
- `POST /api/contact-enrichment/enrich` - Enrich contact record

### Loan Pre-qualification
- `POST /api/loan-prequalification/process` - Process loan application
- `GET /api/loan-prequalification/status/{id}` - Get processing status
- `POST /api/loan-prequalification/qualify` - Run qualification assessment

## Documentation

- [Setup Guide](docs/setup-guide.md)
- [Contact Enrichment Guide](docs/contact-enrichment-guide.md)
- [Loan Pre-qualification Guide](docs/loan-prequalification-guide.md)


