/**
 * Test class for DocumentProcessor
 */
@isTest
private class DocumentProcessorTest {
    
    @isTest
    static void testProcessDocument_Success() {
        String testContent = 'This is a sample document content.';
        String testSchema = '{"properties": {"Name": {"type": "string"}}}';

        Test.startTest();
        List<DocumentProcessor.DocumentRequest> requests = new List<DocumentProcessor.DocumentRequest>();
        DocumentProcessor.DocumentRequest request = new DocumentProcessor.DocumentRequest();
        request.documentContent = testContent;
        request.schema = testSchema;
        requests.add(request);
        List<String> results = DocumentProcessor.processDocument(requests);
        String result = results[0];
        Test.stopTest();

        System.assert(result != null, 'Result should not be null');
        System.assert(result.contains('success'), 'Result should indicate success');
        System.assert(result.contains('Sample Resume Name'), 'Result should contain extracted data');
    }

    @isTest
    static void testProcessDocument_EmptyContent() {
        String testContent = '';
        String testSchema = '{"properties": {"Name": {"type": "string"}}}';

        Test.startTest();
        Boolean caughtException = false;
        try {
            List<DocumentProcessor.DocumentRequest> requests = new List<DocumentProcessor.DocumentRequest>();
            DocumentProcessor.DocumentRequest request = new DocumentProcessor.DocumentRequest();
            request.documentContent = testContent;
            request.schema = testSchema;
            requests.add(request);
            DocumentProcessor.processDocument(requests);
        } catch (DocumentProcessingException e) {
            caughtException = true;
            System.assertEquals('Document content or schema cannot be empty.', e.getMessage(), 'Incorrect exception message');
        }
        Test.stopTest();

        System.assert(caughtException, 'DocumentProcessingException should have been caught');
    }

    @isTest
    static void testExtractDocumentDetails_Success() {
        // Get test contact
        Contact testContact = new Contact(FirstName = 'John', LastName = 'Doe', Email = 'john.doe@test.com');
        insert testContact;
        
        Id mockDocumentId = testContact.Id; // Using Contact ID as a placeholder for ContentDocument ID
        String schemaConfig = '{"fields": ["Name", "Email", "Phone"]}';

        Test.startTest();
        Map<String, Object> result = DocumentProcessor.extractDocumentDetails(mockDocumentId, schemaConfig);
        Test.stopTest();

        System.assert(result != null, 'Result should not be null');
        System.assertEquals('success', result.get('status'), 'Status should be success');
        System.assert(result.containsKey('extractedFields'), 'Extracted fields should be present');
    }

    @isTest
    static void testExtractDocumentDetails_NullDocumentId() {
        String schemaConfig = '{"fields": ["Name"]}';
        Test.startTest();
        Boolean caughtException = false;
        try {
            DocumentProcessor.extractDocumentDetails(null, schemaConfig);
        } catch (IllegalArgumentException e) {
            caughtException = true;
            System.assertEquals('Document ID cannot be null', e.getMessage(), 'Incorrect exception message');
        }
        Test.stopTest();
        System.assert(caughtException, 'IllegalArgumentException should have been caught for null document ID');
    }
}