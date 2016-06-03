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

    $("#total").val(0);
    $("#change").val(0);
    $("#payed").val(0);

    return false;
}

function calcChange() {
    var total = parseFloat($("#total").val());
    var payed = parseFloat($("#payed").val());
    if (isNaN(payed - total)) {
        $("#change").val(0);
    } else {
        $("#change").val(payed - total);
    }
}

function recalcTotal() {
    var sum = 0;
    $(".sessioninput").each(function() {
        var n = parseInt($(this).val(), 10);
        var price = parseFloat($(this).data("price"));
        sum += price * n;
    });
    $("#total").val(sum);
}

$(document).ready(function() {
    $("form").submit(function() {
        var msg = $("#finish").data("msg");
        var ret = confirm(msg);
        if (ret) {
            setTimeout(clean, 1000);
        }
        return ret;
    });

    $("#clean").click(clean);
    $("#payed").keyup(calcChange);

    $('.sessioninput').change(function() {
        recalcTotal();
    });
    recalcTotal();
    calcChange();
});
