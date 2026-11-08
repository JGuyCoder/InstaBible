<?php

function respondWithError(int $status, string $message, ?string $details = null): void
{
    http_response_code($status);
    header("Content-Type: application/json; charset=utf-8");
    $response = ["error" => $message];
    if ($details !== null && $details !== "") {
        $response["details"] = $details;
    }
    echo json_encode($response);
    exit;
}

function loadElevenLabsApiKey(): ?string
{
    $apiKey = getenv("ELEVENLABS_API_KEY");
    if ($apiKey !== false && trim($apiKey) !== "") {
        return trim($apiKey);
    }

    // PHP does not load .env files automatically. Read the project-root file
    // when the key was not provided by the server environment.
    $envPath = __DIR__ . DIRECTORY_SEPARATOR . ".env";
    if (!is_readable($envPath)) {
        return null;
    }

    $lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if ($lines === false) {
        return null;
    }

    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === "" || strpos($line, "#") === 0) {
            continue;
        }

        $separator = strpos($line, "=");
        if ($separator === false || trim(substr($line, 0, $separator)) !== "ELEVENLABS_API_KEY") {
            continue;
        }

        $value = trim(substr($line, $separator + 1));
        if (strlen($value) >= 2 && (($value[0] === '"' && $value[strlen($value) - 1] === '"') || ($value[0] === "'" && $value[strlen($value) - 1] === "'"))) {
            $value = substr($value, 1, -1);
        }

        return trim($value) !== "" ? trim($value) : null;
    }

    return null;
}

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    respondWithError(405, "Method not allowed");
}

$data = json_decode(file_get_contents("php://input"), true);
$text = is_array($data) ? ($data["text"] ?? "") : "";

if (!is_string($text) || trim($text) === "") {
    respondWithError(400, "Please provide text");
}

$apiKey = loadElevenLabsApiKey();
if ($apiKey === null) {
    respondWithError(500, "API key not configured. Set ELEVENLABS_API_KEY in the server environment or project-root .env file.");
}

if (!function_exists("curl_init")) {
    respondWithError(500, "PHP cURL extension is not enabled on this server.");
}

$url = "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb?output_format=mp3_44100_128";
$payload = [
    "text" => $text,
    "model_id" => "eleven_v4"
];

$ch = curl_init($url);
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($payload),
    CURLOPT_HTTPHEADER => [
        "xi-api-key: " . $apiKey,
        "Content-Type: application/json",
        "Accept: audio/mpeg"
    ],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 120
]);

$audio = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError = curl_error($ch);
curl_close($ch);

if ($audio === false) {
    respondWithError(502, "Could not connect to ElevenLabs.", $curlError);
}

if ($httpCode < 200 || $httpCode >= 300) {
    // ElevenLabs returns JSON for API errors. Forward its message to help
    // diagnose invalid credentials, voice access, quota, and request issues.
    respondWithError(502, "ElevenLabs rejected the speech request.", substr($audio, 0, 2000));
}

header("Content-Type: audio/mpeg");
echo $audio;

?>
