document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle
    const themeSwitcher = document.querySelector('.theme-switcher');
    const body = document.body;

    if (themeSwitcher && body) {
        if (!localStorage.getItem('theme')) {
            body.classList.add('dark-theme');
            themeSwitcher.textContent = '🌓';
            localStorage.setItem('theme', 'dark');
        } else if (localStorage.getItem('theme') === 'light') {
            body.classList.remove('dark-theme');
            themeSwitcher.textContent = '🌙';
        } else {
            body.classList.add('dark-theme');
            themeSwitcher.textContent = '🌓';
        }

        themeSwitcher.addEventListener('click', () => {
            if (body.classList.contains('dark-theme')) {
                body.classList.remove('dark-theme');
                themeSwitcher.textContent = '🌙';
                localStorage.setItem('theme', 'light');
            } else {
                body.classList.add('dark-theme');
                themeSwitcher.textContent = '🌓';
                localStorage.setItem('theme', 'dark');
            }
            console.log('Theme toggled to:', localStorage.getItem('theme'));
        });
    } else {
        console.error('Theme switcher or body element not found');
    }

    // Nav Toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('open');
            console.log('Nav menu toggled:', navMenu.classList.contains('active'));
        });
    } else {
        console.error('Nav toggle or menu element not found');
    }

    // Tab Switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    if (tabButtons.length && tabContents.length) {
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));

                button.classList.add('active');
                const tabId = button.dataset.tab;
                const tabContent = document.querySelector(`#${tabId}`);
                if (tabContent) {
                    tabContent.classList.add('active');
                    console.log(`Switched to tab: ${tabId}`);
                } else {
                    console.error(`Tab content with ID ${tabId} not found`);
                }
            });
        });
    } else {
        console.error('Tab buttons or contents not found');
    }

    // Contact Owner Toggle
    const contactOwnerLink = document.querySelector('.contact-owner');
    const contactOptions = document.querySelector('.contact-options');

    if (contactOwnerLink && contactOptions) {
        contactOwnerLink.addEventListener('click', (e) => {
            e.preventDefault();
            const isVisible = contactOptions.classList.contains('visible');
            contactOptions.classList.toggle('visible', !isVisible);
            console.log('Contact options toggled:', contactOptions.classList.contains('visible'));
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!contactOwnerLink.contains(e.target) && !contactOptions.contains(e.target)) {
                contactOptions.classList.remove('visible');
            }
        });

        contactOptions.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', (e) => {
                console.log('Contact sub-option clicked:', link.textContent);
            });
        });
    } else {
        console.error('Contact owner or options element not found');
    }

    // Delete Unit with Secret Key
    const deleteButtons = document.querySelectorAll('.delete-unit-btn');

    if (deleteButtons.length) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault(); // Prevent default confirmation dialog
                const unitId = button.dataset.unitId;
                const unitName = button.closest('.unit-header').querySelector('h3').textContent;

                // Prompt for confirmation
                if (!confirm(`Are you sure you want to delete ${unitName}?`)) {
                    return;
                }

                // Prompt for secret key
                const secretKey = prompt('Enter the secret key to delete this unit:');
                if (!secretKey) {
                    alert('Secret key is required.');
                    console.log('Unit deletion cancelled: No secret key provided');
                    return;
                }

                // Send deletion request
                fetch('/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: `delete_unit_id=${encodeURIComponent(unitId)}&secret_key=${encodeURIComponent(secretKey)}`
                })
                .then(response => response.text())
                .then(() => {
                    // Reload page to reflect changes
                    window.location.reload();
                })
                .catch(err => {
                    console.error('Error deleting unit:', err);
                    alert('Failed to delete unit. Please try again.');
                });
            });
        });
        console.log('Delete unit buttons initialized');
    } else {
        console.error('No delete unit buttons found');
    }

    // Notes Search
    const searchInput = document.querySelector('#notes-search');
    const searchBtn = document.querySelector('.search-btn');

    if (searchInput && searchBtn) {
        searchInput.addEventListener('input', filterNotes);
        searchBtn.addEventListener('click', filterNotes);
        console.log('Notes search initialized');
    } else {
        console.error('Search input or button not found');
    }

    function filterNotes() {
        const query = searchInput.value.toLowerCase();
        document.querySelectorAll('.unit').forEach(unit => {
            const unitName = unit.querySelector('h3').textContent.toLowerCase();
            const materials = unit.querySelectorAll('.material-name');
            let match = unitName.includes(query);
            materials.forEach(material => {
                if (material.textContent.toLowerCase().includes(query)) match = true;
            });
            unit.style.display = match ? 'block' : 'none';
        });
        console.log('Notes filtered with query:', query);
    }

    // Simplify Form Validation
    const simplifyForm = document.querySelector('#simplifyForm');
    if (simplifyForm) {
        simplifyForm.addEventListener('submit', function(event) {
            const keywords = document.querySelector('#keywords').value.trim();
            const fileInput = document.querySelector('#pdf_file').files[0];

            if (!keywords) {
                event.preventDefault();
                alert('No keywords?');
                return;
            }

            if (!fileInput || !fileInput.name.toLowerCase().endswith('.pdf')) {
                event.preventDefault();
                alert('Upload a PDF file.');
                return;
            }

            console.log('Form submitting to: ' + this.action);
            document.getElementById('debugOutput').textContent = 'Submitting to: ' + this.action;
        });
    } else {
        console.error('Simplify form not found');
    }

    // Countdown Timer
    document.querySelectorAll('.countdown').forEach(span => {
        const dueDate = span.dataset.due;
        if (dueDate) {
            const due = new Date(dueDate.split('/').reverse().join('-'));
            function updateCountdown() {
                const now = new Date();
                const diff = due - now;
                if (diff <= 0) {
                    span.textContent = 'Expired';
                    span.style.color = 'var(--error-color)';
                } else {
                    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                    span.textContent = `${days}d ${hours}h ${minutes}m`;
                }
            }
            updateCountdown();
            setInterval(updateCountdown, 60000);
            console.log('Countdown initialized for due date:', dueDate);
        }
    });

    // Chaos Meter
    const chaosScore = document.querySelector('.chaos-score');
    const meterFill = document.querySelector('.meter-fill');

    if (chaosScore && meterFill) {
        function updateChaosMeter() {
            const count = document.querySelectorAll('.assignment-item').length;
            const percent = count <= 5 ? count * 20 : 100;
            const tag = count <= 1 ? 'Calm' : count <= 2 ? 'Stirring' : count <= 4 ? 'Frenzy' : 'Chaos';
            const color = count <= 1 ? '#00FF7F' : count <= 2 ? '#FFFF00' : count <= 4 ? '#FFA500' : '#FF4444';
            chaosScore.textContent = tag;
            chaosScore.style.color = color;
            meterFill.style.width = `${percent}%`;
            meterFill.style.background = color;
            console.log('Chaos meter updated:', { count, tag, percent });
        }
        updateChaosMeter();
    }

    // Socket.IO Chat (Only for ai_chat.html)
    const dialogueBox = document.getElementById('dialogue-box');
    const form = document.querySelector('form');
    const questionInput = document.getElementById('question');
    if (dialogueBox && form && questionInput) {
        const socket = io.connect('http://localhost:5100', { transports: ['polling'] });

        socket.on('connect', () => {
            console.log('Connected to Socket.IO');
        });

        socket.on('ai_response', (data) => {
            console.log('AI Response:', data.msg);
            const message = document.createElement('p');
            message.innerHTML = `<strong>AI:</strong> ${data.msg}`;
            dialogueBox.appendChild(message);
            dialogueBox.scrollTop = dialogueBox.scrollHeight;
        });

        socket.on('error', (err) => {
            console.error('Socket.IO Error:', err);
        });

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const question = questionInput.value.trim();
            const file = fileInput.files[0];

            if (question && !file) {
                const userMessage = document.createElement('p');
                userMessage.textContent = `You: ${question}`;
                dialogueBox.appendChild(userMessage);
                dialogueBox.scrollTop = dialogueBox.scrollHeight;
                socket.emit('ai_message', { 'msg': question });
                questionInput.value = '';
            } else if (file || (question && file)) {
                const formData = new FormData(form);
                fetch('/ai_chat', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.text())
                .then(() => {
                    const userMessage = document.createElement('p');
                    userMessage.textContent = `You: ${question || 'File upload'}`;
                    dialogueBox.appendChild(userMessage);
                    dialogueBox.scrollTop = dialogueBox.scrollHeight;
                    questionInput.value = '';
                    fileInput.value = '';
                })
                .catch(err => console.error('Fetch error:', err));
            }
        });
        console.log('Socket.IO initialized for AI chat');
    } else {
        console.error('Dialogue box or form not found');
    }

    // Dynamic Unit Fields for Group Setup
    const addUnitBtn = document.querySelector('.add-unit-btn');
    const unitsContainer = document.querySelector('#units-container');

    if (addUnitBtn && unitsContainer) {
        addUnitBtn.addEventListener('click', () => {
            const unitCount = unitsContainer.querySelectorAll('option').length;
            const newFieldset = document.createElement('fieldset');
            newFieldset.className = 'unit-fieldset';
            newFieldset.innerHTML = `
                <legend>Unit ${unitCount + 1}</legend>
                <div class="form-group">
                    <label for="unit-name-${unitCount}">Unit Name:</label>
                    <input type="text" id="unit-name-${unitCount}" name="units[]" required>
                </div>
                <div class="form-group">
                    <label for="lecturer-name-${unitCount}">Lecturer:</label>
                    <input type="text" id="lecturer-name-${unitCount}" name="lecturers[]">
                </div>
                <div class="form-group">
                    <label for="phone-number-${unitCount}">Phone:</label>
                    <input type="tel" id="phone-number-${unitCount}" name="phones[]">
                </div>
                <div class="form-group">
                    <label for="email-id-${unitCount}">Email:</label>
                    <input type="email" id="email-id-${unitCount}" name="emails[]">
                </div>
                <button type="button" class="remove-unit-btn">Remove</button>
            `;
            unitsContainer.appendChild(newFieldset);

            // Add handler for remove button
            newFieldset.querySelector('.remove-unit-btn').addEventListener('click', () => {
                newFieldset.remove();
                console.log('Unit fieldset removed');
            });

            console.log('New unit fieldset added');
        });
        console.log('Dynamic unit fields initialized');
    } else {
        console.error('Add unit button or units container not found');
    }
});