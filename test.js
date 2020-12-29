fd = new FormData()
fd.append('file', )

var req = fetch('/streamer', {
    method: 'post',
    body: fd /* or aFile[0]*/
  }); // returns a promise
  
  req.then(function(response) {
    // returns status + response headers
    // but not yet the body, 
    // for that call `response[text() || json() || arrayBuffer()]` <-- also promise
  
    if (res.ok) {
      // status code was 200-299
    } else {
      // status was something else
    }
  }, function(error) {
    console.error('failed due to network error or cross domain')
  })