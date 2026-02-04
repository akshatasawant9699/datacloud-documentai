/**
 * DocumentAIController - Apex controller for LWC components
 * Provides methods to extract document data and display with confidence scores
 */
public with sharing class DocumentAIController {
    
    // INSTANCE_URL is dynamically retrieved from URL.getOrgDomainUrl()
    private static final String DEFAULT_ML_MODEL = 'llmgateway__VertexAIGemini20Flash001';
    
    /**
     * Extract data from a ContentDocument
     * @param contentDocumentId - The ID of the ContentDocument to process
     * @param schemaConfig - Optional custom schema JSON
     * @return ExtractionResponse with extracted data and confidence scores
     */
    @AuraEnabled
    public static ExtractionResponse extractDocumentData(Id contentDocumentId, String schemaConfig) {
        ExtractionResponse response = new ExtractionResponse();
        
        try {
            // Get the document content
            ContentVersion cv = [
                SELECT Id, Title, FileExtension, VersionData, ContentDocumentId 
                FROM ContentVersion 
                WHERE ContentDocumentId = :contentDocumentId 
                AND IsLatest = true 
                LIMIT 1
            ];
            
            // Convert to base64
            String base64Data = EncodingUtil.base64Encode(cv.VersionData);
            String mimeType = getMimeType(cv.FileExtension);
            
            // Use default schema if not provided
            if (String.isBlank(schemaConfig)) {
                schemaConfig = getDefaultSchema();
            }
            
            // Call Document AI - use dynamic org URL
            String instanceUrl = URL.getOrgDomainUrl().toExternalForm();
            String extractedJson = DocumentAIExtractor.callDocumentAIWithSession(
                base64Data, 
                mimeType, 
                schemaConfig, 
                DEFAULT_ML_MODEL,
                instanceUrl
            );
            
            // Parse results
            response.success = true;
            response.documentTitle = cv.Title;
            response.rawJson = extractedJson;
            response.fields = parseFieldsWithConfidence(extractedJson);
            response.documentType = getDocumentType(response.fields);
            
        } catch (Exception e) {
            response.success = false;
            response.errorMessage = e.getMessage();
            System.debug('DocumentAI Error: ' + e.getMessage() + '\n' + e.getStackTraceString());
        }
        
        return response;
    }
    
    /**
     * Get available schemas for different document types
     */
    @AuraEnabled(cacheable=true)
    public static List<SchemaOption> getAvailableSchemas() {
        List<SchemaOption> schemas = new List<SchemaOption>();
        
        schemas.add(new SchemaOption('default', 'Auto-Detect (Sales Order / Invoice)', getDefaultSchema()));
        schemas.add(new SchemaOption('invoice', 'Invoice Only', getInvoiceSchema()));
        schemas.add(new SchemaOption('salesorder', 'Sales Order Only', getSalesOrderSchema()));
        schemas.add(new SchemaOption('healthcare', 'Healthcare Form', getHealthcareSchema()));
        
        return schemas;
    }
    
    /**
     * Parse extracted JSON into field results with confidence scores
     */
    private static List<FieldData> parseFieldsWithConfidence(String jsonData) {
        List<FieldData> fields = new List<FieldData>();
        
        if (String.isBlank(jsonData)) {
            return fields;
        }
        
        try {
            Map<String, Object> dataMap = (Map<String, Object>) JSON.deserializeUntyped(jsonData);
            
            for (String fieldName : dataMap.keySet()) {
                Object fieldValue = dataMap.get(fieldName);
                
                if (fieldValue instanceof Map<String, Object>) {
                    Map<String, Object> fieldData = (Map<String, Object>) fieldValue;
                    
                    FieldData fd = new FieldData();
                    fd.name = fieldName;
                    fd.displayName = formatFieldName(fieldName);
                    fd.fieldType = (String) fieldData.get('type');
                    
                    Object value = fieldData.get('value');
                    if (value != null && String.valueOf(value) != 'null') {
                        if (fd.fieldType == 'array' && value instanceof List<Object>) {
                            fd.value = JSON.serializePretty(value);
                            fd.isArray = true;
                            fd.arrayItems = parseArrayItems((List<Object>) value);
                        } else {
                            fd.value = String.valueOf(value);
                            fd.isArray = false;
                        }
                        fd.hasValue = true;
                    } else {
                        fd.value = '';
                        fd.hasValue = false;
                        fd.isArray = false;
                    }
                    
                    // Get confidence score
                    Object confScore = fieldData.get('confidence_score');
                    if (confScore != null) {
                        fd.confidenceScore = Decimal.valueOf(String.valueOf(confScore));
                        fd.confidencePercent = (fd.confidenceScore * 100).setScale(0);
                        fd.confidenceClass = getConfidenceClass(fd.confidenceScore);
                    }
                    
                    fields.add(fd);
                }
            }
        } catch (Exception e) {
            System.debug('Error parsing JSON: ' + e.getMessage());
        }
        
        // Sort by field name
        fields.sort();
        
        return fields;
    }
    
    /**
     * Parse array items (like line_items)
     */
    private static List<Map<String, String>> parseArrayItems(List<Object> items) {
        List<Map<String, String>> result = new List<Map<String, String>>();
        
        for (Object item : items) {
            if (item instanceof Map<String, Object>) {
                Map<String, Object> itemMap = (Map<String, Object>) item;
                Map<String, String> parsedItem = new Map<String, String>();
                
                if (itemMap.get('value') instanceof Map<String, Object>) {
                    Map<String, Object> valueMap = (Map<String, Object>) itemMap.get('value');
                    for (String key : valueMap.keySet()) {
                        Object val = valueMap.get(key);
                        if (val instanceof Map<String, Object>) {
                            Map<String, Object> fieldVal = (Map<String, Object>) val;
                            parsedItem.put(key, String.valueOf(fieldVal.get('value')));
                        }
                    }
                }
                result.add(parsedItem);
            }
        }
        
        return result;
    }
    
    /**
     * Get confidence CSS class
     */
    private static String getConfidenceClass(Decimal score) {
        if (score >= 0.9) return 'slds-text-color_success';
        if (score >= 0.7) return 'slds-text-color_weak';
        return 'slds-text-color_error';
    }
    
    /**
     * Format field name for display
     */
    private static String formatFieldName(String fieldName) {
        String formatted = fieldName.replace('_', ' ');
        formatted = formatted.substring(0, 1).toUpperCase() + formatted.substring(1);
        return formatted;
    }
    
    /**
     * Get document type from extracted fields
     */
    private static String getDocumentType(List<FieldData> fields) {
        for (FieldData fd : fields) {
            if (fd.name == 'document_type' && fd.hasValue) {
                return fd.value;
            }
        }
        return 'Unknown';
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
    
    // ============ Schema Definitions ============
    
    private static String getDefaultSchema() {
        return '{"type":"object","properties":{"document_type":{"type":"string","description":"Identify: Sales Order, Invoice, Purchase Order, etc."},"document_number":{"type":"string","description":"Primary document identifier"},"document_date":{"type":"string","description":"Document date"},"customer_name":{"type":"string","description":"Customer name"},"customer_address":{"type":"string","description":"Customer address"},"vendor_name":{"type":"string","description":"Vendor/Seller name"},"vendor_address":{"type":"string","description":"Vendor address"},"total_amount":{"type":"number","description":"Total amount"},"currency":{"type":"string","description":"Currency code"},"line_items":{"type":"array","description":"Line items","items":{"type":"object","properties":{"description":{"type":"string"},"quantity":{"type":"number"},"unit_price":{"type":"number"},"line_total":{"type":"number"}}}}}}';
    }
    
    private static String getInvoiceSchema() {
        return '{"type":"object","properties":{"invoice_number":{"type":"string","description":"Invoice number"},"invoice_date":{"type":"string","description":"Invoice date"},"due_date":{"type":"string","description":"Due date"},"customer_name":{"type":"string","description":"Customer name"},"customer_address":{"type":"string","description":"Customer address"},"vendor_name":{"type":"string","description":"Vendor name"},"subtotal":{"type":"number","description":"Subtotal"},"tax_amount":{"type":"number","description":"Tax amount"},"total_amount":{"type":"number","description":"Total amount"},"currency":{"type":"string","description":"Currency"}}}';
    }
    
    private static String getSalesOrderSchema() {
        return '{"type":"object","properties":{"sales_order_number":{"type":"string","description":"Sales Order number"},"order_date":{"type":"string","description":"Order date"},"delivery_date":{"type":"string","description":"Delivery date"},"customer_name":{"type":"string","description":"Customer name"},"payment_terms":{"type":"string","description":"Payment terms"},"delivery_conditions":{"type":"string","description":"Delivery conditions"},"total_amount":{"type":"number","description":"Total amount"},"currency":{"type":"string","description":"Currency"}}}';
    }
    
    private static String getHealthcareSchema() {
        return '{"extractMultiple":true,"type":"object","properties":{"documents":{"type":"array","items":{"type":"object","properties":{"patient_first_name":{"type":"string"},"patient_last_name":{"type":"string"},"patient_dob":{"type":"string"},"facility_name":{"type":"string"},"hcp_name":{"type":"string"},"medication":{"type":"string"},"diagnosis":{"type":"string"}}}}}}';
    }
    
    // ============ Wrapper Classes ============
    
    public class ExtractionResponse {
        @AuraEnabled public Boolean success { get; set; }
        @AuraEnabled public String documentTitle { get; set; }
        @AuraEnabled public String documentType { get; set; }
        @AuraEnabled public String rawJson { get; set; }
        @AuraEnabled public List<FieldData> fields { get; set; }
        @AuraEnabled public String errorMessage { get; set; }
        
        public ExtractionResponse() {
            this.fields = new List<FieldData>();
        }
    }
    
    public class FieldData implements Comparable {
        @AuraEnabled public String name { get; set; }
        @AuraEnabled public String displayName { get; set; }
        @AuraEnabled public String fieldType { get; set; }
        @AuraEnabled public String value { get; set; }
        @AuraEnabled public Boolean hasValue { get; set; }
        @AuraEnabled public Boolean isArray { get; set; }
        @AuraEnabled public Decimal confidenceScore { get; set; }
        @AuraEnabled public Decimal confidencePercent { get; set; }
        @AuraEnabled public String confidenceClass { get; set; }
        @AuraEnabled public List<Map<String, String>> arrayItems { get; set; }
        
        public Integer compareTo(Object compareTo) {
            FieldData other = (FieldData) compareTo;
            return this.name.compareTo(other.name);
        }
    }
    
    public class SchemaOption {
        @AuraEnabled public String value { get; set; }
        @AuraEnabled public String label { get; set; }
        @AuraEnabled public String schema { get; set; }
        
        public SchemaOption(String value, String label, String schema) {
            this.value = value;
            this.label = label;
            this.schema = schema;
        }
    }
}
