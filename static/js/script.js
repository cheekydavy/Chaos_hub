// Mock Database
let groupData = JSON.parse(localStorage.getItem('groupData')) || { members: [], units: [], timetable: null, deadlines: [], notices: [], emails: [] };
let isAdmin = false;
let adminPhone = '';

document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Setup
    const themeSwitcher = document.querySelector('.theme-switcher');
    const body = document.body;

    // Set dark mode as default if no theme saved
    if (!localStorage.getItem('theme')) {
        body.classList.add('dark-theme');
        themeSwitcher.textContent = '🌓'; // Sun for light mode
        localStorage.setItem('theme', 'dark');
    } else if (localStorage.getItem('theme') === 'light') {
        body.classList.remove('dark-theme');
        themeSwitcher.textContent = '🌙'; // Moon for dark mode
    } else {
        body.classList.add('dark-theme');
        themeSwitcher.textContent = '🌓'; // Sun for light mode
    }

    // Toggle theme on click
    themeSwitcher.addEventListener('click', () => {
        if (body.classList.contains('dark-theme')) {
            body.classList.remove('dark-theme');
            themeSwitcher.textContent = '🌙'; // Moon for dark mode
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.add('dark-theme');
            themeSwitcher.textContent = '🌓'; // Sun for light mode
            localStorage.setItem('theme', 'dark');
        }
    });

    // Login Handling
    const loginForm = document.querySelector('#login-form');
    const loginModal = document.querySelector('#login-modal');
    const joinModal = document.querySelector('#join-modal');
    const joinForm = document.querySelector('#join-form');
    const adminPanel = document.querySelector('#admin-panel');

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.querySelector('#username').value;
        const password = document.querySelector('#password').value;
        adminPhone = document.querySelector('#phone').value;
        const groupName = document.querySelector('#group-name').value;
        
        if (username && password) {
            isAdmin = true;
            const key = Math.random().toString(36).substring(2, 15);
            groupData.groupKey = key;
            groupData.admin = username;
            groupData.groupName = groupName;
            localStorage.setItem('groupData', JSON.stringify(groupData));
            document.querySelector('#key-value').textContent = key;
            document.querySelector('#group-key').style.display = 'block';
            loginModal.style.display = 'none';
            adminPanel.style.display = 'block';
            updateUI();
        }
    });

    // Join Group
    joinForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const key = document.querySelector('#join-key').value;
        if (key === groupData.groupKey) {
            groupData.members.push(`User${Math.floor(Math.random() * 1000)}`);
            localStorage.setItem('groupData', JSON.stringify(groupData));
            joinModal.style.display = 'none';
            updateUI();
        }
    });

    // Unit Input
    const unitForm = document.querySelector('#unit-form');
    unitForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const unitName = document.querySelector('#unit-name').value;
        groupData.units.push({ name: unitName, notes: [] });
        localStorage.setItem('groupData', JSON.stringify(groupData));
        updateUnits();
    });

    // Timetable Upload
    const timetableForm = document.querySelector('#timetable-form');
    timetableForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const file = document.querySelector('#timetable-file').files[0];
        groupData.timetable = { name: file.name, date: new Date().toLocaleDateString() };
        localStorage.setItem('groupData', JSON.stringify(groupData));
        updateTimetable();
    });

    // Deadline Input with Mask
    const deadlineForm = document.querySelector('#deadline-form');
    const taskDateInput = document.querySelector('#task-date');
    
    // Simple date mask (dd/mm/yyyy)
    taskDateInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 2) value = value.slice(0, 2) + '/' + value.slice(2);
        if (value.length > 5) value = value.slice(0, 5) + '/' + value.slice(5, 9);
        e.target.value = value.slice(0, 10);
    });

    deadlineForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const taskName = document.querySelector('#task-name').value;
        const taskDate = document.querySelector('#task-date').value;
        if (/^\d{2}\/\d{2}\/\d{4}$/.test(taskDate)) {
            groupData.deadlines.push({ name: taskName, date: taskDate });
            localStorage.setItem('groupData', JSON.stringify(groupData));
            updateDeadlines();
            deadlineForm.reset();
        } else {
            alert('Date must be in dd/mm/yyyy format!');
        }
    });

    // Notice Input
    const noticeForm = document.querySelector('#notice-form');
    noticeForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const title = document.querySelector('#notice-title').value;
        const text = document.querySelector('#notice-text').value;
        groupData.notices.push({ title, text, date: new Date().toLocaleDateString() });
        localStorage.setItem('groupData', JSON.stringify(groupData));
        updateNotices();
    });

    // Email Input
    const emailForm = document.querySelector('#email-form');
    emailForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = document.querySelector('#email-name').value;
        const address = document.querySelector('#email-address').value;
        groupData.emails.push({ name, address });
        localStorage.setItem('groupData', JSON.stringify(groupData));
        updateEmails();
    });

    // Update UI Functions
    function updateUnits() {
        const container = document.querySelector('.units-container');
        container.innerHTML = '';
        groupData.units.forEach((unit, index) => {
            const div = document.createElement('div');
            div.className = 'unit';
            div.innerHTML = `
                <h3>${unit.name}</h3>
                <div class="unit-materials">
                    ${unit.notes.map(note => `
                        <div class="material-item">
                            <span class="material-name">${note.name}</span>
                            <a href="#" class="grab-link" data-index="${index}" data-note="${note.name}">PDF</a>
                        </div>
                    `).join('')}
                    ${isAdmin ? `<input type="file" class="note-upload" data-unit="${index}">` : ''}
                </div>
            `;
            container.appendChild(div);
        });

        document.querySelectorAll('.note-upload').forEach(upload => {
            upload.addEventListener('change', (e) => {
                const unitIndex = e.target.dataset.unit;
                const file = e.target.files[0];
                groupData.units[unitIndex].notes.push({ name: file.name });
                localStorage.setItem('groupData', JSON.stringify(groupData));
                updateUnits();
            });
        });
    }

    function updateTimetable() {
        const upload = document.querySelector('#timetable-upload');
        upload.innerHTML = groupData.timetable ? `
            <p>Latest Schedule:</p>
            <a href="#" class="doc-link">${groupData.timetable.name}</a>
            <p class="upload-date">Updated: ${groupData.timetable.date}</p>
        ` : '';
    }

    function updateDeadlines() {
        const list = document.querySelector('.assignment-list');
        list.innerHTML = '';
        groupData.deadlines.forEach((deadline, index) => {
            const diffDays = Math.ceil((new Date(deadline.date.split('/').reverse().join('-')) - new Date()) / (1000 * 60 * 60 * 24));
            const item = document.createElement('div');
            item.className = 'assignment-item';
            item.innerHTML = `
                <h3>${deadline.name}</h3>
                <p>Drops: ${deadline.date}</p>
                <p>Fuse: <span class="days-left">${diffDays}</span> days</p>
                <button class="defuse-btn">Defused</button>
                ${isAdmin ? `<button class="remove-btn" data-index="${index}">Remove</button>` : ''}
            `;
            list.appendChild(item);
        });

        document.querySelectorAll('.defuse-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.closest('.assignment-item').style.opacity = '0.5';
                btn.textContent = 'Done';
                btn.disabled = true;
            });
        });

        document.querySelectorAll('.remove-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const index = btn.dataset.index;
                groupData.deadlines.splice(index, 1);
                localStorage.setItem('groupData', JSON.stringify(groupData));
                updateDeadlines();
            });
        });
    }

    function updateNotices() {
        const feed = document.querySelector('.notice-feed');
        feed.innerHTML = '';
        groupData.notices.forEach(notice => {
            feed.innerHTML += `
                <article class="notice-item">
                    <h3>${notice.title}</h3>
                    <p>${notice.text}</p>
                    <span class="notice-stamp">${notice.date}</span>
                </article>
            `;
        });
    }

    function updateEmails() {
        const dropdown = document.querySelector('#email-dropdown');
        dropdown.innerHTML = '<option value="">Select Email</option>';
        groupData.emails.forEach(email => {
            dropdown.innerHTML += `<option value="${email.address}">${email.name}</option>`;
        });
    }

    function updateUI() {
        document.querySelector('#admin-phone').textContent = isAdmin ? adminPhone : groupData.adminPhone || '';
        const memberList = document.querySelector('#member-list');
        memberList.innerHTML = '';
        groupData.members.forEach(member => {
            memberList.innerHTML += `<li>${member}${member === groupData.admin ? ' (Admin)' : ''}</li>`;
        });
        updateUnits();
        updateTimetable();
        updateDeadlines();
        updateNotices();
        updateEmails();
    }

    // Navbar Toggle for Mobile
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
    });

    // Notes Search
    const searchInput = document.querySelector('#notes-search');
    const searchBtn = document.querySelector('.search-btn');
    searchInput.addEventListener('input', filterNotes);
    searchBtn.addEventListener('click', filterNotes);

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

    // Chaos Meter (Tied to Deadlines)
    const chaosScore = document.querySelector('.chaos-score');
    const meterFill = document.querySelector('.meter-fill');
    function updateChaosMeter() {
        const count = groupData.deadlines.length;
        const percent = count <= 5 ? count * 20 : 100;
        const tag = count <= 1 ? 'Calm' : count === 2 ? 'Stirring' : count === 4 ? 'Frenzy' : 'Chaos';
        const color = count <= 1 ? '#00FF7F' : count === 2 ? '#FFFF00' : count === 4 ? '#FFA500' : '#FF4444';
        chaosScore.textContent = tag;
        chaosScore.style.color = color;
        meterFill.style.width = `${percent}%`;
        meterFill.style.background = color;
    }
    updateChaosMeter(); // Initial call
    // Call this in updateDeadlines too (already hooked)

    // Show Modals Initially
    loginModal.style.display = 'block';
    joinModal.style.display = 'block';
});