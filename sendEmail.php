<?php

// Send a POST request to the Flask backend
function sendRequestToFlaskBackend() {
    $url = 'http://localhost:5000/bypass';  // Flask backend URL

    // Create data to send to Flask
    $data = json_encode([
        'username' => 'testuser',  // Replace with your actual username
        'password' => 'testpassword'  // Replace with your actual password
    ]);

    // Set the HTTP options for the POST request
    $options = [
        'http' => [
            'header'  => "Content-Type: application/json\r\n",
            'method'  => 'POST',
            'content' => $data,
        ],
    ];

    // Create the context for the request
    $context  = stream_context_create($options);

    // Execute the request and get the response
    $response = file_get_contents($url, false, $context);

    if ($response === FALSE) {
        echo "Error: Failed to fetch data from Flask.";
    } else {
        // Process the response from Flask
        $responseData = json_decode($response, true);

        // If the request was successful, you can handle the response here
        echo "Data sent successfully: " . $responseData['message'];
    }
}

// Trigger the function when the button is clicked (via JS)
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    sendRequestToFlaskBackend();
}

?>

<!-- HTML for triggering the PHP script with a button -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Trigger Data Grabbing</title>
</head>
<body>
    <h1>Click the button to trigger data grabbing and email sending</h1>
    
    <button id="triggerButton">Grab Data and Send Email</button>

    <script>
        document.getElementById("triggerButton").addEventListener("click", function() {
            fetch("sendEmail.php", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: "action=trigger"  // The action can be any value for server to process
            })
            .then(response => response.text())
            .then(data => {
                console.log("Response from PHP:", data);
                alert(data);  // Show a response message
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Error occurred: " + error);
            });
        });
    </script>
</body>
</html>
