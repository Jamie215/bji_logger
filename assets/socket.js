function logToServer(message) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/log", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify({ message: message }));
}

var socket;

function logMessage(message) {
    let logs = localStorage.getItem("logMessages") || "";
    logs += message + "\n";
    localStorage.setItem("logMessages", logs);
    console.log(message);
}
window.onload = function() {
    var logs = localStorage.getItem("logMessages");
    if (logs) {
        console.log("Stored logs:");
        console.log(logs);
        localStorage.removeItem("logMessages");
    }
    // Check if the page was refreshed
    if (performance.getEntriesByType("navigation")[0].type === "reload") {
        logMessage("Page Refreshed");
        localStorage.setItem('isRefreshed', 'true');
    } else {
        logMessage("normal navigation");
        localStorage.setItem('isRefreshed', 'false');
    }

    socket = io();
    logMessage("socket initialized");
    
    // Set flag before unload
    window.onbeforeunload = function() {
        logMessage("entered window onbeforeunload");
        const data = { event: localStorage.getItem('isRefreshed') === 'true' ? 'page_refreshed' : 'window_closed' };

        if (localStorage.getItem('isRefreshed') === 'true') {
            logMessage("Emitting page_refreshed event");
            navigator.sendBeacon("/emit_event", JSON.stringify(data));
        } else {
            logMessage("Emiting window_closed event");
            navigator.sendBeacon("/emit_event", JSON.stringify(data));
        }
        socket.disconnect();
    };

    socket.on('connect', function() {
        logMessage('Socket connected');
    });

    socket.on('disconnect', function() {
        logMessage('Socket disconnected');
    });
};