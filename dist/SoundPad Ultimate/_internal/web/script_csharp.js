// Navigation
function navigate(pageId, navItem) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active-page'));
    document.getElementById('page-' + pageId).classList.add('active-page');

    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    navItem.classList.add('active');
}

// Theme Handling
function changeTheme(themeName) {
    document.body.setAttribute('data-theme', themeName);
    if (window.chrome?.webview?.hostObjects?.backend) {
        window.chrome.webview.hostObjects.backend.SaveTheme(themeName);
    }
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
function toggleEngine() {
    isEngineOn = !isEngineOn;
    const btn = document.getElementById('enginePill');
    btn.classList.toggle('on');

    const text = document.getElementById('engineText');
    text.innerText = isEngineOn ? 'ENGINE ON' : 'ENGINE OFF';

    if (window.chrome?.webview?.hostObjects?.backend) {
        window.chrome.webview.hostObjects.backend.ToggleEngine(isEngineOn);
    }

    if (isEngineOn) {
        showToast("Engine de Áudio Iniciada!", "success");
    } else {
        showToast("Engine Desligada.", "error");
    }
}

// Load Sounds from Backend
async function loadSounds() {
    try {
        if (window.chrome?.webview?.hostObjects?.backend) {
            const soundsStr = await window.chrome.webview.hostObjects.backend.GetSounds();
            allSounds = JSON.parse(soundsStr);
            renderSounds(allSounds);
        }
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
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div class="title" style="flex:1;">${title}</div>
                <div class="dropdown">
                    <button class="btn-dots" onclick="toggleDropdown(this, event)">⋮</button>
                    <div class="dropdown-content">
                        <a href="#" onclick="renameSound('${sound.file}')">✏️ Renomear</a>
                        <a href="#" class="delete-btn" onclick="deleteSound('${sound.file}')">🗑️ Excluir</a>
                    </div>
                </div>
            </div>
            <div class="shortcut">${sound.shortcut ? sound.shortcut.toUpperCase() : 'SEM ATALHO'}</div>
            <div class="card-actions">
                <button class="btn-play">▶ Play</button>
                <button class="btn-bind">Bind</button>
            </div>
        `;

        card.querySelector('.btn-play').addEventListener('click', (e) => {
            e.stopPropagation();
            if (window.chrome?.webview?.hostObjects?.backend) {
                window.chrome.webview.hostObjects.backend.PlaySound(sound.file);
            }
        });

        bindBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            bindBtn.innerText = "Pressione...";
            bindBtn.style.color = "var(--accent)";

            let new_key = await window.listenForKey();

            if (window.chrome?.webview?.hostObjects?.backend) {
                window.chrome.webview.hostObjects.backend.SaveHotkey(sound.file, new_key);
            }
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

window.renameSound = async function (oldFile) {
    const newName = prompt("Digite o novo nome:", oldFile.replace('.mp3', ''));
    if (newName && newName.trim() !== "") {
        if (window.chrome?.webview?.hostObjects?.backend) {
            window.chrome.webview.hostObjects.backend.RenameSound(oldFile, newName.trim());
            loadSounds();
            showToast("Som renomeado!", "success");
        }
    }
};

window.deleteSound = async function (file) {
    if (confirm("Tem certeza que deseja excluir " + file + "?")) {
        if (window.chrome?.webview?.hostObjects?.backend) {
            window.chrome.webview.hostObjects.backend.DeleteSound(file);
            loadSounds();
            showToast("Som excluído!", "success");
        }
    }
};

window.toggleDropdown = function (element, e) {
    e.stopPropagation();
    document.querySelectorAll('.dropdown-content').forEach(d => {
        if (d !== element.nextElementSibling) d.classList.remove('show');
    });
    element.nextElementSibling.classList.toggle('show');
};

window.onclick = function (e) {
    if (!e.target.matches('.btn-dots')) {
        document.querySelectorAll('.dropdown-content').forEach(d => d.classList.remove('show'));
    }
};

window.listenForKey = function () {
    return new Promise(resolve => {
        const handler = (evt) => {
            evt.preventDefault();
            window.removeEventListener('keydown', handler);
            let k = evt.code.replace('Key', '').replace('Digit', '').replace('Numpad', 'NumPad');
            if (evt.code === 'Space') k = 'Space';
            if (evt.code === 'Escape') k = 'Esc';
            resolve(k);
        };
        window.addEventListener('keydown', handler);
    });
};

// Modals
function openAddModal() {
    document.getElementById('addModal').style.display = 'flex';
}

function closeAddModal() {
    document.getElementById('addModal').style.display = 'none';
    document.getElementById('myinstantsLink').value = '';
}

async function downloadMyInstants() {
    const link = document.getElementById('myinstantsLink').value;
    if (!link) return;

    const btn = document.querySelector('#addModal .btn-primary');
    btn.innerText = "Baixando...";
    btn.disabled = true;

    showToast("Baixando e processando áudio...", "warning");

    let success = false;
    try {
        if (window.chrome?.webview?.hostObjects?.backend) {
            success = await window.chrome.webview.hostObjects.backend.DownloadSound(link);
        }
    } catch (e) {
        console.error(e);
    }

    btn.innerText = "Adicionar";
    btn.disabled = false;

    if (success) {
        closeAddModal();
        document.getElementById('soundUrl').value = '';
        loadSounds();
        showToast("Download Concluído!", "success");
    } else {
        showToast("Falha ao baixar MP3", "error");
    }
}

// Settings
async function loadSettings() {
    if (!window.chrome?.webview?.hostObjects?.backend) return;
    const settingsStr = await window.chrome.webview.hostObjects.backend.GetSettings();
    const settings = JSON.parse(settingsStr);

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

    populate('micSelect', settings.input_devices, 'mic');
    populate('cableSelect', settings.output_devices, 'cable');
    populate('phoneSelect', settings.output_devices, 'phone');

    const killBtn = document.getElementById('killSwitchBtn');
    if (killBtn) killBtn.innerText = settings.kill_switch.toUpperCase() || "NENHUM";

    const micListenCheck = document.getElementById('micListenCheck');
    if (micListenCheck) micListenCheck.checked = settings.listen_mic;

    const volMic = document.getElementById('vol_mic');
    if (volMic) { volMic.value = settings.vol_mic; document.getElementById('val_vol_mic').innerText = Math.round(settings.vol_mic * 100) + '%'; }

    const volDiscord = document.getElementById('vol_discord');
    if (volDiscord) { volDiscord.value = settings.vol_discord; document.getElementById('val_vol_discord').innerText = Math.round(settings.vol_discord * 100) + '%'; }

    const volMe = document.getElementById('vol_me');
    if (volMe) { volMe.value = settings.vol_me; document.getElementById('val_vol_me').innerText = Math.round(settings.vol_me * 100) + '%'; }

    if (settings.theme) {
        const themeSel = document.getElementById('themeSelector');
        if (themeSel) themeSel.value = settings.theme;
        changeTheme(settings.theme);
    }

    // Initialize Sliders coloring on load
    updateVolumes();
}

function saveDevice(type, value) {
    if (!value) return;
    if (window.chrome?.webview?.hostObjects?.backend) {
        window.chrome.webview.hostObjects.backend.SaveDevice(type, value);
    }
    showToast("Dispositivo alterado.", "success");
}

function toggleMicListen(enabled) {
    if (window.chrome?.webview?.hostObjects?.backend) {
        window.chrome.webview.hostObjects.backend.ToggleMicListen(enabled);
    }
    showToast(enabled ? "Retorno Ligado" : "Retorno Desligado", enabled ? "success" : "error");
}

window.updateVolumes = function () {
    const micElem = document.getElementById('vol_mic');
    const discordElem = document.getElementById('vol_discord');
    const meElem = document.getElementById('vol_me');

    if (!micElem || !discordElem || !meElem) return;

    const mic = parseFloat(micElem.value);
    const discord = parseFloat(discordElem.value);
    const me = parseFloat(meElem.value);

    // Update Text Labels
    document.getElementById('val_vol_mic') ? document.getElementById('val_vol_mic').innerText = Math.round(mic * 100) + '%' : null;
    document.getElementById('val_vol_discord') ? document.getElementById('val_vol_discord').innerText = Math.round(discord * 100) + '%' : null;
    document.getElementById('val_vol_me') ? document.getElementById('val_vol_me').innerText = Math.round(me * 100) + '%' : null;

    // Dynamically color the sliders (0 to 2 range -> 0% to 100%)
    const setSliderBg = (elem) => {
        const percentage = (elem.value / elem.max) * 100;
        elem.style.background = `linear-gradient(to right, var(--accent) ${percentage}%, var(--border) ${percentage}%)`;
    };

    setSliderBg(micElem);
    setSliderBg(discordElem);
    setSliderBg(meElem);

    if (window.chrome?.webview?.hostObjects?.backend) {
        window.chrome.webview.hostObjects.backend.SetVolumes(mic, discord, me);
    }
};

async function bindKillSwitch(btn) {
    btn.innerText = "Pressione...";
    btn.style.color = "var(--accent)";

    let new_key = await window.listenForKey();

    if (window.chrome?.webview?.hostObjects?.backend) {
        window.chrome.webview.hostObjects.backend.SaveKillswitch(new_key);
    }

    btn.innerText = new_key ? new_key.toUpperCase() : "NENHUM";
    btn.style.color = "";
    showToast("Kill Switch atualizado!", "success");
}

// Window init
window.onload = () => {
    loadSounds();
    loadSettings();
};
