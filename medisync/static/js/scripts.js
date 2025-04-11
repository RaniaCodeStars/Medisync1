const menuOpenButton = document.querySelector("#menu-open-button");
const menuCloseButton = document.querySelector("#menu-close-button");



menuOpenButton.addEventListener("click", () => {
    //toggle mobile menu visibility 
    document.body.classList.toggle("show-mobile-menu");
});

menuCloseButton.addEventListener("click", () => menuOpenButton.click());



document.getElementById("read-more-btn").addEventListener("click", function () {
    var fullText = document.getElementById("full-text");
    var button = document.getElementById("read-more-btn");

    if (fullText.style.display === "none" || fullText.style.display === "") {
        fullText.style.display = "block";
        setTimeout(() => (fullText.style.opacity = "1"), 100); // Animation fluide
        button.textContent = "Lire moins";
    } else {
        fullText.style.opacity = "0";
        setTimeout(() => (fullText.style.display = "none"), 500);
        button.textContent = "Lire plus";
    }
});


