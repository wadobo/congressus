$(document).ready(function() {

    // EVENTS
    $("#id_numbered").change(function() {
        show_legend(numbered=this.checked);
    });

    function show_legend(numbered) {
        if (numbered) {
            help = "Numere los asientos. Un ejemplo de como numeraríamos los asientos con 4 filas y 3 columnas:<br>";
            help += "10|11|12<br>";
            help += "7|8|9<br>";
            help += "4|5|6<br>";
            help += "1|2|3<br>";
        } else {
             help = "Selecciona la disponibilidad y disposición de los asientos, siguiendo la siguiente nomenclatura:<br>";
            help += "O --> Ocupado<br>";
            help += "L --> Libre<br>";
            help += "R --> Reservado<br>";
            help += "Un ejemplo de 3 filas y 4 columnas:<br>";
            help += "<tr>LLOO<br>";
            help += "OOOL<br>";
            help += "RRRR<br>";
        }
        $("p.help")[0].innerHTML = help;
    }
    show_legend($("#id_numbered").checked);

    window.preview = function() {
        var layout = $('#id_layout').val();
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

});
