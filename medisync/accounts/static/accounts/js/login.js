// Affichage du mot de passe
document.addEventListener("DOMContentLoaded", function () {
  const togglePassword = document.querySelector("#togglePassword");
  const passwordField = document.querySelector("input[name='password']");

  if (togglePassword) {
      togglePassword.addEventListener("click", function (e) {
          // Toggle le type de champ de mot de passe
          const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
          passwordField.setAttribute("type", type);

          // Change l'icône en fonction de l'état
          togglePassword.classList.toggle("fa-eye-slash");
      });
  }
});

// Ajout d'une validation en temps réel pour l'email et le mot de passe
document.addEventListener("DOMContentLoaded", function () {
  const emailField = document.querySelector("input[name='email']");
  const passwordField = document.querySelector("input[name='password']");
  const emailError = document.createElement("small");
  const passwordError = document.createElement("small");

  // Validation email
  emailField.addEventListener("input", function () {
      if (!emailField.validity.valid) {
          emailError.textContent = "Email invalide";
          emailError.style.color = "red";
          emailField.parentNode.appendChild(emailError);
      } else {
          emailError.textContent = "";
      }
  });

  // Validation mot de passe
  passwordField.addEventListener("input", function () {
      if (passwordField.value.length < 6) {
          passwordError.textContent = "Le mot de passe doit contenir au moins 6 caractères.";
          passwordError.style.color = "red";
          passwordField.parentNode.appendChild(passwordError);
      } else {
          passwordError.textContent = "";
      }
  });
});
