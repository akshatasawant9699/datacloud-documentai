// Create this file at /Users/ananth.anto/CascadeProjects/hello-curl/static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('extractForm');
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.querySelector('.file-name');
    const imagePreview = document.getElementById('imagePreview');
    const previewSection = document.querySelector('.preview-section');
    const loadingIndicator = document.getElementById('loading');
    const resultSection = document.getElementById('result');
    const resultContent = document.getElementById('resultContent');
    
    // Authentication elements
    const authStatus = document.getElementById('auth-status');
    const authIcon = document.getElementById('auth-icon');
    const authMessage = document.getElementById('auth-message');
    const authButton = document.getElementById('auth-button');
    const analyzeBtn = document.getElementById('analyze-btn');

    // Check authentication status on page load
    checkAuthStatus();

    // Update file name display when file is selected
    fileInput.addEventListener('change', function() {
        const fileName = this.files[0]?.name || 'No file chosen';
        fileNameDisplay.textContent = fileName;

        // Show preview for images only
        if (this.files && this.files[0]) {
            const file = this.files[0];
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    previewSection.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                // Hide preview for non-image files
                previewSection.style.display = 'none';
            }
        }
    });

    // Authentication functions
    async function checkAuthStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.authenticated) {
                authIcon.textContent = '✅';
                authMessage.textContent = 'Authenticated with Salesforce';
                authStatus.className = 'auth-status authenticated';
                authButton.style.display = 'none';
                analyzeBtn.disabled = false;
            } else {
                authIcon.textContent = '❌';
                authMessage.textContent = 'Not authenticated. Please authenticate to use the application.';
                authStatus.className = 'auth-status not-authenticated';
                authButton.style.display = 'block';
                analyzeBtn.disabled = true;
            }
        } catch (error) {
            console.error('Error checking auth status:', error);
            authIcon.textContent = '❌';
            authMessage.textContent = 'Error checking authentication status';
            authStatus.className = 'auth-status not-authenticated';
            authButton.style.display = 'block';
            analyzeBtn.disabled = true;
        }
    }

    // PKCE helper functions
    function base64urlencode(str) {
        return btoa(String.fromCharCode.apply(null, new Uint8Array(str)))
            .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    async function sha256(plain) {
        const encoder = new TextEncoder();
        const data = encoder.encode(plain);
        const hash = await window.crypto.subtle.digest('SHA-256', data);
        return base64urlencode(hash);
    }

    async function authenticateWithSalesforce() {
        try {
            const response = await fetch('/api/auth-info');
            const data = await response.json();
            
            if (!data.loginUrl || !data.clientId) {
                alert('Salesforce configuration missing on server');
                return;
            }

            // PKCE: generate code_verifier and code_challenge
            const codeVerifier = Array.from(crypto.getRandomValues(new Uint8Array(32)))
                .map(b => ('0' + b.toString(16)).slice(-2)).join('');
            const codeChallenge = await sha256(codeVerifier);

            // Store code_verifier in sessionStorage
            sessionStorage.setItem('pkce_code_verifier', codeVerifier);

            const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);
            const authUrl = `https://${data.loginUrl}/services/oauth2/authorize?response_type=code&client_id=${data.clientId}&redirect_uri=${redirectUri}&scope=full%20api%20refresh_token&code_challenge=${codeChallenge}&code_challenge_method=S256`;

            window.location.href = authUrl;
        } catch (error) {
            alert('Failed to initiate authentication: ' + error.message);
        }
    }

    // Add event listener for authentication button
    authButton.addEventListener('click', authenticateWithSalesforce);

    // Function to decode HTML entities
    function decodeHtmlEntities(str) {
        const textarea = document.createElement('textarea');
        textarea.innerHTML = str;
        return textarea.value;
    }

    // Function to format field name for display
    function formatFieldName(fieldName) {
        return fieldName
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    // Function to get confidence indicator
    function getConfidenceIndicator(score) {
        if (score === null || score === undefined) {
            return { icon: '⚪', color: '#6c757d', text: 'N/A' };
        }
        const percent = Math.round(score * 100);
        if (percent >= 90) {
            return { icon: '🟢', color: '#28a745', text: `${percent}%` };
        } else if (percent >= 70) {
            return { icon: '🟡', color: '#ffc107', text: `${percent}%` };
        } else {
            return { icon: '🔴', color: '#dc3545', text: `${percent}%` };
        }
    }

    // Function to detect document type
    function detectDocumentType(jsonData) {
        // Check for explicit document_type field with a valid value
        if (jsonData.document_type && jsonData.document_type.value && 
            jsonData.document_type.value !== null && 
            String(jsonData.document_type.value).toLowerCase() !== 'null' &&
            String(jsonData.document_type.value).trim() !== '') {
            return jsonData.document_type.value;
        }
        
        // Helper function to check if field has a valid value (for detection purposes)
        const hasValidValue = (field) => {
            if (!field) return false;
            const val = field.value;
            // Numbers (including 0) are valid
            if (typeof val === 'number') return true;
            // Check for null/undefined/empty
            if (val === null || val === undefined) return false;
            if (String(val).toLowerCase() === 'null') return false;
            if (typeof val === 'string' && val.trim() === '') return false;
            // Arrays need at least one item
            if (Array.isArray(val)) return val.length > 0;
            return true;
        };
        
        // Count invoice-specific fields with values
        let invoiceScore = 0;
        if (hasValidValue(jsonData.invoice_number)) invoiceScore += 3;
        if (hasValidValue(jsonData.invoice_date)) invoiceScore += 2;
        if (hasValidValue(jsonData.due_date)) invoiceScore += 2;
        if (hasValidValue(jsonData.amount_paid)) invoiceScore += 1;
        if (hasValidValue(jsonData.balance_due)) invoiceScore += 1;
        
        // Count sales order-specific fields with values
        let salesOrderScore = 0;
        if (hasValidValue(jsonData.sales_order_number)) salesOrderScore += 3;
        if (hasValidValue(jsonData.order_date)) salesOrderScore += 2;
        if (hasValidValue(jsonData.delivery_date)) salesOrderScore += 2;
        if (hasValidValue(jsonData.delivery_conditions)) salesOrderScore += 1;
        if (hasValidValue(jsonData.shipping_method)) salesOrderScore += 1;
        if (hasValidValue(jsonData.purchase_order_number)) salesOrderScore += 1;
        
        // Determine document type based on scores
        if (invoiceScore > salesOrderScore && invoiceScore >= 2) {
            return 'Invoice';
        } else if (salesOrderScore > invoiceScore && salesOrderScore >= 2) {
            return 'Sales Order';
        } else if (invoiceScore >= 2) {
            return 'Invoice';
        } else if (salesOrderScore >= 2) {
            return 'Sales Order';
        }
        
        // Check document_number field as fallback
        if (hasValidValue(jsonData.document_number)) {
            const docNum = String(jsonData.document_number.value).toLowerCase();
            if (docNum.includes('inv') || docNum.includes('fak') || docNum.includes('bill')) {
                return 'Invoice';
            }
            if (docNum.includes('so') || docNum.includes('order') || docNum.includes('po')) {
                return 'Sales Order';
            }
        }
        
        // If we have line items and total, likely a commercial document
        if (hasValidValue(jsonData.line_items) || hasValidValue(jsonData.total_amount)) {
            return 'Commercial Document';
        }
        
        return 'Document';
    }

    // Function to check if a field has a value
    function hasFieldValue(fieldData) {
        if (!fieldData || typeof fieldData !== 'object') return false;
        const value = fieldData.value;
        // null, undefined, or string "null" means no value
        if (value === null || value === undefined || String(value).toLowerCase() === 'null') return false;
        // Empty string means no value
        if (typeof value === 'string' && value.trim() === '') return false;
        // Empty array means no value
        if (Array.isArray(value) && value.length === 0) return false;
        // 0 is a valid value for numbers
        if (typeof value === 'number') return true;
        return true;
    }

    // Function to render line items table
    function renderLineItemsTable(lineItems) {
        if (!lineItems || !Array.isArray(lineItems) || lineItems.length === 0) {
            return '<span style="color: #6c757d;">No line items</span>';
        }

        // Extract all possible column headers from line items
        const columns = new Set();
        lineItems.forEach(item => {
            if (item && item.value && typeof item.value === 'object') {
                Object.keys(item.value).forEach(key => columns.add(key));
            }
        });

        const columnList = Array.from(columns);
        
        let html = `
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 5px;">
                <thead>
                    <tr style="background-color: #e9ecef;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">#</th>
                        ${columnList.map(col => `<th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">${formatFieldName(col)}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
        `;

        lineItems.forEach((item, index) => {
            html += '<tr>';
            html += `<td style="padding: 8px; border: 1px solid #dee2e6;">${index + 1}</td>`;
            
            columnList.forEach(col => {
                let cellValue = '—';
                if (item && item.value && item.value[col]) {
                    const fieldData = item.value[col];
                    if (fieldData && fieldData.value !== null && fieldData.value !== undefined) {
                        cellValue = String(fieldData.value);
                    }
                }
                html += `<td style="padding: 8px; border: 1px solid #dee2e6;">${cellValue}</td>`;
            });
            
            html += '</tr>';
        });

        html += '</tbody></table>';
        return html;
    }

    // Function to parse and display confidence scores
    function displayConfidenceScores(jsonData) {
        const confidenceDisplay = document.getElementById('confidenceDisplay');
        const tableBody = document.getElementById('confidenceTableBody');
        
        if (!jsonData || typeof jsonData !== 'object') {
            confidenceDisplay.style.display = 'none';
            return;
        }

        // Detect and display document type
        const docType = detectDocumentType(jsonData);
        let docTypeHtml = document.getElementById('docTypeIndicator');
        if (!docTypeHtml) {
            docTypeHtml = document.createElement('div');
            docTypeHtml.id = 'docTypeIndicator';
            confidenceDisplay.insertBefore(docTypeHtml, confidenceDisplay.firstChild);
        }
        
        const docTypeLower = docType.toLowerCase();
        let docTypeIcon, docTypeColor;
        
        if (docTypeLower.includes('invoice') || docTypeLower.includes('faktura') || docTypeLower.includes('bill')) {
            docTypeIcon = '🧾';
            docTypeColor = '#0d6efd';
        } else if (docTypeLower.includes('sales') || docTypeLower.includes('order') || docTypeLower.includes('purchase')) {
            docTypeIcon = '📦';
            docTypeColor = '#198754';
        } else if (docTypeLower.includes('commercial')) {
            docTypeIcon = '📋';
            docTypeColor = '#6f42c1';
        } else {
            docTypeIcon = '📄';
            docTypeColor = '#6c757d';
        }
        
        docTypeHtml.innerHTML = `
            <div style="background: linear-gradient(135deg, ${docTypeColor}15, ${docTypeColor}05); 
                        border-left: 4px solid ${docTypeColor}; 
                        padding: 15px 20px; 
                        margin-bottom: 20px; 
                        border-radius: 0 8px 8px 0;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 32px;">${docTypeIcon}</span>
                    <div>
                        <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 1px;">Document Type Detected</div>
                        <div style="font-size: 24px; font-weight: 600; color: ${docTypeColor};">${docType}</div>
                    </div>
                </div>
            </div>
        `;

        tableBody.innerHTML = '';
        
        // Separate fields with values and without values
        const fieldsWithValues = [];
        const fieldsWithoutValues = [];
        let lineItemsData = null;

        for (const [fieldName, fieldData] of Object.entries(jsonData)) {
            if (fieldData && typeof fieldData === 'object' && 'value' in fieldData) {
                // Special handling for line_items
                if (fieldName === 'line_items') {
                    lineItemsData = { fieldName, fieldData };
                    continue;
                }
                
                if (hasFieldValue(fieldData)) {
                    fieldsWithValues.push({ fieldName, fieldData });
                } else {
                    fieldsWithoutValues.push({ fieldName, fieldData });
                }
            }
        }

        // Sort each group alphabetically
        fieldsWithValues.sort((a, b) => a.fieldName.localeCompare(b.fieldName));
        fieldsWithoutValues.sort((a, b) => a.fieldName.localeCompare(b.fieldName));

        // Combine: fields with values first, then line items, then empty fields
        const sortedFields = [...fieldsWithValues];
        if (lineItemsData) {
            sortedFields.push(lineItemsData);
        }
        sortedFields.push(...fieldsWithoutValues);

        let hasConfidenceData = false;

        // Add separator before empty fields if there are any
        let addedEmptySeparator = false;

        for (const { fieldName, fieldData } of sortedFields) {
            hasConfidenceData = true;
            
            // Add separator before empty fields section
            if (!hasFieldValue(fieldData) && fieldName !== 'line_items' && !addedEmptySeparator && fieldsWithoutValues.length > 0) {
                addedEmptySeparator = true;
                const separatorRow = document.createElement('tr');
                separatorRow.innerHTML = `
                    <td colspan="3" style="padding: 15px 12px; background-color: #f8f9fa; color: #6c757d; font-style: italic; font-size: 13px;">
                        ⬇️ Fields not found in document (${fieldsWithoutValues.length})
                    </td>
                `;
                tableBody.appendChild(separatorRow);
            }

            const row = document.createElement('tr');
            row.style.borderBottom = '1px solid #dee2e6';
            
            // Dim rows without values
            if (!hasFieldValue(fieldData) && fieldName !== 'line_items') {
                row.style.opacity = '0.6';
                row.style.backgroundColor = '#fafafa';
            }

            // Field name cell
            const nameCell = document.createElement('td');
            nameCell.style.padding = '12px';
            nameCell.style.fontWeight = '500';
            nameCell.textContent = formatFieldName(fieldName);
            row.appendChild(nameCell);

            // Value cell
            const valueCell = document.createElement('td');
            valueCell.style.padding = '12px';
            
            const value = fieldData.value;
            if (fieldName === 'line_items' && fieldData.type === 'array' && Array.isArray(value)) {
                // Render line items as a table
                valueCell.innerHTML = renderLineItemsTable(value);
                valueCell.colSpan = 1;
            } else if (value !== null && value !== undefined && String(value) !== 'null' && String(value) !== '') {
                valueCell.textContent = String(value);
            } else {
                valueCell.innerHTML = '<span style="color: #6c757d;">—</span>';
            }
            row.appendChild(valueCell);

            // Confidence cell
            const confCell = document.createElement('td');
            confCell.style.padding = '12px';
            confCell.style.textAlign = 'center';
            confCell.style.verticalAlign = 'top';
            
            const confidence = fieldData.confidence_score;
            const indicator = getConfidenceIndicator(confidence);
            
            confCell.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>${indicator.icon}</span>
                    <span style="color: ${indicator.color}; font-weight: 600;">${indicator.text}</span>
                </div>
            `;
            row.appendChild(confCell);

            tableBody.appendChild(row);
        }

        confidenceDisplay.style.display = hasConfidenceData ? 'block' : 'none';
    }

    // Toggle raw JSON display
    const toggleRawJsonBtn = document.getElementById('toggleRawJson');
    if (toggleRawJsonBtn) {
        toggleRawJsonBtn.addEventListener('click', function() {
            const rawJsonPre = document.getElementById('resultContent');
            rawJsonPre.style.display = rawJsonPre.style.display === 'none' ? 'block' : 'none';
        });
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Check authentication before proceeding
        if (analyzeBtn.disabled) {
            alert('Please authenticate with Salesforce first.');
            return;
        }
        
        loadingIndicator.style.display = 'flex';
        resultSection.style.display = 'none';

        try {
            const formData = new FormData(this);
            const response = await fetch('/extract-data', {
                method: 'POST',
                body: formData
            });

            if (response.status === 401) {
                // Authentication error - recheck status
                await checkAuthStatus();
                alert('Authentication required. Please authenticate with Salesforce first.');
                return;
            }

            let result = await response.text();
            let jsonData = null;
            
            try {
                // Try to parse as JSON
                jsonData = JSON.parse(result);
                // Convert back to string with proper formatting
                result = JSON.stringify(jsonData, null, 2);
            } catch (e) {
                // If parsing fails, use the raw text
                console.error('JSON parsing failed:', e);
            }

            // Decode any HTML entities in the result
            result = decodeHtmlEntities(result);
            
            // Display confidence scores if available
            if (jsonData) {
                displayConfidenceScores(jsonData);
            }
            
            resultContent.textContent = result;
            resultSection.style.display = 'block';
        } catch (error) {
            resultContent.textContent = 'Error: ' + error.message;
            resultSection.style.display = 'block';
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });
});