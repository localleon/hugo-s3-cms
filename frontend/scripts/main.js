// Global Consts and init stuff
const apiUrl = "https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/"
var delay = 1000; // that's 1 seconds of not typing
var timer = null;
let auth0 = null;



// initalize the application
window.onload = async () => {
    await configureClient();
    updateUI();

    const isAuthenticated = await auth0.isAuthenticated();

    if (isAuthenticated) {
        // show the gated content
        updateUI()
        return;
    }

    // check for the code and state parameters
    const query = window.location.search;
    if (query.includes("code=") && query.includes("state=")) {

        // Process the login state
        await auth0.handleRedirectCallback();

        updateUI();

        // Use replaceState to redirect the user away and remove the querystring parameters
        window.history.replaceState({}, document.title, "/");
    }
};

const fetchAuthConfig = () => fetch("/auth_config.json");

const configureClient = async () => {
    // Get Auth Configuration Parameters from client
    const response = await fetchAuthConfig();
    const config = await response.json();

    auth0 = await createAuth0Client({
        domain: config.domain,
        client_id: config.clientId,
        audience: config.audience   // audience value for api access
    });
};

const login = async () => {
    await auth0.loginWithRedirect({
        redirect_uri: window.location.origin
    });
};

const logout = () => {
    auth0.logout({
        returnTo: window.location.origin
    });
};

const updateUI = async () => {
    // hide contents of the single-page-application to make the login feel more fluid

    const isAuthenticated = await auth0.isAuthenticated();

    document.getElementById("btn-logout").disabled = !isAuthenticated;
    document.getElementById("btn-login").disabled = isAuthenticated;

    if (isAuthenticated) {
        document.getElementById("spa").style.visibility = "visible";
    } else {
        document.getElementById("spa").style.visibility = "hidden";

    }

};

// Markdown Preview Stuff 

function isTyping() {
    // Automatic Markdown-Preview when the user is tpying 
    clearTimeout(timer);
    let value = document.getElementById('mdUserText').value;
    if (value) {
        preview()
        timer = setTimeout(null, delay);
    }
}

function preview() {
    let text = document.getElementById('mdUserText').value
    // Sanitize the HTML from the server here to prevent XSS 
    let clean = DOMPurify.sanitize(text);
    // Preview in box
    document.getElementById('preview').innerHTML = marked.parse(clean);
}


// Interaction with the HTTP Api 
function submitPost() {
    console.log("Submitting post!")
    //TODO: Check if fields are filled

    // Construct json object from form 
    let post = {
        "title": document.getElementById('ftitle').value,
        "date": document.getElementById('fdate').value,
        "author": document.getElementById('fauthor').value,
        "content": document.getElementById('mdUserText').value
    }
    let url = apiUrl + "upload"
    // Upload post via Rest-Api 
    postData(url, post).then(data => {
        alert(data['msg'])
    });


    // Refresh view
    clearPostFields()
    setTimeout(listObjects(), 2000)
}

function clearPostFields() {
    document.getElementById('preview').innerHTML = null
    document.getElementById('ftitle').value = ""
    document.getElementById('fdate').value = ""
    document.getElementById('fauthor').value = ""
    document.getElementById('mdUserText').value = ""
}


function constructObject(key) {
    // constructObjects constructs a html element that displays an markdown post

    // Creating wrapper object for file object 
    let div = document.createElement("div")
    div.setAttribute("class", "row singleObject")

    // Description part 
    let divC1 = document.createElement("div")
    divC1.setAttribute("class", "column")
    p = document.createElement("p")
    p.innerHTML = key
    divC1.appendChild(p)

    // Inner Elements get and delete
    let divC2 = document.createElement("div")
    divC2.setAttribute("class", "column")

    // Get Button
    let imgG = document.createElement("img")
    imgG.src = "images/icons/view.png"
    imgG.alt = "Download"
    imgG.setAttribute("class", "icon")

    imgG.setAttribute("onclick", "displayPost('" + key + "')")

    // Delete Button
    let imgD = document.createElement("img")
    imgD.src = "images/icons/delete.png"
    imgD.alt = "Delete"
    imgD.setAttribute("class", "icon")
    imgD.setAttribute("onclick", "deletePostPrompt('" + key + "')")


    divC2.appendChild(imgG)
    divC2.appendChild(imgD)

    // Append to final object
    div.appendChild(divC1)
    div.appendChild(divC2)

    return div
}

function listObjects() {
    // Reset preview of objects
    document.getElementById('getPreview').innerHTML = null
    // Request objects from api 
    getObjects().then(objects => {
        keys = objects['Contents']
        // Create a div from array and insert each object into the document
        list = document.getElementById('objectList')
        list.innerHTML = null
        for (var i = 0; i < keys.length; i++) {
            obj = constructObject(keys[i])
            list.appendChild(obj)
        }
    })
}


function displayPost(key) {
    console.log("Displaying post " + key)
    getObject(key).then(resp => {
        // The .md files on the server are in Hugo-Format. We need to extract only the markdown content from the files
        postParts = atob(resp['body']).split('---')
        document.getElementById('getPreview').innerHTML = marked.parse(postParts[2]);
    })
}

function deletePostPrompt(key) {
    // Confirm if the user really wants to delete the item
    let dialog = confirm("Do you want to delete " + key + "?");
    if (dialog) {
        deletePost(key)
        console.log('Post' + key + ' deleted')

        // Refresh view 
        setTimeout(listObjects(), 1000)
    }
    else {
        console.log('Post' + key + ' was not deleted')
    }
}


// HTTP-API Functions

async function getObject(key) {
    // Get the access token from the Auth0 client
    const token = await auth0.getTokenSilently();

    let url = apiUrl + "get?" + new URLSearchParams({
        key: key
    })
    const response = await fetch(url, {
        method: 'GET', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer'
    });
    return response.json();
}

async function getObjects() {
    // Get the access token from the Auth0 client
    const token = await auth0.getTokenSilently();

    let url = apiUrl + "list"
    const response = await fetch(url, {
        method: 'GET', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer',
    });
    return response.json();
}

async function deletePost(key) {
    // Get the access token from the Auth0 client
    const token = await auth0.getTokenSilently();

    let url = apiUrl + "delete?" + new URLSearchParams({
        key: key
    })
    const response = await fetch(url, {
        method: 'DELETE', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer'
    });
    return response.json();
}


// Post to API
async function postData(url = '', data = {}) {
    // Get the access token from the Auth0 client
    const token = await auth0.getTokenSilently();

    const response = await fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer',
        body: JSON.stringify(data)
    });
    return response.json();
}