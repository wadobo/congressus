$(document).ready(function() {

    function edit_types(msg) {
        // Edit select with invitation types and pass types
        tinvi = msg['invitation_types'];
        var select_invi = $("#type-invitations");
        for (var i in tinvi) {
            opt = tinvi[i][0];
            value = tinvi[i][1];
            select_invi.append('<option value="'+opt+'">'+value+'</option>');
        }

        var select_pass = $("#type-passes");
        tpass = msg['pass_types'];
        for (var p in tpass) {
            opt = tpass[p][0];
            value = tpass[p][1];
            select_pass.append('<option value="'+opt+'">'+value+'</option>');
        }
    }

    function get_types() {
        var deferred = new $.Deferred();
        $.ajax({
            type: "POST",
            data: {},
            dataType: 'JSON',
            url: "/generator/get-types/",
            success: function(msg){
                edit_types(msg);
                deferred.resolve(msg);
            }
        });
        return deferred.promise();
    }
    get_types();

});

