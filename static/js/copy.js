document.addEventListener('DOMContentLoaded', () => {
    const dialogueBox = document.querySelector('#dialogue-box');
    if (dialogueBox) {
        dialogueBox.addEventListener('click', (event) => {
            const copyIcon = event.target.closest('.copy-icon');
            if (copyIcon) {
                const text = copyIcon.dataset.copyText;
                if (text) {
                    copyToClipboard(text, copyIcon);
                }
            }
        });
    }
});

function copyToClipboard(text, element) {
    console.log('Attempting to copy:', text);
    try {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                console.log('Copy successful');
                element.classList.add('copied');
                element.textContent = '✅';
                setTimeout(() => {
                    element.classList.remove('copied');
                    element.textContent = '📋';
                }, 2000);
            }).catch(err => {
                console.error('Copy failed:', err);
                fallbackCopy(text, element);
            });
        } else {
            fallbackCopy(text, element);
        }
    } catch (err) {
        console.error('Clipboard API error:', err);
        alert('Clipboard access failed.');
    }
}

function fallbackCopy(text, element) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        console.log('Fallback copy successful');
        element.classList.add('copied');
        element.textContent = '✅';
        setTimeout(() => {
            element.classList.remove('copied');
            element.textContent = '📋';
        }, 2000);
    } catch (err) {
        console.error('Fallback copy failed:', err);
        alert('Failed to copy text.');
    }
    document.body.removeChild(textarea);
}