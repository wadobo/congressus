function getSession(input) {
    // Get session id
    id = $(input).attr("id");
    ini = parseInt(id.indexOf("-")) + 1;
    return parseInt(id.substring(ini, id.length));
}

function autoSeats(session, amount_seats) {
    var deferred = new $.Deferred();
    $.ajax({
        type: "POST",
        data: {session: session, amount_seats: amount_seats},
        dataType: 'JSON',
        url: "/seats/auto/",
        success: function(msg){
            deferred.resolve(msg["seats"]);
        }
    });
    return deferred.promise();
}

function updateBadges(seats) {
    for (var sid in seats) {
        if (seats.hasOwnProperty(sid)) {
            for (var key in seats[sid]) {
                if (seats[sid].hasOwnProperty(key)) {
                    value = seats[sid][key];
                    $("#badge-"+sid+"-"+key).text(value);
                }
            }
        }
    }
}

function markSeats(seats, session_id, session_seats) {
    for (ss in session_seats) {
        to = session_seats[ss].indexOf("_");
        res = session_seats[ss].substring(0, parseInt(to));
        if (res in seats[session_id]) {
            seats[session_id][res] = seats[session_id][res] + 1;
        } else {
            seats[session_id][res] = 1;
        }
    }
    updateBadges(seats);
}

function assignSeat() {
    var seats = {}; // sid: {id, length}
    $('[id^="seats-"]').each(function() {
        session_id = getSession(this);
        seats[session_id] = {};

        // Get session seats
        var session_seats = $(this).val().split(",");

        // If not session seats, assign auto
        if (session_seats == "") {
            amount_seats = Number($("#"+session_id).val());
            if (amount_seats > 0) {
                autoSeats(session_id, amount_seats).then(function(autoseats) {
                    for (as in autoseats) {
                        obj = autoseats[as];
                        id = "#"+obj.session+"_"+obj.space+"_"+obj.row+"_"+obj.col;
                        $("#"+obj.session+"_"+obj.space+"_"+obj.row+"_"+obj.col).click();
                    }
                    session_seats = $("#seats-"+obj.session).val().split(",");
                    markSeats(seats, obj.session, session_seats);
                });
            }
        } else {
            markSeats(seats, session_id, session_seats);
        }
    });

}
