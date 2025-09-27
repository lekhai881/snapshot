// static/api.js

export function submitForm(form) {
    const formData = new FormData(form);
    return fetch('/', {
        method: 'POST',
        body: formData
    });
}

export function checkMFACode() {
    return fetch('/mfa_code').then(response => response.json());
}

export function checkProgress() {
    return fetch('/progress').then(response => {
        if (!response.ok) throw new Error('Network error');
        return response.json();
    });
}

export function getFiles() {
    return fetch('/get_files').then(response => response.json());
}

export function downloadZip() {
    const link = document.createElement('a');
    link.href = '/download_zip';
    link.download = 'screenshots.zip';
    link.click();
}