document.addEventListener("DOMContentLoaded", function () {
    const doctorId = getDoctorId();

    if (doctorId) {
        console.log(`ID du médecin confirmé : ${doctorId}`);
        fetchConsultationReasons(doctorId);

        // Initialiser le calendrier
        initCalendar(doctorId);

        checkOnlineConsultationSupport(doctorId);

        const submitBtn = document.getElementById("submit");
        submitBtn.addEventListener("click", handleSubmit);
    } else {
        showFatalError(`
            <h3>Erreur technique</h3>
            <p>Nous n'avons pas pu identifier le médecin.</p>
            <div class="debug-info" style="display:none">
                <p>URL : ${window.location.href}</p>
                <p>Chemin : ${window.location.pathname}</p>
            </div>
            <button onclick="location.href='/'" class="btn">Retour à l'accueil</button>
            <button onclick="document.querySelector('.debug-info').style.display='block'" class="btn">
                Afficher les détails
            </button>
        `);
    }
});

document.getElementById("urgence-checkbox").addEventListener("change", function (e) {
    document.getElementById("urgence-details").style.display =
        e.target.checked ? "block" : "none";

    // Désélectionne les motifs si urgence cochée
    if (e.target.checked) {
        document.querySelectorAll('input[name="answer"]').forEach(el => el.checked = false);
    }
});

// Désélectionne l'urgence si un motif est choisi
document.querySelectorAll('input[name="answer"]').forEach(radio => {
    radio.addEventListener("change", function () {
        if (this.checked) {
            document.getElementById("urgence-checkbox").checked = false;
            document.getElementById("urgence-details").style.display = "none";
        }
    });
});

/** Fonction ultra-robuste pour récupérer l'ID du médecin */
function getDoctorId() {
    const methods = [
        () => {
            const match = window.location.pathname.match(/book\/(\d+)\/?$/);
            return match ? match[1] : null;
        },
        () => new URLSearchParams(window.location.search).get('doctor_id'),
        () => {
            const el = document.querySelector('[data-doctor-id]');
            return el ? el.dataset.doctorId : null;
        }
    ];

    for (const method of methods) {
        try {
            const id = method();
            if (id && /^\d+$/.test(id)) {
                console.log("ID trouvé via :", method.name, id);
                return id;
            }
        } catch (e) {
            console.warn("Erreur avec", method.name, e);
        }
    }
    console.warn("Aucune source d'ID trouvée.");
    return null;
}

function getSelectedAnswer() {
    const selected = document.querySelector('input[name="answer"]:checked');
    return selected ? selected.value : null;
}

/** Récupérer les motifs de consultation depuis l'API */
function fetchConsultationReasons(doctorId) {
    fetch(`http://127.0.0.1:8000/appointments/api/get-consultation-reasons/${doctorId}/`)
        .then(response => {
            if (!response.ok) throw new Error(`Erreur HTTP : ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log("Réponse des motifs de consultation :", data);
            const normalDiv = document.getElementById("normal");

            if (data.has_reasons === false || data.consultation_reasons.length === 0) {
                // Aucun motif défini → Afficher seulement "Consultation normale" + Urgence
                document.getElementById("quiz-options").innerHTML = "";
                normalDiv.style.display = "block";
            } else {
                // Motifs définis → Afficher uniquement les motifs + Urgence
                normalDiv.style.display = "none";
                afficherConsultationReasons(data.consultation_reasons);
            }
        })
        .catch(err => console.error("Erreur lors de la récupération des motifs :", err));
}


/** Afficher la liste des motifs de consultation dans le quiz */
function afficherConsultationReasons(reasons) {
    const quizOptions = document.getElementById("quiz-options");
    if (reasons.length === 0) {
        quizOptions.innerHTML = "<p>Aucun motif de consultation disponible.</p>";
        return;
    }
    quizOptions.innerHTML = "";
    reasons.forEach(reason => {
        const li = document.createElement("li");
        li.innerHTML = `
            <input type="radio" name="answer" id="option_${reason.id}" class="answer" value="${reason.id}">
            <label for="option_${reason.id}">${reason.name}</label>
        `;
        quizOptions.appendChild(li);
    });
}

function initCalendar(doctorId) {
    const today = new Date();
    let currentMonth = today.getMonth();
    let currentYear = today.getFullYear();

    const prevBtn = document.getElementById("prev-btn");
    const nextBtn = document.getElementById("next-btn");


    // Associer les événements de clic pour navigation
    prevBtn.addEventListener("click", () => changeMonth(-1));
    nextBtn.addEventListener("click", () => changeMonth(1));

    displayMonth(currentYear, currentMonth, doctorId);

    /** Fonction pour changer le mois visible */
    function changeMonth(offset) {
        const newMonth = currentMonth + offset;
        if (newMonth < 0) {
            currentMonth = 11; // Décembre
            currentYear--;
        } else if (newMonth > 11) {
            currentMonth = 0; // Janvier
            currentYear++;
        } else {
            currentMonth = newMonth;
        }
        displayMonth(currentYear, currentMonth, doctorId);
    }
}


/** Nouvelle fonction pour récupérer les disponibilités */
function fetchAvailableDates(doctorId) {
    const url = `http://127.0.0.1:8000/appointments/api/get-combined-available-dates/${doctorId}/`;

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error(`Erreur HTTP : ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log("Réponse complète de l'API : ", data);
            const dates = data.available_dates || [];

            if (dates.length === 0) {
                console.warn("Aucune disponibilité configurée pour ce médecin");
                showNoAvailabilityMessage();
                return;
            }

            displayMonth(dates);
        })
        .catch(err => {
            console.error("Erreur lors de la récupération des disponibilités :", err);
        });
}


/** Fonction d'affichage des dates du calendrier */
function displayMonth(year, month, doctorId) {
    const calendarDiv = document.getElementById("calendar");
    if (!calendarDiv) return;

    // Mettre à jour le titre du calendrier
    const titleElement = document.querySelector(".call-title");
    const monthName = new Date(year, month).toLocaleString("fr-FR", { month: "long", year: "numeric" });
    if (titleElement) {
        titleElement.textContent = `Calendrier Medcin de ${monthName}:`; // Met à jour le titre avec le mois/année actuel
    }

    calendarDiv.innerHTML = ""; // Effacer le contenu précédent


    const daysInMonth = new Date(year, month + 1, 0).getDate(); // Nombre de jours dans le mois
    const today = new Date();
    const minimumDelay = new Date(today.getTime() + 24 * 60 * 60 * 1000); // 24 heures minimum
    const maximumDelay = new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000); // 90 jours maximum

    fetch(`http://127.0.0.1:8000/appointments/api/get-combined-available-dates/${doctorId}/`)
        .then(response => {
            if (!response.ok) throw new Error(`Erreur HTTP : ${response.status}`);
            return response.json();
        })
        .then(data => {
            const availableDates = data.available_dates || [];
            const isUrgence = document.getElementById("urgence-checkbox").checked;

            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                const dateObj = new Date(dateStr);
                const dayAvailability = availableDates.find(d => d.date === dateStr);

                const dayDiv = document.createElement("div");
                dayDiv.className = "day";
                dayDiv.textContent = day;

                if (dateObj < minimumDelay || dateObj > maximumDelay) {
                    dayDiv.classList.add("non-working-day");
                    dayDiv.style.pointerEvents = "none";
                } else if (dayAvailability) {
                    if (isUrgence) {
                        // Mode Urgence : seulement les créneaux d'urgence
                        if (dayAvailability.has_emergency) {
                            dayDiv.classList.add("urgence-day");
                            dayDiv.addEventListener("click", () => showHours(dateStr));
                        } else {
                            dayDiv.classList.add("non-working-day");
                            dayDiv.style.pointerEvents = "none";
                        }
                    } else {
                        // Mode Normal : 
                        // - Affiche si disponibilité spécifique OU hebdomadaire non-urgente
                        // - Vérifie que has_non_emergency est true
                        if (dayAvailability.is_specific || dayAvailability.has_non_emergency) {
                            dayDiv.classList.add(dayAvailability.is_specific ? "specific-day" : "working-day");
                            dayDiv.addEventListener("click", () => showHours(dateStr));
                        } else {
                            dayDiv.classList.add("non-working-day");
                            dayDiv.style.pointerEvents = "none";
                        }
                    }
                } else {
                    dayDiv.classList.add("non-working-day");
                    dayDiv.style.pointerEvents = "none";
                }

                calendarDiv.appendChild(dayDiv);
            }
        })
        .catch(err => console.error("Erreur lors de la récupération des disponibilités :", err));
}

function showErrorInCalendar(errorMessage) {
    const calendarDiv = document.getElementById("calendar");
    if (!calendarDiv) return;

    calendarDiv.innerHTML = `<p style="color: red;">Erreur : ${errorMessage}</p>`;
}


/** Fonction pour afficher les heures disponibles pour une date sélectionnée */
function showHours(date) {
    const isUrgence = document.getElementById("urgence-checkbox").checked;
    console.log(`Tentative d'affichage des heures pour la date : ${date}`);

    const doctorId = getDoctorId();
    if (!doctorId) {
        console.error("Aucun ID de médecin obtenu.");
        return;
    }
    console.log(`Utilisation de l'ID du médecin : ${doctorId}`);
    // Reformatage de la date
    const dateObj = new Date(date);
    const options = { weekday: "long", day: "numeric", month: "long", year: "numeric" };
    const formattedDate = dateObj.toLocaleDateString("fr-FR", options);

    // On récupère l'ID du motif sélectionné (s'il existe)
    const selectedReasonId = getSelectedAnswer();
    let url = `/appointments/api/get-available-times/?date=${date}&doctor_id=${doctorId}&is_emergency=${isUrgence}`;
    if (!isUrgence && selectedReasonId) {
        url += `&consultation_reason_id=${selectedReasonId}`;
    }
    console.log("URL utilisée pour récupérer les heures :", url);

    const hoursDiv = document.getElementById("hours");
    if (!hoursDiv) {
        console.error("L'élément #hours est introuvable dans le DOM.");
        return;
    }

    hoursDiv.style.display = "block";
    hoursDiv.innerHTML = `<h3>${isUrgence ? 'Créneaux d\'urgence' : 'Créneaux disponibles'} pour le ${formattedDate}</h3>`;

    fetch(url)
        .then(response => {
            console.log("Réponse du fetch pour get-available-times :", response);
            if (!response.ok) {
                throw new Error(`Erreur lors de la récupération des heures : ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Données reçues de l'API pour les heures :", data);
            const { available_times } = data;
            if (!available_times || available_times.length === 0) {
                hoursDiv.innerHTML += "<p>Aucune heure disponible.</p>";
                return;
            }
            data.available_times.forEach(time => {
                const hourBtn = document.createElement("button");
                hourBtn.className = isUrgence ? "hour-btn emergency-slot" : "hour-btn";
                hourBtn.classList.add("hour-btn");
                hourBtn.textContent = time;
                hourBtn.addEventListener("click", () => {
                    // ▼▼▼ DÉSÉLECTIONNE LES AUTRES BOUTONS ▼▼▼
                    document.querySelectorAll(".hour-btn").forEach(btn => btn.classList.remove("selected"));
                    hourBtn.classList.add("selected");

                    // ▼▼▼ FORMATAGE DATE/HEURE POUR DJANGO ▼▼▼
                    const dateObj = new Date(date);
                    const formattedDate = dateObj.toISOString().split('T')[0]; // "2024-05-20"
                    // Dans la fonction showHours > hourBtn.addEventListener("click", () => {
                    const formattedTime = time.includes('h')
                        ? time.replace('h', ':')
                        : time.slice(0, 2) + time.slice(2); // Gère "14h30" et "1430"
                    // ▼▼▼ AFFICHAGE DU CRÉNEAU SELECTIONNÉ ▼▼▼
                    const selectedSlotText = `Le ${dateObj.toLocaleDateString('fr-FR')} à ${formattedTime}`;
                    document.getElementById("selected-slot").innerHTML = `<strong>Créneau sélectionné :</strong> ${selectedSlotText}`;
                    document.getElementById("confirm-slot-btn").style.display = "block";

                    // ▼▼▼ STOCKAGE POUR L'ENVOI ▼▼▼
                    window.selectedSlot = {
                        doctorId: getDoctorId(),
                        date: formattedDate,      // Format Django : "AAAA-MM-JJ"
                        time: formattedTime,     // Format Django : "HH:MM"
                        isUrgence: document.getElementById("urgence-checkbox").checked,
                        urgencyDetails: document.getElementById("urgence-raison").value,
                        reasonId: getSelectedAnswer() // Récupère l'ID du motif sélectionné
                    };

                });
                hoursDiv.appendChild(hourBtn);
            });
        })
        .catch(err => {
            console.error("Erreur lors de la récupération des heures :", err);
            hoursDiv.innerHTML += `<p>Erreur lors de la récupération des heures : ${err.message}</p>`;
        });
}



document.getElementById("confirm-slot-btn").addEventListener("click", function () {
    if (!window.selectedSlot) {
        alert("Veuillez sélectionner un créneau horaire !");
        return;
    }
    afficherFormulaireRendezVous(); // ◀◀◀ Affiche le modal
});


/** Fonction appelée lorsque l'utilisateur soumet le quiz */
function handleSubmit() {
    const isUrgence = document.getElementById("urgence-checkbox").checked;
    const urgenceDetails = isUrgence ? document.getElementById("urgence-raison").value : null;
    const selectedReason = getSelectedAnswer();
    const isNormalConsultation = document.getElementById("normal-checkbox").checked;

    // Validation
    if (!selectedReason && !isUrgence && !isNormalConsultation) {
        alert("Veuillez choisir un motif, cocher 'urgence', ou sélectionner 'consultation normale'.");
        return;
    }
    if (isUrgence && !urgenceDetails) {
        alert("Veuillez décrire votre urgence");
        return;
    }

    // Stockage des données
    window.bookingData = {
        isUrgence,
        urgenceDetails,
        motifId: selectedReason,
        isNormalConsultation
    };

    afficherCalendrier();
}

/** Fonction de récupération de l'ID du motif sélectionné */
function getSelectedAnswer() {
    const answers = document.querySelectorAll(".answer");
    let selectedAnswer = null;
    answers.forEach(answer => {
        if (answer.checked) selectedAnswer = answer.value;
    });
    return selectedAnswer;
}

/** Fonction pour masquer le quiz et afficher le calendrier */
function afficherCalendrier() {
    const quizContainer = document.getElementById("quiz");
    const calendrierContainer = document.querySelector(".calendrier-container");
    const navBtns = document.querySelector(".calendar-navigation");


    quizContainer.style.display = "none";
    calendrierContainer.style.display = "block";

    if (navBtns) {
        navBtns.style.display = "block"; // ou "block" selon ton CSS
    }
}

/** Fonction pour afficher une erreur fatale */
function showFatalError(content) {
    const container = document.getElementById('appointment-container') || document.body;
    container.innerHTML = `
        <div class="error-screen">
            <div class="error-content">
                ${content}
            </div>
        </div>
    `;
}

document.getElementById("urgence-checkbox").addEventListener("change", function (e) {
    document.getElementById("urgence-details").style.display =
        e.target.checked ? "block" : "none";

    if (e.target.checked) {
        document.querySelectorAll('input[name="answer"]').forEach(el => el.checked = false);
    }

    // 🔁 Mettre à jour le calendrier avec le bon mode
    const doctorId = getDoctorId();
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    displayMonth(currentYear, currentMonth, doctorId);
});

async function getDoctorName(doctorId) {
    const response = await fetch(`/api/doctors/${doctorId}/`);
    const data = await response.json();
    return `${data.doctor.nom} ${data.doctor.prenom}`;
}

// Affiche la modal de confirmation
// Dans la fonction afficherFormulaireRendezVous()
function afficherFormulaireRendezVous() {
    const modal = document.getElementById('confirmation-modal');
    const selected = window.selectedSlot;
    const doctorName = document.body.dataset.doctorName;

    // Remplir les infos de base
    document.getElementById('confirmation-doctor').textContent = doctorName;
    document.getElementById('confirmation-date').textContent = new Date(selected.date).toLocaleDateString('fr-FR');
    document.getElementById('confirmation-time').textContent = selected.time;

    // Masquer tous les champs optionnels d'abord
    document.getElementById('confirmation-type').parentElement.style.display = 'none';
    document.getElementById('confirmation-reason').style.display = 'none';
    document.getElementById('confirmation-emergency').style.display = 'none';

    if (selected.isUrgence) {
        // Cas urgence - afficher seulement l'urgence
        document.getElementById('confirmation-type').parentElement.style.display = 'block';
        document.getElementById('confirmation-type').textContent = "Urgence 🚨";
        document.getElementById('confirmation-emergency').style.display = 'block';
        document.getElementById('confirmation-emergency-text').textContent = selected.urgencyDetails;
    } 
    else if (selected.reasonId) {
        // Cas motif spécifique - afficher seulement le motif
        document.getElementById('confirmation-reason').style.display = 'block';
        
        // Récupérer le texte du motif
        const selectedRadio = document.querySelector(`input[name="answer"][value="${selected.reasonId}"]`);
        if (selectedRadio) {
            const reasonLabel = selectedRadio.nextElementSibling;
            document.getElementById('confirmation-reason-text').textContent = reasonLabel.textContent.trim();
        }
    }
    else {
        // Cas consultation normale - afficher seulement le type
        document.getElementById('confirmation-type').parentElement.style.display = 'block';
        document.getElementById('confirmation-type').textContent = "Consultation normale";
    }

    modal.style.display = 'block';
}

// Gestion de la fermeture de la modal
document.querySelector('.close-modal').addEventListener('click', () => {
    document.getElementById('confirmation-modal').style.display = 'none';
});

document.getElementById("final-confirmation-btn").addEventListener("click", async () => {
    try {
        if (!window.selectedSlot) {
            alert("Aucun créneau sélectionné !");
            return;
        }

        // ▼▼▼ Validation minimale côté client ▼▼▼
        if (window.selectedSlot.isUrgence && !window.selectedSlot.urgencyDetails) {
            alert("Veuillez décrire l'urgence.");
            return;
        }

        // ▼▼▼ Envoi des données ▼▼▼
        const response = await fetch('/confirm-appointment/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify({
                doctor_id: window.selectedSlot.doctorId,
                date: window.selectedSlot.date,
                time: window.selectedSlot.time,
                is_urgence: window.selectedSlot.isUrgence,
                urgence_details: window.selectedSlot.urgencyDetails || '',
                reason_id: window.selectedSlot.reasonId || null
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur serveur");
        }

        window.location.href = `/appointments/confirmation/${data.appointment_id}/`;

    } catch (error) {

    }
});



function checkOnlineConsultationSupport(doctorId) {
    console.log("Vérification support en ligne pour le médecin :", doctorId);

    fetch(`http://127.0.0.1:8000/appointments/api/get-doctor-info/${doctorId}/`, {
        credentials: 'include', // ✅ Pour envoyer les cookies (session)
        headers: {
            'X-CSRFToken': getCookie('csrftoken'), // ✅ Si la vue Django nécessite le token CSRF
        }
    })
    .then(response => {
        if (!response.ok) throw new Error("Erreur lors de la récupération du médecin");
        return response.json();
    })
    .then(data => {
        console.log("Réponse API médecin :", data);
        const acceptsOnline = data.accept_online_appointments;

        const onlineCheckbox = document.getElementById("online-checkbox");
        const fixedText = document.getElementById("consultation-fixed-text");

        if (!onlineCheckbox || !fixedText) {
            console.warn("Les éléments du DOM pour la consultation en ligne sont introuvables.");
            return;
        }
        const onlineCheckboxDiv = onlineCheckbox.parentElement.parentElement;

        if (acceptsOnline) {
            onlineCheckboxDiv.style.display = "block";
            fixedText.style.display = "none";
        } else {
            onlineCheckboxDiv.style.display = "none";
            fixedText.style.display = "block";
        }
    })
    .catch(err => {
        console.error("Erreur en vérifiant la prise en charge en ligne :", err);
    });
}




// ▼▼▲▲ NOUVEAU CODE À AJOUTER ▲▲▼▼ (à la fin de rrrrr.js)
document.getElementById("final-confirmation-btn").addEventListener("click", async () => {
    try {
        const selected = window.selectedSlot;
        const isOnline = document.getElementById("online-checkbox").checked;
        const notes = document.getElementById('appointment-notes').value;


        // ▼▼▼ Validation supplémentaire ▼▼▼
        if (!selected.time.match(/^\d{1,2}:\d{2}$/)) {
            alert("Format d'heure invalide. Utilisez HH:MM.");
            return;
        }

        // ▼▼▼ Envoi avec CSRF ▼▼▼
        const response = await fetch('/appointments/confirm-appointment/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // Correction ici
            },
            credentials: 'include',
            body: JSON.stringify({
                doctor_id: selected.doctorId,
                date: selected.date,
                time: selected.time.replace('h', ':'), // Force le format HH:MM
                is_urgence: selected.isUrgence,
                urgence_details: selected.urgencyDetails || '',
                reason_id: selected.reasonId || null,
                is_online: isOnline, // ◀◀◀ Ajout du statut en ligne
                notes: notes
            })
        });

        // ▼▼▼ Gestion des erreurs ▼▼▼
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Erreur serveur");
        }

        const data = await response.json();
        const modalContent = document.querySelector('#confirmation-modal .modal-content');
        modalContent.innerHTML = `
            <h2 class="success-title">✅ Rendez‑vous confirmé</h2>
            <p class="success-message">Votre rendez‑vous a bien été réservé avec succès.</p>
            <button id="close-success-btn" class="btn-close-success">Fermer</button>
        `;
        // Afficher la modal (au cas où elle aurait été cachée)
        document.getElementById('confirmation-modal').style.display = 'block';

        // Gestion du bouton “Fermer”
        document.getElementById('close-success-btn').addEventListener('click', () => {
            document.getElementById('confirmation-modal').style.display = 'none';
            // Optionnel : tu peux recharger le calendrier ou la page
            // location.reload();
        });


    } catch (error) {
        console.error('Erreur:', error);
        alert(`Échec : ${error.message}`);
    }
});

// Fonction utilitaire pour récupérer le cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}