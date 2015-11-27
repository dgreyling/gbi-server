$(document).ready(function() {
    function toggleUserPassword() {
        if ( $('#is_protected').prop('checked') ) {
            $('#username').prop('disabled', 'disabled');
            $('#password').prop('disabled', 'disabled');
        } else {
            $('#username').prop('disabled', '');
            $('#password').prop('disabled', '');
        }
    }

    if ( $('#is_protected').prop('checked') ) {
        toggleUserPassword();
    }

    $('#is_protected').click(function() {
        toggleUserPassword();
    });

    function geojsonLink() {
        var viewCoverage =  $('#view_coverage').val();
        var geojsonURL = 'http://geojson.io/#data=data:application/json,';
        var url = geojsonURL + encodeURIComponent (viewCoverage);
        $('#load-geojson-io').prop('href', url);
    }

    $('#view_coverage').keyup(function() {
        geojsonLink();
    });
    geojsonLink();
});