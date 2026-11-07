// Inclusive
function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

let rand_chapter = "";

// Read and parse JSON
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
                $("#scroller-container").append(`<div class="link-container"><a class="link" href="https://www.bible.com/bible/111/PRO.${rand_chapter}.NIV">- - Context - -</a></div>`);
            })
        .catch(function (error) {
            document.getElementById("reference").innerHTML = "You are scrolling too fast!!!!!!";
            console.log(error);
        });
    })
    .catch(function (error) {
        console.log(error);
    });

// document.getElementById("reference").innerHTML = "Provervs 3:3";
// document.getElementById("verse").innerHTML = "This is a bible verse, it is a really good verse.";