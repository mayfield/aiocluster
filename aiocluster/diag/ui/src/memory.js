
$(document).ready(function() {
    (async function() {
        let procs_tpl = $.templates("#procs-template");
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
            $('#cpu-usage').html(percent(cpu_sum));
            await sleep(1);
        }
    })();
});
