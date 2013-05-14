$(document).ready(function() {
    if ($.cookie('currentEnvironment') === null) {
        $.cookie('currentEnvironment', $('.envSelector option:selected').val(), { expires: 365, path: '/' });
    } else {
        $('.envSelector option[value="' + $.cookie('currentEnvironment') + '"]').prop('selected', true);
    }

    $('.envSelector').change(function() {
        $.cookie('currentEnvironment', $(this).find(':selected').val(), { expires: 365, path: '/' });
    });

    $('#refreshRateInput').val(0);

    // Silly closure example
    var totalTimePopup = refreshList(5000);
    $('#refreshRateInput').change(function() {
        setInterval(refreshItem, $('#refreshRateInput').val() * 1000, 'extraInfoFoSho');
    });

    if (!$('#refresh').length) {
        $('#navRefresh').hide();
    } else {
        document.onkeypress = stopRKey;
    }

});

function refreshList(interval) {
    var interval = interval;
    var totalMonitorTime = 0;
    return function () {
        totalMonitorTime = totalMonitorTime + interval;
//        alert("monitored for " + totalMonitorTime + ", " + extraInfo);
        location.reload(true);
    }
};

function refreshItem() {
    $.get("/primitive/" + document.URL.split("/").pop(), function(data) {
        if ($('.primitive').html() != $(data).html()) {
            $('.primitive').fadeTo(250, 0, function () {
                $('.primitive').replaceWith($(data).hide());
                $('.primitive').fadeIn(250);
            });
        }
    });
};

function stopRKey(evt) { 
    var evt = (evt) ? evt : ((event) ? event : null); 
    var node = (evt.target) ? evt.target : ((evt.srcElement) ? evt.srcElement : null); 
    if ((evt.keyCode == 13) && (node.type=="text")) {
        document.activeElement.blur();
        return false;
    }
}
