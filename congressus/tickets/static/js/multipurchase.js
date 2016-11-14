// Fix to make startsWith work in IE 11
if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position) {
        position = position || 0;
        return this.substr(position, searchString.length) === searchString;
    };
}

var loading = '<span class="glyphicon glyphicon-refresh spinning"></span>';
var seaticon = '<span class="glyphicon glyphicon-th"></span>';
var sessionsloading = {};

function loadingSession(s, isloading) {
    if (isloading) {
        $("#tooltip-"+s).html(loading);
        $(".plus[data-id="+s+"]").attr("disabled", "");
        $(".minus[data-id="+s+"]").attr("disabled", "");
    } else {
        $("#tooltip-"+s).html(seaticon);
        $(".plus[data-id="+s+"]").removeAttr("disabled");
        $(".minus[data-id="+s+"]").removeAttr("disabled");
    }
    setLoading(s, isloading);
}

function setLoading(id, isloading) {
    if (isloading) {
        sessionsloading[id] = true;
    } else {
        sessionsloading[id] = false;
    }

    for (i in sessionsloading) {
        if (sessionsloading[i]) {
            $("#finish").attr("disabled", "");
            return;
        }
    }

    $("#finish").removeAttr("disabled");
}

var old_session = -1;
var old_layout = -1;

delays = {};
selected_seats = {};

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
    } else if (ev == 'autoseat') {
        autoSelectSeatCB(data.session, data.seats, data.error);
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

    updateBadges(session, layout);

    $("#"+session).keydown();
}

function updateBadges(session, layout) {
    //updating the label with the number of selected seats
    var currentval = $("#seats-"+session).val();
    var current = currentval.split(",");
    var n = 0;
    current.forEach(function(element) {
        if (element.startsWith(layout + '_')) {
            n++;
        }
    });
    badge = $("#badge-"+session+"-"+layout);
    badge.text(n);
    if (n) {
        badge.addClass("label-success");
        badge.removeClass("label-default");
    } else {
        badge.removeClass("label-success");
        badge.addClass("label-default");
    }
    // Remove old badges. recursive function
    if (old_session != -1 && (old_session != session || old_layout != layout)) {
        updateBadges(old_session, old_layout);
    }
    old_session = session;
    old_layout = layout;
}

function recalcSums(obj) {
    var session = obj.attr("id");
    var val = parseInt(obj.val(), 10);

    if (isNaN(val)) {
        obj.val(0);
        val = 0;
    }

    var max = parseInt(obj.attr('max') || 500, 10);
    if (val > max) {
        val = max;
        obj.val(max);
    }

    var price = parseFloat(obj.data("price"));
    $("#"+session+"-subtotal-price").html(val * price);
}

function recalcTotal() {
    var sum = 0;
    $(".sessioninput").each(function() {
        var n = parseInt($(this).val(), 10);
        var price = parseFloat($(this).data("price"));
        sum += price * n;
    });
    $("#total").html(sum);
}

function fillSelectedSeats(obj) {
    // obj should be a .seats-input
    var session = obj.data('session');
    var v = obj.val();
    if (v) {
        var current = [];
        current = v.split(",");
        $("#"+session).val(current.length);
        $("#"+session).keydown();

        function recursiveSelection(arr, finish) {
            loadingSession(session, true);
            var c = arr.pop();
            var selector = '#' + session + '_' + c;
            var layout = c.split('_')[0];
            var l = $('.layout-'+session+'-'+layout);
            var obj = $('.display-'+session+'-'+layout);

            SeatMap.preloadLayout(l, obj, function() {
                updateBadges(session, layout);
                loadingSession(session, false);
                $(selector).addClass("seat-selected");
                if (arr.length) {
                    recursiveSelection(arr, finish);
                } else {
                    finish();
                }
            });
        }

        recursiveSelection(current.slice(0), function() {
            current.forEach(function(c) {
                var layout = c.split('_')[0];
                updateBadges(session, layout);
            });
        });
    } else {
        loadingSession(session, false);
    }
}

function autoSelectSeatCB(s, seats, error) {
    loadingSession(s, false);

    if (seats.length) {
        var value = [];
        seats.forEach(function(obj) {
            value.push(obj.layout+"_"+obj.row+"_"+obj.col);
        });
        $("#seats-"+s).val(value.join(","));
        fillSelectedSeats($("#seats-"+s));
    } else {
        if ($("#"+s).val() != 0) {
            $("#"+s).val(0);
            $("#"+s).select();
        }
        var layouts = $('#modal-'+s+' .layout');
        layouts.each(function() {
            var id = $(this).data('id');
            updateBadges(s, id);
        });
        alertify.alert(error);
        loadingSession(s, false);
    }
}

function autoSelectSeat(s, n) {
    loadingSession(s, true);
    ws.send('autoseats ' + s + ' ' + n + ' ' + client);
}

function cleanSelectedSeat() {
    selected_seats = {};
}

function seatsChange(obj) {
    // obj should be a .sessioninput
    if (!obj) {
        obj = $(this);
    }
    // Only recalcTotal and autoseats if seats are changed
    if (selected_seats[obj.attr('id')] ==  obj.val()) {
        return;
    } else {
        selected_seats[obj.attr('id')] =  obj.val();
    }

    recalcSums(obj);
    recalcTotal();

    // if no name in the input, it's a numbered session
    // we do here the seat auto selection
    if (!obj.attr("name")) {
        var val = obj.val();
        var s = obj.data('session');
        var v = $("#seats-"+s).val();
        if (!v) {
            autoSelectSeat(s, val);
        } else {
            var current = [];
            current = v.split(",");
            if (current.length != val) {
                // unselecting all selected
                current.forEach(function(c) {
                    selector = '#' + s + '_' + c;
                    $(selector).removeClass('seat-selected');

                    a = c.split('_');
                    args = s;
                    args += ' ' + a[0];
                    args += ' ' + a[1];
                    args += ' ' + a[2];
                    args += ' ' + client;
                    ws.send('drop_seat ' + args);
                });
                $("#seats-"+s).val("");

                autoSelectSeat(s, val);
            }
        }
    }
}

function preSubmit() {
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

    confirms = ""
    for(var i=0; i<warnings.length; i++) {
        var w = warnings[i];
        if (check_warning(w, sessions)) {
            confirms += w.message + "\n\n";
        }
    }
    return confirms;
}

$(document).ready(function() {

    $("#btn-continue").click(function() {
        confirms = preSubmit();
        if (confirms) {
            alertify.confirm(confirms, function(e) {
                if (e) {
                    $("form").submit();
                } else {
                    return false;
                }
            });
        } else {
            $("form").submit();
        }
    });

    $('.withtooltip').tooltip();

    $(".seatmap").each(function() {
        var session = $(this).data('session');
        var obj = $("#modal-" + session);
        SeatMap.bindLayout(obj);
    });

    SeatMap.cbs.add(seatCB);
    ws.cbs.add(websocketCB);

    if (session_expired) {
        $(".sessioninput").val("0");
        $(".seats-input").val("");
    }

    $(".seats-input").each(function() {
        fillSelectedSeats($(this));
    });

    // calculating sums
    $('.sessioninput').keydown(function(e) {
        if (e.keyCode == 13) {
            return;
        }
        var obj = $(this);
        var id = obj.attr('id');
        if (e.keyCode == 9 || e.keyCode == 16) {
            seatsChange(obj);
            clearTimeout(delays[id]);
            setLoading("delay" + id, false);
        } else {
            setLoading("delay" + id, true);
            clearTimeout(delays[id]);
            delays[id] = setTimeout(function() {
                seatsChange(obj);
                setLoading("delay" + id, false);
            }, 500);
        }
    });
    recalcTotal();

    $('.sessioninput').each(function() {
        selected_seats[$(this).attr('id')] = $(this).val();
        recalcSums($(this));
        $(this).click(function() { $(this).select(); });
    });

    $(".plus").click(function() {
        var id = '#' + $(this).data("id");
        var max = parseInt($(id).attr('max') || 500, 10);
        var current = parseInt($(id).val(), 10);

        var next = current + 1;
        if (next > max) {
            next = max;
        }
        $(id).val(next);
        $(id).keydown();
        $(".plus").blur();
    });
    $(".minus").click(function() {
        var id = '#' + $(this).data("id");
        var min = parseInt($(id).attr('min') || 0, 10);
        var current = parseInt($(id).val(), 10);

        var next = current - 1;
        if (next < min) {
            next = min;
        }
        $(id).val(next);
        $(id).keydown();
        $(".minus").blur();
    });
});
