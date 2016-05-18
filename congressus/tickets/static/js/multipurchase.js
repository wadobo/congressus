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
});
