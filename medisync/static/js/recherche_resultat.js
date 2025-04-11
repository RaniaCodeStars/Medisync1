document.addEventListener("DOMContentLoaded", function () {
    const menuOpenButton = document.querySelector("#menu-open-button");
    const menuCloseButton = document.querySelector("#menu-close-button");
    const readMoreButton = document.getElementById("read-more-btn");
    const fullText = document.getElementById("full-text");

    if (menuOpenButton && menuCloseButton) {
        menuOpenButton.addEventListener("click", () => {
            document.body.classList.toggle("show-mobile-menu");
        });

        menuCloseButton.addEventListener("click", () => menuOpenButton.click());
    }

    if (readMoreButton && fullText) {
        readMoreButton.addEventListener("click", function () {
            if (fullText.style.display === "none" || fullText.style.display === "") {
                fullText.style.display = "block";
                setTimeout(() => (fullText.style.opacity = "1"), 100);
                readMoreButton.textContent = "Lire moins";
            } else {
                fullText.style.opacity = "0";
                setTimeout(() => (fullText.style.display = "none"), 500);
                readMoreButton.textContent = "Lire plus";
            }
        });
    }
});





/*document.addEventListener('DOMContentLoaded', function() {
    // Sélectionner tous les calendriers
    document.querySelectorAll('.doctor-calendar div[id^="calendar-"]').forEach((calendarEl) => {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'timeGridWeek'
            },
            locale: 'fr',
            slotMinTime: '08:00:00',
            slotMaxTime: '20:00:00',
            slotDuration: '01:00:00',
            allDaySlot: false,
            events: [
                {
                    title: '09:00 - 12:00\n14:00 - 17:00',
                    start: '2024-03-25',
                    display: 'background',
                    color: '#f0f0f0',
                    textColor: '#000',
                    allDay: true
                }
            ],
            eventContent: function(arg) {
                return {
                    html: `<div style="padding: 5px; text-align: center;">${arg.event.title}</div>`
                };
            }
        });

        calendar.render();
    });
});

*/


/*Maps*/
var map = L.map('map').setView([36.7525, 3.0419], 7); // Centré sur l'Algérie

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

var markers = {};  // Dictionnaire pour stocker les marqueurs

// Fonction pour afficher la localisation du médecin
function showDoctorLocation(element) {
    var lat = parseFloat(element.getAttribute('data-lat'));
    var lng = parseFloat(element.getAttribute('data-lng'));
    var name = element.getAttribute('data-name');

    if (!isNaN(lat) && !isNaN(lng)) {
        // Vérifier si un marqueur existe déjà pour ce médecin
        if (!markers[name]) {
            // Créer un nouveau marqueur s'il n'existe pas
            markers[name] = L.marker([lat, lng])
                .bindPopup(`<b>${name}</b>`)
                .addTo(map);
        }

        // Zoom sur la localisation du médecin
        map.setView([lat, lng], 12);
        markers[name].openPopup(); // Ouvrir le popup
    } else {
        console.warn(`❌ Erreur: coordonnées invalides pour ${name}`);
    }
}

// Ajouter les marqueurs initiaux pour chaque médecin
document.querySelectorAll('.doctor-info').forEach(function(item) {
    var lat = parseFloat(item.getAttribute('data-lat'));
    var lng = parseFloat(item.getAttribute('data-lng'));
    var name = item.getAttribute('data-name');

    if (!isNaN(lat) && !isNaN(lng)) {
        markers[name] = L.marker([lat, lng])
            .bindPopup(`<b>${name}</b>`)
            .addTo(map);
    }
});





document.addEventListener("DOMContentLoaded", function() {
    // Initialisation de la carte globale
    var map = L.map('map').setView([36.7525, 3.0419], 7); // Centré sur l'Algérie

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    var markers = {}; // Dictionnaire pour stocker les marqueurs

    // Fonction pour afficher la localisation de la clinique
    function showClinicLocation(element) {
        var lat = parseFloat(element.getAttribute('data-lat'));
        var lng = parseFloat(element.getAttribute('data-lng'));
        var name = element.getAttribute('data-name');

        if (!isNaN(lat) && !isNaN(lng)) {
            // Vérifier si un marqueur existe déjà pour cette clinique
            if (!markers[name]) {
                // Créer un nouveau marqueur s'il n'existe pas
                markers[name] = L.marker([lat, lng])
                    .bindPopup(`<b>${name}</b>`)
                    .addTo(map);
            }

            // Zoom sur la localisation de la clinique
            map.setView([lat, lng], 12);
            markers[name].openPopup(); // Ouvrir le popup
        } else {
            console.warn(`❌ Erreur: coordonnées invalides pour ${name}`);
        }
    }

    // Ajouter les marqueurs initiaux pour chaque clinique
    document.querySelectorAll('.clinic-card').forEach(function(item) {
        var lat = parseFloat(item.getAttribute('data-lat'));
        var lng = parseFloat(item.getAttribute('data-lng'));
        var name = item.getAttribute('data-name');

        if (!isNaN(lat) && !isNaN(lng)) {
            markers[name] = L.marker([lat, lng])
                .bindPopup(`<b>${name}</b>`)
                .addTo(map);
        }
    });
});


/*Button clinic medcin  */

document.addEventListener("DOMContentLoaded", function () {
    const doctorButton = document.querySelector(".doct");
    const clinicButton = document.querySelector(".clin");
    const doctorSection = document.querySelector(".list-doctor");
    const clinicSection = document.querySelector(".list-clinic");

    if (doctorSection && clinicSection) {
        // Afficher les médecins par défaut et cacher les cliniques
        doctorSection.style.display = "block";
        clinicSection.style.display = "none";

        // Ajouter une classe active au bouton sélectionné
        doctorButton.classList.add("active");

        doctorButton.addEventListener("click", function () {
            doctorSection.style.display = "block";
            clinicSection.style.display = "none";
            doctorButton.classList.add("active");
            clinicButton.classList.remove("active");
        });

        clinicButton.addEventListener("click", function () {
            doctorSection.style.display = "none";
            clinicSection.style.display = "block";
            clinicButton.classList.add("active");
            doctorButton.classList.remove("active");
        });
    }
});







/*avtover localisation */

document.querySelector(".location-button").addEventListener("click", function () {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                // Remplir le champ avec "Votre localisation"
                document.querySelector(".location-input").value = "Votre localisation";
            },
            (error) => {
                alert("Erreur de localisation : Vérifiez les permissions ou activez la localisation.");
            }
        );
    } else {
        alert("La géolocalisation n'est pas supportée par votre navigateur.");
    }
});

// Fonction pour convertir les coordonnées GPS en adresse (utilise une API comme OpenCage ou Google Maps)
function convertCoordinatesToAddress(lat, lng) {
    const apiKey = "VOTRE_CLE_API"; // Remplace avec ta clé API (Google Maps, OpenCage, etc.)
    const url = `https://api.opencagedata.com/geocode/v1/json?q=${lat}+${lng}&key=${apiKey}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.results.length > 0) {
                document.querySelector(".location-input").value = data.results[0].formatted;
            }
        })
        .catch(error => console.error("Erreur lors de la conversion de l'adresse :", error));
}






/*telechargement de photo */