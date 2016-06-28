var notifyTimer = null;
var enabled = true;

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
    notifyTimer = setTimeout(function() {
        gonormal();
        setEnabled(true);
    }, 1000);
}

function setEnabled(t) {
    enabled = t;
    if (!enabled) {
        $("#order").attr("disabled", "disabled");
        $("#ordergo").attr("disabled", "disabled");
    } else {
        $("#order").removeAttr("disabled");
        $("#ordergo").removeAttr("disabled");
    }
}

function makeReq() {
    if (!enabled) {
        return;
    }

    setEnabled(false);
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

function enableQrCode() {
    var mobile = window.innerWidth <= 800;

    function detect_mobile() {
        var options = decodeURIComponent(window.location.search.slice(1))
                                         .split('&')
                                         .reduce(function _reduce (/*Object*/ a, /*String*/ b) {
                                           b = b.split('=');
                                           a[b[0]] = b[1];
                                           return a;
                                         }, {});
        nomobile = options.nomobile;

        if (navigator.userAgent.match(/iPad/i) != null)
            mobile = false;
        else if (navigator.userAgent.match(/iPhone/i) != null)
            mobile = true;
        else if (navigator.userAgent.match(/Android/i) != null)
            mobile = true;

        if (mobile && !nomobile) {
            document.location = 'http://www.ANCCE.es/app'
            //document.location = "{% url publicMobile concurso.codigoWeb %}"+window.location.search;
            return false;
        }

        return true;
    }

    if (mobile) {
        $('#reader').html5_qrcode(
            function(data){
                $("#order").val(data);
                alert(data);
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
