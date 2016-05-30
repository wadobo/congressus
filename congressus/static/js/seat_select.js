function assignSeat() {
    console.log("assignSeat");
    var seats = {}; // sid: {id, length}
    $('[id^="seats-"]').each(function() {
        // Get session id
        id = $(this).attr("id");
        ini = parseInt(id.indexOf("-")) + 1;
        sid = parseInt(id.substring(ini, id.length));
        seats[sid] = {};

        // Get values of session
        var values = $(this).val().split(",");
        // If not values, assign auto
        if (values == "") {
            console.log("ID", sid, $("#"+sid).val());
            // TODO: autoassign
            return;
        }
        for (val in values) {
            to = values[val].indexOf("_");
            res = values[val].substring(0, parseInt(to));
            if (res in seats[sid]) {
                seats[sid][res] = seats[sid][res] + 1;
            } else {
                seats[sid][res] = 1;
            }
        }
    });

    // Update badges
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
