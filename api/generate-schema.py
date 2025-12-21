from http.server import BaseHTTPRequestHandler
import json
import base64
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.utils import create_response

def generate_schema_from_document(filename, mime_type):
    """Generate a schema based on document type detected from filename"""
    filename_lower = filename.lower()
    
    # Resume/CV schema
    if any(word in filename_lower for word in ['resume', 'cv', 'curriculum']):
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the candidate"
                },
                "email": {
                    "type": "string",
                    "description": "Email address"
                },
                "phone": {
                    "type": "string",
                    "description": "Phone number"
                },
                "address": {
                    "type": "string",
                    "description": "Address or location"
                },
                "summary": {
                    "type": "string",
                    "description": "Professional summary or objective"
                },
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of skills"
                },
                "experience": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "title": {"type": "string"},
                            "duration": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    },
                    "description": "Work experience"
                },
                "education": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "institution": {"type": "string"},
                            "degree": {"type": "string"},
                            "year": {"type": "string"}
                        }
                    },
                    "description": "Educational background"
                }
            },
            "required": ["name"]
        }
    
    # Invoice schema
    elif 'invoice' in filename_lower:
        return {
            "type": "object",
            "properties": {
                "VendorName": {"type": "string", "description": "Name of the vendor"},
                "VendorAddress": {"type": "string", "description": "Address of the vendor"},
                "InvoiceNumber": {"type": "string", "description": "Invoice number"},
                "InvoiceDate": {"type": "string", "description": "Date of invoice"},
                "BillingAddress": {"type": "string", "description": "Billing address"},
                "Items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unitPrice": {"type": "number"},
                            "total": {"type": "number"}
                        }
                    }
                },
                "TotalAmount": {"type": "number", "description": "Total amount"}
            },
            "required": ["InvoiceNumber", "TotalAmount"]
        }
    
    # Receipt schema
    elif 'receipt' in filename_lower:
        return {
            "type": "object",
            "properties": {
                "MerchantName": {"type": "string"},
                "MerchantAddress": {"type": "string"},
                "TransactionDate": {"type": "string"},
                "Items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": "number"},
                            "price": {"type": "number"}
                        }
                    }
                },
                "Total": {"type": "number"}
            },
            "required": ["MerchantName", "Total"]
        }
    
    # Purchase Order schema
    elif any(word in filename_lower for word in ['purchase', 'order', 'po']):
        return {
            "type": "object",
            "properties": {
                "PONumber": {"type": "string", "description": "Purchase order number"},
                "OrderDate": {"type": "string", "description": "Order date"},
                "Vendor": {"type": "string", "description": "Vendor name"},
                "ShipTo": {"type": "string", "description": "Shipping address"},
                "Items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "itemCode": {"type": "string"},
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "unitPrice": {"type": "number"}
                        }
                    }
                },
                "TotalAmount": {"type": "number"}
            },
            "required": ["PONumber"]
        }
    
    # Contract/Agreement schema
    elif any(word in filename_lower for word in ['contract', 'agreement']):
        return {
            "type": "object",
            "properties": {
                "contractTitle": {"type": "string"},
                "effectiveDate": {"type": "string"},
                "parties": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "terms": {"type": "string"},
                "signatureDate": {"type": "string"}
            },
            "required": ["contractTitle"]
        }
    
    # Sales/Proof of Sale schema
    elif any(word in filename_lower for word in ['sale', 'sales', 'proof']):
        return {
            "type": "object",
            "properties": {
                "sellerName": {"type": "string", "description": "Name of seller"},
                "buyerName": {"type": "string", "description": "Name of buyer"},
                "saleDate": {"type": "string", "description": "Date of sale"},
                "itemsSold": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "number"},
                            "price": {"type": "number"}
                        }
                    }
                },
                "totalAmount": {"type": "number", "description": "Total sale amount"},
                "paymentMethod": {"type": "string"}
            },
            "required": ["totalAmount"]
        }
    
    # Default generic schema
    else:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "date": {"type": "string", "description": "Document date"},
                "content": {"type": "string", "description": "Main content"},
                "keyValues": {
                    "type": "object",
                    "description": "Key-value pairs extracted"
                }
            }
        }

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """Handle schema generation requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form data
            # For Vercel, we'll expect JSON with base64 encoded file
            try:
                data = json.loads(post_data.decode('utf-8'))
                filename = data.get('filename', 'document.pdf')
                mime_type = data.get('mime_type', 'application/pdf')
                base64_data = data.get('base64_data')
                
                if not base64_data:
                    response = create_response(400, {
                        'success': False,
                        'error': 'File data is required'
                    })
                    self.send_response(response['statusCode'])
                    for key, value in response['headers'].items():
                        self.send_header(key, value)
                    self.end_headers()
                    self.wfile.write(response['body'].encode('utf-8'))
                    return
                
                # Generate schema
                schema = generate_schema_from_document(filename, mime_type)
                
                response = create_response(200, {
                    'success': True,
                    'schema': schema,
                    'filename': filename,
                    'mime_type': mime_type
                })
                
            except json.JSONDecodeError:
                response = create_response(400, {
                    'success': False,
                    'error': 'Invalid JSON data'
                })
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode('utf-8'))
            
        except Exception as e:
            response = create_response(500, {
                'success': False,
                'error': f'Server error: {str(e)}'
            })
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode('utf-8'))

