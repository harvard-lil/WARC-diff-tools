// document.addEventListener("DOMContentLoaded",function(){

var s = new WebSocket("ws://localhost:8082/websocket/");
// debugger;
s.onopen = function(e) {
  console.log("onopen, connected !!!", e);
  console.log(s);
  s.send("ciao");
};

s.onmessage = function(e) {
    console.log('onmessage', e);
    var bb = document.getElementById('blackboard')
    var html = bb.innerHTML;
    bb.innerHTML = html + '<br/>' + e.data;
};

s.onerror = function(e) {
  console.log('onerror received!', e);
};

s.onclose = function(e) {
  console.log("onclose, connection closed", e);
};

// });
function invia() {
  console.log('clicking invia');
  var value = document.getElementById('testo').value;
  console.log('attempting to send value', value);
  s.send(value);
}

// if secure, needs to  be different scheme
// ws_scheme = 'ws'
// if 'HTTPS' in env or env['wsgi.url_scheme'] == 'https':
//     ws_scheme = 'wss'
//
