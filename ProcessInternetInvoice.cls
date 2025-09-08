public class ProcessInternetInvoice {
    
    // Configuration constants - same as DocumentAIResumeProcessorSimple
    private static final String DOCUMENT_AI_ENDPOINT = '<salesforce_instance_url>/services/data/v64.0/ssot/document-processing/actions/extract-data?htmlEncode=false';
    private static final String CONTENT_TYPE = 'application/json';
    
    // OAuth 2.0 credentials for authentication
    private static final String LOGIN_URL = 'https://akshatasaw-250204-730-demo.my.salesforce.com';
    private static final String CLIENT_ID = '<client_id>';
    private static final String CLIENT_SECRET = '<client_secret>';
    
    // IDP Configuration ID or Name for Document AI processing
    private static final String IDP_CONFIGURATION_ID_OR_NAME = 'Internet_Invoice';
    
    // Request wrapper class for invocable methods
    public class InternetInvoiceRequest {
        @InvocableVariable
        public String contentDocumentId;
        
        @InvocableVariable
        public String sessionId;
    }
    
    // Response wrapper class for invocable methods
    public class InternetInvoiceResponse {
        @InvocableVariable
        public Boolean success;
        
        @InvocableVariable
        public String errorMessage;
        
        @InvocableVariable
        public String extractedDataJson;
        
        @InvocableVariable
        public String rawResponse;
        
        // Individual fields for easy access - Internet Invoice specific fields
        @InvocableVariable
        public String invoiceNumber;
        
        @InvocableVariable
        public String amountDue;
        
        @InvocableVariable
        public String dueDate;
        
        @InvocableVariable
        public String serviceProvider;
        
        @InvocableVariable
        public String accountNumber;
        
        @InvocableVariable
        public String billingPeriod;
        
        @InvocableVariable
        public String paymentMethod;
        
        @InvocableVariable
        public String customerName;
        
        @InvocableVariable
        public String customerAddress;
    }
    
    /**
     * Main invocable method to process internet invoice using Document AI
     * @param requests List of InternetInvoiceRequest objects
     * @return List of InternetInvoiceResponse objects
     */
    @InvocableMethod(label='Process Internet Invoice using Document AI')
    public static List<InternetInvoiceResponse> processInternetInvoice(List<InternetInvoiceRequest> requests) {
        List<InternetInvoiceResponse> responses = new List<InternetInvoiceResponse>();
        
        System.debug('ProcessInternetInvoice: Starting processing for ' + requests.size() + ' requests');
        
        for (Integer i = 0; i < requests.size(); i++) {
            InternetInvoiceRequest request = requests[i];
            InternetInvoiceResponse response = new InternetInvoiceResponse();
            
            System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Processing ContentDocument ID: ' + request.contentDocumentId);
            
            try {
                // Step 1: Get the file content from Salesforce
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Step 1 - Retrieving file content...');
                String base64Content = getFileContent(request.contentDocumentId, request.sessionId);
                if (base64Content == null) {
                    System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: ERROR - Failed to retrieve file content');
                    response.success = false;
                    response.errorMessage = 'Failed to retrieve file content from Salesforce';
                    responses.add(response);
                    continue;
                }
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: SUCCESS - File content retrieved, base64 length: ' + base64Content.length());
                
                // Step 2: Create the request body for Internet Invoice processing
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Step 2 - Preparing API request...');
                String requestBodyJson = createInternetInvoiceRequestBody(base64Content);
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Request body prepared, size: ' + requestBodyJson.length() + ' chars');
                
                // Step 3: Make the API call
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Step 3 - Making API call...');
                String apiResponse = makeAPICall(requestBodyJson, request.sessionId);
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: API response received, size: ' + apiResponse.length() + ' chars');
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Raw API response: ' + apiResponse);
                
                // Step 4: Parse the response
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Step 4 - Parsing API response...');
                Map<String, Object> responseMap = (Map<String, Object>) JSON.deserializeUntyped(apiResponse);
                List<Object> dataList = (List<Object>) responseMap.get('data');
                
                if (dataList != null && !dataList.isEmpty()) {
                    Map<String, Object> firstData = (Map<String, Object>) dataList[0];
                    String extractedDataStr = (String) firstData.get('data');
                    String error = (String) firstData.get('error');
                    
                    System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Extracted data string: ' + extractedDataStr);
                    System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Error field: ' + error);
                    
                    if (error == null && extractedDataStr != null && extractedDataStr != '{}') {
                        System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Processing extracted data...');
                        
                        // Decode HTML entities and parse the extracted data
                        String decodedData = decodeHtmlEntities(extractedDataStr);
                        System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Decoded data: ' + decodedData);
                        
                        Map<String, Object> extractedDataMap = (Map<String, Object>) JSON.deserializeUntyped(decodedData);
                        System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Parsed data map: ' + extractedDataMap);
                        
                        // Format the extracted data and populate individual fields
                        Map<String, Object> formattedData = formatExtractedData(extractedDataMap);
                        System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Formatted data: ' + formattedData);
                        
                        response.success = true;
                        response.extractedDataJson = JSON.serialize(formattedData);
                        response.rawResponse = apiResponse;
                        
                        // Populate individual fields for Flow access
                        populateIndividualFields(response, formattedData);
                        
                        // Store extracted values in debug variables for easy access
                        logExtractedValues(response, i+1);
                        
                        System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: SUCCESS - Data extracted successfully');
                        
                    } else {
                        System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: ERROR - No data extracted or error occurred');
                        response.success = false;
                        response.errorMessage = 'No data extracted from internet invoice. Error: ' + error;
                        response.rawResponse = apiResponse;
                    }
                } else {
                    System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: ERROR - Invalid response format - no data array');
                    response.success = false;
                    response.errorMessage = 'Invalid response format from Document AI API';
                    response.rawResponse = apiResponse;
                }
                
            } catch (Exception e) {
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: EXCEPTION - ' + e.getMessage());
                System.debug('ProcessInternetInvoice [Request ' + (i+1) + ']: Stack trace: ' + e.getStackTraceString());
                response.success = false;
                response.errorMessage = 'Exception occurred: ' + e.getMessage();
                response.rawResponse = e.getStackTraceString();
            }
            
            responses.add(response);
        }
        
        System.debug('ProcessInternetInvoice: Completed processing all requests');
        return responses;
    }
    
    /**
     * Create the request body for Internet Invoice processing
     */
    private static String createInternetInvoiceRequestBody(String base64Content) {
        String requestBodyJson = '{\n' +
            '  "idpConfigurationIdOrName": "' + IDP_CONFIGURATION_ID_OR_NAME + '",\n' +
            '  "files": [\n' +
            '    {\n' +
            '      "mimeType": "application/pdf",\n' +
            '      "data": "' + base64Content + '"\n' +
            '    }\n' +
            '  ]\n' +
            '}';
        
        return requestBodyJson;
    }
    
    /**
     * Get file content from Salesforce using the ContentDocument ID
     */
    private static String getFileContent(String contentDocumentId, String sessionId) {
        try {
            System.debug('getFileContent: Starting file retrieval for ContentDocument ID: ' + contentDocumentId);
            
            // Query the ContentVersion to get the file content
            System.debug('getFileContent: Querying ContentVersion for latest file...');
            List<ContentVersion> cvList = [SELECT VersionData, FileType, Title, ContentSize 
                                         FROM ContentVersion 
                                         WHERE ContentDocumentId = :contentDocumentId 
                                         AND IsLatest = true 
                                         LIMIT 1];
            
            if (cvList.isEmpty()) {
                System.debug('getFileContent: ERROR - No ContentVersion found for ContentDocument ID: ' + contentDocumentId);
                return null;
            }
            
            ContentVersion cv = cvList[0];
            System.debug('getFileContent: Found file - Title: ' + cv.Title + ', Type: ' + cv.FileType + ', Size: ' + cv.ContentSize + ' bytes');
            
            // Convert BLOB to base64 directly
            System.debug('getFileContent: Converting BLOB to base64...');
            String base64Data = EncodingUtil.base64Encode(cv.VersionData);
            System.debug('getFileContent: SUCCESS - Converted to base64, length: ' + base64Data.length() + ' characters');
            
            return base64Data;
            
        } catch (Exception e) {
            System.debug('getFileContent: EXCEPTION - ' + e.getMessage());
            System.debug('getFileContent: Stack trace: ' + e.getStackTraceString());
            return null;
        }
    }
    
    /**
     * Make API call to Document AI service
     */
    private static String makeAPICall(String requestBody, String sessionId) {
        System.debug('makeAPICall: Preparing HTTP request...');
        System.debug('makeAPICall: Endpoint: ' + DOCUMENT_AI_ENDPOINT);
        System.debug('makeAPICall: Session ID length: ' + (sessionId != null ? sessionId.length() : 0) + ' characters');
        
        Http http = new Http();
        HttpRequest request = new HttpRequest();
        
        request.setEndpoint(DOCUMENT_AI_ENDPOINT);
        request.setMethod('POST');
        request.setHeader('Content-Type', CONTENT_TYPE);
        request.setHeader('Authorization', 'Bearer ' + sessionId);
        request.setBody(requestBody);
        
        System.debug('makeAPICall: Sending HTTP request...');
        HttpResponse response = http.send(request);
        
        System.debug('makeAPICall: Response received - Status: ' + response.getStatusCode());
        System.debug('makeAPICall: Response body length: ' + response.getBody().length() + ' characters');
        
        return response.getBody();
    }
    
    /**
     * Decode HTML entities in the response
     */
    private static String decodeHtmlEntities(String input) {
        if (input == null) return null;
        
        // Common HTML entity replacements
        input = input.replace('&quot;', '"');
        input = input.replace('&apos;', '\'');
        input = input.replace('&lt;', '<');
        input = input.replace('&gt;', '>');
        input = input.replace('&amp;', '&');
        input = input.replace('&#39;', '\'');
        input = input.replace('&nbsp;', ' ');
        
        return input;
    }
    
    /**
     * Format the extracted data for better readability
     */
    private static Map<String, Object> formatExtractedData(Map<String, Object> extractedData) {
        Map<String, Object> formattedData = new Map<String, Object>();
        
        for (String key : extractedData.keySet()) {
            Object value = extractedData.get(key);
            if (value instanceof Map<String, Object>) {
                Map<String, Object> valueMap = (Map<String, Object>) value;
                if (valueMap.containsKey('value')) {
                    formattedData.put(key, valueMap.get('value'));
                } else {
                    formattedData.put(key, value);
                }
            } else {
                formattedData.put(key, value);
            }
        }
        
        return formattedData;
    }
    
    /**
     * Populate individual fields for easy Flow access
     */
    private static void populateIndividualFields(InternetInvoiceResponse response, Map<String, Object> formattedData) {
        if (formattedData.containsKey('InvoiceNumber')) {
            response.invoiceNumber = (String) formattedData.get('InvoiceNumber');
        }
        if (formattedData.containsKey('AmountDue')) {
            response.amountDue = (String) formattedData.get('AmountDue');
        }
        if (formattedData.containsKey('DueDate')) {
            response.dueDate = (String) formattedData.get('DueDate');
        }
        if (formattedData.containsKey('ServiceProvider')) {
            response.serviceProvider = (String) formattedData.get('ServiceProvider');
        }
        if (formattedData.containsKey('AccountNumber')) {
            response.accountNumber = (String) formattedData.get('AccountNumber');
        }
        if (formattedData.containsKey('BillingPeriod')) {
            response.billingPeriod = (String) formattedData.get('BillingPeriod');
        }
        if (formattedData.containsKey('PaymentMethod')) {
            response.paymentMethod = (String) formattedData.get('PaymentMethod');
        }
        if (formattedData.containsKey('CustomerName')) {
            response.customerName = (String) formattedData.get('CustomerName');
        }
        if (formattedData.containsKey('CustomerAddress')) {
            response.customerAddress = (String) formattedData.get('CustomerAddress');
        }
    }
    
    /**
     * Log extracted values as individual variables for easy access
     */
    private static void logExtractedValues(InternetInvoiceResponse response, Integer requestNumber) {
        System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: ===== EXTRACTED VALUES =====');
        
        // Internet Invoice fields
        if (response.invoiceNumber != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Invoice Number = ' + response.invoiceNumber);
        }
        if (response.amountDue != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Amount Due = ' + response.amountDue);
        }
        if (response.dueDate != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Due Date = ' + response.dueDate);
        }
        if (response.serviceProvider != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Service Provider = ' + response.serviceProvider);
        }
        if (response.accountNumber != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Account Number = ' + response.accountNumber);
        }
        if (response.billingPeriod != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Billing Period = ' + response.billingPeriod);
        }
        if (response.paymentMethod != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Payment Method = ' + response.paymentMethod);
        }
        if (response.customerName != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Customer Name = ' + response.customerName);
        }
        if (response.customerAddress != null) {
            System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: Customer Address = ' + response.customerAddress);
        }
        
        System.debug('ProcessInternetInvoice [Request ' + requestNumber + ']: ============================');
    }
}
