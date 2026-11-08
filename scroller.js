window.scrollTo({ top: 0, behavior: 'instant' });

function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

let rand_chapter = "";

const scrollerContainer = document.getElementById("scroller-container");
function resizeScroller() {
    scrollerContainer.style.height = `${window.scrollHeight}px`;
    window.scrollTo({ top: 0, behavior: 'instant' });
}

// Keep the panel sized to the current viewport if the window changes size.
//window.addEventListener("resize", resizeScroller);

// Read and parse JSON
function loadNewVerse() {
    fetch("./data/proverbs_structure.json")
        .then(function (proverbsData) { return proverbsData.json(); })
        .then(function(data) {
            console.log("Number of chapters:", data.chapters.length);
            console.log("Verses per chapter:", data.chapters);

            // Randomize verse
            let rand_chapter = getRndInteger(1, data.chapters.length);
            let rand_verse = getRndInteger(1, data.chapters[rand_chapter-1]);
            let url = "https://bible-api.com/proverbs%20" +  rand_chapter + ":" + rand_verse;
            document.getElementById("reference").innerHTML = "Provervs " + rand_chapter + ":" + rand_verse;
            
            // Fetch verse from bible-api
            console.log(url);
            fetch(url)
                .then(function (response) { return response.json(); })
                .then(function(data) {

                    document.getElementById("verse").innerHTML = data.text;

                    $("#link").replaceWith(`
                            <a id="link" href="https://www.bible.com/bible/111/PRO.${rand_chapter}.NIV">- - Context - -</a>
                    `);

                    resizeScroller();
                })
            .catch(function (error) {
                document.getElementById("reference").innerHTML = "You are scrolling too fast!!!!!!";
                console.log(error);
            });
        })
        .catch(function (error) {
            console.log(error);
        });
}

// document.getElementById("reference").innerHTML = "Provervs 3:3";
// document.getElementById("verse").innerHTML = "This is a bible verse, it is a really good verse.";

loadNewVerse();

let reloadPending = false;

window.addEventListener('scroll', function () {
  const pageHeight = document.documentElement.scrollHeight;
  const atBottom = window.innerHeight + window.scrollY >= pageHeight - 1;

  // Scroll events continue firing while the page is at the bottom. Reload once.
  if (atBottom && !reloadPending) {
    reloadPending = true;
    window.location.reload();
  }
});
