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
            const authUrl = `https://${data.loginUrl}/services/oauth2/authorize?response_type=code&client_id=${data.clientId}&redirect_uri=${redirectUri}&scope=api%20cdp_query_api%20cdp_profile_api&code_challenge=${codeChallenge}&code_challenge_method=S256`;

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
            
            try {
                // Try to parse as JSON
                const jsonData = JSON.parse(result);
                // Convert back to string with proper formatting
                result = JSON.stringify(jsonData, null, 2);
            } catch (e) {
                // If parsing fails, use the raw text
                console.error('JSON parsing failed:', e);
            }

            // Decode any HTML entities in the result
            result = decodeHtmlEntities(result);
            
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