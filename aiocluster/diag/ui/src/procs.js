
$(document).ready(function() {
    (async function() {
        let tpl_data = await $.get('templates/procs.html');
        let procs_tpl = $.templates(tpl_data);

        var myLineChart = new Chart($('#cpu-graph'), {
            type: 'line',
            data: {
                datasets: [{
                    data: [1,2,3,4,5,6,7,8,9,7,6,5,3,12,1,1,1,3,4,45],
                }]
            },
            options: {}
        });

        while (true) {
            let mem_sum = 0;
            let cpu_sum = 0;
            let api_data = await $.get('/api/v1/ps');
            
            api_data.workers.forEach(function(x) {
                mem_sum += x.memory.rss;
                cpu_sum += x.cpu_percent;
            });
            $('#procs-holder').html(procs_tpl.render(api_data));
            $('#worker-count').html(api_data.workers.length);
            $('#mem-usage').html(megabytes(mem_sum));
            $('#cpu-usage').html(percent(cpu_sum / 100));
            await sleep(1);
        }
    })();
});
