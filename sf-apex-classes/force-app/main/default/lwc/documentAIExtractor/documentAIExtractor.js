import { LightningElement, api, track, wire } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import extractDocumentData from '@salesforce/apex/DocumentAIController.extractDocumentData';
import getAvailableSchemas from '@salesforce/apex/DocumentAIController.getAvailableSchemas';

export default class DocumentAIExtractor extends LightningElement {
    @api recordId;
    
    @track isLoading = false;
    @track errorMessage = '';
    @track uploadedDocumentId = null;
    @track extractedFields = [];
    @track documentTitle = '';
    @track documentType = '';
    @track rawJson = '';
    @track showRawJson = false;
    @track schemaOptions = [];
    @track selectedSchema = 'default';
    @track selectedSchemaConfig = '';
    
    acceptedFormats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'];
    
    connectedCallback() {
        this.loadSchemaOptions();
    }
    
    loadSchemaOptions() {
        getAvailableSchemas()
            .then(result => {
                this.schemaOptions = result.map(schema => ({
                    label: schema.label,
                    value: schema.value,
                    schema: schema.schema
                }));
                // Set default schema config
                const defaultOption = this.schemaOptions.find(opt => opt.value === 'default');
                if (defaultOption) {
                    this.selectedSchemaConfig = defaultOption.schema;
                }
            })
            .catch(error => {
                console.error('Error loading schemas:', error);
            });
    }
    
    get isExtractDisabled() {
        return !this.uploadedDocumentId || this.isLoading;
    }
    
    get hasResults() {
        return this.extractedFields.length > 0;
    }
    
    get totalFields() {
        return this.extractedFields.length;
    }
    
    get fieldsWithValues() {
        return this.extractedFields.filter(f => f.hasValue).length;
    }
    
    get rawJsonButtonLabel() {
        return this.showRawJson ? 'Hide Raw JSON' : 'Show Raw JSON';
    }
    
    get formattedRawJson() {
        try {
            return JSON.stringify(JSON.parse(this.rawJson), null, 2);
        } catch (e) {
            return this.rawJson;
        }
    }
    
    handleUploadFinished(event) {
        const uploadedFiles = event.detail.files;
        if (uploadedFiles.length > 0) {
            this.uploadedDocumentId = uploadedFiles[0].documentId;
            this.showToast('Success', 'File uploaded successfully', 'success');
        }
    }
    
    handleSchemaChange(event) {
        this.selectedSchema = event.detail.value;
        const selectedOption = this.schemaOptions.find(opt => opt.value === this.selectedSchema);
        if (selectedOption) {
            this.selectedSchemaConfig = selectedOption.schema;
        }
    }
    
    handleExtract() {
        if (!this.uploadedDocumentId) {
            this.showToast('Error', 'Please upload a document first', 'error');
            return;
        }
        
        this.isLoading = true;
        this.errorMessage = '';
        this.extractedFields = [];
        
        extractDocumentData({ 
            contentDocumentId: this.uploadedDocumentId,
            schemaConfig: this.selectedSchemaConfig
        })
            .then(result => {
                this.isLoading = false;
                
                if (result.success) {
                    this.documentTitle = result.documentTitle;
                    this.documentType = result.documentType || 'Unknown';
                    this.rawJson = result.rawJson;
                    
                    // Process fields with confidence styling
                    this.extractedFields = result.fields.map(field => ({
                        ...field,
                        variant: this.getProgressRingVariant(field.confidenceScore)
                    }));
                    
                    this.showToast('Success', `Extracted ${this.fieldsWithValues} fields from document`, 'success');
                } else {
                    this.errorMessage = result.errorMessage;
                    this.showToast('Error', result.errorMessage, 'error');
                }
            })
            .catch(error => {
                this.isLoading = false;
                this.errorMessage = error.body ? error.body.message : error.message;
                this.showToast('Error', this.errorMessage, 'error');
            });
    }
    
    handleClear() {
        this.uploadedDocumentId = null;
        this.extractedFields = [];
        this.documentTitle = '';
        this.documentType = '';
        this.rawJson = '';
        this.showRawJson = false;
        this.errorMessage = '';
    }
    
    toggleRawJson() {
        this.showRawJson = !this.showRawJson;
    }
    
    handleViewArray(event) {
        const fieldName = event.target.dataset.field;
        const field = this.extractedFields.find(f => f.name === fieldName);
        if (field && field.value) {
            // Show modal or expanded view
            alert('Line Items:\n' + field.value);
        }
    }
    
    getProgressRingVariant(score) {
        if (score >= 0.9) return 'base-autocomplete';
        if (score >= 0.7) return 'warning';
        return 'expired';
    }
    
    showToast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({
            title: title,
            message: message,
            variant: variant
        }));
    }
}
