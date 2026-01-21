// Globale variabele om de speler in op te slaan
let player = null;

document.addEventListener("DOMContentLoaded", function() {
    console.log("Tractor Monitor JS geladen!");

    const tabLinks = document.querySelectorAll('.tab-link');
    const startBtn = document.getElementById('start-stream-btn');

    // --- Tab Navigatie Logica ---
    tabLinks.forEach(button => {
        button.addEventListener('click', function() {
            const targetTabId = this.getAttribute('data-tab');
            
            // Reset actieve statussen
            tabLinks.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Activeer de gekozen tab
            this.classList.add('active');
            document.getElementById(targetTabId).classList.add('active');

            // --- NIEUW: STREAM STARTEN/STOPPEN BIJ TAB WISSEL ---
            if (targetTabId === 'stream-tab') {
                console.log("Camera tab geopend, stream starten...");
                startStream();
            } else {
                 console.log("Weg van camera tab, stream stoppen om data te besparen.");
                 stopStream();
            }
        });
    });

    // Knop voor handmatig starten
    if (startBtn) {
        startBtn.addEventListener('click', startStream);
    }
});

// --- Functie om de JSMpeg speler te starten ---
function startStream() {
    // Als er al een speler draait, doe niks
    if (player) {
        console.log("Stream draait al.");
        return;
    }

    const canvas = document.getElementById('video-canvas');
    // LET OP: Vervang 'localhost' door het IP van je PC als je op je telefoon test!
    // Bijv: 'ws://192.168.178.23:8080'
    // Voor nu op dezelfde PC werkt localhost prima.
    const streamUrl = 'ws://' + window.location.hostname + ':8080';

    console.log("Verbinden met stream server op:", streamUrl);

    // Maak de JSMpeg speler aan
    player = new JSMpeg.Player(streamUrl, {
        canvas: canvas, // Vertel hem op welk canvas hij moet tekenen
        autoplay: true, // Probeer direct te starten
        audio: false,   // Geen audio nodig
        loop: true      // Blijf proberen te verbinden
    });
}

// --- Functie om de speler te stoppen (bespaart data/CPU) ---
function stopStream() {
    if (player) {
        console.log("Stream stoppen.");
        player.destroy(); // Vernietig de speler instantie
        player = null;    // Reset de variabele
    }
}