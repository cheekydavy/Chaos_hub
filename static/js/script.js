document.addEventListener('DOMContentLoaded', () => {
    const themeSwitcher = document.querySelector('.theme-switcher');
    const body = document.body;

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
    });

    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('open');
        });
    }

    const searchInput = document.querySelector('#notes-search');
    const searchBtn = document.querySelector('.search-btn');

    if (searchInput && searchBtn) {
        searchInput.addEventListener('input', filterNotes);
        searchBtn.addEventListener('click', filterNotes);
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
    }

    document.querySelectorAll('.countdown').forEach(span => {
        const dueDate = span.dataset.due;
        const due = new Date(dueDate.split('/').reverse().join('-'));
        function updateCountdown() {
            const now = new Date();
            const diff = due - now;
            if (diff <= 0) {
                span.textContent = 'Expired';
                span.style.color = '#FF4444';
            } else {
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                span.textContent = `${days}d ${hours}h ${minutes}m`;
            }
        }
        updateCountdown();
        setInterval(updateCountdown, 60000);
    });

    const chaosScore = document.querySelector('.chaos-score');
    const meterFill = document.querySelector('.meter-fill');

    if (chaosScore && meterFill) {
        function updateChaosMeter() {
            const count = document.querySelectorAll('.assignment-item').length;
            const percent = count <= 5 ? count * 20 : 100;
            const tag = count <= 1 ? 'Calm' : count === 2 ? 'Not-Bad' : count === 4 ? 'Stirring' : 'Chaos';
            const color = count <= 1 ? '#00FF7F' : count === 2 ? '#FFFF00' : count === 4 ? '#FFA500' : '#FF4444';
            chaosScore.textContent = tag;
            chaosScore.style.color = color;
            meterFill.style.width = `${percent}%`;
            meterFill.style.background = color;
        }
        updateChaosMeter();
    }

    const socket = io.connect('http://127.0.0.1:5000', { transports: ['polling'] });
    const dialogueBox = document.getElementById('dialogue-box');
    const form = document.querySelector('form');
    const questionInput = document.getElementById('question');
    const fileInput = document.getElementById('file');

    if (dialogueBox && form && questionInput && fileInput) {
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
                socket.emit('ai_message', {'msg': question});
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
    } else {
        console.error('Chat elements not found—check ai_chat.html');
    }
});