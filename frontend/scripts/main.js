
const apiUrl = "https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/"
var delay = 1000; // that's 1 seconds of not typing
var timer = null;


function init() {

}

function submitPost() {
    console.log("Submitting post!")


    //TODO: Check if all fields are filled 

    // Construct json object from form 
    let post = {
        "title": document.getElementById('ftitle').value,
        "date": document.getElementById('fdate').value,
        "author": document.getElementById('fauthor').value,
        "content": document.getElementById('ftext').value
    }
    let url = apiUrl + "upload"
    // Upload post via Rest-Api 
    postData(url, post).then(data => {
        alert(data['msg'])
    });

}


function isTyping() {
    // Automatic Markdown-Preview when the user is tpying 
    clearTimeout(timer);
    var value = document.getElementById('ftext').value;
    if (value) {
        preview()
        timer = setTimeout(notTyping, delay);
    }
}

function preview() {
    // TODO: Sanitize HTML here -> else XSS möglich
    ftext = document.getElementById('ftext').value
    document.getElementById('preview').innerHTML = marked.parse(ftext);
}

function listObjects() {
    getObjects().then(objects => {
        keys = objects['Contents']

        // Create a table from array and insert it into the document
        container = document.getElementById("objectTableContainer")
        table = document.createElement("table")
        container.appendChild(table)
        for (var i = 0; i < keys.length; i++) {
            var tr = table.insertRow(-1)
            tr.innerHTML = keys[i]
        }
    })
}

async function getObjects() {
    url = apiUrl + "list"
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
    data = {
        "key": key
    }
    url = apiUrl + "delete"
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
        referrerPolicy: 'no-referrer',
        body: JSON.stringify(data)
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