/*
 */
let showLoading = (isLoading) => {
    var loadingWindow = document.getElementById("loadingWindow")
    if (isLoading) {
        if (!loadingWindow.classList.contains("show")) {
            loadingWindow.classList.add("show")
        }
    } else {
        loadingWindow.classList.remove("show")
    }
}

/* 
 */

window.addEventListener("DOMContentLoaded", () => {
    //connect to socket based on server id 
    var socketName = "ServerLogsAll"

    //Connect to socket feed 
    let serviceSocket = new WebSocket(
        'ws://' +
        window.location.host +
        `/ws/service/${socketName}/`
    );

    serviceSocket.onmessage = function(e) {
        var event = JSON.parse(e.data);
        if (socketCallback)
            socketCallback(event)
    };

    serviceSocket.onclose = function(e) {
        alert('Conection to service socket closed unexpectedly');
    };

})


let socketCallback = null

let dimWindow = (dim) => {
    var window = document.querySelector(".dim-panel")
    if (!window.classList.contains("dim") && dim) {
        window.classList.add("dim")
        return
    }
    window.classList.remove("dim")
}