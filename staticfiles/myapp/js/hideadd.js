document.addEventListener("DOMContentLoaded", function () {
    // Find and remove the sidebar +Add link next to "Infos"
    const addLinks = document.querySelectorAll("a.addlink");

    addLinks.forEach(link => {
        if (link.href.includes("/info/add")) {
            link.style.display = "none";
        }
    });
});
