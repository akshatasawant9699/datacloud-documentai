import { LightningElement, wire, api } from 'lwc';
import { getObjectInfo, getPicklistValues } from 'lightning/uiObjectInfoApi';
import OPPORTUNITY_OBJECT from '@salesforce/schema/Opportunity';
import checkIfDealSourcePersonIsInternal from '@salesforce/apex/NewPublicDealFormController.checkIfDealSourcePersonIsInternal';
import DEAL_LOG_NA_REASON from '@salesforce/schema/Opportunity.DealLogNAReason__c';
import DEAL_SOURCE from '@salesforce/schema/Opportunity.DealSource__c';

const DEAL_TYPE_NEW_CLIENT = 'New Bid, New Client';
const DEAL_TYPE_REBID = 'Renewal/Re-Bid, Existing Client';
const DEAL_TYPE_INCREMENTAL = 'New Bid, Existing Client';
const FIELD_ESTIMATED_WIN_DATE = 'Estimated Win Date (TSS/ICM enter Close Date)';
const FIELD_ACCOUNT_CREATION_REQUIRED = 'AccountCreationRequired__c';
const FIELD_CREDIT_FACILITY_REQUIRED = 'CreditFacilityRequired__c';
const FIELD_IMPLEMENTATION_NEEDED = 'ImplementationNeeded__c';
const TRADINGAREAL2_CCM = '133';
const TSS_DEALS = ['TSS-CT', 'TSS-DR', 'TSS-SeS'];
const SES_DEAL = 'SeS';
const ICM_AT_RISK_DEAL = 'ICM - Business At Risk';
const ICM_Deal = 'ICM';
const EXPECTED_1ST_YEAR_REVENUE = 'Expected 1st Year Revenue';
const IMPLEMENTATION_LEAD_TEAM = 'Implementation Lead Team';
const DEAL_IS_PUBLIC = 'Deal is Public';

export default class NewPublicDealFormRecord extends LightningElement {
    Name;
    Amount = 0;
    ESGDeal__c = 'No';
    DealType__c;
    RebidCurrentValue__c = 0;
    RebidAtRisk__c;
    CreditFacilityRequired__c;
    AccountCreationRequired__c;
    ImplementationNeeded__c;
    GCSTeamInvolved__c = 'No';
    gcsValue = 'No';
    RFP__c = false;
    StageName;
    TradingAreaL1__c;
    TradingAreaL2__c;
    AtRiskDeal__c = false;
    SubStageName__c;
    DealSource__c;
    DealLogNAReason__c;
    cruiseDealIdRequired = false;
    otherDealLogReasonRequired = false;
    RFPToggle = false;
    GCSToggle = false;

    _defaultValues;

    @api recordTypeId;
    @api showAdditionalFields;

    @api
    get defaultValues() {
        return this._defaultValues || {};
    }

    @api
    selectedTemplateName;

    set selectedTemplateName(value) {
        this._selectedTemplateName = value;
        if (value && value.includes(SES_DEAL)) {
            this.DealLogNAReason__c = DEAL_IS_PUBLIC;
        } else {
            this.DealLogNAReason__c = null;
        }
    }

    get selectedTemplateName() {
        return this._selectedTemplateName;
    }

    set defaultValues(value = {}) {
        this._defaultValues = value;
        Object.keys(value).forEach((key) => {
            this[key] = value[key];
        });
    }

    @wire(getObjectInfo, { objectApiName: OPPORTUNITY_OBJECT })
    objectInfo;

    @wire(getPicklistValues, {recordTypeId: '$recordTypeId', fieldApiName: DEAL_LOG_NA_REASON})
    dealLogNAReasonPicklistValues;

    @wire(getPicklistValues, {recordTypeId: '$recordTypeId', fieldApiName: DEAL_SOURCE})
    dealSourcePicklistValues;

    @api
    focus() {
        this.template.querySelector("lightning-input[title='name']").focus();
    }

    @api
    validate() {
        this.template.querySelector("button[type='submit']").click();
        const fields = {};
        for (let input of this.template.querySelectorAll('lightning-input-field')) {
            if (!input.reportValidity()) {
                console.log('Missing value for: ' + input.fieldName);
                return false;
            }
            fields[input.fieldName] = input.value;
        }
        return fields;
    }

    @api
    submit() {
        return this.template.querySelector('lightning-record-edit-form').submit();
    }

    get recordTypeName() {
        // Returns a map of record type Ids
        if (!this.objectInfo.data) return undefined;
        const rtis = this.objectInfo.data.recordTypeInfos;
        return Object.values(rtis).find((rti) => rti.recordTypeId === this.recordTypeId)?.name;
    }

    get labels() {
        if (!this.objectInfo.data) return {};
        return {
            dealTypeNewClient: DEAL_TYPE_NEW_CLIENT,
            dealTypeRebid: DEAL_TYPE_REBID,
            dealTypeIncremental: DEAL_TYPE_INCREMENTAL,
            fieldName: this.objectInfo.data.fields.Name.label,
            fieldAmount: EXPECTED_1ST_YEAR_REVENUE,
            fieldClientName: this.objectInfo.data.fields.AccountId.label,
            fieldCurrency: this.objectInfo.data.fields.CurrencyIsoCode.label,
            fieldOverview: this.objectInfo.data.fields.Description.label,
            fieldESG: this.objectInfo.data.fields.ESGDeal__c.label,
            fieldEstimatedWinDate: FIELD_ESTIMATED_WIN_DATE,
            fieldPrimaryCampaignSource: this.objectInfo.data.fields.CampaignId.label,
            fieldRebid: this.objectInfo.data.fields.RebidCurrentValue__c.label,
            fieldRebidAtRisk: this.objectInfo.data.fields.RebidAtRisk__c.label,
            fieldRFP: this.objectInfo.data.fields.RFP__c.label,
            fieldImpLeadTeam: IMPLEMENTATION_LEAD_TEAM,
            fieldGCSTeamInvolved: this.objectInfo.data.fields.GCSTeamInvolved__c.label
        };
    }

    get rebidHelpText() {
        return this.objectInfo.data.fields.RebidCurrentValue__c.inlineHelpText
    }

    get isAtRiskRebid() {
        return this.DealType__c === DEAL_TYPE_REBID && this.AtRiskDeal__c === false;
    }

    get isTssTemplate() {
        return TSS_DEALS.includes(this.selectedTemplateName);
    }

    get requiresDealLogNAReason() {
        return TSS_DEALS.includes(this.selectedTemplateName) || this.selectedTemplateName === SES_DEAL;
    }

    get requiresDealSource() {
        return this.isTssTemplate || this.selectedTemplateName === SES_DEAL;
    }

    get isAtRiskDealTemplate() {
        return this.selectedTemplateName === ICM_AT_RISK_DEAL;
    }

    get isNonRiskICMDealTemplate() {
        return this.selectedTemplateName === ICM_Deal;
    }

    get labelAccountCreationRequired() {
        if (!this.objectInfo.data) return '';
        return this.objectInfo.data.fields[FIELD_ACCOUNT_CREATION_REQUIRED].label;
    }

    get labelCreditFacilityRequired() {
        if (!this.objectInfo.data) return '';
        return this.objectInfo.data.fields[FIELD_CREDIT_FACILITY_REQUIRED].label;
    }

    get labelImplementationNeeded() {
        if (!this.objectInfo.data) return '';
        return this.objectInfo.data.fields[FIELD_IMPLEMENTATION_NEEDED].label;
    }

    get isCreditFacilityRequired() {
        return this.CreditFacilityRequired__c === 'Yes';
    }

    get isAccountCreationRequired() {
        return this.AccountCreationRequired__c === 'Yes';
    }

    get isImplementationNeeded() {
        return this.ImplementationNeeded__c === 'Yes';
    }

    get isImplementationNotNeeded() {
        return !this.isImplementationNeeded;
    }

    get variance() {
        return this.Amount - this.RebidCurrentValue__c;
    }

    get dealLogReasonPicklistValues() {
        return this.dealLogNAReasonPicklistValues?.data?.values;
    }

    get picklistValues() {
        return this.dealSourcePicklistValues?.data?.values;
    }

    handleNameChanged(event) {
        this.Name = event.target.value;
    }

    handleDealTypeSelected(event) {
        this.DealType__c = event.detail.value;
    }

    handleAmountChange(event) {
        this.Amount = parseInt(event.target.value || 0, 10);
    }

    handleRebidChange(event) {
        this.RebidCurrentValue__c = parseInt(event.target.value || 0, 10);
    }

    handleSubmit(event) {
        event.preventDefault();
    }

    handleSourcePersonChange(event) {
        const fieldName = event.target.dataset.field;
        const fieldValue = event.target.value;
        checkIfDealSourcePersonIsInternal({ dealSourcePersonId: fieldValue })
            .then((result) => {
                if (result) {
                    this.dispatchEvent(
                        new CustomEvent('dealfieldschanged', {
                            detail: { fieldName: fieldName, fieldValue: fieldValue }
                        })
                    );
                }
            })
            .catch((e) => {
                console.error('error!', e);
            });
    }

    handleToggleChange(event) {
        const fieldName = event.target.dataset.field;
        if (this.objectInfo.data.fields[fieldName].dataType === 'Picklist') {
            this[fieldName] = event.target.checked ? 'Yes' : 'No';
        } else {
            this[fieldName] = event.target.checked;
            console.log('fieldName ', fieldName);
            
            // When RFP is checked, automatically check GCS Team Involved
            if (fieldName === 'RFP__c' && event.target.checked) {
                this.GCSToggle = true;
                this.gcsValue = 'Yes';
                this.GCSTeamInvolved__c = 'Yes';
            }
            
            this.dispatchEvent(
                new CustomEvent('dealfieldschanged', {
                    detail: { fieldName: fieldName, fieldValue: event.target.checked }
                })
            );
        }
    }

    handleRFPToggleChange(event){
        
        this.RFPToggle = event.target.checked ? 'Yes' : 'No';
        if(this.RFPToggle){
            this.GCSToggle = true;
        }
    }

    handleGCSToggleChange(event){
        console.log(' line 274 ',event.target.dataset.field )
        this.gcsValue = event.target.checked ? 'Yes' : 'No';
    }
    
    handleDealSourceChange(event) {
        this.DealSource__c = event.target.value
    }

    handleDealLogReasonChange(event) {
        this.DealLogNAReason__c = event.target.value;
        this.otherDealLogReasonRequired = event.target.value == 'Other';  
        this.cruiseDealIdRequired = event.target.value == 'Maintaining insider list – Ad-hoc Inside Information';     
    }

    focusMessage(e) {
        this.refs.message.style.visibility = "visible";
      }
    
    hideMessage(e) {
        this.refs.message.style.visibility = "hidden";
      }
}