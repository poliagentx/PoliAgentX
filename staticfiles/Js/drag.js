
document.addEventListener("DOMContentLoaded", function () {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("{{ upload_form.government_expenditure.id_for_label }}"); // Django gives it an ID
    const form = fileInput.closest("form");

    // Highlight drop zone when dragging a file over it
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("border-blue-500", "bg-gray-100");
    });

    // Remove highlight when leaving drop zone
    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("border-blue-500", "bg-gray-100");
    });

    // Handle file drop
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("border-blue-500", "bg-gray-100");

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files; // Assign dropped files to input
            console.log("File dropped:", files[0].name);

            // Optionally update drop zone text
            dropZone.querySelector("p.text-gray-700").textContent = files[0].name;
        }
    });
});
