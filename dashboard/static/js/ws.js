// var socket = new ReconnectingWebSocket("ws://" + window.location.host + "/websocket/", []);
//
// socket.send(JSON.stringify({
//   data: 'compare'
// }));


var s = new WebSocket("ws://" + window.location.host + "/websocket/");
s.onopen = function(e) {
  console.log("onopen, connected !!!", e);
  s.send(formatWSMessage("connected", "connection established", ""));
};

s.onmessage = function(msg) {
    var parsed = JSON.parse(msg.data);
    if(parsed.data.task === "initial_compare"){
      $('#go-to-compare').prop("disabled",false);
    }
    if ('compare_id' in Object.keys(parsed) && parsed.compare_id === compare_id) {
      if (parsed.reason === "check_compare_status") {
        if (parsed.response === true) {
          $('#go-to-compare').prop("disabled",false);
        } else if (parsed.response === false) {

          $('#go-to-compare').prop("disabled",true);
        }
      }
    }
    console.log('onmessage', formatWSMessage(msg));
};

s.onerror = function(e) {
  console.log('onerror received!', formatWSMessage(e));
};

s.onclose = function(e) {
  console.log("onclose, connection closed", formatWSMessage(e));
};

var formatWSMessage = function(reason, message, data) {
  return JSON.stringify({
    "reason": reason ? reason : '',
    "message": message ? message : '',
    "data": data ? data : ''
  })
};
