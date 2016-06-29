function initial_data() {
    data_sales = {
        labels: ["1", "2", "3", "4", "5", "6", "7"],
        datasets: [
            {
                label: "All",
                borderColor: "rgba(0,0,0,1)",
                borderWidth: 5,
                pointBorderWidth: 1,
                pointRadius: 1,
                data: [5, 15, 20, 21, 40, 60, 100],
            }, 
            {
                label: "C1",
                fill: false,
                borderColor: "rgba(75,192,192,1)",
                borderWidth: 1,
                pointBorderWidth: 0,
                pointRadius: 0,
                data: [1, 7, 16, 17, 24, 44, 68],
            } 
        ]
    };

    data_access = {
        labels: [1, 5, 10, 15, 20, 25, 30],
        datasets: [
            {
                label: "All",
                borderColor: "rgba(0,0,0,1)",
                borderWidth: 5,
                pointBorderWidth: 1,
                pointRadius: 1,
                data: [5, 15, 20, 21, 40, 60, 100],
            }, 
            {
                label: "C1",
                fill: false,
                borderColor: "rgba(75,192,192,1)",
                borderWidth: 1,
                pointBorderWidth: 0,
                pointRadius: 0,
                data: [1, 7, 16, 17, 24, 44, 68],
            } 
        ]
    };
    last_label_access = 30;
}
initial_data();


function fill_charts() {
    var ctx_sales = $("#chart-sales").get(0).getContext("2d");
    var ctx_access = $("#chart-access").get(0).getContext("2d");

    window.chart_sales = new Chart(ctx_sales, {
        type: 'line',
        data: data_sales,
        options: {}
    });

    window.chart_access = new Chart(ctx_access, {
        type: 'line',
        data: data_access,
        options: {}
    });
}
fill_charts();

function update_charts(chart, label, datasets) {
    chart.data.labels.shift();
    chart.data.labels.push(label);

    var d = 0;
    for (var dset in chart.data.datasets) {
        console.log(chart.data.datasets[dset].data);
        chart.data.datasets[dset].data.shift();
        chart.data.datasets[dset].data.push(datasets[d]);
        d++;
    }
    chart.update();
}

setTimeout(function(){
    update_charts(window.chart_access, 35, [100, 80]);
}, 5000);


$(document).ready(function() {
});
