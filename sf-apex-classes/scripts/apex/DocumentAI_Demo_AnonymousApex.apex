/**
 * Anonymous Apex for Document AI Demo
 * Run this in Developer Console or VS Code to test extraction
 * 
 * SETUP STEPS:
 * 1. Upload a document to Salesforce Files first
 * 2. Get the ContentDocumentId
 * 3. Replace 'YOUR_CONTENT_DOCUMENT_ID' below with the actual ID
 * 4. Execute this script
 */

// Configuration
// Get instance URL dynamically
String INSTANCE_URL = URL.getOrgDomainUrl().toExternalForm();
String ML_MODEL = 'llmgateway__VertexAIGemini20Flash001';

// Universal schema that works for any document type
String schemaConfig = '{' +
    '"type":"object",' +
    '"properties":{' +
        '"document_type":{"type":"string","description":"Identify: Sales Order, Invoice, Purchase Order, Healthcare Form, etc."},' +
        '"document_number":{"type":"string","description":"Primary document identifier"},' +
        '"document_date":{"type":"string","description":"Document date"},' +
        '"customer_name":{"type":"string","description":"Customer name"},' +
        '"vendor_name":{"type":"string","description":"Vendor name"},' +
        '"total_amount":{"type":"number","description":"Total amount"},' +
        '"currency":{"type":"string","description":"Currency"},' +
        '"line_items":{"type":"array","description":"Line items","items":{"type":"object","properties":{"description":{"type":"string"},"quantity":{"type":"number"},"unit_price":{"type":"number"}}}}' +
    '}' +
'}';

// ============================================================
// Option 1: Test with an existing ContentDocument
// ============================================================
// Replace this with your actual ContentDocumentId
// You can find it by querying: SELECT Id, Title FROM ContentDocument ORDER BY CreatedDate DESC LIMIT 5

Id contentDocumentId = 'YOUR_CONTENT_DOCUMENT_ID'; // <-- REPLACE THIS

if (contentDocumentId != null && contentDocumentId != 'YOUR_CONTENT_DOCUMENT_ID') {
    try {
        // Get the document
        ContentVersion cv = [
            SELECT Id, Title, FileExtension, VersionData 
            FROM ContentVersion 
            WHERE ContentDocumentId = :contentDocumentId 
            AND IsLatest = true 
            LIMIT 1
        ];
        
        System.debug('📄 Processing document: ' + cv.Title);
        
        // Encode to base64
        String base64Data = EncodingUtil.base64Encode(cv.VersionData);
        
        // Determine MIME type
        String mimeType = 'application/pdf';
        if (cv.FileExtension == 'png') mimeType = 'image/png';
        else if (cv.FileExtension == 'jpg' || cv.FileExtension == 'jpeg') mimeType = 'image/jpeg';
        
        // Build request body
        Map<String, Object> requestBody = new Map<String, Object>();
        requestBody.put('mlModel', ML_MODEL);
        requestBody.put('schemaConfig', schemaConfig);
        
        List<Map<String, String>> files = new List<Map<String, String>>();
        Map<String, String> fileData = new Map<String, String>();
        fileData.put('mimeType', mimeType);
        fileData.put('data', base64Data);
        files.add(fileData);
        requestBody.put('files', files);
        
        String jsonBody = JSON.serialize(requestBody);
        
        // Make API call
        String endpoint = INSTANCE_URL + '/services/data/v65.0/ssot/document-processing/actions/extract-data?htmlEncode=false&extractDataWithConfidenceScore=true';
        
        HttpRequest req = new HttpRequest();
        req.setEndpoint(endpoint);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        req.setTimeout(120000);
        req.setBody(jsonBody);
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        System.debug('📊 Response Status: ' + res.getStatusCode());
        
        if (res.getStatusCode() == 200 || res.getStatusCode() == 201) {
            // Parse response
            Map<String, Object> responseMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> dataList = (List<Object>) responseMap.get('data');
            
            if (dataList != null && !dataList.isEmpty()) {
                Map<String, Object> firstResult = (Map<String, Object>) dataList[0];
                String extractedData = (String) firstResult.get('data');
                
                // Clean up HTML entities
                extractedData = extractedData.replace('&quot;', '"');
                
                System.debug('');
                System.debug('════════════════════════════════════════════════════════════');
                System.debug('📊 EXTRACTED DATA WITH CONFIDENCE SCORES');
                System.debug('════════════════════════════════════════════════════════════');
                
                // Parse and display
                Map<String, Object> extracted = (Map<String, Object>) JSON.deserializeUntyped(extractedData);
                
                for (String fieldName : extracted.keySet()) {
                    Object fieldValue = extracted.get(fieldName);
                    
                    if (fieldValue instanceof Map<String, Object>) {
                        Map<String, Object> fieldData = (Map<String, Object>) fieldValue;
                        Object value = fieldData.get('value');
                        Object confidence = fieldData.get('confidence_score');
                        
                        String confDisplay = '';
                        if (confidence != null) {
                            Decimal confScore = Decimal.valueOf(String.valueOf(confidence)) * 100;
                            if (confScore >= 90) confDisplay = '🟢 ' + confScore.setScale(0) + '%';
                            else if (confScore >= 70) confDisplay = '🟡 ' + confScore.setScale(0) + '%';
                            else confDisplay = '🔴 ' + confScore.setScale(0) + '%';
                        }
                        
                        if (value != null && String.valueOf(value) != 'null') {
                            System.debug('');
                            System.debug('  ' + fieldName.replace('_', ' ').toUpperCase() + ': ' + String.valueOf(value));
                            System.debug('    └─ Confidence: ' + confDisplay);
                        }
                    }
                }
                
                System.debug('');
                System.debug('════════════════════════════════════════════════════════════');
                System.debug('📈 CONFIDENCE LEGEND:');
                System.debug('   🟢 High (90%+) - Reliable');
                System.debug('   🟡 Medium (70-89%) - Review');
                System.debug('   🔴 Low (<70%) - Verify');
                System.debug('════════════════════════════════════════════════════════════');
            }
        } else {
            System.debug('❌ API Error: ' + res.getBody());
        }
        
    } catch (Exception e) {
        System.debug('❌ Error: ' + e.getMessage());
        System.debug(e.getStackTraceString());
    }
} else {
    // ============================================================
    // Option 2: List available documents to choose from
    // ============================================================
    System.debug('');
    System.debug('📂 AVAILABLE DOCUMENTS IN YOUR ORG:');
    System.debug('════════════════════════════════════════════════════════════');
    
    List<ContentDocument> docs = [
        SELECT Id, Title, FileExtension, CreatedDate 
        FROM ContentDocument 
        ORDER BY CreatedDate DESC 
        LIMIT 10
    ];
    
    for (ContentDocument doc : docs) {
        System.debug('  ID: ' + doc.Id + '  |  Title: ' + doc.Title + '.' + doc.FileExtension);
    }
    
    System.debug('');
    System.debug('👆 Copy one of the IDs above and replace YOUR_CONTENT_DOCUMENT_ID');
    System.debug('   Then run this script again.');
}
