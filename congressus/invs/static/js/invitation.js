$(document).ready( function() { 
    input_seat = $("#id_seats");
    span = $("<span id='span_seats'></span>");
    span.insertAfter(input_seat);
    input_seat.keyup(function() {
        invi_type = $("#id_type").val();
        value = input_seat.val();
        $.ajax({
            type: "POST",
            data: {'invi_type': invi_type, 'string': value},
            dataType: 'JSON',
            url: "/seats/bystr/",
            success: function(msg) {
                if (msg.error) {
                    m = msg.error;
                } else {
                    m = "Total:" + msg.total + "-->" + msg.values;
                }
                $("#span_seats").text(m);
            }
        });
    });
});
