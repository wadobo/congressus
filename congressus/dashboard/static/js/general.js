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

function update_charts(chart, label, datasets) {
    chart.data.labels.shift();
    chart.data.labels.push(label);
    var d = 0;
    for (var dset in chart.data.datasets) {
        chart.data.datasets[dset].data.shift();
        chart.data.datasets[dset].data.push(datasets[d]);
        d++;
    }
    chart.update();
}

$(document).ready(function() {
});
