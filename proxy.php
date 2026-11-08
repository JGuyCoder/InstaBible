<?php

header("Content-Type: audio/mpeg");

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    http_response_code(405);
    header("Content-Type: application/json");
    echo json_encode(["error" => "Method not allowed"]);
    exit;
}

// Load API key from environment
$apiKey = getenv("ELEVENLABS_API_KEY");

// Get submitted text
$data = json_decode(file_get_contents("php://input"), true);
$text = $data["text"] ?? "";

if (!$apiKey) {
    http_response_code(500);
    header("Content-Type: application/json");
    echo json_encode(["error" => "API key not configured"]);
    exit;
}

if (!is_string($text) || trim($text) === "") {
    http_response_code(400);
    header("Content-Type: application/json");
    echo json_encode(["error" => "Please provide text"]);
    exit;
}

// ElevenLabs API endpoint
$url = "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb?output_format=mp3_44100_128";

// Request payload
$payload = [
    "text" => $text,
    "model_id" => "eleven_v4"
];

// Initialize cURL
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

// Execute request
$audio = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError = curl_error($ch);

curl_close($ch);

// Handle errors
if ($audio === false || $httpCode < 200 || $httpCode >= 300) {
    http_response_code(502);
    header("Content-Type: application/json");

    echo json_encode([
        "error" => "ElevenLabs failed to generate audio",
        "details" => $curlError ?: $audio
    ]);

    exit;
}

// Return generated MP3
echo $audio;

?>