// Example JavaScript for validation or interactivity if needed

document.addEventListener('DOMContentLoaded', function() {
  const form = document.querySelector('form');
  
  // Form submit event
  form.addEventListener('submit', function(event) {
    const username = document.getElementById('username');
    const email = document.getElementById('email');
    const password = document.getElementById('password');
    const role = document.getElementById('role');
    
    // Basic validation (can be extended as per needs)
    if (username.value === "" || email.value === "" || password.value === "" || role.value === "") {
      event.preventDefault();
      alert("Tous les champs sont requis!");
    }
  });
});
