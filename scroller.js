window.scrollTo({ top: 1200, behavior: 'instant' });

function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

let currentAudio = null;
const verseHistory = [];
const maxHistoryLength = 6;
let historyIndex = -1;
let isLoadingVerse = false;

const scrollerContainer = document.getElementById("scroller-container");
function resizeScroller() {
    scrollerContainer.style.height = "auto";
    const contentHeight = scrollerContainer.scrollHeight;
    const viewportHeight = window.innerHeight;
    if (viewportHeight > contentHeight) {
        scrollerContainer.style.height = `${viewportHeight}px`;
    }
    window.scrollTo({ top: 1200, behavior: 'instant' });
}

async function generateSpeech(verse) {
    const text = verse;
    const player = document.getElementById("audioPlayer");

    if (!text.trim()) {
    console.log("no text.");
    return;
    }

    try {
    const response = await fetch("/proxy", {
        method: "POST",
        headers: {
        "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
    });

    if (!response.ok) {
        throw new Error("Failed to generate speech.");
    }

    const audioBlob = await response.blob();
    const audioURL = URL.createObjectURL(audioBlob);

    player.src = audioURL;
    await player.play();

    } catch (error) {
    console.error(error);
    console.log("Error generating speech.");
    }
}

async function fetchVerse(chapter, verse) {
    const url = `https://bible-api.com/proverbs%20${chapter}:${verse}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Verse request failed: ${response.status}`);
    }
    return response.json();
}

async function getRandomVerse() {
    const response = await fetch("./data/proverbs_structure.json");
    if (!response.ok) {
        throw new Error(`Chapter data request failed: ${response.status}`);
    }
    const data = await response.json();
    const chapter = getRndInteger(1, data.chapters.length);
    const verse = getRndInteger(1, data.chapters[chapter - 1]);
    return { chapter, verse };
}

function showVerse(entry) {
    document.getElementById("reference").textContent = entry.reference;
    document.getElementById("verse").textContent = entry.text;
    document.getElementById("link").href = `https://www.bible.com/bible/111/PRO.${entry.chapter}.NIV`;
    document.getElementById("link").textContent = "Read Context";

    const randMusic = getRndInteger(1, 10);
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }
    currentAudio = new Audio(`http://pankrjrpi.eastus.cloudapp.azure.com/instabible/music/${randMusic}.mp3`);
    currentAudio.play();
    resizeScroller();
}

async function loadNewVerse(direction = "forward") {
    if (isLoadingVerse) return;
    isLoadingVerse = true;
    try {
        if (direction === "backward") {
            if (historyIndex <= 0) return;
            historyIndex--;
        } else if (historyIndex < verseHistory.length - 1) {
            historyIndex++;
        } else {
            document.getElementById("verse").textContent = "Verse";

            const reference = await getRandomVerse();
            const data = await fetchVerse(reference.chapter, reference.verse);
            verseHistory.push({
                ...reference,
                reference: `Proverbs ${reference.chapter}:${reference.verse}`,
                text: data.text
            });
            if (verseHistory.length > maxHistoryLength) {
                verseHistory.shift();
            }
            historyIndex = verseHistory.length - 1;
        }

        showVerse(verseHistory[historyIndex]);
    } catch (error) {
        document.getElementById("reference").textContent = "Unable to load a verse. Please try again.";
        console.log(error);
    } finally {
        isLoadingVerse = false;
    }
}

// document.getElementById("reference").innerHTML = "Provervs 3:3";
// document.getElementById("verse").innerHTML = "This is a bible verse, it is a really good verse.";

loadNewVerse();

let reloadPending = false;

window.addEventListener('keydown', function (event) {
  if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
    event.preventDefault();
    loadNewVerse("forward");
  } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
    event.preventDefault();
    loadNewVerse("backward");
  }
});

function disableScroll() {
    document.body.classList.add("stop-scrolling");
    setTimeout(() => {
        reloadPending = false;
        document.body.classList.remove("stop-scrolling");
    }, 500); // 500 is good for stop scrolling
}

window.addEventListener('scroll', function () {
  const pageHeight = document.documentElement.scrollHeight;
  const atBottom = window.innerHeight + window.scrollY >= pageHeight - 1;

  // Scroll events continue firing while the page is at the bottom. Reload once.
  if (atBottom) {
    reloadPending = true;
    window.scrollTo({ top: 1200, behavior: 'instant' });
    disableScroll();
    loadNewVerse("forward");
    return;
    //window.location.reload();
  }

  const atTop = window.scrollY <= 100;

  if (atTop) {
    reloadPending = true;
    window.scrollTo({ top: 1200, behavior: 'instant' });
    disableScroll();
    loadNewVerse("backward");
  }
});



