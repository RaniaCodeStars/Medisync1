
document.addEventListener('DOMContentLoaded', function () {
    const cancelButtons = document.querySelectorAll('.action-btn');
    
    cancelButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            event.preventDefault();

            const appointmentId = button.dataset.id;
            const row = button.closest('tr'); // Trouve la ligne du tableau correspondante

            Swal.fire({
                title: 'Annulation du rendez-vous',
                text: "Êtes-vous sûr de vouloir annuler ce rendez-vous ?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#7F7F7F',
                confirmButtonText: 'Oui, annuler',
                cancelButtonText: 'Non'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(`/appointments/appointment/${appointmentId}/cancel/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        }
                    }).then(response => response.json())
                      .then(data => {
                          if (data.success) {
                              Swal.fire({
                                  title: 'Annulé',
                                  text: 'Votre rendez-vous a été annulé avec succès.',
                                  icon: 'success',
                                  confirmButtonColor: '#92bcf2'
                              });

                              // Mise à jour de l'interface utilisateur
                              if (row) {
                                  // Met à jour la cellule du statut (5ème colonne)
                                  const statusCell = row.cells[4];
                                  if (statusCell) {
                                      statusCell.textContent = 'Annulé';
                                      statusCell.style.color = 'red';
                                  }
                                  
                                  // Désactive ou supprime le bouton Annuler
                                  button.disabled = true;
                                  button.textContent = 'Annulé';
                              }
                          } else {
                              Swal.fire({
                                  title: 'Erreur',
                                  text: data.error || 'Une erreur est survenue.',
                                  icon: 'error'
                              });
                          }
                      }).catch(error => {
                          console.error('Erreur:', error);
                          Swal.fire({
                              title: 'Erreur',
                              text: 'Une erreur inattendue est survenue.',
                              icon: 'error'
                          });
                      });
                }
            });
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            cookies.forEach(cookie => {
                const cookieTrimmed = cookie.trim();
                if (cookieTrimmed.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookieTrimmed.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }
});