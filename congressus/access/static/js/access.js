var notifyTimer = null;

function gonormal() {
    $("body").removeClass("wrong");
    $("body").removeClass("right");
    $("body").removeClass("maybe");
}

function notify(what) {
    gonormal();
    $("body").addClass(what);
    var audio = new Audio($("#audio-"+what).attr('src'));
    audio.play();
    clearTimeout(notifyTimer);
    notifyTimer = setTimeout(gonormal, 1000);
}

function makeReq() {
    var req = $("#order").val();
    var url = $("#access").attr("action");
    d = {'order': req};
    $.post(url, d, function(data) {
        notify(data.st);
        $("#extra").html(data.extra);
    }).fail(function() {
        notify("wrong");
        $("#extra").html('');
    });
    $("#order").val("");
    $("#order").focus();
    return false;
}

$(document).ready(function() {
    $("#access").submit(makeReq);
});
