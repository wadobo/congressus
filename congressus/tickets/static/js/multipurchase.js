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

function seat_droped(session, layout, seat) {
    var selector = '#' + session + '_' + layout + '_' + seat;
    $(selector).addClass("seat-L");
    $(selector).removeClass("seat-H");
    $(selector).unbind("click").click(function() {
        SeatMap.clickSeat($(this));
    });
}

function seat_holded(session, layout, seat) {
    var selector = '#' + session + '_' + layout + '_' + seat;

    if ($(selector).hasClass("seat-selected")) {
        return;
    }

    $(selector).addClass("seat-H");
    $(selector).removeClass("seat-L");
    $(selector).unbind("click");
}

function seat_reserved(session, layout, seat) {
    var selector = '#' + session + '_' + layout + '_' + seat;
    $(selector).addClass("seat-R");
    $(selector).removeClass("seat-L");
    $(selector).removeClass("seat-H");
    $(selector).unbind("click");
}

function websocketCB(ev, data) {
    if (ev == 'hold') {
        var seat = data.row + '_' + data.col;
        seat_holded(data.session, data.layout, seat);
    } else if (ev == 'drop') {
        var seat = data.row + '_' + data.col;
        seat_droped(data.session, data.layout, seat);
    } else if (ev == 'confirm') {
        var seat = data.row + '_' + data.col;
        seat_reserved(data.session, data.layout, seat);
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

    args = session;
    args += ' ' + layout;
    args += ' ' + row;
    args += ' ' + col;
    args += ' ' + client;

    if (ev == 'select') {
        current.push(str);
        ws.send('hold_seat ' + args);
    } else if (ev == 'unselect') {
        var idx = current.indexOf(str);
        if (idx >= 0) {
            current.splice(idx, 1);
        }
        ws.send('drop_seat ' + args);
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
    });

    SeatMap.cbs.add(seatCB);
    ws.cbs.add(websocketCB);

    // removing holds seats
    $(".seat-holded").each(function() {
        var session = $(this).data('session');
        var layout = $(this).data('layout');
        var seat = $(this).data('seat').replace(/-/g, '_');
        var selector = '#' + session + '_' + layout + '_' + seat;
        seat_holded(session, layout, seat);
    });

    // removing reserved seats
    $(".seat-reserved").each(function() {
        var session = $(this).data('session');
        var layout = $(this).data('layout');
        var seat = $(this).data('seat').replace(/-/g, '_');
        seat_reserved(session, layout, seat);
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
