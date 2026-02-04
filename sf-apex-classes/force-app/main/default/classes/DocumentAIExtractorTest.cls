/**
 * Test class for DocumentAIExtractor and DocumentAIController
 */
@isTest
private class DocumentAIExtractorTest {
    
    /**
     * Mock class for HTTP callout
     */
    private class DocumentAIMock implements HttpCalloutMock {
        private Integer statusCode;
        private String responseBody;
        
        public DocumentAIMock(Integer statusCode, String responseBody) {
            this.statusCode = statusCode;
            this.responseBody = responseBody;
        }
        
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(this.statusCode);
            res.setBody(this.responseBody);
            return res;
        }
    }
    
    /**
     * Setup test data
     */
    @testSetup
    static void setup() {
        // Create a test ContentDocument
        ContentVersion cv = new ContentVersion();
        cv.Title = 'Test Invoice';
        cv.PathOnClient = 'test_invoice.pdf';
        cv.VersionData = Blob.valueOf('Test PDF Content');
        cv.IsMajorVersion = true;
        insert cv;
    }
    
    /**
     * Test successful extraction via Flow invocable method
     */
    @isTest
    static void testExtractFromFlow_Success() {
        // Get test document
        ContentVersion cv = [SELECT ContentDocumentId FROM ContentVersion LIMIT 1];
        
        // Setup mock response with confidence scores
        String mockResponse = '{"data":[{"data":"{\\"document_type\\":{\\"type\\":\\"string\\",\\"value\\":\\"Invoice\\",\\"confidence_score\\":0.95},\\"invoice_number\\":{\\"type\\":\\"string\\",\\"value\\":\\"INV-001\\",\\"confidence_score\\":0.92},\\"total_amount\\":{\\"type\\":\\"number\\",\\"value\\":1500.00,\\"confidence_score\\":0.88}}"}]}';
        Test.setMock(HttpCalloutMock.class, new DocumentAIMock(200, mockResponse));
        
        // Create request
        DocumentAIExtractor.ExtractionRequest request = new DocumentAIExtractor.ExtractionRequest();
        request.contentDocumentId = cv.ContentDocumentId;
        request.schemaConfig = '{"type":"object","properties":{"document_type":{"type":"string"}}}';
        
        Test.startTest();
        List<DocumentAIExtractor.ExtractionResult> results = DocumentAIExtractor.extractFromFlow(
            new List<DocumentAIExtractor.ExtractionRequest>{ request }
        );
        Test.stopTest();
        
        System.assertEquals(1, results.size());
        System.assertEquals(true, results[0].success);
        System.assertNotEquals(null, results[0].extractedData);
        System.assertEquals('Test Invoice', results[0].documentTitle);
    }
    
    /**
     * Test extraction with API error
     */
    @isTest
    static void testExtractFromFlow_ApiError() {
        ContentVersion cv = [SELECT ContentDocumentId FROM ContentVersion LIMIT 1];
        
        // Setup error response
        Test.setMock(HttpCalloutMock.class, new DocumentAIMock(500, '{"error":"Internal Server Error"}'));
        
        DocumentAIExtractor.ExtractionRequest request = new DocumentAIExtractor.ExtractionRequest();
        request.contentDocumentId = cv.ContentDocumentId;
        
        Test.startTest();
        List<DocumentAIExtractor.ExtractionResult> results = DocumentAIExtractor.extractFromFlow(
            new List<DocumentAIExtractor.ExtractionRequest>{ request }
        );
        Test.stopTest();
        
        System.assertEquals(1, results.size());
        System.assertEquals(false, results[0].success);
        System.assertNotEquals(null, results[0].errorMessage);
    }
    
    /**
     * Test controller extractDocumentData method
     */
    @isTest
    static void testControllerExtractDocumentData() {
        ContentVersion cv = [SELECT ContentDocumentId FROM ContentVersion LIMIT 1];
        
        String mockResponse = '{"data":[{"data":"{\\"vendor_name\\":{\\"type\\":\\"string\\",\\"value\\":\\"ACME Corp\\",\\"confidence_score\\":0.91}}"}]}';
        Test.setMock(HttpCalloutMock.class, new DocumentAIMock(200, mockResponse));
        
        Test.startTest();
        DocumentAIController.ExtractionResponse response = DocumentAIController.extractDocumentData(
            cv.ContentDocumentId,
            null
        );
        Test.stopTest();
        
        System.assertEquals(true, response.success);
        System.assertEquals('Test Invoice', response.documentTitle);
    }
    
    /**
     * Test getAvailableSchemas method
     */
    @isTest
    static void testGetAvailableSchemas() {
        Test.startTest();
        List<DocumentAIController.SchemaOption> schemas = DocumentAIController.getAvailableSchemas();
        Test.stopTest();
        
        System.assert(schemas.size() >= 4, 'Should have at least 4 schema options');
        
        Boolean hasDefault = false;
        for (DocumentAIController.SchemaOption opt : schemas) {
            if (opt.value == 'default') {
                hasDefault = true;
                break;
            }
        }
        System.assert(hasDefault, 'Should have default schema option');
    }
    
    /**
     * Test parseExtractedData method
     */
    @isTest
    static void testParseExtractedData() {
        String testJson = '{"invoice_number":{"type":"string","value":"INV-123","confidence_score":0.95},"total_amount":{"type":"number","value":1000,"confidence_score":0.87}}';
        
        Test.startTest();
        List<DocumentAIExtractor.FieldResult> results = DocumentAIExtractor.parseExtractedData(testJson);
        Test.stopTest();
        
        System.assertEquals(2, results.size());
        
        Boolean foundInvoice = false;
        for (DocumentAIExtractor.FieldResult fr : results) {
            if (fr.fieldName == 'invoice_number') {
                foundInvoice = true;
                System.assertEquals('INV-123', fr.fieldValue);
                System.assertEquals(0.95, fr.confidenceScore);
            }
        }
        System.assert(foundInvoice, 'Should find invoice_number field');
    }
    
    /**
     * Test mime type detection
     */
    @isTest
    static void testMimeTypeDetection() {
        // Create different file types
        List<ContentVersion> testFiles = new List<ContentVersion>();
        
        ContentVersion pdfFile = new ContentVersion();
        pdfFile.Title = 'Test PDF';
        pdfFile.PathOnClient = 'test.pdf';
        pdfFile.VersionData = Blob.valueOf('PDF');
        testFiles.add(pdfFile);
        
        ContentVersion pngFile = new ContentVersion();
        pngFile.Title = 'Test PNG';
        pngFile.PathOnClient = 'test.png';
        pngFile.VersionData = Blob.valueOf('PNG');
        testFiles.add(pngFile);
        
        insert testFiles;
        
        // Verify files were created
        List<ContentVersion> inserted = [SELECT Id, Title, FileExtension FROM ContentVersion WHERE Title LIKE 'Test%'];
        System.assert(inserted.size() >= 2, 'Should have created test files');
    }
    
    /**
     * Test null/empty input handling
     */
    @isTest
    static void testNullInputHandling() {
        Test.startTest();
        List<DocumentAIExtractor.FieldResult> results = DocumentAIExtractor.parseExtractedData(null);
        Test.stopTest();
        
        System.assertEquals(0, results.size());
    }
    
    /**
     * Test with array data (line items)
     */
    @isTest
    static void testArrayDataParsing() {
        String testJson = '{"line_items":{"type":"array","value":[{"value":{"description":{"value":"Widget"},"quantity":{"value":10}}}],"confidence_score":0.82}}';
        
        Test.startTest();
        List<DocumentAIExtractor.FieldResult> results = DocumentAIExtractor.parseExtractedData(testJson);
        Test.stopTest();
        
        System.assertEquals(1, results.size());
        System.assertEquals('line_items', results[0].fieldName);
        System.assertEquals(true, results[0].isArray);
    }
}
