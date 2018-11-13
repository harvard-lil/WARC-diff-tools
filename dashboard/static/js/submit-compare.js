//buttons
var lookUpBtn = $('#look-up-archives');
var cancelBtn = $('#cancel');
var submitBtn = $('#submit');
var oldestDate = new Date('1995-01-01');
var form = $('#create-compare-form');

var validateForm = function() {
  var $inputs = $('#create-compare-form :input');
  var invalid = 0;
  for (var i = 0; i < $inputs.length; i++) {
    var input = $inputs[i];
    if ($(input).attr('type') === 'url') {
      if (input.validity.typeMismatch) {
        $(input).next('.error').text('Please enter a valid URL');
        invalid += 1;
      } else if  (!$(input).val()) {
        $(input).next('.error').text('This field is required');
        invalid += 1;
      } else {
        $(input).next('.error').text('');
        invalid -= 1;
      }
    } else if ($(input).attr('type') === 'date') {
      if ($(input).val()) {
        var validDate = validateDate($(input));
        if (!validDate) {
          invalid += 1;
        } else {
          clearError($(input));
          invalid -= 1;
        }
      } else {
        $(input).next('.error').text('This field is required');
      }
    }
  }
  return invalid <= 0
};

var clearError = function (el) {
  el.next('.error').text('');
};

var clickLookUp = function(evt) {
  var valid = false;
  lookUpBtn.on('click', function(){
    valid = validateForm();
    if (valid) {
      document.createcompareform.submit()
    }
  });

};
var today = new Date();


var validateDate = function(date_el) {
  if (!date_el || !date_el.val()){
    $(date_el).next('.error').text('This field is required');
    return false;
  } else {
    var old_date = new Date(date_el.val());
    if (isNaN(old_date)) {
      $(date_el).next('.error').text('Please enter a valid date');
      return false;
  }

    if (old_date > today) {
      $(date_el).next('.error').text('Please enter a date in the past');
      return false;
    } else if (old_date < oldestDate) {
      $(date_el).next('.error').text('Please enter a date in the future');
      return false;
    }
  }
  return true;
};

document.addEventListener("DOMContentLoaded", function(){
  clickLookUp();
});