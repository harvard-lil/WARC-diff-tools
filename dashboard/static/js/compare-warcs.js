var resizeTimeout, wrapper;
var detailsButtons = $(".btn-resource-details");

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function init () {
  adjustTopMargin();
  var clicked = false;
  if (detailsButtons) {
    $(".resource-row").hide();
    for (var i=0; i < detailsButtons.length; i++) {
      var btn = detailsButtons[i];
      $("#" + btn.id).click(function(evt){
        clicked = !clicked;
        handleShowDetails(clicked, evt.target.id);
      });
    }
  }

  window.onresize = function(){
    if (resizeTimeout)
      clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(adjustTopMargin, 200);
  };
  // callBackgroundTask();
}

function callBackgroundTask() {
  var csrftoken = getCookie('csrftoken');
  var url = 'background/' + window.compare_id;

  $.ajax({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      },
      url: url,
      method: "POST",
      csrfmiddlewaretoken : csrftoken
      }).done(function () {
    console.log('done!');
  })
}


function handleShowDetails (open, btn_id) {
  var resource_type = btn_id.split("resource-count-")[1];
  if (open) {
    $(".comparison-table").css('display', 'block');
    if (resource_type === "changed") {
      $(".resource-changed").show();
      $(".resource-added").hide();
      $(".resource-missing").hide();
    } else if (resource_type === "added") {
      $(".resource-added").show();
      $(".resource-changed").hide();
      $(".resource-missing").hide();
    } else if (resource_type === "missing") {
      $(".resource-missing").show();
      $(".resource-changed").hide();
      $(".resource-added").hide();
    } else if (resource_type === "total") {
      $(".resource-row").show();
    }
  } else {
    $(".resource-row").hide();
    $(".comparison-table").hide();
  }
}

function adjustTopMargin () {
  wrapper = document.getElementsByClassName("capture-wrapper")[0];
  var header = document.getElementsByTagName('header')[0];
  if (!wrapper) return;
  // wrapper.style.marginTop = header.offsetHeight+"px";
  wrapper.style.marginTop = "0px";
}

init();

document.addEventListener("DOMContentLoaded",function(){
  setTimeout(function(){
    callBackgroundTask();
  }, 2000);
});
