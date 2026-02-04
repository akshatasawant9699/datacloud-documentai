# Document AI End-to-End Demo

Extract information from any document type using Salesforce Document AI with **confidence scores**.

## Features

- **Universal Schema**: Same configuration works for Sales Orders, Invoices, Healthcare Forms, etc.
- **Confidence Scores**: Each extracted field includes a confidence percentage
- **Multiple Interfaces**: Apex, Flow, LWC, and Python script options
- **Dynamic Document Types**: Auto-detects document type during extraction

---

## Quick Start

### Option 1: Python Demo Script (Quickest)

```bash
cd demo
python document_ai_demo.py
```

This will:
1. Authenticate with Salesforce
2. Let you choose demo type (Invoice, Healthcare, or Interactive)
3. Display extracted data with confidence scores

### Option 2: Salesforce LWC Component

1. Deploy the components to your org:
   ```bash
   cd sf-apex-classes
   sf project deploy start --source-dir force-app
   ```

2. Add the **Document AI Extractor** component to any Lightning page

3. Upload a document and click "Extract Data"

### Option 3: Flow

1. Deploy the Flow:
   ```bash
   sf project deploy start --metadata Flow:Document_AI_Extraction_Demo
   ```

2. Run the Flow from Setup → Flows → Document AI Extraction Demo

### Option 4: Anonymous Apex (Developer Console)

1. Open Developer Console
2. Debug → Open Execute Anonymous Window
3. Paste contents of `sf-apex-classes/scripts/apex/DocumentAI_Demo_AnonymousApex.apex`
4. Replace `YOUR_CONTENT_DOCUMENT_ID` with an actual document ID
5. Execute

---

## Understanding Confidence Scores

Each extracted field includes a confidence score from the AI model:

| Score | Indicator | Meaning |
|-------|-----------|---------|
| 90%+ | 🟢 Green | High confidence - Reliable extraction |
| 70-89% | 🟡 Yellow | Medium confidence - May need review |
| <70% | 🔴 Red | Low confidence - Requires verification |

### Sample Output

```
════════════════════════════════════════════════════════════
📊 EXTRACTED DATA WITH CONFIDENCE SCORES
════════════════════════════════════════════════════════════

  DOCUMENT TYPE: Sales Order
    └─ Confidence: 🟢 96%

  DOCUMENT NUMBER: SO-2024-001
    └─ Confidence: 🟢 94%

  CUSTOMER NAME: Acme Corporation
    └─ Confidence: 🟢 92%

  TOTAL AMOUNT: 15750.00
    └─ Confidence: 🟡 87%

  LINE ITEMS:
    Confidence: 🟡 82%
    Item 1:
      - description: Widget Pro
      - quantity: 100
      - unit_price: 157.50
```

---

## API Details

### Endpoint

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

### Universal Schema (Works for Any Document)

```json
{
  "type": "object",
  "properties": {
    "document_type": {
      "type": "string",
      "description": "Identify: Sales Order, Invoice, PO, Healthcare Form, etc."
    },
    "document_number": {
      "type": "string",
      "description": "Primary document identifier"
    },
    "document_date": {
      "type": "string",
      "description": "Document date"
    },
    "customer_name": {
      "type": "string",
      "description": "Customer name"
    },
    "vendor_name": {
      "type": "string",
      "description": "Vendor name"
    },
    "total_amount": {
      "type": "number",
      "description": "Total amount"
    },
    "line_items": {
      "type": "array",
      "items": {...}
    }
  }
}
```

---

## Configuration

Create a `.env` file from `.env.example` and fill in your Salesforce credentials:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `LOGIN_URL` - Your Salesforce login URL
- `CLIENT_ID` - Connected App Client ID
- `CLIENT_SECRET` - Connected App Client Secret
- `API_VERSION` - Salesforce API version (e.g., v65.0)

---

## Supported File Types

- PDF (`.pdf`)
- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- TIFF (`.tiff`, `.tif`)
- BMP (`.bmp`)

---

## Component Overview

### Apex Classes

| Class | Description |
|-------|-------------|
| `DocumentAIExtractor` | Main extraction logic, Flow invocable method |
| `DocumentAIController` | LWC controller with confidence parsing |
| `DocumentAIExtractorTest` | Unit tests |

### Lightning Web Component

| Component | Description |
|-----------|-------------|
| `documentAIExtractor` | Full-featured UI with file upload, schema selection, and results display |

### Flow

| Flow | Description |
|------|-------------|
| `Document_AI_Extraction_Demo` | Screen Flow for end-to-end demo |

---

## Deployment Commands

```bash
# Deploy everything
sf project deploy start --source-dir sf-apex-classes/force-app

# Deploy specific class
sf project deploy start --metadata ApexClass:DocumentAIExtractor

# Deploy LWC
sf project deploy start --metadata LightningComponentBundle:documentAIExtractor

# Deploy Flow
sf project deploy start --metadata Flow:Document_AI_Extraction_Demo
```

---

## Troubleshooting

### "Callout not allowed" Error
- Ensure Remote Site Setting is deployed
- Add your instance URL to Remote Site Settings in Setup

### Low Confidence Scores
- Try higher quality document scans
- Ensure text is legible
- Use appropriate schema for document type

### Authentication Errors
- Verify credentials are correct
- Check Connected App settings
- Ensure user has API access

---

## Next Steps

1. **Customize Schema**: Modify `schemaConfig` for specific document types
2. **Add Automation**: Trigger extraction from Record-Triggered Flow
3. **Store Results**: Create custom objects to store extracted data
4. **Review Workflow**: Route low-confidence extractions for human review
