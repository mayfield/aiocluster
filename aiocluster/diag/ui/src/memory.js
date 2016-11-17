
$(document).ready(function() {
    (async function() {
        let procs_tpl = $.templates("#procs-template");
        while (true) {
            let mem_sum = 0;
            let cpu_sum = 0;
            let api_data = await aioc.api.get('memory');
            
            api_data.workers.forEach(function(x) {
                mem_sum += x.memory.rss;
                cpu_sum += x.cpu_percent;
            });
            $('#procs-holder').html(procs_tpl.render(api_data));
            await sleep(1);
        }
    })();
});
