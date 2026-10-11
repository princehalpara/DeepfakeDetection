const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const checkBtn = document.getElementById("checkBtn");
const resultBox = document.getElementById("result");
const dropZone = document.getElementById("dropZone");
const fileName = document.getElementById("fileName");
const emptyPreview = document.getElementById("emptyPreview");

let selectedFile = null;
let previewUrl = null;

const defaultButtonHtml = `
  <span class="btn-icon" aria-hidden="true">
    <svg viewBox="0 0 24 24" role="img" focusable="false">
      <path d="M4 12h16M12 4v16M7 7l10 10M17 7 7 17"/>
    </svg>
  </span>
  <span>Check Image</span>
`;

function setButtonLoading(isLoading) {
  checkBtn.disabled = isLoading || !selectedFile;
  checkBtn.innerHTML = isLoading ? "<span>Checking...</span>" : defaultButtonHtml;
}

function setSelectedFile(file) {
  selectedFile = file || null;
  resultBox.hidden = true;

  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }

  if (!selectedFile) {
    preview.hidden = true;
    emptyPreview.hidden = false;
    fileName.textContent = "No image selected";
    checkBtn.disabled = true;
    return;
  }

  previewUrl = URL.createObjectURL(selectedFile);
  preview.src = previewUrl;
  preview.hidden = false;
  emptyPreview.hidden = true;
  fileName.textContent = selectedFile.name;
  checkBtn.disabled = false;
}

fileInput.addEventListener("change", () => {
  setSelectedFile(fileInput.files[0]);
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) {
    setSelectedFile(file);
  }
});

checkBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  const formData = new FormData();
  formData.append("file", selectedFile);

  setButtonLoading(true);
  resultBox.hidden = true;

  try {
    const res = await fetch("/predict", { method: "POST", body: formData });

    let data = null;
    try {
      data = await res.json();
    } catch (parseErr) {
      data = null;
    }

    if (!res.ok) {
      const errorMessage = data && data.error ? data.error : `Server error (${res.status})`;
      resultBox.textContent = errorMessage;
      resultBox.className = "error";
    } else if (data && data.result) {
      resultBox.textContent = `${data.result} - ${data.confidence}% confidence`;
      resultBox.className = data.result === "REAL" ? "real" : "fake";
    } else {
      resultBox.textContent = "Unexpected response from server.";
      resultBox.className = "error";
    }
  } catch (err) {
    console.error("Connection error:", err);
    resultBox.textContent = "Unable to connect to the prediction server.";
    resultBox.className = "error";
  }

  resultBox.hidden = false;
  setButtonLoading(false);
});
