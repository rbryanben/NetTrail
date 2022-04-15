// Data 
let ApplicationData = {

}

/*
const routes = [
    { path: "/", redirect: "/Console/ServerLogs/AllLogs/Server/All" },
    {
        path: "/Console",
        component: ConsoleWindow,
        children: [{
            path: "ServerLogs",
            component: serverLogsPage,
            children: [{
                path: "AllLogs/Server/:server_id",
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
    { path: "/Configure", component: ConfigurationWindow },
] */

const routes = [{
        path: "/Console",
        redirect: "/Console/Network/NetworkServers/Servers/ActiveServers"
    },
    {
        path: "/",
        redirect: "/Console/Network/NetworkServers/Servers/ActiveServers"
    },
    { path: "/Configure", component: ConfigurationWindow },
    {
        path: "/Console/:menu/:sub_menu",
        component: ConsoleWindow,
        children: [{
                path: "Trail",
                component: dashBoardComponent,
                children: [{
                    path: 'Dagger',
                    component: dashboardChildComponent
                }]
            }, {
                path: "Logs",
                component: serverLogsPage,
                children: [{
                    path: "AllLogs/Server/:server_id",
                    component: allServerLogsPage
                }]
            }, {
                path: "Servers",
                component: networkServersPage,
                children: [{
                    path: "ActiveServers",
                    component: activeNetworkServersPage
                }]
            },
            {
                path: "AppLogs",
                component: applicationLogsPage,
                children: [{
                    path: "AllLogs/Application/:application_name",
                    component: allApplicationLogsPage
                }]
            },
            {
                path: "Apps",
                component: applicationsPage,
                children: [{
                    path: "All",
                    component: allApplicationsPage
                }]
            }
        ]
    }
]

Vue.use(VueVirtualScroller)

Vue.component('recyclescroller', VueVirtualScroller.RecycleScroller)

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
}