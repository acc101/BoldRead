document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const uploadButton = document.getElementById('upload-button');
    const resultContainer = document.getElementById('c2');
    const downloadLink = document.getElementById('download-link');

    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            uploadButton.removeAttribute('disabled');
        } else {
            fileName.textContent = 'No file selected.';
            uploadButton.setAttribute('disabled', true);
        }
    });

    uploadButton.addEventListener('click', async () => {
        if (!fileInput.files.length) {
            alert('Please select a file first.');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/process-file', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('An error occurred while processing the file.');
            }

            const result = await response.blob();
            const downloadUrl = URL.createObjectURL(result);
            downloadLink.href = downloadUrl;
            downloadLink.download = `formatted_${file.name}`;
            resultContainer.style.display = 'block';
        } catch (error) {
            console.error(error);
            alert('An error occurred while processing the file. Please try again.');
        }
    });
});
