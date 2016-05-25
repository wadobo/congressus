function check_warning(w, sessions) {
    if (w.type == 'req') {
        var firstFound = true;
        var secondFound = true;
        var ss = [];
        w.sessions1.forEach(function(s1) { ss.push(s1); });
        w.sessions2.forEach(function(s2) { ss.push(s2); });

        for (var i=0; i<w.sessions1.length; i++) {
            if (sessions.indexOf(w.sessions1[i]) < 0) {
                firstFound = false;
            }
        }
        for (var i=0; i<w.sessions2.length; i++) {
            if (sessions.indexOf(w.sessions2[i]) < 0) {
                secondFound = false;
            }
        }

        if (firstFound && !secondFound) {
            return true;
        }

        return false;
    }
}

function seatCB(ev, seat) {
    var row = seat.data("row");
    var col = seat.data("col");
    var session = seat.data("session");
    var layout = seat.data("layout");

    var current = [];
    var currentval = $("#seats-"+session).val();
    if (currentval) {
        current = currentval.split(",");
    }

    var str = layout + '_' + row + '_' + col;

    if (ev == 'select') {
        current.push(str);
    } else if (ev == 'unselect') {
        var idx = current.indexOf(str);
        if (idx >= 0) {
            current.splice(idx, 1);
        }
    }

    $("#seats-"+session).val(current.join(","));
    $("#"+session).val(current.length);
}

$(document).ready(function() {
    $("form").submit(function() {
        var warnings = [];
        var sessions = [];

        $('.sessioninput').each(function() {
            val = parseInt($(this).val(), 10);
            id = $(this).attr("id");
            if (val) {
                sessions.push(id);
            }
        });

        $('.warning').each(function() {
            var warning = {};
            warning.name = $(this).data('name');
            warning.sessions1 = String($(this).data('sessions1')).split(',');
            warning.sessions2 = String($(this).data('sessions2')).split(',');
            warning.type = $(this).data('type');
            warning.message = $(this).data('message');
            warnings.push(warning);
        });

        for(var i=0; i<warnings.length; i++) {
            var w = warnings[i];
            if (check_warning(w, sessions)) {
                return confirm(w.message);
            }
        }

        return true;
    });

    $(".seatmap").each(function() {
        var session = $(this).data('session');
        var obj = $("#modal-" + session);
        SeatMap.bindLayout(obj);

        // TODO remove this
        // example to show how to mark a seat as occupied to sync between
        // clients with socket.io

        //setTimeout(function() {
        //    var layout = '1';
        //    var position = '2_2';
        //    var selector = ".display-"+session+'-'+layout + ' .preview';
        //    console.log(selector);
        //    $(selector).seatCharts().status(position, "unavailable");
        //}, 5000);
    });
    SeatMap.cbs.add(seatCB);

    // removing reserved seats
    $(".seat-reserved").each(function() {
        var session = $(this).data('session');
        var layout = $(this).data('layout');
        var seat = $(this).data('seat').replace(/-/g, '_');
        var selector = '#' + session + '_' + layout + '_' + seat;
        $(selector).addClass("seat-R");
        $(selector).removeClass("seat-L");
    });

    $(".seats-input").each(function() {
        var session = $(this).data('session');
        var v = $(this).val();
        if (v) {
            var current = [];
            current = v.split(",");
            current.forEach(function(c) {
                var selector = '#' + session + '_' + c;
                $(selector).addClass("seat-selected");
            });
            $("#"+session).val(current.length);
        }
    });
});
