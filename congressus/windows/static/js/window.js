function clean() {
    $(".seat-selected").each(function() {
        $(this).click();
    });

    $("input").each(function() {
        if ($(this).attr("type") == 'number') {
            $(this).val("0");
            $(this).change();
        } else {
            $(this).val("");
        }
    });

    $("#total").html("0");
    $("#change").html("0");
    $("#payed").val(0);

    return false;
}

function calcChange() {
    var total = parseFloat($("#total").html());
    var payed = parseFloat($("#payed").val());
    if (isNaN(payed - total)) {
        $("#change").html(0);
    } else {
        $("#change").html(payed - total);
    }
}

function recalcTotal() {
    var sum = 0;
    $(".sessioninput").each(function() {
        var n = parseInt($(this).val(), 10);
        var price = parseFloat($(this).data("price"));
        sum += price * n;
    });
    $("#total").html(sum);
}

$(document).ready(function() {
    $("form").submit(function() {
        var msg = $("#finish").data("msg");
        return confirm(msg);
    });

    $("#clean").click(clean);
    $("#payed").keyup(calcChange);

    $('.sessioninput').change(function() {
        recalcTotal();
    });
    recalcTotal();
    calcChange();
});
