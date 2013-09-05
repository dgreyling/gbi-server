$(document).ready(function() {
    if ( $("#is_protected").prop("checked") ) {
        toggle_userpw()
    }

    $("#is_protected").click(function() {
        toggle_userpw()
    });
});

function toggle_userpw() {
    if ( $("#is_protected").prop("checked") ) {
        $("#username").prop('disabled', 'disabled')
        $("#password").prop('disabled', 'disabled')
    } else {
        $("#username").prop('disabled', '')
        $("#password").prop('disabled', '')
    }
}