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
