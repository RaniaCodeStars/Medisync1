document.addEventListener("DOMContentLoaded", function () {
    const menuOpenButton = document.querySelector("#menu-open-button");
    const menuCloseButton = document.querySelector("#menu-close-button");
    const readMoreButton = document.getElementById("read-more-btn");
    const fullText = document.getElementById("full-text");
    const mainNav = document.querySelector(".main-nav");

    if (menuOpenButton && menuCloseButton) {
        menuOpenButton.addEventListener("click", () => {
            document.body.classList.toggle("show-mobile-menu");
            // Ajout pour cacher/afficher la nav principale
            if (mainNav) {
                mainNav.style.display = document.body.classList.contains("show-mobile-menu") 
                    ? "none" 
                    : "block";
            }
        });

        menuCloseButton.addEventListener("click", () => {
            document.body.classList.remove("show-mobile-menu");
            // Réafficher la nav principale
            if (mainNav) {
                mainNav.style.display = "block";
            }
        });
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





























































document.addEventListener("DOMContentLoaded", function () {
    var shortText = document.getElementById("short-text");
    var fullText = document.getElementById("more-text");
    var button = document.getElementById("toggle-btn");

    button.addEventListener("click", function () {
        if (fullText.style.display === "none") {
            fullText.style.display = "inline"; // Afficher le reste du texte
            button.textContent = "▴ Voir moins";
        } else {
            shortText.style.display = "inline"; // Réafficher le texte court
            fullText.style.display = "none"; // Cacher le reste du texte
            button.textContent = "▾ Voir plus";
        }
    });
});





































document.addEventListener("DOMContentLoaded", function () {
    // Récupération de l'ID de la clinique à partir de Django
    const clinicId = "{{ clinic.id }}"; // S'assurer que clinic.id est disponible dans le template

    if (!clinicId) {
        console.error("Erreur : l'ID de la clinique est introuvable.");
        return;
    }

    // Appel AJAX pour récupérer les horaires de la clinique
    fetch(`/clinic/${clinicId}/horaires/`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Erreur lors de la récupération des horaires.");
            }
            return response.json();
        })
        .then(data => {
            const todayContainer = document.querySelector(".week-container");
            const moreTextContainer = document.getElementById("more-text2");

            // Vérification si les conteneurs existent
            if (!todayContainer || !moreTextContainer) {
                console.error("Erreur : les conteneurs d'affichage des horaires sont introuvables.");
                return;
            }

            // Vider les conteneurs pour éviter les doublons
            todayContainer.innerHTML = "";
            moreTextContainer.innerHTML = "";

            // Affichage des horaires d'aujourd'hui
            if (data.today_hours.length > 0) {
                data.today_hours.forEach(hour => {
                    todayContainer.innerHTML += `<div class="day-box">${hour.opening} - ${hour.closing}</div>`;
                });
            } else {
                todayContainer.innerHTML = "<p>Aucun horaire disponible aujourd'hui.</p>";
            }

            // Affichage des horaires des autres jours
            if (Object.keys(data.other_days_hours).length > 0) {
                for (const [day, hours] of Object.entries(data.other_days_hours)) {
                    let dayLabel = `<label class="jours">${day}: `;
                    let hoursText = hours.map(h => `${h.opening} - ${h.closing}`).join(", ");
                    moreTextContainer.innerHTML += `${dayLabel} ${hoursText}</label><br>`;
                }
            } else {
                moreTextContainer.innerHTML = "<p>Aucun horaire disponible pour les autres jours.</p>";
            }
        })
        .catch(error => console.error("Erreur lors du chargement des horaires:", error));
});

// Fonction pour afficher/masquer les horaires des autres jours
function toggleText2() {
    var moreText = document.getElementById("more-text2");
    if (moreText.style.display === "none" || moreText.style.display === "") {
        moreText.style.display = "block";
    } else {
        moreText.style.display = "none";
    }
}












































function toggleText2() {
    const moreText = document.getElementById('more-text2');
    const btn = event.target; // Le bouton cliqué
    
    if (moreText.style.display === "none") {
        moreText.style.display = "inline"; // "block" fonctionne mieux que "inline" pour les div
        btn.textContent = "▴ Voir moins";
    } else {
        moreText.style.display = "none";
        btn.textContent = "▾ Voir plus";
    }
}



















