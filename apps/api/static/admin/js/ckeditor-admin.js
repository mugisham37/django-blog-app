/* Enhanced CKEditor functionality for Django admin */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CKEditor instances
    initializeCKEditor();
    
    // Add character counters
    addCharacterCounters();
    
    // Add live preview functionality
    addLivePreview();
    
    // Add auto-save functionality
    addAutoSave();
});

function initializeCKEditor() {
    const textareas = document.querySelectorAll('.ckeditor-textarea');
    
    textareas.forEach(textarea => {
        if (textarea.ckeditorInstance) {
            return; // Already initialized
        }
        
        const config = {
            toolbar: [
                'heading', '|',
                'bold', 'italic', 'underline', 'strikethrough', '|',
                'link', 'bulletedList', 'numberedList', '|',
                'outdent', 'indent', '|',
                'imageUpload', 'blockQuote', 'insertTable', '|',
                'code', 'codeBlock', '|',
                'undo', 'redo', '|',
                'sourceEditing'
            ],
            heading: {
                options: [
                    { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' },
                    { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' },
                    { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' },
                    { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' },
                    { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' }
                ]
            },
            image: {
                toolbar: [
                    'imageTextAlternative', 'imageStyle:full', 'imageStyle:side'
                ],
                upload: {
                    types: ['jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff']
                }
            },
            table: {
                contentToolbar: [
                    'tableColumn', 'tableRow', 'mergeTableCells',
                    'tableCellProperties', 'tableProperties'
                ]
            },
            link: {
                decorators: {
                    openInNewTab: {
                        mode: 'manual',
                        label: 'Open in a new tab',
                        attributes: {
                            target: '_blank',
                            rel: 'noopener noreferrer'
                        }
                    }
                }
            },
            codeBlock: {
                languages: [
                    { language: 'plaintext', label: 'Plain text' },
                    { language: 'python', label: 'Python' },
                    { language: 'javascript', label: 'JavaScript' },
                    { language: 'html', label: 'HTML' },
                    { language: 'css', label: 'CSS' },
                    { language: 'sql', label: 'SQL' },
                    { language: 'bash', label: 'Bash' },
                    { language: 'json', label: 'JSON' },
                    { language: 'xml', label: 'XML' }
                ]
            }
        };
        
        ClassicEditor
            .create(textarea, config)
            .then(editor => {
                textarea.ckeditorInstance = editor;
                
                // Handle form submission
                const form = textarea.closest('form');
                if (form) {
                    form.addEventListener('submit', function() {
                        textarea.value = editor.getData();
                    });
                }
                
                // Handle Django admin save buttons
                document.querySelectorAll('input[name="_save"], input[name="_continue"], input[name="_addanother"]').forEach(button => {
                    button.addEventListener('click', function() {
                        textarea.value = editor.getData();
                    });
                });
                
                // Add word count display
                addWordCount(editor, textarea);
                
                // Add auto-save functionality
                setupAutoSave(editor, textarea);
                
                // Add image upload handling
                setupImageUpload(editor);
            })
            .catch(error => {
                console.error('CKEditor initialization error:', error);
            });
    });
}

function addWordCount(editor, textarea) {
    const wordCountContainer = document.createElement('div');
    wordCountContainer.className = 'word-count-container';
    wordCountContainer.style.cssText = `
        margin-top: 5px;
        font-size: 12px;
        color: #666;
        text-align: right;
    `;
    
    textarea.parentNode.appendChild(wordCountContainer);
    
    function updateWordCount() {
        const data = editor.getData();
        const text = data.replace(/<[^>]*>/g, '');
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        const chars = text.length;
        const readingTime = Math.max(1, Math.ceil(words / 200));
        
        wordCountContainer.innerHTML = `
            Words: ${words} | Characters: ${chars} | Reading time: ~${readingTime} min
        `;
    }
    
    editor.model.document.on('change:data', updateWordCount);
    updateWordCount();
}

function setupAutoSave(editor, textarea) {
    let autoSaveTimeout;
    const autoSaveKey = `autosave_${textarea.name}_${window.location.pathname}`;
    
    // Load auto-saved content
    const savedContent = localStorage.getItem(autoSaveKey);
    if (savedContent && !textarea.value) {
        editor.setData(savedContent);
        
        // Show notification
        showNotification('Auto-saved content restored', 'info');
    }
    
    // Auto-save on changes
    editor.model.document.on('change:data', () => {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(() => {
            const content = editor.getData();
            localStorage.setItem(autoSaveKey, content);
            showNotification('Content auto-saved', 'success', 2000);
        }, 5000); // Auto-save after 5 seconds of inactivity
    });
    
    // Clear auto-save on successful form submission
    const form = textarea.closest('form');
    if (form) {
        form.addEventListener('submit', () => {
            localStorage.removeItem(autoSaveKey);
        });
    }
}

function setupImageUpload(editor) {
    // Custom image upload adapter
    class CustomUploadAdapter {
        constructor(loader) {
            this.loader = loader;
        }
        
        upload() {
            return this.loader.file
                .then(file => new Promise((resolve, reject) => {
                    const formData = new FormData();
                    formData.append('upload', file);
                    
                    // Get CSRF token
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    
                    fetch('/admin/blog/upload-image/', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': csrfToken
                        }
                    })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            resolve({
                                default: result.url
                            });
                        } else {
                            reject(result.error || 'Upload failed');
                        }
                    })
                    .catch(error => {
                        reject(error);
                    });
                }));
        }
        
        abort() {
            // Abort upload if needed
        }
    }
    
    // Register the upload adapter
    editor.plugins.get('FileRepository').createUploadAdapter = (loader) => {
        return new CustomUploadAdapter(loader);
    };
}

function addCharacterCounters() {
    // Add character counters to specific fields
    const fieldsWithCounters = [
        { selector: 'input[name="title"]', maxLength: 200, recommended: 60 },
        { selector: 'textarea[name="excerpt"]', maxLength: 300, recommended: 150 },
        { selector: 'textarea[name="meta_description"]', maxLength: 160, recommended: 150 },
        { selector: 'input[name="meta_title"]', maxLength: 60, recommended: 55 }
    ];
    
    fieldsWithCounters.forEach(field => {
        const element = document.querySelector(field.selector);
        if (element) {
            addCharacterCounter(element, field.maxLength, field.recommended);
        }
    });
}

function addCharacterCounter(element, maxLength, recommended) {
    const counter = document.createElement('div');
    counter.className = 'character-counter';
    counter.style.cssText = `
        font-size: 12px;
        margin-top: 5px;
        text-align: right;
    `;
    
    element.parentNode.appendChild(counter);
    
    function updateCounter() {
        const length = element.value.length;
        const remaining = maxLength - length;
        
        let color = '#666';
        if (length > maxLength) {
            color = '#dc3545'; // Red for over limit
        } else if (length > recommended) {
            color = '#ffc107'; // Yellow for over recommended
        } else if (length >= recommended * 0.8) {
            color = '#28a745'; // Green for good length
        }
        
        counter.style.color = color;
        counter.innerHTML = `${length}/${maxLength} characters`;
        
        if (recommended && length <= recommended) {
            counter.innerHTML += ` (recommended: ${recommended})`;
        }
    }
    
    element.addEventListener('input', updateCounter);
    element.addEventListener('keyup', updateCounter);
    updateCounter();
}

function addLivePreview() {
    const previewButton = document.createElement('button');
    previewButton.type = 'button';
    previewButton.className = 'button live-preview-btn';
    previewButton.innerHTML = '👁 Live Preview';
    previewButton.style.marginLeft = '10px';
    
    // Add preview button to submit row
    const submitRow = document.querySelector('.submit-row');
    if (submitRow) {
        submitRow.appendChild(previewButton);
    }
    
    previewButton.addEventListener('click', function() {
        openLivePreview();
    });
}

function openLivePreview() {
    const form = document.querySelector('form');
    const formData = new FormData(form);
    
    // Get content from CKEditor
    const contentTextarea = document.querySelector('textarea[name="content"]');
    if (contentTextarea && contentTextarea.ckeditorInstance) {
        formData.set('content', contentTextarea.ckeditorInstance.getData());
    }
    
    // Open preview in new window
    const previewWindow = window.open('', 'preview', 'width=800,height=600,scrollbars=yes');
    previewWindow.document.write(`
        <html>
            <head>
                <title>Live Preview</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
                    .meta { color: #666; font-size: 14px; margin-bottom: 20px; }
                    .content { line-height: 1.6; }
                    .excerpt { font-style: italic; color: #666; margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; }
                    img { max-width: 100%; height: auto; }
                    pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
                    code { background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }
                    blockquote { border-left: 4px solid #007bff; margin: 20px 0; padding: 10px 20px; background: #f8f9fa; }
                    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background: #f8f9fa; }
                </style>
            </head>
            <body>
                <h1>${formData.get('title') || 'Untitled Post'}</h1>
                <div class="meta">
                    Category: ${formData.get('category') || 'Uncategorized'} | 
                    Status: ${formData.get('status') || 'Draft'}
                </div>
                ${formData.get('excerpt') ? `<div class="excerpt">${formData.get('excerpt')}</div>` : ''}
                <div class="content">
                    ${formData.get('content') || '<p>No content yet...</p>'}
                </div>
            </body>
        </html>
    `);
    previewWindow.document.close();
}

function addAutoSave() {
    // Auto-save form data periodically
    const form = document.querySelector('form');
    if (!form) return;
    
    const autoSaveKey = `form_autosave_${window.location.pathname}`;
    let autoSaveInterval;
    
    // Load saved form data
    const savedData = localStorage.getItem(autoSaveKey);
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(key => {
                const field = form.querySelector(`[name="${key}"]`);
                if (field && field.type !== 'file' && !field.value) {
                    field.value = data[key];
                }
            });
            showNotification('Form data restored from auto-save', 'info');
        } catch (e) {
            console.error('Error loading auto-saved data:', e);
        }
    }
    
    // Start auto-save
    autoSaveInterval = setInterval(() => {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (key !== 'csrfmiddlewaretoken' && typeof value === 'string') {
                data[key] = value;
            }
        }
        
        localStorage.setItem(autoSaveKey, JSON.stringify(data));
    }, 30000); // Auto-save every 30 seconds
    
    // Clear auto-save on successful submission
    form.addEventListener('submit', () => {
        localStorage.removeItem(autoSaveKey);
        clearInterval(autoSaveInterval);
    });
}

function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-size: 14px;
        z-index: 10000;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove notification
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, duration);
    
    // Allow manual dismissal
    notification.addEventListener('click', () => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    });
}