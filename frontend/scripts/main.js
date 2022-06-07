// Global Consts and init stuff
const apiUrl = "https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/"
var delay = 1000; // that's 1 seconds of not typing
var timer = null;
var auth0 = null;
var token = null;
var refreshDelay = 4000;
var pageCounter = 1;

// initalize the application
window.onload = async () => {
    // setup auth0
    await configureClient();
    const isAuthenticated = await auth0.isAuthenticated();

    if (isAuthenticated) {
        token = await auth0.getTokenSilently();

        // update ui elements for startup
        updateUI()
        pagedObjectPreview()
        setDefaultDateForPost()

        return;
    }
    // check for the code and state parameters
    const query = window.location.search;

    if (query.includes("code=") && query.includes("state=")) {

        // Process the login state
        await auth0.handleRedirectCallback();
        token = await auth0.getTokenSilently();
        updateUI()

        // Use replaceState to redirect the user away and remove the querystring parameters
        window.history.replaceState({}, document.title, "/");

        // Load List Objects and update ui
        updateUI()
        pagedObjectPreview()
        setDefaultDateForPost()
    }
};

const updateUI = async () => {
    const isAuthenticated = await auth0.isAuthenticated();
    // hide contents of the single-page-application to make the login feel more fluid
    setDisplayByID("btn-login", !isAuthenticated)
    setDisplayByID("btn-logout", isAuthenticated)
    setDisplayByID("spa", isAuthenticated)
    setDisplayByID("login-text", !isAuthenticated)
};

function setDisplayByID(id, boolean) {
    var elm = document.getElementById(id)
    if (boolean) {
        elm.style.display = "block";
    } else {
        elm.style.display = "none";
    }
}

function setVisibilityByID(id, boolean) {
    var elm = document.getElementById(id)

    if (boolean) {
        elm.style.visibility = "visible"
    } else {
        elm.style.visibility = "hidden"
    }
}


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

    marked.use({
        breaks: true,
        sanitize: true,
    });

    // Preview in box
    document.getElementById('createPreview').innerHTML = marked.parse(clean);
}


function displayPost(key) {
    getObject(key).then(resp => {
        // The .md files on the server are in Hugo-Format. We need to extract only the markdown content from the files
        let postParts = b64DecodeUnicode(resp['body']).split('---');
        document.getElementById('getPreview').innerHTML = marked.parse(postParts[2]);
    }).catch((error) => {
        Swal.fire({
            icon: "error",
            text: "Ein Error ist mit der API aufgetreten." + error
        });
    });
}

function b64DecodeUnicode(str) {
    // b54 decoding  from bytestream, to percent-encoding, to original string. We can't use atob() if we want to preserve the utf-8 functionality 
    return decodeURIComponent(atob(str).split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
}

// Post Submitting 

function getPostContent() {
    let fields = {
        "title": document.getElementById('ftitle').value,
        "date": document.getElementById('fdate').value,
        "author": document.getElementById('fauthor').value,
        "content": document.getElementById('mdUserText').value
    }

    // check if every form field is filled
    let allFilled = Object.values(fields).filter(e => e.length >= 1);

    if (allFilled.length == 4) {
        return fields
    } else {
        // we dont have any post content
        return
    }
}

function createPostFromUi() {
    // Creates a post object from ui data and submits it to the backend via createPost()
    let post = getPostContent()

    // Abort Condition if some post fields are not filled
    if (!post) {
        Swal.fire({
            title: 'Felder fehlen! ',
            text: "Nicht alle Felder wurden ausgefüllt! Bitte fülle alle Felder aus.",
            icon: "error",
        });
        return
    }
    createPost(post)
}

function createPost(postObject) {
    // Creates a post in the backend via the api
    postData(apiUrl + "upload", post).then(response => {
        if (response.status == 200) {
            response.json().then(_data => {
                Swal.fire({
                    title: 'Post erstellt.',
                    text: "Der Post wurde erfolgreich in das Backend hochgeladen",
                    icon: "success",
                });
                // Refresh view
                clearPostFields();
                setTimeout(pagedObjectPreview, refreshDelay);
            })

        } else if (response.status == 400) {
            response.json().then(data => {
                Swal.fire({
                    title: 'Fehlermeldung',
                    text: data['msg'],
                    icon: "question",
                });
                // Refresh view
                clearPostFields();
                setTimeout(pagedObjectPreview, refreshDelay);
            })
        }
    }).catch((error) => {
        Swal.fire({
            title: 'Etwas ist schiefgelaufen :-(',
            text: "Ein Error ist mit der Netzwerkverbindung aufgetreten." + error,
            icon: "error",
        });
    });
}

function clearPostFields() {
    // Clear all fields for a fresh start
    document.getElementById('preview').innerHTML = null
    document.getElementById('ftitle').value = ""
    document.getElementById('fdate').value = ""
    document.getElementById('fauthor').value = ""
    document.getElementById('mdUserText').value = ""
}

// Object Preview
function setDefaultDateForPost() {
    // Safari handles date input forms different then firefox. We need to set a date here on startup
    var today = new Date().toISOString().split('T')[0];
    document.getElementById("fdate").value = today;
}

function constructObjectRow(child1, child2) {
    // check if the provided vars are actual objects
    if (child1 != null) {
        div.appendChild(child1)
    }
    if (child2 != null) {
        div.appendChild(child2)
    }
    return div
}

function constructObject(key) {
    // constructObjects constructs a html element that displays an markdown post

    // Creating wrapper object for file object 
    let div = document.createElement("div")
    div.setAttribute("class", "row singleObject")

    // Description part 
    let divC1 = document.createElement("div")
    divC1.setAttribute("class", "column")
    let p = document.createElement("p")
    p.setAttribute("class", "objectTitle")
    p.innerHTML = key
    divC1.appendChild(p)

    // Inner Elements get and delete
    let divC2 = document.createElement("div")
    divC2.setAttribute("class", "column")

    // Get Button
    let imgG = document.createElement("img")
    imgG.src = "images/icons/view.webp"
    imgG.alt = "Download"
    imgG.setAttribute("class", "icon")

    imgG.setAttribute("onclick", "displayPost('" + key + "')")

    // Delete Button
    let imgD = document.createElement("img")
    imgD.src = "images/icons/delete.webp"
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

function previewObjects(objectKeys) {
    // Reset preview of objects
    let list = document.getElementById('objectList');
    list.innerHTML = null;


    // Output a warning message if the user reaches an empty object page
    if (objectKeys.length == 0) {
        Swal.fire({
            icon: "info",
            text: "Es existieren keine weiteren Objekte"
        });
    }

    // Construct HTML Objects to display object keys
    for (var i = 0; i < objectKeys.length; i += 2) {

        // Check if we have file objects and then create a control html element for them
        let div = document.createElement("div")
        div.setAttribute("class", "row")
        if (objectKeys[i]) {
            div.append(constructObject(objectKeys[i]))
        }
        if (objectKeys[i + 1]) {
            div.append(constructObject(objectKeys[i + 1]))
        }
        list.appendChild(div);
    }
}

function pagedObjectPreview() {
    // Helper Function for previewing the current page 
    getObjectKeysForCurrentPage().then(data => {
        previewObjects(data);
        updatePagingUI()
    });
}

async function updatePagingUI() {
    // update paging counter asynchronisly 
    document.getElementById("pageNumCounter").innerHTML = pageCounter

    // request the next page from the api and 
    getObjects(pageCounter + 1).then(response => {
        let keys = response['Contents'];

        // update the button status to reflect if we have more pages or not
        let apiHasMoreItems = (keys.length != 0)
        document.getElementById("btn-pageUp").disabled = !apiHasMoreItems

        // Enable and disable the back button if we have pages over 1
        if (pageCounter == 1) {
            document.getElementById("btn-pageDown").disabled = true
        } else {
            document.getElementById("btn-pageDown").disabled = false

        }
    });
}

function pageUp() {
    pageCounter += 1
    pagedObjectPreview()
}

function pageDown() {
    if (pageCounter > 1) {
        pageCounter -= 1
        pagedObjectPreview()
    }
}

function getObjectKeysForCurrentPage() {
    // Extract Keys for current page
    return getObjects(pageCounter).then(response => {
        return response['Contents'];
    })
}

// Delete Functionallity
function deletePostPrompt(key) {
    // Confirm if the user really wants to delete the item
    Swal.fire({
        title: "Möchtest du das wirklich?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Löschen!'
    }).then((result) => {
        /* Read more about isConfirmed, isDenied below */
        if (result.isConfirmed) {
            Swal.fire('Poof! Deine Post wurde gelöscht!', '', 'success')
            deletePost(key)
            // Refresh view 
            setTimeout(pagedObjectPreview, refreshDelay)
        }
    })
}