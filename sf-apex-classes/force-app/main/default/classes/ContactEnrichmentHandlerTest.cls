/**
 * Test class for ContactEnrichmentHandler
 */
@isTest
private class ContactEnrichmentHandlerTest {
    
    @isTest
    static void testEnrichContactFromDocument_Success() {
        // Create a test contact
        Contact testContact = new Contact(FirstName = 'John', LastName = 'Doe', Email = 'john.doe@example.com');
        insert testContact;

        // Sample extracted data
        String extractedDataJson = '{"FirstName": "Jane", "LastName": "Smith", "Email": "jane.smith@example.com", "Phone": "555-123-4567", "Address": "123 Main St, Anytown, USA"}';
        
        ContactEnrichmentHandler.ContactEnrichmentRequest request = new ContactEnrichmentHandler.ContactEnrichmentRequest();
        request.contactId = testContact.Id;
        request.extractedDataJson = extractedDataJson;
        List<ContactEnrichmentHandler.ContactEnrichmentRequest> requests = new List<ContactEnrichmentHandler.ContactEnrichmentRequest>{request};

        Test.startTest();
        List<String> results = ContactEnrichmentHandler.enrichContactFromDocument(requests);
        Test.stopTest();

        // Verify the contact was updated
        Contact updatedContact = [SELECT Id, FirstName, LastName, Email, Phone, MailingStreet FROM Contact WHERE Id = :testContact.Id];

        System.assert(results != null && !results.isEmpty(), 'Result should not be null or empty');
        System.assert(results[0].contains('success'), 'Result should indicate success');
        System.assertEquals('Jane', updatedContact.FirstName, 'First name should be updated');
        System.assertEquals('Smith', updatedContact.LastName, 'Last name should be updated');
        System.assertEquals('jane.smith@example.com', updatedContact.Email, 'Email should be updated');
        System.assertEquals('555-123-4567', updatedContact.Phone, 'Phone should be updated');
        System.assertEquals('123 Main St, Anytown, USA', updatedContact.MailingStreet, 'Address should be updated');
    }

    @isTest
    static void testEnrichContactFromDocument_InvalidContactId() {
        String extractedDataJson = '{"FirstName": "Jane"}';
        
        ContactEnrichmentHandler.ContactEnrichmentRequest request = new ContactEnrichmentHandler.ContactEnrichmentRequest();
        request.contactId = null;
        request.extractedDataJson = extractedDataJson;
        List<ContactEnrichmentHandler.ContactEnrichmentRequest> requests = new List<ContactEnrichmentHandler.ContactEnrichmentRequest>{request};

        Test.startTest();
        List<String> results = ContactEnrichmentHandler.enrichContactFromDocument(requests);
        Test.stopTest();

        System.assert(results != null && !results.isEmpty(), 'Result should not be null or empty');
        System.assert(results[0].contains('error'), 'Result should indicate error');
        System.assert(results[0].contains('Contact ID and extracted data cannot be empty.'), 'Incorrect exception message');
    }

    @isTest
    static void testEnrichContactFromDocument_EmptyExtractedData() {
        Contact testContact = new Contact(FirstName = 'John', LastName = 'Doe');
        insert testContact;

        ContactEnrichmentHandler.ContactEnrichmentRequest request = new ContactEnrichmentHandler.ContactEnrichmentRequest();
        request.contactId = testContact.Id;
        request.extractedDataJson = '';
        List<ContactEnrichmentHandler.ContactEnrichmentRequest> requests = new List<ContactEnrichmentHandler.ContactEnrichmentRequest>{request};

        Test.startTest();
        List<String> results = ContactEnrichmentHandler.enrichContactFromDocument(requests);
        Test.stopTest();

        System.assert(results != null && !results.isEmpty(), 'Result should not be null or empty');
        System.assert(results[0].contains('error'), 'Result should indicate error');
        System.assert(results[0].contains('Contact ID and extracted data cannot be empty.'), 'Incorrect exception message');
    }

    @isTest
    static void testProcessDocumentAndEnrichContact_Success() {
        // Create a test contact
        Contact testContact = new Contact(FirstName = 'John', LastName = 'Doe');
        insert testContact;

        String documentContent = 'Sample resume content';
        String schema = '{"properties": {"Name": {"type": "string"}}}';

        Test.startTest();
        String result = ContactEnrichmentHandler.processDocumentAndEnrichContact(testContact.Id, documentContent, schema);
        Test.stopTest();

        System.assert(result != null, 'Result should not be null');
        System.assert(result.contains('success'), 'Result should indicate success');
    }
}