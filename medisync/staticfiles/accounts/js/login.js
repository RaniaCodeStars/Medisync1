const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');
const signupForm = document.getElementById('signup-form');
const loginForm = document.getElementById('login-form');

// Basculer entre les formulaires
registerBtn.addEventListener('click', () => {
  container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
  container.classList.remove("active");
});

// Gérer l'inscription
signupForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('signup-username').value;
  const email = document.getElementById('signup-email').value;
  const password = document.getElementById('signup-password').value;

  const response = await fetch('/accounts/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password, action: 'signup' }),
  });

  if (response.ok) {
    alert('Inscription réussie ! Connectez-vous maintenant.');
    container.classList.remove("active");  // Basculer vers le formulaire de connexion
  } else {
    alert('Erreur lors de l\'inscription');
  }
});

// Gérer la connexion
loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  const response = await fetch('/accounts/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, action: 'login' }),
  });

  const data = await response.json();

  if (response.ok) {
    localStorage.setItem('token', data.access);
    localStorage.setItem('role', data.role);
    alert('Connexion réussie !');
    // Rediriger en fonction du rôle
    switch (data.role) {
      case 'MEDECIN':
        window.location.href = '/dashboard-medecin';
        break;
      case 'PATIENT':
        window.location.href = '/dashboard-patient';
        break;
      case 'ADMIN':
        window.location.href = '/dashboard-admin';
        break;
      case 'PHARMACIEN':
        window.location.href = '/dashboard-pharmacien';
        break;
      default:
        window.location.href = '/';
    }
  } else {
    alert('Erreur de connexion');
  }
});