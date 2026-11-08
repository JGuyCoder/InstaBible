fetch("heresies.json")
  .then(res => res.json())
  .then(lines => {
    const headerIndices = [];
    lines.forEach((line, i) => {
      if (line.startsWith("@@")) headerIndices.push(i);
    });

    if (headerIndices.length === 0) {
      console.error("No @@ headers found.");
      return;
    }

    const randomIdx = headerIndices[Math.floor(Math.random() * headerIndices.length)];
    const laterHeaders = headerIndices.filter(i => i > randomIdx);
    const nextIdx = laterHeaders.length > 0 ? laterHeaders[0] : lines.length;

    const header = lines[randomIdx];
    const section = lines.slice(randomIdx + 1, nextIdx);

    const output = document.getElementById("output");
    const input = document.getElementById("answer");
    const checkBtn = document.getElementById("check");

    checkBtn.addEventListener("click", () => {
      const answer = input.value.trim();

      if (section.includes(answer)) {
        output.innerText = "Faith Defended!";
        input.disabled = true;
        checkBtn.style.display = "none";

        const refreshBtn = document.createElement("button");
        refreshBtn.id = "refresh";
        refreshBtn.textContent = "Another heresy?";
        refreshBtn.onclick = () => location.reload();
        output.appendChild(document.createElement("br"));
        output.appendChild(refreshBtn);
      } else {
        output.innerText = "Incorrect. Try again.";
        input.value = "";
        input.focus();
      }
    });

    // Also allow Enter key
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") checkBtn.click();
    });
  })
  .catch(err => console.error(err));
