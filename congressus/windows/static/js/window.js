function clean() {
    $(".seat-selected").each(function() {
        $(this).click();
    });

    $("input.sessioninput").each(function() {
        if ($(this).attr("type") == 'number') {
            $(this).val("0");
            $(this).change();
        } else {
            $(this).val("0");
        }
    });

    $("[value=none]").click();
    $("[value=cash]").click();
    $("#total").val(0);
    $("#change").val(0);
    $("#payed").val("");

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

function apply_discount(total) {
    var rcheck = $("input[name=discount]:checked");
    var type = rcheck.attr("data-type");
    var value = (rcheck.attr("data-value"));
    if (type == 'none') {
        res = total;
    } else if (type == 'percent') {
        res = total - total * (value / 100);
    } else if (type == 'amount') {
        res -= value;
    } else {
        res = total;
    }
    return res;

}

function recalcTotal() {
    var sum = 0;
    $(".sessioninput").each(function() {
        var n = parseInt($(this).val(), 10);
        var price = parseFloat($(this).data("price"));
        sum += price * n;
    });
    sum = apply_discount(sum);
    $("#total").val(sum);
}

$(document).ready(function() {
    $("form").submit(function() {
        var msg = $("#finish").data("msg");
        var ret = confirm(msg);
        if (ret) {
            args = ' ' + window.windows;
            args += ' ' + moment().format('YYYY-MM-DDThh:mm:ss.SSSSSSZ');
            args += ' ' + $('input[name=payment]:checked').val();
            args += ' ' + $(".seat-selected").length;
            ws.send('add_sale' + args);
            setTimeout(clean, 1000);
        }
        return ret;
    });

    $("#clean").click(clean);
    $("#payed").keyup(calcChange);

    $('.sessioninput').change(function() {
        recalcTotal();
    });
    $("input[name=discount]:radio").change(function() {
        recalcTotal();
    });
    recalcTotal();
    calcChange();
});
