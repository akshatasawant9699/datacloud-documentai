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

    // Function to decode HTML entities
    function decodeHtmlEntities(str) {
        const textarea = document.createElement('textarea');
        textarea.innerHTML = str;
        return textarea.value;
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        loadingIndicator.style.display = 'flex';
        resultSection.style.display = 'none';

        try {
            const formData = new FormData(this);
            const response = await fetch('/extract-data', {
                method: 'POST',
                body: formData
            });

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