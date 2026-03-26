document.addEventListener('DOMContentLoaded', function() {
  // Confirmation avant suppression
  const deleteButtons = document.querySelectorAll('.delete-btn');
  deleteButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      if (!confirm('Êtes-vous sûr de vouloir supprimer ce patient ?')) {
        e.preventDefault();
      }
    });
  });

  // Recherche dynamique
  const searchInput = document.getElementById('patientSearch');
  const patientRows = document.querySelectorAll('.patient-row');
  
  searchInput.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    
    patientRows.forEach(row => {
      const rowText = row.textContent.toLowerCase();
      if (rowText.includes(searchTerm)) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  });

  // Tooltips Bootstrap
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl, {
      trigger: 'hover'
    });
  });

  // Animation au survol des boutons d'action
  const actionButtons = document.querySelectorAll('.btn-group .btn');
  actionButtons.forEach(button => {
    button.addEventListener('mouseenter', function() {
      this.style.transform = 'scale(1.1)';
    });
    button.addEventListener('mouseleave', function() {
      this.style.transform = 'scale(1)';
    });
  });
});