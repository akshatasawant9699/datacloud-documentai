/**
 * DocumentAIExtractor - Apex class to extract data from documents using Salesforce Document AI
 * Supports any document type (Sales Order, Invoice, Healthcare Forms, etc.)
 * Returns extracted data with confidence scores
 */
public with sharing class DocumentAIExtractor {
    
    // Constants
    private static final String API_VERSION = 'v65.0';
    private static final String EXTRACT_ENDPOINT = '/services/data/' + API_VERSION + '/ssot/document-processing/actions/extract-data?htmlEncode=false&extractDataWithConfidenceScore=true';
    private static final String DEFAULT_ML_MODEL = 'llmgateway__VertexAIGemini20Flash001';
    
    /**
     * Invocable method for Flow integration
     * Extracts data from a ContentDocument using Document AI
     */
    @InvocableMethod(label='Extract Document Data' description='Extract data from a document using Document AI' category='Document AI')
    public static List<ExtractionResult> extractFromFlow(List<ExtractionRequest> requests) {
        List<ExtractionResult> results = new List<ExtractionResult>();
        
        for (ExtractionRequest request : requests) {
            ExtractionResult result = new ExtractionResult();
            try {
                // Get the document content
                ContentVersion cv = [
                    SELECT Id, Title, FileExtension, VersionData, ContentDocumentId 
                    FROM ContentVersion 
                    WHERE ContentDocumentId = :request.contentDocumentId 
                    AND IsLatest = true 
                    LIMIT 1
                ];
                
                // Convert to base64
                String base64Data = EncodingUtil.base64Encode(cv.VersionData);
                String mimeType = getMimeType(cv.FileExtension);
                
                // Get schema config
                String schemaConfig = String.isNotBlank(request.schemaConfig) 
                    ? request.schemaConfig 
                    : getDefaultSchema();
                
                // Get ML model
                String mlModel = String.isNotBlank(request.mlModel) 
                    ? request.mlModel 
                    : DEFAULT_ML_MODEL;
                
                // Call Document AI API
                String extractedJson = callDocumentAI(base64Data, mimeType, schemaConfig, mlModel);
                
                result.success = true;
                result.extractedData = extractedJson;
                result.documentTitle = cv.Title;
                result.errorMessage = null;
                
            } catch (Exception e) {
                result.success = false;
                result.extractedData = null;
                result.errorMessage = e.getMessage();
            }
            results.add(result);
        }
        
        return results;
    }
    
    /**
     * Main method to call Document AI API
     */
    public static String callDocumentAI(String base64Data, String mimeType, String schemaConfig, String mlModel) {
        // Build request body
        Map<String, Object> requestBody = new Map<String, Object>();
        requestBody.put('mlModel', mlModel);
        requestBody.put('schemaConfig', schemaConfig);
        
        List<Map<String, String>> files = new List<Map<String, String>>();
        Map<String, String> fileData = new Map<String, String>();
        fileData.put('mimeType', mimeType);
        fileData.put('data', base64Data);
        files.add(fileData);
        requestBody.put('files', files);
        
        String jsonBody = JSON.serialize(requestBody);
        
        // Make HTTP callout
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:DocumentAI_NamedCredential' + EXTRACT_ENDPOINT);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setTimeout(120000); // 2 minute timeout for large documents
        req.setBody(jsonBody);
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200 || res.getStatusCode() == 201) {
            // Parse and return the extracted data
            Map<String, Object> responseMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> dataList = (List<Object>) responseMap.get('data');
            
            if (dataList != null && !dataList.isEmpty()) {
                Map<String, Object> firstResult = (Map<String, Object>) dataList[0];
                String extractedData = (String) firstResult.get('data');
                
                if (String.isNotBlank(extractedData)) {
                    // Clean up HTML entities if present
                    extractedData = extractedData.replace('&quot;', '"').replace('&#92;', '\\');
                    return extractedData;
                }
            }
            return res.getBody();
        } else {
            throw new DocumentAIException('API Error: ' + res.getStatusCode() + ' - ' + res.getBody());
        }
    }
    
    /**
     * Alternative method using Session ID (for testing without Named Credentials)
     */
    public static String callDocumentAIWithSession(String base64Data, String mimeType, String schemaConfig, String mlModel, String instanceUrl) {
        // Build request body
        Map<String, Object> requestBody = new Map<String, Object>();
        requestBody.put('mlModel', mlModel);
        requestBody.put('schemaConfig', schemaConfig);
        
        List<Map<String, String>> files = new List<Map<String, String>>();
        Map<String, String> fileData = new Map<String, String>();
        fileData.put('mimeType', mimeType);
        fileData.put('data', base64Data);
        files.add(fileData);
        requestBody.put('files', files);
        
        String jsonBody = JSON.serialize(requestBody);
        
        // Make HTTP callout
        HttpRequest req = new HttpRequest();
        req.setEndpoint(instanceUrl + EXTRACT_ENDPOINT);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        req.setTimeout(120000);
        req.setBody(jsonBody);
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200 || res.getStatusCode() == 201) {
            Map<String, Object> responseMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> dataList = (List<Object>) responseMap.get('data');
            
            if (dataList != null && !dataList.isEmpty()) {
                Map<String, Object> firstResult = (Map<String, Object>) dataList[0];
                String extractedData = (String) firstResult.get('data');
                
                if (String.isNotBlank(extractedData)) {
                    extractedData = extractedData.replace('&quot;', '"').replace('&#92;', '\\');
                    return extractedData;
                }
            }
            return res.getBody();
        } else {
            throw new DocumentAIException('API Error: ' + res.getStatusCode() + ' - ' + res.getBody());
        }
    }
    
    /**
     * Get MIME type from file extension
     */
    private static String getMimeType(String fileExtension) {
        Map<String, String> mimeTypes = new Map<String, String>{
            'pdf' => 'application/pdf',
            'png' => 'image/png',
            'jpg' => 'image/jpeg',
            'jpeg' => 'image/jpeg',
            'tiff' => 'image/tiff',
            'tif' => 'image/tiff',
            'bmp' => 'image/bmp'
        };
        
        String ext = fileExtension.toLowerCase();
        return mimeTypes.containsKey(ext) ? mimeTypes.get(ext) : 'application/pdf';
    }
    
    /**
     * Default schema for Sales Order / Invoice extraction
     */
    private static String getDefaultSchema() {
        Map<String, Object> schema = new Map<String, Object>();
        schema.put('type', 'object');
        
        Map<String, Object> properties = new Map<String, Object>();
        
        // Document identification
        properties.put('document_type', new Map<String, Object>{
            'type' => 'string',
            'description' => 'Identify the document type: Sales Order, Invoice, Purchase Order, etc.'
        });
        properties.put('document_number', new Map<String, Object>{
            'type' => 'string',
            'description' => 'Primary document identifier'
        });
        properties.put('document_date', new Map<String, Object>{
            'type' => 'string',
            'description' => 'Date of the document'
        });
        
        // Customer info
        properties.put('customer_name', new Map<String, Object>{'type' => 'string', 'description' => 'Customer name'});
        properties.put('customer_address', new Map<String, Object>{'type' => 'string', 'description' => 'Customer address'});
        
        // Vendor info
        properties.put('vendor_name', new Map<String, Object>{'type' => 'string', 'description' => 'Vendor/Seller name'});
        properties.put('vendor_address', new Map<String, Object>{'type' => 'string', 'description' => 'Vendor address'});
        
        // Financial
        properties.put('total_amount', new Map<String, Object>{'type' => 'number', 'description' => 'Total amount'});
        properties.put('currency', new Map<String, Object>{'type' => 'string', 'description' => 'Currency code'});
        
        schema.put('properties', properties);
        
        return JSON.serialize(schema);
    }
    
    /**
     * Parse extracted data and return as list of field results with confidence scores
     */
    public static List<FieldResult> parseExtractedData(String jsonData) {
        List<FieldResult> results = new List<FieldResult>();
        
        if (String.isBlank(jsonData)) {
            return results;
        }
        
        Map<String, Object> dataMap = (Map<String, Object>) JSON.deserializeUntyped(jsonData);
        
        for (String fieldName : dataMap.keySet()) {
            Object fieldValue = dataMap.get(fieldName);
            
            if (fieldValue instanceof Map<String, Object>) {
                Map<String, Object> fieldData = (Map<String, Object>) fieldValue;
                
                FieldResult fr = new FieldResult();
                fr.fieldName = fieldName;
                fr.fieldType = (String) fieldData.get('type');
                fr.fieldValue = String.valueOf(fieldData.get('value'));
                fr.confidenceScore = fieldData.get('confidence_score') != null 
                    ? Decimal.valueOf(String.valueOf(fieldData.get('confidence_score'))) 
                    : null;
                
                // Handle nested arrays (like line_items)
                if (fr.fieldType == 'array' && fieldData.get('value') instanceof List<Object>) {
                    fr.fieldValue = JSON.serialize(fieldData.get('value'));
                    fr.isArray = true;
                }
                
                results.add(fr);
            }
        }
        
        return results;
    }
    
    // ============ Wrapper Classes ============
    
    /**
     * Input class for Flow
     */
    public class ExtractionRequest {
        @InvocableVariable(label='Content Document Id' required=true)
        public Id contentDocumentId;
        
        @InvocableVariable(label='Schema Config JSON' required=false)
        public String schemaConfig;
        
        @InvocableVariable(label='ML Model' required=false)
        public String mlModel;
    }
    
    /**
     * Output class for Flow
     */
    public class ExtractionResult {
        @InvocableVariable(label='Success')
        public Boolean success;
        
        @InvocableVariable(label='Extracted Data JSON')
        public String extractedData;
        
        @InvocableVariable(label='Document Title')
        public String documentTitle;
        
        @InvocableVariable(label='Error Message')
        public String errorMessage;
    }
    
    /**
     * Class to hold individual field results with confidence
     */
    public class FieldResult {
        @AuraEnabled public String fieldName { get; set; }
        @AuraEnabled public String fieldType { get; set; }
        @AuraEnabled public String fieldValue { get; set; }
        @AuraEnabled public Decimal confidenceScore { get; set; }
        @AuraEnabled public Boolean isArray { get; set; }
        
        public FieldResult() {
            this.isArray = false;
        }
    }
    
    /**
     * Custom exception
     */
    public class DocumentAIException extends Exception {}
}
