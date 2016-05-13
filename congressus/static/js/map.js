function show_layout(obj) {
    var layout = obj.data('layout');
    var dir = ' <span class="glyphicon '+obj.data('glyph')+'" aria-hidden="true"></span>';
    $('#layout').html(obj.data('name') + dir);
    $('#preview').remove();
    $('#display').append('<div id="preview"></div>');
    var sc = $('#preview').seatCharts({
        map: layout.split("\n"),
        seats: {
            L: {
                price   : 50,
                classes : 'front-seat'
            },
            O: {
                classes : 'unavailable'
            },
            R: {
                classes : 'unavailable'
            }

        },
        click: function () {
            if (this.status() == 'available') {
                //do some stuff, i.e. add to the cart
                return 'selected';
            } else if (this.status() == 'selected') {
                //seat has been vacated
                return 'available';
            } else if (this.status() == 'unavailable') {
                //seat has been already booked
                return 'unavailable';
            } else {
                return this.style();
            }
        }
    });
}

$(document).ready(function() {
    $(".layout").click(function() {
        show_layout($(this));
    });
});
