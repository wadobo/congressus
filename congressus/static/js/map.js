(function() {
    var map = window.SeatMap = {};
    map.cbs = $.Callbacks();

    map.showLayout = function(parentObj, obj) {
        var layout = obj.data('layout');
        var session = obj.data('session');
        var layoutid = obj.data('id');
        var dir = ' <span class="glyphicon '+obj.data('glyph')+'" aria-hidden="true"></span>';
        var display = '.display-' + session + '-' + layoutid;
        $(display + ' .layout-name').html(obj.data('name') + dir);
        var sc = $(display + ' .preview').seatCharts({
            map: layout.split("\n"),
            seats: {
                L: {
                    layout: layoutid,
                    session: session,
                    classes: 'front-seat'
                },
                O: {
                    layout: layoutid,
                    session: session,
                    classes : 'unavailable'
                },
                R: {
                    layout: layoutid,
                    session: session,
                    classes : 'unavailable'
                }

            },
            click: function () {
                if (this.status() == 'available') {
                    map.cbs.fire("select", this);
                    return 'selected';
                } else if (this.status() == 'selected') {
                    //seat has been vacated
                    map.cbs.fire("unselect", this);
                    return 'available';
                } else if (this.status() == 'unavailable') {
                    //seat has been already booked
                    return 'unavailable';
                } else {
                    return this.style();
                }
            }
        });
    },

    map.bindLayout = function(obj) {
        obj.find(".layout").each(function() {
            map.showLayout(obj, $(this));
        });

        obj.find(".layout").click(function() {
            var layoutid = $(this).data('id');
            var session = $(this).data('session');
            var display = '.display-' + session + '-' + layoutid;
            obj.find('.display').hide();
            obj.find(display).show();
        });

        obj.find('.display').hide();
    }
}).call(this);
