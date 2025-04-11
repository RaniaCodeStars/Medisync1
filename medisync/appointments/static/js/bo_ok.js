document.addEventListener("DOMContentLoaded", function () {
    const doctorId = getDoctorId();

    if (doctorId) {
        console.log(`ID du médecin confirmé : ${doctorId}`);
        fetchConsultationReasons(doctorId);

        // Initialiser le calendrier
        initCalendar(doctorId);

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

/** Récupérer les motifs de consultation depuis l'API */
function fetchConsultationReasons(doctorId) {
    fetch(`http://127.0.0.1:8000/appointments/api/get-consultation-reasons/${doctorId}/`)
        .then(response => {
            if (!response.ok) throw new Error(`Erreur HTTP : ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log("Réponse des motifs de consultation :", data);
            // Si le médecin n'a défini aucun motif, on masque le quiz et on affiche directement le calendrier
            if (data.has_reasons === false) {
                // Masquer la section quiz
                const quizContainer = document.getElementById("quiz");
                if (quizContainer) {
                    quizContainer.style.display = "none";
                }
                // Afficher le conteneur du calendrier
                const calendrierContainer = document.querySelector(".calendrier-container");
                if (calendrierContainer) {
                    calendrierContainer.style.display = "block";
                }
            } else {
                // Afficher la liste des motifs de consultation pour que l'utilisateur puisse faire son choix.
                // On modifie ici la valeur de l'input pour qu'elle soit l'ID du motif.
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

            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                const dateObj = new Date(dateStr);

                const dayDiv = document.createElement("div");
                dayDiv.className = "day";
                dayDiv.textContent = day;

                // Appliquer les règles de délais
                if (dateObj < minimumDelay || dateObj > maximumDelay) {
                    dayDiv.classList.add("non-working-day");
                    dayDiv.style.pointerEvents = "none";
                } else {
                    const isAvailable = availableDates.find(d => d.date === dateStr);
                    if (isAvailable) {
                        dayDiv.classList.add(isAvailable.is_specific ? "specific-day" : "working-day");
                        dayDiv.addEventListener("click", () => showHours(dateStr));
                    } else {
                        dayDiv.classList.add("non-working-day");
                        dayDiv.style.pointerEvents = "none";
                    }
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
    let url = `/appointments/api/get-available-times/?date=${date}&doctor_id=${doctorId}`;
    if (selectedReasonId) {
        url += `&consultation_reason_id=${selectedReasonId}`;
    }
    console.log("URL utilisée pour récupérer les heures :", url);
    
    const hoursDiv = document.getElementById("hours");
    if (!hoursDiv) {
        console.error("L'élément #hours est introuvable dans le DOM.");
        return;
    }
    
    hoursDiv.style.display = "block";
    hoursDiv.innerHTML = `<h3>Heures disponibles pour le ${formattedDate}</h3>`;
    
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
            available_times.forEach(time => {
                const hourBtn = document.createElement("button");
                hourBtn.classList.add("hour-btn");
                hourBtn.textContent = time;
                hourBtn.addEventListener("click", () => {
                    document.querySelectorAll(".hour-btn").forEach(btn => btn.classList.remove("selected"));
                    hourBtn.classList.add("selected");
                    const selectedSlot = `Le ${formattedDate} à ${time}`;
                    console.log(`Créneau sélectionné : ${selectedSlot}`);
                    document.getElementById("selected-slot").innerHTML = `<strong>Créneau sélectionné :</strong> ${selectedSlot}`;
                    const confirmButton = document.getElementById("confirm-slot-btn");
                    confirmButton.style.display = "block";
                });
                hoursDiv.appendChild(hourBtn);
            });
        })
        .catch(err => {
            console.error("Erreur lors de la récupération des heures :", err);
            hoursDiv.innerHTML += `<p>Erreur lors de la récupération des heures : ${err.message}</p>`;
        });
}

/** Fonction appelée lorsque l'utilisateur soumet le quiz */
function handleSubmit() {
    const selectedAnswer = getSelectedAnswer();
    if (!selectedAnswer) {
        alert("Veuillez sélectionner un motif avant de continuer.");
        return;
    }
    console.log("Motif sélectionné :", selectedAnswer);
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
    quizContainer.style.display = "none";
    calendrierContainer.style.display = "block";
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
