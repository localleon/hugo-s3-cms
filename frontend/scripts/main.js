// Global Consts and init stuff
const apiUrl = "https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/"
var delay = 1000; // that's 1 seconds of not typing
var timer = null;
init()

function init() {
    console.log("Initalized Web-Application")
    listObjects()
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
    let url = apiUrl + "get/" + key

    const response = await fetch(url, {
        method: 'GET', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Content-Type': 'application/json'
            // TODO: Inject authorization headers here 
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer'
    });
    return response.json();
}

async function getObjects() {
    let url = apiUrl + "list"
    const response = await fetch(url, {
        method: 'GET', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Content-Type': 'application/json'
            // TODO: Inject authorization headers here 
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer',
    });
    return response.json();
}

async function deletePost(key) {
    let url = apiUrl + "delete/" + key
    const response = await fetch(url, {
        method: 'DELETE', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Content-Type': 'application/json'
            // TODO: Inject authorization headers here 
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer'
    });
    return response.json();
}


// Post to API
async function postData(url = '', data = {}) {
    const response = await fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE
        mode: 'cors',
        cache: 'no-cache',
        credentials: 'omit',
        headers: {
            'Content-Type': 'application/json'
            // TODO: Inject authorization headers here 
        },
        redirect: 'follow',
        referrerPolicy: 'no-referrer',
        body: JSON.stringify(data)
    });
    return response.json();
}