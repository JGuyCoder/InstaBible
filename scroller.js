// Inclusive
function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Read and parse JSON
fetch("./data/proverbs_structure.json")
    .then(function (proverbsData) { return proverbsData.json(); })
    .then(function(data) {
        console.log("Number of chapters:", data.chapters.length);
        console.log("Verses per chapter:", data.chapters);

        let randomChapter = getRndInteger(1, data.chapters.length);
        let randomVerse = getRndInteger(1, data.chapters[randomChapter-1]);
        let url = "https://bible-api.com/proverbs%20" +  randomChapter + ":" + randomVerse;
        document.getElementById("reference").innerHTML = "Provervs " + randomChapter + ":" + randomVerse;
        console.log(url);
        fetch(url)
            .then(function (response) { return response.json(); })
            .then(function(data) {
                document.getElementById("verse").innerHTML = data.text;
            })
        .catch(function (error) {
            document.getElementById("reference").innerHTML = "You are scrolling too fast!!!!!!";
            console.log(error);
        });
    })
    .catch(function (error) {
        console.log(error);
    });