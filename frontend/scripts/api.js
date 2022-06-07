// Auth Stuff
const fetchAuthConfig = () => fetch("/auth_config.json");
var auth0 = null;
var token = null;

const configureClient = async () => {
    // Get Auth Configuration Parameters from client
    const response = await fetchAuthConfig();
    const config = await response.json();

    auth0 = await createAuth0Client({
        domain: config.domain,
        client_id: config.clientId,
        audience: config.audience, // audience value for api access
        scope: "openid profile email",
    });
};

const login = async () => {
    await auth0.loginWithRedirect({
        redirect_uri: window.location.origin,
    });
};

const logout = () => {
    auth0.logout({
        returnTo: window.location.origin,
    });
};

// hugo-backend Functions
async function getObject(key) {
    let url = apiUrl + "get/" + key;

    const response = await fetch(url, {
        method: "GET", // *GET, POST, PUT, DELETE
        mode: "cors",
        cache: "no-cache",
        credentials: "omit",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        redirect: "follow",
        referrerPolicy: "no-referrer",
    });
    return response.json();
}

async function getObjects(pageNum) {
    let url =
        apiUrl +
        "list?" +
        new URLSearchParams({
            page: pageNum,
        });

    const response = await fetch(url, {
        method: "GET", // *GET, POST, PUT, DELETE
        mode: "cors",
        cache: "no-cache",
        credentials: "omit",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        redirect: "follow",
        referrerPolicy: "no-referrer",
    });
    return response.json();
}

async function deletePost(key) {
    let url = apiUrl + "delete/" + key;

    const response = await fetch(url, {
        method: "DELETE", // *GET, POST, PUT, DELETE
        mode: "cors",
        cache: "no-cache",
        credentials: "omit",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        redirect: "follow",
        referrerPolicy: "no-referrer",
    });
    return response.json();
}

async function postData(url = "", data = {}) {
    // The response of the
    return fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE
        mode: "cors",
        cache: "no-cache",
        credentials: "omit",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        redirect: "follow",
        referrerPolicy: "no-referrer",
        body: JSON.stringify(data),
    });
}