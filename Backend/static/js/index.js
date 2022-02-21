// Data 
let ApplicationData = {

}

const routes = [
    { path: "/", redirect: "/Console/ServerLogs/AllLogs" },
    {
        path: "/Console",
        component: ConsoleWindow,
        children: [{
            path: "ServerLogs",
            component: serverLogsPage,
            children: [{
                path: "AllLogs",
                component: allServerLogsPage
            }]
        }, {
            path: "NetworkServers",
            component: networkServersPage,
            children: [{
                path: "ActiveServers",
                component: activeNetworkServersPage
            }]
        }]
    },
    { path: "Configure", component: ConfigurationWindow },
]

const router = new VueRouter({
    routes
})

//Application 
const MainApplication = new Vue({
    router,
    delimiters: ['[[', ']]'],
    el: "#Application",
    data: ApplicationData,
    mounted: function() {
        //start
        this.startUp();
        showLoading(false)
    },
    methods: {
        startUp: function() {

            //check if the service is configure 
            getFromServer("/api/getServiceStatus", null, (response, status) => {
                if (status == 501)
                    this.configureService()
            })
        },
        configureService: function() {
            router.push("/Configure")
        }
    },
})


// Service Worker 
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(reg => {
            console.log("Service Worker Registered")
        })
        .catch(error => {
            console.log(`Service Worker Error : ${error}`)
        })

} else {
    console.log('Service Worker Unvailable')
}