function get_initial_data() {
    var deferred = new $.Deferred();
    $.ajax({
        type: "POST",
        data: {},
        dataType: 'JSON',
        url: "/dashboard/general/",
        success: function(msg){
            data_sales = msg.sales_log;
            data_access = msg.access_log;
            fill_charts();
            // TODO: get data to websocket
            //setTimeout(function() {
            //    update_charts(window.chart_sales, 'window1', '2016-06-30', 1);
            //}, 5000);
            deferred.resolve(msg);
        }
    });
    return deferred.promise();
}
get_initial_data();


function fill_charts() {
    var ctx_sales = $("#chart-sales").get(0).getContext("2d");
    var ctx_access = $("#chart-access").get(0).getContext("2d");

    window.chart_sales = new Chart(ctx_sales, {
        type: 'line',
        data: data_sales,
        options: {
            scales: {yAxes: [{ ticks: { beginAtZero: true }}]}
        }
    });

    window.chart_access = new Chart(ctx_access, {
        type: 'line',
        data: data_access,
        options: {
            scales: {yAxes: [{ ticks: { beginAtZero: true }}]}
        }
    });
}

function update_charts(chart, dataset_label, label, amount) {
    main_dataset = 0
    n = 0
    ndataset = null;
    for (var dat in chart.data.datasets) {
        if (chart.data.datasets[dat].label == dataset_label) {
            ndataset = n;
            break;
        }
        n++;
    }
    index = chart.data.labels.indexOf(label);

    chart.data.datasets[main_dataset].data[index] += amount;
    if (ndataset !== null) {
        chart.data.datasets[ndataset].data[index] += amount;
    }
    chart.update();
}

$(document).ready(function() {
});
