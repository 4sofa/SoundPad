// Navigation
function navigateTo(pageId, navItem) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active-page'));
    document.getElementById(pageId).classList.add('active-page');

    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    navItem.classList.add('active');
}

// Theme Handling
function changeTheme(themeName) {
    document.body.setAttribute('data-theme', themeName);
    eel.save_theme(themeName)();
}

// Toast Notifications
function showToast(message, type = "success") {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.borderLeftColor = type === 'error' ? '#ef4444' : 'var(--accent)';
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// Global Variables
let isEngineOn = false;
let allSounds = [];

// Engine Toggle
document.getElementById('engineToggle').addEventListener('click', function () {
    isEngineOn = !isEngineOn;
    this.classList.toggle('on');

    const text = this.querySelector('.engine-text');
    text.innerText = isEngineOn ? 'ENGINE ON' : 'ENGINE OFF';

    eel.toggle_engine(isEngineOn)();

    if (isEngineOn) {
        showToast("Engine de Áudio Iniciada!", "success");
    } else {
        showToast("Engine Desligada.", "error");
    }
});

// Load Sounds from Backend
async function loadSounds() {
    try {
        allSounds = await eel.get_sounds()();
        renderSounds(allSounds);
    } catch (err) {
        console.error("Failed to load sounds:", err);
    }
}

// Render Sounds Grid
function renderSounds(soundsArray) {
    const grid = document.getElementById('soundsGrid');
    grid.innerHTML = '';

    soundsArray.forEach(sound => {
        const title = sound.file.replace('.mp3', '').replace(/-/g, ' ').toUpperCase().substring(0, 20);
        const card = document.createElement('div');
        card.className = 'sound-card';
        card.innerHTML = `
            <div class="title">${title}</div>
            <div class="shortcut">${sound.shortcut ? sound.shortcut.toUpperCase() : 'SEM ATALHO'}</div>
            <div class="card-actions">
                <button class="btn-play">▶ Play</button>
                <button class="btn-bind">Bind</button>
            </div>
        `;

        card.querySelector('.btn-play').addEventListener('click', (e) => {
            e.stopPropagation();
            eel.play_sound(sound.file)();
        });

        const bindBtn = card.querySelector('.btn-bind');
        bindBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            bindBtn.innerText = "Pressione...";
            bindBtn.style.color = "var(--accent)";
            const new_key = await eel.bind_hotkey(sound.file)();
            card.querySelector('.shortcut').innerText = new_key ? new_key.toUpperCase() : 'SEM ATALHO';
            bindBtn.innerText = "Bind";
            bindBtn.style.color = "";
            showToast("Atalho salvo!", "success");
        });

        grid.appendChild(card);
    });
}

// Search Filter
document.getElementById('searchInput').addEventListener('keyup', (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = allSounds.filter(s => s.file.toLowerCase().includes(term));
    renderSounds(filtered);
});

// Modals
function openAddModal() {
    document.getElementById('addModal').style.display = 'flex';
}

function closeAddModal() {
    document.getElementById('addModal').style.display = 'none';
    document.getElementById('addLinkInput').value = '';
}

async function downloadSound() {
    const link = document.getElementById('addLinkInput').value;
    if (!link) return;

    const btn = document.getElementById('downloadBtn');
    const originalText = btn.innerText;
    btn.innerText = "Baixando...";
    btn.disabled = true;

    const success = await eel.download_sound(link)();

    btn.innerText = originalText;
    btn.disabled = false;

    if (success) {
        closeAddModal();
        loadSounds();
        showToast("Download Concluído!", "success");
    } else {
        showToast("Falha ao baixar MP3", "error");
    }
}

// Settings
async function loadSettings() {
    const settings = await eel.get_settings()();

    const populate = (id, list, selected) => {
        const select = document.getElementById(id);
        if (!select) return;
        select.innerHTML = '';
        list.forEach(item => {
            const opt = document.createElement('option');
            opt.value = opt.innerText = item;
            if (settings[selected] && item.includes(settings[selected])) opt.selected = true;
            select.appendChild(opt);
        });
    }

    populate('micSelect', settings.devices, 'mic');
    populate('cableSelect', settings.devices, 'cable');
    populate('phoneSelect', settings.devices, 'phone');

    const killBtn = document.getElementById('killSwitchBtn');
    if (killBtn) killBtn.innerText = settings.kill_switch.toUpperCase() || "NENHUM";

    if (settings.theme) {
        const themeSel = document.getElementById('themeSelector');
        if (themeSel) themeSel.value = settings.theme;
        changeTheme(settings.theme);
    }
}

function saveDevice(type, value) {
    if (!value) return;
    eel.save_device(type, value)();
    showToast("Dispositivo alterado.", "success");
}

async function bindKillSwitch(btn) {
    btn.innerText = "Pressione...";
    btn.style.color = "var(--accent)";
    const new_key = await eel.bind_killswitch()();
    btn.innerText = new_key ? new_key.toUpperCase() : "NENHUM";
    btn.style.color = "";
    showToast("Kill Switch atualizado!", "success");
}

// Window init
window.onload = () => {
    loadSounds();
    loadSettings();
};
