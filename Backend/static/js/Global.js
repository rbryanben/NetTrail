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