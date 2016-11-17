var notifyTimer = null;
var enabled = true;

function gonormal() {
    $("body").removeClass("wrong");
    $("body").removeClass("right");
    $("body").removeClass("maybe");
    $("body").removeClass("incorrect");
}

function notify(what) {
    gonormal();
    $("body").addClass(what);
    var audio = new Audio($("#audio-"+what).attr('src'));
    audio.play();
    clearTimeout(notifyTimer);
    timeTimeout = 1000;
    if (what == 'right') {
        timeTimeout = 500;
    }
    notifyTimer = setTimeout(function() {
        gonormal();
        setEnabled(true);
    }, timeTimeout);

    args = ' ' + window.ac;
    args += ' ' + moment().format('YYYY-MM-DDTHH:mm:ss.SSSSSSZ');
    args += ' ' + what;
    ws.send('add_ac' + args);
}

function setEnabled(t) {
    enabled = t;
    if (!enabled) {
        $("#order").attr("disabled", "disabled");
        $("#ordergo").attr("disabled", "disabled");
    } else {
        $("#order").removeAttr("disabled");
        $("#ordergo").removeAttr("disabled");
        $("#order").focus();
    }
}

function makeReq() {
    if (!enabled) {
        return;
    }

    setEnabled(false);
    var req = $("#order").val();
    var url = $("#access").attr("action");

    $("#last").html(req);

    d = {'order': req};
    $.post(url, d, function(data) {
        notify(data.st);
        $("#extra").html(data.extra);
        $("#extra2").html(data.extra2);
    }).fail(function() {
        notify("wrong");
        $("#extra").html('');
        $("#extra2").html('');
    });
    $("#order").val("");
    $("#order").focus();
    return false;
}

function enableQrCode() {
    if (window.innerWidth <= 800) {
        $('#reader').html5_qrcode(
            function(data){
                $("#order").val(data);
                makeReq();
            },
            function(error){
                //show read errors
            }, function(videoError){
                //the video stream could be opened
            }
        );
    }
}

$(document).ready(function() {
    $("#access").submit(makeReq);

    enableQrCode();
});
