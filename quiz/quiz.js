
document.addEventListener("DOMContentLoaded", () => {
    const app = document.getElementById("quizApp");

    if (!app) {
        console.error('Quiz initialization failed: missing element with id="quizApp".');
        return;
    }

    const QUESTIONS_PER_QUIZ = 10;
    const STARTING_DIFFICULTY = 3;
    const STORAGE_KEY = "instaBibleLearnerProfile";
    const MAX_RECENT_ATTEMPTS = 500;

    let questionBank = [];
    let remainingQuestions = [];
    let attempts = [];
    let currentQuestion = null;
    let questionNumber = 0;
    let score = 0;
    let targetDifficulty = STARTING_DIFFICULTY;
    let consecutiveCorrect = 0;
    let questionStartTime = 0;
    let answered = false;

    let learnerProfile = createEmptyProfile();

    // --------------------------------------------------
    // Persistent learner profile
    // --------------------------------------------------

    function createEmptyProfile() {
        return {
            version: 1,
            totalAnswered: 0,
            totalCorrect: 0,
            totalResponseTimeMs: 0,
            books: {},
            difficultyHistory: [],
            recentAttempts: []
        };
    }

    function loadLearnerProfile() {
        try {
            const savedProfile = localStorage.getItem(STORAGE_KEY);

            if (!savedProfile) {
                learnerProfile = createEmptyProfile();
                return;
            }

            const parsed = JSON.parse(savedProfile);

            if (
                !parsed ||
                parsed.version !== 1 ||
                !Number.isFinite(parsed.totalAnswered) ||
                !Number.isFinite(parsed.totalCorrect) ||
                !Number.isFinite(parsed.totalResponseTimeMs) ||
                typeof parsed.books !== "object" ||
                parsed.books === null
            ) {
                throw new Error("Saved learner profile has an invalid format.");
            }

            learnerProfile = {
                ...createEmptyProfile(),
                ...parsed,
                difficultyHistory: Array.isArray(parsed.difficultyHistory)
                    ? parsed.difficultyHistory
                    : [],
                recentAttempts: Array.isArray(parsed.recentAttempts)
                    ? parsed.recentAttempts
                    : []
            };

        } catch (error) {
            console.error("Could not load learner profile:", error);
            learnerProfile = createEmptyProfile();
        }
    }

    function saveLearnerProfile() {
        try {
            localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(learnerProfile)
            );
        } catch (error) {
            console.error("Could not save learner profile:", error);
        }
    }

    function recordProfileAttempt(attempt) {
        learnerProfile.totalAnswered++;

        if (attempt.correct) {
            learnerProfile.totalCorrect++;
        }

        learnerProfile.totalResponseTimeMs += attempt.response_time_ms;

        // Track performance by Bible book.
        if (!learnerProfile.books[attempt.topic]) {
            learnerProfile.books[attempt.topic] = {
                total: 0,
                correct: 0,
                responseTimeMs: 0
            };
        }

        const book = learnerProfile.books[attempt.topic];

        book.total++;

        if (attempt.correct) {
            book.correct++;
        }

        book.responseTimeMs += attempt.response_time_ms;

        // Track difficulty history.
        learnerProfile.difficultyHistory.push({
            difficulty: attempt.difficulty,
            correct: attempt.correct,
            timestamp: Date.now()
        });

        // Keep the difficulty history bounded.
        if (learnerProfile.difficultyHistory.length > MAX_RECENT_ATTEMPTS) {
            learnerProfile.difficultyHistory =
                learnerProfile.difficultyHistory.slice(-MAX_RECENT_ATTEMPTS);
        }

        // Keep a bounded history of individual attempts.
        learnerProfile.recentAttempts.push({
            question_id: attempt.question_id,
            topic: attempt.topic,
            difficulty: attempt.difficulty,
            correct: attempt.correct,
            response_time_ms: attempt.response_time_ms,
            timestamp: Date.now()
        });

        if (learnerProfile.recentAttempts.length > MAX_RECENT_ATTEMPTS) {
            learnerProfile.recentAttempts =
                learnerProfile.recentAttempts.slice(-MAX_RECENT_ATTEMPTS);
        }

        // Save immediately after every answer.
        saveLearnerProfile();
    }

    function getLifetimeAccuracy() {
        if (learnerProfile.totalAnswered === 0) {
            return 0;
        }

        return Math.round(
            (learnerProfile.totalCorrect / learnerProfile.totalAnswered) * 100
        );
    }
    function getStartingDifficulty() {
    const recentAttempts = learnerProfile.recentAttempts.slice(-20);

    // Not enough history yet: use the default difficulty.
    if (recentAttempts.length < 5) {
        return STARTING_DIFFICULTY;
    }

    const accuracy =
        recentAttempts.filter(attempt => attempt.correct).length /
        recentAttempts.length;

    const averageDifficulty =
        recentAttempts.reduce(
            (total, attempt) => total + attempt.difficulty,
            0
        ) / recentAttempts.length;

    let startingDifficulty = Math.round(averageDifficulty);

    // Adjust based on recent performance.
    if (accuracy >= 0.80) {
        startingDifficulty++;
    } else if (accuracy <= 0.45) {
        startingDifficulty--;
    }

    return Math.max(1, Math.min(5, startingDifficulty));
    }
    function getAverageResponseTime() {
        if (learnerProfile.totalAnswered === 0) {
            return 0;
        }

        return Math.round(
            learnerProfile.totalResponseTimeMs /
            learnerProfile.totalAnswered
        );
    }

    function formatResponseTime(milliseconds) {
        return `${(milliseconds / 1000).toFixed(1)} seconds`;
    }

    // --------------------------------------------------
    // Utility functions
    // --------------------------------------------------

    function shuffle(array) {
        const result = [...array];

        for (let i = result.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [result[i], result[j]] = [result[j], result[i]];
        }

        return result;
    }

    function createElement(tag, className, text) {
        const element = document.createElement(tag);

        if (className) {
            element.className = className;
        }

        if (text !== undefined) {
            element.textContent = text;
        }

        return element;
    }

    function updateDifficulty(correct) {
        if (correct) {
            consecutiveCorrect++;

            if (consecutiveCorrect >= 2) {
                targetDifficulty = Math.min(5, targetDifficulty + 1);
                consecutiveCorrect = 0;
            }
        } else {
            consecutiveCorrect = 0;
            targetDifficulty = Math.max(1, targetDifficulty - 1);
        }
    }

    // --------------------------------------------------
    // Question selection
    // --------------------------------------------------

    function selectQuestion() {
        if (remainingQuestions.length === 0) {
            return null;
        }

        const closestDistance = Math.min(
            ...remainingQuestions.map(question =>
                Math.abs(question.difficulty - targetDifficulty)
            )
        );

        const candidates = remainingQuestions.filter(question =>
            Math.abs(question.difficulty - targetDifficulty) === closestDistance
        );

        const selected = candidates[
            Math.floor(Math.random() * candidates.length)
        ];

        remainingQuestions = remainingQuestions.filter(
            question => question.id !== selected.id
        );

        return selected;
    }

    // --------------------------------------------------
    // Loading the question bank
    // --------------------------------------------------

    async function loadQuestions() {
        app.replaceChildren(
            createElement("p", "quiz-loading", "Loading question bank...")
        );

        try {
            const response = await fetch("./quiz.json");

            if (!response.ok) {
                throw new Error(`Could not load quiz.json (${response.status}).`);
            }

            const data = await response.json();

            if (!Array.isArray(data.questions) || data.questions.length === 0) {
                throw new Error("The question bank does not contain a valid questions array.");
            }

            questionBank = data.questions.filter(isValidQuestion);

            if (questionBank.length < QUESTIONS_PER_QUIZ) {
                throw new Error(
                    `Only ${questionBank.length} valid questions were found. ` +
                    `At least ${QUESTIONS_PER_QUIZ} are required.`
                );
            }

            showStartScreen();

        } catch (error) {
            console.error(error);

            app.replaceChildren(
                createElement("h2", "quiz-error", "Unable to load the quiz"),
                createElement("p", "", error.message),
                createElement(
                    "p",
                    "",
                    "Check that quiz.json is in the same folder as quiz.html and that the site is being served locally."
                )
            );
        }
    }

    function isValidQuestion(question) {
        return (
            question &&
            typeof question.id === "string" &&
            typeof question.question === "string" &&
            typeof question.topic === "string" &&
            Number.isInteger(question.difficulty) &&
            question.difficulty >= 1 &&
            question.difficulty <= 5 &&
            Array.isArray(question.options) &&
            question.options.length === 4 &&
            question.options.every(option =>
                option &&
                typeof option.id === "string" &&
                typeof option.text === "string"
            ) &&
            question.options.some(
                option => option.id === question.correct_option_id
            )
        );
    }

    // --------------------------------------------------
    // Learner statistics display
    // --------------------------------------------------

    function createProfileSummary() {
        const section = createElement("section", "quiz-profile");

        section.appendChild(
            createElement("h2", "quiz-breakdown-heading", "Your Learning Profile")
        );

        const stats = createElement("div", "quiz-profile-stats");

        const metrics = [
            ["Questions answered", learnerProfile.totalAnswered.toLocaleString()],
            ["Lifetime accuracy", `${getLifetimeAccuracy()}%`],
            ["Average response time",
                learnerProfile.totalAnswered === 0
                    ? "N/A"
                    : formatResponseTime(getAverageResponseTime())
            ],
            ["Books practiced", Object.keys(learnerProfile.books).length]
        ];

        metrics.forEach(([label, value]) => {
            const metric = createElement("p", "quiz-info");
            metric.append(
                createElement("strong", "", `${label}: `),
                document.createTextNode(value)
            );
            stats.appendChild(metric);
        });

        section.appendChild(stats);

        return section;
    }

    function createLifetimeBookBreakdown() {
        const section = createElement("section", "quiz-breakdown");

        section.appendChild(
            createElement("h2", "quiz-breakdown-heading", "Lifetime Performance by Book")
        );

        const books = Object.entries(learnerProfile.books)
            .sort((a, b) => {
                const accuracyA = a[1].correct / a[1].total;
                const accuracyB = b[1].correct / b[1].total;
                return accuracyA - accuracyB;
            });

        if (books.length === 0) {
            section.appendChild(
                createElement("p", "quiz-info", "No previous attempts yet.")
            );
            return section;
        }

        books.forEach(([topic, stats]) => {
            const accuracy = Math.round(
                (stats.correct / stats.total) * 100
            );

            section.appendChild(
                createElement(
                    "p",
                    "quiz-breakdown-row",
                    `${topic}: ${stats.correct}/${stats.total} correct (${accuracy}%)`
                )
            );
        });

        return section;
    }

    // --------------------------------------------------
    // Start screen
    // --------------------------------------------------

    function showStartScreen() {
        app.replaceChildren();

        const heading = createElement("h1", "quiz-title", "Test Yourself");

        const description = createElement(
            "p",
            "quiz-description",
            "Test your knowledge of Scripture with questions from across all 66 books of the Bible."
        );

        const questionCount = createElement(
            "p",
            "quiz-info",
            `${QUESTIONS_PER_QUIZ} questions per attempt`
        );

        const bankCount = createElement(
            "p",
            "quiz-info",
            `${questionBank.length.toLocaleString()} available questions`
        );

        const startButton = createElement(
            "button",
            "quiz-button",
            "Start Quiz"
        );

        startButton.type = "button";
        startButton.addEventListener("click", startQuiz);

        app.append(
            heading,
            description,
            questionCount,
            bankCount,
            createProfileSummary(),
            startButton
        );
    }

    // --------------------------------------------------
    // Start and reset quiz
    // --------------------------------------------------

    function startQuiz() {
        remainingQuestions = shuffle(questionBank);
        attempts = [];
        currentQuestion = null;
        questionNumber = 0;
        score = 0;
        targetDifficulty = getStartingDifficulty();
        consecutiveCorrect = 0;
        answered = false;

        displayNextQuestion();
    }

    // --------------------------------------------------
    // Display questions
    // --------------------------------------------------

    function displayNextQuestion() {
        if (questionNumber >= QUESTIONS_PER_QUIZ) {
            showResults();
            return;
        }

        currentQuestion = selectQuestion();

        if (!currentQuestion) {
            showResults();
            return;
        }

        questionNumber++;
        answered = false;
        questionStartTime = performance.now();

        app.replaceChildren();

        const progressText = createElement(
            "p",
            "quiz-progress-text",
            `Question ${questionNumber} of ${QUESTIONS_PER_QUIZ}`
        );

        const progress = createElement("progress", "quiz-progress");
        progress.max = QUESTIONS_PER_QUIZ;
        progress.value = questionNumber - 1;

        const metadata = createElement(
            "p",
            "quiz-metadata",
            `${currentQuestion.topic} · Difficulty ${currentQuestion.difficulty}/5`
        );

        const questionHeading = createElement(
            "h2",
            "quiz-question",
            currentQuestion.question
        );

        const reference = createElement(
            "p",
            "quiz-reference",
            currentQuestion.reference || ""
        );

        const optionsContainer = createElement("div", "quiz-options");

        const shuffledOptions = shuffle(currentQuestion.options);

        shuffledOptions.forEach(option => {
            const button = createElement(
                "button",
                "quiz-option",
                `${option.id}. ${option.text}`
            );

            button.type = "button";
            button.addEventListener("click", () => submitAnswer(option));

            optionsContainer.appendChild(button);
        });

        const feedback = createElement("div", "quiz-feedback");
        feedback.setAttribute("aria-live", "polite");

        app.append(
            progressText,
            progress,
            metadata,
            questionHeading,
            reference,
            optionsContainer,
            feedback
        );
    }

    // --------------------------------------------------
    // Answer checking
    // --------------------------------------------------

    function submitAnswer(selectedOption) {
        if (answered || !currentQuestion) {
            return;
        }

        answered = true;

        const responseTime = Math.round(
            performance.now() - questionStartTime
        );

        const correct =
            selectedOption.id === currentQuestion.correct_option_id;

        if (correct) {
            score++;
        }

        const attempt = {
            question_id: currentQuestion.id,
            topic: currentQuestion.topic,
            correct: correct,
            response_time_ms: responseTime,
            difficulty: currentQuestion.difficulty
        };

        attempts.push(attempt);

        // Persist this answer across browser sessions.
        recordProfileAttempt(attempt);

        updateDifficulty(correct);

        const optionButtons = app.querySelectorAll(".quiz-option");

        optionButtons.forEach(button => {
            button.disabled = true;
        });

        const feedback = app.querySelector(".quiz-feedback");

        const result = createElement(
            "h3",
            correct ? "quiz-correct" : "quiz-incorrect",
            correct ? "Correct!" : "Incorrect"
        );

        const correctOption = currentQuestion.options.find(
            option => option.id === currentQuestion.correct_option_id
        );

        const answerText = createElement(
            "p",
            "quiz-answer",
            `Correct answer: ${correctOption.text}`
        );

        const explanation = createElement(
            "p",
            "quiz-explanation",
            currentQuestion.explanation || ""
        );

        const sourceLink = document.createElement("a");
        sourceLink.className = "quiz-source";
        sourceLink.textContent = "Read the passage";

        if (currentQuestion.source_url) {
            sourceLink.href = currentQuestion.source_url;
            sourceLink.target = "_blank";
            sourceLink.rel = "noopener noreferrer";
        } else {
            sourceLink.hidden = true;
        }

        const nextButton = createElement(
            "button",
            "quiz-button",
            questionNumber === QUESTIONS_PER_QUIZ
                ? "View Results"
                : "Next Question"
        );

        nextButton.type = "button";
        nextButton.addEventListener("click", displayNextQuestion);

        feedback.append(
            result,
            answerText,
            explanation,
            sourceLink,
            nextButton
        );
    }

    // --------------------------------------------------
    // Results
    // --------------------------------------------------

    function showResults() {
        app.replaceChildren();

        const heading = createElement(
            "h1",
            "quiz-title",
            "Quiz Complete!"
        );

        const scoreHeading = createElement(
            "h2",
            "quiz-score",
            `${score} / ${attempts.length}`
        );

        const percentage = Math.round(
            (score / attempts.length) * 100
        );

        const accuracy = createElement(
            "p",
            "quiz-accuracy",
            `This attempt's accuracy: ${percentage}%`
        );

        const topicStats = {};

        attempts.forEach(attempt => {
            if (!topicStats[attempt.topic]) {
                topicStats[attempt.topic] = {
                    correct: 0,
                    total: 0
                };
            }

            topicStats[attempt.topic].total++;

            if (attempt.correct) {
                topicStats[attempt.topic].correct++;
            }
        });

        const breakdownHeading = createElement(
            "h2",
            "quiz-breakdown-heading",
            "This Attempt by Book"
        );

        const breakdown = createElement("div", "quiz-breakdown");

        Object.entries(topicStats)
            .sort((a, b) => a[0].localeCompare(b[0]))
            .forEach(([topic, stats]) => {
                const row = createElement(
                    "p",
                    "quiz-breakdown-row",
                    `${topic}: ${stats.correct}/${stats.total} correct`
                );

                breakdown.appendChild(row);
            });

        const restartButton = createElement(
            "button",
            "quiz-button",
            "Try Again"
        );

        restartButton.type = "button";
        restartButton.addEventListener("click", showStartScreen);

        app.append(
            heading,
            scoreHeading,
            accuracy,
            createProfileSummary(),
            breakdownHeading,
            breakdown,
            createLifetimeBookBreakdown(),
            restartButton
        );

        console.log("Quiz attempt history:", attempts);
        console.log("Persistent learner profile:", learnerProfile);
    }

    // --------------------------------------------------
    // Initialize
    // --------------------------------------------------

    loadLearnerProfile();
    loadQuestions();
});
