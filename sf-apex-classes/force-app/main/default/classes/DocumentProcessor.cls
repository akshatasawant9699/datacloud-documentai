/**
 * DocumentProcessor - Handles document processing using Document AI
 * This class processes documents and extracts structured data
 */
public with sharing class DocumentProcessor {
    
    /**
     * Process a document using Document AI - Invocable method for Flows
     * @param documentContent The content of the document to process
     * @param schema The JSON schema for data extraction
     * @return JSON string containing extracted data
     */
    @InvocableMethod(label='Process Document' description='Process a document using Document AI')
    public static List<String> processDocument(List<DocumentRequest> requests) {
        List<String> results = new List<String>();
        for (DocumentRequest request : requests) {
            results.add(processDocumentInternal(request.documentContent, request.schema));
        }
        return results;
    }
    
    /**
     * Internal method to process a single document
     */
    public static String processDocumentInternal(String documentContent, String schema) {
        try {
            // Validate input parameters
            if (String.isBlank(documentContent) || String.isBlank(schema)) {
                throw new DocumentProcessingException('Document content or schema cannot be empty.');
            }
            
            // In a real scenario, this would involve calling an external AI service
            // or complex parsing logic based on the schema.
            System.debug('Processing document with content length: ' + documentContent.length());
            System.debug('Using schema: ' + schema);
            
            // For demonstration, return a structured JSON response
            Map<String, Object> result = new Map<String, Object>();
            result.put('status', 'success');
            result.put('extractedData', new Map<String, String>{
                'Name' => 'Sample Resume Name',
                'Email' => 'sample.email@example.com',
                'Phone' => '123-456-7890',
                'Experience' => '5 years',
                'Skills' => 'Apex, Lightning, Integration',
                'Address' => '123 Main St, Anytown, USA'
            });
            
            return JSON.serializePretty(result);
            
        } catch (Exception e) {
            System.debug('Error processing document: ' + e.getMessage());
            throw new DocumentProcessingException('Error processing document: ' + e.getMessage());
        }
    }
    
    /**
     * Extract document details using Document AI
     * @param documentId The ID of the document to process
     * @param schemaConfig JSON schema configuration for data extraction
     * @return Map containing extracted document details
     */
    @AuraEnabled
    public static Map<String, Object> extractDocumentDetails(Id documentId, String schemaConfig) {
        try {
            // Validate input parameters
            if (documentId == null) {
                throw new IllegalArgumentException('Document ID cannot be null');
            }
            
            if (String.isBlank(schemaConfig)) {
                throw new IllegalArgumentException('Schema configuration cannot be empty');
            }

            // In a real scenario, this would involve calling an external Document AI service
            // or using Salesforce's native Document AI capabilities.
            System.debug('Processing document with ID: ' + documentId);
            System.debug('Using schema configuration: ' + schemaConfig);

            // For demonstration purposes, return dummy extracted data
            Map<String, Object> extractedData = new Map<String, Object>();
            extractedData.put('status', 'success');
            extractedData.put('documentId', documentId);
            extractedData.put('extractedFields', new Map<String, String>{
                'Name' => 'Sample Resume Name',
                'Email' => 'sample.email@example.com',
                'Phone' => '123-456-7890',
                'Experience' => '5 years',
                'Skills' => 'Apex, Lightning, Integration'
            });
            
            return extractedData;

        } catch (Exception e) {
            System.debug('Error extracting document details: ' + e.getMessage());
            throw new AuraHandledException('Error extracting document details: ' + e.getMessage());
        }
    }
    
    /**
     * Input class for the invocable method
     */
    public class DocumentRequest {
        @InvocableVariable(label='Document Content' description='The content of the document to process' required=true)
        public String documentContent;
        
        @InvocableVariable(label='Schema' description='The JSON schema for data extraction' required=true)
        public String schema;
    }
}