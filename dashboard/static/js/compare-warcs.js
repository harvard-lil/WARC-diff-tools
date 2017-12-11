var resizeTimeout, wrapper;

var detailsButtons = $(".btn-resource-details");

var detailsTray = document.getElementById("collapse-details");

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
}

function handleShowDetails (open, btn_id) {
  var resource_type = btn_id.split("resource-count-")[1];
  if (open) {
    $(".comparison-table").show();
    if (resource_type === "modified") {
      $(".resource-modified").show();
      $(".resource-added").hide();
      $(".resource-missing").hide();
    } else if (resource_type === "added") {
      $(".resource-added").show();
      $(".resource-modified").hide();
      $(".resource-missing").hide();
    } else if (resource_type === "missing") {
      $(".resource-missing").show();
      $(".resource-modified").hide();
      $(".resource-added").hide();
    } else if (resource_type === "total") {
      $(".resource-row").show();
    }
  } else {
    $(".resource-row").hide();
    $(".comparison-table").hide();
  }
  detailsTray.style.display = open ? "block" : "none";
}

function adjustTopMargin () {
  wrapper = document.getElementsByClassName("capture-wrapper")[0];
  var header = document.getElementsByTagName('header')[0];
  if (!wrapper) return;
  // wrapper.style.marginTop = header.offsetHeight+"px";
  wrapper.style.marginTop = "0px";
}

init();
