window.addEventListener("beforeunload", function (e) {
    navigator.sendBeacon("/shutdown");
});