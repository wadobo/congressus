function autoSeats(session, amount_seats) {
    var deferred = new $.Deferred();
    $.ajax({
        type: "POST",
        data: {session: session, amount_seats: amount_seats},
        dataType: 'JSON',
        url: "/seats/auto/",
        success: function(msg){
            if (msg.error) {
                deferred.reject(msg);
            } else {
                deferred.resolve(msg["seats"]);
            }
        }
    });
    return deferred.promise();
}
