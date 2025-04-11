document.addEventListener('DOMContentLoaded', function () {
    // Sélection des éléments HTML
    const calendarEl = document.getElementById('calendar');
    const timeList = document.getElementById('time-list');
    const availableTimesSection = document.getElementById('available-times');
    const reservationModal = document.getElementById('reservationModal');
    const selectedDateDisplay = document.getElementById('selected-date-display');
    const selectedDateInput = document.getElementById('formDate');
    const selectedTimeInput = document.getElementById('formTime');
    const selectedDateElement = document.getElementById("selectedDate");
    const selectedTimeElement = document.getElementById("selectedTime");
    const consultationReasonSelect = document.getElementById("consultation-reason");

    // Vérification du chargement des disponibilités transmises via Django
    console.log("Disponibilités chargées :", availabilities);

    // Initialisation du calendrier FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth', // Vue par défaut : affichage mensuel
        events: availabilities.map(availability => ({
            title: availability.is_active ? "Disponible" : "Indisponible",
            start: availability.date,
            allDay: true,
            color: availability.is_active ? "blue" : "grey" // Bleu si actif, gris sinon
        })),
        dateClick: function (info) {
            // Vérifier si la raison de consultation est sélectionnée
            const selectedReasonId = consultationReasonSelect.value;
            if (!selectedReasonId) {
                alert("Veuillez d'abord sélectionner une raison de consultation !");
                return;
            }

            // Vérifier si la date cliquée est active
            const clickedDate = availabilities.find(slot => slot.date === info.dateStr);
            if (clickedDate && clickedDate.is_active) {
                // Afficher la liste des créneaux horaires pour la date cliquée
                selectedDateDisplay.textContent = info.dateStr;
                selectedDateInput.value = info.dateStr;
                availableTimesSection.style.display = "block";

                // Réinitialiser les créneaux horaires
                timeList.innerHTML = "";

                // Récupérer les créneaux horaires spécifiques pour la date cliquée
                const availableSlots = availabilities.filter(slot => slot.date === info.dateStr && slot.is_active);

                // Ajouter les créneaux horaires à la liste
                availableSlots.forEach(slot => {
                    const li = document.createElement("li");
                    li.textContent = slot.start_time; // Heure du créneau
                    li.classList.add("available-slot");
                    li.addEventListener("click", function () {
                        // Afficher la fenêtre modale et passer les données sélectionnées
                        selectedTimeInput.value = slot.start_time;
                        selectedTimeElement.textContent = slot.start_time;
                        reservationModal.style.display = "block";

                        // Appliquer le style "sélectionné"
                        document.querySelectorAll(".available-slot").forEach(el => el.classList.remove("selected"));
                        li.classList.add("selected");
                    });
                    timeList.appendChild(li);
                });
            } else {
                // Alerte si la date cliquée est inactive
                alert("Aucun horaire disponible pour cette date. Veuillez en choisir une autre.");
            }
        }
    });

    // Rendu du calendrier
    calendar.render();

    // Gestion de la fermeture de la fenêtre modale
    document.querySelectorAll(".close").forEach(function (btn) {
        btn.onclick = function () {
            reservationModal.style.display = "none"; // Fermer la fenêtre modale
        };
    });

    // Optionnel : Fermeture de la fenêtre modale lorsqu'on clique en dehors
    window.onclick = function (event) {
        if (event.target === reservationModal) {
            reservationModal.style.display = "none";
        }
    };

    // Écouter les changements dans les raisons de consultation
    consultationReasonSelect.addEventListener("change", function () {
        // Réinitialiser l'affichage lors du changement de la raison
        selectedDateDisplay.textContent = "";
        availableTimesSection.style.display = "none";
        timeList.innerHTML = "";
    });
});
