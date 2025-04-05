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

    // Navbar Toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        navToggle.classList.toggle('open');
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

    // Countdown Timers
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
        setInterval(updateCountdown, 60000); // Update every minute
    });

    // Chaos Meter (Tied to Assignments)
    const chaosScore = document.querySelector('.chaos-score');
    const meterFill = document.querySelector('.meter-fill');
    function updateChaosMeter() {
        const count = document.querySelectorAll('.assignment-item').length;
        const percent = count <= 5 ? count * 20 : 100;
        const tag = count <= 1 ? 'Calm' : count === 2 ? 'Stirring' : count === 4 ? 'Frenzy' : 'Chaos';
        const color = count <= 1 ? '#00FF7F' : count === 2 ? '#FFFF00' : count === 4 ? '#FFA500' : '#FF4444';
        chaosScore.textContent = tag;
        chaosScore.style.color = color;
        meterFill.style.width = `${percent}%`;
        meterFill.style.background = color;
    }
    updateChaosMeter(); // Initial call
});