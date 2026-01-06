/**
 * ContactEnrichmentHandler - Handles contact enrichment from document data
 * This class enriches Contact records based on extracted document data
 */
public with sharing class ContactEnrichmentHandler {
    
    /**
     * Enrich a Contact record based on extracted document data - Invocable method for Flows
     */
    @InvocableMethod(label='Enrich Contact from Document' description='Enrich a Contact record based on extracted document data')
    public static List<String> enrichContactFromDocument(List<ContactEnrichmentRequest> requests) {
        List<String> results = new List<String>();
        for (ContactEnrichmentRequest request : requests) {
            results.add(enrichContactFromDocumentInternal(request.contactId, request.extractedDataJson));
        }
        return results;
    }
    
    /**
     * Internal method to enrich a single contact
     */
    public static String enrichContactFromDocumentInternal(Id contactId, String extractedDataJson) {
        if (contactId == null || String.isBlank(extractedDataJson)) {
            throw new ContactEnrichmentException('Contact ID and extracted data cannot be empty.');
        }

        try {
            // Deserialize the extracted data
            Map<String, Object> extractedData = (Map<String, Object>) JSON.deserializeUntyped(extractedDataJson);

            // Retrieve the Contact record
            Contact c = [SELECT Id, FirstName, LastName, Email, Phone, MailingStreet, MailingCity, MailingState, MailingPostalCode, Description FROM Contact WHERE Id = :contactId LIMIT 1];

            if (c == null) {
                throw new ContactEnrichmentException('Contact with ID ' + contactId + ' not found.');
            }

            // Update contact fields based on extracted data
            if (extractedData.containsKey('FirstName') && extractedData.get('FirstName') != null) {
                c.FirstName = String.valueOf(extractedData.get('FirstName'));
            }
            if (extractedData.containsKey('LastName') && extractedData.get('LastName') != null) {
                c.LastName = String.valueOf(extractedData.get('LastName'));
            }
            if (extractedData.containsKey('Email') && extractedData.get('Email') != null) {
                c.Email = String.valueOf(extractedData.get('Email'));
            }
            if (extractedData.containsKey('Phone') && extractedData.get('Phone') != null) {
                c.Phone = String.valueOf(extractedData.get('Phone'));
            }
            if (extractedData.containsKey('Address') && extractedData.get('Address') != null) {
                c.MailingStreet = String.valueOf(extractedData.get('Address'));
            }
            if (extractedData.containsKey('City') && extractedData.get('City') != null) {
                c.MailingCity = String.valueOf(extractedData.get('City'));
            }
            if (extractedData.containsKey('State') && extractedData.get('State') != null) {
                c.MailingState = String.valueOf(extractedData.get('State'));
            }
            if (extractedData.containsKey('PostalCode') && extractedData.get('PostalCode') != null) {
                c.MailingPostalCode = String.valueOf(extractedData.get('PostalCode'));
            }
            if (extractedData.containsKey('Description') && extractedData.get('Description') != null) {
                c.Description = String.valueOf(extractedData.get('Description'));
            }

            update c;

            Map<String, Object> result = new Map<String, Object>();
            result.put('status', 'success');
            result.put('message', 'Contact ' + c.Id + ' enriched successfully.');
            result.put('updatedContact', new Map<String, Object>{
                'Id' => c.Id,
                'FirstName' => c.FirstName,
                'LastName' => c.LastName,
                'Email' => c.Email,
                'Phone' => c.Phone,
                'MailingStreet' => c.MailingStreet,
                'MailingCity' => c.MailingCity,
                'MailingState' => c.MailingState,
                'MailingPostalCode' => c.MailingPostalCode
            });

            return JSON.serializePretty(result);

        } catch (QueryException qe) {
            throw new ContactEnrichmentException('Database error: ' + qe.getMessage());
        } catch (Exception e) {
            throw new ContactEnrichmentException('Error enriching contact: ' + e.getMessage());
        }
    }
    
    /**
     * Process document and enrich contact in one operation
     * @param contactId The ID of the Contact record to enrich
     * @param documentContent The content of the document to process
     * @param schema The JSON schema for data extraction
     * @return A JSON string indicating the status and any updated contact fields
     */
    @AuraEnabled
    public static String processDocumentAndEnrichContact(Id contactId, String documentContent, String schema) {
        try {
            // First, process the document
            String extractedDataJson = DocumentProcessor.processDocumentInternal(documentContent, schema);
            
            // Parse the result to get the extracted data
            Map<String, Object> processResult = (Map<String, Object>) JSON.deserializeUntyped(extractedDataJson);
            Map<String, Object> extractedData = (Map<String, Object>) processResult.get('extractedData');
            
            // Convert to JSON string for enrichment
            String enrichmentDataJson = JSON.serialize(extractedData);
            
            // Now enrich the contact
            return enrichContactFromDocumentInternal(contactId, enrichmentDataJson);
            
        } catch (Exception e) {
            throw new ContactEnrichmentException('Error processing document and enriching contact: ' + e.getMessage());
        }
    }
    
    
    /**
     * Input class for the invocable method
     */
    public class ContactEnrichmentRequest {
        @InvocableVariable(label='Contact ID' description='The ID of the Contact record to enrich' required=true)
        public Id contactId;
        
        @InvocableVariable(label='Extracted Data JSON' description='A JSON string containing data extracted from a document' required=true)
        public String extractedDataJson;
    }
    
    /**
     * Input class for the process and enrich invocable method
     */
    public class ProcessAndEnrichRequest {
        @InvocableVariable(label='Contact ID' description='The ID of the Contact record to enrich' required=true)
        public Id contactId;
        
        @InvocableVariable(label='Document Content' description='The content of the document to process' required=true)
        public String documentContent;
        
        @InvocableVariable(label='Schema' description='The JSON schema for data extraction' required=true)
        public String schema;
    }
}