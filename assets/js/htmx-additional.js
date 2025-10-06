import htmx from 'htmx.org';
import 'htmx-ext-sse';
import Swal from 'sweetalert2'

window.htmx = htmx;

htmx.config.responseHandling = [
  {"code":"204", "swap": false},
  {"code":"[23]..", "swap": true},
  {"code":"422", "swap": true, "error": true},
  {"code":"[45]..", "swap": false, "error":true},
  {"code":"...", "swap": true}
]

document.addEventListener("htmx:confirm", function (e) {
  if (!e.detail.elt.hasAttribute('hx-confirm')) return

  e.preventDefault()
  Swal.fire({
    title: "Are you sure?",
    text: `${e.detail.question}`
  }).then(function (result) {
    if (result.isConfirmed) {
      // If the user confirms, we manually issue the request
      e.detail.issueRequest(true); // true to skip the built-in window.confirm()
    }
  })
})


document.addEventListener("htmx:responseError", function (e) {
  const xhr = e.detail.xhr

  let msg = JSON.parse(xhr.responseText);
  if (msg instanceof Object) {
    msg = msg.detail[0].msg;
  }
  ToastCustom(`Code ${xhr.status} - ${msg}`, "error")
})

document.body.addEventListener('htmx:sseClose', function (e) {
    const reason = e.detail.type
    switch (reason) {
        case "nodeMissing":
          break;
        case "nodeReplaced":
          break;
        case "message":
          const spinner = document.getElementById("sse-spinner");
          if (spinner) {
              spinner.remove();
          }
          break;
    }
})
