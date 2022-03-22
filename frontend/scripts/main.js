
const apiUrl = "https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/"

function submitPost() {
    console.log("Submitting post!")

    // Construct json object from form 
    let post = {
        "title": document.getElementById('ftitle').value,
        "date": document.getElementById('fdate').value,
        "author": document.getElementById('fauthor').value,
        "content": document.getElementById('ftext').value
    }
    let url = apiUrl + "upload"
    postData(url, post).then(data => {
        alert(data['msg'])
    });

}

function preview() {
    console.log("Displaying preview of post!")

    ftext = document.getElementById('ftext').value
    document.getElementById('preview').innerHTML = marked.parse(ftext);
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